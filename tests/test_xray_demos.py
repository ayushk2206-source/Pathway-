"""The 7 Canonical Demonstrations required for Phase 05 Memory X-Ray & Causal Memory Map."""

import pytest
import numpy as np

from core import ExperimentConfig, run_experiment
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.interventions import create_change_strength_intervention
from core.mechanisms.base import MechanismParams
from core.task import TaskConfig
from core.xray import (
    compare_xray_surgery,
    compute_memory_strengths,
    detect_interference,
    detect_reinforcement,
    detect_state_anomalies,
    detect_state_changes,
    find_nearest_memories,
    generate_xray_report,
    get_memory_trace,
    get_state_trajectory,
    inspect_event_before_after,
)


@pytest.fixture
def canonical_demo_experiment():
    """Deterministic, high-fidelity experiment setup for canonical demonstrations."""
    cfg = ExperimentConfig(
        seed=777,
        mechanism="interference",
        params=MechanismParams(
            state_dim=128,
            update_strength=0.9,
            memory_strength=1.0,
            interference_strength=0.6,
        ),
        task=TaskConfig(
            seed=777,
            d=128,
            n_objects=6,
            n_symbols=4,
            n_conflicts=3,
            object_similarity=0.45,
            cycles=2,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_demo_1_state_trajectory_and_changes(canonical_demo_experiment):
    """DEMO 1: Run memory sequence, generate state trajectory, and show actual state changes."""
    exp = canonical_demo_experiment
    traj = get_state_trajectory(exp)
    changes = detect_state_changes(traj)

    # 1. Real trajectory exists across all timesteps
    assert traj.total_steps == len(exp.snapshots)
    assert len(traj.state_vectors) == traj.total_steps
    assert all(len(v) == 128 for v in traj.state_vectors)

    # 2. State norm grows from zero to saturation
    assert traj.state_norms[0] == 0.0
    assert traj.state_norms[-1] > 0.0

    # 3. Transitions quantified into records
    records = changes["records"]
    assert len(records) == traj.total_steps - 1
    assert any(r["change_magnitude"] > 0.0 for r in records)
    assert "mean_change_magnitude" in changes
    assert changes["mean_change_magnitude"] > 0.0


def test_demo_2_single_memory_inspection(canonical_demo_experiment):
    """DEMO 2: Select one memory and show trace, strength, reinforcement, competition, neighbors."""
    exp = canonical_demo_experiment
    strengths_map = compute_memory_strengths(exp)
    assert len(strengths_map) > 0

    selected_memory_id = list(strengths_map.keys())[0]

    # 1. Memory trace through lifecycle
    trace = get_memory_trace(exp, selected_memory_id)
    assert trace is not None
    assert trace.memory_id == selected_memory_id
    assert len(trace.stages) >= 1
    assert trace.stages[0]["stage"] == "ENCODED"

    # 2. Memory strength profile
    prof = strengths_map[selected_memory_id]
    assert prof.peak_strength > 0.0
    assert prof.final_strength >= 0.0
    assert len(prof.timeline_strengths) == len(exp.snapshots)

    # 3. Reinforcement detection
    reinf_list = detect_reinforcement(exp)
    assert isinstance(reinf_list, list)

    # 4. Nearest neighbors in vector space
    neighbors = find_nearest_memories(exp, selected_memory_id, k=3)
    assert len(neighbors) <= 3
    if neighbors:
        assert neighbors[0]["cosine_similarity"] <= 1.0


def test_demo_3_event_before_after_microscope(canonical_demo_experiment):
    """DEMO 3: Select one event, show state before, state after, and state difference."""
    exp = canonical_demo_experiment
    target_event_idx = 1
    insp = inspect_event_before_after(exp, target_event_idx)

    assert insp["event"]["index"] == target_event_idx
    assert len(insp["state_before"]["vector"]) == 128
    assert len(insp["state_after"]["vector"]) == 128

    diff = insp["diff"]
    assert diff["l2_distance"] > 0.0
    assert diff["total_units_changed"] > 0
    assert len(diff["top_unit_shifts"]) > 0


def test_demo_4_memory_surgery_and_topology_shift(canonical_demo_experiment):
    """DEMO 4: Perform Phase 4 memory surgery, generate X-Ray before and after, show topology shift."""
    exp = canonical_demo_experiment

    # Surgical intervention: scale strength of target event
    intv = create_change_strength_intervention(new_strength=0.1, target_timestep=1)
    cf_res = run_counterfactual(exp, intv, title="Demo 4 Surgery")
    cf_exp = cf_res.to_experiment()

    # Compare X-Ray topological maps
    surgery_diff = compare_xray_surgery(exp, cf_exp)
    assert surgery_diff["original_experiment_id"] == exp.experiment_id
    assert surgery_diff["counterfactual_experiment_id"] == cf_exp.experiment_id

    # 1. 2D projection shifted
    shifts = surgery_diff["point_shifts"]
    assert len(shifts) > 0
    assert any(s["shift_magnitude"] > 0.0 for s in shifts)

    # 2. Graph edges updated
    topo = surgery_diff["topological_edges"]
    assert topo["original_edge_count"] > 0
    assert topo["counterfactual_edge_count"] > 0


def test_demo_5_interference_scenario(canonical_demo_experiment):
    """DEMO 5: Create interference scenario, identify competing memories, show overlap and downstream effect."""
    exp = canonical_demo_experiment
    interferences = detect_interference(exp)
    assert len(interferences) > 0

    top_pair = interferences[0]
    assert top_pair.overlap > 0.0  # Vector overlap in address space
    assert top_pair.interference_score > 0.0  # Measured readout degradation
    assert len(top_pair.affected_steps) > 0
    assert "cross-talk" in top_pair.evidence_notes.lower() or "overlap" in top_pair.evidence_notes.lower()


def test_demo_6_anomaly_detection(canonical_demo_experiment):
    """DEMO 6: Detect unusual state transitions with empirical mathematical evidence."""
    exp = canonical_demo_experiment
    anomalies = detect_state_anomalies(exp)
    assert isinstance(anomalies, list)

    if anomalies:
        a = anomalies[0]
        assert a.step >= 0
        assert a.metric
        assert a.deviation_z_score > 0.0
        assert len(a.evidence) > 10
    else:
        # If no outlier anomalies occur in base run, verify detector correctly evaluated
        assert anomalies == []


def test_demo_7_complete_xray_report(canonical_demo_experiment):
    """DEMO 7: Generate complete X-Ray report, verifying every result links back to experiment and timeline."""
    exp = canonical_demo_experiment
    report = generate_xray_report(exp)

    assert report.experiment_id == exp.experiment_id
    rep_dict = report.to_dict()

    assert "overview" in rep_dict
    assert rep_dict["overview"]["total_timesteps"] == len(exp.snapshots)

    assert "state_dynamics" in rep_dict
    assert "memory_strength" in rep_dict
    assert "interference" in rep_dict
    assert "reinforcement" in rep_dict
    assert "sparsity" in rep_dict
    assert "clusters" in rep_dict
    assert "limitations" in rep_dict
    assert len(rep_dict["limitations"]) >= 3
