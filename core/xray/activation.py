"""Memory activation profiling across state dimensions (Phase 05)."""

from __future__ import annotations

from typing import Sequence, Union
import numpy as np

from .models import ActivationProfile


def compute_activation_profile(
    state_vector: Union[Sequence[float], np.ndarray],
    step: int = 0,
    threshold: float = 1e-9,
) -> ActivationProfile:
    """Measure empirical activation properties of the memory state vector at a step.

    Does NOT assume a fixed sparsity level; measures the actual distribution.
    """
    v = np.asarray(state_vector, dtype=np.float64).reshape(-1)
    total = v.size
    if total == 0:
        return ActivationProfile(
            step=step,
            active_units_count=0,
            total_units=0,
            mean_activation=0.0,
            max_activation=0.0,
            min_activation=0.0,
            std_activation=0.0,
            sparsity_ratio=0.0,
            activation_entropy=0.0,
            distribution_quantiles={"p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0},
        )

    abs_v = np.abs(v)
    active_mask = abs_v > threshold
    active_count = int(np.sum(active_mask))
    sparsity_ratio = float(active_count / total)

    mean_val = float(np.mean(abs_v))
    max_val = float(np.max(abs_v))
    min_val = float(np.min(abs_v))
    std_val = float(np.std(abs_v))

    # Quantiles over absolute activation
    p25, p50, p75, p90 = np.percentile(abs_v, [25, 50, 75, 90])

    # Activation entropy over normalized energy distribution
    sum_abs = float(np.sum(abs_v))
    if sum_abs > 1e-12:
        probs = abs_v / sum_abs
        nonzero_p = probs[probs > 1e-12]
        entropy = float(-np.sum(nonzero_p * np.log2(nonzero_p)))
        # Normalize entropy by max possible log2(total)
        max_entropy = float(np.log2(total)) if total > 1 else 1.0
        normalized_entropy = float(entropy / max_entropy) if max_entropy > 0 else 0.0
    else:
        normalized_entropy = 0.0

    return ActivationProfile(
        step=step,
        active_units_count=active_count,
        total_units=total,
        mean_activation=mean_val,
        max_activation=max_val,
        min_activation=min_val,
        std_activation=std_val,
        sparsity_ratio=sparsity_ratio,
        activation_entropy=normalized_entropy,
        distribution_quantiles={
            "p25": float(p25),
            "p50": float(p50),
            "p75": float(p75),
            "p90": float(p90),
        },
    )
