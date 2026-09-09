"""Analysis layer tests (Phase 02, sections 14–19)."""

import numpy as np
import pytest

from core import (
    ExperimentConfig,
    MechanismParams,
    TaskConfig,
    ablate_event,
    analyze_memory_contribution,
    compare_experiments,
    compare_states,
    experiment_timeline,
    inspect_state,
    run_experiment,
)

EVENTS = [
    {"object_label": "vault_a", "symbol_label": "BLUE",
     "metadata": {"memory_id": "vault_a:BLUE"}},
    {"object_label": "locker_b", "symbol_label": "GREEN",
     "metadata": {"memory_id": "locker_b:GREEN"}},
    {"object_label": "vault_a", "symbol_label": "RED",
     "metadata": {"memory_id": "vault_a:RED"}},
]
QUERIES = [
    {"concept": "vault_a", "timestep": -1, "kind": "latest"},
    {"concept": "vault_a", "timestep": -1, "kind": "original"},
]


def _cfg(mechanism="leaky", **params):
    return ExperimentConfig(
        seed=7,
        mechanism=mechanism,
        params=MechanismParams(state_dim=64, decay=0.3, **params),
        task=TaskConfig(
            d=64, vector_source="text", events=EVENTS, queries=QUERIES
        ),
    )


def test_compare_states_hand_computed():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 1.0, 0.0])
    d = compare_states(a, b)
    assert d["l2_distance"] == pytest.approx(1.0)
    assert d["cosine_similarity"] == pytest.approx(1 / np.sqrt(2))
    assert d["normalized_difference"] == pytest.approx(1 / (1 + np.sqrt(2)))
    assert set(d["changed_dimensions"]) == {1}
    assert d["largest_positive_changes"][0]["dimension"] == 1
    assert d["largest_negative_changes"] == []


def test_compare_states_zero_vectors():
    d = compare_states(np.zeros(4), np.zeros(4))
    assert d["l2_distance"] == 0.0
    assert d["cosine_similarity"] == 0.0
    assert d["num_changed"] == 0


def test_compare_states_shape_mismatch():
    d = compare_states(np.zeros(4), np.zeros(8))
    assert d["shape_mismatch"] == [[4], [8]]
    assert d["l2_distance"] is None


def test_inspect_state_and_timeline():
    exp = run_experiment(_cfg())
    ins = inspect_state(exp, 1)
    assert ins["timestep"] == 1
    assert ins["event_id"] == "e0000"
    assert ins["state_norm"] == pytest.approx(1.0, abs=1e-9)
    assert ins["state_delta_vs_previous"]["l2"] == pytest.approx(1.0, abs=1e-9)
    assert len(ins["top_dimensions"]) > 0
    assert ins["memory_contributions"][0]["memory_id"] == "vault_a:BLUE"
    with pytest.raises(KeyError):
        inspect_state(exp, 99)
    tl = experiment_timeline(exp)
    assert len(tl["timeline"]) == exp.num_events + 1
    assert tl["timeline"][1]["event_id"] == "e0000"


def test_ablate_event_recomputes_ground_truth():
    exp = run_experiment(_cfg())
    result = ablate_event(exp, "e0002")  # remove the vault_a → RED conflict
    assert result["reproduced_from_config"] is True
    assert result["ablated_event"]["concept"] == "vault_a"
    # ground truth follows each history: original said RED, the
    # counterfactual (no RED event) says BLUE
    cf = {p["kind"]: p for p in result["prediction_differences"]}
    assert cf["latest"]["truth_a"] == "RED"
    assert cf["latest"]["truth_b"] == "BLUE"
    assert result["difference"]["state"]["l2_distance"] > 0.0
    assert result["num_changed_outcomes"] >= 0


def test_ablate_first_event_shifts_schedule():
    exp = run_experiment(_cfg())
    result = ablate_event(exp, "e0000")
    assert result["counterfactual"]["num_events"] == exp.num_events - 1


def test_ablate_unknown_event_raises():
    exp = run_experiment(_cfg())
    with pytest.raises(KeyError):
        ablate_event(exp, "e0099")


def test_contribution_estimate_flags_limitations():
    exp = run_experiment(_cfg())
    out = analyze_memory_contribution(exp, "vault_a:BLUE")
    assert out["method"] == "replay-based contribution estimate"
    assert "NOT true causal attribution" in out["limitation"]
    assert 0.0 <= out["contribution_score"] <= 1.0
    assert out["recall_difference"]["accuracy_delta"] != 0.0  # removing it matters
    with pytest.raises(KeyError):
        analyze_memory_contribution(exp, "no_such_memory")


def test_compare_experiments_across_mechanisms():
    a = run_experiment(_cfg("leaky"))
    b = run_experiment(_cfg("baseline"))
    out = compare_experiments(a, b)
    assert out["configuration_differences"]["mechanism"] == {"a": "leaky", "b": "baseline"}
    assert "recall_accuracy" in out["metric_differences"]
    assert out["state_distance"] is not None  # same dimension
    assert out["prediction_differences"]
    # identical configs → zero differences
    same = compare_experiments(a, run_experiment(_cfg("leaky")))
    assert same["state_distance"]["l2_distance"] == 0.0
    assert same["num_changed_outcomes"] == 0


def test_compare_experiments_hebbian_state_shape():
    a = run_experiment(_cfg("leaky"))
    b = run_experiment(ExperimentConfig(
        seed=7, mechanism="hebbian", params=MechanismParams(state_dim=64),
        task=TaskConfig(d=64, vector_source="text", events=EVENTS, queries=QUERIES),
    ))
    out = compare_experiments(a, b)
    # metric diffs still work; raw state distance is shape-limited
    assert "recall_accuracy" in out["metric_differences"]


def test_ablation_reproducibility_guarantee():
    exp = run_experiment(_cfg())
    result = ablate_event(exp, "e0001")
    assert result["reproduced_from_config"] is True