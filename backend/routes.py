"""API routes (section 13).

All endpoints return clean JSON. There is no authentication yet, by design.
Computation stays in ``core``; this layer only translates payloads,
persists experiments, and answers recall probes against stored state.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from core import (
    Experiment,
    ExperimentConfig,
    MECHANISM_INFO,
    MechanismParams,
    Query,
    Task,
    TaskConfig,
    __version__,
    create_mechanism,
    generate_task,
    run_experiment,
)
from core.experiment import SCHEMA_VERSION

from .schemas import (
    CompareRequest,
    ExperimentRunRequest,
    GenerateRequest,
    RecallRequest,
    ReplayRequest,
)
from .store import ExperimentStore

router = APIRouter()


def _store(request: Request) -> ExperimentStore:
    return request.app.state.store


def _run_from_request(req: ExperimentRunRequest, replay_of: str | None = None) -> Experiment:
    config = ExperimentConfig.from_api(req.model_dump())
    try:
        return run_experiment(config, replay_of=replay_of)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# health / introspection
# ---------------------------------------------------------------------------
@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "core_version": __version__,
        "schema_version": SCHEMA_VERSION,
        "mechanisms": list(MECHANISM_INFO),
    }


@router.get("/mechanisms")
def mechanisms() -> dict:
    return {"mechanisms": MECHANISM_INFO, "metric_definitions": _metric_definitions()}


def _metric_definitions() -> dict:
    from core.metrics import METRIC_DEFINITIONS

    return METRIC_DEFINITIONS


# ---------------------------------------------------------------------------
# experiments
# ---------------------------------------------------------------------------
@router.get("/experiments")
def list_experiments(request: Request) -> list[dict]:
    """List all stored experiments with summary metadata."""
    store = _store(request)
    out = []
    for exp_id in store.list_ids():
        exp = store.get(exp_id)
        if exp:
            out.append({
                "experiment_id": exp.experiment_id,
                "mechanism": exp.mechanism,
                "created_at": exp.created_at,
                "num_events": len(exp.events),
                "parameters": exp.parameters,
                "metrics": exp.metrics,
                "version": getattr(exp, "version", 1),
            })
    return out


@router.post("/experiments/demo")
def run_demo_experiment(request: Request) -> dict:
    """Run and store a canonical demonstration experiment for immediate excavation."""
    cfg = ExperimentConfig(
        seed=777,
        mechanism="interference",
        params=MechanismParams(
            state_dim=128,
            update_strength=0.9,
            memory_strength=1.0,
            interference_strength=0.6,
        ),
        task=TaskConfig(
            seed=777,
            d=128,
            n_objects=6,
            n_symbols=4,
            n_conflicts=3,
            object_similarity=0.45,
            cycles=2,
            order="interleaved",
            probe_original=True,
        ),
    )
    exp = run_experiment(cfg)
    _store(request).save(exp)
    return exp.to_dict()


@router.post("/experiments/run")
def run_experiment_endpoint(req: ExperimentRunRequest, request: Request) -> dict:
    exp = _run_from_request(req)
    _store(request).save(exp)
    return exp.to_dict()


@router.post("/experiments/generate")
def generate_endpoint(req: GenerateRequest, request: Request) -> dict:
    """Materialize a task (events, vectors, queries) without running it."""
    seed = req.seed if req.seed is not None else 0
    try:
        task = generate_task(TaskConfig.from_dict(req.task.model_dump()), fallback_seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return task.to_dict()


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str, request: Request) -> dict:
    exp = _store(request).get(experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id!r} not found")
    return exp.to_dict()


@router.post("/experiments/{experiment_id}/replay")
def replay_experiment(experiment_id: str, req: ReplayRequest, request: Request) -> dict:
    """Re-run the recorded experiment from its stored config.

    With no overrides this reproduces the original run exactly (the
    determinism proof). ``params`` overrides are a sensitivity probe;
    editing the event history (counterfactuals) arrives in Phase 02.
    """
    exp = _store(request).get(experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id!r} not found")

    config = ExperimentConfig.from_dict(exp.config)
    if req.params is not None:
        # merge overrides into the recorded parameters (sensitivity probe),
        # so unmentioned fields (e.g. state_dim) keep their recorded values
        merged = dict(exp.parameters)
        # exclude_unset: only fields the caller actually provided override
        merged.update(req.params.model_dump(exclude_unset=True))
        config.params = MechanismParams(**merged)
    try:
        replayed = run_experiment(config, replay_of=experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    _store(request).save(replayed)
    return replayed.to_dict()


@router.post("/recall")
def recall_endpoint(req: RecallRequest, request: Request) -> dict:
    """Ask a stored experiment's state a question at a point in its history.

    The state at ``timestep`` (events processed) is restored into the
    mechanism and probed with the object's key vector. Ground truth is the
    symbol bound to the object at/before that timestep unless the caller
    overrides it with ``expected_symbol_label``.
    """
    exp = _store(request).get(req.experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"experiment {req.experiment_id!r} not found")

    task = Task.from_dict(exp.task)
    if req.object_label not in task.objects:
        raise HTTPException(
            status_code=400,
            detail=f"unknown object {req.object_label!r}; known: {sorted(task.objects)}",
        )

    t = req.timestep
    if t < 0:
        t = len(task.events) - 1
    if t >= len(task.events):
        t = len(task.events) - 1
    snap = exp.snapshot_at(t + 1)  # snapshots: timestep = events processed
    if snap is None:
        raise HTTPException(status_code=404, detail=f"no snapshot at timestep {t}")

    try:
        mech = create_mechanism(
            exp.mechanism, MechanismParams(**exp.parameters), seed=exp.seed
        )
        mech.restore_state(snap["state_vector"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # ground truth: latest binding at/before timestep t, or caller override
    if req.expected_symbol_label is not None:
        expected = req.expected_symbol_label
        if expected not in task.symbols:
            raise HTTPException(status_code=400, detail=f"unknown symbol {expected!r}")
    else:
        expected = None
        for j in range(t, -1, -1):
            if task.events[j].concept_label == req.object_label:
                expected = task.events[j].attribute_label
                break
        if expected is None:
            raise HTTPException(
                status_code=400,
                detail=f"object {req.object_label!r} was never written before timestep {t}",
            )

    query = Query(
        id="recall-probe",
        timestep=t,
        object_label=req.object_label,
        kind="latest",
        expected_attribute_label=expected,
        key_vector=task.objects[req.object_label],
        expected_value_vector=task.symbols[expected],
    )

    from core.recall import execute_query

    result = execute_query(mech, query, task.symbols)
    out = result.to_dict()
    out["snapshot"] = {
        "timestep": int(snap["timestep"]),
        "state_norm": float(np.linalg.norm(snap["state_vector"])),
        "active_dimensions": snap["active_dimensions"],
        "num_active": int(snap["num_active"]),
    }
    return out


@router.post("/compare")
def compare_endpoint(req: CompareRequest, request: Request) -> dict:
    """Run several configurations and return side-by-side metrics."""
    results = []
    for i, cfg_req in enumerate(req.configs):
        exp = _run_from_request(cfg_req)
        _store(request).save(exp)
        results.append(
            {
                "label": f"run_{i}",
                "experiment_id": exp.experiment_id,
                "mechanism": exp.mechanism,
                "metrics": exp.metrics,
                "config": exp.config,
            }
        )
    keys = sorted({k for r in results for k in r["metrics"] if k != "details"})
    table = {
        key: [r["metrics"].get(key) for r in results] for key in keys
    }
    return {"results": results, "comparison_table": table}