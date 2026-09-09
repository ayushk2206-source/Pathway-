"""Tests for What-If search, minimal intervention, and contribution analysis (Phase 04)."""

import pytest

from core.counterfactual import (
    estimate_event_contribution,
    find_minimal_intervention,
    search_counterfactuals,
)
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig


@pytest.fixture
def conflicting_experiment():
    """Experiment with high interference to evaluate interventions and contribution."""
    cfg = ExperimentConfig(
        seed=77,
        mechanism="leaky",
        params=MechanismParams(decay=0.1, update_strength=0.9),
        task=TaskConfig(
            seed=77,
            n_objects=3,
            n_symbols=4,
            n_conflicts=3,
            cycles=1,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_search_counterfactuals_finds_improvements(conflicting_experiment):
    """Verify search_counterfactuals identifies and ranks candidate interventions."""
    res = search_counterfactuals(
        experiment=conflicting_experiment,
        target_metric="interference_score",
        target_direction="decrease",
        max_candidates=20,
    )

    assert res["target_metric"] == "interference_score"
    assert res["total_evaluated"] > 0
    ranked = res["ranked_candidates"]
    assert len(ranked) > 0

    # Ensure ranked list is sorted by improvement descending
    improvements = [r["improvement"] for r in ranked]
    for i in range(len(improvements) - 1):
        assert improvements[i] >= improvements[i + 1]


def test_find_minimal_intervention_succeeds(conflicting_experiment):
    """Verify find_minimal_intervention finds lowest-magnitude intervention meeting threshold."""
    target_metric = "interference_score"
    target_improvement = 0.05

    res = find_minimal_intervention(
        experiment=conflicting_experiment,
        target_metric=target_metric,
        target_improvement=target_improvement,
        target_direction="decrease",
    )

    if res["success"]:
        assert res["observed_improvement"] >= target_improvement
        assert res["magnitude"] is not None
        assert res["magnitude"] <= 1.0
        assert "achieving an improvement" in res["explanation"]
    else:
        assert "No tested intervention" in res["explanation"]


def test_estimate_event_contribution_ranks_events(conflicting_experiment):
    """Verify forensic forgetting reconstruction ranks events by counterfactual impact."""
    contrib = estimate_event_contribution(
        experiment=conflicting_experiment,
        target_metric="interference_score",
        max_candidates=10,
    )

    assert contrib["target_metric"] == "interference_score"
    assert contrib["total_events_evaluated"] > 0
    assert "causal_safety_disclaimer" in contrib

    ranked = contrib["ranked_contributions"]
    assert len(ranked) > 0

    # Verify ranks are sequential 1, 2, 3...
    for idx, r in enumerate(ranked, start=1):
        assert r["rank"] == idx

    # Verify effect size is sorted descending
    effects = [r["effect_size"] for r in ranked]
    for i in range(len(effects) - 1):
        assert effects[i] >= effects[i + 1]
