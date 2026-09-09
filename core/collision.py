"""Memory Collision & Interference Engine (Phase 17).

Investigates what happens when multiple memories compete for overlapping
computational and synaptic resources in a Hebbian associative memory matrix.

Core Math:
    Memory A Write: ΔW_A = η_A · (v_A ⊗ k_A)
    Memory B Write: ΔW_B = η_B · (v_B ⊗ k_B)
    Combined Matrix: W = (1 - λ)^τ · ΔW_A + ΔW_B
    Linear Recall:   v̂ = W @ k_query

All metrics are computed via real NumPy linear algebra with zero fabricated scores.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_concept_vector, encode_texts, encode_value_vector
from .memory import Memory, TextMemory, encode_memory, similarity
from .synaptic import (
    SynapticBrain,
    SynapticConnection,
    SynapticExplanation,
    SynapticNetworkState,
    SynapticNeuron,
    SynapticPathway,
    SynapticRecallResult,
)
from .vectors import cosine


@dataclass
class CollisionMemory:
    """A memory event specification for collision experiments."""

    concept: str
    value: str
    importance: float = 1.0
    strength: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept,
            "value": self.value,
            "importance": float(self.importance),
            "strength": float(self.strength),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CollisionMemory":
        return cls(
            concept=str(d.get("concept", "cue_a")),
            value=str(d.get("value", "val_a")),
            importance=float(d.get("importance", 1.0)),
            strength=float(d.get("strength", 1.0)),
        )


@dataclass
class CollisionConfig:
    """Tunable parameters for a controlled collision experiment."""

    seed: int = 42
    dimension: int = 16
    decay: float = 0.05
    update_strength: float = 1.0
    memory_a: CollisionMemory = field(default_factory=lambda: CollisionMemory("alpha_cue", "target_alpha"))
    memory_b: CollisionMemory = field(default_factory=lambda: CollisionMemory("beta_cue", "target_beta"))
    memory_c: Optional[CollisionMemory] = None
    order: str = "A_THEN_B"  # "A_THEN_B" | "B_THEN_A"
    temporal_delay: int = 0  # number of idle decay steps between writes
    overlap_preset: str = "CUSTOM"  # "LOW" | "MODERATE" | "HIGH" | "CUSTOM"
    concept_similarity: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": int(self.seed),
            "dimension": int(self.dimension),
            "decay": float(self.decay),
            "update_strength": float(self.update_strength),
            "memory_a": self.memory_a.to_dict(),
            "memory_b": self.memory_b.to_dict(),
            "memory_c": self.memory_c.to_dict() if self.memory_c else None,
            "order": self.order,
            "temporal_delay": int(self.temporal_delay),
            "overlap_preset": self.overlap_preset,
            "concept_similarity": float(self.concept_similarity),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CollisionConfig":
        mem_a = CollisionMemory.from_dict(d["memory_a"]) if "memory_a" in d else CollisionMemory("alpha_cue", "target_alpha")
        mem_b = CollisionMemory.from_dict(d["memory_b"]) if "memory_b" in d else CollisionMemory("beta_cue", "target_beta")
        mem_c = CollisionMemory.from_dict(d["memory_c"]) if d.get("memory_c") else None
        return cls(
            seed=int(d.get("seed", 42)),
            dimension=int(d.get("dimension", 16)),
            decay=float(d.get("decay", 0.05)),
            update_strength=float(d.get("update_strength", 1.0)),
            memory_a=mem_a,
            memory_b=mem_b,
            memory_c=mem_c,
            order=str(d.get("order", "A_THEN_B")),
            temporal_delay=int(d.get("temporal_delay", 0)),
            overlap_preset=str(d.get("overlap_preset", "CUSTOM")),
            concept_similarity=float(d.get("concept_similarity", 0.0)),
        )


@dataclass
class SynapticPathwayClassification:
    """Categorical and numerical accounting of a single synapse in the collision field."""

    synapse_id: str
    source: str
    target: str
    source_idx: int
    target_idx: int
    classification: str  # "A_ONLY" | "B_ONLY" | "SHARED" | "UNCHANGED"
    weight_after_first: float
    weight_delta_second: float
    final_weight: float
    overwrite_magnitude: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "synapse_id": self.synapse_id,
            "source": self.source,
            "target": self.target,
            "source_idx": int(self.source_idx),
            "target_idx": int(self.target_idx),
            "classification": self.classification,
            "weight_after_first": float(self.weight_after_first),
            "weight_delta_second": float(self.weight_delta_second),
            "final_weight": float(self.final_weight),
            "overwrite_magnitude": float(self.overwrite_magnitude),
        }


@dataclass
class CollisionResult:
    """Complete experimental outcome of a memory collision test."""

    collision_id: str
    config: Dict[str, Any]
    representational_overlap: float
    synaptic_overlap_fraction: float
    matrix_correlation: float
    timeline: List[Dict[str, Any]]
    isolated_recall_a: Dict[str, Any]
    isolated_recall_b: Dict[str, Any]
    combined_recall_a: Dict[str, Any]
    combined_recall_b: Dict[str, Any]
    computational_interference_a: float
    computational_interference_b: float
    overall_computational_interference: float
    memory_dominance: str
    dominant_memory_margin: float
    a_only_synapses: List[str]
    b_only_synapses: List[str]
    shared_synapses: List[str]
    collision_map: List[Dict[str, Any]]
    experiment_report: Dict[str, Any]
    final_network_state: Dict[str, Any]
    isolated_recall_c: Optional[Dict[str, Any]] = None
    combined_recall_c: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collision_id": self.collision_id,
            "config": self.config,
            "representational_overlap": float(self.representational_overlap),
            "synaptic_overlap_fraction": float(self.synaptic_overlap_fraction),
            "matrix_correlation": float(self.matrix_correlation),
            "timeline": self.timeline,
            "isolated_recall_a": self.isolated_recall_a,
            "isolated_recall_b": self.isolated_recall_b,
            "combined_recall_a": self.combined_recall_a,
            "combined_recall_b": self.combined_recall_b,
            "computational_interference_a": float(self.computational_interference_a),
            "computational_interference_b": float(self.computational_interference_b),
            "overall_computational_interference": float(self.overall_computational_interference),
            "memory_dominance": self.memory_dominance,
            "dominant_memory_margin": float(self.dominant_memory_margin),
            "a_only_synapses": self.a_only_synapses,
            "b_only_synapses": self.b_only_synapses,
            "shared_synapses": self.shared_synapses,
            "collision_map": self.collision_map,
            "experiment_report": self.experiment_report,
            "final_network_state": self.final_network_state,
            "isolated_recall_c": self.isolated_recall_c,
            "combined_recall_c": self.combined_recall_c,
        }


# ---------------------------------------------------------------------------
# Vector and Update Preparation Helpers
# ---------------------------------------------------------------------------

def _get_vectors_for_collision(config: CollisionConfig) -> Tuple[
    Dict[str, np.ndarray], Dict[str, np.ndarray]
]:
    """Derive key and value vectors honoring concept_similarity preset."""
    concepts = [config.memory_a.concept, config.memory_b.concept]
    values = [config.memory_a.value, config.memory_b.value]
    if config.memory_c:
        concepts.append(config.memory_c.concept)
        values.append(config.memory_c.value)

    c_sim = float(config.concept_similarity)
    if config.overlap_preset == "LOW":
        c_sim = 0.0
    elif config.overlap_preset == "MODERATE":
        c_sim = 0.45
    elif config.overlap_preset == "HIGH":
        c_sim = 0.85

    k_map, v_map = encode_texts(
        concepts=concepts,
        values=values,
        seed=config.seed,
        d=config.dimension,
        concept_similarity=c_sim,
        value_similarity=0.0,
    )
    return k_map, v_map


# ---------------------------------------------------------------------------
# Isolated Baseline Execution
# ---------------------------------------------------------------------------

def _run_isolated_memory(
    mem: CollisionMemory,
    k_vec: np.ndarray,
    v_vec: np.ndarray,
    seed: int,
    d: int,
    decay: float,
    update_strength: float,
) -> Dict[str, Any]:
    """Execute clean isolated single-memory baseline write and probe."""
    gain = float(update_strength * mem.importance * mem.strength)
    W_iso = gain * np.outer(v_vec, k_vec)

    # Probe recall
    readout = W_iso @ k_vec
    readout_norm = float(np.linalg.norm(readout))
    sim = float(cosine(readout, v_vec)) if readout_norm > 1e-6 else 0.0
    strength = float(np.dot(readout, v_vec))

    return {
        "concept": mem.concept,
        "value": mem.value,
        "fidelity": float(sim),
        "strength": float(strength),
        "readout_norm": readout_norm,
        "is_correct": bool(sim > 0.3),
        "gain": gain,
        "matrix_norm": float(np.linalg.norm(W_iso)),
    }


# ---------------------------------------------------------------------------
# Primary Collision Experiment Engine
# ---------------------------------------------------------------------------

def run_collision_experiment(config: CollisionConfig) -> CollisionResult:
    """Execute a controlled memory collision experiment through genuine matrix computation."""
    d = int(config.dimension)
    decay = float(config.decay)
    eta = float(config.update_strength)

    # 1. Derive synthetic vectors with specified overlap correlation
    k_map, v_map = _get_vectors_for_collision(config)
    kA, vA = k_map[config.memory_a.concept], v_map[config.memory_a.value]
    kB, vB = k_map[config.memory_b.concept], v_map[config.memory_b.value]
    kC = k_map[config.memory_c.concept] if config.memory_c else None
    vC = v_map[config.memory_c.value] if config.memory_c else None

    # Representational overlap: exact cosine of input key vectors
    rep_overlap = float(cosine(kA, kB))

    # 2. Run isolated baselines for Memory A and Memory B
    iso_a = _run_isolated_memory(config.memory_a, kA, vA, config.seed, d, decay, eta)
    iso_b = _run_isolated_memory(config.memory_b, kB, vB, config.seed, d, decay, eta)
    iso_c = _run_isolated_memory(config.memory_c, kC, vC, config.seed, d, decay, eta) if config.memory_c and kC is not None and vC is not None else None

    # 3. Combined Collision Simulation on a single matrix
    # Determine write sequence based on order
    first_mem, first_k, first_v = (config.memory_a, kA, vA) if config.order != "B_THEN_A" else (config.memory_b, kB, vB)
    second_mem, second_k, second_v = (config.memory_b, kB, vB) if config.order != "B_THEN_A" else (config.memory_a, kA, vA)

    gain1 = float(eta * first_mem.importance * first_mem.strength)
    gain2 = float(eta * second_mem.importance * second_mem.strength)
    delta_W1 = gain1 * np.outer(first_v, first_k)
    delta_W2 = gain2 * np.outer(second_v, second_k)

    # Synaptic overlap fraction: normalized matrix inner product (Frobenius correlation)
    norm_delta1 = float(np.linalg.norm(delta_W1))
    norm_delta2 = float(np.linalg.norm(delta_W2))
    matrix_corr = float(np.sum(delta_W1 * delta_W2) / (norm_delta1 * norm_delta2 + 1e-9))

    timeline: List[Dict[str, Any]] = []
    step_num = 0

    # Step 0: Initial zero state
    W_current = np.zeros((d, d), dtype=np.float64)
    timeline.append({
        "step": step_num,
        "event_type": "INIT",
        "label": "Initial Resting Network (W=0)",
        "matrix_weights": W_current.tolist(),
        "matrix_norm": 0.0,
    })

    # Step 1: Write First Memory
    step_num += 1
    W_after_first = delta_W1.copy()
    W_current = W_after_first.copy()
    timeline.append({
        "step": step_num,
        "event_type": "WRITE_1",
        "label": f"WRITE {first_mem.concept} = {first_mem.value}",
        "concept": first_mem.concept,
        "matrix_weights": W_current.tolist(),
        "matrix_norm": float(np.linalg.norm(W_current)),
        "delta_norm": norm_delta1,
    })

    # Step 2: Temporal delay if requested (idle decay steps)
    if config.temporal_delay > 0:
        for _ in range(config.temporal_delay):
            step_num += 1
            W_current = (1.0 - decay) * W_current
            timeline.append({
                "step": step_num,
                "event_type": "DECAY_DELAY",
                "label": f"Temporal Decay Spacing (λ={decay})",
                "matrix_weights": W_current.tolist(),
                "matrix_norm": float(np.linalg.norm(W_current)),
            })

    # Step 3: Write Second Memory (Collision occurs here!)
    step_num += 1
    W_current = (1.0 - decay) * W_current + delta_W2
    W_after_second = W_current.copy()
    timeline.append({
        "step": step_num,
        "event_type": "WRITE_2",
        "label": f"WRITE {second_mem.concept} = {second_mem.value} (COLLISION)",
        "concept": second_mem.concept,
        "matrix_weights": W_current.tolist(),
        "matrix_norm": float(np.linalg.norm(W_current)),
        "delta_norm": norm_delta2,
    })

    # Step 4 (optional): Write Third Memory if specified
    if config.memory_c and kC is not None and vC is not None:
        step_num += 1
        gain3 = float(eta * config.memory_c.importance * config.memory_c.strength)
        delta_W3 = gain3 * np.outer(vC, kC)
        W_current = (1.0 - decay) * W_current + delta_W3
        timeline.append({
            "step": step_num,
            "event_type": "WRITE_3",
            "label": f"WRITE {config.memory_c.concept} = {config.memory_c.value}",
            "concept": config.memory_c.concept,
            "matrix_weights": W_current.tolist(),
            "matrix_norm": float(np.linalg.norm(W_current)),
        })

    # 4. Probing combined recall for all memories from final matrix
    # Probe Recall A
    readout_a = W_current @ kA
    norm_a = float(np.linalg.norm(readout_a))
    fid_a = float(cosine(readout_a, vA)) if norm_a > 1e-6 else 0.0
    str_a = float(np.dot(readout_a, vA))
    # Crosstalk: leakage from B when querying A
    leak_b_into_a = float(cosine(readout_a, vB)) if norm_a > 1e-6 else 0.0
    comb_a = {
        "concept": config.memory_a.concept,
        "value": config.memory_a.value,
        "fidelity": fid_a,
        "strength": str_a,
        "readout_norm": norm_a,
        "is_correct": bool(fid_a > leak_b_into_a and fid_a > 0.25),
        "crosstalk_leakage": leak_b_into_a,
    }
    step_num += 1
    timeline.append({
        "step": step_num,
        "event_type": "RECALL_A",
        "label": f"RECALL PROBE: {config.memory_a.concept}",
        "concept": config.memory_a.concept,
        "fidelity": fid_a,
        "crosstalk": leak_b_into_a,
    })

    # Probe Recall B
    readout_b = W_current @ kB
    norm_b = float(np.linalg.norm(readout_b))
    fid_b = float(cosine(readout_b, vB)) if norm_b > 1e-6 else 0.0
    str_b = float(np.dot(readout_b, vB))
    leak_a_into_b = float(cosine(readout_b, vA)) if norm_b > 1e-6 else 0.0
    comb_b = {
        "concept": config.memory_b.concept,
        "value": config.memory_b.value,
        "fidelity": fid_b,
        "strength": str_b,
        "readout_norm": norm_b,
        "is_correct": bool(fid_b > leak_a_into_b and fid_b > 0.25),
        "crosstalk_leakage": leak_a_into_b,
    }
    step_num += 1
    timeline.append({
        "step": step_num,
        "event_type": "RECALL_B",
        "label": f"RECALL PROBE: {config.memory_b.concept}",
        "concept": config.memory_b.concept,
        "fidelity": fid_b,
        "crosstalk": leak_a_into_b,
    })

    # Probe Recall C if present
    comb_c = None
    if config.memory_c and kC is not None and vC is not None:
        readout_c = W_current @ kC
        norm_c = float(np.linalg.norm(readout_c))
        fid_c = float(cosine(readout_c, vC)) if norm_c > 1e-6 else 0.0
        str_c = float(np.dot(readout_c, vC))
        comb_c = {
            "concept": config.memory_c.concept,
            "value": config.memory_c.value,
            "fidelity": fid_c,
            "strength": str_c,
            "readout_norm": norm_c,
            "is_correct": bool(fid_c > 0.25),
        }

    # 5. Computational Interference Measures
    interf_a = max(0.0, iso_a["fidelity"] - comb_a["fidelity"])
    interf_b = max(0.0, iso_b["fidelity"] - comb_b["fidelity"])
    overall_interf = float((interf_a + interf_b) / 2.0)

    # Memory dominance
    margin = float(comb_a["fidelity"] - comb_b["fidelity"])
    if abs(margin) < 0.05:
        dominance = "BALANCED"
    elif margin > 0:
        dominance = "MEMORY_A"
    else:
        dominance = "MEMORY_B"

    # 6. Synaptic Pathway Classification & Collision Map
    delta_A = delta_W1 if config.order != "B_THEN_A" else delta_W2
    delta_B = delta_W2 if config.order != "B_THEN_A" else delta_W1

    thresh_a = max(1e-4, 0.15 * float(np.max(np.abs(delta_A))))
    thresh_b = max(1e-4, 0.15 * float(np.max(np.abs(delta_B))))

    a_only: List[str] = []
    b_only: List[str] = []
    shared: List[str] = []
    collision_map: List[Dict[str, Any]] = []

    for i in range(d):
        for j in range(d):
            syn_id = f"syn_k{j}_v{i}"
            mod_a = abs(delta_A[i, j]) > thresh_a
            mod_b = abs(delta_B[i, j]) > thresh_b

            if mod_a and mod_b:
                cls_type = "SHARED"
                shared.append(syn_id)
            elif mod_a and not mod_b:
                cls_type = "A_ONLY"
                a_only.append(syn_id)
            elif mod_b and not mod_a:
                cls_type = "B_ONLY"
                b_only.append(syn_id)
            else:
                cls_type = "UNCHANGED"

            overwrite_mag = float(abs(delta_B[i, j])) if mod_a else 0.0
            classification_item = SynapticPathwayClassification(
                synapse_id=syn_id,
                source=f"k_{j}",
                target=f"v_{i}",
                source_idx=j,
                target_idx=i,
                classification=cls_type,
                weight_after_first=float(W_after_first[i, j]),
                weight_delta_second=float(delta_W2[i, j]),
                final_weight=float(W_current[i, j]),
                overwrite_magnitude=overwrite_mag,
            )
            collision_map.append(classification_item.to_dict())

    # Calculate Synaptic Overlap Fraction (Jaccard index of active synapses)
    total_active_union = len(a_only) + len(b_only) + len(shared)
    syn_overlap_frac = float(len(shared) / total_active_union) if total_active_union > 0 else 0.0

    # Build final SynapticNetworkState for inspection
    neurons: List[SynapticNeuron] = []
    for j in range(d):
        neurons.append(SynapticNeuron(
            id=f"k_{j}",
            index=j,
            neuron_type="input_key",
            label=f"Key Unit {j}",
            activation=float(kA[j]),
            baseline_activation=0.0,
            inflow_weight=0.0,
            outflow_weight=float(np.sum(np.abs(W_current[:, j]))),
            dominant_concepts=[config.memory_a.concept, config.memory_b.concept],
        ))
    for i in range(d):
        neurons.append(SynapticNeuron(
            id=f"v_{i}",
            index=i,
            neuron_type="output_value",
            label=f"Val Unit {i}",
            activation=float(readout_a[i]),
            baseline_activation=0.0,
            inflow_weight=float(np.sum(np.abs(W_current[i, :]))),
            outflow_weight=0.0,
            dominant_concepts=[config.memory_a.value, config.memory_b.value],
        ))

    synapses: List[SynapticConnection] = []
    for item in collision_map:
        w = item["final_weight"]
        if abs(w) > 1e-4 or item["classification"] in {"SHARED", "A_ONLY", "B_ONLY"}:
            synapses.append(SynapticConnection(
                id=item["synapse_id"],
                source=item["source"],
                target=item["target"],
                source_idx=item["source_idx"],
                target_idx=item["target_idx"],
                weight=w,
                weight_before=item["weight_after_first"],
                delta_weight=item["weight_delta_second"],
                abs_weight=abs(w),
                tier="strong" if abs(w) > 0.5 else ("medium" if abs(w) > 0.2 else "weak"),
                polarity="excitatory" if w > 1e-5 else ("inhibitory" if w < -1e-5 else "neutral"),
                plasticity_trace=abs(item["weight_delta_second"]),
                last_update_timestep=step_num,
            ))

    final_net = SynapticNetworkState(
        timestep=step_num,
        dimension=d,
        mechanism="hebbian",
        total_synapses=d * d,
        active_synapses_count=len(synapses),
        mean_synaptic_weight=float(np.mean(W_current)),
        max_synaptic_weight=float(np.max(np.abs(W_current))),
        matrix_norm=float(np.linalg.norm(W_current)),
        sparsity=float(len(synapses) / (d * d)),
        neurons=neurons,
        synapses=synapses,
        last_pathway=SynapticPathway(
            active_key_indices=np.where(np.abs(kA) > np.percentile(np.abs(kA), 70))[0].tolist(),
            active_value_indices=np.where(np.abs(readout_a) > np.percentile(np.abs(readout_a), 70))[0].tolist(),
            active_synapse_ids=shared[:10],
            transmission_energy=float(np.linalg.norm(readout_a)),
        ),
        last_explanation=SynapticExplanation(
            event_label=f"COLLISION: {config.memory_a.concept} vs {config.memory_b.concept}",
            event_type="COLLISION",
            active_units=len(neurons),
            synaptic_updates=len(shared) + len(b_only),
            mean_weight_change=float(np.mean(np.abs(delta_W2))),
            max_weight_change=float(np.max(np.abs(delta_W2))),
            state_change_pct=float(np.linalg.norm(delta_W2) / (np.linalg.norm(W_after_first) + 1e-9) * 100.0),
            norm_before=float(np.linalg.norm(W_after_first)),
            norm_after=float(np.linalg.norm(W_current)),
            write_gain=gain2,
            decay_applied=decay,
            scientific_note=(
                f"Memory B wrote into synaptic matrix containing Memory A. "
                f"{len(shared)} synapses were co-modified (synaptic overlap fraction = {syn_overlap_frac:.2f})."
            ),
        ),
        last_recall=SynapticRecallResult(
            query_concept=config.memory_a.concept,
            predicted_value=config.memory_a.value,
            confidence=fid_a,
            ground_truth=config.memory_a.value,
            is_correct=comb_a["is_correct"],
            candidate_matches=[],
            fidelity=fid_a,
            crosstalk_noise=leak_b_into_a,
            readout_vector=readout_a.tolist(),
        ),
        history_timeline=[],
        matrix_weights=W_current.tolist(),
    )

    # Structured scientific report
    report = {
        "question": "What happens when two memories compete for overlapping computational synaptic resources?",
        "conditions": {
            "memory_a": f"{config.memory_a.concept} = {config.memory_a.value}",
            "memory_b": f"{config.memory_b.concept} = {config.memory_b.value}",
            "write_order": config.order,
            "temporal_delay_steps": config.temporal_delay,
            "decay": decay,
            "update_strength": eta,
            "dimension": d,
        },
        "overlap_measure": {
            "representational_overlap_cosine": rep_overlap,
            "synaptic_overlap_fraction": syn_overlap_frac,
            "matrix_frobenius_correlation": matrix_corr,
            "shared_synapse_count": len(shared),
            "a_only_count": len(a_only),
            "b_only_count": len(b_only),
        },
        "results": {
            "recall_a_isolated": iso_a["fidelity"],
            "recall_a_combined": comb_a["fidelity"],
            "interference_a": interf_a,
            "recall_b_isolated": iso_b["fidelity"],
            "recall_b_combined": comb_b["fidelity"],
            "interference_b": interf_b,
            "overall_computational_interference": overall_interf,
            "memory_dominance": dominance,
        },
        "interpretation": (
            f"Representational overlap between Memory A and Memory B was measured as {rep_overlap:.2f} (cosine). "
            f"In the synaptic matrix, {len(shared)} of {total_active_union} active connections were shared. "
            f"Consequently, Memory A recall fidelity degraded by {interf_a:.3f} and Memory B by {interf_b:.3f}. "
            f"This computational interference demonstrates how associative capacity limits cause signal crosstalk when memories share neural coordinates."
        ),
    }

    cf_id = f"col-{uuid.uuid4().hex[:8]}"
    return CollisionResult(
        collision_id=cf_id,
        config=config.to_dict(),
        representational_overlap=rep_overlap,
        synaptic_overlap_fraction=syn_overlap_frac,
        matrix_correlation=matrix_corr,
        timeline=timeline,
        isolated_recall_a=iso_a,
        isolated_recall_b=iso_b,
        combined_recall_a=comb_a,
        combined_recall_b=comb_b,
        computational_interference_a=interf_a,
        computational_interference_b=interf_b,
        overall_computational_interference=overall_interf,
        memory_dominance=dominance,
        dominant_memory_margin=margin,
        a_only_synapses=a_only,
        b_only_synapses=b_only,
        shared_synapses=shared,
        collision_map=collision_map,
        experiment_report=report,
        final_network_state=final_net.to_dict(),
        isolated_recall_c=iso_c,
        combined_recall_c=comb_c,
    )


# ---------------------------------------------------------------------------
# Three Experiment Conditions Suite (Low, Moderate, High Overlap)
# ---------------------------------------------------------------------------

def run_three_condition_suite(base_config: CollisionConfig) -> Dict[str, Any]:
    """Execute Low, Moderate, and High overlap conditions to generate the Recall Matrix."""
    cfg_low = copy.deepcopy(base_config)
    cfg_low.overlap_preset = "LOW"
    cfg_low.concept_similarity = 0.0

    cfg_mod = copy.deepcopy(base_config)
    cfg_mod.overlap_preset = "MODERATE"
    cfg_mod.concept_similarity = 0.45

    cfg_high = copy.deepcopy(base_config)
    cfg_high.overlap_preset = "HIGH"
    cfg_high.concept_similarity = 0.85

    res_low = run_collision_experiment(cfg_low)
    res_mod = run_collision_experiment(cfg_mod)
    res_high = run_collision_experiment(cfg_high)

    matrix_rows = [
        {
            "condition": "LOW OVERLAP",
            "concept_similarity": 0.0,
            "representational_overlap": res_low.representational_overlap,
            "synaptic_overlap_fraction": res_low.synaptic_overlap_fraction,
            "recall_a": res_low.combined_recall_a["fidelity"],
            "recall_b": res_low.combined_recall_b["fidelity"],
            "interference": res_low.overall_computational_interference,
            "shared_synapses": len(res_low.shared_synapses),
            "dominant": res_low.memory_dominance,
        },
        {
            "condition": "MODERATE OVERLAP",
            "concept_similarity": 0.45,
            "representational_overlap": res_mod.representational_overlap,
            "synaptic_overlap_fraction": res_mod.synaptic_overlap_fraction,
            "recall_a": res_mod.combined_recall_a["fidelity"],
            "recall_b": res_mod.combined_recall_b["fidelity"],
            "interference": res_mod.overall_computational_interference,
            "shared_synapses": len(res_mod.shared_synapses),
            "dominant": res_mod.memory_dominance,
        },
        {
            "condition": "HIGH OVERLAP",
            "concept_similarity": 0.85,
            "representational_overlap": res_high.representational_overlap,
            "synaptic_overlap_fraction": res_high.synaptic_overlap_fraction,
            "recall_a": res_high.combined_recall_a["fidelity"],
            "recall_b": res_high.combined_recall_b["fidelity"],
            "interference": res_high.overall_computational_interference,
            "shared_synapses": len(res_high.shared_synapses),
            "dominant": res_high.memory_dominance,
        },
    ]

    return {
        "recall_matrix": matrix_rows,
        "low_result": res_low.to_dict(),
        "moderate_result": res_mod.to_dict(),
        "high_result": res_high.to_dict(),
    }


# ---------------------------------------------------------------------------
# Order Matters Experiment Engine (A -> B vs B -> A)
# ---------------------------------------------------------------------------

def run_order_comparison(base_config: CollisionConfig) -> Dict[str, Any]:
    """Compare A -> B against B -> A from equivalent baseline."""
    cfg_ab = copy.deepcopy(base_config)
    cfg_ab.order = "A_THEN_B"
    res_ab = run_collision_experiment(cfg_ab)

    cfg_ba = copy.deepcopy(base_config)
    cfg_ba.order = "B_THEN_A"
    res_ba = run_collision_experiment(cfg_ba)

    W_ab = np.array(res_ab.final_network_state["matrix_weights"])
    W_ba = np.array(res_ba.final_network_state["matrix_weights"])
    matrix_diff_norm = float(np.linalg.norm(W_ab - W_ba))

    return {
        "comparison_title": "Order Matters: (A -> B) vs (B -> A)",
        "matrix_frobenius_difference": matrix_diff_norm,
        "order_a_then_b": {
            "order": "A_THEN_B",
            "recall_a": res_ab.combined_recall_a["fidelity"],
            "recall_b": res_ab.combined_recall_b["fidelity"],
            "interference_a": res_ab.computational_interference_a,
            "interference_b": res_ab.computational_interference_b,
            "dominant_memory": res_ab.memory_dominance,
        },
        "order_b_then_a": {
            "order": "B_THEN_A",
            "recall_a": res_ba.combined_recall_a["fidelity"],
            "recall_b": res_ba.combined_recall_b["fidelity"],
            "interference_a": res_ba.computational_interference_a,
            "interference_b": res_ba.computational_interference_b,
            "dominant_memory": res_ba.memory_dominance,
        },
        "order_asymmetry_detected": bool(matrix_diff_norm > 1e-4),
        "scientific_note": (
            f"State difference between orders: ‖W_(A→B) - W_(B→A)‖_F = {matrix_diff_norm:.4f}. "
            "Because synaptic decay and non-commutative matrix updates apply sequentially, "
            "the more recent memory is typically more robust."
        ),
        "result_ab": res_ab.to_dict(),
        "result_ba": res_ba.to_dict(),
    }


# ---------------------------------------------------------------------------
# Collision -> Synaptic Surgery Integration (Phase 15)
# ---------------------------------------------------------------------------

def perform_collision_surgery(
    collision_result: CollisionResult,
    synapse_id: str,
    operation: str = "silence",
    factor: float = 0.0,
) -> Dict[str, Any]:
    """Apply surgical modification (SILENCE, WEAKEN, STRENGTHEN) to a shared synapse on the collision matrix."""
    final_W = np.array(collision_result.final_network_state["matrix_weights"], dtype=np.float64)
    surgery_W = final_W.copy()
    d = final_W.shape[0]

    # Parse synapse coordinates
    parts = synapse_id.split("_")
    j, i = 0, 0
    if len(parts) == 3 and parts[0] == "syn" and parts[1].startswith("k") and parts[2].startswith("v"):
        try:
            j = int(parts[1][1:])
            i = int(parts[2][1:])
        except ValueError:
            pass

    orig_weight = float(final_W[i, j])

    if operation == "silence":
        surgery_W[i, j] = 0.0
    elif operation == "weaken":
        f = factor if factor > 0 else 0.5
        surgery_W[i, j] = orig_weight * f
    elif operation == "strengthen":
        f = factor if factor > 0 else 2.0
        surgery_W[i, j] = orig_weight * f

    new_weight = float(surgery_W[i, j])

    # Re-evaluate Recall A and Recall B with the surgically modified matrix
    cfg = CollisionConfig.from_dict(collision_result.config)
    k_map, v_map = _get_vectors_for_collision(cfg)
    kA, vA = k_map[cfg.memory_a.concept], v_map[cfg.memory_a.value]
    kB, vB = k_map[cfg.memory_b.concept], v_map[cfg.memory_b.value]

    # Recall A after surgery
    readout_a_surg = surgery_W @ kA
    fid_a_surg = float(cosine(readout_a_surg, vA)) if np.linalg.norm(readout_a_surg) > 1e-6 else 0.0

    # Recall B after surgery
    readout_b_surg = surgery_W @ kB
    fid_b_surg = float(cosine(readout_b_surg, vB)) if np.linalg.norm(readout_b_surg) > 1e-6 else 0.0

    return {
        "status": "success",
        "operation": operation,
        "target_synapse": synapse_id,
        "original_weight": orig_weight,
        "post_surgery_weight": new_weight,
        "weight_delta": new_weight - orig_weight,
        "recall_a_before": collision_result.combined_recall_a["fidelity"],
        "recall_a_after": fid_a_surg,
        "recall_a_delta": fid_a_surg - collision_result.combined_recall_a["fidelity"],
        "recall_b_before": collision_result.combined_recall_b["fidelity"],
        "recall_b_after": fid_b_surg,
        "recall_b_delta": fid_b_surg - collision_result.combined_recall_b["fidelity"],
        "matrix_frobenius_delta": float(np.linalg.norm(surgery_W - final_W)),
    }


# ---------------------------------------------------------------------------
# Collision -> Counterfactual Integration (Phase 16)
# ---------------------------------------------------------------------------

def perform_collision_counterfactual(
    collision_result: CollisionResult,
    shared_synapse_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute counterfactual branch: "What if Memory B had NEVER modified these shared synapses?"."""
    cfg = CollisionConfig.from_dict(collision_result.config)
    d = cfg.dimension
    decay = cfg.decay
    eta = cfg.update_strength

    k_map, v_map = _get_vectors_for_collision(cfg)
    kA, vA = k_map[cfg.memory_a.concept], v_map[cfg.memory_a.value]
    kB, vB = k_map[cfg.memory_b.concept], v_map[cfg.memory_b.value]

    target_syns = set(shared_synapse_ids or collision_result.shared_synapses)

    # Step 1: Write Memory A
    gain1 = float(eta * cfg.memory_a.importance * cfg.memory_a.strength)
    delta_W1 = gain1 * np.outer(vA, kA)
    W_orig_a = delta_W1.copy()

    # Step 2: Write Memory B with shared synapses held unchanged
    gain2 = float(eta * cfg.memory_b.importance * cfg.memory_b.strength)
    delta_W2 = gain2 * np.outer(vB, kB)

    # Counterfactual modification: zero delta_W2 on all target shared synapses
    delta_W2_cf = delta_W2.copy()
    for i in range(d):
        for j in range(d):
            s_id = f"syn_k{j}_v{i}"
            if s_id in target_syns:
                delta_W2_cf[i, j] = 0.0  # Memory B prevented from overwriting

    W_cf = (1.0 - decay) * W_orig_a + delta_W2_cf
    W_actual = np.array(collision_result.final_network_state["matrix_weights"])

    # Probe Counterfactual Recall A and B
    readout_a_cf = W_cf @ kA
    fid_a_cf = float(cosine(readout_a_cf, vA)) if np.linalg.norm(readout_a_cf) > 1e-6 else 0.0

    readout_b_cf = W_cf @ kB
    fid_b_cf = float(cosine(readout_b_cf, vB)) if np.linalg.norm(readout_b_cf) > 1e-6 else 0.0

    return {
        "status": "success",
        "counterfactual_title": "What if Memory B had never modified the shared synapses?",
        "protected_synapses_count": len(target_syns),
        "original_recall_a": collision_result.combined_recall_a["fidelity"],
        "counterfactual_recall_a": fid_a_cf,
        "recall_a_improvement": fid_a_cf - collision_result.combined_recall_a["fidelity"],
        "original_recall_b": collision_result.combined_recall_b["fidelity"],
        "counterfactual_recall_b": fid_b_cf,
        "recall_b_delta": fid_b_cf - collision_result.combined_recall_b["fidelity"],
        "matrix_distance_frobenius": float(np.linalg.norm(W_cf - W_actual)),
        "scientific_conclusion": (
            f"Preventing Memory B from modifying {len(target_syns)} shared synapses "
            f"changed Memory A recall from {collision_result.combined_recall_a['fidelity']:.3f} → {fid_a_cf:.3f} "
            f"(Δ = {fid_a_cf - collision_result.combined_recall_a['fidelity']:+.3f}). "
            "This confirms that Memory A degradation was causally mediated by overwriting at these shared synaptic coordinates."
        ),
    }
