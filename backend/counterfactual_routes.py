"""REST API endpoints for Counterfactual Memory Archaeology (Phase 04).

Mounted under ``/api/counterfactual``. Provides endpoints for running counterfactuals,
ablations, memory surgeries, divergence analysis, what-if searches, minimal intervention
discovery, forensic forgetting reconstruction, timeline tree exploration, and exports.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response

from core.experiment import Experiment
from core.counterfactual import (
    CounterfactualExperiment,
    CounterfactualValidationError,
    Intervention,
    InterventionType,
    ReplayStrategy,
    Timeline,
    compare_multiple_histories,
    compare_synaptic_states_at_step,
    create_ablation,
    create_surgery,
    diff_histories,
    estimate_event_contribution,
    export_counterfactual_json,
    export_divergence_csv,
    find_minimal_intervention,
    reproduce_counterfactual,
    run_counterfactual,
    search_counterfactuals,
)

from .counterfactual_schemas import (
    AblationRequest,
    CompareHistoriesRequest,
    CompareMultipleHistoriesRequest,
    ContributionRequest,
    DiffHistoriesRequest,
    MinimalInterventionRequest,
    ReproduceCounterfactualRequest,
    RunCounterfactualRequest,
    SearchCounterfactualsRequest,
    SurgeryRequest,
    SynapticCompareRequest,
    SynapticInterventionRequest,
)
from .store import ExperimentStore

router = APIRouter(prefix="/counterfactual", tags=["Counterfactual Memory Archaeology"])


def _store(request: Request) -> ExperimentStore:
    return request.app.state.store


@router.post("/run")
def run_counterfactual_endpoint(req: RunCounterfactualRequest, request: Request) -> Dict[str, Any]:
    """Execute a counterfactual intervention against an existing memory experiment."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    try:
        intv = Intervention.from_dict(req.intervention.model_dump())
        strat = ReplayStrategy(req.strategy) if req.strategy else ReplayStrategy.FULL_REPLAY
        cf = run_counterfactual(
            experiment=exp,
            intervention=intv,
            strategy=strat,
            title=req.title or "",
            description=req.description or "",
        )
        store.save_counterfactual(cf)
        return cf.to_dict()
    except CounterfactualValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counterfactual replay failed: {e}")


@router.post("/ablate")
def create_ablation_endpoint(req: AblationRequest, request: Request) -> Dict[str, Any]:
    """Surgically ablate a single historical event and observe downstream divergence."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    try:
        cf = create_ablation(
            experiment=exp,
            event_id_or_timestep=req.event_id_or_timestep,
            title=req.title or "",
        )
        store.save_counterfactual(cf)
        return cf.to_dict()
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/surgery")
def create_surgery_endpoint(req: SurgeryRequest, request: Request) -> Dict[str, Any]:
    """Surgically modify properties of a historical event and replay."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    try:
        cf = create_surgery(
            experiment=exp,
            event_id_or_timestep=req.event_id_or_timestep,
            modifications=req.modifications,
            title=req.title or "",
        )
        store.save_counterfactual(cf)
        return cf.to_dict()
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("")
def list_counterfactuals_endpoint(
    request: Request,
    parent_id: Optional[str] = Query(None, description="Filter by parent experiment ID"),
) -> List[Dict[str, Any]]:
    """List all saved counterfactual experiments."""
    cfs = _store(request).list_counterfactuals(parent_id=parent_id)
    return [cf.to_dict() for cf in cfs]


@router.get("/{counterfactual_id}")
def get_counterfactual_endpoint(counterfactual_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve a full counterfactual record by ID."""
    cf = _store(request).get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")
    return cf.to_dict()


@router.get("/{counterfactual_id}/divergence")
def get_divergence_endpoint(counterfactual_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve the step-by-step divergence profile of a counterfactual experiment."""
    cf = _store(request).get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")
    return cf.divergence


@router.post("/compare")
def compare_histories_endpoint(req: CompareHistoriesRequest, request: Request) -> Dict[str, Any]:
    """Compare an original history against a counterfactual history."""
    store = _store(request)
    orig = store.get(req.original_experiment_id)
    if not orig:
        raise HTTPException(status_code=404, detail=f"Original experiment '{req.original_experiment_id}' not found")

    cf = store.get_counterfactual(req.counterfactual_experiment_id)
    if cf:
        return cf.comparison

    # Fallback to base experiment comparison
    cf_exp = store.get(req.counterfactual_experiment_id)
    if not cf_exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.counterfactual_experiment_id}' not found")

    return diff_histories(orig, cf_exp)


