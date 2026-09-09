"""Tests for Experiment Lab Variable abstraction and registry (Phase 03)."""

import pytest

from core.lab.variables import (
    VARIABLE_REGISTRY,
    Variable,
    VariableRegistry,
    VariableRole,
    VariableType,
    get_variable,
    validate_variable_value,
)


def test_builtin_variables_present():
    vars_all = VARIABLE_REGISTRY.list_all()
    assert len(vars_all) >= 12

    indep = VARIABLE_REGISTRY.list_by_role(VariableRole.INDEPENDENT)
    dep = VARIABLE_REGISTRY.list_by_role(VariableRole.DEPENDENT)
    ctrl = VARIABLE_REGISTRY.list_by_role(VariableRole.CONTROLLED)

    assert any(v.name == "memory_similarity" for v in indep)
    assert any(v.name == "update_strength" for v in indep)
    assert any(v.name == "decay" for v in indep)
    assert any(v.name == "recall_accuracy" for v in dep)
    assert any(v.name == "interference_score" for v in dep)
    assert any(v.name == "seed" for v in ctrl)


def test_variable_validation_ranges():
    sim_var = get_variable("memory_similarity")
    assert sim_var is not None

    # Valid values
    valid, err = sim_var.validate_value(0.0)
    assert valid and err is None

    valid, err = sim_var.validate_value(0.75)
    assert valid and err is None

    valid, err = sim_var.validate_value(1.0)
    assert valid and err is None

    # Invalid values
    valid, err = sim_var.validate_value(1.5)
    assert not valid
    assert "must be <=" in err

    valid, err = sim_var.validate_value(-0.1)
    assert not valid
    assert "must be >=" in err

    valid, err = sim_var.validate_value("not_a_number")
    assert not valid
    assert "must be a float" in err


def test_variable_choice_validation():
    mech_var = get_variable("mechanism")
    assert mech_var is not None

    valid, _ = mech_var.validate_value("leaky")
    assert valid

    valid, _ = mech_var.validate_value("interference")
    assert valid

    valid, err = mech_var.validate_value("invalid_mech")
    assert not valid
    assert "not in allowed values" in err


def test_custom_variable_registration():
    reg = VariableRegistry()
    custom_var = Variable(
        name="custom_damping",
        description="Custom damping factor",
        type=VariableType.FLOAT,
        role=VariableRole.INDEPENDENT,
        default=0.5,
        minimum=0.0,
        maximum=2.0,
    )
    reg.register(custom_var)
    assert reg.get("custom_damping") == custom_var

    valid, err = reg.validate_variable("custom_damping", 3.5)
    assert not valid
    assert "must be <= 2.0" in err
