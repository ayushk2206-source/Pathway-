"""Tests for Experiment Lab controlled runner, sweeps, and multi-trials (Phase 03)."""

import pytest
import numpy as np

from core.lab.runner import (
    derive_trial_seed,
    reproduce_lab_experiment,
    run_condition_trials,
    run_controlled_comparison,
    run_grid_sweep,
    run_parameter_sweep,
)


def test_deterministic_seed_derivation():
    s1 = derive_trial_seed(42, 0)
    s2 = derive_trial_seed(42, 0)
    s3 = derive_trial_seed(42, 1)

    assert s1 == s2, "Derived trial seed must be identical for identical inputs"
    assert s1 != s3, "Different trial indices must produce distinct seeds"
    assert 0 <= s1 <= 2_147_483_647


def test_parameter_sweep_real_computation():
    values = [0.1, 0.5, 0.9]
    base_cfg = {"state_dim": 64, "mechanism": "leaky", "decay": 0.3}

    res = run_parameter_sweep(
        parameter="update_strength",
        values=values,
        base_config=base_cfg,
        trials=1,
        seed=10,
    )

    assert res.parameter == "update_strength"
    assert len(res.conditions) == 3

    # Verify real metrics differ as update_strength changes
    mags = [c.aggregated_metrics["update_magnitude"]["mean"] for c in res.conditions]
    assert mags[0] < mags[1] < mags[2], "Higher update_strength must produce larger update magnitude"

    # Verify relationship analysis was performed
    assert "update_magnitude" in res.relationship_analysis or "memory_retention" in res.relationship_analysis


def test_controlled_variable_isolation():
    """Verify that changing independent variable affects only targeted knob, leaving controls unchanged."""
    base_cfg = {
        "mechanism": "baseline",
        "state_dim": 64,
        "update_strength": 1.0,
        "n_conflicts": 1,
    }

    sweep = run_parameter_sweep("memory_similarity", [0.0, 0.8], base_config=base_cfg, seed=5)

    c0 = sweep.conditions[0]
    c1 = sweep.conditions[1]

    # Independent variable differed
    assert c0.parameter_values["memory_similarity"] == 0.0
    assert c1.parameter_values["memory_similarity"] == 0.8

    # Controlled variables remained strictly invariant
    assert c0.parameter_values["state_dim"] == c1.parameter_values["state_dim"] == 64
    assert c0.parameter_values["mechanism"] == c1.parameter_values["mechanism"] == "baseline"
    assert c0.parameter_values["update_strength"] == c1.parameter_values["update_strength"] == 1.0


def test_grid_sweep_2d():
    xs = [0.0, 0.5]
    ys = [0.2, 0.8]
    base_cfg = {"state_dim": 64, "mechanism": "interference"}

    grid = run_grid_sweep(
        param_x="memory_similarity",
        values_x=xs,
        param_y="update_strength",
        values_y=ys,
        base_config=base_cfg,
        seed=15,
    )

    assert grid.param_x == "memory_similarity"
    assert grid.param_y == "update_strength"
    assert len(grid.cells) == 4

    # Matrix metrics shape check: 2 rows (ys) x 2 cols (xs)
    assert "memory_retention" in grid.matrix_metrics
    mat = grid.matrix_metrics["memory_retention"]
    assert len(mat) == 2
    assert len(mat[0]) == 2
    assert all(val is not None for row in mat for val in row)


def test_controlled_comparison_baseline_vs_treatment():
    baseline = {"mechanism": "baseline", "state_dim": 64, "update_strength": 0.2}
    treatment = {"mechanism": "baseline", "state_dim": 64, "update_strength": 1.0}

    comp = run_controlled_comparison(baseline, treatment, seed=20)

    assert "update_strength" in comp.differing_variables
    assert comp.differing_variables["update_strength"]["baseline"] == 0.2
    assert comp.differing_variables["update_strength"]["treatment"] == 1.0

    # Metric deltas exist and reflect change
    assert "update_magnitude" in comp.metric_deltas
    assert comp.metric_deltas["update_magnitude"] > 0
    assert comp.state_difference is not None


def test_repeated_trials_statistics():
    cond_params = {"mechanism": "leaky", "state_dim": 64, "input_noise": 0.2}

    res = run_condition_trials("noisy_test", cond_params, master_seed=42, trials=5)

    assert len(res.trials) == 5
    # Seeds must be distinct across trials
    seeds = [t.seed for t in res.trials]
    assert len(set(seeds)) == 5

    # Check statistical aggregation
    stat = res.aggregated_metrics["recall_accuracy"]
    assert "mean" in stat
    assert "median" in stat
    assert "std" in stat
    assert "ci_lower" in stat
    assert "ci_upper" in stat
    assert stat["sample_size"] == 5
    assert stat["min"] <= stat["mean"] <= stat["max"]


def test_reproduce_lab_experiment():
    cfg = {"mechanism": "leaky", "state_dim": 64, "decay": 0.2, "n_conflicts": 1}

    # Initial execution
    res1 = run_condition_trials("initial", cfg, master_seed=77, trials=1)
    metrics1 = {k: v["mean"] for k, v in res1.aggregated_metrics.items()}

    # Reproduce
    repro = reproduce_lab_experiment(cfg, expected_metrics=metrics1, seed=77, trials=1)

    assert repro["reproduced"] is True
    assert repro["exact_match"] is True
    for mk, match_data in repro["metric_matches"].items():
        assert match_data["matched"] is True
        assert match_data["difference"] == pytest.approx(0.0, abs=1e-9)
