"""Tests for statistical, relationship, and non-linear pattern analysis (Phase 03)."""

import pytest
import numpy as np

from core.lab.analysis import (
    aggregate_metric_samples,
    analyze_sweep_relationship,
    cohens_d,
    detect_nonlinear_patterns,
    pearson_correlation,
    spearman_correlation,
)


def test_aggregate_metric_samples():
    # 1 sample
    s1 = aggregate_metric_samples([0.8])
    assert s1["mean"] == 0.8
    assert s1["sample_size"] == 1
    assert s1["std"] == 0.0

    # Multiple samples
    samples = [0.8, 0.82, 0.85, 0.79, 0.84]
    s_multi = aggregate_metric_samples(samples)
    assert s_multi["sample_size"] == 5
    assert s_multi["min"] == 0.79
    assert s_multi["max"] == 0.85
    assert s_multi["ci_lower"] < s_multi["mean"] < s_multi["ci_upper"]


def test_correlations():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pos = [2.0, 4.0, 6.0, 8.0, 10.0]
    y_neg = [10.0, 8.0, 6.0, 4.0, 2.0]

    assert pearson_correlation(x, y_pos) == pytest.approx(1.0)
    assert spearman_correlation(x, y_pos) == pytest.approx(1.0)

    assert pearson_correlation(x, y_neg) == pytest.approx(-1.0)
    assert spearman_correlation(x, y_neg) == pytest.approx(-1.0)


def test_cohens_d_effect_size():
    base = [0.1, 0.12, 0.11]
    treat = [0.8, 0.85, 0.82]

    d = cohens_d(base, treat)
    assert d is not None
    assert d > 5.0, "Large separation should yield large Cohen's d effect size"


def test_analyze_sweep_relationship_cautious_summary():
    x = [0.1, 0.3, 0.5, 0.7, 0.9]
    y = [0.15, 0.32, 0.51, 0.68, 0.89]

    res = analyze_sweep_relationship(x, y, x_name="similarity", y_name="interference")

    assert res["trend"] == "strongly_increasing"
    assert res["is_monotonic"] is True
    assert res["pearson_r"] > 0.95
    # Scientific honesty check: must not claim direct universal causality
    assert "does not assert a biological causal law" in res["scientific_summary"] or "simulation dynamics" in res["scientific_summary"]


def test_nonlinear_pattern_detection_peak():
    # Inverted-U: rises then falls
    x = [0.0, 0.25, 0.5, 0.75, 1.0]
    y = [0.2, 0.6, 0.9, 0.55, 0.15]

    pat = detect_nonlinear_patterns(x, y)
    assert pat["pattern"] == "peak"
    assert pat["confidence"] >= 0.8
    assert pat["approximate_region"] is not None


def test_nonlinear_pattern_detection_valley():
    # U-shaped: falls then rises
    x = [0.0, 0.25, 0.5, 0.75, 1.0]
    y = [0.9, 0.4, 0.1, 0.45, 0.88]

    pat = detect_nonlinear_patterns(x, y)
    assert pat["pattern"] == "valley"
    assert pat["confidence"] >= 0.8


def test_nonlinear_pattern_detection_threshold():
    # Sharp jump between index 2 and 3
    x = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    y = [0.1, 0.11, 0.12, 0.85, 0.87, 0.89]

    pat = detect_nonlinear_patterns(x, y)
    assert pat["pattern"] == "threshold"
    assert pat["approximate_region"] == [0.3, 0.4]


def test_nonlinear_pattern_detection_plateau():
    # Rises then flatlines
    x = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    y = [0.1, 0.4, 0.7, 0.701, 0.702, 0.699, 0.701]

    pat = detect_nonlinear_patterns(x, y)
    assert pat["pattern"] == "plateau"
