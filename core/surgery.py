"""Synaptic Surgery Engine (Phase 15).

Implements a safe experimental-branch architecture for controlled synaptic
ablation and modification experiments on the Live Synaptic Brain.

DESIGN:
    - NEVER mutates the original SynapticBrain.W matrix.
    - Creates an isolated SurgerySession with:
        * baseline_W  — frozen copy at lock time
        * surgery_W   — mutable experimental copy
        * library     — frozen memory library
    - Surgery operations modify surgery_W only.
    - Recall runs on both matrices for side-by-side comparison.

TRANSPARENCY:
    This is an educational controlled ablation experiment.
    The relevance metric used in Memory X-Ray is:
        relevance_score(i,j) = |W[i,j] * k_query[j]|
    (effective synaptic transmission for synapse (i→j) under query k_query).
    This is derived from the linear readout equation:
        v̂ = W @ k_query   →   v̂[i] = Σ_j W[i,j] * k_query[j]
    Each W[i,j] * k_query[j] is the contribution of synapse (i,j) to output i.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_concept_vector, encode_value_vector
from .memory import Memory, similarity
from .vectors import cosine


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SurgeryOperation:
    """One recorded surgery action on the experimental branch."""

    op_id: str
    operation: str          # "silence" | "weaken" | "strengthen" | "restore"
    synapse_ids: List[str]
    factor: Optional[float]
    timestamp_step: int
    weight_deltas: Dict[str, float]  # synapse_id -> weight change applied
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_id": self.op_id,
            "operation": self.operation,
            "synapse_ids": self.synapse_ids,
            "factor": self.factor,
            "timestamp_step": self.timestamp_step,
            "weight_deltas": self.weight_deltas,
            "description": self.description,
        }


@dataclass
class RecallComparison:
    """Side-by-side recall results for baseline vs surgery branch."""

    query_concept: str
    expected_value: Optional[str]

    # Baseline branch
    baseline_predicted: Optional[str]
    baseline_confidence: float
    baseline_fidelity: float
    baseline_readout_norm: float
    baseline_top_synapse_ids: List[str]

    # Surgery branch
    surgery_predicted: Optional[str]
    surgery_confidence: float
    surgery_fidelity: float
    surgery_readout_norm: float
    surgery_top_synapse_ids: List[str]

    # Deltas
    delta_confidence: float
    delta_fidelity: float
    delta_readout_norm: float
    agreement: bool

    # Meta
    operations_applied: int
    experiment_label: str
    caution_note: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_concept": self.query_concept,
            "expected_value": self.expected_value,
            "baseline": {
                "predicted": self.baseline_predicted,
                "confidence": float(self.baseline_confidence),
                "fidelity": float(self.baseline_fidelity),
                "readout_norm": float(self.baseline_readout_norm),
                "top_synapse_ids": self.baseline_top_synapse_ids,
            },
            "surgery": {
                "predicted": self.surgery_predicted,
                "confidence": float(self.surgery_confidence),
                "fidelity": float(self.surgery_fidelity),
                "readout_norm": float(self.surgery_readout_norm),
                "top_synapse_ids": self.surgery_top_synapse_ids,
            },
            "change": {
                "delta_confidence": float(self.delta_confidence),
                "delta_fidelity": float(self.delta_fidelity),
                "delta_readout_norm": float(self.delta_readout_norm),
                "agreement": self.agreement,
            },
            "operations_applied": self.operations_applied,
            "experiment_label": self.experiment_label,
            "caution_note": self.caution_note,
        }


@dataclass
class SynapseXRay:
    """Per-synapse relevance analysis for a specific query concept."""

    synapse_id: str
    source: str
    target: str
    source_idx: int
    target_idx: int

    # Weights
    current_weight: float
    baseline_weight: float       # equals current for non-surgery context
    weight_before: float
    delta_weight: float
    abs_weight: float
    tier: str                    # "strong" | "medium" | "weak" | "inactive"
    polarity: str                # "excitatory" | "inhibitory" | "neutral"

    # Relevance to query concept
    relevance_score: float       # |W[i,j] * k_query[j]| — documented metric
    relevance_tier: str          # "high" | "moderate" | "weak" | "unrelated"
    k_query_component: float     # k_query[j] value for this synapse's source dim
    contribution_to_readout: float  # W[i,j] * k_query[j] (signed)

    # History meta
    last_update_timestep: int
    plasticity_trace: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "synapse_id": self.synapse_id,
            "source": self.source,
            "target": self.target,
            "source_idx": int(self.source_idx),
            "target_idx": int(self.target_idx),
            "current_weight": float(self.current_weight),
            "baseline_weight": float(self.baseline_weight),
            "weight_before": float(self.weight_before),
            "delta_weight": float(self.delta_weight),
            "abs_weight": float(self.abs_weight),
            "tier": self.tier,
            "polarity": self.polarity,
            "relevance_score": float(self.relevance_score),
            "relevance_tier": self.relevance_tier,
            "k_query_component": float(self.k_query_component),
            "contribution_to_readout": float(self.contribution_to_readout),
            "last_update_timestep": int(self.last_update_timestep),
            "plasticity_trace": float(self.plasticity_trace),
        }


@dataclass
class MemoryXRay:
    """Memory X-Ray: identifies which synapses are responsible for a memory."""

    query_concept: str
    expected_value: Optional[str]
    dimension: int
    seed: int

    # Synapse breakdown
    total_synapses_analyzed: int
    highly_relevant: int    # relevance_tier == "high"
    moderately_relevant: int
    weakly_relevant: int
    unrelated: int

    # Sorted list of all synapses
    synapses: List[SynapseXRay]

    # Readout stats
    readout_norm: float
    top_confidence: float
    predicted_value: Optional[str]

    # Transparency
    metric_description: str
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_concept": self.query_concept,
            "expected_value": self.expected_value,
            "dimension": int(self.dimension),
            "seed": int(self.seed),
            "summary": {
                "total_synapses_analyzed": self.total_synapses_analyzed,
                "highly_relevant": self.highly_relevant,
                "moderately_relevant": self.moderately_relevant,
                "weakly_relevant": self.weakly_relevant,
                "unrelated": self.unrelated,
            },
            "synapses": [s.to_dict() for s in self.synapses],
            "readout": {
                "norm": float(self.readout_norm),
                "top_confidence": float(self.top_confidence),
                "predicted_value": self.predicted_value,
            },
            "transparency": {
                "metric_description": self.metric_description,
                "disclaimer": self.disclaimer,
            },
        }


@dataclass
class SurgerySession:
    """An isolated experimental branch of the synaptic weight matrix.

    The original brain is never touched after lock.
    """

    session_id: str
    seed: int
    d: int
    mechanism: str

    # Frozen baseline
    baseline_W: np.ndarray           # d x d, never modified after lock
    baseline_timestep: int

    # Mutable surgery branch
    surgery_W: np.ndarray            # d x d, all ops applied here
    surgery_op_count: int = 0

    # Weight history at lock (for per-synapse baseline reference)
    baseline_W_prev: np.ndarray = field(default_factory=lambda: np.zeros((1,)))
    baseline_last_delta: np.ndarray = field(default_factory=lambda: np.zeros((1,)))
    baseline_last_update_steps: np.ndarray = field(default_factory=lambda: np.zeros((1,)))

    # Memory library (frozen)
    library: List[Memory] = field(default_factory=list)

    # Log
    operations: List[SurgeryOperation] = field(default_factory=list)

    # Last recall comparison
    last_comparison: Optional[RecallComparison] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "seed": int(self.seed),
            "d": int(self.d),
            "mechanism": self.mechanism,
            "baseline_timestep": int(self.baseline_timestep),
            "surgery_op_count": int(self.surgery_op_count),
            "operations": [op.to_dict() for op in self.operations],
            "last_comparison": self.last_comparison.to_dict() if self.last_comparison else None,
            "library_size": len(self.library),
            "surgery_matrix_norm": float(np.linalg.norm(self.surgery_W)),
            "baseline_matrix_norm": float(np.linalg.norm(self.baseline_W)),
        }


# ---------------------------------------------------------------------------
# Surgery engine functions
# ---------------------------------------------------------------------------

def lock_baseline(brain: Any) -> SurgerySession:
    """Create a surgery session by freezing the current brain state.

    Args:
        brain: SynapticBrain instance (not modified).

    Returns:
        A new SurgerySession with deep-copied matrices.
    """
    session = SurgerySession(
        session_id=uuid.uuid4().hex[:12],
        seed=int(brain.seed),
        d=int(brain.d),
        mechanism=brain.mechanism,
        baseline_W=brain.W.copy(),
        baseline_timestep=int(brain.timestep),
        surgery_W=brain.W.copy(),
        baseline_W_prev=brain.W_prev.copy(),
        baseline_last_delta=brain.last_delta.copy(),
        baseline_last_update_steps=brain.last_update_steps.copy(),
        library=list(brain.library),  # Memory objects are read-only dataclass-ish
    )
    return session


def _parse_synapse_id(synapse_id: str) -> Tuple[int, int]:
    """Parse 'syn_kJ_vI' → (source_j, target_i).

    Returns (-1, -1) on failure.
    """
    parts = synapse_id.split("_")
    if len(parts) == 3 and parts[0] == "syn" and parts[1].startswith("k") and parts[2].startswith("v"):
        try:
            return int(parts[1][1:]), int(parts[2][1:])
        except ValueError:
            pass
    return -1, -1


def weaken_synapses(
    session: SurgerySession,
    synapse_ids: List[str],
    factor: float = 0.5,
) -> SurgeryOperation:
    """Multiply selected synapse weights by factor (0 < factor < 1 weakens).

    Args:
        session: Active surgery session (mutated in-place on surgery_W).
        synapse_ids: List of 'syn_kJ_vI' IDs.
        factor: Multiplicative factor. Values < 1 weaken, > 1 strengthen.

    Returns:
        Recorded SurgeryOperation.
    """
    weight_deltas: Dict[str, float] = {}
    for sid in synapse_ids:
        j, i = _parse_synapse_id(sid)
        if 0 <= i < session.d and 0 <= j < session.d:
            old = float(session.surgery_W[i, j])
            session.surgery_W[i, j] *= factor
            weight_deltas[sid] = float(session.surgery_W[i, j]) - old

    op = SurgeryOperation(
        op_id=uuid.uuid4().hex[:8],
        operation="weaken",
        synapse_ids=synapse_ids,
        factor=float(factor),
        timestamp_step=session.surgery_op_count,
        weight_deltas=weight_deltas,
        description=(
            f"Weakened {len(synapse_ids)} synapse(s) by factor {factor:.3f} in experimental branch. "
            "Original brain is unaffected."
        ),
    )
    session.operations.append(op)
    session.surgery_op_count += 1
    return op


def strengthen_synapses(
    session: SurgerySession,
    synapse_ids: List[str],
    factor: float = 2.0,
) -> SurgeryOperation:
    """Multiply selected synapse weights by factor (factor > 1 strengthens).

    Args:
        session: Active surgery session (mutated in-place on surgery_W).
        synapse_ids: List of 'syn_kJ_vI' IDs.
        factor: Multiplicative factor. Values > 1 strengthen.
    """
    weight_deltas: Dict[str, float] = {}
    for sid in synapse_ids:
        j, i = _parse_synapse_id(sid)
        if 0 <= i < session.d and 0 <= j < session.d:
            old = float(session.surgery_W[i, j])
            session.surgery_W[i, j] *= factor
            weight_deltas[sid] = float(session.surgery_W[i, j]) - old

    op = SurgeryOperation(
        op_id=uuid.uuid4().hex[:8],
        operation="strengthen",
        synapse_ids=synapse_ids,
        factor=float(factor),
        timestamp_step=session.surgery_op_count,
        weight_deltas=weight_deltas,
        description=(
            f"Strengthened {len(synapse_ids)} synapse(s) by factor {factor:.3f} in experimental branch. "
            "Original brain is unaffected."
        ),
    )
    session.operations.append(op)
    session.surgery_op_count += 1
    return op


def silence_synapses(
    session: SurgerySession,
    synapse_ids: List[str],
) -> SurgeryOperation:
    """Set selected synapse weights to exactly 0 in the surgery branch.

    This is a controlled ablation: the synaptic connection is temporarily
    removed from the experimental copy.  The baseline is unchanged.

    Args:
        session: Active surgery session (mutated in-place on surgery_W).
        synapse_ids: List of 'syn_kJ_vI' IDs to silence.
    """
    weight_deltas: Dict[str, float] = {}
    for sid in synapse_ids:
        j, i = _parse_synapse_id(sid)
        if 0 <= i < session.d and 0 <= j < session.d:
            old = float(session.surgery_W[i, j])
            session.surgery_W[i, j] = 0.0
            weight_deltas[sid] = -old

    op = SurgeryOperation(
        op_id=uuid.uuid4().hex[:8],
        operation="silence",
        synapse_ids=synapse_ids,
        factor=0.0,
        timestamp_step=session.surgery_op_count,
        weight_deltas=weight_deltas,
        description=(
            f"CONTROLLED ABLATION EXPERIMENT: Silenced {len(synapse_ids)} synapse(s). "
            "Their weights are set to 0 in the experimental branch. "
            "Removing this connection does not imply causation."
        ),
    )
    session.operations.append(op)
    session.surgery_op_count += 1
    return op


def restore_synapses(
    session: SurgerySession,
    synapse_ids: List[str],
) -> SurgeryOperation:
    """Restore selected synapses from the frozen baseline matrix.

    Args:
        session: Active surgery session (mutated in-place on surgery_W).
        synapse_ids: List of 'syn_kJ_vI' IDs to restore.
    """
    weight_deltas: Dict[str, float] = {}
    for sid in synapse_ids:
        j, i = _parse_synapse_id(sid)
        if 0 <= i < session.d and 0 <= j < session.d:
            old = float(session.surgery_W[i, j])
            session.surgery_W[i, j] = float(session.baseline_W[i, j])
            weight_deltas[sid] = float(session.surgery_W[i, j]) - old

    op = SurgeryOperation(
        op_id=uuid.uuid4().hex[:8],
        operation="restore",
        synapse_ids=synapse_ids,
        factor=None,
        timestamp_step=session.surgery_op_count,
        weight_deltas=weight_deltas,
        description=(
            f"Restored {len(synapse_ids)} synapse(s) to baseline values from the frozen snapshot. "
            "These connections now match the pre-surgery state."
        ),
    )
    session.operations.append(op)
    session.surgery_op_count += 1
    return op


def reset_session(session: SurgerySession) -> SurgeryOperation:
    """Discard all surgery modifications and restore surgery_W from baseline.

    Args:
        session: Active session (surgery_W is fully reset).

    Returns:
        A RESTORE_ALL SurgeryOperation record.
    """
    session.surgery_W = session.baseline_W.copy()
    session.last_comparison = None

    op = SurgeryOperation(
        op_id=uuid.uuid4().hex[:8],
        operation="restore_all",
        synapse_ids=["*"],
        factor=None,
        timestamp_step=session.surgery_op_count,
        weight_deltas={},
        description="Full session reset: experimental branch restored to baseline. All prior operations discarded.",
    )
    session.operations.append(op)
    session.surgery_op_count += 1
    return op


def run_recall_comparison(
    session: SurgerySession,
    query_concept: str,
    expected_value: Optional[str] = None,
    measure: str = "cosine",
    top_k: int = 5,
) -> RecallComparison:
    """Run recall on both baseline and surgery branch, return comparison.

    Both branches use the same k_query and memory library.
    This ensures the only variable is the weight matrix.

    Args:
        session: Active surgery session.
        query_concept: Concept to query.
        expected_value: Optional ground truth.
        measure: Similarity metric ('cosine' or 'dot').
        top_k: Candidates to consider.

    Returns:
        RecallComparison with side-by-side metrics.
    """
    k_query = encode_concept_vector(query_concept, session.seed, session.d)

    def _recall_on_W(W: np.ndarray) -> Dict[str, Any]:
        readout = W @ k_query
        readout_norm = float(np.linalg.norm(readout))
        candidates = []
        for mem in session.library:
            sim = float(similarity(readout, mem.value_vector, measure=measure))
            candidates.append({"memory_id": mem.id, "concept": mem.concept, "value": mem.value, "similarity": sim})
        candidates.sort(key=lambda c: c["similarity"], reverse=True)
        top = candidates[:top_k]
        predicted = top[0]["value"] if top else None
        confidence = top[0]["similarity"] if top else 0.0
        fidelity = max(0.0, confidence)
        # Top active synapses for this W
        eff_trans = np.abs(W * k_query[np.newaxis, :])
        threshold = float(np.percentile(eff_trans, 85)) if np.any(eff_trans > 1e-8) else 0.0
        top_syn = [
            f"syn_k{j}_v{i}"
            for i in range(session.d)
            for j in range(session.d)
            if eff_trans[i, j] > threshold
        ][:15]
        return {
            "predicted": predicted,
            "confidence": confidence,
            "fidelity": fidelity,
            "readout_norm": readout_norm,
            "top_syn": top_syn,
        }

    b = _recall_on_W(session.baseline_W)
    s = _recall_on_W(session.surgery_W)

    num_ops = sum(1 for op in session.operations if op.operation != "restore_all")

    comparison = RecallComparison(
        query_concept=query_concept,
        expected_value=expected_value,
        baseline_predicted=b["predicted"],
        baseline_confidence=b["confidence"],
        baseline_fidelity=b["fidelity"],
        baseline_readout_norm=b["readout_norm"],
        baseline_top_synapse_ids=b["top_syn"],
        surgery_predicted=s["predicted"],
        surgery_confidence=s["confidence"],
        surgery_fidelity=s["fidelity"],
        surgery_readout_norm=s["readout_norm"],
        surgery_top_synapse_ids=s["top_syn"],
        delta_confidence=s["confidence"] - b["confidence"],
        delta_fidelity=s["fidelity"] - b["fidelity"],
        delta_readout_norm=s["readout_norm"] - b["readout_norm"],
        agreement=(b["predicted"] == s["predicted"]),
        operations_applied=num_ops,
        experiment_label="CONTROLLED ABLATION EXPERIMENT" if any(
            op.operation == "silence" for op in session.operations
        ) else "SYNAPTIC MODIFICATION EXPERIMENT",
        caution_note=(
            "Changes shown here are computed from the experimental branch. "
            "This intervention is associated with a change in recall. "
            "Correlation does not establish causation."
        ),
    )
    session.last_comparison = comparison
    return comparison


def compute_memory_xray(
    W: np.ndarray,
    W_prev: np.ndarray,
    last_delta: np.ndarray,
    last_update_steps: np.ndarray,
    library: List[Memory],
    seed: int,
    d: int,
    query_concept: str,
    expected_value: Optional[str] = None,
    measure: str = "cosine",
    top_k: int = 5,
) -> MemoryXRay:
    """Compute Memory X-Ray: per-synapse relevance for a query concept.

    Relevance metric:
        relevance_score(i,j) = |W[i,j] * k_query[j]|
    This is the effective transmission of synapse (i→j) under query k_query,
    derived from v̂[i] = Σ_j W[i,j] * k_query[j].

    Tier thresholds (relative to max relevance):
        high     : >= 50% of max relevance score
        moderate : >= 20% of max relevance score
        weak     : >= 5%  of max relevance score
        unrelated: < 5%   of max relevance score

    Args:
        W: Current weight matrix (d x d).
        W_prev: Previous weight matrix.
        last_delta: Last delta matrix.
        last_update_steps: Last update timestep matrix.
        library: Memory library.
        seed: Encoding seed.
        d: Dimension.
        query_concept: Concept to analyze.
        expected_value: Optional ground truth.
        measure: Similarity metric.
        top_k: Candidates.

    Returns:
        MemoryXRay with complete synapse breakdown.
    """
    k_query = encode_concept_vector(query_concept, seed, d)
    readout = W @ k_query
    readout_norm = float(np.linalg.norm(readout))

    # Recall on the given W
    candidates = []
    for mem in library:
        sim = float(similarity(readout, mem.value_vector, measure=measure))
        candidates.append({"value": mem.value, "similarity": sim})
    candidates.sort(key=lambda c: c["similarity"], reverse=True)
    predicted = candidates[0]["value"] if candidates else None
    top_conf = candidates[0]["similarity"] if candidates else 0.0

    # Effective transmission matrix: |W[i,j] * k_query[j]|
    eff_trans = np.abs(W * k_query[np.newaxis, :])  # shape (d, d)
    max_w = float(np.max(np.abs(W))) if np.any(np.abs(W) > 1e-8) else 1.0
    max_eff = float(np.max(eff_trans)) if np.any(eff_trans > 1e-8) else 1.0

    synapse_list: List[SynapseXRay] = []
    counts = {"high": 0, "moderate": 0, "weak": 0, "unrelated": 0}

    for i in range(d):
        for j in range(d):
            w = float(W[i, j])
            w_prev = float(W_prev[i, j]) if W_prev.shape == W.shape else 0.0
            delta_w = float(last_delta[i, j]) if last_delta.shape == W.shape else 0.0
            abs_w = abs(w)
            contrib = float(W[i, j] * k_query[j])  # signed contribution to v̂[i]
            eff = abs(contrib)  # relevance score

            # Skip synapses with no weight AND no relevance
            if abs_w < 1e-8 and eff < 1e-8:
                continue

            # Relevance tier
            rel_ratio = eff / max_eff if max_eff > 1e-8 else 0.0
            if rel_ratio >= 0.50:
                rel_tier = "high"
            elif rel_ratio >= 0.20:
                rel_tier = "moderate"
            elif rel_ratio >= 0.05:
                rel_tier = "weak"
            else:
                rel_tier = "unrelated"
            counts[rel_tier] += 1

            # Synapse tier based on weight magnitude
            w_ratio = abs_w / max_w if max_w > 1e-8 else 0.0
            if w_ratio >= 0.5:
                tier = "strong"
            elif w_ratio >= 0.2:
                tier = "medium"
            elif abs_w > 1e-5:
                tier = "weak"
            else:
                tier = "inactive"

            polarity = "excitatory" if w > 1e-5 else ("inhibitory" if w < -1e-5 else "neutral")
            last_step = int(last_update_steps[i, j]) if last_update_steps.shape == W.shape else 0

            synapse_list.append(SynapseXRay(
                synapse_id=f"syn_k{j}_v{i}",
                source=f"k_{j}",
                target=f"v_{i}",
                source_idx=j,
                target_idx=i,
                current_weight=w,
                baseline_weight=w,
                weight_before=w_prev,
                delta_weight=delta_w,
                abs_weight=abs_w,
                tier=tier,
                polarity=polarity,
                relevance_score=eff,
                relevance_tier=rel_tier,
                k_query_component=float(k_query[j]),
                contribution_to_readout=contrib,
                last_update_timestep=last_step,
                plasticity_trace=abs(delta_w),
            ))

    # Sort by relevance (descending)
    synapse_list.sort(key=lambda s: s.relevance_score, reverse=True)

    return MemoryXRay(
        query_concept=query_concept,
        expected_value=expected_value,
        dimension=d,
        seed=seed,
        total_synapses_analyzed=len(synapse_list),
        highly_relevant=counts["high"],
        moderately_relevant=counts["moderate"],
        weakly_relevant=counts["weak"],
        unrelated=counts["unrelated"],
        synapses=synapse_list,
        readout_norm=readout_norm,
        top_confidence=top_conf,
        predicted_value=predicted,
        metric_description=(
            "Relevance score: |W[i,j] * k_query[j]| — the effective synaptic transmission "
            "of synapse (i,j) for the query concept's key vector component k_query[j]. "
            "Derived from the linear readout equation v̂ = W @ k_query."
        ),
        disclaimer=(
            "Educational computational model of synaptic plasticity. "
            "Relevance scores reflect computational contribution, not biological causation."
        ),
    )


def get_synapse_xray_in_session(
    session: SurgerySession,
    synapse_id: str,
) -> Dict[str, Any]:
    """Inspect a single synapse across baseline and surgery branches.

    Returns both weight values and their difference.
    """
    j, i = _parse_synapse_id(synapse_id)
    if not (0 <= i < session.d and 0 <= j < session.d):
        return {"error": f"Invalid synapse ID: {synapse_id}"}

    baseline_w = float(session.baseline_W[i, j])
    surgery_w = float(session.surgery_W[i, j])
    delta = surgery_w - baseline_w

    # Find what operations touched this synapse
    touching_ops = []
    for op in session.operations:
        if synapse_id in op.synapse_ids or "*" in op.synapse_ids:
            touching_ops.append(op.to_dict())

    return {
        "synapse_id": synapse_id,
        "source": f"k_{j}",
        "target": f"v_{i}",
        "source_idx": int(j),
        "target_idx": int(i),
        "baseline_weight": baseline_w,
        "surgery_weight": surgery_w,
        "weight_delta": float(delta),
        "abs_baseline": abs(baseline_w),
        "abs_surgery": abs(surgery_w),
        "is_modified": abs(delta) > 1e-9,
        "operations_applied": touching_ops,
        "disclaimer": (
            "Surgery weight is from the experimental branch only. "
            "Baseline weight reflects the locked session snapshot."
        ),
    }
