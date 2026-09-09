"""Memory strength calculation across timeline (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core import Experiment
from core.events import Event
from core.vectors import cosine, unbind
from .models import MemoryStrengthProfile
from .types import DecayPattern


def _extract_memory_cues(experiment: Experiment) -> List[Dict[str, Any]]:
    """Extract distinct memory items (events with valid key and value vectors)."""
    memories: List[Dict[str, Any]] = []
    seen_ids = set()

    for idx, ev_dict in enumerate(experiment.events):
        ev_id = ev_dict.get("id") or f"e{idx:04d}"
        if ev_id in seen_ids:
            continue
        seen_ids.add(ev_id)

        k_raw = ev_dict.get("key_vector")
        v_raw = ev_dict.get("value_vector")
        if k_raw is None or v_raw is None:
            continue

        memories.append({
            "memory_id": ev_id,
            "concept_label": ev_dict.get("concept_label", f"mem_{idx}"),
            "attribute_label": ev_dict.get("attribute_label", ""),
            "timestep": int(ev_dict.get("timestep", idx)),
            "key_vector": np.asarray(k_raw, dtype=np.float64),
            "value_vector": np.asarray(v_raw, dtype=np.float64),
        })
    return memories


def compute_memory_strengths(experiment: Experiment) -> Dict[str, MemoryStrengthProfile]:
    """Compute representation strength trajectory for each memory item across history."""
    memories = _extract_memory_cues(experiment)
    snapshots = experiment.snapshots
    total_steps = len(snapshots)

    profiles: Dict[str, MemoryStrengthProfile] = {}

    for mem in memories:
        m_id = mem["memory_id"]
        c_label = mem["concept_label"]
        enc_step = mem["timestep"] + 1  # 1-based snapshot timestep
        key = mem["key_vector"]
        val = mem["value_vector"]

        strengths: List[float] = []
        reinforcements = 0

        for s_idx, snap in enumerate(snapshots):
            # Prior to first encoding, strength is zero
            if s_idx < enc_step:
                strengths.append(0.0)
                continue

            state_raw = snap.get("state_vector", [])
            state = np.asarray(state_raw, dtype=np.float64)

            if state.size == 0 or np.linalg.norm(state) < 1e-12:
                strengths.append(0.0)
                continue

            # Unbind memory key from state and measure cosine similarity to true value
            recovered = unbind(state, key)
            sim = cosine(recovered, val)
            s_val = max(0.0, float(sim))
            strengths.append(s_val)

        # Count reinforcements (subsequent writes with the same concept label)
        for idx, ev in enumerate(experiment.events):
            if idx > mem["timestep"] and ev.get("concept_label") == c_label:
                reinforcements += 1

        active_strengths = strengths[enc_step:] if enc_step < len(strengths) else [0.0]
        init_s = active_strengths[0] if active_strengths else 0.0
        peak_s = max(active_strengths) if active_strengths else 0.0
        final_s = active_strengths[-1] if active_strengths else 0.0

        # Decay rate calculation
        peak_idx = strengths.index(peak_s) if peak_s > 0 else enc_step
        decay_rate = None
        if total_steps - 1 > peak_idx and peak_s > 0.0:
            drop = peak_s - final_s
            dt = (total_steps - 1) - peak_idx
            decay_rate = max(0.0, float(drop / dt))

        # Pattern classification
        if reinforcements > 0 and final_s >= init_s - 0.05:
            pattern = DecayPattern.REINFORCED
        elif final_s >= peak_s - 0.08 and final_s > 0.5:
            pattern = DecayPattern.STABLE
        elif len(active_strengths) >= 3 and final_s > min(active_strengths) + 0.15:
            pattern = DecayPattern.RECOVERED
        elif decay_rate is not None and decay_rate > 0.2:
            pattern = DecayPattern.RAPIDLY_LOST
        else:
            pattern = DecayPattern.DECAYING

        profiles[m_id] = MemoryStrengthProfile(
            memory_id=m_id,
            concept_label=c_label,
            initial_strength=init_s,
            peak_strength=peak_s,
            final_strength=final_s,
            timeline_strengths=strengths,
            decay_rate=decay_rate,
            reinforcement_count=reinforcements,
            pattern=pattern,
        )

    return profiles
