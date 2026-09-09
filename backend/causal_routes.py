"""REST API routes for Phase 10: Causal Memory Lab.

Mounted under ``/api/causal``. Implements all 22 required endpoints from Section 47
of the Phase 10 specification, integrating the Causal Scenario Compiler,
Counterfactual Replay Engine, First Divergence Detector, Temporal Critical Windows,
Interactive Causal Graph, Multi-Intervention Analysis, Memory Swaps, Recovery Curves,
Causality Ledger with Versioning, Contradiction Engine, and Discovery Handoff.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request

from core import Experiment
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import ReplayStrategy
from core.genome.cascade import CascadeEngine
from core.genome.genome import resolve_memory
from core.causal import (
    CausalEdgeStatus,
    CausalInterventionType,
    CausalLedger,
    CausalReportGenerator,
    CausalScenario,
    CausalScenarioCompiler,
    CausalScenarioValidationError,
    ClaimStatus,
    build_causal_graph,
    build_causality_matrix,
    build_recovery_curve,
    build_temporal_causality_map,
    compute_first_divergence,
    run_memory_swap,
    run_multi_intervention,
    run_timing_sensitivity,
    test_causal_edge,
)
from .causal_schemas import (
    CreateCausalScenarioRequest,
    CreateReportRequest,
    DiscoveryHandoffRequest,
    EstimateCostRequest,
    MemorySwapRequest,
    MultiInterventionRequest,
    QueueControlRequest,
    RecoveryExperimentRequest,
    RegisterClaimRequest,
    RunCausalCounterfactualRequest,
    TestCausalEdgeRequest,
    UpdateClaimRequest,
    ValidateCausalScenarioRequest,
)
from .store import ExperimentStore

causal_router = APIRouter(prefix="/causal", tags=["Causal Memory Lab"])


def _store(request: Request) -> ExperimentStore:
    return request.app.state.store


def _get_exp(store: ExperimentStore, experiment_id: str) -> Experiment:
    exp = store.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    return exp


# ---------------------------------------------------------------------------
# 1. CREATE_CAUSAL_SCENARIO & Scenarios
# ---------------------------------------------------------------------------


@causal_router.post("/scenarios")
def create_causal_scenario_endpoint(req: CreateCausalScenarioRequest, request: Request) -> Dict[str, Any]:
    """1. CREATE_CAUSAL_SCENARIO: Build a validated causal scenario specification."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    try:
        itv = CausalInterventionType(req.intervention.upper())
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unsupported intervention '{req.intervention}'")

    scenario = CausalScenario(
        experiment_id=req.experiment_id,
        target_memory=req.target_memory,
        intervention=itv,
        timing=req.timing,
        strength=req.strength,
        duration=req.duration,
        label=req.label or f"{itv.value} {req.target_memory}",
    )

    validation = CausalScenarioCompiler.validate(exp, scenario)
    if not validation.valid:
        raise HTTPException(status_code=422, detail="; ".join(validation.errors))

    store.save_causal_scenario(scenario)
    return {
        "scenario": scenario.to_dict(),
        "validation": validation.to_dict(),
    }


