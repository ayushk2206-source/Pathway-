"""Synaptic Surgery & Memory X-Ray API routes (Phase 15).

Exposes endpoints for:
    - Locking the live brain state into an isolated experimental SurgerySession
    - Weaken, strengthen, silence, restore, and reset operations on the surgery branch
    - Side-by-side recall comparison between baseline and surgery branches
    - Memory X-Ray to identify which synapses are computationally relevant to a memory
    - Per-synapse inspection with baseline and experimental weights
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from core.surgery import (
    SurgerySession,
    compute_memory_xray,
    get_synapse_xray_in_session,
    lock_baseline,
    reset_session,
    restore_synapses,
    run_recall_comparison,
    silence_synapses,
    strengthen_synapses,
    weaken_synapses,
)
from .surgery_schemas import (
    LockBaselineRequest,
    MemoryXRayRequest,
    SurgeryRecallRequest,
    SynapseOperationRequest,
)
from .synaptic_routes import get_live_brain

surgery_router = APIRouter(tags=["surgery"])

_ACTIVE_SURGERY_SESSION: Optional[SurgerySession] = None


def get_active_surgery_session() -> Optional[SurgerySession]:
    """Retrieve the current surgery session if locked."""
    return _ACTIVE_SURGERY_SESSION


def set_active_surgery_session(session: Optional[SurgerySession]) -> None:
    """Set or clear the active surgery session."""
    global _ACTIVE_SURGERY_SESSION
    _ACTIVE_SURGERY_SESSION = session


@surgery_router.post("/surgery/lock")
def lock_surgery_session(req: Optional[LockBaselineRequest] = None) -> Dict[str, Any]:
    """Lock the live brain's current state as the surgery baseline.

    Creates an isolated copy of the synaptic weight matrix W. Future surgery
    operations modify only the experimental branch; the baseline snapshot is frozen.
    """
    global _ACTIVE_SURGERY_SESSION
    dim = req.dimension if req else 16
    decay = req.decay if req else 0.05
    seed = req.seed if req else 42

    brain = get_live_brain(dimension=dim, decay=decay, seed=seed)
    session = lock_baseline(brain)
    _ACTIVE_SURGERY_SESSION = session

    return {
        "status": "locked",
        "message": (
            "Baseline locked. An experimental copy of the synaptic matrix has been created. "
            "All subsequent surgery operations modify this experimental branch only."
        ),
        "session": session.to_dict(),
    }


@surgery_router.get("/surgery/state")
def get_surgery_state() -> Dict[str, Any]:
    """Retrieve the active surgery session state or indicate no session."""
    if _ACTIVE_SURGERY_SESSION is None:
        return {
            "locked": False,
            "session": None,
            "message": "No active surgery session. Call POST /api/surgery/lock to lock baseline.",
        }
    return {
        "locked": True,
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
        "message": "Active surgery session loaded.",
    }


@surgery_router.post("/surgery/weaken")
def weaken_synapses_endpoint(req: SynapseOperationRequest) -> Dict[str, Any]:
    """Weaken selected synapses by a multiplicative factor (< 1.0) on the experimental branch."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    factor = req.factor if req.factor is not None else 0.5
    op = weaken_synapses(_ACTIVE_SURGERY_SESSION, req.synapse_ids, factor=factor)
    return {
        "operation": op.to_dict(),
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
    }


@surgery_router.post("/surgery/strengthen")
def strengthen_synapses_endpoint(req: SynapseOperationRequest) -> Dict[str, Any]:
    """Strengthen selected synapses by a multiplicative factor (> 1.0) on the experimental branch."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    factor = req.factor if req.factor is not None else 2.0
    op = strengthen_synapses(_ACTIVE_SURGERY_SESSION, req.synapse_ids, factor=factor)
    return {
        "operation": op.to_dict(),
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
    }


@surgery_router.post("/surgery/silence")
def silence_synapses_endpoint(req: SynapseOperationRequest) -> Dict[str, Any]:
    """Set selected synapse weights to 0 on the experimental branch (controlled ablation experiment)."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    op = silence_synapses(_ACTIVE_SURGERY_SESSION, req.synapse_ids)
    return {
        "operation": op.to_dict(),
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
    }


