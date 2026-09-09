"""REST API endpoints for Experiment Lab (Phase 03).

Mounted under ``/api/lab``. Provides endpoints for experimental inquiry, variable metadata,
parameter sweeps, 2D landscapes, hypothesis testing, competing hypothesis comparison,
discriminating experiment discovery, next-experiment suggestion, lineage, and export.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response

from core.lab import (
    ComparisonResult,
    CompetingHypothesesGroup,
    EdgeType,
    ExperimentValidationError,
    ExperimentValidator,
    Hypothesis,
    HypothesisStatus,
    LabExperiment,
    PredictedDirection,
    Prediction,
    PredictionEvaluation,
    SweepResult,
    VARIABLE_REGISTRY,
    diff_lab_experiments,
    evaluate_prediction,
    export_experiment_csv,
    export_experiment_json,
    find_discriminating_experiment,
    generate_scientific_report,
    reproduce_lab_experiment,
    run_controlled_comparison,
    run_grid_sweep,
    run_parameter_sweep,
    suggest_next_experiment,
    update_hypothesis_with_evidence,
)

from .lab_schemas import (
    CompetingHypothesesRequest,
    ControlledComparisonRequest,
    CreateHypothesisRequest,
    DiffExperimentsRequest,
    DiscriminatingExperimentRequest,
    EvaluateHypothesisRequest,
    GridSweepRequest,
    LabExperimentCreateRequest,
    ParameterSweepRequest,
    ReproduceExperimentRequest,
    SuggestNextRequest,
)
from .store import ExperimentStore

router = APIRouter(prefix="/lab", tags=["Experiment Lab"])


def _store(request: Request) -> ExperimentStore:
    return request.app.state.store


# ---------------------------------------------------------------------------
# Variable Registry Metadata
# ---------------------------------------------------------------------------
@router.get("/variables")
def list_variables() -> Dict[str, Any]:
    """Retrieve catalog of all experimental variables, roles, types, and constraints."""
    vars_list = [v.to_dict() for v in VARIABLE_REGISTRY.list_all()]
    return {
        "variables": vars_list,
        "count": len(vars_list),
        "independent": [v["name"] for v in vars_list if v["role"] == "independent"],
        "dependent": [v["name"] for v in vars_list if v["role"] == "dependent"],
        "controlled": [v["name"] for v in vars_list if v["role"] == "controlled"],
    }


# ---------------------------------------------------------------------------
# Experiments CRUD & Execution
# ---------------------------------------------------------------------------
@router.post("/experiments")
def create_lab_experiment(req: LabExperimentCreateRequest, request: Request) -> Dict[str, Any]:
    """Create a new LabExperiment record and optionally execute immediately."""
    data = req.model_dump()
    val_res = ExperimentValidator.validate_lab_experiment(data)
    if not val_res.valid:
        raise HTTPException(status_code=400, detail=val_res.errors)

    exp_id = f"lab-{uuid.uuid4().hex[:10]}"
    lab_exp = LabExperiment(
        experiment_id=exp_id,
        title=req.title,
        research_question=req.research_question,
        hypothesis=req.hypothesis,
        hypothesis_id=req.hypothesis_id,
        objective=req.objective,
        mechanism=req.mechanism,
        independent_variables=req.independent_variables,
        dependent_variables=req.dependent_variables,
        controlled_variables=req.controlled_variables,
        baseline_configuration=req.baseline_configuration,
        treatment_configurations=req.treatment_configurations,
        seed=req.seed,
        trials=req.trials,
    )

    if req.run_immediately:
        from core.lab.models import ExperimentStatus
        from core.lab.runner import run_condition_trials

        # Run baseline
        base_res = run_condition_trials(
            "baseline",
            req.baseline_configuration or {"mechanism": req.mechanism},
            master_seed=req.seed,
            trials=req.trials,
        )
        conditions = [base_res]

        for i, treat in enumerate(req.treatment_configurations):
            t_res = run_condition_trials(
                f"treatment_{i+1}",
                treat,
                master_seed=req.seed,
                trials=req.trials,
            )
            conditions.append(t_res)

        lab_exp.results = conditions
        lab_exp.status = ExperimentStatus.COMPLETED
        lab_exp.metrics = {k: v["mean"] for k, v in base_res.aggregated_metrics.items()}
        lab_exp.conclusion = f"Completed {len(conditions)} condition(s) across {req.trials} trial(s)."

    _store(request).save_lab_experiment(lab_exp)

    # Link hypothesis in graph if specified
    if req.hypothesis_id:
        _store(request).get_graph().add_edge(
            source_id=lab_exp.experiment_id,
            target_id=req.hypothesis_id,
            edge_type=EdgeType.TESTS,
        )
        _store(request).save_graph()

    return lab_exp.to_dict()


@router.get("/experiments")
def list_lab_experiments(request: Request) -> Dict[str, Any]:
    """List all saved lab experiments."""
    exps = _store(request).list_lab_experiments()
    return {
        "experiments": [
            {
                "experiment_id": e.experiment_id,
                "title": e.title,
                "research_question": e.research_question,
                "mechanism": e.mechanism,
                "status": e.status.value,
                "version": e.version,
                "created_at": e.created_at,
            }
            for e in exps
        ],
        "count": len(exps),
    }


@router.get("/experiments/{experiment_id}")
def get_lab_experiment(experiment_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve full details, results, and provenance of a lab experiment."""
    exp = _store(request).get_lab_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Lab experiment '{experiment_id}' not found")
    return exp.to_dict()


