"""Tests verifying that agents CANNOT bypass ExperimentValidator, CounterfactualValidator, or quotas (Phase 05)."""

import pytest

from agency.provenance.research_memory import ResearchMemory
from core.counterfactual.interventions import (
    CounterfactualValidator,
    create_ablation_intervention,
    create_change_strength_intervention,
)
from core.lab.validation import (
    ExperimentValidator,
    MAX_PARAMETER_COMBINATIONS,
    MAX_TRIALS,
)


def test_agent_cannot_bypass_parameter_bounds():
    """Verify that agent proposal with out-of-bounds parameter is strictly rejected."""
    # Propose invalid decay value > 1.0 (decay physical bound: [0.0, 1.0])
    invalid_proposal = {
        "parameter": "decay",
        "values": [0.1, 0.5, 2.5],  # 2.5 is out of bounds!
        "trials": 3,
    }

    res = ExperimentValidator.validate_parameter_sweep(
        parameter=invalid_proposal["parameter"],
        values=invalid_proposal["values"],
        trials=invalid_proposal["trials"],
    )

    assert res.valid is False
    assert any("exceeds max" in err.lower() or "out of range" in err.lower() or "2.5" in err for err in res.errors)


def test_agent_cannot_bypass_quota_limits():
    """Verify that agent proposal exceeding maximum combinations or trials is rejected."""
    # Exceed MAX_PARAMETER_COMBINATIONS
    too_many_values = list(range(MAX_PARAMETER_COMBINATIONS + 10))
    res_comb = ExperimentValidator.validate_parameter_sweep(
        parameter="memory_similarity",
        values=too_many_values,
        trials=1,
    )
    assert res_comb.valid is False
    assert any("exceeds maximum limit" in err for err in res_comb.errors)

    # Exceed MAX_TRIALS
    res_trials = ExperimentValidator.validate_parameter_sweep(
        parameter="memory_similarity",
        values=[0.2, 0.4],
        trials=MAX_TRIALS + 10,
    )
    assert res_trials.valid is False
    assert any("exceeds maximum allowed" in err for err in res_trials.errors)


def test_agent_cannot_bypass_counterfactual_validation():
    """Verify that agent cannot execute an invalid counterfactual intervention."""
    mock_events = [
        {"timestep": 0, "concept_label": "obj_A"},
        {"timestep": 1, "concept_label": "obj_B"},
    ]

    # Propose invalid ablation target timestep 10 (history only has 2 events)
    invalid_ablation = create_ablation_intervention(target_timestep=10)
    cf_res = CounterfactualValidator.validate(invalid_ablation, mock_events)

    assert cf_res.valid is False
    assert any("out of bounds" in err.lower() or "out of range" in err.lower() for err in cf_res.errors)


def test_failed_proposals_recorded_in_research_memory():
    """Verify that failed attempts are saved in ResearchMemory and never hidden."""
    memory = ResearchMemory(investigation_id="inv_test_safety")

    # Record rejected proposal
    memory.record_failed_attempt(
        stage="experiment_validation",
        config={"parameter": "decay", "values": [5.0]},
        error="Decay 5.0 exceeds max bound 1.0",
        hypothesis="Extreme decay test",
        lesson="Agent proposed invalid bounds; corrected by platform validator.",
    )

    assert len(memory.failed_attempts) == 1
    att = memory.failed_attempts[0]
    assert att.stage == "experiment_validation"
    assert "exceeds max" in att.error_message
    assert "platform validator" in att.lesson_learned