@surgery_router.post("/surgery/restore")
def restore_synapses_endpoint(req: SynapseOperationRequest) -> Dict[str, Any]:
    """Restore selected synapses back to their baseline values from the frozen snapshot."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    op = restore_synapses(_ACTIVE_SURGERY_SESSION, req.synapse_ids)
    return {
        "operation": op.to_dict(),
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
    }


@surgery_router.post("/surgery/reset")
def reset_surgery_endpoint() -> Dict[str, Any]:
    """Reset the experimental branch back to the frozen baseline state."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    op = reset_session(_ACTIVE_SURGERY_SESSION)
    return {
        "operation": op.to_dict(),
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
    }


@surgery_router.post("/surgery/recall")
def surgery_recall_endpoint(req: SurgeryRecallRequest) -> Dict[str, Any]:
    """Execute associative recall on BOTH baseline and surgery branches to evaluate effects."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    comparison = run_recall_comparison(
        _ACTIVE_SURGERY_SESSION,
        query_concept=req.query_concept,
        expected_value=req.expected_value,
        measure=req.measure,
        top_k=req.top_k,
    )
    return {
        "comparison": comparison.to_dict(),
        "session": _ACTIVE_SURGERY_SESSION.to_dict(),
    }


@surgery_router.get("/surgery/synapse/{synapse_id}/xray")
def synapse_xray_endpoint(synapse_id: str) -> Dict[str, Any]:
    """Inspect a single synapse across baseline and surgery branches."""
    if _ACTIVE_SURGERY_SESSION is None:
        raise HTTPException(
            status_code=400,
            detail="No active surgery session. Please lock baseline first via POST /api/surgery/lock.",
        )
    info = get_synapse_xray_in_session(_ACTIVE_SURGERY_SESSION, synapse_id)
    if "error" in info:
        raise HTTPException(status_code=400, detail=info["error"])
    return info


@surgery_router.post("/surgery/xray/memory")
def memory_xray_endpoint(req: MemoryXRayRequest) -> Dict[str, Any]:
    """Perform a Memory X-Ray to identify which synapses are computationally responsible for a concept.

    Can inspect the 'live' brain, the locked 'baseline', or the 'surgery' experimental branch.
    """
    branch = req.branch or "live"

    if branch in ("baseline", "surgery"):
        if _ACTIVE_SURGERY_SESSION is None:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot inspect branch '{branch}': no active surgery session locked.",
            )
        W = _ACTIVE_SURGERY_SESSION.baseline_W if branch == "baseline" else _ACTIVE_SURGERY_SESSION.surgery_W
        W_prev = _ACTIVE_SURGERY_SESSION.baseline_W_prev
        last_delta = _ACTIVE_SURGERY_SESSION.baseline_last_delta
        last_update_steps = _ACTIVE_SURGERY_SESSION.baseline_last_update_steps
        library = _ACTIVE_SURGERY_SESSION.library
        seed = _ACTIVE_SURGERY_SESSION.seed
        d = _ACTIVE_SURGERY_SESSION.d
    else:
        brain = get_live_brain(dimension=req.dimension, decay=req.decay, seed=req.seed)
        W = brain.W
        W_prev = brain.W_prev
        last_delta = brain.last_delta
        last_update_steps = brain.last_update_steps
        library = brain.library
        seed = brain.seed
        d = brain.d

    xray = compute_memory_xray(
        W=W,
        W_prev=W_prev,
        last_delta=last_delta,
        last_update_steps=last_update_steps,
        library=library,
        seed=seed,
        d=d,
        query_concept=req.query_concept,
        expected_value=req.expected_value,
    )
    res = xray.to_dict()
    res["branch"] = branch
    return res