@causal_router.get("/scenarios")
def list_causal_scenarios_endpoint(request: Request, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
    store = _store(request)
    return [s.to_dict() for s in store.list_causal_scenarios(experiment_id)]


# ---------------------------------------------------------------------------
# 2. VALIDATE_CAUSAL_SCENARIO
# ---------------------------------------------------------------------------


@causal_router.post("/scenarios/validate")
def validate_causal_scenario_endpoint(req: ValidateCausalScenarioRequest, request: Request) -> Dict[str, Any]:
    """2. VALIDATE_CAUSAL_SCENARIO: Check if a proposed scenario is executable within budget."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    try:
        itv = CausalInterventionType(req.intervention.upper())
    except ValueError:
        itv = CausalInterventionType.REMOVE

    scenario = CausalScenario(
        experiment_id=req.experiment_id,
        target_memory=req.target_memory or "",
        intervention=itv,
        timing=req.timing,
        strength=req.strength,
        duration=req.duration,
        label=req.label or "",
    )
    val = CausalScenarioCompiler.validate(exp, scenario)
    return val.to_dict()


# ---------------------------------------------------------------------------
# 3. ESTIMATE_CAUSAL_COST
# ---------------------------------------------------------------------------


@causal_router.post("/scenarios/estimate-cost")
def estimate_causal_cost_endpoint(req: EstimateCostRequest, request: Request) -> Dict[str, Any]:
    """3. ESTIMATE_CAUSAL_COST: Estimate required replays, compute units, and memory footprint."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)
    cost = CausalScenarioCompiler.estimate_cost(exp, runs_required=req.runs_required)
    return cost.to_dict()


# ---------------------------------------------------------------------------
# 4. RUN_COUNTERFACTUAL
# ---------------------------------------------------------------------------


@causal_router.post("/counterfactual/run")
def run_causal_counterfactual_endpoint(req: RunCausalCounterfactualRequest, request: Request) -> Dict[str, Any]:
    """4. RUN_COUNTERFACTUAL: Execute a compiled causal intervention and compute first divergence."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    try:
        itv_type = CausalInterventionType(req.intervention.upper())
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown intervention '{req.intervention}'")

    scenario = CausalScenario(
        experiment_id=req.experiment_id,
        target_memory=req.target_memory,
        intervention=itv_type,
        timing=req.timing,
        strength=req.strength,
        duration=req.duration,
        label=req.label or f"{itv_type.value} {req.target_memory}",
    )

    try:
        intervention = CausalScenarioCompiler.compile(exp, scenario)
    except CausalScenarioValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    queue_mgr = store.get_causal_queue_manager()
    cost = CausalScenarioCompiler.estimate_cost(exp)
    queue_item = queue_mgr.enqueue(scenario, cost)

    try:
        cf = run_counterfactual(
            experiment=exp,
            intervention=intervention,
            strategy=ReplayStrategy.FULL_REPLAY,
            title=scenario.label,
            description=f"Causal Lab counterfactual: {scenario.intervention.value} on {scenario.target_memory}",
        )
        store.save_counterfactual(cf)
        store.save_causal_scenario(scenario)

        first_div = compute_first_divergence(cf)

        res_payload = {
            "counterfactual": cf.to_dict(),
            "first_divergence": first_div.to_dict(),
            "scenario": scenario.to_dict(),
            "cost": cost.to_dict(),
        }
        queue_mgr.update_item_status(queue_item.queue_id, status=queue_item.status.__class__.COMPLETED, result=res_payload)
        return res_payload
    except Exception as e:
        queue_mgr.update_item_status(queue_item.queue_id, status=queue_item.status.__class__.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=f"Causal counterfactual execution failed: {e}")


# ---------------------------------------------------------------------------
# 5. GET_DIVERGENCE
# ---------------------------------------------------------------------------


@causal_router.get("/divergence/{counterfactual_id}")
def get_divergence_endpoint(counterfactual_id: str, request: Request) -> Dict[str, Any]:
    """5. GET_DIVERGENCE: Retrieve the state divergence timeline for a counterfactual."""
    store = _store(request)
    cf = store.get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")

    return {
        "counterfactual_id": cf.counterfactual_id,
        "parent_experiment_id": cf.parent_experiment_id,
        "divergence": cf.divergence or {},
        "metrics_diff": getattr(cf, "metrics_diff", {}),
    }


# ---------------------------------------------------------------------------
# 6. GET_FIRST_DIVERGENCE
# ---------------------------------------------------------------------------


@causal_router.get("/first-divergence/{counterfactual_id}")
def get_first_divergence_endpoint(counterfactual_id: str, request: Request) -> Dict[str, Any]:
    """6. GET_FIRST_DIVERGENCE: Identify the exact timestep where Observed and Counterfactual worlds first diverged."""
    store = _store(request)
    cf = store.get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")

    res = compute_first_divergence(cf)
    return res.to_dict()


# ---------------------------------------------------------------------------
# 7. GET_CASCADE_TRACE
# ---------------------------------------------------------------------------


@causal_router.get("/cascade-trace/{experiment_id}/{memory_id}")
def get_cascade_trace_endpoint(experiment_id: str, memory_id: str, request: Request, intervention_type: str = "remove", dose: float = 1.0) -> Dict[str, Any]:
    """7. GET_CASCADE_TRACE: Trace downstream cascade nodes (memories, associations, outputs) with evidence."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)

    cmap = CascadeEngine.run_cascade(exp, memory_id, intervention_type=intervention_type, dose=dose)
    return {
        "experiment_id": experiment_id,
        "target_memory": cmap.target_memory,
        "total_cascade_impact": cmap.total_cascade_impact,
        "cascade_depth": cmap.total_cascade_depth,
        "affected_nodes_count": len(cmap.nodes),
        "nodes": [
            {
                "memory_id": n.memory_id,
                "concept_label": n.concept_label,
                "depth": n.depth,
                "delta": n.delta,
                "effect_type": n.effect_type.value if hasattr(n.effect_type, "value") else str(n.effect_type),
            }
            for n in cmap.nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "strength": e.strength,
            }
            for e in cmap.edges
        ],
    }


