"""The 7 canonical demonstrations required for Phase 04 Counterfactual Memory Archaeology."""

import pytest
import numpy as np

from core.counterfactual import (
    compare_multiple_histories,
    create_ablation,
    create_change_strength_intervention,
    create_modify_intervention,
    create_surgery,
    diff_histories,
    estimate_event_contribution,
    find_minimal_intervention,
    reproduce_counterfactual,
    run_counterfactual,
)
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig


@pytest.fixture
def demo_experiment():
    """Deterministic 8-event memory history for the demonstrations."""
    cfg = ExperimentConfig(
        seed=123,
        mechanism="leaky",
        params=MechanismParams(decay=0.15, update_strength=0.9),
        task=TaskConfig(
            seed=123,
            n_objects=4,
            n_symbols=5,
            n_conflicts=3,
            cycles=1,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_demo_1_remove_a_memory(demo_experiment):
    """DEMO 1 — REMOVE A MEMORY: Take a history, remove one event, replay, show downstream divergence."""
    # Target event at timestep 2
    orig_event = demo_experiment.events[2]

    # Perform ablation
    cf = create_ablation(demo_experiment, event_id_or_timestep=2)

    # Assertions
    assert cf.counterfactual_result["num_events"] == demo_experiment.num_events - 1
    assert cf.divergence["first_divergence_step"] is not None
    assert cf.divergence["first_divergence_step"] <= 3
    assert cf.divergence["final_state_distance_l2"] > 0.0

    # Downstream divergence timeline must be tracked
    timeline = cf.divergence["timeline"]
    assert len(timeline) > 0
    # Before the ablated event, states must match
    assert timeline[0]["state_distance_l2"] == pytest.approx(0.0, abs=1e-9)


def test_demo_2_memory_surgery(demo_experiment):
    """DEMO 2 — MEMORY SURGERY: Increase the strength of one memory, replay, compare."""
    # Target event at timestep 1: boost strength from 1.0 to 2.5
    intv = create_change_strength_intervention(new_strength=2.5, target_timestep=1)
    cf = run_counterfactual(demo_experiment, intv, title="Strength Boost Surgery")

    # Divergence begins at snapshot 2 (after event 1 write)
    assert cf.divergence["first_divergence_step"] == 2
    assert cf.divergence["final_state_distance_l2"] > 0.0

    # Final state norm changed
    norm_orig = cf.original_result["final_state_norm"]
    norm_cf = cf.counterfactual_result["final_state_norm"]
    assert norm_cf != norm_orig


def test_demo_3_alternate_histories(demo_experiment):
    """DEMO 3 — ALTERNATE HISTORIES: Create three alternate histories, compare them against the original."""
    # Alternate History 1: Remove event 1
    cf1 = create_ablation(demo_experiment, event_id_or_timestep=1, title="Branch 1: Ablate E1")

    # Alternate History 2: Modify event 2 strength to 0.1
    cf2 = create_surgery(demo_experiment, event_id_or_timestep=2, modifications={"strength": 0.1}, title="Branch 2: Dampen E2")

    # Alternate History 3: Boost event 3 strength to 2.0
    intv3 = create_change_strength_intervention(new_strength=2.0, target_timestep=3)
    cf3 = run_counterfactual(demo_experiment, intv3, title="Branch 3: Boost E3")

    # Compare the 3 branches against original
    comparison = compare_multiple_histories([
        demo_experiment,
        {"experiment_id": cf1.counterfactual_id, "metrics": cf1.counterfactual_result["metrics"], "events": demo_experiment.events[:-1]},
        {"experiment_id": cf2.counterfactual_id, "metrics": cf2.counterfactual_result["metrics"], "events": demo_experiment.events},
        {"experiment_id": cf3.counterfactual_id, "metrics": cf3.counterfactual_result["metrics"], "events": demo_experiment.events},
    ])

    assert comparison["total_timelines_compared"] == 4
    assert len(comparison["branch_comparisons"]) == 3


def test_demo_4_contribution_analysis(demo_experiment):
    """DEMO 4 — CONTRIBUTION ANALYSIS: Find which historical events have the largest counterfactual effect on a selected metric."""
    contrib = estimate_event_contribution(
        experiment=demo_experiment,
        target_metric="interference_score",
    )

    ranked = contrib["ranked_contributions"]
    assert len(ranked) >= 4

    # The top-ranked event must have the highest effect size
    top_event = ranked[0]
    second_event = ranked[1]
    assert top_event["effect_size"] >= second_event["effect_size"]
    assert top_event["rank"] == 1
    assert "forensic_summary" in contrib


def test_demo_5_minimal_intervention(demo_experiment):
    """DEMO 5 — MINIMAL INTERVENTION: Give a target improvement, find the smallest tested intervention achieving it."""
    target_metric = "interference_score"
    target_improvement = 0.02

    res = find_minimal_intervention(
        experiment=demo_experiment,
        target_metric=target_metric,
        target_improvement=target_improvement,
        target_direction="decrease",
    )

    if res["success"]:
        assert res["observed_improvement"] >= target_improvement
        assert res["magnitude"] is not None
        assert res["minimal_intervention"] is not None
    else:
        assert res["explanation"] is not None


def test_demo_6_reproduction(demo_experiment):
    """DEMO 6 — REPRODUCTION: Reproduce a saved counterfactual, verify deterministic bit-exact match within tolerance."""
    # 1. Run counterfactual
    intv = create_change_strength_intervention(new_strength=0.3, target_timestep=2)
    orig_cf = run_counterfactual(demo_experiment, intv)

    # 2. Extract metrics
    expected_metrics = orig_cf.counterfactual_result["metrics"]

    # 3. Reproduce and verify
    repro = reproduce_counterfactual(
        original_experiment=demo_experiment,
        intervention=intv,
        expected_metrics=expected_metrics,
        tolerance=1e-9,
    )

    assert repro["reproduced"] is True
    assert repro["exact_match"] is True
    assert all(m["matched"] for m in repro["metric_matches"].values())


def test_demo_7_divergence_propagation(demo_experiment):
    """DEMO 7 — DIVERGENCE PROPAGATION: Show how a small historical change evolves through later events."""
    # Small modification at step 1: reduce strength slightly from 1.0 to 0.7
    intv = create_change_strength_intervention(new_strength=0.7, target_timestep=1)
    cf = run_counterfactual(demo_experiment, intv)

    div = cf.divergence
    timeline = div["timeline"]

    # Check propagation tracking
    assert len(timeline) == len(demo_experiment.snapshots)

    # Step 0 (initial zero vector): identical
    assert timeline[0]["state_distance_l2"] == pytest.approx(0.0, abs=1e-9)

    # Step 1 (after event 0): identical
    assert timeline[1]["state_distance_l2"] == pytest.approx(0.0, abs=1e-9)

    # Step 2 (after event 1 write): perturbation introduced
    assert timeline[2]["state_distance_l2"] > 0.0

    # Steps 2+: divergence evolves and propagates through later writes
    distances = [t["state_distance_l2"] for t in timeline]
    assert max(distances) > 0.0
    assert div["classification"] is not None
    assert div["cumulative_divergence"] > 0.0
