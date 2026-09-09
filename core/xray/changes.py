"""State change detection between consecutive timeline steps (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from .models import StateChangeRecord, StateTrajectory
from .types import StateChangeClassification


def detect_state_changes(trajectory: StateTrajectory) -> Dict[str, Any]:
    """Calculate consecutive state deltas ΔS and classify transition regimes.

    Identifies:
    - low-change regions (stable intervals)
    - high-change regions (active write/interference phases)
    - sudden transitions (abrupt shocks)
    - stabilization periods (decaying delta magnitudes)
    """
    vectors = [np.asarray(v, dtype=np.float64) for v in trajectory.state_vectors]
    records: List[StateChangeRecord] = []
    magnitudes: List[float] = []

    if len(vectors) < 2:
        return {
            "records": [],
            "low_change_regions": [],
            "high_change_regions": [],
            "sudden_transitions": [],
            "stabilization_periods": [],
            "mean_change_magnitude": 0.0,
            "max_change_magnitude": 0.0,
        }

    for i in range(len(vectors) - 1):
        s_prev = vectors[i]
        s_curr = vectors[i + 1]
        ev_id = trajectory.event_ids[i + 1]
        step_idx = trajectory.steps[i + 1]

        delta = s_curr - s_prev
        l2_delta = float(np.linalg.norm(delta))

        # Relative change magnitude scaled by current norm
        norm_prev = float(np.linalg.norm(s_prev))
        norm_curr = float(np.linalg.norm(s_curr))
        base_norm = 0.5 * (norm_prev + norm_curr)

        if base_norm > 1e-12:
            change_mag = float(l2_delta / base_norm)
        else:
            change_mag = l2_delta

        # Cosine shift
        denom = norm_prev * norm_curr
        if denom > 1e-12:
            cos_sim = float(np.dot(s_prev, s_curr) / denom)
            cos_delta = float(1.0 - max(-1.0, min(1.0, cos_sim)))
        else:
            cos_delta = 1.0 if l2_delta > 1e-6 else 0.0

        # Classification
        if change_mag < 0.25:
            classification = StateChangeClassification.STABLE
        elif change_mag < 0.85:
            classification = StateChangeClassification.SHIFT
        else:
            classification = StateChangeClassification.MAJOR_SHIFT

        records.append(
            StateChangeRecord(
                step=step_idx,
                event_id=ev_id,
                change_magnitude=change_mag,
                l2_delta=l2_delta,
                cosine_delta=cos_delta,
                classification=classification,
            )
        )
        magnitudes.append(change_mag)

    # Statistical baseline for region identification
    mean_mag = float(np.mean(magnitudes)) if magnitudes else 0.0
    std_mag = float(np.std(magnitudes)) if magnitudes else 0.0
    max_mag = float(np.max(magnitudes)) if magnitudes else 0.0

    low_change_regions: List[Dict[str, Any]] = []
    high_change_regions: List[Dict[str, Any]] = []
    sudden_transitions: List[Dict[str, Any]] = []
    stabilization_periods: List[Dict[str, Any]] = []

    current_low: Optional[Dict[str, Any]] = None
    current_high: Optional[Dict[str, Any]] = None

    for r in records:
        # Check sudden transition (outlier change)
        if (std_mag > 1e-9 and (r.change_magnitude - mean_mag) / std_mag > 1.8) or (
            r.classification == StateChangeClassification.MAJOR_SHIFT
        ):
            sudden_transitions.append({
                "step": r.step,
                "event_id": r.event_id,
                "magnitude": r.change_magnitude,
                "z_score": float((r.change_magnitude - mean_mag) / std_mag) if std_mag > 1e-9 else 2.0,
            })

        # Low change tracking
        if r.classification == StateChangeClassification.STABLE:
            if current_low is None:
                current_low = {"start_step": r.step, "end_step": r.step, "steps": [r.step]}
            else:
                current_low["end_step"] = r.step
                current_low["steps"].append(r.step)
        else:
            if current_low:
                low_change_regions.append(current_low)
                current_low = None

        # High change tracking
        if r.classification in (StateChangeClassification.SHIFT, StateChangeClassification.MAJOR_SHIFT):
            if current_high is None:
                current_high = {"start_step": r.step, "end_step": r.step, "steps": [r.step]}
            else:
                current_high["end_step"] = r.step
                current_high["steps"].append(r.step)
        else:
            if current_high:
                high_change_regions.append(current_high)
                current_high = None

    if current_low:
        low_change_regions.append(current_low)
    if current_high:
        high_change_regions.append(current_high)

    # Stabilization periods: windows of >= 2 consecutive steps where magnitude monotonically decays
    for i in range(len(records) - 2):
        if (
            records[i].change_magnitude > records[i + 1].change_magnitude
            and records[i + 1].change_magnitude > records[i + 2].change_magnitude
            and records[i + 2].change_magnitude < mean_mag
        ):
            stabilization_periods.append({
                "start_step": records[i].step,
                "end_step": records[i + 2].step,
                "delta_drop": records[i].change_magnitude - records[i + 2].change_magnitude,
            })

    return {
        "records": [r.to_dict() for r in records],
        "low_change_regions": low_change_regions,
        "high_change_regions": high_change_regions,
        "sudden_transitions": sudden_transitions,
        "stabilization_periods": stabilization_periods,
        "mean_change_magnitude": mean_mag,
        "max_change_magnitude": max_mag,
    }