@router.post("/compare-multiple")
def compare_multiple_endpoint(req: CompareMultipleHistoriesRequest, request: Request) -> Dict[str, Any]:
    """Compare multiple timelines side-by-side against the root history."""
    store = _store(request)
    histories = []
    for hid in req.experiment_ids:
        exp = store.get(hid)
        if exp:
            histories.append(exp)
        else:
            cf = store.get_counterfactual(hid)
            if cf:
                histories.append({
                    "experiment_id": cf.counterfactual_id,
                    "metrics": cf.counterfactual_result.get("metrics", {}),
                    "events": cf.original_configuration.get("task", {}).get("events", []),
                    "snapshots": [],
                })
            else:
                raise HTTPException(status_code=404, detail=f"History '{hid}' not found")

    return compare_multiple_histories(histories)


@router.post("/diff")
def diff_histories_endpoint(req: DiffHistoriesRequest, request: Request) -> Dict[str, Any]:
    """Compute structural event differences, metric shifts, and state diff between two histories."""
    store = _store(request)
    ea = store.get(req.experiment_id_a)
    eb = store.get(req.experiment_id_b)
    if not ea:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id_a}' not found")
    if not eb:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id_b}' not found")
    return diff_histories(ea, eb)


@router.post("/search")
def search_counterfactuals_endpoint(req: SearchCounterfactualsRequest, request: Request) -> Dict[str, Any]:
    """Search over an intervention space to find the counterfactual that most improves a metric."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    return search_counterfactuals(
        experiment=exp,
        target_metric=req.target_metric,
        target_direction=req.target_direction,
        allowed_interventions=req.allowed_interventions,
        max_candidates=req.max_candidates,
    )


@router.post("/minimal-intervention")
def minimal_intervention_endpoint(req: MinimalInterventionRequest, request: Request) -> Dict[str, Any]:
    """Find the smallest-magnitude intervention meeting or exceeding a target metric improvement."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    return find_minimal_intervention(
        experiment=exp,
        target_metric=req.target_metric,
        target_improvement=req.target_improvement,
        target_direction=req.target_direction,
        allowed_interventions=req.allowed_interventions,
        max_candidates=req.max_candidates,
    )


@router.post("/contribution")
def contribution_analysis_endpoint(req: ContributionRequest, request: Request) -> Dict[str, Any]:
    """Perform forensic forgetting reconstruction by evaluating single-event counterfactual contributions."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    return estimate_event_contribution(
        experiment=exp,
        target_metric=req.target_metric,
        target_object=req.target_object,
        max_candidates=req.max_candidates,
    )


@router.post("/reproduce")
def reproduce_counterfactual_endpoint(req: ReproduceCounterfactualRequest, request: Request) -> Dict[str, Any]:
    """Verify bit-exact reproducibility of a counterfactual execution within numerical tolerance."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Base experiment '{req.experiment_id}' not found")

    intv = Intervention.from_dict(req.intervention.model_dump())
    return reproduce_counterfactual(
        original_experiment=exp,
        intervention=intv,
        expected_metrics=req.expected_metrics,
        tolerance=req.tolerance,
    )


@router.get("/tree/{history_id}")
def get_counterfactual_tree_endpoint(history_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve the branching timeline tree rooted at history_id."""
    tree = _store(request).get_counterfactual_tree(history_id)
    return tree.to_dict()


@router.get("/timeline/{history_id}")
def get_timeline_endpoint(history_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve the ordered historical timeline with states and events."""
    store = _store(request)
    exp = store.get(history_id)
    if exp:
        tl = Timeline(
            timeline_id=exp.experiment_id,
            experiment_id=exp.experiment_id,
            events=exp.events,
            snapshots=exp.snapshots,
            queries=exp.queries,
            metrics=exp.metrics,
            is_original=True,
        )
        return tl.to_dict()

    cf = store.get_counterfactual(history_id)
    if cf:
        return cf.to_dict()

    raise HTTPException(status_code=404, detail=f"Timeline '{history_id}' not found")


@router.get("/{counterfactual_id}/export/json")
def export_json_endpoint(counterfactual_id: str, request: Request) -> Response:
    """Export complete counterfactual record as JSON."""
    cf = _store(request).get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")
    content = export_counterfactual_json(cf)
    return Response(content=content, media_type="application/json")


@router.get("/{counterfactual_id}/export/csv")
def export_csv_endpoint(counterfactual_id: str, request: Request) -> Response:
    """Export divergence curve as CSV."""
    cf = _store(request).get_counterfactual(counterfactual_id)
    if not cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual '{counterfactual_id}' not found")
    content = export_divergence_csv(cf)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{counterfactual_id}_divergence.csv"'},
    )


