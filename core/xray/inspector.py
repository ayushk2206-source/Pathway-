"""Microscopic before/after event inspector (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import numpy as np

from core import Experiment
from .diff import compare_states
from .strength import _extract_memory_cues, compute_memory_strengths


def inspect_event_before_after(
    experiment: Experiment,
    event_index_or_id: Union[int, str],
) -> Dict[str, Any]:
    """Inspect the internal computational microscope of state before, after, and diff for an event."""
    events = experiment.events
    snapshots = experiment.snapshots

    # Resolve event index
    if isinstance(event_index_or_id, int):
        ev_idx = event_index_or_id
    else:
        ev_idx = next(
            (i for i, ev in enumerate(events) if ev.get("id") == event_index_or_id),
            0,
        )

    if ev_idx < 0 or ev_idx >= len(events):
        raise IndexError(f"Event index {ev_idx} out of bounds (0 to {len(events)-1})")

    ev = events[ev_idx]
    ev_id = ev.get("id") or f"e{ev_idx:04d}"

    step_before = ev_idx
    step_after = ev_idx + 1

    snap_before = snapshots[step_before]
    snap_after = snapshots[step_after] if step_after < len(snapshots) else snapshots[-1]

    s_before = np.asarray(snap_before.get("state_vector", []), dtype=np.float64)
    s_after = np.asarray(snap_after.get("state_vector", []), dtype=np.float64)

    # 1. State comparison diff
    state_diff = compare_states(s_before, s_after)

    # 2. Changed units
    delta = s_after - s_before
    changed_units_indices = [int(i) for i in np.where(np.abs(delta) > 1e-4)[0]]
    unit_shifts = [
        {
            "unit": int(i),
            "before": float(s_before[i]),
            "after": float(s_after[i]),
            "delta": float(delta[i]),
        }
        for i in changed_units_indices[:20]  # Top 20 unit shifts
    ]

    # 3. Changed memory strengths
    strengths_map = compute_memory_strengths(experiment)
    memories = _extract_memory_cues(experiment)
    memory_strength_deltas: List[Dict[str, Any]] = []

    for m in memories:
        m_id = m["memory_id"]
        prof = strengths_map.get(m_id)
        if not prof:
            continue

        str_b = prof.timeline_strengths[step_before] if step_before < len(prof.timeline_strengths) else 0.0
        str_a = prof.timeline_strengths[step_after] if step_after < len(prof.timeline_strengths) else 0.0
        s_diff = str_a - str_b

        if abs(s_diff) > 0.005:
            memory_strength_deltas.append({
                "memory_id": m_id,
                "label": m["concept_label"],
                "strength_before": str_b,
                "strength_after": str_a,
                "delta": s_diff,
                "direction": "strengthened" if s_diff > 0 else "weakened",
            })

    # 4. Metric changes if queries ran at this step
    queries_before = snap_before.get("query_results", [])
    queries_after = snap_after.get("query_results", [])

    return {
        "event": {
            "index": ev_idx,
            "id": ev_id,
            "concept_label": ev.get("concept_label"),
            "attribute_label": ev.get("attribute_label"),
            "strength": ev.get("strength", 1.0),
            "importance": ev.get("importance", 1.0),
        },
        "state_before": {
            "step": step_before,
            "norm": float(np.linalg.norm(s_before)),
            "sparsity": float(np.mean(np.abs(s_before) > 1e-9)),
            "vector": s_before.tolist(),
        },
        "state_after": {
            "step": step_after,
            "norm": float(np.linalg.norm(s_after)),
            "sparsity": float(np.mean(np.abs(s_after) > 1e-9)),
            "vector": s_after.tolist(),
        },
        "diff": {
            "l1_distance": state_diff.l1_distance,
            "l2_distance": state_diff.l2_distance,
            "cosine_distance": state_diff.cosine_distance,
            "normalized_difference": state_diff.normalized_difference,
            "total_units_changed": len(changed_units_indices),
            "top_unit_shifts": unit_shifts,
            "memory_strength_deltas": memory_strength_deltas,
        },
        "query_results_after": queries_after,
    }
