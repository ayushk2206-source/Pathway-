"""Tests for divergence analysis, propagation tracking, and classification (Phase 04)."""

import pytest

from core.counterfactual import (
    DivergenceClassification,
    classify_divergence,
    compute_divergence_profile,
    create_ablation,
)
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig


@pytest.fixture
def standard_experiment():
    cfg = ExperimentConfig(
        seed=100,
        mechanism="interference",
        params=MechanismParams(interference_strength=0.8, update_strength=1.0),
        task=TaskConfig(
            seed=100,
            n_objects=4,
            n_symbols=4,
            n_conflicts=3,
            cycles=1,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_divergence_propagation_metrics(standard_experiment):
    """Test step-by-step divergence metrics: L2, cosine, relative L2."""
    cf = create_ablation(standard_experiment, event_id_or_timestep=1)
    div = cf.divergence

    # Basic propagation checks
    assert div["first_divergence_step"] is not None
    assert div["final_state_distance_l2"] > 0.0
    assert div["cumulative_divergence"] > 0.0

    timeline = div["timeline"]
    assert len(timeline) == len(standard_experiment.snapshots) - 1

    # Before intervention step (step 0), state distance should be 0.0
    assert timeline[0]["state_distance_l2"] == pytest.approx(0.0, abs=1e-9)
    assert timeline[0]["cosine_similarity"] == pytest.approx(1.0, abs=1e-9)

    # After intervention step (step >= 1), divergence becomes non-zero
    assert any(t["state_distance_l2"] > 0.01 for t in timeline[1:])


def test_affected_and_unaffected_memories(standard_experiment):
    """Verify that affected and unaffected memories are partitioned correctly."""
    cf = create_ablation(standard_experiment, event_id_or_timestep=0)
    div = cf.divergence

    affected = div["affected_memories"]
    unaffected = div["unaffected_memories"]

    # All objects in original experiment should be accounted for
    total_objects = {q["object_label"] for q in standard_experiment.queries}
    reported_objects = {a["object_label"] for a in affected} | set(unaffected)
    assert reported_objects == total_objects


def test_classification_transient():
    """Verify TRANSIENT classification: surges then returns to near-zero."""
    distances = [0.0, 0.5, 0.8, 0.4, 0.00001]
    cosines = [1.0, 0.8, 0.6, 0.9, 0.9999]
    cls, conf, _ = classify_divergence(
        distances=distances,
        cosines=cosines,
        affected_count=1,
        total_memories=4,
        first_step=1,
        intervention_step=1,
    )
    assert cls == DivergenceClassification.TRANSIENT
    assert conf >= 0.8


def test_classification_damped():
    """Verify DAMPED classification: peaks and steadily declines."""
    distances = [0.0, 0.9, 0.7, 0.4, 0.2]
    cosines = [1.0, 0.5, 0.7, 0.85, 0.92]
    cls, conf, _ = classify_divergence(
        distances=distances,
        cosines=cosines,
        affected_count=2,
        total_memories=4,
        first_step=1,
        intervention_step=1,
    )
    assert cls == DivergenceClassification.DAMPED
    assert conf >= 0.8


def test_classification_cumulative():
    """Verify CUMULATIVE classification: monotonic growth from first divergence."""
    distances = [0.0, 0.1, 0.25, 0.45, 0.70]
    cosines = [1.0, 0.95, 0.88, 0.75, 0.60]
    cls, conf, _ = classify_divergence(
        distances=distances,
        cosines=cosines,
        affected_count=2,
        total_memories=4,
        first_step=1,
        intervention_step=1,
    )
    assert cls == DivergenceClassification.CUMULATIVE
    assert conf >= 0.8


def test_classification_delayed():
    """Verify DELAYED classification: intervention at step 1, divergence at step 4."""
    distances = [0.0, 0.0, 0.0, 0.0, 0.5]
    cosines = [1.0, 1.0, 1.0, 1.0, 0.8]
    cls, conf, _ = classify_divergence(
        distances=distances,
        cosines=cosines,
        affected_count=1,
        total_memories=4,
        first_step=4,
        intervention_step=1,
    )
    assert cls == DivergenceClassification.DELAYED
    assert conf >= 0.8


def test_classification_oscillating():
    """Verify OSCILLATING classification: multiple direction changes."""
    distances = [0.0, 0.5, 0.2, 0.7, 0.3, 0.8]
    cosines = [1.0, 0.7, 0.9, 0.6, 0.85, 0.5]
    cls, conf, _ = classify_divergence(
        distances=distances,
        cosines=cosines,
        affected_count=3,
        total_memories=4,
        first_step=1,
        intervention_step=1,
    )
    assert cls == DivergenceClassification.OSCILLATING
    assert conf >= 0.8