@router.post("/experiments/{experiment_id}/reproduce")
def reproduce_experiment_endpoint(
    experiment_id: str, req: ReproduceExperimentRequest, request: Request
) -> Dict[str, Any]:
    """Verify deterministic reproducibility by re-executing stored configuration."""
    exp = _store(request).get_lab_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Lab experiment '{experiment_id}' not found")

    base_cfg = exp.baseline_configuration or {"mechanism": exp.mechanism}
    res = reproduce_lab_experiment(
        original_config=base_cfg,
        expected_metrics=exp.metrics,
        seed=exp.seed,
        trials=exp.trials,
        tolerance=req.tolerance,
    )

    if res["exact_match"]:
        _store(request).get_graph().add_edge(
            source_id=res["reproduced_experiment_id"],
            target_id=experiment_id,
            edge_type=EdgeType.REPRODUCES,
        )
        _store(request).save_graph()

    return res


@router.post("/experiments/diff")
def diff_experiments_endpoint(req: DiffExperimentsRequest, request: Request) -> Dict[str, Any]:
    """Compare two lab experiments and return structured differences."""
    a = _store(request).get_lab_experiment(req.experiment_id_a)
    if not a:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id_a}' not found")
    b = _store(request).get_lab_experiment(req.experiment_id_b)
    if not b:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id_b}' not found")

    return diff_lab_experiments(a, b)


# ---------------------------------------------------------------------------
# 1D Parameter Sweep & 2D Grid Sweep
# ---------------------------------------------------------------------------
@router.post("/sweep")
def parameter_sweep_endpoint(req: ParameterSweepRequest, request: Request) -> Dict[str, Any]:
    """Execute a 1-dimensional parameter sweep across a range of values."""
    try:
        sweep_res = run_parameter_sweep(
            parameter=req.parameter,
            values=req.values,
            base_config=req.base_config,
            trials=req.trials,
            seed=req.seed,
        )
    except ExperimentValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors)

    exp_id = f"sweep-{uuid.uuid4().hex[:10]}"
    title = req.title or f"Parameter Sweep: {req.parameter} ({len(req.values)} conditions)"
    q = req.research_question or f"How does varying '{req.parameter}' affect memory retention and interference?"

    lab_exp = LabExperiment(
        experiment_id=exp_id,
        title=title,
        research_question=q,
        mechanism=str((req.base_config or {}).get("mechanism", "leaky")),
        independent_variables=[req.parameter],
        dependent_variables=["memory_retention", "interference_score", "recall_accuracy"],
        controlled_variables=req.base_config or {},
        baseline_configuration=req.base_config or {},
        seed=req.seed,
        trials=req.trials,
        results=sweep_res,
        metrics=(
            sweep_res.conditions[0].aggregated_metrics
            if sweep_res.conditions
            else {}
        ),
        status=LabExperiment.status.COMPLETED,
        conclusion=f"Parameter sweep completed across {len(req.values)} values.",
    )
    _store(request).save_lab_experiment(lab_exp)

    out = sweep_res.to_dict()
    out["experiment_id"] = exp_id
    out["title"] = title
    return out