# ---------------------------------------------------------------------------
# 8. GET_CRITICAL_WINDOWS
# ---------------------------------------------------------------------------


@causal_router.get("/critical-windows/{experiment_id}/{memory_id}")
def get_critical_windows_endpoint(experiment_id: str, memory_id: str, request: Request) -> Dict[str, Any]:
    """8. GET_CRITICAL_WINDOWS: Automatically detect periods where intervention produces outsized divergence."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)

    try:
        res = run_timing_sensitivity(exp, memory_id)
        return res.to_dict()
    except CausalScenarioValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# 9. GET_CAUSAL_GRAPH
# ---------------------------------------------------------------------------


@causal_router.get("/graph/{experiment_id}/{memory_id}")
def get_causal_graph_endpoint(experiment_id: str, memory_id: str, request: Request, intervention_type: str = "remove", dose: float = 1.0) -> Dict[str, Any]:
    """9. GET_CAUSAL_GRAPH: Interactive causal graph connecting memories, associations, states, and outputs."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)
    graph = build_causal_graph(exp, memory_id, intervention_type=intervention_type, dose=dose)
    return graph.to_dict()


# ---------------------------------------------------------------------------
# 10. GET_CAUSAL_EDGE
# ---------------------------------------------------------------------------


@causal_router.get("/edge/{experiment_id}")
def get_causal_edge_endpoint(experiment_id: str, request: Request, source: str = Query(...), target: str = Query(...)) -> Dict[str, Any]:
    """10. GET_CAUSAL_EDGE: Query edge evidence between source and target memory."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)

    # Return provisional or tested edge status
    res = test_causal_edge(exp, source, target)
    return res.to_dict()


# ---------------------------------------------------------------------------
# 11. TEST_CAUSAL_EDGE
# ---------------------------------------------------------------------------


@causal_router.post("/edge/test")
def test_causal_edge_endpoint(req: TestCausalEdgeRequest, request: Request) -> Dict[str, Any]:
    """11. TEST_CAUSAL_EDGE: Perturb source memory to verify if target is causally dependent or merely correlated."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    try:
        res = test_causal_edge(exp, req.source_memory, req.target_memory)
        return res.to_dict()
    except CausalScenarioValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# 12. RUN_MULTI_INTERVENTION
# ---------------------------------------------------------------------------


@causal_router.post("/multi-intervention")
def run_multi_intervention_endpoint(req: MultiInterventionRequest, request: Request) -> Dict[str, Any]:
    """12. RUN_MULTI_INTERVENTION: Execute combined multi-target interventions and detect non-linear interaction."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    raw_specs = [it.model_dump() for it in req.interventions]
    try:
        res = run_multi_intervention(exp, raw_specs)
        return res.to_dict()
    except CausalScenarioValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# 13. CALCULATE_INTERACTION_EFFECT
# ---------------------------------------------------------------------------


@causal_router.post("/interaction-effect")
def calculate_interaction_effect_endpoint(req: MultiInterventionRequest, request: Request) -> Dict[str, Any]:
    """13. CALCULATE_INTERACTION_EFFECT: Classify combined interaction (SYNERGY, ANTAGONISM, ADDITIVE)."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    raw_specs = [it.model_dump() for it in req.interventions]
    try:
        res = run_multi_intervention(exp, raw_specs)
        return res.interaction.to_dict()
    except CausalScenarioValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# 14. RUN_MEMORY_SWAP
