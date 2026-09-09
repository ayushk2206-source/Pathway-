"""FastAPI route handlers for Phase 21: Memory Ecosystem / Unified Synaptic Memory World."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from core.ecosystem import MemoryEcosystemEngine
from .ecosystem_schemas import (
    CompareStatesRequest,
    CreateCheckpointRequest,
    SelectMemoryRequest,
    SubmitHypothesisRequest,
)

ecosystem_router = APIRouter(prefix="/ecosystem", tags=["ecosystem"])

# Global singleton ecosystem engine instance
_engine: Optional[MemoryEcosystemEngine] = None


def get_ecosystem_engine() -> MemoryEcosystemEngine:
    global _engine
    if _engine is None:
        _engine = MemoryEcosystemEngine(dimension=16, seed=42)
    return _engine


@ecosystem_router.get("/overview")
def get_ecosystem_overview() -> Dict[str, Any]:
    """Returns complete state overview of the unified memory ecosystem."""
    engine = get_ecosystem_engine()
    passports = engine.list_passports()
    active_passport = engine.get_memory_passport(engine.active_memory_id)

    return {
        "active_memory_id": engine.active_memory_id,
        "is_following": engine.is_following,
        "active_passport": active_passport.to_dict(),
        "passports": [p.to_dict() for p in passports],
        "total_memories": len(passports),
        "total_events": len(engine.get_unified_timeline()),
        "scientific_claim": (
            "Recent activity temporarily changes synaptic connections, allowing information "
            "to be represented and retrieved through an evolving internal state."
        ),
    }


@ecosystem_router.get("/memory/{memory_id}")
def get_memory_ecosystem_details(memory_id: str) -> Dict[str, Any]:
    """Returns passport, lifecycle pipeline, branch tree, and ledger for a single memory."""
    engine = get_ecosystem_engine()
    passport = engine.get_memory_passport(memory_id)
    lifecycle = engine.get_memory_lifecycle(memory_id)
    branches = engine.get_memory_branch_tree(memory_id)
    checkpoints = engine.list_checkpoints(memory_id)
    ledger = engine.get_change_ledger(memory_id)

    return {
        "passport": passport.to_dict(),
        "lifecycle": lifecycle.to_dict(),
        "branch_tree": branches.to_dict(),
        "checkpoints": [cp.to_dict() for cp in checkpoints],
        "ledger": ledger.to_dict(),
    }


@ecosystem_router.post("/select-memory")
def select_active_memory(req: SelectMemoryRequest) -> Dict[str, Any]:
    """Sets the active memory globally across all ecosystem workspaces."""
    engine = get_ecosystem_engine()
    passport = engine.set_active_memory(req.memory_id, follow=req.follow)
    return {
        "success": True,
        "active_memory_id": engine.active_memory_id,
        "is_following": engine.is_following,
        "passport": passport.to_dict(),
    }


@ecosystem_router.get("/timeline")
def get_unified_timeline(memory_id: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Returns unified computational timeline events, optionally filtered by memory."""
    engine = get_ecosystem_engine()
    events = engine.get_unified_timeline(memory_id=memory_id)
    return {
        "memory_id": memory_id,
        "total_events": len(events),
        "events": [e.to_dict() for e in events],
    }


@ecosystem_router.get("/relationships")
def get_memory_relationships() -> Dict[str, Any]:
    """Returns evidence-based relationship graph among all memories."""
    engine = get_ecosystem_engine()
    relationships = engine.build_relationship_map()
    return {
        "total_relationships": len(relationships),
        "relationships": [r.to_dict() for r in relationships],
    }


@ecosystem_router.get("/ledger/{memory_id}")
def get_synaptic_change_ledger(
    memory_id: str,
    transition: str = Query("SYNAPTIC WRITE", description="Transition name")
) -> Dict[str, Any]:
    """Returns before vs after ledger with explicit OBSERVED/INFERRED scientific claims."""
    engine = get_ecosystem_engine()
    ledger = engine.get_change_ledger(memory_id, transition_name=transition)
    return {
        "ledger": ledger.to_dict(),
    }


@ecosystem_router.post("/hypothesis")
def submit_learner_hypothesis(req: SubmitHypothesisRequest) -> Dict[str, Any]:
    """Submits and evaluates learner prediction against empirical computational outcome."""
    engine = get_ecosystem_engine()
    hyp = engine.record_hypothesis(
        memory_id=req.memory_id,
        experiment_type=req.experiment_type,
        prediction_text=req.prediction_text,
        predicted_outcome=req.predicted_outcome,
    )
    return {
        "hypothesis": hyp.to_dict(),
    }


@ecosystem_router.get("/hypotheses")
def list_learner_hypotheses(memory_id: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Lists registered hypotheses with empirical evaluation results."""
    engine = get_ecosystem_engine()
    hyps = engine.get_hypotheses(memory_id=memory_id)
    return {
        "hypotheses": [h.to_dict() for h in hyps],
    }


@ecosystem_router.post("/checkpoint")
def create_memory_checkpoint(req: CreateCheckpointRequest) -> Dict[str, Any]:
    """Saves a named checkpoint snapshot for a memory."""
    engine = get_ecosystem_engine()
    cp = engine.create_checkpoint(memory_id=req.memory_id, label=req.label)
    return {
        "checkpoint": cp.to_dict(),
    }


@ecosystem_router.get("/checkpoints/{memory_id}")
def list_memory_checkpoints(memory_id: str) -> Dict[str, Any]:
    """Lists all saved checkpoints for a memory."""
    engine = get_ecosystem_engine()
    cps = engine.list_checkpoints(memory_id=memory_id)
    return {
        "memory_id": memory_id,
        "checkpoints": [cp.to_dict() for cp in cps],
    }


@ecosystem_router.post("/compare-states")
def compare_memory_states(req: CompareStatesRequest) -> Dict[str, Any]:
    """Compares two experimental states or checkpoints."""
    engine = get_ecosystem_engine()
    diff = engine.compare_states(req.state_a, req.state_b)
    return {
        "comparison": diff,
    }


@ecosystem_router.get("/replay/{memory_id}")
def replay_memory_history(memory_id: str) -> Dict[str, Any]:
    """Reconstructs the actual empirical transition playback steps for a memory."""
    engine = get_ecosystem_engine()
    replay_data = engine.replay_memory(memory_id=memory_id)
    return replay_data
