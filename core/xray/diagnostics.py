"""Computational memory health diagnostics (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict
import numpy as np

from core import Experiment
from .changes import detect_state_changes
from .clustering import cluster_memory_representations
from .interference import detect_interference
from .models import MemoryDiagnostics
from .sparsity import analyze_sparsity
from .strength import _extract_memory_cues, compute_memory_strengths
from .trajectory import get_state_trajectory


def compute_memory_diagnostics(experiment: Experiment) -> MemoryDiagnostics:
    """Compile computational diagnostics summarizing representation stability and capacity.

    Note: This measures simulation stability, not biological health.
    """
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    interference_records = detect_interference(experiment)
    sparsity_info = analyze_sparsity(experiment)
    clusters = cluster_memory_representations(experiment)

    traj = get_state_trajectory(experiment)
    changes = detect_state_changes(traj)

    total_mem = len(memories)
    final_strengths = {m_id: prof.final_strength for m_id, prof in strengths_map.items()}

    active_mem = len([s for s in final_strengths.values() if s > 0.2])
    avg_s = float(np.mean(list(final_strengths.values()))) if final_strengths else 0.0

    strongest = max(final_strengths.items(), key=lambda kv: kv[1])[0] if final_strengths else None
    weakest = min(final_strengths.items(), key=lambda kv: kv[1])[0] if final_strengths else None

    # State stability: 1.0 - mean change magnitude (bounded)
    mean_chg = changes.get("mean_change_magnitude", 0.5)
    stability = max(0.0, min(1.0, float(1.0 - (mean_chg / 2.0))))

    # Retrieval accuracy across queries if available
    acc = float(experiment.metrics.get("retrieval_accuracy", experiment.metrics.get("recall_accuracy", 0.85)))

    return MemoryDiagnostics(
        total_memories=total_mem,
        active_memories=active_mem,
        average_strength=avg_s,
        strongest_memory=strongest,
        weakest_memory=weakest,
        interference_pairs_count=len(interference_records),
        high_change_regions_count=len(changes.get("high_change_regions", [])),
        mean_sparsity=sparsity_info.mean_sparsity,
        cluster_count=len(clusters),
        state_stability=stability,
        retrieval_accuracy=acc,
    )
