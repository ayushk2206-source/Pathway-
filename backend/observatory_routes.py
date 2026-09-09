"""FastAPI routes for Phase 19: Adaptive Memory Observatory."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status

from core.observatory import (
    AdaptiveObservatoryEngine,
    ChangeDetection,
    EnvironmentShiftReport,
    LearnerPrediction,
    ObservatorySession,
    ObservatorySnapshot,
    StabilityPlasticityMetrics,
    StreamEvent,
)
from .observatory_schemas import (
    ChangeDetectionRequest,
    CompareSessionsRequest,
    CounterfactualBranchRequest,
    ExportDetectiveCaseRequest,
    InterventionBranchRequest,
    RunStreamRequest,
    StepStreamRequest,
    SubmitPredictionRequest,
)

observatory_router = APIRouter(prefix="/observatory", tags=["Adaptive Memory Observatory"])

# In-memory store for active sessions
_OBSERVATORY_SESSIONS: Dict[str, ObservatorySession] = {}


def _get_or_create_default_session() -> ObservatorySession:
    """Ensure at least one canonical environment shift session exists."""
    for s in _OBSERVATORY_SESSIONS.values():
        if "Shift" in s.name:
            return s
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    _OBSERVATORY_SESSIONS[session.session_id] = session
    return session


@observatory_router.get("/presets")
def get_stream_presets():
    """Retrieve available educational stream presets."""
    return {
        "presets": [
            {
                "preset_id": "env_shift",
                "name": "Environment Shift (A → B → A)",
                "description": "Examines whether an established memory survives, degrades, or recovers when world context changes and returns.",
                "total_steps": 10,
                "scientific_focus": "Contextual Stability & Associative Recovery",
            },
            {
                "preset_id": "collision_stream",
                "name": "Continuous Concept Collision Stream",
                "description": "Stream presenting overlapping concept representations to observe cumulative crosstalk noise over time.",
                "total_steps": 8,
                "scientific_focus": "Catastrophic Overwrite & Shared Coordinates",
            },
            {
                "preset_id": "decay_recovery",
                "name": "Temporal Decay vs Plasticity Re-encoding",
                "description": "Long idle decay period followed by selective re-encoding to investigate passive trace loss vs active reconstruction.",
                "total_steps": 9,
                "scientific_focus": "Exponential Attenuation & Latent Engram Recovery",
            },
        ]
    }


@observatory_router.get("/sessions")
def list_observatory_sessions():
    """List all active or completed observatory sessions."""
    _get_or_create_default_session()
    return {
        "total": len(_OBSERVATORY_SESSIONS),
        "sessions": [
            {
                "session_id": s.session_id,
                "name": s.name,
                "dimension": s.dimension,
                "decay": s.decay,
                "update_strength": s.update_strength,
                "total_timesteps": len(s.snapshots),
                "reproducible_hash": s.compute_hash(),
            }
            for s in _OBSERVATORY_SESSIONS.values()
        ],
    }


@observatory_router.get("/sessions/{session_id}")
def get_observatory_session(session_id: str):
    """Retrieve full timeline and snapshots for a specific session."""
    _get_or_create_default_session()
    if session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observatory session '{session_id}' not found.",
        )
    return {"session": _OBSERVATORY_SESSIONS[session_id].to_dict()}


@observatory_router.post("/stream/run")
def run_stream_endpoint(req: RunStreamRequest):
    """Execute a stream sequence (either from preset or custom event list)."""
    if req.preset_id == "env_shift" or (not req.events and not req.preset_id):
        session, report = AdaptiveObservatoryEngine.run_env_shift_protocol(
            dimension=req.dimension,
            decay=req.decay,
            update_strength=req.update_strength,
            seed=req.seed,
        )
        _OBSERVATORY_SESSIONS[session.session_id] = session
        return {
            "session": session.to_dict(),
            "environment_shift_report": report.to_dict(),
        }

    events: List[StreamEvent] = []
    if req.events:
        for ev in req.events:
            events.append(
                StreamEvent(
                    timestep=ev.timestep,
                    environment_id=ev.environment_id,
                    event_type=ev.event_type,
                    label=ev.label,
                    concept=ev.concept,
                    value=ev.value,
                    importance=ev.importance,
                    strength=ev.strength,
                    n_steps=ev.n_steps,
                    metadata=ev.metadata,
                )
            )
    else:
        # Default collision stream
        events = [
            StreamEvent(timestep=1, environment_id="STREAM_MAIN", event_type="WRITE", label="Write A1", concept="cue_alpha", value="val_alpha", strength=1.0),
            StreamEvent(timestep=2, environment_id="STREAM_MAIN", event_type="WRITE", label="Write B1", concept="cue_beta", value="val_beta", strength=1.0),
            StreamEvent(timestep=3, environment_id="STREAM_MAIN", event_type="WRITE", label="Write A2 (Reinforce)", concept="cue_alpha", value="val_alpha", strength=1.2),
            StreamEvent(timestep=4, environment_id="STREAM_MAIN", event_type="DECAY", label="Decay 2 Steps", n_steps=2),
            StreamEvent(timestep=5, environment_id="STREAM_MAIN", event_type="WRITE", label="Write C1 (Distractor)", concept="cue_gamma", value="val_gamma", strength=1.0),
        ]

    tracked = [(p[0], p[1]) for p in req.tracked_probes] if req.tracked_probes else None
    session = AdaptiveObservatoryEngine.run_stream(
        events=events,
        dimension=req.dimension,
        decay=req.decay,
        update_strength=req.update_strength,
        seed=req.seed,
        name=req.name,
        tracked_probes=tracked,
    )
    _OBSERVATORY_SESSIONS[session.session_id] = session
    return {"session": session.to_dict()}


@observatory_router.post("/diff")
def diff_observatory_states_endpoint(req: ChangeDetectionRequest):
    """Compute exact difference between two timesteps in a session."""
    if req.session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{req.session_id}' not found.",
        )
    session = _OBSERVATORY_SESSIONS[req.session_id]
    t_before = max(0, min(len(session.snapshots) - 1, req.timestep_before))
    t_after = max(0, min(len(session.snapshots) - 1, req.timestep_after))

    diff = AdaptiveObservatoryEngine.detect_changes(
        snap_before=session.snapshots[t_before],
        snap_after=session.snapshots[t_after],
    )
    return {"diff": diff.to_dict()}


@observatory_router.post("/stability-plasticity")
def stability_plasticity_endpoint(req: ChangeDetectionRequest):
    """Calculate Stability vs Plasticity metrics between two timesteps."""
    if req.session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{req.session_id}' not found.",
        )
    session = _OBSERVATORY_SESSIONS[req.session_id]
    t_before = max(0, min(len(session.snapshots) - 1, req.timestep_before))
    t_after = max(0, min(len(session.snapshots) - 1, req.timestep_after))

    metrics = AdaptiveObservatoryEngine.compute_stability_plasticity(
        snap_before=session.snapshots[t_before],
        snap_after=session.snapshots[t_after],
    )
    return {"metrics": metrics.to_dict()}


@observatory_router.post("/intervention")
def intervention_branch_endpoint(req: InterventionBranchRequest):
    """Phase 15 integration: Apply surgical modification to synapses at step and branch forward."""
    if req.session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{req.session_id}' not found.",
        )
    parent_session = _OBSERVATORY_SESSIONS[req.session_id]
    branch_session, record = AdaptiveObservatoryEngine.branch_intervention(
        session=parent_session,
        intervention_step=req.step,
        operation=req.operation,
        synapse_ids=req.synapse_ids,
        factor=req.factor,
    )
    _OBSERVATORY_SESSIONS[branch_session.session_id] = branch_session
    return {
        "intervention": record,
        "branch_session": branch_session.to_dict(),
    }


@observatory_router.post("/counterfactual")
def counterfactual_branch_endpoint(req: CounterfactualBranchRequest):
    """Phase 16 integration: Branch counterfactual timeline from step."""
    if req.session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{req.session_id}' not found.",
        )
    parent_session = _OBSERVATORY_SESSIONS[req.session_id]
    branch_session, record = AdaptiveObservatoryEngine.branch_counterfactual(
        session=parent_session,
        intervention_step=req.step,
        counterfactual_label=req.label,
    )
    _OBSERVATORY_SESSIONS[branch_session.session_id] = branch_session
    return {
        "counterfactual": record,
        "branch_session": branch_session.to_dict(),
    }


@observatory_router.post("/compare")
def compare_sessions_endpoint(req: CompareSessionsRequest):
    """Side-by-side comparison of two observatory sessions."""
    if req.session_a_id not in _OBSERVATORY_SESSIONS or req.session_b_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both session IDs not found.",
        )
    res = AdaptiveObservatoryEngine.compare_sessions(
        session_a=_OBSERVATORY_SESSIONS[req.session_a_id],
        session_b=_OBSERVATORY_SESSIONS[req.session_b_id],
    )
    return {"comparison": res}


@observatory_router.post("/predict")
def submit_prediction_endpoint(req: SubmitPredictionRequest):
    """Record learner prediction before a shift and verify against measured outcome."""
    if req.session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{req.session_id}' not found.",
        )
    session = _OBSERVATORY_SESSIONS[req.session_id]
    step = max(0, min(len(session.snapshots) - 1, req.target_timestep))
    snap = session.snapshots[step]

    # Find recall for target memory
    probe = next((p for p in snap.probes if p.concept == req.target_memory), None)
    actual_fid = probe.fidelity if probe else 0.5
    prev_fid = 0.95
    if step > 0:
        prev_probe = next((p for p in session.snapshots[step - 1].probes if p.concept == req.target_memory), None)
        if prev_probe:
            prev_fid = prev_probe.fidelity

    # Determine ground truth outcome category
    if actual_fid >= 0.85:
        actual_outcome = "A"  # Previous memory remains stable
    elif actual_fid < 0.60:
        actual_outcome = "B"  # Previous memory weakens significantly
    else:
        actual_outcome = "D"  # Both partially coexist

    is_accurate = req.predicted_choice == actual_outcome

    feedback = (
        f"At T{step}, target memory '{req.target_memory}' recall was measured as {actual_fid:.3f} "
        f"(compared to {prev_fid:.3f} prior to event). Ground-truth outcome aligns with Option {actual_outcome}."
    )

    pred = LearnerPrediction(
        prediction_id=f"PRED-{uuid.uuid4().hex[:6].upper()}",
        target_timestep=req.target_timestep,
        target_memory=req.target_memory,
        predicted_choice=req.predicted_choice,
        choice_label=req.choice_label,
        actual_outcome=actual_outcome,
        is_accurate=is_accurate,
        observation_feedback=feedback,
    )
    session.predictions.append(pred)

    return {
        "prediction": pred.to_dict(),
        "measured_fidelity": actual_fid,
        "is_accurate": is_accurate,
        "feedback": feedback,
    }


@observatory_router.post("/export-case")
def export_case_endpoint(req: ExportDetectiveCaseRequest):
    """Phase 18 integration: Export an observatory stream anomaly into a Memory Detective Case."""
    if req.session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{req.session_id}' not found.",
        )
    session = _OBSERVATORY_SESSIONS[req.session_id]
    case = AdaptiveObservatoryEngine.export_to_detective_case(
        session=session,
        anomaly_step=req.anomaly_step,
        target_memory=req.target_memory,
    )
    return {"case": case.to_dict()}


@observatory_router.get("/export/{session_id}")
def export_session_json(session_id: str):
    """Export complete session archive as machine-readable JSON."""
    if session_id not in _OBSERVATORY_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    session = _OBSERVATORY_SESSIONS[session_id]
    return {
        "export_format": "PATHWAY_OBSERVATORY_V1",
        "session": session.to_dict(),
        "sha256": session.compute_hash(),
    }
