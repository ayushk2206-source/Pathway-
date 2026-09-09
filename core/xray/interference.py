"""Memory interference detection (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from .models import InterferenceRecord
from .strength import _extract_memory_cues, compute_memory_strengths


def detect_interference(experiment: Experiment) -> List[InterferenceRecord]:
    """Detect competing memories whose vector overlap induces measurable degradation.

    Note: Grounded in circular convolution cross-talk arithmetic in superposition;
    avoids biological claims.
    """
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    records: List[InterferenceRecord] = []

    for i, m_a in enumerate(memories):
        prof_a = strengths_map.get(m_a["memory_id"])
        if not prof_a:
            continue

        for j, m_b in enumerate(memories):
            if i == j:
                continue

            prof_b = strengths_map.get(m_b["memory_id"])
            if not prof_b:
                continue

            # Cue overlap in address space
            overlap = float(cosine(m_a["key_vector"], m_b["key_vector"]))

            # Check if write of B negatively affected A
            b_step = m_b["timestep"] + 1
            affected_steps: List[int] = []
            max_drop = 0.0

            if b_step > m_a["timestep"] + 1 and b_step < len(prof_a.timeline_strengths):
                s_before = prof_a.timeline_strengths[b_step - 1]
                s_after = prof_a.timeline_strengths[b_step]
                drop = s_before - s_after
                if drop > 0.01:
                    max_drop = drop
                    affected_steps.append(b_step)

            # Or if overlap is high (> 0.2) and final strength was degraded
            if (overlap > 0.15 and max_drop > 0.02) or (overlap > 0.35 and prof_a.final_strength < prof_a.peak_strength - 0.05):
                score = float(max(0.0, overlap * (max_drop if max_drop > 0 else (prof_a.peak_strength - prof_a.final_strength))))
                if not affected_steps:
                    affected_steps = [b_step] if b_step < len(prof_a.timeline_strengths) else [len(prof_a.timeline_strengths) - 1]

                records.append(
                    InterferenceRecord(
                        memory_a=m_a["memory_id"],
                        memory_b=m_b["memory_id"],
                        overlap=overlap,
                        interference_score=score,
                        affected_steps=affected_steps,
                        evidence_notes=(
                            f"Memory '{m_b['concept_label']}' shares {overlap:.3f} cosine cue overlap with "
                            f"'{m_a['concept_label']}', resulting in empirical readout degradation."
                        ),
                    )
                )

    # Sort by interference score descending
    records.sort(key=lambda r: r.interference_score, reverse=True)
    return records
