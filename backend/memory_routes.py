"""Phase 02 memory engine routes (sections 21–23).

Everything here returns data from *real computation* — writes, recalls,
collision reports, retention curves, capacity sweeps, order comparisons,
interference matrices, ablations, contribution estimates, and state
inspection all execute the deterministic core engine. The responses are
deliberately shaped for the future visualization layer (compact timeline,
structured state diffs, matrix cells), but nothing is precomputed or fake.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from core import (
    Experiment,
    ExperimentConfig,
    MechanismParams,
    Memory,
    SCENARIOS,
    TextMemory,
    capacity_sweep,
    collision_report,
    compare_experiments,
    create_mechanism,
    encode_memory,
    interference_matrix,
    order_comparison,
    recall_memory,
    retention_curve,
    run_experiment,
    run_scenario,
    strength_sweep,
    write_memory,
    write_memories,
)
from core.analysis import ablate_event, analyze_memory_contribution, experiment_timeline, inspect_state
from core.task import QuerySpec, TaskConfig

from .schemas import (
    AblationRequest,
    CapacityRequest,
    CollisionRequest,
    CompareStoredRequest,
    ContributionRequest,
    MatrixRequest,
    MemoryExperimentRequest,
    MemoryQuerySpec,
    MemoryRecallRequest,
    MemoryWriteRequest,
    OrderRequest,
    RetentionRequest,
    ScenarioRequest,
)

router = APIRouter()


def _store(request: Request):
    return request.app.state.store


def _params(p) -> MechanismParams:
    data = p.model_dump() if hasattr(p, "model_dump") else dict(p)
    try:
        return MechanismParams(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _mechanism(seed: int, mechanism: str, params: MechanismParams):
    try:
        return create_mechanism(mechanism, params, seed=seed)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _get_experiment(request: Request, experiment_id: str) -> Experiment:
    exp = _store(request).get(experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"experiment {experiment_id!r} not found")
    return exp


# ---------------------------------------------------------------------------
# atomic memory operations
# ---------------------------------------------------------------------------
@router.post("/memory/write")
def memory_write(req: MemoryWriteRequest) -> dict:
    """Encode one text memory and write it into a fresh mechanism state.

    Returns the encoded memory and the full ``UpdateResult`` accounting
    (state before/after, update vector, affected dimensions, memory vs
    interference contribution).
    """
    params = _params(req.params)
    mech = _mechanism(req.seed, req.mechanism, params)
    memory = encode_memory(
        TextMemory(
            concept=req.memory.concept,
            value=req.memory.value,
            importance=req.memory.importance,
            strength=req.memory.strength,
            metadata=req.memory.metadata,
        ),
        seed=req.seed,
        d=params.state_dim,
    )
    update = write_memory(mech, memory, timestep=req.timestep)
    return {
        "seed": req.seed,
        "mechanism": req.mechanism,
        "memory": memory.to_dict(include_vectors=True),
        "update_result": update.to_dict(),
    }


@router.post("/memory/recall")
def memory_recall(req: MemoryRecallRequest) -> dict:
    """Write a list of memories sequentially, then query one concept."""
    params = _params(req.params)
    mech = _mechanism(req.seed, req.mechanism, params)
    memories = [
        encode_memory(
            TextMemory(concept=m.concept, value=m.value, importance=m.importance,
                       strength=m.strength, metadata=m.metadata),
            seed=req.seed,
            d=params.state_dim,
        )
        for m in req.memories
    ]
    updates = write_memories(mech, memories, start_timestep=0)
    result = recall_memory(
        mech,
        TextMemory(concept=req.query.concept),
        memories,
        seed=req.seed,
        d=params.state_dim,
        expected_value=req.expected_value,
        timestep=len(memories) - 1,
        measure=req.measure,
        top_k=req.top_k,
    )
    return {
        "seed": req.seed,
        "mechanism": req.mechanism,
        "writes": [u.to_dict() for u in updates],
        "final_state_norm": float(mech.get_state_snapshot()["norm"]),
        "recall": result.to_dict(),
    }


# ---------------------------------------------------------------------------
# memory experiments
# ---------------------------------------------------------------------------
@router.post("/experiments/memory")
def memory_experiment(req: MemoryExperimentRequest, request: Request) -> dict:
    """Run a complete memory experiment (writes + queries) and persist it.

    Uses the deterministic text encoder (vector_source="text"), so the
    stored config fully reproduces the run (replay/ablation work).
    """
    params = _params(req.params)
    events = [
        {
            "object_label": m.concept,
            "symbol_label": m.value,
            "importance": m.importance,
            "strength": m.strength,
            "metadata": {
                "memory_id": f"{m.concept}:{m.value}",
                "memory_concept": m.concept,
            },
        }
        for m in req.memories
    ]
    queries = req.queries or [
        MemoryQuerySpec(concept=m.concept, timestep=-1, kind="latest")
        for m in req.memories
    ]
    config = ExperimentConfig(
        seed=req.seed,
        mechanism=req.mechanism,
        params=params,
        task=TaskConfig(
            seed=req.seed,
            d=params.state_dim,
            n_objects=len({e["object_label"] for e in events}),
            n_symbols=len({e["symbol_label"] for e in events}),
            n_conflicts=0,
            object_similarity=0.0,
            symbol_similarity=0.0,
            cycles=1,
            order="structured",
            probe_original=True,
            input_noise=req.input_noise,
            vector_source="text",
            events=events,
            queries=[q.model_dump() for q in queries],
        ),
    )
    try:
        exp = run_experiment(config)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    _store(request).save(exp)
    return exp.to_dict()


# ---------------------------------------------------------------------------
# specialized experiments (reports from real runs)
# ---------------------------------------------------------------------------
@router.post("/experiments/collision")
def memory_collision(req: CollisionRequest, request: Request) -> dict:
    params = _params(req.params)
    report = collision_report(
        seed=req.seed,
        mechanism=req.mechanism,
        params=params,
        concept=req.concept,
        value_a=req.value_a,
        value_b=req.value_b,
        similarity=req.similarity,
        strength_a=req.strength_a,
        strength_b=req.strength_b,
    )
    exp = Experiment.from_dict(report.pop("experiment"))
    _store(request).save(exp)
    report["experiment_id"] = exp.experiment_id
    return report


@router.post("/experiments/retention")
def memory_retention(req: RetentionRequest) -> dict:
    params = _params(req.params)
    try:
        return retention_curve(
            seed=req.seed,
            mechanism=req.mechanism,
            params=params,
            lags=req.lags,
            concept=req.concept,
            value=req.value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/experiments/ablation")
def memory_ablation(req: AblationRequest, request: Request) -> dict:
    exp = _get_experiment(request, req.experiment_id)
    try:
        return ablate_event(exp, req.event_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/experiments/compare")
def compare_stored(req: CompareStoredRequest, request: Request) -> dict:
    a = _get_experiment(request, req.experiment_id_a)
    b = _get_experiment(request, req.experiment_id_b)
    return compare_experiments(a, b)


@router.post("/experiments/capacity")
def memory_capacity(req: CapacityRequest) -> dict:
    params = _params(req.params)
    return capacity_sweep(
        seed=req.seed,
        mechanism=req.mechanism,
        params=params,
        dimensions=req.dimensions,
        n_facts=req.n_facts,
    )


@router.post("/experiments/order")
def memory_order(req: OrderRequest) -> dict:
    params = _params(req.params)
    return order_comparison(
        seed=req.seed,
        mechanism=req.mechanism,
        params=params,
        orders=req.orders,
    )


@router.post("/experiments/interference-matrix")
def memory_matrix(req: MatrixRequest) -> dict:
    params = _params(req.params)
    return interference_matrix(
        seed=req.seed,
        mechanism=req.mechanism,
        params=params,
        similarities=req.similarities,
        update_strengths=req.update_strengths,
    )


@router.get("/scenarios")
def scenarios_listing() -> dict:
    return {
        "scenarios": {
            name: {
                "description": s.description,
                "learning_objective": s.learning_objective,
                "kind": s.kind,
                "defaults": s.defaults,
            }
            for name, s in SCENARIOS.items()
        }
    }


@router.post("/experiments/scenario")
def run_scenario_endpoint(req: ScenarioRequest, request: Request) -> dict:
    """Run a named scenario (persists the experiment when one is produced)."""
    overrides = dict(req.overrides)
    params = overrides.get("params")
    if isinstance(params, dict):
        overrides["params"] = _params(params)
    try:
        out = run_scenario(req.name, overrides)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if out.get("experiment"):
        exp = Experiment.from_dict(out["experiment"])
        _store(request).save(exp)
        out["experiment_id"] = exp.experiment_id
    return out


# ---------------------------------------------------------------------------
# state inspection (sections 14, 23)
# ---------------------------------------------------------------------------
@router.get("/experiments/{experiment_id}/state/{timestep}")
def state_inspection(experiment_id: str, timestep: int, request: Request) -> dict:
    exp = _get_experiment(request, experiment_id)
    try:
        return inspect_state(exp, timestep)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/experiments/{experiment_id}/timeline")
def timeline(experiment_id: str, request: Request) -> dict:
    exp = _get_experiment(request, experiment_id)
    return experiment_timeline(exp)


@router.post("/experiments/{experiment_id}/memory-contribution")
def contribution(experiment_id: str, req: ContributionRequest, request: Request) -> dict:
    exp = _get_experiment(request, experiment_id)
    try:
        return analyze_memory_contribution(exp, req.memory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))