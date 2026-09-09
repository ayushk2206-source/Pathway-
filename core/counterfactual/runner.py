"""High-level runner entrypoints for Counterfactual Memory Archaeology (Phase 04)."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional, Union

import numpy as np

from core.analysis import compare_states
from core.experiment import Experiment
from .diff import diff_histories
from .divergence import compute_divergence_profile
from .explanation import generate_counterfactual_explanation
from .interventions import (
    Intervention,
    create_modify_intervention,
    create_remove_intervention,
)
from .models import CounterfactualExperiment
from .replay import replay_counterfactual_engine
from .types import CounterfactualStatus, InterventionType, ReplayStrategy


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


def run_counterfactual(
    experiment: Experiment,
    intervention: Intervention,
    strategy: ReplayStrategy = ReplayStrategy.FULL_REPLAY,
    title: str = "",
    description: str = "",
) -> CounterfactualExperiment:
    """Execute a counterfactual intervention against an immutable history.

    Replays the memory engine, computes divergence propagation, structural diffs,
    and returns a fully structured CounterfactualExperiment record.
    """
    cf_id = f"cf-{uuid.uuid4().hex[:8]}"

    # Execute replay (original experiment is strictly unchanged)
    cf_exp, branch_point = replay_counterfactual_engine(experiment, intervention, strategy=strategy)

    # Compute step-by-step divergence profile
    target_idx = intervention.target_timestep if intervention.target_timestep is not None else branch_point
    divergence = compute_divergence_profile(experiment, cf_exp, intervention_step=target_idx)

    # Compute structural & state diffs
    diff = diff_histories(experiment, cf_exp)

    # Locate target event summary for narrative explanation
    target_ev_summary = None
    if intervention.target_timestep is not None and 0 <= intervention.target_timestep < len(experiment.events):
        target_ev_summary = experiment.events[intervention.target_timestep]
    elif intervention.target_event_id:
        for ev in experiment.events:
            if ev.get("id") == intervention.target_event_id:
                target_ev_summary = ev
                break

    # Generate deterministic natural language explanation
    explanation = generate_counterfactual_explanation(
        intervention=intervention,
        divergence=divergence,
        original_metrics=experiment.metrics,
        counterfactual_metrics=cf_exp.metrics,
        target_event_summary=target_ev_summary,
    )

    # Provenance metadata
    provenance = {
        "parent_experiment_id": experiment.experiment_id,
        "master_seed": experiment.seed,
        "mechanism": experiment.mechanism,
        "branch_point": branch_point,
        "replay_strategy": strategy.value if isinstance(strategy, ReplayStrategy) else str(strategy),
        "engine_version": getattr(experiment, "version", 1),
        "history_length_original": len(experiment.events),
        "history_length_counterfactual": len(cf_exp.events),
        "explanation": explanation,
    }

    original_result = {
        "metrics": experiment.metrics,
        "final_state_norm": float(np.linalg.norm(experiment.snapshots[-1].get("state_vector", []))),
        "num_events": len(experiment.events),
    }

    counterfactual_result = {
        "metrics": cf_exp.metrics,
        "final_state_norm": float(np.linalg.norm(cf_exp.snapshots[-1].get("state_vector", []))),
        "num_events": len(cf_exp.events),
        "experiment_id": cf_exp.experiment_id,
        "experiment": cf_exp.to_dict(),
    }

    comparison = {
        "diff": diff,
        "state_distance_l2": divergence.final_state_distance_l2,
        "cosine_similarity": divergence.final_cosine_similarity,
        "relative_l2": divergence.final_relative_l2,
        "first_divergence_step": divergence.first_divergence_step,
        "divergence_classification": divergence.classification.value,
        "explanation": explanation["detailed_narrative"],
    }

    return CounterfactualExperiment(
        counterfactual_id=cf_id,
        parent_experiment_id=experiment.experiment_id,
        parent_history_id=experiment.config.get("history_id"),
        title=title or f"Counterfactual: {intervention.description or intervention.intervention_type.value}",
        description=description or explanation["summary"],
        original_configuration=experiment.config,
        intervention=intervention.to_dict(),
        intervention_type=intervention.intervention_type.value,
        intervention_target=intervention.target_event_id or intervention.target_timestep,
        intervention_parameters=intervention.parameters,
        original_result=original_result,
        counterfactual_result=counterfactual_result,
        comparison=comparison,
        divergence=divergence.to_dict(),
        provenance=provenance,
        status=CounterfactualStatus.COMPLETED,
    )


def create_ablation(
    experiment: Experiment,
    event_id_or_timestep: int | str,
    title: str = "",
) -> CounterfactualExperiment:
    """Specialized memory ablation: remove one event from history and track downstream impact."""
    if isinstance(event_id_or_timestep, int):
        intv = create_remove_intervention(target_timestep=event_id_or_timestep)
    else:
        intv = create_remove_intervention(target_event_id=event_id_or_timestep)
    return run_counterfactual(
        experiment=experiment,
        intervention=intv,
        title=title or f"Memory Ablation ({event_id_or_timestep})",
    )


def create_surgery(
    experiment: Experiment,
    event_id_or_timestep: int | str,
    modifications: Dict[str, Any],
    title: str = "",
) -> CounterfactualExperiment:
    """Specialized memory surgery: surgically modify properties of one historical memory."""
    if isinstance(event_id_or_timestep, int):
        intv = create_modify_intervention(modifications=modifications, target_timestep=event_id_or_timestep)
    else:
        intv = create_modify_intervention(modifications=modifications, target_event_id=event_id_or_timestep)
    return run_counterfactual(
        experiment=experiment,
        intervention=intv,
        title=title or f"Memory Surgery ({event_id_or_timestep})",
    )


def reproduce_counterfactual(
    original_experiment: Experiment,
    intervention: Intervention,
    expected_metrics: Dict[str, float],
    tolerance: float = 1e-9,
) -> Dict[str, Any]:
    """Verify bit-exact reproducibility of a counterfactual experiment within numerical tolerance."""
    reproduced = run_counterfactual(original_experiment, intervention)
    actual_metrics = reproduced.counterfactual_result.get("metrics", {})

    matches: Dict[str, Dict[str, Any]] = {}
    all_matched = True

    for k, expected_val in expected_metrics.items():
        if k in actual_metrics and isinstance(expected_val, (int, float)):
            try:
                act_val = float(actual_metrics[k])
                exp_val = float(expected_val)
            except (ValueError, TypeError):
                continue
            diff = abs(act_val - exp_val)
            is_match = diff <= tolerance
            matches[k] = {
                "expected": exp_val,
                "actual": act_val,
                "diff": diff,
                "matched": is_match,
            }
            if not is_match:
                all_matched = False

    return {
        "reproduced": all_matched,
        "exact_match": all_matched,
        "tolerance": tolerance,
        "metric_matches": matches,
        "reproduced_counterfactual_id": reproduced.counterfactual_id,
    }


def compare_multiple_histories(
    histories: List[Union[Experiment, Dict[str, Any]]],
) -> Dict[str, Any]:
    """Compare multiple timelines against the root history (Original vs Branch A vs Branch B vs Branch C)."""
    if not histories:
        return {"error": "No histories provided for comparison"}

    parsed: List[Dict[str, Any]] = [
        h.to_dict() if hasattr(h, "to_dict") else dict(h) for h in histories
    ]
    root = parsed[0]
    root_id = root.get("experiment_id", "root")

    branches: List[Dict[str, Any]] = []
    comparison_table: List[Dict[str, Any]] = []

    metrics_keys = sorted(root.get("metrics", {}).keys())

    for idx, h in enumerate(parsed):
        hid = h.get("experiment_id", f"hist_{idx}")
        h_metrics = h.get("metrics", {})

        row: Dict[str, Any] = {
            "history_id": hid,
            "is_root": idx == 0,
            "mechanism": h.get("mechanism"),
            "num_events": len(h.get("events", [])),
        }
        for k in metrics_keys:
            row[k] = h_metrics.get(k)
        comparison_table.append(row)

        if idx > 0:
            diff = diff_histories(root, h)
            branches.append({
                "branch_id": hid,
                "state_distance_l2": diff.get("state_difference", {}).get("l2_distance"),
                "cosine_similarity": diff.get("state_difference", {}).get("cosine_similarity"),
                "metric_deltas": diff.get("metric_difference", {}).get("metric_deltas", {}),
                "event_changes_count": diff.get("event_differences", {}).get("total_event_changes", 0),
            })

    return {
        "root_history_id": root_id,
        "total_timelines_compared": len(parsed),
        "metrics_comparison_table": _sanitize(comparison_table),
        "branch_comparisons": _sanitize(branches),
    }
