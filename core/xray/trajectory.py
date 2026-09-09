"""State trajectory extraction across experiment timeline (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core import Experiment
from .models import StateTrajectory


def get_state_trajectory(experiment: Experiment) -> StateTrajectory:
    """Extract chronological state trajectory from an experiment."""
    steps: List[int] = []
    event_ids: List[Optional[str]] = []
    state_norms: List[float] = []
    state_vectors: List[List[float]] = []
    metrics: List[Dict[str, float]] = []

    # Map queries and metrics by timestep if present
    for s_idx, snap in enumerate(experiment.snapshots):
        step = int(snap.get("timestep", s_idx))
        ev_id = snap.get("event_id")
        vec = snap.get("state_vector", [])
        norm = float(snap.get("norm", np.linalg.norm(vec) if vec else 0.0))

        # Query metrics available at this snapshot
        step_metrics: Dict[str, float] = {}
        for qr in snap.get("query_results", []):
            if "confidence" in qr:
                step_metrics["confidence"] = float(qr["confidence"])
            if "quality" in qr:
                step_metrics["quality"] = float(qr["quality"])
            if "correctness" in qr:
                step_metrics["correctness"] = 1.0 if qr["correctness"] else 0.0

        if not step_metrics and s_idx == len(experiment.snapshots) - 1:
            # Include final experiment scalar metrics at last step
            for k, v in experiment.metrics.items():
                if isinstance(v, (int, float)) and not np.isnan(v):
                    step_metrics[k] = float(v)

        steps.append(step)
        event_ids.append(ev_id)
        state_norms.append(norm)
        state_vectors.append(vec)
        metrics.append(step_metrics)

    return StateTrajectory(
        experiment_id=experiment.experiment_id,
        steps=steps,
        event_ids=event_ids,
        state_norms=state_norms,
        state_vectors=state_vectors,
        metrics=metrics,
        total_steps=len(steps),
    )
