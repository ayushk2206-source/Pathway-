"""Tests for Experiment Lab Validation and Resource Limits (Phase 03)."""

import pytest

from core.lab.validation import (
    MAX_PARAMETER_COMBINATIONS,
    MAX_TRIALS,
    ExperimentValidationError,
    ExperimentValidator,
)


def test_validator_rejects_empty_parameters():
    res = ExperimentValidator.validate_parameter_sweep("", [0.1, 0.2])
    assert not res.valid
    assert any("Parameter name must be a non-empty string" in e for e in res.errors)


def test_validator_rejects_empty_values():
    res = ExperimentValidator.validate_parameter_sweep("decay", [])
    assert not res.valid
    assert any("Sweep values list cannot be empty" in e for e in res.errors)


def test_validator_enforces_resource_limits_trials():
    # Trials > 100 should fail
    res = ExperimentValidator.validate_parameter_sweep("decay", [0.1, 0.2], trials=101)
    assert not res.valid
    assert any("exceeds maximum allowed (100)" in e for e in res.errors)

    # Negative or zero trials should fail
    res_zero = ExperimentValidator.validate_parameter_sweep("decay", [0.1, 0.2], trials=0)
    assert not res_zero.valid


def test_validator_enforces_resource_limits_combinations():
    # More than 144 sweep values
    huge_values = [i * 0.01 for i in range(150)]
    res = ExperimentValidator.validate_parameter_sweep("decay", huge_values, trials=1)
    assert not res.valid
    assert any("exceeds maximum limit" in e for e in res.errors)


def test_validator_rejects_out_of_range_values():
    # decay must be in [0, 1]
    res = ExperimentValidator.validate_parameter_sweep("decay", [0.0, 0.5, 1.5])
    assert not res.valid
    assert any("must be <= 1.0" in e for e in res.errors)


def test_validator_grid_sweep_constraints():
    # Same parameter for X and Y should fail
    res = ExperimentValidator.validate_grid_sweep("decay", [0.1, 0.2], "decay", [0.1, 0.2])
    assert not res.valid
    assert any("requires two distinct parameters" in e for e in res.errors)

    # Valid grid should pass
    res_valid = ExperimentValidator.validate_grid_sweep("memory_similarity", [0.1, 0.5], "update_strength", [0.5, 1.0])
    assert res_valid.valid


def test_validator_lab_experiment_missing_fields():
    data = {
        "title": "",
        "research_question": "",
        "mechanism": "unknown_mechanism",
    }
    res = ExperimentValidator.validate_lab_experiment(data)
    assert not res.valid
    assert any("title is required" in e for e in res.errors)
    assert any("question is required" in e for e in res.errors)
    assert any("Unknown mechanism" in e for e in res.errors)
