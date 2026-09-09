"""Tests for Phase 18 Research Lab Engine (custom experiments, reproducibility, history, comparison)."""

import pytest
import numpy as np

from core.forensics import (
    CustomExperimentConfig,
    ResearchLabEngine,
)


def test_research_lab_custom_experiment_execution():
    """Verify that a custom experiment executes and returns valid metrics."""
    engine = ResearchLabEngine()
    cfg = CustomExperimentConfig(
        name="Decay vs Plasticity Test",
        dimension=16,
        decay=0.05,
        plasticity_eta=1.2,
        memories=[
            {"concept": "mars", "value": "red_planet"},
            {"concept": "jupiter", "value": "gas_giant"},
        ],
        concept_similarity=0.3,
        seed=101,
        notes="Testing retention with eta=1.2",
    )

    res = engine.run_experiment(cfg)
    assert res.run_id == "EXP-001"
    assert res.matrix_norm > 0.0
    assert len(res.recalls) == 2
    assert res.research_notes == "Testing retention with eta=1.2"
    assert len(engine.get_history()) == 1


def test_research_lab_100_percent_reproducibility():
    """Verify that running the same experiment configuration twice produces byte-identical results."""
    engine = ResearchLabEngine()
    cfg = CustomExperimentConfig(
        dimension=16,
        decay=0.03,
        plasticity_eta=1.0,
        memories=[
            {"concept": "sun", "value": "star"},
            {"concept": "moon", "value": "satellite"},
        ],
        seed=999,
    )

    res1 = engine.run_experiment(cfg)
    res2 = engine.run_experiment(cfg)

    W1 = np.array(res1.matrix_weights)
    W2 = np.array(res2.matrix_weights)

    # Identical matrix weights
    assert np.allclose(W1, W2, atol=1e-12)
    assert res1.average_fidelity == res2.average_fidelity


def test_research_lab_experiment_comparison():
    """Verify side-by-side comparative inspection between two experiments."""
    engine = ResearchLabEngine()
    cfg_low_decay = CustomExperimentConfig(decay=0.01, seed=42)
    cfg_high_decay = CustomExperimentConfig(decay=0.20, seed=42)

    res_a = engine.run_experiment(cfg_low_decay)
    res_b = engine.run_experiment(cfg_high_decay)

    comp = engine.compare_experiments(res_a.run_id, res_b.run_id)

    assert "matrix_frobenius_distance" in comp
    assert comp["matrix_frobenius_distance"] > 0.0
    assert comp["parameter_differences"]["decay_delta"] == pytest.approx(0.19, abs=1e-5)
    # Higher decay should result in lower average fidelity
    assert comp["fidelity_delta"] <= 0.0
    assert "scientific_interpretation" in comp


def test_research_lab_synaptic_silencing():
    """Verify that custom experiment supports silencing a designated synapse."""
    engine = ResearchLabEngine()
    cfg_normal = CustomExperimentConfig(seed=42)
    res_normal = engine.run_experiment(cfg_normal)

    cfg_silenced = CustomExperimentConfig(seed=42, synaptic_silencing_id="syn_k0_v0")
    res_silenced = engine.run_experiment(cfg_silenced)

    W_silenced = np.array(res_silenced.matrix_weights)
    assert W_silenced[0, 0] == 0.0
