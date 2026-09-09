"""Structured memory explanation object builder (Phase 05)."""

from __future__ import annotations

from typing import Optional
from core import Experiment
from .importance import compute_memory_importance
from .interference import detect_interference
from .models import MemoryExplanation
from .strength import _extract_memory_cues, compute_memory_strengths
from .trace import get_memory_trace


def build_memory_explanation(experiment: Experiment, memory_id: str) -> Optional[MemoryExplanation]:
    """Compile structured, empirical evidence explaining a memory's state without LLM generation."""
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    importance_map = compute_memory_importance(experiment)
    interference_records = detect_interference(experiment)
    trace = get_memory_trace(experiment, memory_id)

    target_mem = next((m for m in memories if m["memory_id"] == memory_id), None)
    if not target_mem or not trace:
        return None

    prof = strengths_map.get(memory_id)
    imp = importance_map.get(memory_id)

    # Number of competing memories that interfere with this one
    competing_count = len([
        ir for ir in interference_records
        if ir.memory_a == memory_id or ir.memory_b == memory_id
    ])

    # Find step with peak strength
    peak_step = trace.encoded_timestep
    if prof and prof.timeline_strengths:
        peak_step = prof.timeline_strengths.index(prof.peak_strength)

    # Concise factual history summary
    history_bullets = [
        f"Encoded at timeline step t={trace.encoded_timestep} as '{target_mem['concept_label']}' -> '{target_mem.get('attribute_label')}'.",
        f"Peak readout strength of {prof.peak_strength:.3f} observed at step t={peak_step}." if prof else "",
        f"Experienced {prof.reinforcement_count} reinforcing writes across experiment." if prof else "",
        f"Subjected to interference from {competing_count} competing memory representation(s)." if competing_count else "Zero direct interference detected.",
        f"Final state retention strength measured at {prof.final_strength:.3f} (pattern: {prof.pattern.value})." if prof else "",
    ]
    history_clean = [b for b in history_bullets if b]

    return MemoryExplanation(
        memory_id=memory_id,
        label=target_mem["concept_label"],
        encoded_at=trace.encoded_timestep,
        reinforcement_count=prof.reinforcement_count if prof else 0,
        strongest_representation_step=peak_step,
        peak_strength=prof.peak_strength if prof else 0.0,
        final_strength=prof.final_strength if prof else 0.0,
        competing_memory_count=competing_count,
        counterfactual_contribution=imp.counterfactual_contribution if imp else 0.0,
        lifecycle_history=history_clean,
    )
