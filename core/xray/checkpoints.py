"""Checkpoint access and reproducible state retrieval (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np

from core import Experiment
from .activation import compute_activation_profile


def get_state_checkpoint(
    experiment: Experiment,
    timeline_step: int,
) -> Dict[str, Any]:
    """Retrieve verified memory state snapshot and activation profile at a given timeline step."""
    snapshots = experiment.snapshots
    if timeline_step < 0 or timeline_step >= len(snapshots):
        raise IndexError(
            f"Checkpoint step {timeline_step} out of bounds (0 to {len(snapshots)-1})"
        )

    snap = snapshots[timeline_step]
    vec_raw = snap.get("state_vector", [])
    vec = np.asarray(vec_raw, dtype=np.float64)

    act_prof = compute_activation_profile(vec, step=timeline_step)

    # Event info at or immediately preceding this step
    ev = None
    if timeline_step > 0 and timeline_step - 1 < len(experiment.events):
        ev = experiment.events[timeline_step - 1]

    return {
        "experiment_id": experiment.experiment_id,
        "timeline_step": timeline_step,
        "event_id": snap.get("event_id"),
        "event_details": ev,
        "state_norm": float(np.linalg.norm(vec)),
        "state_vector": vec.tolist(),
        "active_units": [int(i) for i in np.where(np.abs(vec) > 1e-9)[0]],
        "activation_profile": act_prof.to_dict(),
        "trace": snap.get("trace", {}),
        "queries_at_step": snap.get("query_results", []),
    }
