"""State divergence and X-Ray trajectory integration (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from .diff import compare_states
from .strength import _extract_memory_cues, compute_memory_strengths
from .trajectory import get_state_trajectory


def trace_divergence_xray(
    original_experiment: Experiment,
    counterfactual_experiment: Experiment,
) -> Dict[str, Any]:
    """Trace state divergence and memory shifts across timelines between original and counterfactual."""
    orig_traj = get_state_trajectory(original_experiment)
    cf_traj = get_state_trajectory(counterfactual_experiment)

    orig_strengths = compute_memory_strengths(original_experiment)
    cf_strengths = compute_memory_strengths(counterfactual_experiment)
    memories = _extract_memory_cues(original_experiment)

    min_steps = min(orig_traj.total_steps, cf_traj.total_steps)
    step_records: List[Dict[str, Any]] = []
    onset_step = None

    for step_idx in range(min_steps):
        s_orig = np.asarray(orig_traj.state_vectors[step_idx], dtype=np.float64)
        s_cf = np.asarray(cf_traj.state_vectors[step_idx], dtype=np.float64)

        comparison = compare_states(s_orig, s_cf)

        if onset_step is None and comparison.l2_distance > 1e-6:
            onset_step = step_idx

        # Affected memories at this step
        affected: List[Dict[str, Any]] = []
        for mem in memories:
            m_id = mem["memory_id"]
            prof_o = orig_strengths.get(m_id)
            prof_c = cf_strengths.get(m_id)

            so = prof_o.timeline_strengths[step_idx] if (prof_o and step_idx < len(prof_o.timeline_strengths)) else 0.0
            sc = prof_c.timeline_strengths[step_idx] if (prof_c and step_idx < len(prof_c.timeline_strengths)) else 0.0
            delta_s = sc - so

            if abs(delta_s) > 0.01:
                affected.append({
                    "memory_id": m_id,
                    "concept_label": mem["concept_label"],
                    "original_strength": so,
                    "counterfactual_strength": sc,
                    "strength_delta": delta_s,
                })

        step_records.append({
            "step": step_idx,
            "original_state_summary": {
                "norm": orig_traj.state_norms[step_idx],
                "active_units": int(np.sum(np.abs(s_orig) > 1e-9)),
            },
            "counterfactual_state_summary": {
                "norm": cf_traj.state_norms[step_idx],
                "active_units": int(np.sum(np.abs(s_cf) > 1e-9)),
            },
            "l2_distance": comparison.l2_distance,
            "cosine_distance": comparison.cosine_distance,
            "relative_l2": comparison.normalized_difference,
            "affected_memories": affected,
        })

    return {
        "original_experiment_id": original_experiment.experiment_id,
        "counterfactual_experiment_id": counterfactual_experiment.experiment_id,
        "divergence_onset_step": onset_step,
        "final_l2_distance": step_records[-1]["l2_distance"] if step_records else 0.0,
        "total_diverging_steps": len([r for r in step_records if r["l2_distance"] > 1e-6]),
        "steps": step_records,
    }
