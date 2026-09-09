"""Tests for core Memory X-Ray state snapshots, trajectory, diff, and activation (Phase 05)."""

import pytest
import numpy as np

from core import ExperimentConfig, run_experiment
from core.mechanisms.base import MechanismParams
from core.task import TaskConfig
from core.xray import (
    compare_states,
    compute_activation_profile,
    create_memory_snapshots,
    detect_state_changes,
    generate_heatmap_matrices,
    get_state_trajectory,
    analyze_sparsity,
    StateChangeClassification,
)


@pytest.fixture
def sample_experiment():
    """Create a deterministic sample experiment for testing."""
    cfg = ExperimentConfig(
        seed=42,
        mechanism="interference",
        params=MechanismParams(
            state_dim=64,
            update_strength=0.9,
            memory_strength=1.0,
            interference_strength=0.5,
        ),
        task=TaskConfig(
            seed=42,
            d=64,
            n_objects=4,
            n_symbols=4,
            n_conflicts=2,
            cycles=1,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_memory_snapshots_creation(sample_experiment):
    """Verify that MemorySnapshot extracts real mathematical states without fabrication."""
    snapshots = create_memory_snapshots(sample_experiment)
    assert len(snapshots) == len(sample_experiment.snapshots)

    # Initial state (t=0)
    s0 = snapshots[0]
    assert s0.timeline_step == 0
    assert s0.event_id is None
    assert len(s0.state_vector) == 64
    assert s0.sparsity == 0.0  # Initially all zero
    assert len(s0.active_units) == 0
    assert len(s0.inactive_units) == 64

    # Later state (t > 0)
    s1 = snapshots[1]
    assert s1.timeline_step == 1
    assert s1.event_id is not None
    assert s1.sparsity > 0.0
    assert len(s1.active_units) > 0
    assert len(s1.active_units) + len(s1.inactive_units) == 64

    # Serialization
    d = s1.to_dict()
    assert "snapshot_id" in d
    assert "memory_strength" in d
    assert "similarity_statistics" in d
    assert "associations" in d


def test_state_trajectory(sample_experiment):
    """Verify chronological state trajectory progression."""
    traj = get_state_trajectory(sample_experiment)
    assert traj.total_steps == len(sample_experiment.snapshots)
    assert len(traj.steps) == traj.total_steps
    assert len(traj.state_norms) == traj.total_steps
    assert len(traj.state_vectors) == traj.total_steps

    # Norm starts at 0 and grows
    assert traj.state_norms[0] == 0.0
    assert traj.state_norms[1] > 0.0

    d = traj.to_dict()
    assert d["experiment_id"] == sample_experiment.experiment_id


def test_compare_states():
    """Verify sound mathematical distance metrics between memory states."""
    v1 = np.array([1.0, 0.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0, 0.0])

    comp = compare_states(v1, v2)
    assert comp.dimension_count == 4
    assert pytest.approx(comp.l1_distance, 1e-6) == 2.0
    assert pytest.approx(comp.l2_distance, 1e-6) == np.sqrt(2.0)
    assert pytest.approx(comp.cosine_distance, 1e-6) == 1.0  # Orthogonal vectors

    # Identical vectors
    comp_same = compare_states(v1, v1)
    assert comp_same.l1_distance == 0.0
    assert comp_same.l2_distance == 0.0
    assert comp_same.cosine_distance == 0.0
    assert comp_same.normalized_difference == 0.0


def test_activation_profile():
    """Verify activation profile, distribution quantiles, and entropy."""
    vec = np.zeros(100)
    vec[0:10] = 1.0  # 10 active units, 90 inactive

    prof = compute_activation_profile(vec, step=1)
    assert prof.total_units == 100
    assert prof.active_units_count == 10
    assert pytest.approx(prof.sparsity_ratio, 1e-6) == 0.1
    assert pytest.approx(prof.max_activation, 1e-6) == 1.0
    assert prof.activation_entropy > 0.0
    assert "p50" in prof.distribution_quantiles


def test_state_change_detection(sample_experiment):
    """Verify consecutive delta calculation and transition classification."""
    traj = get_state_trajectory(sample_experiment)
    changes = detect_state_changes(traj)

    assert len(changes["records"]) == traj.total_steps - 1
    assert "mean_change_magnitude" in changes
    assert "max_change_magnitude" in changes
    assert changes["max_change_magnitude"] >= changes["mean_change_magnitude"]

    # Classifications must be valid enum strings
    valid_classes = {StateChangeClassification.STABLE.value, StateChangeClassification.SHIFT.value, StateChangeClassification.MAJOR_SHIFT.value}
    for r in changes["records"]:
        assert r["classification"] in valid_classes


def test_heatmaps_generation(sample_experiment):
    """Verify 2D matrix heatmap generation."""
    heatmaps = generate_heatmap_matrices(sample_experiment)
    assert heatmaps["experiment_id"] == sample_experiment.experiment_id

    txm = heatmaps["time_x_memory"]["strength"]
    assert len(txm) == len(sample_experiment.snapshots)
    assert len(txm[0]) == heatmaps["memory_axis"]["count"]

    txu = heatmaps["time_x_unit"]["activation"]
    assert len(txu) == len(sample_experiment.snapshots)
    assert len(txu[0]) == 64


def test_sparsity_analysis(sample_experiment):
    """Verify substrate sparsity analysis over time."""
    sparsity = analyze_sparsity(sample_experiment)
    assert sparsity.total_units == 64
    assert len(sparsity.active_units_per_step) == len(sample_experiment.snapshots)
    assert 0.0 <= sparsity.mean_sparsity <= 1.0
    assert "median_abs_activation" in sparsity.sparsity_distribution
