"""FastAPI routes for the Phase 17 Memory Collision & Interference Lab."""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from core.collision import (
    CollisionConfig,
    CollisionMemory,
    CollisionResult,
    perform_collision_counterfactual,
    perform_collision_surgery,
    run_collision_experiment,
    run_order_comparison,
    run_three_condition_suite,
)
from .collision_schemas import (
    CollisionCounterfactualRequest,
    CollisionRunRequest,
    CollisionSurgeryRequest,
    OrderComparisonRequest,
    ThreeConditionRequest,
)

collision_router = APIRouter(prefix="/collision", tags=["collision"])

# In-memory cache of recent collision results for quick surgery/counterfactual exploration
_COLLISION_CACHE: Dict[str, CollisionResult] = {}


def _schema_to_config(req: CollisionRunRequest) -> CollisionConfig:
    mem_a = CollisionMemory(
        concept=req.memory_a.concept,
        value=req.memory_a.value,
        importance=req.memory_a.importance,
        strength=req.memory_a.strength,
    )
    mem_b = CollisionMemory(
        concept=req.memory_b.concept,
        value=req.memory_b.value,
        importance=req.memory_b.importance,
        strength=req.memory_b.strength,
    )
    mem_c = None
    if req.memory_c:
        mem_c = CollisionMemory(
            concept=req.memory_c.concept,
            value=req.memory_c.value,
            importance=req.memory_c.importance,
            strength=req.memory_c.strength,
        )

    return CollisionConfig(
        seed=req.seed,
        dimension=req.dimension,
        decay=req.decay,
        update_strength=req.update_strength,
        memory_a=mem_a,
        memory_b=mem_b,
        memory_c=mem_c,
        order=req.order,
        temporal_delay=req.temporal_delay,
        overlap_preset=req.overlap_preset,
        concept_similarity=req.concept_similarity,
    )


@collision_router.get("/info")
def collision_info() -> Dict[str, Any]:
    """Scientific overview of memory collision & interference lab."""
    return {
        "title": "Memory Collision & Interference Lab",
        "description": (
            "Deliberately creates multiple memories that compete for overlapping computational "
            "and synaptic resources, demonstrating how associative interference, crosstalk, and "
            "catastrophic forgetting emerge naturally from Hebbian outer-product matrix updates."
        ),
        "equations": {
            "write_a": "ΔW_A = η_A · (v_A ⊗ k_A)",
            "write_b": "ΔW_B = η_B · (v_B ⊗ k_B)",
            "collision_matrix": "W = (1 - λ)^τ · ΔW_A + ΔW_B",
            "linear_recall": "v̂ = W @ k_query",
            "fidelity": "cos(v̂, v_target) = ⟨v̂, v_target⟩ / (‖v̂‖ · ‖v_target‖)",
            "interference": "Interference = Fidelity_isolated - Fidelity_combined",
        },
    }


@collision_router.post("/run")
def run_collision(req: CollisionRunRequest) -> Dict[str, Any]:
    """Execute a controlled memory collision experiment."""
    try:
        config = _schema_to_config(req)
        result = run_collision_experiment(config)
        _COLLISION_CACHE[result.collision_id] = result
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collision experiment failed: {str(e)}")


@collision_router.post("/three-conditions")
def run_three_conditions(req: ThreeConditionRequest) -> Dict[str, Any]:
    """Execute Low, Moderate, and High overlap conditions simultaneously to produce the Recall Matrix."""
    try:
        base_cfg = _schema_to_config(
            CollisionRunRequest(
                seed=req.seed,
                dimension=req.dimension,
                decay=req.decay,
                update_strength=req.update_strength,
                memory_a=req.memory_a,
                memory_b=req.memory_b,
                order=req.order,
                temporal_delay=req.temporal_delay,
            )
        )
        return run_three_condition_suite(base_cfg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Three-condition suite failed: {str(e)}")


@collision_router.post("/order-comparison")
def run_order_comp(req: OrderComparisonRequest) -> Dict[str, Any]:
    """Compare write sequence A -> B vs B -> A."""
    try:
        base_cfg = _schema_to_config(
            CollisionRunRequest(
                seed=req.seed,
                dimension=req.dimension,
                decay=req.decay,
                update_strength=req.update_strength,
                memory_a=req.memory_a,
                memory_b=req.memory_b,
                overlap_preset=req.overlap_preset,
                concept_similarity=req.concept_similarity,
                temporal_delay=req.temporal_delay,
            )
        )
        return run_order_comparison(base_cfg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order comparison failed: {str(e)}")


@collision_router.post("/surgery")
def collision_surgery(req: CollisionSurgeryRequest) -> Dict[str, Any]:
    """Perform surgical modification (silence/weaken/strengthen) on a shared colliding synapse."""
    try:
        config = _schema_to_config(req.config)
        base_result = run_collision_experiment(config)
        return perform_collision_surgery(
            collision_result=base_result,
            synapse_id=req.synapse_id,
            operation=req.operation,
            factor=req.factor,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collision surgery failed: {str(e)}")


@collision_router.post("/counterfactual")
def collision_counterfactual(req: CollisionCounterfactualRequest) -> Dict[str, Any]:
    """Evaluate counterfactual branch: What if Memory B never touched the shared synapses?"""
    try:
        config = _schema_to_config(req.config)
        base_result = run_collision_experiment(config)
        return perform_collision_counterfactual(
            collision_result=base_result,
            shared_synapse_ids=req.shared_synapse_ids,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collision counterfactual failed: {str(e)}")
