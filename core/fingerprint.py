"""Memory Genome & Synaptic Fingerprint Engine (Phase 20).

Provides a computational fingerprint describing HOW each memory is represented
inside the live Hebbian associative memory model.

Core Principles:
1. Grounded in actual linear algebraic model state (W, ΔW, k, v, v̂).
2. Contrasts Surface Input Similarity against Internal Representation Similarity.
3. Quantifies shared vs unique synaptic allocations (Phase 17).
4. Tracks genome evolution across temporal steps (Phase 19).
5. Supports mutation and remeasurement under Synaptic Surgery (Phase 15)
   and Counterfactual interventions (Phase 16).
6. Computes 2D distance maps (MDS/PCA) and detects Representational Outliers.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_concept_vector, encode_value_vector
from .memory import Memory, TextMemory, encode_memory, similarity
from .synaptic import SynapticBrain, SynapticNetworkState, SynapticRecallResult
from .vectors import cosine


@dataclass
class SynapticFingerprint:
    """Computational fingerprint of an encoded memory on the synaptic substrate."""

    memory_id: str
    concept: str
    value: str
    timestep: int
    dimension: int

    # Active Units (where activation > threshold)
    active_key_units: List[int]
    active_value_units: List[int]
    active_unit_count: int

    # Modified Synapses where |ΔW_ij| > threshold
    modified_synapses: List[Tuple[int, int, float]]  # (row, col, delta_weight)
    modified_synapse_count: int

    # Strength Distribution of contributing weights
    synaptic_strength_stats: Dict[str, float]  # mean, std, min, max, l2_norm, frobenius_contribution

    # Activation Distribution
    activation_distribution: Dict[str, float]  # mean, variance, sparsity, max_val

    # Sparsity
    sparsity: float  # unit sparsity percentage

    # Recall Performance
    recall_performance: Dict[str, float]  # fidelity, crosstalk_noise, confidence

    # Normalized Flattened Representation Signature (for distance computations)
    representation_vector: List[float]

    # Derivation Metadata
    derivation_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "concept": self.concept,
            "value": self.value,
            "timestep": int(self.timestep),
            "dimension": int(self.dimension),
            "active_key_units": [int(i) for i in self.active_key_units],
            "active_value_units": [int(i) for i in self.active_value_units],
            "active_unit_count": int(self.active_unit_count),
            "modified_synapses": [
                [int(r), int(c), round(float(w), 6)] for r, c, w in self.modified_synapses
            ],
            "modified_synapse_count": int(self.modified_synapse_count),
            "synaptic_strength_stats": {
                k: float(v) for k, v in self.synaptic_strength_stats.items()
            },
            "activation_distribution": {
                k: float(v) for k, v in self.activation_distribution.items()
            },
            "sparsity": float(self.sparsity),
            "recall_performance": {
                k: float(v) for k, v in self.recall_performance.items()
            },
            "representation_vector": [round(float(x), 6) for x in self.representation_vector],
            "derivation_metadata": self.derivation_metadata,
        }


@dataclass
class FingerprintComparison:
    """Exact computational comparison between two memory fingerprints."""

    memory_a_id: str
    memory_b_id: str
    concept_a: str
    concept_b: str
    surface_similarity: float
    internal_similarity: float
    synaptic_overlap_jaccard: float
    shared_synapses: List[Tuple[int, int, float, float]]  # (row, col, delta_a, delta_b)
    a_only_synapses: List[Tuple[int, int, float]]
    b_only_synapses: List[Tuple[int, int, float]]
    recall_divergence: float
    similarity_discrepancy: float  # |surface - internal|
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_a_id": self.memory_a_id,
            "memory_b_id": self.memory_b_id,
            "concept_a": self.concept_a,
            "concept_b": self.concept_b,
            "surface_similarity": float(self.surface_similarity),
            "internal_similarity": float(self.internal_similarity),
            "synaptic_overlap_jaccard": float(self.synaptic_overlap_jaccard),
            "shared_synapses": [
                [int(r), int(c), round(float(wa), 6), round(float(wb), 6)]
                for r, c, wa, wb in self.shared_synapses
            ],
            "a_only_synapses": [
                [int(r), int(c), round(float(w), 6)] for r, c, w in self.a_only_synapses
            ],
            "b_only_synapses": [
                [int(r), int(c), round(float(w), 6)] for r, c, w in self.b_only_synapses
            ],
            "recall_divergence": float(self.recall_divergence),
            "similarity_discrepancy": float(self.similarity_discrepancy),
            "explanation": self.explanation,
        }


@dataclass
class FingerprintEvolution:
    """Historical progression of a memory's fingerprint across temporal steps."""

    memory_id: str
    concept: str
    timesteps: List[int]
    fingerprints: List[SynapticFingerprint]
    active_unit_trajectory: List[int]
    modified_synapse_trajectory: List[int]
    fidelity_trajectory: List[float]
    frobenius_contribution_trajectory: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "concept": self.concept,
            "timesteps": [int(t) for t in self.timesteps],
            "fingerprints": [fp.to_dict() for fp in self.fingerprints],
            "active_unit_trajectory": [int(x) for x in self.active_unit_trajectory],
            "modified_synapse_trajectory": [int(x) for x in self.modified_synapse_trajectory],
            "fidelity_trajectory": [float(x) for x in self.fidelity_trajectory],
            "frobenius_contribution_trajectory": [
                float(x) for x in self.frobenius_contribution_trajectory
            ],
        }


