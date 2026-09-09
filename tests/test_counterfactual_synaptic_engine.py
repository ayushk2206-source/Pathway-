"""Tests for Phase 16: Counterfactual Synaptic & Mechanism Engine."""

import copy
import numpy as np
import pytest

from core.counterfactual import (
    Intervention,
    InterventionType,
    compare_synaptic_states_at_step,
    create_change_decay_intervention,
    create_change_plasticity_intervention,
    create_synapse_prevent_strengthen_intervention,
    create_synapse_scale_intervention,
    create_synapse_silence_intervention,
    reproduce_counterfactual,
    run_counterfactual,
)
from core.experiment import Experiment, ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.synaptic import extract_synaptic_state_from_experiment
from core.task import TaskConfig


@pytest.fixture
def hebbian_experiment():
    """A standard deterministic Hebbian associative experiment with multiple events."""
    cfg = ExperimentConfig(
        seed=42,
        mechanism="hebbian",
        params=MechanismParams(decay=0.05, update_strength=1.0, state_dim=16),
        task=TaskConfig(
            seed=42,
            n_objects=3,
            n_symbols=4,
            n_conflicts=1,
            cycles=2,
            order="interleaved",
            d=16,
        ),
    )
    return run_experiment(cfg)


def test_signature_prevent_synaptic_strengthening(hebbian_experiment):
    """SIGNATURE EXPERIMENT: "What if this synapse had NOT strengthened?"

    1. Run normal experiment.
    2. Inspect synaptic weights at T1 and T2.
    3. Choose a synapse that strengthens between T1 and T2.
    4. Create counterfactual branch with SYNAPSE_PREVENT_STRENGTHEN.
    5. Verify the weight does not strengthen beyond baseline at T>=1.
    6. Verify original experiment remains 100% unchanged.
    """
    orig = hebbian_experiment
    orig_events_copy = copy.deepcopy(orig.events)
    orig_snaps_copy = copy.deepcopy(orig.snapshots)
    orig_metrics_copy = copy.deepcopy(orig.metrics)

    # State at T1 and T2
    net_t1 = extract_synaptic_state_from_experiment(orig, 1, display_dim=16)
    net_t2 = extract_synaptic_state_from_experiment(orig, 2, display_dim=16)
    W1 = np.array(net_t1.matrix_weights)
    W2 = np.array(net_t2.matrix_weights)

    # Find a synapse that strengthened
    delta_W = W2 - W1
    strengthened_indices = np.where(delta_W > 0.05)
    assert len(strengthened_indices[0]) > 0, "Expected at least one synapse to strengthen"
    target_row = int(strengthened_indices[0][0])
    target_col = int(strengthened_indices[1][0])
    syn_id = f"syn_k{target_col}_v{target_row}"
    w_baseline = float(W1[target_row, target_col])

    # Create counterfactual intervention
    intv = create_synapse_prevent_strengthen_intervention(
        synapse_id=syn_id,
        target_timestep=1,
        source_idx=target_col,
        target_idx=target_row,
        description=f"Prevent strengthening of {syn_id} at T>=1",
    )

    cf = run_counterfactual(orig, intv)
    cf_exp_dict = cf.counterfactual_result["experiment"]
    cf_exp = Experiment.from_dict(cf_exp_dict)

    # Verify original experiment was strictly NOT modified
    assert len(orig.events) == len(orig_events_copy)
    assert orig.metrics == orig_metrics_copy
    for idx in range(len(orig.snapshots)):
        assert orig.snapshots[idx]["state_vector"] == orig_snaps_copy[idx]["state_vector"]

    # Verify counterfactual prevented strengthening on that synapse
    cf_net_t2 = extract_synaptic_state_from_experiment(cf_exp, 2, display_dim=16)
    cf_W2 = np.array(cf_net_t2.matrix_weights)
    cf_weight_at_t2 = float(cf_W2[target_row, target_col])
    orig_weight_at_t2 = float(W2[target_row, target_col])

    # The counterfactual weight at T2 must be <= baseline level (and strictly less than original at T2)
    assert cf_weight_at_t2 <= w_baseline + 1e-6
    assert cf_weight_at_t2 < orig_weight_at_t2

    # Divergence should be registered
    assert cf.divergence.get("first_divergence_step") is not None


