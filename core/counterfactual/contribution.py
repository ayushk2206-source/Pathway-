"""Counterfactual contribution analysis and forensic forgetting reconstruction (Phase 04)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np

from core.experiment import Experiment
from .interventions import create_remove_intervention
from .replay import replay_counterfactual_engine


def _sanitize(val: Any) -> Any:
    if isinstance(val, (np.floating, float)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, dict):
        return {k: _sanitize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize(v) for v in val]
    return val


def estimate_event_contribution(
    experiment: Experiment,
    target_metric: Optional[str] = "interference_score",
    target_object: Optional[str] = None,
    max_candidates: int = 50,
) -> Dict[str, Any]:
    """Estimate the counterfactual contribution of historical events by single-event ablation.

    For each event in the historical trajectory:
    1. Replays a counterfactual history with that single event ablated.
    2. Measures the delta in target metric or target object recall.
    3. Ranks candidates by empirical effect size.

    Scientifically framed as simulation-bounded counterfactual contribution,
    not universal causal attribution.
    """
    events = experiment.events[:max_candidates]
    orig_metrics = experiment.metrics
    orig_queries = {q.get("object_label"): q for q in experiment.queries}

    candidates_evaluated: List[Dict[str, Any]] = []

    for idx, ev in enumerate(events):
        ev_id = ev.get("id", f"e{idx:04d}")
        intv = create_remove_intervention(target_timestep=idx, target_event_id=ev_id)

        try:
            cf_exp, _ = replay_counterfactual_engine(experiment, intv)
        except Exception:
            continue

        # 1. State difference
        orig_vec = np.asarray(experiment.snapshots[-1].get("state_vector", []), dtype=np.float64)
        cf_vec = np.asarray(cf_exp.snapshots[-1].get("state_vector", []), dtype=np.float64)
        state_l2 = float(np.linalg.norm(cf_vec - orig_vec)) if orig_vec.size == cf_vec.size and orig_vec.size > 0 else 0.0

        # 2. Metric impact
        cf_metrics = cf_exp.metrics
        metric_delta = 0.0
        if target_metric and target_metric in orig_metrics and target_metric in cf_metrics:
            metric_delta = float(cf_metrics[target_metric] - orig_metrics[target_metric])

        # 3. Target object recall impact (if examining a specific forgotten memory)
        obj_quality_delta = 0.0
        obj_recovered = False
        if target_object:
            q_orig = orig_queries.get(target_object)
            cf_queries = {q.get("object_label"): q for q in cf_exp.queries}
            q_cf = cf_queries.get(target_object)
            if q_orig and q_cf:
                obj_quality_delta = float(q_cf.get("quality", 0.0) - q_orig.get("quality", 0.0))
                if not q_orig.get("correctness") and q_cf.get("correctness"):
                    obj_recovered = True

        # Primary effect size: object quality delta if target_object specified, else metric delta or state distance
        if target_object:
            effect_size = abs(obj_quality_delta)
        elif target_metric:
            effect_size = abs(metric_delta)
        else:
            effect_size = state_l2

        candidates_evaluated.append({
            "event_id": ev_id,
            "timestep": idx,
            "concept_label": ev.get("concept_label"),
            "attribute_label": ev.get("attribute_label"),
            "importance": float(ev.get("importance", 1.0)),
            "strength": float(ev.get("strength", 1.0)),
            "effect_size": float(effect_size),
            "state_distance_l2": float(state_l2),
            "metric_delta": float(metric_delta),
            "target_object_quality_delta": float(obj_quality_delta) if target_object else None,
            "target_object_recovered": bool(obj_recovered) if target_object else None,
        })

    # Sort candidates by effect size descending
    candidates_evaluated.sort(key=lambda x: x["effect_size"], reverse=True)

    # Assign ranks
    for rank, item in enumerate(candidates_evaluated, start=1):
        item["rank"] = rank

    summary_target = f"target object '{target_object}'" if target_object else f"target metric '{target_metric}'"
    top_candidate = candidates_evaluated[0] if candidates_evaluated else None

    if top_candidate and top_candidate["effect_size"] > 1e-4:
        forensic_summary = (
            f"Ablating event '{top_candidate['event_id']}' ({top_candidate['concept_label']}={top_candidate['attribute_label']} at t={top_candidate['timestep']}) "
            f"produced the largest observed counterfactual shift on {summary_target} (effect size={top_candidate['effect_size']:.4f})."
        )
    else:
        forensic_summary = f"No single historical event ablation produced a significant isolated shift on {summary_target}."

    return {
        "target_metric": target_metric,
        "target_object": target_object,
        "total_events_evaluated": len(candidates_evaluated),
        "forensic_summary": forensic_summary,
        "ranked_contributions": _sanitize(candidates_evaluated),
        "causal_safety_disclaimer": (
            "These rankings reflect one-at-a-time counterfactual ablation deltas within the deterministic simulation. "
            "Because memory update mechanisms exhibit non-linear compounding interactions (superposition, decay, competition), "
            "individual effect sizes should not be interpreted as linear or isolated universal causes."
        ),
    }
