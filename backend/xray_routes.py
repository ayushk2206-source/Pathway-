"""FastAPI endpoints for Memory X-Ray & Causal Memory Map (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.xray import (
    MemoryReplayController,
    analyze_decay_curves,
    analyze_sparsity,
    build_competition_graph,
    build_memory_explanation,
    cluster_memory_representations,
    compare_states,
    compare_xray_surgery,
    compute_activation_profile,
    compute_event_impact,
    compute_memory_diagnostics,
    compute_memory_importance,
    compute_memory_strengths,
    create_memory_snapshots,
    detect_interference,
    detect_reinforcement,
    detect_state_anomalies,
    detect_state_changes,
    execute_xray_query,
    find_nearest_memories,
    generate_heatmap_matrices,
    generate_visualization_contracts,
    generate_xray_report,
    get_memory_trace,
    get_state_checkpoint,
    get_state_trajectory,
    project_memory_map_2d,
    trace_divergence_xray,
)
from .store import ExperimentStore
from .xray_schemas import (
    CompareStatesRequest,
    CompareStatesResponse,
    DivergenceTraceRequest,
    ReplayActionRequest,
    SurgeryDiffRequest,
    XRayQueryRequest,
)

xray_router = APIRouter(prefix="/xray", tags=["xray"])


def get_store(request: Request) -> ExperimentStore:
    return getattr(request.app.state, "store", None) or ExperimentStore()


def _resolve_experiment(exp_id: str, store: ExperimentStore):
    exp = store.get(exp_id)
    if not exp:
        # Check counterfactuals or lab experiments in store
        cf = store._counterfactuals.get(exp_id)
        if cf:
            exp = cf.to_experiment()
        else:
            raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return exp


@xray_router.get("/{id}/snapshots")
def get_snapshots_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Retrieve full verifiable MemorySnapshot records across timeline."""
    exp = _resolve_experiment(id, store)
    snapshots = create_memory_snapshots(exp)
    return {
        "experiment_id": id,
        "total_snapshots": len(snapshots),
        "snapshots": [s.to_dict() for s in snapshots],
    }


@xray_router.get("/{id}/trajectory")
def get_trajectory_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Retrieve chronological state trajectory across timeline."""
    exp = _resolve_experiment(id, store)
    traj = get_state_trajectory(exp)
    return traj.to_dict()


@xray_router.post("/compare-states", response_model=CompareStatesResponse)
def compare_states_endpoint(req: CompareStatesRequest) -> Dict[str, Any]:
    """Compare two arbitrary memory state vectors using L1, L2, and cosine metrics."""
    res = compare_states(req.state_a, req.state_b)
    return res.to_dict()


@xray_router.get("/{id}/heatmaps")
def get_heatmaps_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Generate Time x Memory and Time x Unit 2D heatmap matrix arrays."""
    exp = _resolve_experiment(id, store)
    return generate_heatmap_matrices(exp)


@xray_router.get("/{id}/changes")
def get_state_changes_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Detect and classify consecutive state transitions into STABLE, SHIFT, or MAJOR_SHIFT."""
    exp = _resolve_experiment(id, store)
    traj = get_state_trajectory(exp)
    return detect_state_changes(traj)


@xray_router.get("/{id}/activation-profile")
def get_activation_profile_endpoint(
    id: str,
    step: int = Query(0, ge=0),
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Inspect activation distribution and entropy for a specific timeline step."""
    exp = _resolve_experiment(id, store)
    if step >= len(exp.snapshots):
        raise HTTPException(status_code=400, detail=f"Step {step} exceeds total snapshots.")
    vec = exp.snapshots[step].get("state_vector", [])
    prof = compute_activation_profile(vec, step=step)
    return prof.to_dict()


@xray_router.get("/{id}/sparsity")
def get_sparsity_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Analyze activation sparsity and dimensional utilization over time."""
    exp = _resolve_experiment(id, store)
    analysis = analyze_sparsity(exp)
    return analysis.to_dict()


@xray_router.get("/{id}/strength")
def get_memory_strength_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Retrieve memory representation strength trajectories for all items."""
    exp = _resolve_experiment(id, store)
    strengths_map = compute_memory_strengths(exp)
    return {
        "experiment_id": id,
        "strengths": {m_id: prof.to_dict() for m_id, prof in strengths_map.items()},
    }


@xray_router.get("/{id}/decay")
def get_decay_curves_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Retrieve empirical persistence and decay curves across all memories."""
    exp = _resolve_experiment(id, store)
    return analyze_decay_curves(exp)


@xray_router.get("/{id}/reinforcement")
def get_reinforcement_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Detect memories reinforced by subsequent events."""
    exp = _resolve_experiment(id, store)
    recs = detect_reinforcement(exp)
    return {
        "experiment_id": id,
        "reinforcement_records": [r.to_dict() for r in recs],
    }


@xray_router.get("/{id}/interference")
def get_interference_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Detect competing memories and measure cross-talk degradation."""
    exp = _resolve_experiment(id, store)
    recs = detect_interference(exp)
    return {
        "experiment_id": id,
        "interference_records": [r.to_dict() for r in recs],
    }


@xray_router.get("/{id}/competition")
def get_competition_graph_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Retrieve the memory competition, association, and reinforcement graph."""
    exp = _resolve_experiment(id, store)
    graph = build_competition_graph(exp)
    return graph.to_dict()


