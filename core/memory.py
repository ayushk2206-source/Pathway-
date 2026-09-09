"""Memory engine (Phase 02, sections 1–8).

Sits on top of the Phase 01 substrate. A **Memory** is a named key–value
pair with text labels and deterministic vectors; a write pushes it into
the mechanism state through the exact same update rules Phase 01 defined
(no contradiction — the memory engine is a thin, inspectable layer).

The engine adds the *accounting* Phase 02 needs:

- ``UpdateResult``: state before/after, update vector, affected
  dimensions, and a split of the state change into
  **memory contribution** (the write term ``gain · bind(k, v)``) vs
  **interference contribution** (everything else the update rule did:
  decay, erasure, competition — whatever the mechanism's rule changed
  beyond the memory's own write).
- ``RecallResult``: prediction vs ground truth, confidence, candidates,
  and which dimensions of the state did the work.
- a configurable similarity measure and an explicit, documented
  *educational interference model*.

All vectors are produced by ``core.encoder`` from (text, seed, d) —
deterministic, inspectable, and explicitly **not** a production embedding.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .encoder import encode_concept_vector, encode_value_vector
from .events import Event
from .mechanisms.base import Mechanism, MechanismParams
from .vectors import bind, cosine, unbind

# ---------------------------------------------------------------------------
# similarity measures (section 5)
# ---------------------------------------------------------------------------
SIMILARITY_MEASURES = ("cosine", "euclidean", "dot")


def similarity(
    a: np.ndarray, b: np.ndarray, measure: str = "cosine"
) -> float:
    """Similarity between two vectors under a configurable measure.

    cosine      : ``<a,b> / (||a|| ||b||)`` ∈ [-1, 1]; 0 if either is zero.
                  Directional similarity; the default and primary measure.
    euclidean   : ``1 / (1 + ||a - b||)`` ∈ (0, 1]. Inverts distance so
                  magnitude differences count too.
    dot         : ``<a, b>``, raw. Magnitude-sensitive: larger states score
                  higher regardless of direction. Useful when comparing
                  *strengths* (e.g. memory-strength effects).
    """
    if measure == "cosine":
        return cosine(a, b)
    if measure == "euclidean":
        return 1.0 / (1.0 + float(np.linalg.norm(a - b)))
    if measure == "dot":
        return float(np.dot(a, b))
    raise ValueError(f"unknown similarity measure {measure!r}; use {SIMILARITY_MEASURES}")


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


# ---------------------------------------------------------------------------
# educational interference model (section 6)
# ---------------------------------------------------------------------------
def interference_model(
    a: np.ndarray,
    b: np.ndarray,
    update_strength: float,
    competition_factor: float = 1.0,
    measure: str = "cosine",
) -> float:
    """OUR EDUCATIONAL INTERFERENCE MODEL.

    ``interference(A, B) = similarity(A, B) × update_strength × competition_factor``

    This is a *baseline formulation for teaching*, not a universal law: it
    postulates that two memories interfere in proportion to how similar
    their representations are, how hard the update pushes, and how strongly
    they compete. The platform never uses this formula as ground truth —
    the *measured* interference (old-binding leakage into readouts) comes
    from actually running the mechanisms, and learners can compare the
    model's prediction against the measurement.
    """
    return float(
        max(0.0, similarity(a, b, measure)) * float(update_strength) * float(competition_factor)
    )


# ---------------------------------------------------------------------------
# Memory (section 1)
# ---------------------------------------------------------------------------
@dataclass
class TextMemory:
    """User-facing memory description: \"concept = value\".

    A pure *query* has only a concept (value left empty).
    """

    concept: str
    value: str = ""
    importance: float = 1.0
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    """A materialized memory: text labels + deterministic vectors.

    ``vector`` is the stored pattern ``bind(key_vector, value_vector)`` —
    the exact thing the write pushes into the state.
    """

    id: str
    concept: str
    value: str
    key_vector: np.ndarray
    value_vector: np.ndarray
    vector: np.ndarray
    importance: float = 1.0
    strength: float = 1.0
    creation_timestep: int = 0
    last_accessed_timestep: int = 0
    access_count: int = 0
    source_event_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_vectors: bool = True) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "id": self.id,
            "concept": self.concept,
            "value": self.value,
            "importance": float(self.importance),
            "strength": float(self.strength),
            "creation_timestep": int(self.creation_timestep),
            "last_accessed_timestep": int(self.last_accessed_timestep),
            "access_count": int(self.access_count),
            "source_event_id": self.source_event_id,
            "metadata": self.metadata,
        }
        if include_vectors:
            out["key_vector"] = self.key_vector.tolist()
            out["value_vector"] = self.value_vector.tolist()
            out["vector"] = self.vector.tolist()
        else:
            out["key_vector_norm"] = float(np.linalg.norm(self.key_vector))
            out["value_vector_norm"] = float(np.linalg.norm(self.value_vector))
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Memory":
        kv = np.asarray(d["key_vector"], dtype=np.float64)
        vv = np.asarray(d["value_vector"], dtype=np.float64)
        return cls(
            id=d["id"],
            concept=d["concept"],
            value=d["value"],
            key_vector=kv,
            value_vector=vv,
            vector=np.asarray(d.get("vector", bind(kv, vv)), dtype=np.float64),
            importance=float(d.get("importance", 1.0)),
            strength=float(d.get("strength", 1.0)),
            creation_timestep=int(d.get("creation_timestep", 0)),
            last_accessed_timestep=int(d.get("last_accessed_timestep", 0)),
            access_count=int(d.get("access_count", 0)),
            source_event_id=d.get("source_event_id"),
            metadata=dict(d.get("metadata", {})),
        )


def encode_memory(
    text_memory: TextMemory,
    seed: int,
    d: int,
    memory_id: Optional[str] = None,
) -> Memory:
    """Deterministic text → Memory. Reproducible from (text, seed, d)."""
    key_vector = encode_concept_vector(text_memory.concept, seed, d)
    value_vector = encode_value_vector(text_memory.value, seed, d)
    return Memory(
        id=memory_id or uuid.uuid4().hex[:12],
        concept=text_memory.concept,
        value=text_memory.value,
        key_vector=key_vector,
        value_vector=value_vector,
        vector=bind(key_vector, value_vector),
        importance=float(text_memory.importance),
        strength=float(text_memory.strength),
        metadata=dict(text_memory.metadata),
    )


def _memory_event(memory: Memory, timestep: int) -> Event:
    return Event(
        id=f"m{timestep:04d}",
        timestep=timestep,
        concept_label=memory.concept,
        attribute_label=memory.value,
        key_vector=memory.key_vector,
        value_vector=memory.value_vector,
        importance=memory.importance,
        strength=memory.strength,
        noise=None,  # mechanism-level input_noise applies
        metadata={"memory_id": memory.id, "memory_concept": memory.concept},
    )


# ---------------------------------------------------------------------------
# write (section 2)
# ---------------------------------------------------------------------------
@dataclass
class UpdateResult:
    """The complete accounting of one memory write into the state."""

    timestep: int
    memory_id: str
    state_before: List[float]
    state_after: List[float]
    update_vector: List[float]
    update_magnitude: float
    affected_dimensions: List[int]
    top_affected_dimensions: List[int]
    memory_contribution: float  # norm of the write term gain·bind(k,v)
    interference_contribution: float  # norm of (update − write term)
    memory_contribution_vector: List[float]
    interference_contribution_vector: List[float]
    decay_applied: float
    erasure_norm: float
    mechanism_trace: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestep": int(self.timestep),
            "memory_id": self.memory_id,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "update_vector": self.update_vector,
            "update_magnitude": float(self.update_magnitude),
            "affected_dimensions": self.affected_dimensions,
            "num_affected": len(self.affected_dimensions),
            "top_affected_dimensions": self.top_affected_dimensions,
            "memory_contribution": float(self.memory_contribution),
            "interference_contribution": float(self.interference_contribution),
            "memory_contribution_vector": self.memory_contribution_vector,
            "interference_contribution_vector": self.interference_contribution_vector,
            "decay_applied": float(self.decay_applied),
            "erasure_norm": float(self.erasure_norm),
            "mechanism_trace": self.mechanism_trace,
        }


def write_memory(
    mech: Mechanism,
    memory: Memory,
    timestep: int = 0,
) -> UpdateResult:
    """Write a memory into the mechanism's state; returns full accounting.

    Deterministic: same mechanism state + memory + timestep ⇒ same result.
    """
    state_before = mech.state_vector().copy()
    event = _memory_event(memory, timestep)
    trace = mech.update(event)

    gain = float(
        mech.params.update_strength
        * mech.params.memory_strength
        * memory.importance
        * memory.strength
    )
    write_term = gain * mech.binding_vector(event)

    state_after = mech.state_vector().copy()
    update_vector = state_after - state_before
    interference_vector = update_vector - write_term

    affected = np.where(np.abs(update_vector) > 1e-12)[0]
    order = np.argsort(-np.abs(update_vector), kind="stable")
    top = order[: min(10, order.size)]

    memory.last_accessed_timestep = timestep
    memory.access_count += 1

    return UpdateResult(
        timestep=timestep,
        memory_id=memory.id,
        state_before=state_before.tolist(),
        state_after=state_after.tolist(),
        update_vector=update_vector.tolist(),
        update_magnitude=float(np.linalg.norm(update_vector)),
        affected_dimensions=affected.tolist(),
        top_affected_dimensions=top.tolist(),
        memory_contribution=float(np.linalg.norm(write_term)),
        interference_contribution=float(np.linalg.norm(interference_vector)),
        memory_contribution_vector=write_term.tolist(),
        interference_contribution_vector=interference_vector.tolist(),
        decay_applied=float(mech.params.decay),
        erasure_norm=float(trace.get("erased_norm", 0.0) or 0.0),
        mechanism_trace=trace,
    )


# ---------------------------------------------------------------------------
# recall (section 3)
# ---------------------------------------------------------------------------
@dataclass
class RecallResult:
    """The complete answer to one query against a mechanism state."""

    timestep: int
    query_concept: str
    predicted_value: str
    predicted_memory_id: Optional[str]
    confidence: float
    ground_truth: Optional[str]
    correct: Optional[bool]
    similarity: float
    prediction_vector: List[float]
    candidate_memories: List[Dict[str, Any]]
    state_similarity: float
    relevant_dimensions: List[int]
    measure: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestep": int(self.timestep),
            "query_concept": self.query_concept,
            "predicted_value": self.predicted_value,
            "predicted_memory_id": self.predicted_memory_id,
            "confidence": float(self.confidence),
            "ground_truth": self.ground_truth,
            "correct": self.correct,
            "similarity": float(self.similarity),
            "prediction_vector": self.prediction_vector,
            "candidate_memories": self.candidate_memories,
            "state_similarity": float(self.state_similarity),
            "relevant_dimensions": self.relevant_dimensions,
            "measure": self.measure,
        }


def recall_memory(
    mech: Mechanism,
    query: TextMemory,
    library: List[Memory],
    seed: int,
    d: int,
    expected_value: Optional[str] = None,
    timestep: int = 0,
    measure: str = "cosine",
    top_k: int = 5,
) -> RecallResult:
    """Ask the state \"what is <concept>?\" against a library of memories.

    1. encode the query concept (deterministic),
    2. read the value out of the current state with the query key,
    3. rank library memories by similarity of the readout to each
       memory's *value vector* (the payload),
    4. prediction = best match; confidence = its similarity.

    ``ground_truth``/``correct`` are ``None`` for a pure probe (no expected
    value supplied) — the platform never invents an answer.
    """
    key_vector = encode_concept_vector(query.concept, seed, d)
    readout = mech.recall(key_vector)
    readout_arr = np.asarray(readout, dtype=np.float64)

    candidates = []
    for m in library:
        sim = similarity(readout_arr, m.value_vector, measure)
        candidates.append(
            {
                "memory_id": m.id,
                "concept": m.concept,
                "value": m.value,
                "similarity": float(sim),
            }
        )
    candidates.sort(key=lambda c: c["similarity"], reverse=True)
    top = candidates[:top_k]

    predicted = top[0] if top else None
    ground_truth = expected_value
    correct = (
        None
        if ground_truth is None
        else (predicted["value"] == ground_truth if predicted else False)
    )

    # state_similarity: how close the readout is to the *expected* value
    # vector (when ground truth is known), else to the predicted value's.
    truth_vector = None
    if ground_truth is not None:
        for m in library:
            if m.value == ground_truth:
                truth_vector = m.value_vector
                break
    if truth_vector is None and predicted is not None:
        for m in library:
            if m.value == predicted["value"]:
                truth_vector = m.value_vector
                break
    state_similarity = (
        similarity(readout_arr, truth_vector, measure) if truth_vector is not None else 0.0
    )

    order = np.argsort(-np.abs(readout_arr), kind="stable")
    relevant = order[: min(10, order.size)].tolist()

    return RecallResult(
        timestep=timestep,
        query_concept=query.concept,
        predicted_value=predicted["value"] if predicted else None,
        predicted_memory_id=predicted["memory_id"] if predicted else None,
        confidence=float(top[0]["similarity"]) if top else 0.0,
        ground_truth=ground_truth,
        correct=correct,
        similarity=float(top[0]["similarity"]) if top else 0.0,
        prediction_vector=readout_arr.tolist(),
        candidate_memories=top,
        state_similarity=float(state_similarity),
        relevant_dimensions=relevant,
        measure=measure,
    )


def write_memories(
    mech: Mechanism,
    memories: List[Memory],
    start_timestep: int = 0,
) -> List[UpdateResult]:
    """Write a sequence of memories; returns one UpdateResult each."""
    return [
        write_memory(mech, m, timestep=start_timestep + i)
        for i, m in enumerate(memories)
    ]