"""Experiment runner (section 12).

``run_experiment(config)`` is the single entry point for the whole
platform. It:

1. initializes the mechanism,
2. generates (or receives) the task — events + queries,
3. processes events sequentially, recording a state snapshot after each,
4. executes each query at its configured timestep against the *then-current*
   state (this is what makes "query timing" a real experimental variable),
5. compares predictions against ground truth,
6. computes metrics,
7. returns a complete, serializable ``Experiment``.

Determinism: all randomness flows from the config seed (task vectors, any
input noise). Two calls with the same ``ExperimentConfig`` produce
byte-identical snapshots, queries, and metrics.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .experiment import Experiment, ExperimentConfig, make_experiment
from .mechanisms import create_mechanism
from .metrics import compute_metrics
from .recall import QueryResult, execute_query
from .task import generate_task


def _query_summary(r: QueryResult) -> Dict[str, object]:
    return {
        "query_id": r.query_id,
        "timestep": int(r.timestep),
        "object_label": r.object_label,
        "kind": r.kind,
        "predicted_label": r.predicted_label,
        "truth_label": r.truth_label,
        "confidence": float(r.confidence),
        "correctness": bool(r.correctness),
        "quality": float(r.quality),
    }


def run_experiment(config: ExperimentConfig, replay_of: str | None = None) -> Experiment:
    """Run a complete experiment and return its full record."""
    config_dict = config.to_dict()

    # 1–2. task + mechanism (both derive their randomness from config.seed)
    task = generate_task(config.task, fallback_seed=config.seed)
    mech = create_mechanism(config.mechanism, config.params, seed=config.seed)

    # queries scheduled by timestep (index of the event after which they run)
    queries_by_time: Dict[int, List] = defaultdict(list)
    for q in task.queries:
        queries_by_time[int(q.timestep)].append(q)

    # 3. process events sequentially, snapshotting after each
    snapshots: List[Dict] = []
    initial = mech.get_state_snapshot()
    initial["timestep"] = 0
    initial["event_id"] = None
    initial["trace"] = {
        "mechanism": mech.name,
        "note": "initial state (zero) before any event",
    }
    snapshots.append(initial)

    query_results: List[QueryResult] = []
    for t, event in enumerate(task.events):
        trace = mech.update(event)
        if config.update_steps_per_event > 1:
            trace["extra_steps"] = mech.step_no_input(config.update_steps_per_event - 1)

        snap = mech.get_state_snapshot()
        snap["timestep"] = t + 1  # events processed so far
        snap["event_id"] = event.id
        snap["trace"] = trace

        # 4. execute queries scheduled at this point in history
        for q in queries_by_time.get(t, []):
            res = execute_query(mech, q, task.symbols)
            query_results.append(res)
            snap.setdefault("query_results", []).append(_query_summary(res))
        snapshots.append(snap)

    # 5–6. compare vs ground truth and compute metrics
    predictions = [_query_summary(r) for r in query_results]
    ground_truth = [
        {
            "query_id": r.query_id,
            "timestep": int(r.timestep),
            "object_label": r.object_label,
            "kind": r.kind,
            "truth_label": r.truth_label,
        }
        for r in query_results
    ]
    metrics = compute_metrics(snapshots, query_results, task)

    # 7. assemble the experiment
    return make_experiment(
        seed=config.seed,
        mechanism=config.mechanism,
        params=config.params,
        task_dict=task.to_dict(),
        config_dict=config_dict,
        events=[e.to_dict() for e in task.events],
        snapshots=snapshots,
        queries=[r.to_dict() for r in query_results],
        predictions=predictions,
        ground_truth=ground_truth,
        metrics=metrics,
        replay_of=replay_of,
    )