@router.post("/grid")
def grid_sweep_endpoint(req: GridSweepRequest, request: Request) -> Dict[str, Any]:
    """Execute a 2-dimensional parameter landscape sweep."""
    try:
        grid_res = run_grid_sweep(
            param_x=req.param_x,
            values_x=req.values_x,
            param_y=req.param_y,
            values_y=req.values_y,
            base_config=req.base_config,
            trials=req.trials,
            seed=req.seed,
        )
    except ExperimentValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors)

    exp_id = f"grid-{uuid.uuid4().hex[:10]}"
    title = req.title or f"2D Grid: {req.param_x} x {req.param_y}"
    q = req.research_question or f"Investigate interaction between {req.param_x} and {req.param_y}."

    lab_exp = LabExperiment(
        experiment_id=exp_id,
        title=title,
        research_question=q,
        mechanism=str((req.base_config or {}).get("mechanism", "leaky")),
        independent_variables=[req.param_x, req.param_y],
        dependent_variables=["memory_retention", "interference_score"],
        controlled_variables=req.base_config or {},
        seed=req.seed,
        trials=req.trials,
        results=grid_res,
        status=LabExperiment.status.COMPLETED,
        conclusion=f"Grid sweep evaluated {len(req.values_x) * len(req.values_y)} parameter pairs.",
    )
    _store(request).save_lab_experiment(lab_exp)

    out = grid_res.to_dict()
    out["experiment_id"] = exp_id
    out["title"] = title
    return out


@router.post("/compare")
def compare_endpoint(req: ControlledComparisonRequest, request: Request) -> Dict[str, Any]:
    """Execute a controlled baseline vs treatment comparison."""
    comp_res = run_controlled_comparison(
        baseline_config=req.baseline_config,
        treatment_config=req.treatment_config,
        trials=req.trials,
        seed=req.seed,
    )

    exp_id = f"comp-{uuid.uuid4().hex[:10]}"
    title = req.title or "Controlled Baseline vs Treatment Comparison"
    q = req.research_question or "Evaluate metric deltas under targeted treatment modification."

    diff_keys = list(comp_res.differing_variables.keys())
    lab_exp = LabExperiment(
        experiment_id=exp_id,
        title=title,
        research_question=q,
        mechanism=str(req.baseline_config.get("mechanism", "leaky")),
        independent_variables=diff_keys,
        controlled_variables={k: v for k, v in req.baseline_config.items() if k not in diff_keys},
        baseline_configuration=req.baseline_config,
        treatment_configurations=[req.treatment_config],
        seed=req.seed,
        trials=req.trials,
        results=comp_res,
        status=LabExperiment.status.COMPLETED,
        conclusion=f"Compared baseline against treatment across {len(diff_keys)} modified variable(s).",
    )
    _store(request).save_lab_experiment(lab_exp)

    out = comp_res.to_dict()
    out["experiment_id"] = exp_id
    out["title"] = title
    return out


