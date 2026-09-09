"""Statistical, relationship, and non-linear pattern analysis for Experiment Lab (Phase 03).

Provides rigorous statistical aggregation across trials, correlation and regression
analysis, and data-driven detection of non-linear behavior (plateaus, thresholds,
peaks, valleys, and phase transitions) without hardcoded results.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Critical t-values for 95% two-tailed confidence intervals (df = N - 1)
_STUDENT_T_95: Dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    15: 2.131,
    20: 2.086,
    30: 2.042,
    50: 2.009,
    100: 1.984,
}


def _get_t_critical_95(df: int) -> float:
    if df <= 0:
        return 1.96
    if df in _STUDENT_T_95:
        return _STUDENT_T_95[df]
    # Interpolation / approximation for df > 0
    sorted_dfs = sorted(_STUDENT_T_95.keys())
    for s_df in sorted_dfs:
        if df <= s_df:
            return _STUDENT_T_95[s_df]
    return 1.96


def aggregate_metric_samples(samples: Sequence[float]) -> Dict[str, float]:
    """Calculate mean, median, std, min, max, and 95% CI from sample observations."""
    arr = np.asarray(samples, dtype=np.float64)
    n = arr.size
    if n == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "sample_size": 0,
        }

    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    if n == 1:
        return {
            "mean": mean_val,
            "median": median_val,
            "std": 0.0,
            "min": min_val,
            "max": max_val,
            "ci_lower": mean_val,
            "ci_upper": mean_val,
            "sample_size": 1,
        }

    std_val = float(np.std(arr, ddof=1))  # sample standard deviation
    se = std_val / math.sqrt(n)
    t_crit = _get_t_critical_95(n - 1)
    margin = t_crit * se

    return {
        "mean": mean_val,
        "median": median_val,
        "std": std_val,
        "min": min_val,
        "max": max_val,
        "ci_lower": mean_val - margin,
        "ci_upper": mean_val + margin,
        "sample_size": n,
    }


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Calculate Pearson correlation r between x and y."""
    xa, ya = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if xa.size != ya.size or xa.size < 2:
        return None
    std_x, std_y = np.std(xa), np.std(ya)
    if std_x < 1e-12 or std_y < 1e-12:
        return 0.0  # zero variance
    r = float(np.corrcoef(xa, ya)[0, 1])
    return r if not np.isnan(r) else 0.0