@dataclass
class MemoryDistancePoint:
    """A projected point in the 2D memory distance space."""

    memory_id: str
    concept: str
    value: str
    x: float
    y: float
    active_units: int
    recall_fidelity: float
    is_outlier: bool
    outlier_reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "concept": self.concept,
            "value": self.value,
            "x": round(float(self.x), 6),
            "y": round(float(self.y), 6),
            "active_units": int(self.active_units),
            "recall_fidelity": float(self.recall_fidelity),
            "is_outlier": bool(self.is_outlier),
            "outlier_reasons": self.outlier_reasons,
        }


@dataclass
class MemoryDistanceMap:
    """2D projection of memories derived from pairwise representation vectors."""

    points: List[MemoryDistancePoint]
    projection_method: str  # "PCA_2D" or "MDS_2D"
    variance_explained: Optional[float]
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "projection_method": self.projection_method,
            "variance_explained": float(self.variance_explained)
            if self.variance_explained is not None
            else None,
            "description": self.description,
        }


@dataclass
class MemoryBranchNode:
    """A node in the visual memory family tree tracing branches across experiments."""

    node_id: str
    label: str
    branch_type: str  # "ORIGINAL" | "COLLISION" | "SURGERY" | "COUNTERFACTUAL"
    step: int
    parent_id: Optional[str]
    fingerprint: Optional[SynapticFingerprint]
    children: List["MemoryBranchNode"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "branch_type": self.branch_type,
            "step": int(self.step),
            "parent_id": self.parent_id,
            "fingerprint": self.fingerprint.to_dict() if self.fingerprint else None,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class OutlierReport:
    """Evidence-based evaluation of representational outliers."""

    memory_id: str
    concept: str
    is_outlier: bool
    z_scores: Dict[str, float]
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "concept": self.concept,
            "is_outlier": bool(self.is_outlier),
            "z_scores": {k: float(v) for k, v in self.z_scores.items()},
            "reasons": self.reasons,
        }


@dataclass
class FingerprintChallenge:
    """Predictive learning challenge for students."""

    challenge_id: str
    challenge_type: str  # "MOST_SIMILAR_INTERNAL" | "MOST_CHANGED_INTERFERENCE"
    prompt: str
    target_memory: str
    options: List[str]
    correct_option: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "challenge_type": self.challenge_type,
            "prompt": self.prompt,
            "target_memory": self.target_memory,
            "options": self.options,
            "correct_option": self.correct_option,
            "explanation": self.explanation,
        }


# =====================================================================
# Core Computational Engine: MemoryGenomeEngine
# =====================================================================


