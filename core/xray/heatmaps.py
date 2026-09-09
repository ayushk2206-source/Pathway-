"""Visualization-ready heatmap matrix generation (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from .strength import _extract_memory_cues, compute_memory_strengths


def generate_heatmap_matrices(experiment: Experiment) -> Dict[str, Any]:
    """Generate clean visualization-ready 2D matrix data for heatmaps:

    1. Time x Memory (steps x memories):
       - strength: retrieval fidelity of each memory at each timestep
       - state_alignment: cosine similarity of memory binding vector with current state
    2. Time x Unit (steps x state dimensions):
       - activation: signed activation values
       - magnitude: absolute activation values
       - change_magnitude: absolute unit-level change from previous step
    """
    snapshots = experiment.snapshots
    num_steps = len(snapshots)
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)

    memory_labels = [m["concept_label"] for m in memories]
    memory_ids = [m["memory_id"] for m in memories]
    num_memories = len(memories)

    # 1. TIME x MEMORY: strength matrix [num_steps, num_memories]
    time_x_memory_strength: List[List[float]] = []
    time_x_memory_alignment: List[List[float]] = []

    for s_idx, snap in enumerate(snapshots):
        state_raw = snap.get("state_vector", [])
        state = np.asarray(state_raw, dtype=np.float64)

        step_strength_row: List[float] = []
        step_align_row: List[float] = []

        for mem in memories:
            m_id = mem["memory_id"]
            prof = strengths_map.get(m_id)
            s_val = prof.timeline_strengths[s_idx] if (prof and s_idx < len(prof.timeline_strengths)) else 0.0
            step_strength_row.append(float(s_val))

            # Cosine alignment with state
            b_vec = np.asarray(mem.get("key_vector", []), dtype=np.float64)
            if state.size > 0 and b_vec.size == state.size and np.linalg.norm(state) > 1e-12:
                cos_val = float(cosine(state, b_vec))
            else:
                cos_val = 0.0
            step_align_row.append(float(cos_val))

        time_x_memory_strength.append(step_strength_row)
        time_x_memory_alignment.append(step_align_row)

    # 2. TIME x UNIT: [num_steps, num_units]
    time_x_unit_activation: List[List[float]] = []
    time_x_unit_magnitude: List[List[float]] = []
    time_x_unit_change: List[List[float]] = []

    prev_state: Optional[np.ndarray] = None
    num_units = 0

    for s_idx, snap in enumerate(snapshots):
        state_raw = snap.get("state_vector", [])
        state = np.asarray(state_raw, dtype=np.float64)
        num_units = max(num_units, state.size)

        act_row = [float(x) for x in state]
        mag_row = [float(abs(x)) for x in state]

        if prev_state is not None and prev_state.size == state.size:
            diff = np.abs(state - prev_state)
            chg_row = [float(x) for x in diff]
        else:
            chg_row = [0.0] * state.size

        time_x_unit_activation.append(act_row)
        time_x_unit_magnitude.append(mag_row)
        time_x_unit_change.append(chg_row)
        prev_state = state

    return {
        "experiment_id": experiment.experiment_id,
        "time_axis": [int(snap.get("timestep", i)) for i, snap in enumerate(snapshots)],
        "memory_axis": {
            "memory_ids": memory_ids,
            "labels": memory_labels,
            "count": num_memories,
        },
        "unit_axis": {
            "unit_indices": list(range(num_units)),
            "count": num_units,
        },
        "time_x_memory": {
            "strength": time_x_memory_strength,
            "state_alignment": time_x_memory_alignment,
        },
        "time_x_unit": {
            "activation": time_x_unit_activation,
            "magnitude": time_x_unit_magnitude,
            "change_magnitude": time_x_unit_change,
        },
    }
