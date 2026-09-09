"""Memory reinforcement detection (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from .models import ReinforcementRecord
from .strength import _extract_memory_cues, compute_memory_strengths


def detect_reinforcement(experiment: Experiment) -> List[ReinforcementRecord]:
    """Detect when existing memories are strengthened by subsequent events."""
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    events = experiment.events
    records: List[ReinforcementRecord] = []

    for mem in memories:
        m_id = mem["memory_id"]
        c_label = mem["concept_label"]
        enc_t = mem["timestep"]
        prof = strengths_map.get(m_id)
        if not prof:
            continue

        reinforcing_event_ids: List[str] = []
        strengths_before: List[float] = []
        strengths_after: List[float] = []

        for idx, ev in enumerate(events):
            if idx <= enc_t:
                continue

            ev_id = ev.get("id") or f"e{idx:04d}"
            ev_concept = ev.get("concept_label")

            # Check if event is related (same concept or high key similarity)
            k_ev = ev.get("key_vector")
            is_related = (ev_concept == c_label)
            if not is_related and k_ev is not None:
                sim = float(cosine(mem["key_vector"], np.asarray(k_ev, dtype=np.float64)))
                if sim > 0.6:
                    is_related = True

            if is_related:
                # Step index in snapshots is idx + 1
                s_idx = idx + 1
                if s_idx < len(prof.timeline_strengths):
                    s_prev = prof.timeline_strengths[s_idx - 1]
                    s_curr = prof.timeline_strengths[s_idx]

                    if s_curr > s_prev + 0.02:  # measurable increase
                        reinforcing_event_ids.append(ev_id)
                        strengths_before.append(s_prev)
                        strengths_after.append(s_curr)

        if reinforcing_event_ids:
            s_init = strengths_before[0]
            s_final = strengths_after[-1]
            net = s_final - s_init
            ratio = float(s_final / s_init) if s_init > 1e-6 else 1.0

            records.append(
                ReinforcementRecord(
                    memory_id=m_id,
                    reinforcement_events=reinforcing_event_ids,
                    strength_before=s_init,
                    strength_after=s_final,
                    net_change=net,
                    strengthening_ratio=ratio,
                )
            )

    return records
