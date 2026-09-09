"""Unit tests for Phase 22 Experiment Studio core engine and data models."""

import pytest
from core.studio import (
    ComputationStep,
    ExperimentConfig,
    ExperimentHypothesis,
    ExperimentNote,
    ExperimentResult,
    ExperimentStudioEngine,
    ParameterSweepPoint,
    ParameterSweepResult,
    SynapticDeltaRecord,
)


def test_experiment_config_validation():
    # Valid config
    cfg = ExperimentConfig(
        experiment_id="TEST-001",
        name="Valid Exp",
        experiment_type="ENCODING",
        seed=42,
        d=16,
        decay=0.05,
        update_strength=1.0,
        concept_a="cat",
        value_a="whiskers",
    )
    assert cfg.validate() == []

    # Invalid dimension
    cfg_bad_d = ExperimentConfig(
        experiment_id="TEST-BAD-D",
        name="Bad D",
        experiment_type="ENCODING",
        d=24,  # Not 8, 16, 32, 64
    )
    assert any("Dimension" in err for err in cfg_bad_d.validate())

    # Invalid decay
    cfg_bad_decay = ExperimentConfig(
        experiment_id="TEST-BAD-DECAY",
        name="Bad Decay",
        experiment_type="ENCODING",
        decay=1.2,
    )
    assert any("Decay" in err for err in cfg_bad_decay.validate())


def test_engine_initial_state():
    engine = ExperimentStudioEngine()
    # Check default seeded experiment
    assert len(engine.history) >= 1
    assert engine.history[0].experiment_id == "EXP-BASE-001"
    assert engine.history[0].baseline_metrics["fidelity"] > 0.5


def test_engine_templates_and_journey():
    engine = ExperimentStudioEngine()
    templates = engine.get_templates()
    assert len(templates) == 5
    types = {t["type"] for t in templates}
    assert "INTERFERENCE" in types
    assert "PERSISTENCE" in types
    assert "SURGERY" in types
    assert "COUNTERFACTUAL" in types
    assert "COMPARISON" in types

    journey = engine.get_starter_journey()
    assert journey["total_steps"] == 8
    assert len(journey["steps"]) == 8


def test_encoding_experiment_run():
    engine = ExperimentStudioEngine()
    cfg = ExperimentConfig(
        experiment_id="TEST-ENC-001",
        name="Encoding Test",
        experiment_type="ENCODING",
        seed=100,
        d=16,
        decay=0.0,
        update_strength=1.0,
        concept_a="solar",
        value_a="energy",
    )
    res = engine.run_experiment(cfg)
    assert res.experiment_id == "TEST-ENC-001"
    assert res.experiment_metrics["fidelity"] > 0.8
    assert len(res.pipeline_steps) == 6
    assert res.is_deterministic is True
    assert res.seed_used == 100


def test_interference_experiment_run():
    engine = ExperimentStudioEngine()
    cfg = ExperimentConfig(
        experiment_id="TEST-INT-001",
        name="Interference Test",
        experiment_type="INTERFERENCE",
        seed=42,
        d=16,
        decay=0.05,
        update_strength=1.0,
        concept_a="cat",
        value_a="whiskers",
        interfering_concept="tiger",
        interfering_value="stripes",
        interfering_strength=1.2,
    )
    hypo = ExperimentHypothesis(
        hypothesis_text="Strong interference will degrade cat fidelity.",
        predicted_outcome="RETENTION_DROP",
    )
    res = engine.run_experiment(cfg, hypo)
    assert res.delta_metrics["fidelity_delta"] <= 0.05
    assert len(res.top_synaptic_changes) <= 10
    assert len(res.observation_statements) >= 1
    assert len(res.interpretation_statements) >= 1


def test_export_experiment_json():
    engine = ExperimentStudioEngine()
    exp_id = engine.history[0].experiment_id
    exported = engine.export_experiment_json(exp_id)
    assert exported["schema_version"] == "pathway.phase22.experiment_studio.v1"
    assert exported["experiment"]["experiment_id"] == exp_id
    assert "computational_framework" in exported
    assert "scientific_guardrails" in exported
