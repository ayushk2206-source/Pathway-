"""Computational search for what-if scenarios and minimal interventions (Phase 04)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from core.experiment import Experiment
from .interventions import (
    Intervention,
    create_change_strength_intervention,
    create_freeze_memory_intervention,
    create_remove_intervention,
)
from .replay import replay_counterfactual_engine
from .types import InterventionType, MAX_SEARCH_COMBINATIONS


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


def _intervention_magnitude(intervention: Intervention, orig_event: Optional[Dict[str, Any]] = None) -> float:
    """Quantify the magnitude / invasiveness of an intervention."""
    itype = intervention.intervention_type
    p = intervention.parameters

    if itype == InterventionType.REMOVE_EVENT:
        return 1.0  # complete deletion of an event

    elif itype == InterventionType.CHANGE_STRENGTH:
        orig_s = float(orig_event.get("strength", 1.0)) if orig_event else 1.0
        new_s = p.get("new_strength")
        if new_s is not None:
            return abs(float(new_s) - orig_s)
        factor = p.get("factor", 1.0)
        return abs(1.0 - float(factor))

    elif itype == InterventionType.MODIFY_EVENT:
        mods = p.get("modifications", {})
        mag = 0.0
        if "strength" in mods and orig_event:
            mag += abs(float(mods["strength"]) - float(orig_event.get("strength", 1.0)))
        if "importance" in mods and orig_event:
            mag += abs(float(mods["importance"]) - float(orig_event.get("importance", 1.0)))
        return mag if mag > 0 else 0.5

    elif itype in {InterventionType.FREEZE_MEMORY, InterventionType.TEMPORAL_FREEZE}:
        start = int(p.get("start_timestep", 0))
        end = int(p.get("end_timestep", 0))
        return float(end - start + 1) * 0.5

    return 1.0


def search_counterfactuals(
    experiment: Experiment,
    target_metric: str = "interference_score",
    target_direction: str = "decrease",
    allowed_interventions: Optional[List[str]] = None,
    max_candidates: int = 36,
) -> Dict[str, Any]:
    """Search over an intervention space to find the counterfactual that most improves target_metric."""
    orig_val = float(experiment.metrics.get(target_metric, 0.0))
    events = experiment.events[:min(len(experiment.events), MAX_SEARCH_COMBINATIONS)]

    allowed = set(allowed_interventions) if allowed_interventions else {
        InterventionType.REMOVE_EVENT.value,
        InterventionType.CHANGE_STRENGTH.value,
    }

    candidates: List[Intervention] = []

    # 1. Ablation candidates
    if InterventionType.REMOVE_EVENT.value in allowed:
        for idx, ev in enumerate(events):
            candidates.append(
                create_remove_intervention(
                    target_timestep=idx,
                    target_event_id=ev.get("id"),
                    description=f"Remove event at t={idx} ({ev.get('concept_label')}={ev.get('attribute_label')})",
                )
            )

    # 2. Strength modulation candidates (surgical tuning)
    if InterventionType.CHANGE_STRENGTH.value in allowed:
        for idx, ev in enumerate(events):
            for strength in [0.2, 0.5, 1.5]:
                candidates.append(
                    create_change_strength_intervention(
                        new_strength=strength,
                        target_timestep=idx,
                        target_event_id=ev.get("id"),
                        description=f"Set strength to {strength} at t={idx}",
                    )
                )

    # Limit search quota
    candidates = candidates[:max_candidates]

    results: List[Dict[str, Any]] = []
    for intv in candidates:
        try:
            cf_exp, _ = replay_counterfactual_engine(experiment, intv)
            cf_val = float(cf_exp.metrics.get(target_metric, 0.0))

            if target_direction.lower() == "decrease":
                improvement = orig_val - cf_val
            else:
                improvement = cf_val - orig_val

            target_ev = experiment.events[intv.target_timestep] if intv.target_timestep is not None and intv.target_timestep < len(experiment.events) else None
            mag = _intervention_magnitude(intv, target_ev)

            results.append({
                "intervention": intv.to_dict(),
                "counterfactual_metric": cf_val,
                "improvement": improvement,
                "magnitude": mag,
                "metrics": cf_exp.metrics,
            })
        except Exception:
            continue

    # Sort by improvement descending
    results.sort(key=lambda x: x["improvement"], reverse=True)

    best_intervention = results[0] if results else None

    return {
        "target_metric": target_metric,
        "target_direction": target_direction,
        "baseline_metric": orig_val,
        "total_evaluated": len(results),
        "best_intervention": _sanitize(best_intervention),
        "ranked_candidates": _sanitize(results),
    }


def find_minimal_intervention(
    experiment: Experiment,
    target_metric: str = "interference_score",
    target_improvement: float = 0.10,
    target_direction: str = "decrease",
    allowed_interventions: Optional[List[str]] = None,
    max_candidates: int = 50,
) -> Dict[str, Any]:
    """Find the smallest-magnitude intervention that satisfies the target metric improvement."""
    orig_val = float(experiment.metrics.get(target_metric, 0.0))
    events = experiment.events[:min(len(experiment.events), MAX_SEARCH_COMBINATIONS)]

    candidates: List[Tuple[Intervention, float]] = []

    # Explore fine-grained surgical strength modulations first (smaller magnitudes)
    for idx, ev in enumerate(events):
        orig_s = float(ev.get("strength", 1.0))
        # Small perturbations: 0.9, 0.8, 0.6, 0.4, 0.2, 0.0
        for s in [0.8, 0.6, 0.4, 0.2, 0.0]:
            intv = create_change_strength_intervention(
                new_strength=s,
                target_timestep=idx,
                target_event_id=ev.get("id"),
                description=f"Reduce strength from {orig_s} to {s} at t={idx}",
            )
            candidates.append((intv, abs(orig_s - s)))

    # Add full event ablations (magnitude 1.0)
    for idx, ev in enumerate(events):
        intv = create_remove_intervention(
            target_timestep=idx,
            target_event_id=ev.get("id"),
            description=f"Ablate event at t={idx}",
        )
        candidates.append((intv, 1.0))

    # Add temporal freezes
    if len(events) >= 3:
        for t in range(len(events) - 1):
            intv = create_freeze_memory_intervention(start_timestep=t, end_timestep=t + 1)
            candidates.append((intv, 1.0))

    # Evaluate candidates
    successful_interventions: List[Dict[str, Any]] = []

    for intv, mag in candidates[:max_candidates]:
        try:
            cf_exp, _ = replay_counterfactual_engine(experiment, intv)
            cf_val = float(cf_exp.metrics.get(target_metric, 0.0))

            if target_direction.lower() == "decrease":
                improvement = orig_val - cf_val
            else:
                improvement = cf_val - orig_val

            if improvement >= target_improvement:
                successful_interventions.append({
                    "intervention": intv.to_dict(),
                    "magnitude": mag,
                    "counterfactual_metric": cf_val,
                    "baseline_metric": orig_val,
                    "improvement": improvement,
                    "metrics": cf_exp.metrics,
                })
        except Exception:
            continue

    if successful_interventions:
        # Sort by magnitude ascending, then by improvement descending
        successful_interventions.sort(key=lambda x: (x["magnitude"], -x["improvement"]))
        minimal = successful_interventions[0]
        return {
            "success": True,
            "target_metric": target_metric,
            "target_improvement": target_improvement,
            "baseline_metric": orig_val,
            "minimal_intervention": _sanitize(minimal["intervention"]),
            "magnitude": float(minimal["magnitude"]),
            "result_metric": float(minimal["counterfactual_metric"]),
            "observed_improvement": float(minimal["improvement"]),
            "total_satisfying_candidates": len(successful_interventions),
            "explanation": (
                f"Found minimal intervention with magnitude {minimal['magnitude']:.3f} "
                f"achieving an improvement of {minimal['improvement']:.4f} on '{target_metric}' "
                f"(exceeding target threshold of {target_improvement:.4f})."
            ),
        }

    return {
        "success": False,
        "target_metric": target_metric,
        "target_improvement": target_improvement,
        "baseline_metric": orig_val,
        "minimal_intervention": None,
        "magnitude": None,
        "result_metric": None,
        "observed_improvement": None,
        "total_satisfying_candidates": 0,
        "explanation": f"No tested intervention achieved the requested target improvement of {target_improvement:.4f} on '{target_metric}'.",
    }
