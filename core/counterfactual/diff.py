"""Structural event differences, parameter shifts, and state diffs between histories (Phase 04)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np

from core.analysis import compare_states
from core.experiment import Experiment


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


def diff_histories(
    history_a: Union[Experiment, Dict[str, Any]],
    history_b: Union[Experiment, Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate structural event diffs, parameter differences, state distance, and metric deltas."""
    ha = history_a.to_dict() if hasattr(history_a, "to_dict") else dict(history_a)
    hb = history_b.to_dict() if hasattr(history_b, "to_dict") else dict(history_b)

    events_a = ha.get("events", [])
    events_b = hb.get("events", [])

    # Map events by ID and by content
    ids_a = {e.get("id"): (i, e) for i, e in enumerate(events_a) if e.get("id")}
    ids_b = {e.get("id"): (i, e) for i, e in enumerate(events_b) if e.get("id")}

    added_events: List[Dict[str, Any]] = []
    removed_events: List[Dict[str, Any]] = []
    modified_events: List[Dict[str, Any]] = []
    moved_events: List[Dict[str, Any]] = []

    # Check for removed or modified/moved events from A
    for eid, (idx_a, ev_a) in ids_a.items():
        if eid not in ids_b:
            removed_events.append({
                "id": eid,
                "timestep": idx_a,
                "concept": ev_a.get("concept_label"),
                "value": ev_a.get("attribute_label"),
            })
        else:
            idx_b, ev_b = ids_b[eid]
            if idx_a != idx_b:
                moved_events.append({
                    "id": eid,
                    "from_timestep": idx_a,
                    "to_timestep": idx_b,
                    "concept": ev_a.get("concept_label"),
                })
            # Check property modifications
            mods: Dict[str, Any] = {}
            for prop in ["strength", "importance", "noise", "concept_label", "attribute_label"]:
                va = ev_a.get(prop)
                vb = ev_b.get(prop)
                if va != vb and not (va is None and vb is None):
                    mods[prop] = {"from": va, "to": vb}
            if mods:
                modified_events.append({
                    "id": eid,
                    "timestep": idx_b,
                    "modifications": mods,
                })

    # Check for added events in B
    for eid, (idx_b, ev_b) in ids_b.items():
        if eid not in ids_a:
            added_events.append({
                "id": eid,
                "timestep": idx_b,
                "concept": ev_b.get("concept_label"),
                "value": ev_b.get("attribute_label"),
            })

    # Parameter changes between configs
    params_a = ha.get("parameters", {})
    params_b = hb.get("parameters", {})
    all_param_keys = set(params_a.keys()) | set(params_b.keys())
    parameter_changes: Dict[str, Dict[str, Any]] = {}
    for k in sorted(all_param_keys):
        va = params_a.get(k)
        vb = params_b.get(k)
        if va != vb:
            parameter_changes[k] = {"from": va, "to": vb}

    # Final state difference
    snaps_a = ha.get("snapshots", [])
    snaps_b = hb.get("snapshots", [])
    vec_a = snaps_a[-1].get("state_vector") if snaps_a else None
    vec_b = snaps_b[-1].get("state_vector") if snaps_b else None

    if vec_a is not None and vec_b is not None:
        state_difference = compare_states(vec_a, vec_b)
    else:
        state_difference = {"error": "State vector unavailable in one or both histories"}

    # Metric differences
    metrics_a = ha.get("metrics", {})
    metrics_b = hb.get("metrics", {})
    all_metric_keys = set(metrics_a.keys()) | set(metrics_b.keys())
    metric_deltas: Dict[str, float] = {}
    percentage_changes: Dict[str, Optional[float]] = {}

    for k in sorted(all_metric_keys):
        ma = metrics_a.get(k)
        mb = metrics_b.get(k)
        if isinstance(ma, (int, float)) and isinstance(mb, (int, float)):
            delta = float(mb - ma)
            metric_deltas[k] = delta
            if abs(ma) > 1e-6:
                percentage_changes[k] = float((delta / ma) * 100.0)
            else:
                percentage_changes[k] = None

    return {
        "event_differences": {
            "added_events": added_events,
            "removed_events": removed_events,
            "modified_events": modified_events,
            "moved_events": moved_events,
            "total_event_changes": len(added_events) + len(removed_events) + len(modified_events) + len(moved_events),
        },
        "parameter_changes": parameter_changes,
        "state_difference": _sanitize(state_difference),
        "metric_difference": {
            "metric_deltas": _sanitize(metric_deltas),
            "percentage_changes": _sanitize(percentage_changes),
        },
    }