# ---------------------------------------------------------------------------
# Hypothesis System
# ---------------------------------------------------------------------------
@router.post("/hypotheses")
def create_hypothesis_endpoint(req: CreateHypothesisRequest, request: Request) -> Dict[str, Any]:
    """Register a new scientific hypothesis with directional prediction."""
    hyp_id = f"hyp-{uuid.uuid4().hex[:8]}"
    pred_id = f"pred-{uuid.uuid4().hex[:8]}"

    prediction = Prediction(
        prediction_id=pred_id,
        hypothesis_id=hyp_id,
        independent_variable=req.independent_variable,
        dependent_variable=req.dependent_variable,
        predicted_direction=PredictedDirection(req.predicted_direction.lower()),
        rationale=req.expected_relationship,
    )

    hyp = Hypothesis(
        hypothesis_id=hyp_id,
        statement=req.statement,
        independent_variable=req.independent_variable,
        dependent_variable=req.dependent_variable,
        predicted_direction=PredictedDirection(req.predicted_direction.lower()),
        expected_relationship=req.expected_relationship,
        confidence_before=req.confidence_before,
        confidence_after=req.confidence_before,
        predictions=[prediction],
        status=HypothesisStatus.PROPOSED,
    )

    _store(request).save_hypothesis(hyp)
    return hyp.to_dict()


@router.get("/hypotheses")
def list_hypotheses_endpoint(request: Request) -> Dict[str, Any]:
    """List all registered hypotheses."""
    hyps = _store(request).list_hypotheses()
    return {"hypotheses": [h.to_dict() for h in hyps], "count": len(hyps)}