@router.post("/synaptic-intervention")
def synaptic_intervention_endpoint(req: SynapticInterventionRequest, request: Request) -> Dict[str, Any]:
    """Execute a controlled synaptic or mechanism counterfactual intervention."""
    store = _store(request)
    exp = store.get(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    try:
        itype = InterventionType(req.intervention_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported intervention type '{req.intervention_type}'")

    params: Dict[str, Any] = {}
    if req.synapse_id:
        params["synapse_id"] = req.synapse_id
    if req.factor is not None:
        params["factor"] = float(req.factor)
    if req.new_decay is not None:
        params["new_decay"] = float(req.new_decay)
    if req.new_update_strength is not None:
        params["new_update_strength"] = float(req.new_update_strength)

    desc = req.hypothesis or ""
    if not desc:
        if itype == InterventionType.SYNAPSE_PREVENT_STRENGTHEN:
            desc = f"What if {req.synapse_id} had NOT strengthened at T>={req.target_timestep}?"
        elif itype == InterventionType.SYNAPSE_SILENCE:
            desc = f"What if connection {req.synapse_id} was silenced at T>={req.target_timestep}?"
        elif itype == InterventionType.SYNAPSE_SCALE:
            desc = f"What if {req.synapse_id} was scaled by {req.factor}x at T={req.target_timestep}?"
        elif itype == InterventionType.CHANGE_DECAY:
            desc = f"What if decay happened at rate {req.new_decay}?"
        elif itype == InterventionType.CHANGE_PLASTICITY:
            desc = f"What if memory was written with plasticity {req.new_update_strength}?"

    intv = Intervention(
        intervention_type=itype,
        target_timestep=req.target_timestep,
        parameters=params,
        description=desc,
        metadata={"hypothesis": req.hypothesis or "", "baseline_experiment_id": exp.experiment_id},
    )

    try:
        cf = run_counterfactual(
            experiment=exp,
            intervention=intv,
            title=req.title or desc,
            description=req.hypothesis or desc,
        )
        saved_cf = store.save_counterfactual(cf)

        cf_exp_dict = cf.counterfactual_result.get("experiment")
        if cf_exp_dict and isinstance(cf_exp_dict, dict):
            try:
                cf_exp_obj = Experiment.from_dict(cf_exp_dict)
                store.save(cf_exp_obj)
            except Exception:
                pass

        return {
            "status": "success",
            "counterfactual": saved_cf.to_dict(),
            "counterfactual_id": saved_cf.counterfactual_id,
            "branch_point": saved_cf.provenance.get("branch_point", 0),
            "variable_controlled": desc,
            "metrics_original": exp.metrics,
            "metrics_counterfactual": saved_cf.counterfactual_result.get("metrics", {}),
        }
    except CounterfactualValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(exc)}")


@router.post("/synaptic-compare")
def synaptic_compare_endpoint(req: SynapticCompareRequest, request: Request) -> Dict[str, Any]:
    """Forensically compare original and counterfactual network states at exact timestep T."""
    store = _store(request)
    exp_orig = store.get(req.original_experiment_id)
    if not exp_orig:
        raise HTTPException(status_code=404, detail=f"Original experiment '{req.original_experiment_id}' not found")

    cf = store.get_counterfactual(req.counterfactual_id)
    exp_cf: Optional[Experiment] = None

    if cf:
        cf_exp_dict = cf.counterfactual_result.get("experiment")
        if cf_exp_dict and isinstance(cf_exp_dict, dict):
            exp_cf = Experiment.from_dict(cf_exp_dict)

    if not exp_cf:
        exp_cf = store.get(req.counterfactual_id)

    if not exp_cf:
        raise HTTPException(status_code=404, detail=f"Counterfactual experiment '{req.counterfactual_id}' not found")

    div_step = cf.provenance.get("branch_point") if cf else 0
    desc = cf.intervention.get("description", "") if cf else ""

    result = compare_synaptic_states_at_step(
        original_experiment=exp_orig,
        counterfactual_experiment=exp_cf,
        step_idx=req.step_idx,
        display_dim=req.display_dim,
        divergence_step=div_step,
        intervention_desc=desc,
    )
    return result


@router.get("/branches/{experiment_id}")
def get_experiment_branches_endpoint(experiment_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve all counterfactual branches derived from this experiment."""
    store = _store(request)
    exp = store.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    cfs = store.list_counterfactuals(parent_id=experiment_id)
    branches = []
    for cf in cfs:
        orig_acc = cf.original_result.get("metrics", {}).get("recall_accuracy")
        cf_acc = cf.counterfactual_result.get("metrics", {}).get("recall_accuracy")
        branches.append({
            "branch_id": cf.counterfactual_id,
            "title": cf.title,
            "description": cf.description,
            "intervention_type": cf.intervention_type,
            "divergence_step": cf.provenance.get("branch_point", 0),
            "target_synapse": cf.intervention.get("parameters", {}).get("synapse_id"),
            "original_accuracy": orig_acc,
            "counterfactual_accuracy": cf_acc,
            "accuracy_delta": (float(cf_acc) - float(orig_acc)) if orig_acc is not None and cf_acc is not None else 0.0,
            "created_at": cf.created_at,
            "status": cf.status.value if hasattr(cf.status, "value") else str(cf.status),
        })

    return {
        "experiment_id": experiment_id,
        "total_branches": len(branches),
        "branches": branches,
    }