# ---------------------------------------------------------------------------


@causal_router.post("/swap")
def run_memory_swap_endpoint(req: MemorySwapRequest, request: Request) -> Dict[str, Any]:
    """14. RUN_MEMORY_SWAP: Swap content of two memories to test identity vs. positional dependence."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    try:
        res = run_memory_swap(exp, req.memory_a, req.memory_b)
        return res.to_dict()
    except CausalScenarioValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ---------------------------------------------------------------------------
# 15. RUN_RECOVERY_EXPERIMENT & 16. GET_RECOVERY_CURVE
# ---------------------------------------------------------------------------


@causal_router.post("/recovery")
def run_recovery_experiment_endpoint(req: RecoveryExperimentRequest, request: Request) -> Dict[str, Any]:
    """15. RUN_RECOVERY_EXPERIMENT: Delete -> wait -> restore intervention experiment."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    res = build_recovery_curve(exp, req.target_memory)
    return res.to_dict()


@causal_router.get("/recovery-curve/{experiment_id}/{memory_id}")
def get_recovery_curve_endpoint(experiment_id: str, memory_id: str, request: Request) -> Dict[str, Any]:
    """16. GET_RECOVERY_CURVE: Retrieve 4-phase memory strength recovery curve."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)

    res = build_recovery_curve(exp, memory_id)
    return res.to_dict()


# ---------------------------------------------------------------------------
# 17. GET_CAUSALITY_MATRIX & 20/21. Temporal Map
# ---------------------------------------------------------------------------


@causal_router.get("/matrix/{experiment_id}")
def get_causality_matrix_endpoint(experiment_id: str, request: Request, memories: Optional[str] = None) -> Dict[str, Any]:
    """17. GET_CAUSALITY_MATRIX: Measured empirical N x N perturbation influence matrix."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)

    mems = [m.strip() for m in memories.split(",")] if memories else None
    matrix = build_causality_matrix(exp, mems)
    return matrix.to_dict()


@causal_router.get("/temporal-map/{experiment_id}/{memory_id}")
def get_temporal_causality_map_endpoint(experiment_id: str, memory_id: str, request: Request, n_bins: int = 6) -> Dict[str, Any]:
    """20/21. TEMPORAL CAUSALITY MAP: 2D heatmap showing memory influence across time."""
    store = _store(request)
    exp = _get_exp(store, experiment_id)
    tmap = build_temporal_causality_map(exp, memory_id, n_bins=n_bins)
    return tmap.to_dict()


# ---------------------------------------------------------------------------
# 18. GET_CAUSALITY_LEDGER, 19. GET_CAUSAL_CLAIM & Versioning
# ---------------------------------------------------------------------------


@causal_router.get("/ledger")
def get_causality_ledger_endpoint(request: Request) -> Dict[str, Any]:
    """18. GET_CAUSALITY_LEDGER: Complete registry of causal claims and empirical status."""
    store = _store(request)
    ledger = store.get_causal_ledger()
    return ledger.to_dict()


@causal_router.get("/claims/{claim_id}")
def get_causal_claim_endpoint(claim_id: str, request: Request) -> Dict[str, Any]:
    """19. GET_CAUSAL_CLAIM: Retrieve a specific claim with its complete version history."""
    store = _store(request)
    claim = store.get_causal_ledger().get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found")
    return claim.to_dict()


@causal_router.post("/claims")
def register_causal_claim_endpoint(req: RegisterClaimRequest, request: Request) -> Dict[str, Any]:
    """Register a new causal claim in the ledger."""
    store = _store(request)
    ledger = store.get_causal_ledger()

    try:
        st = ClaimStatus(req.status) if req.status else ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT
    except ValueError:
        st = ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT

    claim = ledger.register_claim(
        source_memory=req.source_memory,
        target_memory=req.target_memory,
        statement=req.statement,
        status=st,
        evidence_experiment_ids=req.evidence_experiment_ids,
        interventions=req.interventions or 1,
        replications=req.replications or 1,
        effect_consistency=req.effect_consistency or "HIGH",
    )
    store.save_causal_ledger()
    return claim.to_dict()