@router.get("/hypotheses/{hypothesis_id}")
def get_hypothesis_endpoint(hypothesis_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve details and evidence log for a hypothesis."""
    hyp = _store(request).get_hypothesis(hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=404, detail=f"Hypothesis '{hypothesis_id}' not found")
    return hyp.to_dict()


@router.post("/hypotheses/{hypothesis_id}/evaluate")
def evaluate_hypothesis_endpoint(
    hypothesis_id: str, req: EvaluateHypothesisRequest, request: Request
) -> Dict[str, Any]:
    """Test a hypothesis against observed empirical results from an experiment."""
    hyp = _store(request).get_hypothesis(hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=404, detail=f"Hypothesis '{hypothesis_id}' not found")

    exp = _store(request).get_lab_experiment(req.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found")

    # Extract baseline vs treatment delta if not provided
    b_val = req.baseline_value
    t_val = req.treatment_value

    if b_val is None or t_val is None:
        if isinstance(exp.results, ComparisonResult):
            b_val = exp.results.baseline_condition.aggregated_metrics.get(hyp.dependent_variable, {}).get("mean", 0.0)
            t_val = exp.results.treatment_condition.aggregated_metrics.get(hyp.dependent_variable, {}).get("mean", 0.0)
        elif isinstance(exp.results, SweepResult) and len(exp.results.conditions) >= 2:
            b_val = exp.results.conditions[0].aggregated_metrics.get(hyp.dependent_variable, {}).get("mean", 0.0)
            t_val = exp.results.conditions[-1].aggregated_metrics.get(hyp.dependent_variable, {}).get("mean", 0.0)
        else:
            b_val = 0.0
            t_val = float(exp.metrics.get(hyp.dependent_variable, 0.0))

    pred = hyp.predictions[0] if hyp.predictions else Prediction(
        prediction_id=f"p-{uuid.uuid4().hex[:6]}",
        hypothesis_id=hyp.hypothesis_id,
        independent_variable=hyp.independent_variable,
        dependent_variable=hyp.dependent_variable,
        predicted_direction=hyp.predicted_direction,
    )

    evaluation = evaluate_prediction(
        prediction=pred,
        baseline_value=b_val,
        treatment_value=t_val,
        correlation=req.correlation,
    )

    update_hypothesis_with_evidence(hyp, req.experiment_id, evaluation)
    _store(request).save_hypothesis(hyp)

    # Add evidence edge into lineage graph
    edge_type = EdgeType.SUPPORTS if evaluation.prediction_correct else EdgeType.CONTRADICTS
    _store(request).get_graph().add_edge(
        source_id=req.experiment_id,
        target_id=hypothesis_id,
        edge_type=edge_type,
        metadata={"evaluation": evaluation.verdict, "strength": evaluation.evidence_strength},
    )
    _store(request).save_graph()

    return {
        "hypothesis": hyp.to_dict(),
        "evaluation": evaluation.to_dict(),
    }


@router.post("/hypotheses/competing")
def competing_hypotheses_endpoint(req: CompetingHypothesesRequest) -> Dict[str, Any]:
    """Evaluate evidence across multiple competing hypotheses."""
    hyps: List[Hypothesis] = []
    for i, h_req in enumerate(req.hypotheses):
        h = Hypothesis(
            hypothesis_id=f"h-comp-{i+1}",
            statement=h_req.statement,
            independent_variable=h_req.independent_variable,
            dependent_variable=h_req.dependent_variable,
            predicted_direction=PredictedDirection(h_req.predicted_direction.lower()),
            expected_relationship=h_req.expected_relationship,
            confidence_before=h_req.confidence_before,
        )
        hyps.append(h)

    group = CompetingHypothesesGroup(
        group_id=f"grp-{uuid.uuid4().hex[:8]}",
        topic=req.topic,
        phenomenon=req.phenomenon,
        hypotheses=hyps,
    )

    deltas = req.observed_deltas or {}
    return group.evaluate_experiment_results(
        experiment_id=req.experiment_id or "comp-exp",
        observed_deltas=deltas,
    )


# ---------------------------------------------------------------------------
# Discovery & Recommendations
# ---------------------------------------------------------------------------
@router.post("/discriminating-experiment")
def discriminating_experiment_endpoint(req: DiscriminatingExperimentRequest) -> Dict[str, Any]:
    """Design a discriminating experiment capable of distinguishing competing hypotheses."""
    hyps: List[Hypothesis] = []
    for i, h_req in enumerate(req.hypotheses):
        h = Hypothesis(
            hypothesis_id=f"h-{i+1}",
            statement=h_req.statement,
            independent_variable=h_req.independent_variable,
            dependent_variable=h_req.dependent_variable,
            predicted_direction=PredictedDirection(h_req.predicted_direction.lower()),
        )
        hyps.append(h)

    return find_discriminating_experiment(hyps, base_config=req.base_config)


@router.post("/suggest-next")
def suggest_next_endpoint(req: SuggestNextRequest) -> Dict[str, Any]:
    """Identify the most informative unexplored experiments based on empirical data."""
    return suggest_next_experiment(
        parameter=req.parameter,
        tested_values=req.tested_values,
        observed_metrics=req.observed_metrics,
        metric_name=req.metric_name,
        parameter_min=req.parameter_min,
        parameter_max=req.parameter_max,
        num_suggestions=req.num_suggestions,
    )


# ---------------------------------------------------------------------------
# Research Lineage, Reporting & Export
# ---------------------------------------------------------------------------
@router.get("/lineage")
def get_lineage_graph(request: Request, node_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch the research lineage graph (optionally focused on a specific node)."""
    graph = _store(request).get_graph()
    if node_id:
        return graph.get_lineage(node_id)
    return graph.to_dict()


@router.get("/experiments/{experiment_id}/report")
def get_experiment_report(experiment_id: str, request: Request) -> Dict[str, Any]:
    """Generate a formal 10-section scientific markdown report."""
    exp = _store(request).get_lab_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    hyp = _store(request).get_hypothesis(exp.hypothesis_id) if exp.hypothesis_id else None
    report_md = generate_scientific_report(exp, hypothesis=hyp)

    return {
        "experiment_id": experiment_id,
        "title": exp.title,
        "report_markdown": report_md,
    }


@router.get("/experiments/{experiment_id}/export")
def export_experiment_data(
    experiment_id: str,
    request: Request,
    format: str = Query("json", description="json | csv"),
) -> Response:
    """Export experiment dataset in JSON or CSV format with full provenance."""
    exp = _store(request).get_lab_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")

    if format.lower() == "csv":
        csv_data = export_experiment_csv(exp)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={experiment_id}.csv"},
        )

    json_data = export_experiment_json(exp)
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={experiment_id}.json"},
    )
