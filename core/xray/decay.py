"""Memory decay and persistence curve analysis (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from .strength import compute_memory_strengths
from .types import DecayPattern


def analyze_decay_curves(experiment: Experiment) -> Dict[str, Any]:
    """Empirically characterize persistence and decay curves across all memories."""
    strengths_map = compute_memory_strengths(experiment)
    snapshots = experiment.snapshots
    timesteps = [int(s.get("timestep", i)) for i, s in enumerate(snapshots)]

    curves: List[Dict[str, Any]] = []
    pattern_counts: Dict[str, int] = {p.value: 0 for p in DecayPattern}

    for m_id, prof in strengths_map.items():
        pattern_counts[prof.pattern.value] += 1
        curves.append({
            "memory_id": m_id,
            "concept_label": prof.concept_label,
            "pattern": prof.pattern.value,
            "initial_strength": prof.initial_strength,
            "peak_strength": prof.peak_strength,
            "final_strength": prof.final_strength,
            "decay_rate": prof.decay_rate,
            "curve": [
                {"timestep": t, "strength": s}
                for t, s in zip(timesteps, prof.timeline_strengths)
            ],
        })

    # Summary statistics
    all_final = [c["final_strength"] for c in curves]
    all_decay_rates = [c["decay_rate"] for c in curves if c["decay_rate"] is not None]

    return {
        "experiment_id": experiment.experiment_id,
        "curves": curves,
        "pattern_distribution": pattern_counts,
        "mean_final_strength": float(np.mean(all_final)) if all_final else 0.0,
        "mean_observed_decay_rate": float(np.mean(all_decay_rates)) if all_decay_rates else 0.0,
        "most_persistent_memory": max(curves, key=lambda c: c["final_strength"])["memory_id"] if curves else None,
        "least_persistent_memory": min(curves, key=lambda c: c["final_strength"])["memory_id"] if curves else None,
    }