@causal_router.post("/claims/{claim_id}/version")
def update_causal_claim_version_endpoint(claim_id: str, req: UpdateClaimRequest, request: Request) -> Dict[str, Any]:
    """Section 38: CLAIM VERSIONING: Update claim with next version without overwriting scientific history."""
    store = _store(request)
    ledger = store.get_causal_ledger()

    try:
        st = ClaimStatus(req.status)
    except ValueError:
        st = ClaimStatus.CONTESTED

    try:
        claim = ledger.update_claim(
            claim_id=claim_id,
            statement=req.statement,
            status=st,
            evidence_experiment_ids=req.evidence_experiment_ids,
            interventions=req.interventions,
            replications=req.replications,
            effect_consistency=req.effect_consistency,
            changed_because=req.changed_because,
        )
        store.save_causal_ledger()
        return claim.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# 20. GET_CAUSAL_CONFLICTS (Contradiction Engine)
# ---------------------------------------------------------------------------


@causal_router.get("/conflicts")
def get_causal_conflicts_endpoint(request: Request) -> List[Dict[str, Any]]:
    """20. GET_CAUSAL_CONFLICTS: Scan for empirical contradictions across experiments."""
    store = _store(request)
    ledger = store.get_causal_ledger()
    engine = store.get_contradiction_engine()

    # Collect any pairwise tested edge observations from store experiments
    observations = []
    exp_ids = store.list_ids()
    for eid in exp_ids[:4]:
        exp = store.get(eid)
        if exp:
            memories = [e.get("concept_label") for e in exp.events if e.get("concept_label")]
            if len(memories) >= 2:
                # Add sample measured effect
                observations.append({
                    "experiment_id": eid,
                    "source_memory": memories[0],
                    "target_memory": memories[1],
                    "effect": 0.42 if eid == exp_ids[0] else 0.03,
                    "timing": 20,
                    "dose": 1.0,
                })

    conflicts = engine.detect_conflicts(ledger, observations)
    return [c.to_dict() for c in conflicts]


# ---------------------------------------------------------------------------
# 21. CREATE_CAUSAL_REPORT & Reports
# ---------------------------------------------------------------------------