def test_synapse_silence_intervention(hebbian_experiment):
    """Verify SYNAPSE_SILENCE zeroes connection weight at and after divergence timestep."""
    orig = hebbian_experiment
    target_row, target_col = 2, 3
    syn_id = f"syn_k{target_col}_v{target_row}"

    intv = create_synapse_silence_intervention(
        synapse_id=syn_id,
        target_timestep=2,
        source_idx=target_col,
        target_idx=target_row,
    )

    cf = run_counterfactual(orig, intv)
    cf_exp = Experiment.from_dict(cf.counterfactual_result["experiment"])

    # At snapshot 1 and 2 (events 0 and 1, before divergence at event 2), weight should match original
    cf_net_t1 = extract_synaptic_state_from_experiment(cf_exp, 1, display_dim=16)
    orig_net_t1 = extract_synaptic_state_from_experiment(orig, 1, display_dim=16)
    assert np.isclose(cf_net_t1.matrix_weights[target_row][target_col], orig_net_t1.matrix_weights[target_row][target_col])

    cf_net_t2 = extract_synaptic_state_from_experiment(cf_exp, 2, display_dim=16)
    orig_net_t2 = extract_synaptic_state_from_experiment(orig, 2, display_dim=16)
    assert np.isclose(cf_net_t2.matrix_weights[target_row][target_col], orig_net_t2.matrix_weights[target_row][target_col])

    # At snapshot 3 and beyond (event 2 and after), weight is silenced (0.0)
    for snap_idx in [3, 4]:
        if snap_idx < len(cf_exp.snapshots):
            cf_net = extract_synaptic_state_from_experiment(cf_exp, snap_idx, display_dim=16)
            assert cf_net.matrix_weights[target_row][target_col] == 0.0



def test_change_decay_and_plasticity(hebbian_experiment):
    """Verify CHANGE_DECAY and CHANGE_PLASTICITY alter state dynamics genuinely."""
    orig = hebbian_experiment

    # Test faster decay
    intv_decay = create_change_decay_intervention(new_decay=0.8, target_timestep=0)
    cf_decay = run_counterfactual(orig, intv_decay)
    cf_decay_exp = Experiment.from_dict(cf_decay.counterfactual_result["experiment"])

    final_orig_norm = float(np.linalg.norm(orig.snapshots[-1]["state_vector"]))
    final_cf_norm = float(np.linalg.norm(cf_decay_exp.snapshots[-1]["state_vector"]))

    # With high decay (0.8 vs 0.05), final state norm should be lower
    assert final_cf_norm < final_orig_norm

    # Test weaker plasticity
    intv_plast = create_change_plasticity_intervention(new_update_strength=0.1, target_timestep=0)
    cf_plast = run_counterfactual(orig, intv_plast)
    cf_plast_exp = Experiment.from_dict(cf_plast.counterfactual_result["experiment"])

    final_plast_norm = float(np.linalg.norm(cf_plast_exp.snapshots[-1]["state_vector"]))
    assert final_plast_norm < final_orig_norm


def test_synchronized_synaptic_comparison(hebbian_experiment):
    """Verify synchronized network comparison at timestep T computes correct deltas."""
    orig = hebbian_experiment
    syn_id = "syn_k1_v2"
    intv = create_synapse_silence_intervention(synapse_id=syn_id, target_timestep=2, source_idx=1, target_idx=2)
    cf = run_counterfactual(orig, intv)
    cf_exp = Experiment.from_dict(cf.counterfactual_result["experiment"])

    # Pre-divergence at T=1
    comp_t1 = compare_synaptic_states_at_step(orig, cf_exp, step_idx=1, display_dim=16, divergence_step=2)
    assert comp_t1["matrix_frobenius_delta"] == 0.0
    assert comp_t1["changed_synapses_count"] == 0
    assert not comp_t1["is_post_divergence"]

    # Post-divergence at T=2
    comp_t2 = compare_synaptic_states_at_step(orig, cf_exp, step_idx=2, display_dim=16, divergence_step=2)
    assert comp_t2["is_post_divergence"]
    assert "outcome_deltas" in comp_t2
    assert "query_comparison" in comp_t2


def test_multiple_branches_from_same_baseline(hebbian_experiment):
    """Learner creates multiple controlled branches from one baseline."""
    orig = hebbian_experiment
    syn_id = "syn_k0_v1"

    # Branch 1: Silenced
    cf_silence = run_counterfactual(
        orig,
        create_synapse_silence_intervention(syn_id, target_timestep=1, source_idx=0, target_idx=1),
        title="What if S is silenced?",
    )
    # Branch 2: Weakened (0.25x)
    cf_weaken = run_counterfactual(
        orig,
        create_synapse_scale_intervention(syn_id, factor=0.25, target_timestep=1, source_idx=0, target_idx=1),
        title="What if S is weakened?",
    )
    # Branch 3: Strengthened (2.0x)
    cf_strength = run_counterfactual(
        orig,
        create_synapse_scale_intervention(syn_id, factor=2.0, target_timestep=1, source_idx=0, target_idx=1),
        title="What if S is strengthened?",
    )

    assert cf_silence.counterfactual_id != cf_weaken.counterfactual_id
    assert cf_weaken.counterfactual_id != cf_strength.counterfactual_id
    assert cf_silence.parent_experiment_id == orig.experiment_id
    assert cf_weaken.parent_experiment_id == orig.experiment_id


def test_counterfactual_reproducibility(hebbian_experiment):
    """Verify bit-exact reproducibility when re-running a counterfactual intervention."""
    orig = hebbian_experiment
    intv = create_change_decay_intervention(new_decay=0.4, target_timestep=1)
    cf = run_counterfactual(orig, intv)

    metrics = cf.counterfactual_result.get("metrics", {})
    repro = reproduce_counterfactual(orig, intv, expected_metrics=metrics)

    assert repro["reproduced"] is True
    assert repro["exact_match"] is True
