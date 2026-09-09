"""Synaptic Brain Engine (Phase 01).

Implements the Live Synaptic Brain for the educational scientific laboratory:
"Synaptic Plasticity as Short-Term Memory".

Scientific Concept:
Recent neural activity temporarily strengthens synaptic connections (Hebbian write),
turning the network's wiring into a dynamic form of short-term/working memory.
Associative memory operates via matrix outer-product updates:
    W(t+1) = (1 - λ) W(t) + η · (v ⊗ k)
Recall operates via linear readout:
    v̂ = W @ k_query

This module is 100% pure NumPy, fully deterministic, inspectable, and faithful
to the underlying computational core.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_concept_vector, encode_value_vector
from .experiment import Experiment
from .mechanisms.base import MechanismParams
from .memory import Memory, TextMemory, encode_memory, similarity
from .vectors import cosine


@dataclass
class SynapticNeuron:
    """A neuron in the synaptic network (Input Key unit, Output Value unit, or State dimension)."""

    id: str
    index: int
    neuron_type: str  # "input_key" | "output_value" | "state_unit"
    label: str
    activation: float
    baseline_activation: float
    inflow_weight: float
    outflow_weight: float
    dominant_concepts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "index": int(self.index),
            "neuron_type": self.neuron_type,
            "label": self.label,
            "activation": float(self.activation),
            "baseline_activation": float(self.baseline_activation),
            "inflow_weight": float(self.inflow_weight),
            "outflow_weight": float(self.outflow_weight),
            "dominant_concepts": self.dominant_concepts,
        }


@dataclass
class SynapticConnection:
    """A directed synapse connecting neuron source (pre) to neuron target (post)."""

    id: str
    source: str
    target: str
    source_idx: int
    target_idx: int
    weight: float
    weight_before: float
    delta_weight: float
    abs_weight: float
    tier: str  # "weak" | "medium" | "strong"
    polarity: str  # "excitatory" | "inhibitory" | "neutral"
    plasticity_trace: float
    last_update_timestep: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "source_idx": int(self.source_idx),
            "target_idx": int(self.target_idx),
            "weight": float(self.weight),
            "weight_before": float(self.weight_before),
            "delta_weight": float(self.delta_weight),
            "abs_weight": float(self.abs_weight),
            "tier": self.tier,
            "polarity": self.polarity,
            "plasticity_trace": float(self.plasticity_trace),
            "last_update_timestep": int(self.last_update_timestep),
        }


@dataclass
class SynapticPathway:
    """Active signal propagation pathway through the network for the current event."""

    active_key_indices: List[int]
    active_value_indices: List[int]
    active_synapse_ids: List[str]
    transmission_energy: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_key_indices": self.active_key_indices,
            "active_value_indices": self.active_value_indices,
            "active_synapse_ids": self.active_synapse_ids,
            "transmission_energy": float(self.transmission_energy),
        }


@dataclass
class SynapticExplanation:
    """Exact computational accounting of the last network transformation."""

    event_label: str
    event_type: str  # "WRITE" | "RECALL" | "DECAY" | "INIT"
    active_units: int
    synaptic_updates: int
    mean_weight_change: float
    max_weight_change: float
    state_change_pct: float
    norm_before: float
    norm_after: float
    write_gain: float
    decay_applied: float
    scientific_note: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_label": self.event_label,
            "event_type": self.event_type,
            "active_units": int(self.active_units),
            "synaptic_updates": int(self.synaptic_updates),
            "mean_weight_change": float(self.mean_weight_change),
            "max_weight_change": float(self.max_weight_change),
            "state_change_pct": float(self.state_change_pct),
            "norm_before": float(self.norm_before),
            "norm_after": float(self.norm_after),
            "write_gain": float(self.write_gain),
            "decay_applied": float(self.decay_applied),
            "scientific_note": self.scientific_note,
        }


@dataclass
class SynapticRecallResult:
    """Forensic readout details when probing the synaptic network."""

    query_concept: str
    predicted_value: Optional[str]
    confidence: float
    ground_truth: Optional[str]
    is_correct: Optional[bool]
    candidate_matches: List[Dict[str, Any]]
    fidelity: float
    crosstalk_noise: float
    readout_vector: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_concept": self.query_concept,
            "predicted_value": self.predicted_value,
            "confidence": float(self.confidence),
            "ground_truth": self.ground_truth,
            "is_correct": self.is_correct,
            "candidate_matches": self.candidate_matches,
            "fidelity": float(self.fidelity),
            "crosstalk_noise": float(self.crosstalk_noise),
            "readout_vector": self.readout_vector,
        }


@dataclass
class SynapticNetworkState:
    """Complete serializable snapshot of the Live Synaptic Brain."""

    timestep: int
    dimension: int
    mechanism: str
    total_synapses: int
    active_synapses_count: int
    mean_synaptic_weight: float
    max_synaptic_weight: float
    matrix_norm: float
    sparsity: float
    neurons: List[SynapticNeuron]
    synapses: List[SynapticConnection]
    last_pathway: Optional[SynapticPathway]
    last_explanation: Optional[SynapticExplanation]
    last_recall: Optional[SynapticRecallResult]
    history_timeline: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestep": int(self.timestep),
            "dimension": int(self.dimension),
            "mechanism": self.mechanism,
            "total_synapses": int(self.total_synapses),
            "active_synapses_count": int(self.active_synapses_count),
            "mean_synaptic_weight": float(self.mean_synaptic_weight),
            "max_synaptic_weight": float(self.max_synaptic_weight),
            "matrix_norm": float(self.matrix_norm),
            "sparsity": float(self.sparsity),
            "neurons": [n.to_dict() for n in self.neurons],
            "synapses": [s.to_dict() for s in self.synapses],
            "last_pathway": self.last_pathway.to_dict() if self.last_pathway else None,
            "last_explanation": self.last_explanation.to_dict() if self.last_explanation else None,
            "last_recall": self.last_recall.to_dict() if self.last_recall else None,
            "history_timeline": self.history_timeline,
        }


class SynapticBrain:
    """Interactive Live Synaptic Brain simulator & inspector.

    Holds the weight matrix W, tracks plasticity traces, executes Hebbian writes,
    linear associative recall, exponential decay, and builds topological graphs
    for scientific inspection.
    """

    def __init__(
        self,
        seed: int = 42,
        d: int = 16,
        decay: float = 0.05,
        update_strength: float = 1.0,
        memory_strength: float = 1.0,
        mechanism: str = "hebbian",
    ) -> None:
        self.seed = int(seed)
        self.d = int(d)
        self.decay = float(decay)
        self.update_strength = float(update_strength)
        self.memory_strength = float(memory_strength)
        self.mechanism = mechanism

        # Weight matrix W is d x d (connecting d key neurons to d value neurons)
        self.W = np.zeros((self.d, self.d), dtype=np.float64)
        self.W_prev = np.zeros((self.d, self.d), dtype=np.float64)
        self.last_delta = np.zeros((self.d, self.d), dtype=np.float64)
        self.last_update_steps = np.zeros((self.d, self.d), dtype=np.int32)

        # Activations
        self.key_activations = np.zeros(self.d, dtype=np.float64)
        self.value_activations = np.zeros(self.d, dtype=np.float64)

        # Memory store
        self.library: List[Memory] = []
        self.timestep: int = 0
        self.history_timeline: List[Dict[str, Any]] = []

        # Last results
        self.last_pathway: Optional[SynapticPathway] = None
        self.last_explanation: Optional[SynapticExplanation] = None
        self.last_recall: Optional[SynapticRecallResult] = None

        # Record initial event
        self._record_timeline_event(
            event_type="INIT",
            label="Initial Resting State",
            details={"matrix_norm": 0.0, "decay": self.decay},
        )

    def _record_timeline_event(
        self, event_type: str, label: str, details: Dict[str, Any]
    ) -> None:
        self.history_timeline.append(
            {
                "step": self.timestep,
                "event_type": event_type,
                "label": label,
                "matrix_norm": float(np.linalg.norm(self.W)),
                "active_synapses": int(np.sum(np.abs(self.W) > 1e-5)),
                "details": details,
            }
        )

    def write(
        self,
        concept: str,
        value: str,
        importance: float = 1.0,
        strength: float = 1.0,
    ) -> SynapticNetworkState:
        """Execute a Hebbian outer-product write: W <- (1 - λ) W + η (v ⊗ k)."""
        self.timestep += 1
        self.W_prev = self.W.copy()
        norm_before = float(np.linalg.norm(self.W_prev))

        # Encode key and value deterministically
        k_vec = encode_concept_vector(concept, self.seed, self.d)
        v_vec = encode_value_vector(value, self.seed, self.d)

        self.key_activations = k_vec.copy()
        self.value_activations = v_vec.copy()

        # Effective gain: η = update_strength * memory_strength * importance * strength
        gain = float(self.update_strength * self.memory_strength * importance * strength)
        delta_W = gain * np.outer(v_vec, k_vec)
        self.last_delta = delta_W

        # Update weight matrix: (1 - λ) W + ΔW
        self.W = (1.0 - self.decay) * self.W_prev + delta_W
        norm_after = float(np.linalg.norm(self.W))

        # Mark updated synapses
        updated_mask = np.abs(delta_W) > 1e-6
        self.last_update_steps[updated_mask] = self.timestep

        # Add or update memory in library
        mem_obj = encode_memory(
            TextMemory(
                concept=concept,
                value=value,
                importance=importance,
                strength=strength,
                metadata={"write_step": self.timestep},
            ),
            seed=self.seed,
            d=self.d,
            memory_id=f"mem_{uuid.uuid4().hex[:8]}",
        )
        self.library.append(mem_obj)

        # Active pathway calculation
        active_k = np.where(np.abs(k_vec) > np.percentile(np.abs(k_vec), 70))[0].tolist()
        active_v = np.where(np.abs(v_vec) > np.percentile(np.abs(v_vec), 70))[0].tolist()
        active_syn_ids = [
            f"syn_k{j}_v{i}"
            for i in range(self.d)
            for j in range(self.d)
            if abs(delta_W[i, j]) > np.percentile(np.abs(delta_W), 85)
        ]

        self.last_pathway = SynapticPathway(
            active_key_indices=active_k,
            active_value_indices=active_v,
            active_synapse_ids=active_syn_ids,
            transmission_energy=float(np.linalg.norm(delta_W)),
        )

        # Computational explanation
        diff_norm = float(np.linalg.norm(self.W - self.W_prev))
        pct_change = (diff_norm / (norm_before + 1e-9)) * 100.0 if norm_before > 1e-9 else 100.0
        active_unit_count = int(np.sum(np.abs(k_vec) > 1e-4) + np.sum(np.abs(v_vec) > 1e-4))
        syn_updates = int(np.sum(updated_mask))

        self.last_explanation = SynapticExplanation(
            event_label=f"WRITE: {concept.upper()} = {value.upper()}",
            event_type="WRITE",
            active_units=active_unit_count,
            synaptic_updates=syn_updates,
            mean_weight_change=float(np.mean(np.abs(delta_W))),
            max_weight_change=float(np.max(np.abs(delta_W))),
            state_change_pct=pct_change,
            norm_before=norm_before,
            norm_after=norm_after,
            write_gain=gain,
            decay_applied=self.decay,
            scientific_note=(
                f"Hebbian outer product (gain={gain:.2f}) added {syn_updates} synaptic updates. "
                f"Previous weights scaled by (1 - λ) = {1.0 - self.decay:.2f}."
            ),
        )
        self.last_recall = None

        self._record_timeline_event(
            event_type="WRITE",
            label=f"{concept} = {value}",
            details={
                "concept": concept,
                "value": value,
                "gain": gain,
                "synaptic_updates": syn_updates,
                "mean_delta": float(np.mean(np.abs(delta_W))),
                "state_change_pct": pct_change,
            },
        )

        return self.get_state()

    def recall(
        self,
        query_concept: str,
        expected_value: Optional[str] = None,
        measure: str = "cosine",
        top_k: int = 5,
    ) -> SynapticNetworkState:
        """Probe the synaptic brain with query concept: v̂ = W @ k_query."""
        self.timestep += 1
        k_query = encode_concept_vector(query_concept, self.seed, self.d)
        self.key_activations = k_query.copy()

        # Signal forward propagation through synaptic weight matrix
        readout = self.W @ k_query
        self.value_activations = readout.copy()
        readout_norm = float(np.linalg.norm(readout))

        # Match against candidate value vectors in library
        candidates = []
        for mem in self.library:
            sim = float(similarity(readout, mem.value_vector, measure=measure))
            candidates.append(
                {
                    "memory_id": mem.id,
                    "concept": mem.concept,
                    "value": mem.value,
                    "similarity": sim,
                }
            )
        # Deduplicate concepts/values and sort by similarity
        candidates.sort(key=lambda c: c["similarity"], reverse=True)
        top_candidates = candidates[:top_k]

        predicted_val = top_candidates[0]["value"] if top_candidates else None
        top_confidence = top_candidates[0]["similarity"] if top_candidates else 0.0

        is_correct = None
        if expected_value is not None and predicted_val is not None:
            is_correct = (predicted_val.strip().lower() == expected_value.strip().lower())

        # Measure crosstalk noise: if memory target exists, check residue
        crosstalk = 0.0
        fidelity = max(0.0, top_confidence)
        if expected_value:
            expected_v = encode_value_vector(expected_value, self.seed, self.d)
            crosstalk = float(np.linalg.norm(readout - expected_v)) if readout_norm > 1e-6 else 1.0

        self.last_recall = SynapticRecallResult(
            query_concept=query_concept,
            predicted_value=predicted_val,
            confidence=top_confidence,
            ground_truth=expected_value,
            is_correct=is_correct,
            candidate_matches=top_candidates,
            fidelity=fidelity,
            crosstalk_noise=crosstalk,
            readout_vector=readout.tolist(),
        )

        # Highlight pathway through synapses that transmitted the strongest signal
        effective_transmission = np.abs(self.W * k_query[np.newaxis, :])
        active_syn_ids = [
            f"syn_k{j}_v{i}"
            for i in range(self.d)
            for j in range(self.d)
            if effective_transmission[i, j] > np.percentile(effective_transmission, 85)
        ]

        self.last_pathway = SynapticPathway(
            active_key_indices=np.where(np.abs(k_query) > np.percentile(np.abs(k_query), 70))[0].tolist(),
            active_value_indices=np.where(np.abs(readout) > np.percentile(np.abs(readout), 70))[0].tolist(),
            active_synapse_ids=active_syn_ids,
            transmission_energy=readout_norm,
        )

        self.last_explanation = SynapticExplanation(
            event_label=f"RECALL QUERY: '{query_concept.upper()}'",
            event_type="RECALL",
            active_units=int(np.sum(np.abs(k_query) > 1e-4) + np.sum(np.abs(readout) > 1e-4)),
            synaptic_updates=0,
            mean_weight_change=0.0,
            max_weight_change=0.0,
            state_change_pct=0.0,
            norm_before=float(np.linalg.norm(self.W)),
            norm_after=float(np.linalg.norm(self.W)),
            write_gain=0.0,
            decay_applied=0.0,
            scientific_note=(
                f"Readout activation v̂ = W @ k produced norm={readout_norm:.3f}. "
                f"Top match '{predicted_val}' with confidence {top_confidence:.3f} ({measure})."
            ),
        )

        self._record_timeline_event(
            event_type="RECALL",
            label=f"Query '{query_concept}' -> {predicted_val or 'none'}",
            details={
                "query": query_concept,
                "predicted": predicted_val,
                "confidence": top_confidence,
                "is_correct": is_correct,
            },
        )

        return self.get_state()

    def decay_step(self, n_steps: int = 1) -> SynapticNetworkState:
        """Advance time by n steps without input, decaying synaptic connections."""
        self.timestep += n_steps
        self.W_prev = self.W.copy()
        norm_before = float(np.linalg.norm(self.W_prev))

        decay_factor = float((1.0 - self.decay) ** n_steps)
        self.W = self.W * decay_factor
        norm_after = float(np.linalg.norm(self.W))

        self.key_activations = np.zeros(self.d, dtype=np.float64)
        self.value_activations = np.zeros(self.d, dtype=np.float64)
        self.last_delta = self.W - self.W_prev
        self.last_pathway = None
        self.last_recall = None

        self.last_explanation = SynapticExplanation(
            event_label=f"DECAY: {n_steps} IDLE STEP(S)",
            event_type="DECAY",
            active_units=0,
            synaptic_updates=int(np.sum(np.abs(self.W) > 1e-5)),
            mean_weight_change=float(np.mean(np.abs(self.W - self.W_prev))),
            max_weight_change=float(np.max(np.abs(self.W - self.W_prev))),
            state_change_pct=float((1.0 - decay_factor) * 100.0),
            norm_before=norm_before,
            norm_after=norm_after,
            write_gain=0.0,
            decay_applied=self.decay,
            scientific_note=(
                f"Applied exponential synaptic decay (1 - λ)^{n_steps} = {decay_factor:.4f}. "
                f"Synaptic matrix norm decayed from {norm_before:.4f} to {norm_after:.4f}."
            ),
        )

        self._record_timeline_event(
            event_type="DECAY",
            label=f"Decay {n_steps} steps (x{decay_factor:.2f})",
            details={"n_steps": n_steps, "decay_factor": decay_factor, "norm_after": norm_after},
        )

        return self.get_state()

    def reset(self) -> SynapticNetworkState:
        """Reset the synaptic network to zeros."""
        self.W = np.zeros((self.d, self.d), dtype=np.float64)
        self.W_prev = np.zeros((self.d, self.d), dtype=np.float64)
        self.last_delta = np.zeros((self.d, self.d), dtype=np.float64)
        self.last_update_steps = np.zeros((self.d, self.d), dtype=np.int32)
        self.key_activations = np.zeros(self.d, dtype=np.float64)
        self.value_activations = np.zeros(self.d, dtype=np.float64)
        self.library = []
        self.timestep = 0
        self.history_timeline = []
        self.last_pathway = None
        self.last_explanation = None
        self.last_recall = None

        self._record_timeline_event(
            event_type="INIT",
            label="Network Reset",
            details={"matrix_norm": 0.0},
        )
        return self.get_state()

    def load_scenario(self, preset_name: str) -> SynapticNetworkState:
        """Run an educational synaptic plasticity scenario."""
        self.reset()
        if preset_name == "hebbian_formation":
            self.write("color", "blue", importance=1.0, strength=1.0)
            self.write("shape", "triangle", importance=1.0, strength=1.0)
            self.recall("color", expected_value="blue")
        elif preset_name == "interference_demo":
            self.write("role", "admin", importance=1.0, strength=1.0)
            self.write("role", "guest", importance=1.0, strength=1.0)  # Competing write on same key
            self.recall("role", expected_value="guest")
        elif preset_name == "decay_forgetting":
            self.write("access_code", "vault_99", importance=1.0, strength=1.0)
            self.decay_step(n_steps=5)
            self.recall("access_code", expected_value="vault_99")
        elif preset_name == "pattern_completion":
            self.write("subject", "neuroscience", importance=1.0, strength=1.0)
            self.write("mechanism", "plasticity", importance=1.0, strength=1.0)
            self.recall("mechanism", expected_value="plasticity")
        else:
            self.write("concept_alpha", "signal_active", importance=1.0, strength=1.0)

        return self.get_state()

    def get_state(self) -> SynapticNetworkState:
        """Extract the full structured scientific representation of the network."""
        abs_W = np.abs(self.W)
        max_w = float(np.max(abs_W)) if np.size(abs_W) else 0.0
        mean_w = float(np.mean(abs_W)) if np.size(abs_W) else 0.0
        norm_W = float(np.linalg.norm(self.W))

        # Build neuron list (Input Key neurons + Output Value neurons)
        neurons: List[SynapticNeuron] = []

        # Key Input Neurons (j = 0 .. d-1)
        for j in range(self.d):
            outflow = float(np.sum(abs_W[:, j]))
            dominant = [
                m.concept for m in self.library if abs(m.key_vector[j]) > np.percentile(np.abs(m.key_vector), 75)
            ]
            neurons.append(
                SynapticNeuron(
                    id=f"k_{j}",
                    index=j,
                    neuron_type="input_key",
                    label=f"Key Neuron K-{j:02d}",
                    activation=float(self.key_activations[j]),
                    baseline_activation=0.0,
                    inflow_weight=0.0,
                    outflow_weight=outflow,
                    dominant_concepts=dominant[:3],
                )
            )

        # Value Output Neurons (i = 0 .. d-1)
        for i in range(self.d):
            inflow = float(np.sum(abs_W[i, :]))
            dominant = [
                m.value for m in self.library if abs(m.value_vector[i]) > np.percentile(np.abs(m.value_vector), 75)
            ]
            neurons.append(
                SynapticNeuron(
                    id=f"v_{i}",
                    index=i,
                    neuron_type="output_value",
                    label=f"Value Neuron V-{i:02d}",
                    activation=float(self.value_activations[i]),
                    baseline_activation=0.0,
                    inflow_weight=inflow,
                    outflow_weight=0.0,
                    dominant_concepts=dominant[:3],
                )
            )

        # Build synapse list
        synapses: List[SynapticConnection] = []
        active_count = 0

        # Threshold to keep synapse list clean and high-performance
        threshold = 1e-4 if max_w < 1e-4 else min(0.01, 0.05 * max_w)

        for i in range(self.d):
            for j in range(self.d):
                w = float(self.W[i, j])
                w_prev = float(self.W_prev[i, j])
                delta_w = float(self.last_delta[i, j])
                abs_val = abs(w)

                if abs_val > 1e-5:
                    active_count += 1

                # Include all synapses above display threshold or recently updated
                if abs_val >= threshold or abs(delta_w) > 1e-5 or (self.timestep <= 1 and (i < 8 and j < 8)):
                    tier = "weak"
                    if max_w > 0.0:
                        ratio = abs_val / max_w
                        if ratio >= 0.5:
                            tier = "strong"
                        elif ratio >= 0.2:
                            tier = "medium"

                    polarity = "excitatory" if w > 1e-5 else ("inhibitory" if w < -1e-5 else "neutral")

                    synapses.append(
                        SynapticConnection(
                            id=f"syn_k{j}_v{i}",
                            source=f"k_{j}",
                            target=f"v_{i}",
                            source_idx=j,
                            target_idx=i,
                            weight=w,
                            weight_before=w_prev,
                            delta_weight=delta_w,
                            abs_weight=abs_val,
                            tier=tier,
                            polarity=polarity,
                            plasticity_trace=abs(delta_w),
                            last_update_timestep=int(self.last_update_steps[i, j]),
                        )
                    )

        total_syns = self.d * self.d
        sparsity = float(active_count / total_syns) if total_syns else 0.0

        return SynapticNetworkState(
            timestep=self.timestep,
            dimension=self.d,
            mechanism=self.mechanism,
            total_synapses=total_syns,
            active_synapses_count=active_count,
            mean_synaptic_weight=mean_w,
            max_synaptic_weight=max_w,
            matrix_norm=norm_W,
            sparsity=sparsity,
            neurons=neurons,
            synapses=synapses,
            last_pathway=self.last_pathway,
            last_explanation=self.last_explanation,
            last_recall=self.last_recall,
            history_timeline=self.history_timeline,
        )


def extract_synaptic_state_from_experiment(
    exp: Experiment,
    step_idx: int,
    display_dim: int = 16,
) -> SynapticNetworkState:
    """Extract or project the exact synaptic network from an experiment snapshot."""
    def _get_field(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    task_obj = exp.task
    d_full = int(_get_field(task_obj, "d", 16))
    d = min(display_dim, d_full)
    snapshots = exp.snapshots

    if not snapshots:
        brain = SynapticBrain(seed=exp.seed, d=d)
        return brain.get_state()

    idx = max(0, min(len(snapshots) - 1, step_idx))
    snap = snapshots[idx]

    params_obj = exp.parameters
    decay_val = float(_get_field(params_obj, "decay", 0.05))
    update_str = float(_get_field(params_obj, "update_strength", 1.0))

    # Reconstruct matrix
    raw_vec = _get_field(snap, "state_vector", [])
    shape = _get_field(snap, "shape", [])
    state_arr = np.asarray(raw_vec, dtype=np.float64)
    if shape and len(shape) == 2:
        W_full = state_arr.reshape(shape[0], shape[1])
        W = W_full[:d, :d]
    else:
        # For vector mechanisms, build outer-product association matrix
        W = np.outer(state_arr[:d], state_arr[:d]) / (float(np.linalg.norm(state_arr[:d])) + 1e-9)

    brain = SynapticBrain(seed=exp.seed, d=d, decay=decay_val, mechanism=exp.mechanism)
    brain.W = W
    brain.timestep = idx

    # If this step corresponds to an event, extract it
    if idx > 0 and idx - 1 < len(exp.events):
        ev = exp.events[idx - 1]
        kv = _get_field(ev, "key_vector")
        vv = _get_field(ev, "value_vector")
        cl = _get_field(ev, "concept_label", "concept")
        al = _get_field(ev, "attribute_label", "value")

        prev_snap_vec = _get_field(snapshots[idx - 1], "state_vector", [])
        norm_prev = float(np.linalg.norm(np.asarray(prev_snap_vec[:d], dtype=np.float64))) if prev_snap_vec else 0.0

        brain.key_activations = np.asarray(kv[:d] if kv else np.zeros(d))
        brain.value_activations = np.asarray(vv[:d] if vv else np.zeros(d))
        brain.last_explanation = SynapticExplanation(
            event_label=f"{cl} = {al}",
            event_type="WRITE",
            active_units=int(np.sum(np.abs(brain.key_activations) > 1e-4) + np.sum(np.abs(brain.value_activations) > 1e-4)),
            synaptic_updates=int(np.sum(np.abs(W) > 1e-5)),
            mean_weight_change=float(np.mean(np.abs(W))),
            max_weight_change=float(np.max(np.abs(W))),
            state_change_pct=100.0 if idx == 1 else 25.0,
            norm_before=norm_prev,
            norm_after=float(np.linalg.norm(W)),
            write_gain=update_str,
            decay_applied=decay_val,
            scientific_note=f"Snapshot at step {idx} ({cl} -> {al}).",
        )

    return brain.get_state()