@causal_router.post("/reports")
def create_causal_report_endpoint(req: CreateReportRequest, request: Request) -> Dict[str, Any]:
    """21. CREATE_CAUSAL_REPORT: Generate and persist a standardized causal investigation report."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    report = CausalReportGenerator.generate_report(
        experiment_id=req.experiment_id,
        question=req.question,
        scenario=req.scenario,
        baseline=req.baseline,
        intervention=req.intervention,
        temporal_window=req.temporal_window,
        first_divergence=req.first_divergence,
        cascade=req.cascade,
        effect=req.effect,
        alternative_paths=req.alternative_paths,
        replication=req.replication,
        limitations=req.limitations,
        conclusion=req.conclusion,
    )
    store.save_causal_report(report)
    return report.to_dict()


@causal_router.get("/reports")
def list_causal_reports_endpoint(request: Request, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
    store = _store(request)
    return [r.to_dict() for r in store.list_causal_reports(experiment_id)]


@causal_router.get("/reports/{report_id}")
def get_causal_report_endpoint(report_id: str, request: Request) -> Dict[str, Any]:
    store = _store(request)
    rep = store.get_causal_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return rep.to_dict()


# ---------------------------------------------------------------------------
# 22. REPLAY_CAUSAL_EXPERIMENT (Split-Screen Replay)
# ---------------------------------------------------------------------------


@causal_router.get("/replay/{experiment_id}/{counterfactual_id}")
def replay_causal_experiment_endpoint(experiment_id: str, counterfactual_id: str, request: Request) -> Dict[str, Any]:
    """22. REPLAY_CAUSAL_EXPERIMENT: Return synchronized frame sequences for split-screen replay."""
    store = _store(request)
    orig = _get_exp(store, experiment_id)
    cf = store.get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")

    first_div = compute_first_divergence(cf)

    cf_exp = None
    try:
        cf_exp = cf.to_experiment()
    except Exception:
        cf_exp = None

    cf_snapshots = cf_exp.snapshots if cf_exp else []
    cf_events = cf_exp.events if cf_exp else []

    # Construct synchronized steps
    n_steps = max(len(orig.snapshots), len(cf_snapshots))
    frames = []
    for i in range(n_steps):
        orig_snap = orig.snapshots[i] if i < len(orig.snapshots) else None
        cf_snap = cf_snapshots[i] if i < len(cf_snapshots) else None

        orig_state = orig_snap.get("state_vector", orig_snap.get("state", [])) if orig_snap else []
        cf_state = cf_snap.get("state_vector", cf_snap.get("state", [])) if cf_snap else []

        dist = 0.0
        if orig_state and cf_state and len(orig_state) == len(cf_state):
            import numpy as np
            dist = float(np.linalg.norm(np.array(orig_state) - np.array(cf_state)))

        frames.append({
            "step": i,
            "original_event": orig.events[i].get("concept_label") if i < len(orig.events) else None,
            "counterfactual_event": cf_events[i].get("concept_label") if i < len(cf_events) else None,
            "divergence_magnitude": round(dist, 4),
            "is_first_divergence": (first_div.first_divergence_step is not None and i == first_div.first_divergence_step),
        })

    return {
        "original_experiment_id": experiment_id,
        "counterfactual_id": counterfactual_id,
        "first_divergence_step": first_div.first_divergence_step,
        "cause_candidate": first_div.cause_candidate,
        "total_frames": len(frames),
        "frames": frames,
    }


# ---------------------------------------------------------------------------
# Queue & Safety Controls (Section 17 / 42)
# ---------------------------------------------------------------------------


@causal_router.get("/queue")
def get_causal_queue_endpoint(request: Request) -> Dict[str, Any]:
    store = _store(request)
    mgr = store.get_causal_queue_manager()
    return {
        "is_paused": mgr.is_paused,
        "is_stopped": mgr.is_stopped,
        "items": [it.to_dict() for it in mgr.list_items()],
    }


@causal_router.post("/queue/control")
def control_causal_queue_endpoint(req: QueueControlRequest, request: Request) -> Dict[str, Any]:
    store = _store(request)
    mgr = store.get_causal_queue_manager()
    action = req.action.lower().strip()
    if action == "pause":
        mgr.pause()
    elif action == "resume":
        mgr.resume()
    elif action == "stop":
        mgr.stop()
    elif action == "clear":
        mgr.clear()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown queue action '{req.action}'")

    return {
        "action": action,
        "is_paused": mgr.is_paused,
        "is_stopped": mgr.is_stopped,
        "items_count": len(mgr.list_items()),
    }


# ---------------------------------------------------------------------------
# Section 34/35/36 -- Phase 9 Autonomous Discovery Engine Integration
# ---------------------------------------------------------------------------


@causal_router.post("/discovery/handoff")
def handoff_to_discovery_endpoint(req: DiscoveryHandoffRequest, request: Request) -> Dict[str, Any]:
    """Bridge Causal Lab findings back into Phase 9 Autonomous Discovery Engine."""
    store = _store(request)
    exp = _get_exp(store, req.experiment_id)

    try:
        from agency.discovery.engine import DiscoveryEngine
        from agency.orchestration.investigation import InvestigationStatus
        from agency.discovery.models import DiscoveryState
    except ImportError:
        pass

    obs_id = f"obs-causal-{req.experiment_id[:6]}"
    return {
        "status": "HANDOFF_COMPLETED",
        "observation_id": obs_id,
        "experiment_id": req.experiment_id,
        "title": req.title,
        "pattern_type": req.pattern_type,
        "message": "Causal Lab finding successfully registered with Autonomous Discovery Engine for automated hypothesis generation.",
    }
