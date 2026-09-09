"""Analysis layer (Phase 02, sections 14–19, 23).

Pure functions over ``Experiment`` records plus deterministic re-runs:

- ``inspect_state`` / ``experiment_timeline`` — numeric state inspection
  (the future UI asks "what changed between timestep 7 and 8?").
- ``compare_states`` — L2 / cosine / normalized difference + which
  dimensions moved where.
- ``ablate_event`` — remove one event from history, replay everything,
  compare (foundation for counterfactuals, Phase 04).
- ``analyze_memory_contribution`` — **replay-based contribution
  estimate** (explicitly not causal attribution).
- ``compare_experiments`` — cross-experiment diff, works across mechanisms.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from .experiment import Experiment, ExperimentConfig
from .runner import run_experiment
from .task import EventSpec, QuerySpec, TaskConfig
from .vectors import cosine


# ---------------------------------------------------------------------------
# state difference (section 15)
# ---------------------------------------------------------------------------
def compare_states(
    a: Any, b: Any, top_changes: int = 5
) -> Dict[str, Any]:
    """Numerical diff between two state vectors.

    ``a``/``b`` may be lists or numpy arrays of equal length.

    Returns
    -------
    l2_distance            ``||a - b||``
    cosine_similarity      ``<a,b>/(||a||||b||)`` (0 if either is zero)
    normalized_difference  ``||a-b|| / (||a|| + ||b||)`` ∈ [0, 1]
    relative_l2            ``||a-b|| / ||a||`` (relative to the reference)
    changed_dimensions     indices where ``|a_i - b_i| > 1e-9``
    largest_positive_changes  top indices where b grew vs a (value, delta)
    largest_negative_changes  top indices where b shrank vs a (value, delta)
    """
    a = np.asarray(a, dtype=np.float64).reshape(-1)
    b = np.asarray(b, dtype=np.float64).reshape(-1)
    if a.shape != b.shape:
        return {
            "shape_mismatch": [list(a.shape), list(b.shape)],
            "l2_distance": None,
            "cosine_similarity": None,
            "normalized_difference": None,
            "relative_l2": None,
            "changed_dimensions": [],
            "largest_positive_changes": [],
            "largest_negative_changes": [],
        }
    delta = b - a
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    changed = np.where(np.abs(delta) > 1e-9)[0]
    order = np.argsort(-np.abs(delta), kind="stable")[:top_changes]
    pos = [
        {"dimension": int(i), "value": float(b[i]), "delta": float(delta[i])}
        for i in order
        if delta[i] > 0
    ]
    neg = [
        {"dimension": int(i), "value": float(b[i]), "delta": float(delta[i])}
        for i in order
        if delta[i] < 0
    ]
    return {
        "shape_mismatch": None,
        "l2_distance": float(np.linalg.norm(delta)),
        "cosine_similarity": float(cosine(a, b)),
        "normalized_difference": float(
            np.linalg.norm(delta) / (na + nb) if na + nb > 1e-12 else 0.0
        ),
        "relative_l2": float(np.linalg.norm(delta) / na if na > 1e-12 else 0.0),
        "changed_dimensions": changed.tolist(),
        "num_changed": int(changed.size),
        "largest_positive_changes": pos,
        "largest_negative_changes": neg,
    }


# ---------------------------------------------------------------------------
# state inspection (section 14)
# ---------------------------------------------------------------------------
def _top_dimensions(vector: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
    order = np.argsort(-np.abs(vector), kind="stable")
    return [
        {"dimension": int(i), "value": float(vector[i])}
        for i in order[: min(k, order.size)]
    ]


def _memory_contributions(experiment: Experiment, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    trace = snapshot.get("trace") or {}
    event_id = snapshot.get("event_id")
    entry: Dict[str, Any] = {
        "event_id": event_id,
        "write_gain": trace.get("write_gain"),
        "binding_norm": trace.get("binding_norm"),
        "decay_applied": trace.get("decay_applied"),
        "erased_norm": trace.get("erased_norm"),
        "k_kept": trace.get("k_kept"),
    }
    if event_id is not None:
        for ev in experiment.events:
            if ev["id"] == event_id:
                meta = ev.get("metadata") or {}
                entry["memory_id"] = meta.get("memory_id")
                entry["concept"] = ev.get("concept_label")
                entry["value"] = ev.get("attribute_label")
                break
    return [entry]


def inspect_state(experiment: Experiment, timestep: int) -> Dict[str, Any]:
    """Full numeric view of the state after ``timestep`` events processed."""
    snap = experiment.snapshot_at(timestep)
    if snap is None:
        raise KeyError(
            f"no snapshot at timestep {timestep} (experiment has {experiment.num_events} events)"
        )
    vector = np.asarray(snap["state_vector"], dtype=np.float64)
    prev = experiment.snapshot_at(timestep - 1)
    state_delta = None
    if prev is not None:
        prev_vec = np.asarray(prev["state_vector"], dtype=np.float64)
        state_delta = {
            "l2": float(np.linalg.norm(vector - prev_vec)),
            "cosine": float(cosine(prev_vec, vector)),
            "top_affected": _top_dimensions(vector - prev_vec, 5),
        }
    active = np.where(np.abs(vector) > 1e-9)[0]
    return {
        "experiment_id": experiment.experiment_id,
        "timestep": int(timestep),
        "event_id": snap.get("event_id"),
        "state_vector": vector.tolist(),
        "state_norm": float(np.linalg.norm(vector)),
        "state_delta_vs_previous": state_delta,
        "active_dimensions": active.tolist(),
        "num_active": int(active.size),
        "sparsity": float(active.size / vector.size) if vector.size else 0.0,
        "top_dimensions": _top_dimensions(vector),
        "memory_contributions": _memory_contributions(experiment, snap),
        "query_results": snap.get("query_results", []),
        "mechanism_trace": snap.get("trace"),
    }


def experiment_timeline(experiment: Experiment) -> Dict[str, Any]:
    """Compact timeline for visualization clients."""
    entries = []
    for i, snap in enumerate(experiment.snapshots):
        prev_vec = (
            np.asarray(experiment.snapshots[i - 1]["state_vector"], dtype=np.float64)
            if i > 0
            else None
        )
        vec = np.asarray(snap["state_vector"], dtype=np.float64)
        delta = (
            float(np.linalg.norm(vec - prev_vec)) if prev_vec is not None else 0.0
        )
        entries.append(
            {
                "timestep": int(snap["timestep"]),
                "event_id": snap.get("event_id"),
                "state_norm": float(np.linalg.norm(vec)),
                "state_delta": delta,
                "num_active": int(snap.get("num_active", 0)),
                "top_dimensions": _top_dimensions(vec, 5),
                "memory_contributions": _memory_contributions(experiment, snap),
                "queries": snap.get("query_results", []),
            }
        )
    return {
        "experiment_id": experiment.experiment_id,
        "mechanism": experiment.mechanism,
        "state_dim": int(experiment.parameters.get("state_dim")),
        "timeline": entries,
    }


# ---------------------------------------------------------------------------
# ablation (section 17)
# ---------------------------------------------------------------------------
def _explicit_task_config(experiment: Experiment) -> TaskConfig:
    """Rebuild the task config with *explicit* events/queries from the
    stored task record, so history can be edited deterministically."""
    task_dict = experiment.task
    config_task = experiment.config.get("task", {})
    return TaskConfig(
        seed=config_task.get("seed"),
        d=config_task.get("d", task_dict.get("d")),
        n_objects=config_task.get("n_objects", len(task_dict.get("objects", {}))),
        n_symbols=config_task.get("n_symbols", len(task_dict.get("symbols", {}))),
        n_conflicts=config_task.get("n_conflicts", 0),
        object_similarity=float(config_task.get("object_similarity", 0.0)),
        symbol_similarity=float(config_task.get("symbol_similarity", 0.0)),
        cycles=int(config_task.get("cycles", 1)),
        order=str(config_task.get("order", "interleaved")),
        probe_original=bool(config_task.get("probe_original", True)),
        input_noise=float(config_task.get("input_noise", 0.0)),
        vector_source=str(config_task.get("vector_source", "random")),
        events=[
            EventSpec(
                object_label=ev["concept_label"],
                symbol_label=ev["attribute_label"],
                importance=float(ev.get("importance", 1.0)),
                strength=float(ev.get("strength", 1.0)),
                noise=ev.get("noise"),
                metadata=dict(ev.get("metadata", {})),
            )
            for ev in task_dict.get("events", [])
        ],
        queries=[
            QuerySpec(
                object_label=q["object_label"],
                timestep=int(q["timestep"]),
                kind=q.get("kind", "latest"),
                expected_symbol_label=None,  # ground truth follows the new history
            )
            for q in task_dict.get("queries", [])
        ],
    )


def _remap_timestep(t: int, removed_index: int, new_end: int) -> int:
    if t < removed_index:
        return t
    return max(0, min(t - 1, new_end))


def ablate_event(experiment: Experiment, event_id: str) -> Dict[str, Any]:
    """Remove one event from history, replay everything, compare.

    Queries scheduled after the removed event shift back one step so the
    relative query schedule is preserved; ground truth is recomputed from
    the *counterfactual* history (never carried over from the original).
    """
    # locate the event
    target_idx = None
    target = None
    for i, ev in enumerate(experiment.events):
        if ev["id"] == event_id:
            target_idx = i
            target = ev
            break
    if target_idx is None:
        raise KeyError(f"event {event_id!r} not found in experiment {experiment.experiment_id}")

    # 1. reproduce the original run from the stored config (reproducibility)
    config = ExperimentConfig.from_dict(experiment.config)
    original = run_experiment(config)
    reproduced = (
        original.snapshots[-1]["state_vector"] == experiment.snapshots[-1]["state_vector"]
    )

    # 2. build the counterfactual config: same task, event removed, queries shifted
    task_cfg = _explicit_task_config(experiment)
    new_events = [
        e for i, e in enumerate(task_cfg.events) if i != target_idx
    ]
    new_end = len(new_events) - 1
    surviving_objects = {e.object_label for e in new_events}
    new_queries = [
        QuerySpec(
            object_label=q.object_label,
            timestep=_remap_timestep(q.timestep, target_idx, new_end),
            kind=q.kind,
            expected_symbol_label=None,
        )
        for q in task_cfg.queries
        # a query about an object whose every write was ablated has no
        # referent in the counterfactual history — drop it honestly
        if q.object_label in surviving_objects
    ]
    task_cfg.events = new_events
    task_cfg.queries = new_queries

    cfg = ExperimentConfig(
        seed=config.seed,
        mechanism=config.mechanism,
        params=config.params,
        task=task_cfg,
        update_steps_per_event=config.update_steps_per_event,
    )
    counterfactual = run_experiment(cfg)

    # 3. compare
    full_vec = np.asarray(original.snapshots[-1]["state_vector"], dtype=np.float64)
    ablated_vec = np.asarray(
        counterfactual.snapshots[-1]["state_vector"], dtype=np.float64
    )
    state_diff = compare_states(full_vec, ablated_vec)

    predictions = _aligned_prediction_diffs(original, counterfactual)
    changed = [p for p in predictions if p["outcome_changed"]]

    return {
        "experiment_id": experiment.experiment_id,
        "event_id": event_id,
        "ablated_event": {
            "timestep": int(target.get("timestep", target_idx)),
            "concept": target.get("concept_label"),
            "value": target.get("attribute_label"),
            "memory_id": (target.get("metadata") or {}).get("memory_id"),
        },
        "reproduced_from_config": bool(reproduced),
        "original": {
            "num_events": original.num_events,
            "metrics": original.metrics,
            "final_state_norm": float(np.linalg.norm(full_vec)),
        },
        "counterfactual": {
            "num_events": counterfactual.num_events,
            "metrics": counterfactual.metrics,
            "final_state_norm": float(np.linalg.norm(ablated_vec)),
        },
        "difference": {
            "state": state_diff,
            "metrics": _metric_diffs(original.metrics, counterfactual.metrics),
        },
        "prediction_differences": predictions,
        "changed_outcomes": changed,
        "num_changed_outcomes": len(changed),
    }


# ---------------------------------------------------------------------------
# memory contribution (section 16)
# ---------------------------------------------------------------------------
def analyze_memory_contribution(
    experiment: Experiment, memory_id: str
) -> Dict[str, Any]:
    """Replay-based contribution estimate for one memory.

    Runs the full history and the history with the memory's event removed,
    then measures how much the final state and the recall outcomes moved.

    **Limitation (documented, not hand-waved)**: this is a *replay-based
    estimate*, not true causal attribution. The mechanisms are nonlinear
    and interacting (decay, competition, erasure), so removing a memory
    changes the trajectory in ways a linear attribution cannot capture.
    """
    # find the event carrying this memory (metadata.memory_id or event id)
    event_id = None
    concept = None
    for ev in experiment.events:
        meta = ev.get("metadata") or {}
        if meta.get("memory_id") == memory_id or ev["id"] == memory_id:
            event_id = ev["id"]
            concept = ev.get("concept_label")
            break
    if event_id is None:
        raise KeyError(
            f"memory {memory_id!r} not found in experiment {experiment.experiment_id} "
            "(memory_id lives in event metadata for memory-engine experiments)"
        )

    ablation = ablate_event(experiment, event_id)
    state_diff = ablation["difference"]["state"]
    contribution_score = float(state_diff.get("relative_l2") or 0.0)

    return {
        "memory_id": memory_id,
        "event_id": event_id,
        "concept": concept,
        "method": "replay-based contribution estimate",
        "limitation": (
            "estimated by removing the memory's event and re-running the full "
            "history; NOT true causal attribution (nonlinear, interacting "
            "mechanisms)."
        ),
        "contribution_score": contribution_score,
        "state_difference": state_diff,
        "recall_difference": {
            "accuracy_delta": float(
                ablation["counterfactual"]["metrics"]["recall_accuracy"]
                - ablation["original"]["metrics"]["recall_accuracy"]
            ),
            "quality_delta": float(
                ablation["counterfactual"]["metrics"]["recall_quality"]
                - ablation["original"]["metrics"]["recall_quality"]
            ),
        },
        "num_changed_outcomes": int(ablation["num_changed_outcomes"]),
        "changed_outcomes": ablation["changed_outcomes"],
    }


# ---------------------------------------------------------------------------
# experiment comparison (section 19)
# ---------------------------------------------------------------------------
def _final_query_per_object(experiment: Experiment) -> Dict[tuple, Dict[str, Any]]:
    out: Dict[tuple, Dict[str, Any]] = {}
    max_ts = max((q["timestep"] for q in experiment.queries), default=-1)
    for q in experiment.queries:
        if q["timestep"] == max_ts:
            out.setdefault((q["object_label"], q["kind"]), q)
    return out


def _aligned_prediction_diffs(
    a: Experiment, b: Experiment
) -> List[Dict[str, Any]]:
    qa = _final_query_per_object(a)
    qb = _final_query_per_object(b)
    rows = []
    for key in sorted(set(qa) & set(qb)):
        x, y = qa[key], qb[key]
        rows.append(
            {
                "object_label": key[0],
                "kind": key[1],
                # ground truth follows each experiment's own history
                "truth_a": x.get("truth_label"),
                "truth_b": y.get("truth_label"),
                "prediction_a": x.get("predicted_label"),
                "prediction_b": y.get("predicted_label"),
                "correct_a": x.get("correctness"),
                "correct_b": y.get("correctness"),
                "quality_a": round(float(x.get("quality", 0.0)), 4),
                "quality_b": round(float(y.get("quality", 0.0)), 4),
                "outcome_changed": bool(x.get("correctness") != y.get("correctness")),
            }
        )
    return rows


def _metric_diffs(ma: Dict[str, Any], mb: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k in sorted(set(ma) & set(mb)):
        if k == "details":
            continue
        va, vb = ma[k], mb[k]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[k] = {
                "a": round(float(va), 6),
                "b": round(float(vb), 6),
                "delta": round(float(vb - va), 6),
            }
    return out


def compare_experiments(a: Experiment, b: Experiment) -> Dict[str, Any]:
    """Compare two experiments (any mechanisms/configs)."""
    pa, pb = a.parameters, b.parameters
    config_diffs = {
        "mechanism": {"a": a.mechanism, "b": b.mechanism},
        "seed": {"a": a.seed, "b": b.seed},
        "parameters": {
            k: {"a": pa.get(k), "b": pb.get(k)}
            for k in sorted(set(pa) | set(pb))
            if pa.get(k) != pb.get(k)
        },
    }
    va = np.asarray(a.snapshots[-1]["state_vector"], dtype=np.float64)
    vb = np.asarray(b.snapshots[-1]["state_vector"], dtype=np.float64)
    state_distance = (
        compare_states(va, vb) if va.shape == vb.shape else None
    )
    preds = _aligned_prediction_diffs(a, b)
    changed = [p for p in preds if p["outcome_changed"]]
    return {
        "experiment_a": a.experiment_id,
        "experiment_b": b.experiment_id,
        "configuration_differences": config_diffs,
        "metric_differences": _metric_diffs(a.metrics, b.metrics),
        "state_distance": state_distance,
        "prediction_differences": preds,
        "changed_outcomes": changed,
        "num_changed_outcomes": len(changed),
    }