def spearman_correlation(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Calculate Spearman rank correlation rho between x and y."""
    xa, ya = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if xa.size != ya.size or xa.size < 2:
        return None

    def _rank(arr: np.ndarray) -> np.ndarray:
        temp = arr.argsort()
        ranks = np.empty_like(temp, dtype=float)
        ranks[temp] = np.arange(len(arr))
        return ranks

    rx, ry = _rank(xa), _rank(ya)
    return pearson_correlation(rx, ry)


def cohens_d(group1: Sequence[float], group2: Sequence[float]) -> Optional[float]:
    """Calculate Cohen's d effect size between treatment and baseline."""
    g1, g2 = np.asarray(group1, dtype=np.float64), np.asarray(group2, dtype=np.float64)
    n1, n2 = g1.size, g2.size
    if n1 == 0 or n2 == 0:
        return None
    if n1 == 1 and n2 == 1:
        diff = float(g2[0] - g1[0])
        return diff if abs(diff) > 1e-12 else 0.0

    s1 = np.var(g1, ddof=1) if n1 > 1 else 0.0
    s2 = np.var(g2, ddof=1) if n2 > 1 else 0.0
    pooled_var = (((n1 - 1) * s1) + ((n2 - 1) * s2)) / max(1, (n1 + n2 - 2))
    s_pooled = math.sqrt(pooled_var) if pooled_var > 1e-12 else 1e-6
    return float((np.mean(g2) - np.mean(g1)) / s_pooled)


def analyze_sweep_relationship(
    x_values: Sequence[float],
    y_values: Sequence[float],
    x_name: str = "x",
    y_name: str = "y",
) -> Dict[str, Any]:
    """Perform numerical relationship analysis on sweep curves."""
    xa = np.asarray(x_values, dtype=np.float64)
    ya = np.asarray(y_values, dtype=np.float64)
    n = xa.size

    if n < 2:
        return {
            "data_points": n,
            "pearson_r": None,
            "spearman_rho": None,
            "slope": None,
            "r_squared": None,
            "trend": "insufficient_data",
            "is_monotonic": True,
            "scientific_summary": "Insufficient data points to determine empirical relationship.",
        }

    r = pearson_correlation(xa, ya)
    rho = spearman_correlation(xa, ya)

    # Linear fit
    std_x = np.std(xa)
    if std_x > 1e-12:
        slope, intercept = np.polyfit(xa, ya, 1)
        y_pred = slope * xa + intercept
        ss_res = np.sum((ya - y_pred) ** 2)
        ss_tot = np.sum((ya - np.mean(ya)) ** 2)
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 1.0
        slope = float(slope)
    else:
        slope, r2 = 0.0, 0.0

    # Monotonicity
    diffs = np.diff(ya)
    non_zero = diffs[np.abs(diffs) > 1e-6]
    is_mono_inc = bool(np.all(non_zero >= 0)) if non_zero.size else True
    is_mono_dec = bool(np.all(non_zero <= 0)) if non_zero.size else True
    is_monotonic = is_mono_inc or is_mono_dec

    # Trend label
    if abs(slope) < 1e-4:
        trend = "invariant"
    elif r is not None and r > 0.7:
        trend = "strongly_increasing"
    elif r is not None and r > 0.3:
        trend = "moderately_increasing"
    elif r is not None and r < -0.7:
        trend = "strongly_decreasing"
    elif r is not None and r < -0.3:
        trend = "moderately_decreasing"
    elif not is_monotonic:
        trend = "non_monotonic"
    else:
        trend = "flat"

    # Scientific summary
    desc_parts = []
    if trend == "invariant":
        desc_parts.append(f"Observed '{y_name}' remained largely invariant across the swept range of '{x_name}'.")
    elif "increasing" in trend:
        desc_parts.append(
            f"Observed '{y_name}' increased with '{x_name}' (Pearson r={r:.3f}, Spearman rho={rho:.3f}, slope={slope:.3f})."
        )
    elif "decreasing" in trend:
        desc_parts.append(
            f"Observed '{y_name}' decreased as '{x_name}' increased (Pearson r={r:.3f}, Spearman rho={rho:.3f}, slope={slope:.3f})."
        )
    else:
        desc_parts.append(f"Observed '{y_name}' exhibited a non-monotonic response to '{x_name}' (Spearman rho={rho:.3f}).")

    if not is_monotonic:
        desc_parts.append("The response curve changes direction over the observed parameter interval.")
    desc_parts.append("Note: This observed statistical association reflects computational simulation dynamics under the specified controls.")

    return {
        "data_points": n,
        "pearson_r": r,
        "spearman_rho": rho,
        "slope": slope,
        "r_squared": max(0.0, r2),
        "trend": trend,
        "is_monotonic": is_monotonic,
        "scientific_summary": " ".join(desc_parts),
    }


def detect_nonlinear_patterns(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> Dict[str, Any]:
    """Detect non-linear characteristics: plateau, threshold, peak, valley, or oscillating."""
    xa = np.asarray(x_values, dtype=np.float64)
    ya = np.asarray(y_values, dtype=np.float64)
    n = xa.size

    if n < 4:
        return {
            "pattern": "linear_or_insufficient_points",
            "approximate_region": None,
            "confidence": 0.5,
            "details": "At least 4 points required for non-linear pattern characterization",
        }

    diffs = np.diff(ya)
    dx = np.diff(xa)
    gradients = diffs / np.where(np.abs(dx) > 1e-12, dx, 1e-6)

    # 1. Peak (Inverted-U)
    max_idx = int(np.argmax(ya))
    if 0 < max_idx < n - 1:
        left_rising = np.all(ya[:max_idx] <= ya[max_idx])
        right_falling = np.all(ya[max_idx:] <= ya[max_idx])
        prominence = ya[max_idx] - max(ya[0], ya[-1])
        if left_rising and right_falling and prominence > 0.05:
            return {
                "pattern": "peak",
                "approximate_region": [float(xa[max_idx - 1]), float(xa[max_idx + 1])],
                "confidence": 0.9,
                "details": f"Inverted-U peak localized at {xa[max_idx]:.3f} with maximum metric value {ya[max_idx]:.3f}",
            }

    # 2. Valley (U-shaped)
    min_idx = int(np.argmin(ya))
    if 0 < min_idx < n - 1:
        left_falling = np.all(ya[:min_idx] >= ya[min_idx])
        right_rising = np.all(ya[min_idx:] >= ya[min_idx])
        depth = min(ya[0], ya[-1]) - ya[min_idx]
        if left_falling and right_rising and depth > 0.05:
            return {
                "pattern": "valley",
                "approximate_region": [float(xa[min_idx - 1]), float(xa[min_idx + 1])],
                "confidence": 0.9,
                "details": f"U-shaped minimum localized at {xa[min_idx]:.3f} with minimum metric value {ya[min_idx]:.3f}",
            }

    # 3. Threshold / Sharp Transition
    abs_grads = np.abs(gradients)
    median_grad = np.median(abs_grads)
    max_grad_idx = int(np.argmax(abs_grads))
    sorted_abs_grads = np.sort(abs_grads)
    second_grad = sorted_abs_grads[-2] if len(sorted_abs_grads) >= 2 else 0.0

    is_isolated_spike = abs_grads[max_grad_idx] > 2.0 * (second_grad + 1e-6)
    if is_isolated_spike and abs_grads[max_grad_idx] > 2.5 * (median_grad + 1e-6) and (ya.max() - ya.min()) > 0.1:
        return {
            "pattern": "threshold",
            "approximate_region": [float(xa[max_grad_idx]), float(xa[max_grad_idx + 1])],
            "confidence": 0.85,
            "details": f"Steep inflection threshold detected in interval [{xa[max_grad_idx]:.3f}, {xa[max_grad_idx + 1]:.3f}]",
        }

    # 4. Plateau (active change followed by flat tail, or vice versa)
    tail_len = max(3, n // 2)
    tail_var = np.var(ya[-tail_len:])
    head_diff = abs(ya[-tail_len] - ya[0])
    if tail_var < 1e-4 and head_diff > 0.1:
        return {
            "pattern": "plateau",
            "approximate_region": [float(xa[-tail_len]), float(xa[-1])],
            "confidence": 0.8,
            "details": f"Metric saturates into a plateau starting near {xa[-tail_len]:.3f}",
        }

    # 5. Monotonic
    diff_signs = np.sign(diffs[np.abs(diffs) > 1e-5])
    if np.all(diff_signs >= 0):
        return {
            "pattern": "monotonic_increasing",
            "approximate_region": [float(xa[0]), float(xa[-1])],
            "confidence": 0.95,
            "details": "Consistently increases across the parameter space",
        }
    if np.all(diff_signs <= 0):
        return {
            "pattern": "monotonic_decreasing",
            "approximate_region": [float(xa[0]), float(xa[-1])],
            "confidence": 0.95,
            "details": "Consistently decreases across the parameter space",
        }

    # 6. Mixed / Oscillating
    sign_changes = np.count_nonzero(np.diff(diff_signs) != 0)
    if sign_changes >= 2:
        return {
            "pattern": "unstable_region",
            "approximate_region": [float(xa[0]), float(xa[-1])],
            "confidence": 0.75,
            "details": f"Direction fluctuates ({sign_changes} sign flips) indicating competitive non-linear dynamics",
        }

    return {
        "pattern": "mixed",
        "approximate_region": [float(xa[0]), float(xa[-1])],
        "confidence": 0.6,
        "details": "Non-linear response without a singular dominant pattern",
    }
