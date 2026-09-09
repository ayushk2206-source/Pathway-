"""State difference analysis between memory state representations (Phase 05)."""

from __future__ import annotations

from typing import Sequence, Union
import numpy as np

from .models import StateComparison


def compare_states(
    state_a: Union[Sequence[float], np.ndarray],
    state_b: Union[Sequence[float], np.ndarray],
) -> StateComparison:
    """Compare two memory states with mathematically sound distance metrics.

    Calculates:
    - L1 distance (Manhattan / sum of absolute coordinate shifts)
    - L2 distance (Euclidean distance)
    - Cosine distance (1.0 - cosine_similarity)
    - Normalized difference (relative L2 norm)
    """
    a = np.asarray(state_a, dtype=np.float64).reshape(-1)
    b = np.asarray(state_b, dtype=np.float64).reshape(-1)

    if a.size != b.size:
        raise ValueError(f"State dimensions mismatch: {a.size} vs {b.size}")

    dim = a.size
    if dim == 0:
        return StateComparison(
            l1_distance=0.0,
            l2_distance=0.0,
            cosine_distance=0.0,
            normalized_difference=0.0,
            dimension_count=0,
            metrics_summary={},
        )

    delta = a - b
    l1 = float(np.sum(np.abs(delta)))
    l2 = float(np.linalg.norm(delta))

    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))

    denom = norm_a * norm_b
    if denom > 1e-12:
        cos_sim = float(np.dot(a, b) / denom)
        # clamp numerical imprecision
        cos_sim = max(-1.0, min(1.0, cos_sim))
        cos_dist = float(1.0 - cos_sim)
    else:
        # Both near zero or one zero
        cos_dist = 0.0 if (norm_a < 1e-12 and norm_b < 1e-12) else 1.0

    # Normalized difference: relative to average baseline magnitude
    avg_norm = 0.5 * (norm_a + norm_b)
    norm_diff = float(l2 / avg_norm) if avg_norm > 1e-12 else 0.0

    summary = {
        "norm_a": norm_a,
        "norm_b": norm_b,
        "norm_ratio": float(norm_b / norm_a) if norm_a > 1e-12 else (1.0 if norm_b < 1e-12 else float("inf")),
        "max_coordinate_delta": float(np.max(np.abs(delta))),
        "mean_coordinate_delta": float(np.mean(np.abs(delta))),
    }

    return StateComparison(
        l1_distance=l1,
        l2_distance=l2,
        cosine_distance=cos_dist,
        normalized_difference=norm_diff,
        dimension_count=dim,
        metrics_summary=summary,
    )
