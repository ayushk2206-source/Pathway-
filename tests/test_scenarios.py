"""Scenario + batch generator tests (Phase 02, sections 9–13, 20)."""

import pytest

from core import (
    MechanismParams,
    SCENARIOS,
    capacity_sweep,
    collision_report,
    interference_matrix,
    order_comparison,
    retention_curve,
    run_scenario,
    strength_sweep,
)


def test_all_scenarios_are_registered_with_objectives():
    expected = {
        "simple_memory",
        "conflicting_memory",
        "long_horizon_recall",
        "memory_collision",
        "forgetting",
        "order_sensitivity",
        "capacity_stress",
        "repeated_memory",
        "noisy_memory",
        "interleaved_memories",
    }
    assert set(SCENARIOS) == expected
    for s in SCENARIOS.values():
        assert s.description
        assert s.learning_objective
        assert s.kind in ("experiment", "report")


@pytest.mark.parametrize(
    "name",
    [
        "simple_memory",
        "conflicting_memory",
        "long_horizon_recall",
        "forgetting",
        "repeated_memory",
        "noisy_memory",
        "interleaved_memories",
    ],
)
def test_experiment_scenarios_run(name):
    out = run_scenario(name)
    exp = out["experiment"]
    assert exp["mechanism"]
    assert len(exp["snapshots"]) == len(exp["events"]) + 1
    assert "recall_accuracy" in exp["metrics"]
    # scenario experiments are deterministic
    again = run_scenario(name)
    assert again["experiment"]["metrics"] == exp["metrics"]


@pytest.mark.parametrize("name", ["memory_collision", "order_sensitivity", "capacity_stress"])
def test_report_scenarios_run(name):
    out = run_scenario(name)
    assert out["report"] is not None
    assert out["experiment"] is None or out["report"]


def test_simple_memory_exact_recall():
    out = run_scenario("simple_memory")
    assert out["experiment"]["metrics"]["recall_accuracy"] == 1.0


def test_conflicting_memory_has_original_probe():
    out = run_scenario("conflicting_memory")
    kinds = {q["kind"] for q in out["experiment"]["queries"]}
    assert kinds == {"latest", "original"}


def test_repeated_memory_strengthens():
    once = run_scenario("repeated_memory", {"repetitions": 1})
    thrice = run_scenario("repeated_memory", {"repetitions": 3})
    assert thrice["experiment"]["metrics"]["memory_retention"] >= once["experiment"]["metrics"]["memory_retention"]


def test_retention_curve_declines_with_lag():
    rc = retention_curve(
        seed=11, mechanism="leaky",
        params=MechanismParams(state_dim=64, decay=0.3),
        lags=[0, 5, 10, 20],
    )
    assert [row["steps"] for row in rc["data"]] == [0, 5, 10, 20]
    retentions = [row["retention"] for row in rc["data"]]
    assert retentions[0] == pytest.approx(1.0, abs=1e-6)  # nothing intervened
    assert retentions[-1] < retentions[0]  # intervening events erode it


def test_retention_curve_deterministic():
    a = retention_curve(seed=11, lags=[0, 5])
    b = retention_curve(seed=11, lags=[0, 5])
    assert a["data"] == b["data"]


def test_capacity_sweep_dimension_matters():
    cs = capacity_sweep(
        seed=12, mechanism="baseline",
        params=MechanismParams(state_dim=128),
        dimensions=[8, 16, 64],
    )
    assert [row["d"] for row in cs["data"]] == [8, 16, 64]
    small = cs["data"][0]
    large = cs["data"][-1]
    assert small["d"] == 8 and large["d"] == 64
    # more capacity must not hurt recall
    assert large["recall_accuracy"] >= small["recall_accuracy"]


def test_order_comparison_states_differ():
    oc = order_comparison(
        seed=13, mechanism="leaky",
        params=MechanismParams(state_dim=64, decay=0.2),
    )
    assert len(oc["orders"]) == 3
    assert len(oc["pairwise_differences"]) == 3
    assert oc["pairwise_differences"][0]["l2_distance"] > 0.0  # reversed order changes state


def test_strength_sweep_strength_matters():
    ss = strength_sweep(
        seed=14, mechanism="baseline",
        params=MechanismParams(state_dim=64),
        strengths=[0.1, 1.0],
    )
    weak, strong = ss["data"][0], ss["data"][-1]
    assert weak["final_state_norm"] < strong["final_state_norm"]
    assert weak["update_magnitude"] < strong["update_magnitude"]


def test_interference_matrix_grid_real_values():
    im = interference_matrix(
        seed=15, mechanism="baseline",
        params=MechanismParams(state_dim=64),
        similarities=[0.0, 0.9],
        update_strengths=[0.2, 1.0],
    )
    assert len(im["data"]) == 4
    for cell in im["data"]:
        assert 0.0 <= cell["interference"] <= 1.0
        assert 0.0 <= cell["retention"] <= 1.0
    # similar keys + strong interfering write ⇒ more leakage
    dissim_weak = next(c for c in im["data"] if c["similarity"] < 0.1 and c["update_strength"] == 0.2)
    sim_strong = next(c for c in im["data"] if c["similarity"] > 0.8 and c["update_strength"] == 1.0)
    assert sim_strong["interference"] > dissim_weak["interference"]


def test_collision_report_structure():
    rep = collision_report(
        seed=16, mechanism="interference",
        params=MechanismParams(state_dim=64, interference_strength=0.8),
        concept="enclosure_7", value_a="TIGER", value_b="LION",
        similarity=0.8,
    )
    for key in (
        "memory_a", "memory_b", "representation_similarity",
        "collision_intensity", "state_before", "state_after_a",
        "state_after_b", "recall", "retention", "interference_score", "experiment",
    ):
        assert key in rep
    assert rep["representation_similarity"]["key_similarity"] > 0.6
    assert rep["retention"]["original_memory"] >= 0.0
    assert rep["interference_score"]["measured"] >= 0.0
    # the interference mechanism erases aligned content → original retention drops
    assert rep["retention"]["original_memory"] < 1.0


def test_collision_hard_same_key():
    rep = collision_report(
        seed=16, mechanism="baseline",
        params=MechanismParams(state_dim=64),
        concept="enclosure_7", value_a="TIGER", value_b="LION",
        similarity=1.0,
    )
    assert rep["representation_similarity"]["hard_collision_same_key"] is True
    assert rep["representation_similarity"]["key_similarity"] == 1.0


def test_unknown_scenario_raises():
    with pytest.raises(KeyError):
        run_scenario("teleport")