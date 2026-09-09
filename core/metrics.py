"""Metrics (section 11).

Every metric is defined precisely below; no invented semantics. The inputs
are the recorded snapshots, the query results, and the task history — all
objects the experiment engine already produces, so metrics are pure
functions of the experiment record (side-effect free, trivially testable).

Definitions
-----------
Let ``x_t`` be the state after event ``t`` (``x_0`` the initial zero state),
``v̂_q`` the predicted value vector for query ``q``, ``v_q`` its ground-truth
vector, and ``cos`` the cosine similarity (0 when either vector is zero).

recall_accuracy    fraction of queries whose predicted symbol label equals
                   the ground-truth label.
recall_quality     mean cosine(v̂_q, v_q) over all queries — *how close* the
                   readout is to the true value, not just the label.
error_rate         1 - recall_accuracy.
mean_squared_error mean ||v̂_q - v_q||² over all queries.
state_similarity   mean over t>=1 of cos(x_t, x_{t-1}): how stable the state
                   is from one event to the next (1 = unchanged, 0 = orthogonal).
state_drift        mean over t>=1 of (1 - cos(x_t, x_{t-1})): how much the
                   state re-orients per event. Complement of state_similarity.
update_magnitude   mean over t>=1 of ||x_t - x_{t-1}||: how hard each event
                   pushes the state (Frobenius norm for matrix mechanisms).
memory_retention   mean cosine(v̂_q, v_q) over the *final* "latest" queries
                   (one per object): how well the end-of-run state still
                   retrieves each object's most recent binding.
interference_score for conflicted objects: mean max(0, cos(v̂_q, v_old)) over
                   their final "latest" queries, where v_old is the
                   *superseded* value — leakage of the old binding into the
                   readout (higher = worse). When the task has no conflicts,
                   falls back to mean (1 - cosine(v̂_q, v_q)) over final
                   "latest" queries (cross-talk noise from superposition).
recovery_score     for conflicted objects: mean of
                   quality(final) / quality(immediately after the conflict
                   write), where quality = cosine(v̂, v_new). >1 means the
                   new binding strengthened over time; <1 means later events
                   eroded it. 0 when the denominator is (near) zero.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from .recall import QueryResult
from .task import Task
from .vectors import cosine

METRIC_DEFINITIONS: Dict[str, str] = {
    "recall_accuracy": (
        "fraction of queries whose predicted symbol label equals the "
        "ground-truth label"
    ),
    "recall_quality": "mean cosine(predicted_vector, truth_vector) over queries",
    "error_rate": "1 - recall_accuracy",
    "mean_squared_error": "mean ||predicted_vector - truth_vector||^2 over queries",
    "state_similarity": (
        "mean cosine(x_t, x_{t-1}) over consecutive snapshots — state "
        "stability from one event to the next"
    ),
    "state_drift": (
        "mean (1 - cosine(x_t, x_{t-1})) over consecutive snapshots — "
        "re-orientation of the state per event"
    ),
    "update_magnitude": (
        "mean ||x_t - x_{t-1}|| over consecutive snapshots — how hard each "
        "event pushes the state"
    ),
    "memory_retention": (
        "mean cosine(predicted, truth) over the final 'latest' query per "
        "object — how well the end-of-run state retrieves each object's "
        "most recent binding"
    ),
    "interference_score": (
        "mean max(0, cosine(predicted, superseded_value)) for conflicted "
        "objects (leakage of the old binding); cross-talk fallback "
        "(mean 1 - quality) when no conflicts exist"
    ),
    "recovery_score": (
        "mean over conflicted objects of quality(final) / "
        "quality(immediately after the conflict write); >1 strengthens, "
        "<1 erodes"
    ),
}


def _snapshot_vector(snap: Dict[str, Any]) -> np.ndarray:
    return np.asarray(snap["state_vector"], dtype=np.float64)


def _final_latest_results(
    results: List[QueryResult],
) -> Dict[str, QueryResult]:
    """Per object: the query result at the final timestep with kind=latest."""
    out: Dict[str, QueryResult] = {}
    max_ts = max((r.timestep for r in results), default=-1)
    for r in results:
        if r.kind == "latest" and r.timestep == max_ts:
            out.setdefault(r.object_label, r)
    return out


def compute_metrics(
    snapshots: List[Dict[str, Any]],
    query_results: List[QueryResult],
    task: Task,
) -> Dict[str, Any]:
    """Compute all metrics from the experiment record (pure function)."""
    n_q = len(query_results)
    accuracy = (
        float(np.mean([1.0 if r.correctness else 0.0 for r in query_results]))
        if n_q
        else 0.0
    )
    quality = float(np.mean([r.quality for r in query_results])) if n_q else 0.0
    mse = (
        float(
            np.mean(
                [
                    float(
                        np.sum(
                            (r.predicted_vector - task.symbols[r.truth_label]) ** 2
                        )
                    )
                    for r in query_results
                ]
            )
        )
        if n_q
        else 0.0
    )

    # ---- state trajectory metrics ---------------------------------------
    vecs = [_snapshot_vector(s) for s in snapshots]
    sims, drifts, mags = [], [], []
    for a, b in zip(vecs[:-1], vecs[1:]):
        c = cosine(a, b)
        sims.append(c)
        drifts.append(1.0 - c)
        mags.append(float(np.linalg.norm(b - a)))
    state_similarity = float(np.mean(sims)) if sims else 0.0
    state_drift = float(np.mean(drifts)) if drifts else 0.0
    update_magnitude = float(np.mean(mags)) if mags else 0.0

    # ---- memory content metrics -----------------------------------------
    final_latest = _final_latest_results(query_results)
    retention = (
        float(np.mean([r.quality for r in final_latest.values()]))
        if final_latest
        else 0.0
    )

    conflict_keys = sorted(task.conflicts.keys())
    interference_vals: List[float] = []
    recovery_vals: List[float] = []
    per_conflict: Dict[str, Dict[str, Any]] = {}
    for obj in conflict_keys:
        recs = task.conflicts[obj]
        old_sym = recs[0]["old_symbol"]
        old_vec = task.symbols[old_sym]
        new_sym = recs[-1]["new_symbol"]
        final = final_latest.get(obj)
        # quality immediately after the conflict write
        after_write = next(
            (r for r in query_results if r.object_label == obj and r.kind == "latest" and r.timestep == recs[-1]["timestep"]),
            None,
        )
        if final is not None:
            leak = max(0.0, cosine(final.predicted_vector, old_vec))
            interference_vals.append(leak)
            if after_write is not None:
                denom = after_write.quality
                recovery = float(final.quality / denom) if denom > 1e-9 else 0.0
            else:
                recovery = 0.0
            recovery_vals.append(recovery)
            per_conflict[obj] = {
                "old_symbol": old_sym,
                "new_symbol": new_sym,
                "final_quality": float(final.quality),
                "after_write_quality": (
                    float(after_write.quality) if after_write is not None else None
                ),
                "old_leakage": float(leak),
                "recovery": float(recovery),
            }

    if interference_vals:
        interference_score = float(np.mean(interference_vals))
    else:
        # no conflicts: cross-talk noise on the final latest queries
        interference_score = (
            float(np.mean([1.0 - r.quality for r in final_latest.values()]))
            if final_latest
            else 0.0
        )
    recovery_score = float(np.mean(recovery_vals)) if recovery_vals else None

    return {
        "recall_accuracy": float(accuracy),
        "recall_quality": float(quality),
        "error_rate": float(1.0 - accuracy),
        "mean_squared_error": float(mse),
        "state_similarity": float(state_similarity),
        "state_drift": float(state_drift),
        "update_magnitude": float(update_magnitude),
        "memory_retention": float(retention),
        "interference_score": float(interference_score),
        "recovery_score": recovery_score,
        "details": {
            "num_queries": int(n_q),
            "num_snapshots": int(len(snapshots)),
            "num_events": int(len(task.events)),
            "conflict_keys": conflict_keys,
            "per_object_final_quality": {
                obj: float(r.quality) for obj, r in sorted(final_latest.items())
            },
            "per_conflict": per_conflict,
        },
    }