class MemoryGenomeEngine:
    """Computes, analyzes, and compares memory fingerprints directly from SynapticBrain."""

    def __init__(self, activation_threshold: float = 0.05, synapse_threshold: float = 0.01):
        self.activation_threshold = activation_threshold
        self.synapse_threshold = synapse_threshold

    def compute_fingerprint(
        self,
        brain: SynapticBrain,
        concept: str,
        value: Optional[str] = None,
        step: Optional[int] = None,
    ) -> SynapticFingerprint:
        """Derive an empirical fingerprint for a memory concept on the given SynapticBrain."""
        d = brain.d
        seed = brain.seed
        timestep = step if step is not None else brain.timestep

        # 1. Compute Key and Value vectors
        k_vec = encode_concept_vector(concept, seed, d)
        target_val = value
        if not target_val:
            # Check library
            for m in brain.library:
                if m.concept.strip().lower() == concept.strip().lower():
                    target_val = m.value
                    break
            if not target_val:
                target_val = f"val_{concept}"

        v_vec = encode_value_vector(target_val, seed, d)

        # 2. Extract Active Units
        active_k = np.where(np.abs(k_vec) >= self.activation_threshold)[0].tolist()
        active_v = np.where(np.abs(v_vec) >= self.activation_threshold)[0].tolist()
        active_unit_count = len(active_k) + len(active_v)

        # 3. Calculate Synaptic Outer-Product Update ΔW = η · (v ⊗ k)
        gain = float(brain.update_strength * brain.memory_strength)
        delta_W = gain * np.outer(v_vec, k_vec)

        # 4. Find Modified Synapses
        mod_indices = np.where(np.abs(delta_W) >= self.synapse_threshold)
        modified_synapses: List[Tuple[int, int, float]] = []
        for r, c in zip(mod_indices[0], mod_indices[1]):
            modified_synapses.append((int(r), int(c), float(delta_W[r, c])))

        # Sort modified synapses by absolute magnitude descending
        modified_synapses.sort(key=lambda s: abs(s[2]), reverse=True)
        modified_synapse_count = len(modified_synapses)

        # 5. Synaptic Strength Statistics
        frob_contrib = float(np.linalg.norm(delta_W))
        all_deltas = delta_W.flatten()
        strength_stats = {
            "mean": float(np.mean(all_deltas)),
            "std": float(np.std(all_deltas)),
            "min": float(np.min(all_deltas)),
            "max": float(np.max(all_deltas)),
            "l2_norm": frob_contrib,
            "frobenius_contribution": frob_contrib,
        }

        # 6. Activation Distribution
        all_acts = np.concatenate([k_vec, v_vec])
        sparsity = float(np.mean(np.abs(all_acts) < self.activation_threshold))
        act_dist = {
            "mean": float(np.mean(all_acts)),
            "variance": float(np.var(all_acts)),
            "max_val": float(np.max(np.abs(all_acts))),
            "sparsity": sparsity,
        }

        # 7. Recall Performance
        # Readout from current W: v̂ = W @ k
        readout = brain.W @ k_vec
        readout_norm = float(np.linalg.norm(readout))
        if readout_norm > 1e-9:
            fidelity = max(0.0, float(similarity(readout, v_vec, measure="cosine")))
            crosstalk = float(np.linalg.norm(readout - v_vec))
        else:
            fidelity = 0.0
            crosstalk = float(np.linalg.norm(v_vec))

        recall_perf = {
            "fidelity": fidelity,
            "crosstalk_noise": crosstalk,
            "confidence": fidelity,
        }

        # 8. Normalized Representation Vector (Flattened unit outer product)
        rep_norm = frob_contrib if frob_contrib > 1e-9 else 1.0
        normalized_rep = (delta_W / rep_norm).flatten().tolist()

        mem_id = f"fp_{concept.lower().replace(' ', '_')}_{timestep}"

        return SynapticFingerprint(
            memory_id=mem_id,
            concept=concept,
            value=target_val,
            timestep=timestep,
            dimension=d,
            active_key_units=active_k,
            active_value_units=active_v,
            active_unit_count=active_unit_count,
            modified_synapses=modified_synapses,
            modified_synapse_count=modified_synapse_count,
            synaptic_strength_stats=strength_stats,
            activation_distribution=act_dist,
            sparsity=sparsity,
            recall_performance=recall_perf,
            representation_vector=normalized_rep,
            derivation_metadata={
                "formula": "ΔW = η · (v ⊗ k)",
                "seed": seed,
                "update_strength": brain.update_strength,
                "decay_rate": brain.decay,
                "activation_threshold": self.activation_threshold,
                "synapse_threshold": self.synapse_threshold,
            },
        )

    def compare_fingerprints(
        self,
        fp_a: SynapticFingerprint,
        fp_b: SynapticFingerprint,
        seed: int = 42,
    ) -> FingerprintComparison:
        """Compare two memory fingerprints on surface and internal dimensions."""
        d = fp_a.dimension

        # 1. Surface Similarity: Cosine similarity of input cues k_A and k_B
        k_a = encode_concept_vector(fp_a.concept, seed, d)
        k_b = encode_concept_vector(fp_b.concept, seed, d)
        surface_sim = float(cosine(k_a, k_b))

        # 2. Internal Similarity: Cosine similarity of normalized representation vectors
        rep_a = np.array(fp_a.representation_vector, dtype=np.float64)
        rep_b = np.array(fp_b.representation_vector, dtype=np.float64)
        internal_sim = float(cosine(rep_a, rep_b))

        # 3. Synaptic Overlap: Partition modified synapses into A-only, B-only, and Shared
        syn_dict_a = {(r, c): w for r, c, w in fp_a.modified_synapses}
        syn_dict_b = {(r, c): w for r, c, w in fp_b.modified_synapses}

        all_keys = set(syn_dict_a.keys()).union(set(syn_dict_b.keys()))
        shared_keys = set(syn_dict_a.keys()).intersection(set(syn_dict_b.keys()))

        jaccard = len(shared_keys) / len(all_keys) if all_keys else 0.0

        shared_synapses: List[Tuple[int, int, float, float]] = [
            (r, c, syn_dict_a[(r, c)], syn_dict_b[(r, c)]) for r, c in shared_keys
        ]
        a_only_synapses: List[Tuple[int, int, float]] = [
            (r, c, syn_dict_a[(r, c)]) for r, c in syn_dict_a if (r, c) not in shared_keys
        ]
        b_only_synapses: List[Tuple[int, int, float]] = [
            (r, c, syn_dict_b[(r, c)]) for r, c in syn_dict_b if (r, c) not in shared_keys
        ]

        recall_divergence = abs(
            fp_a.recall_performance["fidelity"] - fp_b.recall_performance["fidelity"]
        )
        discrepancy = abs(surface_sim - internal_sim)

        # 4. Generate Scientific Explanation
        if discrepancy > 0.35:
            explanation = (
                f"Surface-to-internal divergence observed. While surface similarity is {surface_sim:.3f}, "
                f"internal synaptic similarity is {internal_sim:.3f} (Δ={discrepancy:.3f}). "
                f"Memories share {len(shared_synapses)} synaptic pathways ({jaccard * 100:.1f}% Jaccard overlap)."
            )
        elif internal_sim > 0.7:
            explanation = (
                f"High internal convergence. Memories share {len(shared_synapses)} synapses "
                f"with representation similarity of {internal_sim:.3f}."
            )
        else:
            explanation = (
                f"Independent representations. Surface similarity is {surface_sim:.3f} and "
                f"internal synaptic similarity is {internal_sim:.3f}."
            )

        return FingerprintComparison(
            memory_a_id=fp_a.memory_id,
            memory_b_id=fp_b.memory_id,
            concept_a=fp_a.concept,
            concept_b=fp_b.concept,
            surface_similarity=surface_sim,
            internal_similarity=internal_sim,
            synaptic_overlap_jaccard=jaccard,
            shared_synapses=shared_synapses,
            a_only_synapses=a_only_synapses,
            b_only_synapses=b_only_synapses,
            recall_divergence=recall_divergence,
            similarity_discrepancy=discrepancy,
            explanation=explanation,
        )

    def compare_surface_vs_internal(
        self,
        brain: SynapticBrain,
        concepts: List[str],
    ) -> List[FingerprintComparison]:
        """Pairwise comparison of surface cue similarity vs internal representation similarity."""
        fps = [self.compute_fingerprint(brain, c) for c in concepts]
        comparisons: List[FingerprintComparison] = []
        for i in range(len(fps)):
            for j in range(i + 1, len(fps)):
                comparisons.append(self.compare_fingerprints(fps[i], fps[j], seed=brain.seed))
        return comparisons

    def track_evolution(
        self,
        snapshots_brain: List[SynapticBrain],
        concept: str,
    ) -> FingerprintEvolution:
        """Track how a concept's fingerprint evolves through a sequence of brain states."""
        timesteps: List[int] = []
        fingerprints: List[SynapticFingerprint] = []
        active_units: List[int] = []
        mod_synapses: List[int] = []
        fidelities: List[float] = []
        frob_contribs: List[float] = []

        for b in snapshots_brain:
            fp = self.compute_fingerprint(b, concept)
            timesteps.append(b.timestep)
            fingerprints.append(fp)
            active_units.append(fp.active_unit_count)
            mod_synapses.append(fp.modified_synapse_count)
            fidelities.append(fp.recall_performance["fidelity"])
            frob_contribs.append(fp.synaptic_strength_stats["frobenius_contribution"])

        return FingerprintEvolution(
            memory_id=fingerprints[0].memory_id if fingerprints else f"fp_{concept}_evol",
            concept=concept,
            timesteps=timesteps,
            fingerprints=fingerprints,
            active_unit_trajectory=active_units,
            modified_synapse_trajectory=mod_synapses,
            fidelity_trajectory=fidelities,
            frobenius_contribution_trajectory=frob_contribs,
        )

    def run_cloning_experiment(
        self,
        seed: int = 42,
        dimension: int = 16,
        target_concept: str = "Concept Alpha",
        target_value: str = "Value Alpha",
        intervening_concept: str = "Intervening Beta",
        intervening_value: str = "Value Beta",
    ) -> Dict[str, Any]:
        """Run Cloning Stability experiment:

        Capture fingerprint of A -> introduce new information -> recall A -> capture fingerprint again.
        """
        brain = SynapticBrain(seed=seed, d=dimension, update_strength=0.3, decay=0.02)

        # 1. Write Memory A
        brain.write(target_concept, target_value)
        fp_before = self.compute_fingerprint(brain, target_concept, target_value)

        # 2. Introduce Intervening Information
        brain.write(intervening_concept, intervening_value)

        # 3. Recall Memory A
        brain.recall(target_concept, expected_value=target_value)
        fp_after = self.compute_fingerprint(brain, target_concept, target_value)

        # 4. Compare fingerprints
        comp = self.compare_fingerprints(fp_before, fp_after, seed=seed)

        return {
            "target_concept": target_concept,
            "fingerprint_before": fp_before.to_dict(),
            "fingerprint_after": fp_after.to_dict(),
            "comparison": comp.to_dict(),
            "stability_conclusion": (
                f"Recall fidelity shifted from {fp_before.recall_performance['fidelity']:.3f} "
                f"to {fp_after.recall_performance['fidelity']:.3f}. "
                f"Internal representation similarity: {comp.internal_similarity:.3f}."
            ),
        }

    def run_collision_mutation(
        self,
        seed: int = 42,
        dimension: int = 16,
        concept_a: str = "Memory A",
        value_a: str = "Target A",
        concept_b: str = "Memory B (Comp)",
        value_b: str = "Target B",
    ) -> Dict[str, Any]:
        """Run Collision Mutation experiment: A -> B -> A recall."""
        brain = SynapticBrain(seed=seed, d=dimension, update_strength=0.4, decay=0.02)

        # Write A
        brain.write(concept_a, value_a)
        fp_a_initial = self.compute_fingerprint(brain, concept_a, value_a)

        # Write B (overlapping or competing)
        brain.write(concept_b, value_b)
        fp_b = self.compute_fingerprint(brain, concept_b, value_b)

        # Recall A
        brain.recall(concept_a, expected_value=value_a)
        fp_a_mutated = self.compute_fingerprint(brain, concept_a, value_a)

        comp = self.compare_fingerprints(fp_a_initial, fp_a_mutated, seed=seed)

        return {
            "concept_a": concept_a,
            "concept_b": concept_b,
            "fingerprint_a_before": fp_a_initial.to_dict(),
            "fingerprint_b": fp_b.to_dict(),
            "fingerprint_a_after_collision": fp_a_mutated.to_dict(),
            "mutation_comparison": comp.to_dict(),
            "interpretation": (
                f"Computational visualization: Competing write introduced interference. "
                f"Fidelity dropped by {(fp_a_initial.recall_performance['fidelity'] - fp_a_mutated.recall_performance['fidelity']):.3f}. "
                f"Active units changed from {fp_a_initial.active_unit_count} to {fp_a_mutated.active_unit_count}."
            ),
        }

    def run_surgery_and_remeasure(
        self,
        seed: int = 42,
        dimension: int = 16,
        concept: str = "Memory Surgery Test",
        value: str = "Value Surgery",
        target_synapse: Tuple[int, int] = (0, 0),
        new_weight: float = 0.0,
    ) -> Dict[str, Any]:
        """Select a contributing synapse, ablate or modify it, and remeasure fingerprint."""
        brain = SynapticBrain(seed=seed, d=dimension, update_strength=0.35, decay=0.01)
        brain.write(concept, value)
        fp_before = self.compute_fingerprint(brain, concept, value)

        # Apply surgery
        r, c = target_synapse
        prev_w = float(brain.W[r, c])
        brain.W[r, c] = new_weight

        # Re-recall
        brain.recall(concept, expected_value=value)
        fp_after = self.compute_fingerprint(brain, concept, value)

        comp = self.compare_fingerprints(fp_before, fp_after, seed=seed)

        return {
            "concept": concept,
            "target_synapse": [r, c],
            "weight_before": prev_w,
            "weight_after": new_weight,
            "fingerprint_before": fp_before.to_dict(),
            "fingerprint_after": fp_after.to_dict(),
            "comparison": comp.to_dict(),
            "recall_fidelity_before": fp_before.recall_performance["fidelity"],
            "recall_fidelity_after": fp_after.recall_performance["fidelity"],
        }

    def run_counterfactual_comparison(
        self,
        seed: int = 42,
        dimension: int = 16,
        concept: str = "Memory CF",
        value: str = "Value CF",
        cf_update_strength: float = 0.05,
    ) -> Dict[str, Any]:
        """Original Memory vs Counterfactual Memory under altered plasticity."""
        # Original Brain
        brain_orig = SynapticBrain(seed=seed, d=dimension, update_strength=0.4, decay=0.01)
        brain_orig.write(concept, value)
        brain_orig.recall(concept, expected_value=value)
        fp_orig = self.compute_fingerprint(brain_orig, concept, value)

        # Counterfactual Brain
        brain_cf = SynapticBrain(seed=seed, d=dimension, update_strength=cf_update_strength, decay=0.01)
        brain_cf.write(concept, value)
        brain_cf.recall(concept, expected_value=value)
        fp_cf = self.compute_fingerprint(brain_cf, concept, value)

        comp = self.compare_fingerprints(fp_orig, fp_cf, seed=seed)

        return {
            "concept": concept,
            "original_fingerprint": fp_orig.to_dict(),
            "counterfactual_fingerprint": fp_cf.to_dict(),
            "comparison": comp.to_dict(),
            "divergence_summary": (
                f"What-if η={cf_update_strength:.2f} instead of 0.40: "
                f"Fidelity changed from {fp_orig.recall_performance['fidelity']:.3f} to {fp_cf.recall_performance['fidelity']:.3f}. "
                f"Internal representation similarity: {comp.internal_similarity:.3f}."
            ),
        }

    def compute_distance_map(
        self,
        fingerprints: List[SynapticFingerprint],
    ) -> MemoryDistanceMap:
        """Compute a 2D projection of memories via Principal Component Analysis (PCA)

        on the normalized representation vectors.
        """
        if not fingerprints:
            return MemoryDistanceMap(points=[], projection_method="PCA_2D", variance_explained=0.0, description="Empty")

        if len(fingerprints) == 1:
            pt = MemoryDistancePoint(
                memory_id=fingerprints[0].memory_id,
                concept=fingerprints[0].concept,
                value=fingerprints[0].value,
                x=0.0,
                y=0.0,
                active_units=fingerprints[0].active_unit_count,
                recall_fidelity=fingerprints[0].recall_performance["fidelity"],
                is_outlier=False,
                outlier_reasons=[],
            )
            return MemoryDistanceMap(points=[pt], projection_method="PCA_2D", variance_explained=1.0, description="Single memory")

        # Stack representation vectors: shape (N, D*D)
        X = np.array([fp.representation_vector for fp in fingerprints], dtype=np.float64)
        N, p = X.shape

        # Center data
        X_centered = X - np.mean(X, axis=0, keepdims=True)

        # SVD for PCA: X_centered = U @ S @ Vt
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

        # 2D projection
        if len(S) >= 2:
            coords = U[:, :2] * S[:2]
            var_explained = float(np.sum(S[:2] ** 2) / (np.sum(S ** 2) + 1e-9))
        else:
            coords = np.zeros((N, 2))
            coords[:, 0] = U[:, 0] * S[0]
            var_explained = 1.0

        # Detect outliers
        outlier_reports = self.detect_outliers(fingerprints)
        outlier_map = {r.memory_id: r for r in outlier_reports}

        points: List[MemoryDistancePoint] = []
        for i, fp in enumerate(fingerprints):
            rep = outlier_map.get(fp.memory_id)
            is_out = rep.is_outlier if rep else False
            reasons = rep.reasons if rep else []

            points.append(
                MemoryDistancePoint(
                    memory_id=fp.memory_id,
                    concept=fp.concept,
                    value=fp.value,
                    x=float(coords[i, 0]),
                    y=float(coords[i, 1]),
                    active_units=fp.active_unit_count,
                    recall_fidelity=fp.recall_performance["fidelity"],
                    is_outlier=is_out,
                    outlier_reasons=reasons,
                )
            )

        return MemoryDistanceMap(
            points=points,
            projection_method="PCA_2D",
            variance_explained=var_explained,
            description="2D projection of normalized synaptic representation vectors via SVD.",
        )

    def detect_outliers(
        self,
        fingerprints: List[SynapticFingerprint],
    ) -> List[OutlierReport]:
        """Detect Representational Outliers based on active units, sparsity, and Frobenius contributions."""
        if len(fingerprints) < 3:
            return [
                OutlierReport(
                    memory_id=fp.memory_id,
                    concept=fp.concept,
                    is_outlier=False,
                    z_scores={},
                    reasons=[],
                )
                for fp in fingerprints
            ]

        # Extract features
        active_counts = np.array([fp.active_unit_count for fp in fingerprints], dtype=np.float64)
        sparsities = np.array([fp.sparsity for fp in fingerprints], dtype=np.float64)
        frob_contribs = np.array(
            [fp.synaptic_strength_stats["frobenius_contribution"] for fp in fingerprints],
            dtype=np.float64,
        )

        def z_score(arr: np.ndarray) -> np.ndarray:
            std = np.std(arr)
            return (arr - np.mean(arr)) / (std + 1e-9)

        z_act = z_score(active_counts)
        z_spar = z_score(sparsities)
        z_frob = z_score(frob_contribs)

        reports: List[OutlierReport] = []
        for i, fp in enumerate(fingerprints):
            z_dict = {
                "active_units": float(z_act[i]),
                "sparsity": float(z_spar[i]),
                "frobenius_contribution": float(z_frob[i]),
            }

            reasons: List[str] = []
            if abs(z_act[i]) > 1.8:
                reasons.append(
                    f"Active unit count ({fp.active_unit_count}) deviates significantly (z={z_act[i]:.2f})"
                )
            if abs(z_spar[i]) > 1.8:
                reasons.append(
                    f"Unit sparsity ({fp.sparsity:.2f}) deviates significantly (z={z_spar[i]:.2f})"
                )
            if abs(z_frob[i]) > 1.8:
                reasons.append(
                    f"Frobenius update norm ({fp.synaptic_strength_stats['frobenius_contribution']:.2f}) deviates (z={z_frob[i]:.2f})"
                )

            reports.append(
                OutlierReport(
                    memory_id=fp.memory_id,
                    concept=fp.concept,
                    is_outlier=len(reasons) > 0,
                    z_scores=z_dict,
                    reasons=reasons,
                )
            )

        return reports

    def build_family_tree(
        self,
        target_concept: str = "Concept Alpha",
        seed: int = 42,
        dimension: int = 16,
    ) -> MemoryBranchNode:
        """Build a hierarchical memory family tree connecting Original, Collision, Surgery,

        and Counterfactual branches.
        """
        brain = SynapticBrain(seed=seed, d=dimension, update_strength=0.35, decay=0.01)
        brain.write(target_concept, "Target Alpha")
        brain.recall(target_concept, expected_value="Target Alpha")
        fp_root = self.compute_fingerprint(brain, target_concept, "Target Alpha")

        root = MemoryBranchNode(
            node_id="branch_orig",
            label=f"{target_concept} (Original)",
            branch_type="ORIGINAL",
            step=1,
            parent_id=None,
            fingerprint=fp_root,
            children=[],
        )

        # 1. Collision Child Branch
        brain_col = copy.deepcopy(brain)
        brain_col.write("Concept Beta (Competing)", "Target Beta")
        brain_col.recall(target_concept, expected_value="Target Alpha")
        fp_col = self.compute_fingerprint(brain_col, target_concept, "Target Alpha")

        col_node = MemoryBranchNode(
            node_id="branch_col",
            label="After Collision Write",
            branch_type="COLLISION",
            step=2,
            parent_id="branch_orig",
            fingerprint=fp_col,
            children=[],
        )

        # Surgery Grandchild Branch off Collision
        brain_surg = copy.deepcopy(brain_col)
        if fp_col.modified_synapses:
            r, c, _ = fp_col.modified_synapses[0]
            brain_surg.W[r, c] = 0.0
            brain_surg.recall(target_concept, expected_value="Target Alpha")
            fp_surg = self.compute_fingerprint(brain_surg, target_concept, "Target Alpha")
            surg_node = MemoryBranchNode(
                node_id="branch_surg",
                label=f"Surgery on W[{r},{c}]",
                branch_type="SURGERY",
                step=3,
                parent_id="branch_col",
                fingerprint=fp_surg,
                children=[],
            )
            col_node.children.append(surg_node)

        # 2. Counterfactual Child Branch off Original
        brain_cf = SynapticBrain(seed=seed, d=dimension, update_strength=0.08, decay=0.01)
        brain_cf.write(target_concept, "Target Alpha")
        brain_cf.recall(target_concept, expected_value="Target Alpha")
        fp_cf = self.compute_fingerprint(brain_cf, target_concept, "Target Alpha")

        cf_node = MemoryBranchNode(
            node_id="branch_cf",
            label="What-If: Low Plasticity (η=0.08)",
            branch_type="COUNTERFACTUAL",
            step=1,
            parent_id="branch_orig",
            fingerprint=fp_cf,
            children=[],
        )

        root.children.extend([col_node, cf_node])
        return root

    def get_challenges(self) -> List[FingerprintChallenge]:
        """Provide scientific prediction challenges for the learner."""
        return [
            FingerprintChallenge(
                challenge_id="ch_sim_internal",
                challenge_type="MOST_SIMILAR_INTERNAL",
                prompt="Which memory shares the highest internal synaptic representation similarity with Concept Alpha?",
                target_memory="Concept Alpha",
                options=["Concept Beta (Shared Context)", "Concept Gamma (Orthogonal Cue)", "Concept Delta (Weak Write)"],
                correct_option="Concept Beta (Shared Context)",
                explanation=(
                    "Concept Beta activates overlapping key dimensions, producing co-linear "
                    "synaptic outer products (high cosine internal similarity)."
                ),
            ),
            FingerprintChallenge(
                challenge_id="ch_mut_interference",
                challenge_type="MOST_CHANGED_INTERFERENCE",
                prompt="Which memory exhibits the largest fingerprint mutation after a competing write?",
                target_memory="Concept Alpha",
                options=["Dense Overlapping Representation", "Sparse Orthogonal Representation", "Consolidated Memory"],
                correct_option="Dense Overlapping Representation",
                explanation=(
                    "Dense overlapping representations share higher synaptic volume with competing "
                    "writes, undergoing maximum weight depression and crosstalk distortion."
                ),
            ),
        ]

    def export_fingerprint_json(self, fp: SynapticFingerprint) -> Dict[str, Any]:
        """Export clean JSON representation of a synaptic fingerprint."""
        return {
            "format": "pathway_synaptic_fingerprint_v1",
            "memory_id": fp.memory_id,
            "concept": fp.concept,
            "value": fp.value,
            "timestep": fp.timestep,
            "dimension": fp.dimension,
            "statistics": {
                "active_unit_count": fp.active_unit_count,
                "modified_synapse_count": fp.modified_synapse_count,
                "sparsity": fp.sparsity,
                "recall_fidelity": fp.recall_performance["fidelity"],
                "frobenius_norm": fp.synaptic_strength_stats["frobenius_contribution"],
            },
            "fingerprint": fp.to_dict(),
        }
