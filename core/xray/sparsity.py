"""Substrate sparsity analysis over time (Phase 05)."""

from __future__ import annotations

from typing import Dict, List
import numpy as np

from core import Experiment
from .models import SparsityAnalysis


def analyze_sparsity(experiment: Experiment, threshold: float = 1e-9) -> SparsityAnalysis:
    """Analyze activation sparsity dynamics of the computational memory substrate across time.

    Note: Represents mathematical dimension utilization in simulation; does not assert
    biological equivalence to neural tissue.
    """
    snapshots = experiment.snapshots
    active_per_step: List[int] = []
    ratio_per_step: List[float] = []
    total_units = 0
    all_values: List[float] = []
    has_negative_activations = False

    for snap in snapshots:
        vec_raw = snap.get("state_vector", [])
        vec = np.asarray(vec_raw, dtype=np.float64)
        total_units = max(total_units, vec.size)

        if vec.size > 0:
            if np.any(vec < -1e-9):
                has_negative_activations = True
            all_values.extend(np.abs(vec).tolist())

            active_count = int(np.sum(np.abs(vec) > threshold))
            active_per_step.append(active_count)
            ratio_per_step.append(float(active_count / vec.size))
        else:
            active_per_step.append(0)
            ratio_per_step.append(0.0)

    mean_s = float(np.mean(ratio_per_step)) if ratio_per_step else 0.0
    min_s = float(np.min(ratio_per_step)) if ratio_per_step else 0.0
    max_s = float(np.max(ratio_per_step)) if ratio_per_step else 0.0

    # Sparsity distribution percentiles
    if all_values:
        p25, p50, p75, p95 = np.percentile(all_values, [25, 50, 75, 95])
        dist = {
            "p25": float(p25),
            "median_abs_activation": float(p50),
            "p75": float(p75),
            "p95": float(p95),
        }
    else:
        dist = {"p25": 0.0, "median_abs_activation": 0.0, "p75": 0.0, "p95": 0.0}

    return SparsityAnalysis(
        experiment_id=experiment.experiment_id,
        active_units_per_step=active_per_step,
        total_units=total_units,
        sparsity_ratio_per_step=ratio_per_step,
        mean_sparsity=mean_s,
        min_sparsity=min_s,
        max_sparsity=max_s,
        sparsity_distribution=dist,
        supports_non_negative=not has_negative_activations,
    )
