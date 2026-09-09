"""FastAPI endpoints for Phase 20: Memory Genome & Synaptic Fingerprint."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from core.fingerprint import MemoryGenomeEngine, SynapticFingerprint
from core.synaptic import SynapticBrain
from .fingerprint_schemas import (
    CloningTestRequest,
    CollisionMutationRequest,
    CompareFingerprintsRequest,
    ComputeFingerprintRequest,
    CounterfactualFingerprintRequest,
    FingerprintSurgeryRequest,
    SurfaceVsInternalRequest,
    VerifyChallengeRequest,
)

fingerprint_router = APIRouter(prefix="/fingerprint", tags=["fingerprint"])
engine = MemoryGenomeEngine()


def _get_demo_brain(dimension: int = 16, seed: int = 42) -> SynapticBrain:
    """Construct a canonical synaptic brain with multiple distinct memories."""
    brain = SynapticBrain(seed=seed, d=dimension, update_strength=0.35, decay=0.01)
    concepts_values = [
        ("Concept Alpha", "Target Alpha"),
        ("Concept Beta (Shared)", "Target Beta"),
        ("Concept Gamma", "Target Gamma"),
        ("Concept Delta (Dense)", "Target Delta"),
        ("Concept Epsilon (Sparse)", "Target Epsilon"),
    ]
    for c, v in concepts_values:
        brain.write(c, v)
    return brain


@fingerprint_router.get("/demo")
def get_fingerprint_demo(dimension: int = 16, seed: int = 42) -> Dict[str, Any]:
    """Return pre-computed demo multi-memory fingerprints and distance map for instant discovery."""
    brain = _get_demo_brain(dimension=dimension, seed=seed)
    concepts = [m.concept for m in brain.library]
    fingerprints = [engine.compute_fingerprint(brain, c) for c in concepts]
    distance_map = engine.compute_distance_map(fingerprints)
    outliers = engine.detect_outliers(fingerprints)
    challenges = engine.get_challenges()

    return {
        "fingerprints": [fp.to_dict() for fp in fingerprints],
        "distance_map": distance_map.to_dict(),
        "outliers": [o.to_dict() for o in outliers],
        "challenges": [ch.to_dict() for ch in challenges],
        "concepts": concepts,
    }


@fingerprint_router.post("/compute")
def compute_fingerprint_endpoint(req: ComputeFingerprintRequest) -> Dict[str, Any]:
    """Compute a single empirical synaptic fingerprint."""
    brain = SynapticBrain(
        seed=req.seed,
        d=req.dimension,
        update_strength=req.update_strength,
        decay=req.decay,
    )
    brain.write(req.concept, req.value or f"val_{req.concept}")
    brain.recall(req.concept, expected_value=req.value)
    fp = engine.compute_fingerprint(brain, req.concept, req.value)
    return {"fingerprint": fp.to_dict()}


@fingerprint_router.post("/compare")
def compare_fingerprints_endpoint(req: CompareFingerprintsRequest) -> Dict[str, Any]:
    """Compare two memory concepts on surface and internal synaptic dimensions."""
    brain = SynapticBrain(seed=req.seed, d=req.dimension, update_strength=0.35, decay=0.01)
    brain.write(req.concept_a, req.value_a or f"val_{req.concept_a}")
    brain.write(req.concept_b, req.value_b or f"val_{req.concept_b}")

    fp_a = engine.compute_fingerprint(brain, req.concept_a, req.value_a)
    fp_b = engine.compute_fingerprint(brain, req.concept_b, req.value_b)

    comp = engine.compare_fingerprints(fp_a, fp_b, seed=req.seed)
    return {
        "fingerprint_a": fp_a.to_dict(),
        "fingerprint_b": fp_b.to_dict(),
        "comparison": comp.to_dict(),
    }


@fingerprint_router.post("/surface-vs-internal")
def surface_vs_internal_endpoint(req: SurfaceVsInternalRequest) -> Dict[str, Any]:
    """Pairwise evaluation of Surface Similarity vs Internal Representation Similarity."""
    brain = SynapticBrain(seed=req.seed, d=req.dimension, update_strength=0.35, decay=0.01)
    for c in req.concepts:
        brain.write(c, f"val_{c}")

    comparisons = engine.compare_surface_vs_internal(brain, req.concepts)
    return {
        "comparisons": [c.to_dict() for c in comparisons],
        "total_pairs": len(comparisons),
    }


@fingerprint_router.post("/cloning-test")
def cloning_test_endpoint(req: CloningTestRequest) -> Dict[str, Any]:
    """Execute Before/After memory cloning stability experiment."""
    res = engine.run_cloning_experiment(
        seed=req.seed,
        dimension=req.dimension,
        target_concept=req.target_concept,
        target_value=req.target_value,
        intervening_concept=req.intervening_concept,
        intervening_value=req.intervening_value,
    )
    return res


@fingerprint_router.post("/collision-mutation")
def collision_mutation_endpoint(req: CollisionMutationRequest) -> Dict[str, Any]:
    """Execute collision mutation experiment and quantify fingerprint delta."""
    res = engine.run_collision_mutation(
        seed=req.seed,
        dimension=req.dimension,
        concept_a=req.concept_a,
        value_a=req.value_a,
        concept_b=req.concept_b,
        value_b=req.value_b,
    )
    return res


@fingerprint_router.post("/surgery")
def fingerprint_surgery_endpoint(req: FingerprintSurgeryRequest) -> Dict[str, Any]:
    """Apply surgery to contributing synapse and remeasure fingerprint."""
    target_syn = (req.target_synapse[0], req.target_synapse[1])
    res = engine.run_surgery_and_remeasure(
        seed=req.seed,
        dimension=req.dimension,
        concept=req.concept,
        value=req.value,
        target_synapse=target_syn,
        new_weight=req.new_weight,
    )
    return res


@fingerprint_router.post("/counterfactual")
def counterfactual_endpoint(req: CounterfactualFingerprintRequest) -> Dict[str, Any]:
    """Compare original fingerprint against counterfactual plasticity fingerprint."""
    res = engine.run_counterfactual_comparison(
        seed=req.seed,
        dimension=req.dimension,
        concept=req.concept,
        value=req.value,
        cf_update_strength=req.cf_update_strength,
    )
    return res


@fingerprint_router.get("/distance-map")
def distance_map_endpoint(dimension: int = 16, seed: int = 42) -> Dict[str, Any]:
    """Return 2D PCA/MDS projection map of active memories."""
    brain = _get_demo_brain(dimension=dimension, seed=seed)
    fingerprints = [engine.compute_fingerprint(brain, m.concept) for m in brain.library]
    d_map = engine.compute_distance_map(fingerprints)
    return {"distance_map": d_map.to_dict()}


@fingerprint_router.get("/outliers")
def outliers_endpoint(dimension: int = 16, seed: int = 42) -> Dict[str, Any]:
    """Detect representational outliers across memories."""
    brain = _get_demo_brain(dimension=dimension, seed=seed)
    fingerprints = [engine.compute_fingerprint(brain, m.concept) for m in brain.library]
    reports = engine.detect_outliers(fingerprints)
    return {"outliers": [r.to_dict() for r in reports]}


@fingerprint_router.get("/family-tree/{concept}")
def family_tree_endpoint(concept: str, dimension: int = 16, seed: int = 42) -> Dict[str, Any]:
    """Return memory family tree branching across original, collision, surgery, and counterfactual states."""
    tree = engine.build_family_tree(target_concept=concept, seed=seed, dimension=dimension)
    return {"family_tree": tree.to_dict()}


@fingerprint_router.get("/challenges")
def challenges_endpoint() -> Dict[str, Any]:
    """Return interactive prediction challenges."""
    challenges = engine.get_challenges()
    return {"challenges": [c.to_dict() for c in challenges]}


@fingerprint_router.post("/challenges/verify")
def verify_challenge_endpoint(req: VerifyChallengeRequest) -> Dict[str, Any]:
    """Verify learner's prediction challenge answer."""
    challenges = engine.get_challenges()
    matched = next((c for c in challenges if c.challenge_id == req.challenge_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail="Challenge not found")

    is_correct = (req.selected_option.strip().lower() == matched.correct_option.strip().lower())
    return {
        "challenge_id": matched.challenge_id,
        "is_correct": is_correct,
        "correct_option": matched.correct_option,
        "explanation": matched.explanation,
    }


@fingerprint_router.post("/export")
def export_fingerprint_endpoint(req: ComputeFingerprintRequest) -> Dict[str, Any]:
    """Export clean JSON fingerprint for offline research."""
    brain = SynapticBrain(seed=req.seed, d=req.dimension, update_strength=req.update_strength, decay=req.decay)
    brain.write(req.concept, req.value or f"val_{req.concept}")
    brain.recall(req.concept, expected_value=req.value)
    fp = engine.compute_fingerprint(brain, req.concept, req.value)
    return engine.export_fingerprint_json(fp)
