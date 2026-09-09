"""Memory lifecycle trace through experiment history (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core import Experiment
from .models import MemoryTrace
from .strength import _extract_memory_cues, compute_memory_strengths
from .types import MemoryLifecycleStage


def get_memory_trace(experiment: Experiment, memory_id: str) -> Optional[MemoryTrace]:
    """Reconstruct the empirical chronological lifecycle of a single memory item."""
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)

    target_mem = next((m for m in memories if m["memory_id"] == memory_id), None)
    if not target_mem:
        return None

    c_label = target_mem["concept_label"]
    enc_timestep = target_mem["timestep"]
    prof = strengths_map.get(memory_id)
    strengths = prof.timeline_strengths if prof else []

    stages: List[Dict[str, Any]] = []

    # 1. Encoding event
    enc_step = enc_timestep + 1
    init_s = strengths[enc_step] if enc_step < len(strengths) else 0.0
    stages.append({
        "step": enc_step,
        "stage": MemoryLifecycleStage.ENCODED.value,
        "event_id": target_mem["memory_id"],
        "strength": init_s,
        "description": f"Initial encoding of concept '{c_label}' bound to '{target_mem['attribute_label']}'.",
    })

    current_stage = MemoryLifecycleStage.ENCODED

    # Iterate through remaining timeline steps
    for idx, ev in enumerate(experiment.events):
        step_idx = idx + 1
        if step_idx <= enc_step or step_idx >= len(strengths):
            continue

        ev_id = ev.get("id") or f"e{idx:04d}"
        ev_concept = ev.get("concept_label")
        s_prev = strengths[step_idx - 1]
        s_curr = strengths[step_idx]

        # Check for query retrieval at this step
        snap = experiment.snapshots[step_idx] if step_idx < len(experiment.snapshots) else {}
        queried = any(
            qr.get("object_label") == c_label
            for qr in snap.get("query_results", [])
        )

        if queried:
            current_stage = MemoryLifecycleStage.RECALLED
            stages.append({
                "step": step_idx,
                "stage": MemoryLifecycleStage.RECALLED.value,
                "event_id": ev_id,
                "strength": s_curr,
                "description": f"Query probe executed for concept '{c_label}'. Readout verified.",
            })
        elif ev_concept == c_label and s_curr > s_prev + 0.02:
            current_stage = MemoryLifecycleStage.REINFORCED
            stages.append({
                "step": step_idx,
                "stage": MemoryLifecycleStage.REINFORCED.value,
                "event_id": ev_id,
                "strength": s_curr,
                "description": f"Reinforcing write observed; strength increased from {s_prev:.3f} to {s_curr:.3f}.",
            })
        elif s_prev - s_curr > 0.08:
            # Drop in strength
            if s_curr < 0.15:
                current_stage = MemoryLifecycleStage.FADED
                stages.append({
                    "step": step_idx,
                    "stage": MemoryLifecycleStage.FADED.value,
                    "event_id": ev_id,
                    "strength": s_curr,
                    "description": f"Memory representation faded below significance threshold (strength={s_curr:.3f}).",
                })
            else:
                current_stage = MemoryLifecycleStage.WEAKENED
                stages.append({
                    "step": step_idx,
                    "stage": MemoryLifecycleStage.WEAKENED.value,
                    "event_id": ev_id,
                    "strength": s_curr,
                    "description": f"Memory weakened by write of event '{ev_id}' (strength dropped by {s_prev - s_curr:.3f}).",
                })

    final_s = strengths[-1] if strengths else init_s

    return MemoryTrace(
        memory_id=memory_id,
        concept_label=c_label,
        encoded_timestep=enc_step,
        stages=stages,
        final_stage=current_stage,
        final_strength=final_s,
    )
