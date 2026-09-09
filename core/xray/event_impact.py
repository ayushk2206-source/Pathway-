"""Event impact mapping connecting history to state transformations (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from .models import EventImpact
from .strength import _extract_memory_cues, compute_memory_strengths


def compute_event_impact(experiment: Experiment) -> List[EventImpact]:
    """Calculate the precise before/after impact of each event on internal state."""
    snapshots = experiment.snapshots
    events = experiment.events
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)

    impacts: List[EventImpact] = []

    for idx, ev in enumerate(events):
        ev_id = ev.get("id") or f"e{idx:04d}"
        step_before = idx
        step_after = idx + 1

        if step_after >= len(snapshots):
            continue

        snap_before = snapshots[step_before]
        snap_after = snapshots[step_after]

        s_before = np.asarray(snap_before.get("state_vector", []), dtype=np.float64)
        s_after = np.asarray(snap_after.get("state_vector", []), dtype=np.float64)

        if s_before.size == 0 or s_after.size == 0:
            continue

        delta = s_after - s_before
        l2_delta = float(np.linalg.norm(delta))
        norm_before = float(np.linalg.norm(s_before))
        norm_after = float(np.linalg.norm(s_after))

        base_norm = 0.5 * (norm_before + norm_after)
        chg_mag = float(l2_delta / base_norm) if base_norm > 1e-12 else l2_delta

        # Unit-level shifts
        affected_units = int(np.sum(np.abs(delta) > 1e-4))

        # Memory-level shifts
        affected_memories: List[Dict[str, Any]] = []
        for mem in memories:
            m_id = mem["memory_id"]
            prof = strengths_map.get(m_id)
            if not prof:
                continue

            str_before = prof.timeline_strengths[step_before] if step_before < len(prof.timeline_strengths) else 0.0
            str_after = prof.timeline_strengths[step_after] if step_after < len(prof.timeline_strengths) else 0.0
            m_delta = str_after - str_before

            if abs(m_delta) > 0.01:
                affected_memories.append({
                    "memory_id": m_id,
                    "concept_label": mem["concept_label"],
                    "strength_before": str_before,
                    "strength_after": str_after,
                    "strength_delta": m_delta,
                    "direction": "strengthened" if m_delta > 0 else "weakened",
                })

        impacts.append(
            EventImpact(
                event_id=ev_id,
                timestep=idx,
                change_magnitude=chg_mag,
                affected_memories=affected_memories,
                affected_units_count=affected_units,
                state_norm_before=norm_before,
                state_norm_after=norm_after,
            )
        )

    return impacts
