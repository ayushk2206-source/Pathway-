"""Unit and integration tests for Phase 22 experiment types, A/B comparisons, sweeps, and branching."""

import pytest
from core.studio import (
    ExperimentConfig,
    ExperimentHypothesis,
    ExperimentStudioEngine,
)


def test_surgery_experiment():
    engine = ExperimentStudioEngine()
    cfg = ExperimentConfig(
        experiment_id="TEST-SURGERY-001",
        name="Targeted Micro-Surgery",
        experiment_type="SURGERY",
        seed=42,
        d=16,
        concept_a="galaxy",
        value_a="spiral",
        surgery_action="zero",
    )
    res = engine.run_experiment(cfg)
    assert res.experiment_type if hasattr(res, "experiment_type") else res.config.experiment_type == "SURGERY"
    assert len(res.top_synaptic_changes) > 0
    # Top change should reflect altered synapse
    assert any(c.weight_after == 0.0 for c in res.top_synaptic_changes)


def test_persistence_decay_cycles():
    engine = ExperimentStudioEngine()
    cfg = ExperimentConfig(
        experiment_id="TEST-PERSISTENCE-001",
        name="Persistence Decay Test",
        experiment_type="PERSISTENCE",
        seed=42,
        d=16,
        decay=0.2,
        decay_cycles=6,
        concept_a="apple",
        value_a="orchard",
    )
    res = engine.run_experiment(cfg)
    # 6 cycles of decay=0.2 should significantly reduce matrix norm
    assert res.delta_metrics["matrix_norm_delta"] < 0
    assert res.experiment_metrics["matrix_norm"] < res.baseline_metrics["matrix_norm"]


def test_counterfactual_experiment():
    engine = ExperimentStudioEngine()
    cfg = ExperimentConfig(
        experiment_id="TEST-CF-001",
        name="Counterfactual Plasticity",
        experiment_type="COUNTERFACTUAL",
        seed=42,
        d=16,
        decay=0.05,
        update_strength=0.5,
        cf_param_name="update_strength",
        cf_param_value=1.8,
        concept_a="quantum",
        value_a="wave",
    )
    res = engine.run_experiment(cfg)
    # Higher learning rate in counterfactual should increase norm
    assert res.delta_metrics["matrix_norm_delta"] > 0


def test_ab_comparison():
    engine = ExperimentStudioEngine()
    cfg_a = ExperimentConfig(
        experiment_id="EXP-A-LOW",
        name="Low Interference",
        experiment_type="INTERFERENCE",
        seed=42,
        d=16,
        concept_a="cat",
        value_a="whiskers",
        interfering_concept="dog",
        interfering_value="bark",
        interfering_strength=0.2,
    )
    cfg_b = ExperimentConfig(
        experiment_id="EXP-B-HIGH",
        name="High Interference",
        experiment_type="INTERFERENCE",
        seed=42,
        d=16,
        concept_a="cat",
        value_a="whiskers",
        interfering_concept="dog",
        interfering_value="bark",
        interfering_strength=1.5,
    )
    comp = engine.run_ab_comparison(cfg_a, cfg_b)
    assert comp.exp_a.config.interfering_strength == 0.2
    assert comp.exp_b.config.interfering_strength == 1.5
    assert "interfering_strength" in comp.differing_parameters
    # High interference should produce lower or equal fidelity compared to low
    assert comp.diff_summary["fidelity_diff"] <= 0.05


def test_parameter_sweep():
    engine = ExperimentStudioEngine()
    base_cfg = ExperimentConfig(
        experiment_id="EXP-SWEEP-BASE",
        name="Sweep Base",
        experiment_type="INTERFERENCE",
        seed=42,
        d=16,
        concept_a="cat",
        value_a="whiskers",
        interfering_concept="tiger",
        interfering_value="stripes",
    )
    sweep_res = engine.run_parameter_sweep(
        base_config=base_cfg,
        param_name="interfering_strength",
        param_values=[0.0, 0.3, 0.6, 0.9, 1.2],
    )
    assert sweep_res.param_name == "interfering_strength"
    assert len(sweep_res.points) == 5
    assert sweep_res.points[0].param_value == 0.0
    assert sweep_res.points[0].fidelity > 0.8
    assert sweep_res.correlation != 0.0


def test_branch_and_duplicate():
    engine = ExperimentStudioEngine()
    # Duplicate existing experiment and change decay
    base_id = engine.history[0].experiment_id
    branched = engine.duplicate_and_branch(
        experiment_id=base_id,
        modified_param="decay",
        new_value=0.4,
    )
    assert branched.config.decay == 0.4
    assert branched.config.changed_variable == "decay"
    assert branched.experiment_id.startswith("EXP-BRANCH-")
