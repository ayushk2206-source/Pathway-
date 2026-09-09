"""Memory state snapshot generator (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core import Experiment
from core.vectors import cosine
from .models import MemorySnapshot
from .strength import _extract_memory_cues, compute_memory_strengths


def create_memory_snapshots(experiment: Experiment) -> List[MemorySnapshot]:
    """Extract verified MemorySnapshot records from real experiment states."""
    snapshots_data = experiment.snapshots
    strengths_by_mem = compute_memory_strengths(experiment)
    memories = _extract_memory_cues(experiment)

    # Pre-compute pairwise cue similarities for association detection
    pairwise_sims: Dict[str, Dict[str, float]] = {}
    for i, m1 in enumerate(memories):
        pairwise_sims.setdefault(m1["memory_id"], {})
        for j, m2 in enumerate(memories):
            if i != j:
                sim = float(cosine(m1["key_vector"], m2["key_vector"]))
                pairwise_sims[m1["memory_id"]][m2["memory_id"]] = sim

    result: List[MemorySnapshot] = []

    for s_idx, raw_snap in enumerate(snapshots_data):
        step = int(raw_snap.get("timestep", s_idx))
        ev_id = raw_snap.get("event_id")
        vec_raw = raw_snap.get("state_vector", [])
        vec = np.asarray(vec_raw, dtype=np.float64)

        abs_vec = np.abs(vec)
        active_units = [int(i) for i in np.where(abs_vec > 1e-9)[0]]
        inactive_units = [int(i) for i in np.where(abs_vec <= 1e-9)[0]]
        sparsity = float(len(active_units) / vec.size) if vec.size else 0.0

        # Memory strengths at this exact timeline step
        step_strengths: Dict[str, float] = {}
        for m_id, prof in strengths_by_mem.items():
            if s_idx < len(prof.timeline_strengths):
                step_strengths[m_id] = prof.timeline_strengths[s_idx]
            else:
                step_strengths[m_id] = 0.0

        # Active associations (cues with similarity > 0.3)
        associations: Dict[str, List[str]] = {}
        for m_id, sim_map in pairwise_sims.items():
            assoc_targets = [target for target, s in sim_map.items() if s > 0.3]
            associations[m_id] = assoc_targets

        # Similarity statistics across known active memories
        active_sim_values = []
        for sim_map in pairwise_sims.values():
            active_sim_values.extend(sim_map.values())

        if active_sim_values:
            sim_stats = {
                "mean_similarity": float(np.mean(active_sim_values)),
                "max_similarity": float(np.max(active_sim_values)),
                "min_similarity": float(np.min(active_sim_values)),
                "std_similarity": float(np.std(active_sim_values)),
            }
        else:
            sim_stats = {
                "mean_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0,
                "std_similarity": 0.0,
            }

        snapshot_id = f"snap_{experiment.experiment_id}_{step:04d}"
        created_at = experiment.created_at

        result.append(
            MemorySnapshot(
                snapshot_id=snapshot_id,
                experiment_id=experiment.experiment_id,
                timeline_step=step,
                event_id=ev_id,
                timestamp=created_at,
                state_vector=vec.tolist(),
                active_units=active_units,
                inactive_units=inactive_units,
                sparsity=sparsity,
                memory_strength=step_strengths,
                associations=associations,
                similarity_statistics=sim_stats,
                metadata={
                    "mechanism": experiment.mechanism,
                    "norm": float(np.linalg.norm(vec)),
                    "trace": raw_snap.get("trace", {}),
                },
            )
        )

    return result
