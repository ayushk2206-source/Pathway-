"""Tests for counterfactual interventions, immutability, and replay (Phase 04)."""

import copy
import pytest

from core.counterfactual import (
    CounterfactualValidationError,
    Intervention,
    InterventionType,
    create_ablation,
    create_change_similarity_intervention,
    create_change_strength_intervention,
    create_duplicate_intervention,
    create_freeze_memory_intervention,
    create_inject_memory_intervention,
    create_modify_intervention,
    create_move_intervention,
    create_remove_intervention,
    create_replace_intervention,
    create_reset_memory_intervention,
    create_surgery,
    create_temporal_surgery_intervention,
    run_counterfactual,
)
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig


@pytest.fixture
def base_experiment():
    """A standard deterministic 6-event experiment."""
    cfg = ExperimentConfig(
        seed=42,
        mechanism="leaky",
        params=MechanismParams(decay=0.2, update_strength=0.9),
        task=TaskConfig(
            seed=42,
            n_objects=3,
            n_symbols=4,
            n_conflicts=2,
            cycles=1,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_immutable_original_history(base_experiment):
    """CRITICAL TEST: Verify original history is strictly immutable and reproduces identically."""
    # Capture complete deep copy of original state and events
    orig_events = copy.deepcopy(base_experiment.events)
    orig_snaps = copy.deepcopy(base_experiment.snapshots)
    orig_metrics = copy.deepcopy(base_experiment.metrics)

    # Apply aggressive counterfactual intervention (ablate an event)
    cf = create_ablation(base_experiment, event_id_or_timestep=1)

    # 1. Verify original experiment in memory was NOT mutated
    assert len(base_experiment.events) == len(orig_events)
    assert base_experiment.events == orig_events
    assert base_experiment.snapshots == orig_snaps
    assert base_experiment.metrics == orig_metrics

    # 2. Re-run original experiment from original config and assert bit-exact match
    rerun_cfg = ExperimentConfig.from_dict(base_experiment.config)
    rerun_exp = run_experiment(rerun_cfg)
    assert rerun_exp.snapshots[-1]["state_vector"] == orig_snaps[-1]["state_vector"]
    assert rerun_exp.metrics == orig_metrics


def test_intervention_remove_event(base_experiment):
    """Test REMOVE_EVENT intervention."""
    intv = create_remove_intervention(target_timestep=2)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.counterfactual_result["num_events"] == base_experiment.num_events - 1
    assert cf.divergence["first_divergence_step"] is not None
    assert cf.divergence["final_state_distance_l2"] > 0.0


def test_intervention_duplicate_event(base_experiment):
    """Test DUPLICATE_EVENT intervention."""
    intv = create_duplicate_intervention(target_timestep=1)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.counterfactual_result["num_events"] == base_experiment.num_events + 1
    assert cf.divergence["first_divergence_step"] is not None


def test_intervention_replace_event(base_experiment):
    """Test REPLACE_EVENT intervention."""
    replacement = {
        "concept_label": "obj_A",
        "attribute_label": "sym_PURPLE",
        "strength": 1.0,
    }
    intv = create_replace_intervention(replacement_spec=replacement, target_timestep=0)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.counterfactual_result["num_events"] == base_experiment.num_events
    assert cf.divergence["first_divergence_step"] == 1


def test_intervention_modify_event(base_experiment):
    """Test MODIFY_EVENT intervention via surgery."""
    cf = create_surgery(base_experiment, event_id_or_timestep=0, modifications={"strength": 0.2})

    assert cf.counterfactual_result["num_events"] == base_experiment.num_events
    assert cf.divergence["first_divergence_step"] == 1
    assert cf.divergence["final_state_distance_l2"] > 0.0


def test_intervention_move_event(base_experiment):
    """Test MOVE_EVENT intervention."""
    intv = create_move_intervention(destination_timestep=4, target_timestep=0)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.counterfactual_result["num_events"] == base_experiment.num_events
    assert cf.divergence["first_divergence_step"] is not None


def test_intervention_change_strength(base_experiment):
    """Test CHANGE_STRENGTH intervention."""
    intv = create_change_strength_intervention(new_strength=0.1, target_timestep=1)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.divergence["final_state_distance_l2"] > 0.0


def test_intervention_change_similarity(base_experiment):
    """Test CHANGE_SIMILARITY intervention."""
    intv = create_change_similarity_intervention(delta_similarity=0.5, target_timestep=1)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.status.value == "completed"


def test_intervention_reset_memory(base_experiment):
    """Test RESET_MEMORY intervention."""
    intv = create_reset_memory_intervention(target_timestep=2)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.divergence["final_state_distance_l2"] > 0.0
    assert cf.divergence["first_divergence_step"] is not None


def test_intervention_freeze_memory(base_experiment):
    """Test FREEZE_MEMORY intervention."""
    intv = create_freeze_memory_intervention(start_timestep=1, end_timestep=3)
    cf = run_counterfactual(base_experiment, intv)

    assert cf.divergence["first_divergence_step"] is not None


def test_intervention_inject_memory(base_experiment):
    """Test INJECT_MEMORY intervention."""
    intv = create_inject_memory_intervention(
        timestep=2,
        concept_label="obj_INJECTED",
        attribute_label="sym_RED",
        strength=1.0,
    )
    cf = run_counterfactual(base_experiment, intv)

    assert cf.counterfactual_result["num_events"] == base_experiment.num_events + 1
    assert cf.divergence["first_divergence_step"] is not None


def test_temporal_surgery_interventions(base_experiment):
    """Test TEMPORAL_DELETE, TEMPORAL_FREEZE, and TEMPORAL_SCALE."""
    del_intv = create_temporal_surgery_intervention(operation="delete", start_timestep=1, end_timestep=2)
    cf_del = run_counterfactual(base_experiment, del_intv)
    assert cf_del.counterfactual_result["num_events"] == base_experiment.num_events - 2

    scale_intv = create_temporal_surgery_intervention(operation="scale", start_timestep=1, end_timestep=2, factor=0.5)
    cf_scale = run_counterfactual(base_experiment, scale_intv)
    assert cf_scale.counterfactual_result["num_events"] == base_experiment.num_events


def test_intervention_validation_errors(base_experiment):
    """Test that invalid interventions raise explicit CounterfactualValidationError."""
    # Out of bounds timestep
    bad_intv = create_remove_intervention(target_timestep=999)
    with pytest.raises(CounterfactualValidationError):
        run_counterfactual(base_experiment, bad_intv)

    # Inverted temporal bounds
    bad_temporal = create_freeze_memory_intervention(start_timestep=4, end_timestep=1)
    with pytest.raises(CounterfactualValidationError):
        run_counterfactual(base_experiment, bad_temporal)