@xray_router.get("/{id}/clusters")
def get_clusters_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Cluster memory representations by geometric similarity."""
    exp = _resolve_experiment(id, store)
    clusters = cluster_memory_representations(exp)
    return {
        "experiment_id": id,
        "clusters": [c.to_dict() for c in clusters],
    }


@xray_router.get("/{id}/map")
def get_memory_map_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Project memory state representations onto a 2D PCA visualization map."""
    exp = _resolve_experiment(id, store)
    mmap = project_memory_map_2d(exp)
    return mmap.to_dict()


@xray_router.get("/{id}/neighbors/{memory_id}")
def get_neighbors_endpoint(
    id: str,
    memory_id: str,
    k: int = Query(5, ge=1, le=50),
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Find nearest neighbors in vector space for a target memory."""
    exp = _resolve_experiment(id, store)
    neighbors = find_nearest_memories(exp, memory_id, k=k)
    return {
        "experiment_id": id,
        "target_memory_id": memory_id,
        "neighbors": neighbors,
    }


@xray_router.get("/{id}/trace/{memory_id}")
def get_trace_endpoint(
    id: str,
    memory_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve full chronological lifecycle trace for a target memory."""
    exp = _resolve_experiment(id, store)
    trace = get_memory_trace(exp, memory_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return trace.to_dict()


@xray_router.get("/{id}/event-impact")
def get_event_impact_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Calculate before/after state transformation impact for every event."""
    exp = _resolve_experiment(id, store)
    impacts = compute_event_impact(exp)
    return {
        "experiment_id": id,
        "event_impacts": [im.to_dict() for im in impacts],
    }


@xray_router.get("/{id}/importance")
def get_importance_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Evaluate 6-dimensional importance profile for each memory."""
    exp = _resolve_experiment(id, store)
    imp_map = compute_memory_importance(exp)
    return {
        "experiment_id": id,
        "importance_profiles": {m_id: imp.to_dict() for m_id, imp in imp_map.items()},
    }


@xray_router.get("/{id}/explanation/{memory_id}")
def get_explanation_endpoint(
    id: str,
    memory_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Compile structured evidence explaining a memory's state."""
    exp = _resolve_experiment(id, store)
    expl = build_memory_explanation(exp, memory_id)
    if not expl:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return expl.to_dict()


@xray_router.get("/{id}/inspector/{event_idx}")
def get_inspector_endpoint(
    id: str,
    event_idx: int,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Inspect state microscope before and after a specific event."""
    exp = _resolve_experiment(id, store)
    return inspect_event_before_after(exp, event_idx)


@xray_router.get("/{id}/diagnostics")
def get_diagnostics_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Retrieve computational diagnostics for the memory state."""
    exp = _resolve_experiment(id, store)
    diag = compute_memory_diagnostics(exp)
    return diag.to_dict()


@xray_router.get("/{id}/anomalies")
def get_anomalies_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Detect statistically unusual state transitions and jumps."""
    exp = _resolve_experiment(id, store)
    anomalies = detect_state_anomalies(exp)
    return {
        "experiment_id": id,
        "anomalies": [a.to_dict() for a in anomalies],
    }


@xray_router.get("/{id}/checkpoint/{step}")
def get_checkpoint_endpoint(
    id: str,
    step: int,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve verified state snapshot at a timeline checkpoint."""
    exp = _resolve_experiment(id, store)
    return get_state_checkpoint(exp, step)


@xray_router.post("/{id}/replay")
def replay_control_endpoint(
    id: str,
    req: ReplayActionRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Interactive event playback step control."""
    exp = _resolve_experiment(id, store)
    controller = MemoryReplayController(exp)

    action = req.action.lower()
    if action == "start":
        return controller.start()
    elif action == "pause":
        return controller.pause()
    elif action == "resume":
        return controller.resume()
    elif action == "step_forward":
        return controller.step_forward()
    elif action == "step_backward":
        return controller.step_backward()
    elif action == "jump":
        return controller.jump_to_event(req.step_or_event_id or 0)
    else:
        raise HTTPException(status_code=400, detail=f"Unrecognized action '{req.action}'.")


@xray_router.post("/query")
def xray_query_endpoint(
    req: XRayQueryRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Execute deterministic analytical inquiry on memory state."""
    exp = _resolve_experiment(req.experiment_id, store)
    return execute_xray_query(exp, req.query, req.params)


@xray_router.post("/surgery-diff")
def surgery_diff_endpoint(
    req: SurgeryDiffRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Compare memory topological maps and graphs before and after counterfactual surgery."""
    orig_exp = _resolve_experiment(req.original_experiment_id, store)
    cf_exp = _resolve_experiment(req.counterfactual_experiment_id, store)
    return compare_xray_surgery(orig_exp, cf_exp)


@xray_router.post("/divergence")
def divergence_trace_endpoint(
    req: DivergenceTraceRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Trace state divergence and memory shifts across timelines."""
    orig_exp = _resolve_experiment(req.original_experiment_id, store)
    cf_exp = _resolve_experiment(req.counterfactual_experiment_id, store)
    return trace_divergence_xray(orig_exp, cf_exp)


@xray_router.get("/{id}/report")
def get_xray_report_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Generate comprehensive, evidence-linked Memory X-Ray report."""
    exp = _resolve_experiment(id, store)
    rep = generate_xray_report(exp)
    return rep.to_dict()


@xray_router.get("/{id}/contracts")
def get_contracts_endpoint(id: str, store: ExperimentStore = Depends(get_store)) -> Dict[str, Any]:
    """Compile visualization contracts for all 10 frontend visual targets."""
    exp = _resolve_experiment(id, store)
    return generate_visualization_contracts(exp)
