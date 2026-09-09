"""Experiment runner, determinism, metrics, and serialization tests."""

import json

import numpy as np
import pytest

from core import (
    ExperimentConfig,
    MechanismParams,
    TaskConfig,
    run_experiment,
    save_experiment,
    load_experiment,
)
from core.experiment import strip_non_deterministic
from core.metrics import METRIC_DEFINITIONS


def _cfg(**kw):
    params = kw.get("params", MechanismParams(state_dim=64))
    base = dict(
        seed=42,
        mechanism="baseline",
        params=params,
        task=TaskConfig(
            d=params.state_dim, n_objects=4, n_symbols=3, n_conflicts=2
        ),
    )
    base.update(kw)
    return ExperimentConfig(**base)


def test_same_seed_is_byte_identical():
    a = run_experiment(_cfg())
    b = run_experiment(_cfg())
    assert a.experiment_id != b.experiment_id  # ids are unique per run
    assert strip_non_deterministic(a.to_dict()) == strip_non_deterministic(b.to_dict())


def test_different_seed_changes_result():
    a = run_experiment(_cfg(seed=42))
    b = run_experiment(_cfg(seed=43))
    assert strip_non_deterministic(a.to_dict()) != strip_non_deterministic(b.to_dict())


def test_all_mechanisms_deterministic():
    for name in ("baseline", "leaky", "competitive", "hebbian", "interference"):
        cfg = _cfg(mechanism=name)
        a = run_experiment(cfg)
        b = run_experiment(cfg)
        assert strip_non_deterministic(a.to_dict()) == strip_non_deterministic(
            b.to_dict()
        ), name


@pytest.mark.parametrize("mechanism", ["baseline", "leaky", "competitive", "hebbian", "interference"])
def test_state_dimension_stays_fixed(mechanism):
    d = 48
    exp = run_experiment(
        _cfg(
            mechanism=mechanism,
            params=MechanismParams(state_dim=d),
            task=TaskConfig(d=d, n_objects=4, n_symbols=3, n_conflicts=2),
        )
    )
    expected = d * d if mechanism == "hebbian" else d
    assert len(exp.snapshots) == exp.num_events + 1  # initial + one per event
    for snap in exp.snapshots:
        assert len(snap["state_vector"]) == expected
        assert snap["shape"] == ([d, d] if mechanism == "hebbian" else [d])


def test_snapshot_contents():
    exp = run_experiment(_cfg())
    snap = exp.snapshots[1]  # after the first event
    for key in (
        "timestep",
        "event_id",
        "state_vector",
        "active_dimensions",
        "num_active",
        "sparsity",
        "params",
        "trace",
        "mechanism",
    ):
        assert key in snap
    assert snap["timestep"] == 1
    assert snap["event_id"] == exp.events[0]["id"]
    assert exp.snapshot_at(0)["event_id"] is None  # initial state


def test_metrics_hand_computed_single_pair():
    # One object, one symbol, one event, one end query.
    exp = run_experiment(
        _cfg(
            params=MechanismParams(state_dim=64),
            task=TaskConfig(d=64, n_objects=1, n_symbols=1, n_conflicts=0),
        )
    )
    m = exp.metrics
    assert m["recall_accuracy"] == pytest.approx(1.0)
    assert m["recall_quality"] == pytest.approx(1.0, abs=1e-9)
    assert m["error_rate"] == pytest.approx(0.0)
    assert m["mean_squared_error"] == pytest.approx(0.0, abs=1e-6)
    # x0 = 0, x1 = binding of two unit vectors → ||x1 - x0|| = 1
    assert m["update_magnitude"] == pytest.approx(1.0, abs=1e-9)
    # cos(0, x1) = 0 by convention
    assert m["state_similarity"] == pytest.approx(0.0)
    assert m["state_drift"] == pytest.approx(1.0)
    assert m["memory_retention"] == pytest.approx(1.0, abs=1e-9)
    # no conflicts → cross-talk fallback, still ~0
    assert m["interference_score"] == pytest.approx(0.0, abs=1e-6)
    assert m["recovery_score"] is None


def test_conflict_metrics_present():
    exp = run_experiment(_cfg())
    m = exp.metrics
    assert m["recovery_score"] is not None
    assert 0.0 <= m["interference_score"] <= 1.0
    assert m["details"]["conflict_keys"]
    assert set(m["details"]["per_conflict"]) == set(m["details"]["conflict_keys"])


def test_all_metrics_have_documented_definitions():
    exp = run_experiment(_cfg())
    for name in METRIC_DEFINITIONS:
        assert name in exp.metrics, name


def test_metrics_are_deterministic():
    a = run_experiment(_cfg()).metrics
    b = run_experiment(_cfg()).metrics
    assert a == b


def test_serialization_round_trip_json():
    exp = run_experiment(_cfg())
    data = json.loads(json.dumps(exp.to_dict()))
    from core import Experiment

    restored = Experiment.from_dict(data)
    assert restored.to_dict() == exp.to_dict()


def test_save_and_load(tmp_path):
    exp = run_experiment(_cfg())
    path = save_experiment(exp, tmp_path / "exp.json")
    loaded = load_experiment(path)
    assert loaded.to_dict() == exp.to_dict()


def test_update_strength_zero_freezes_state():
    exp = run_experiment(_cfg(params=MechanismParams(state_dim=64, update_strength=0.0)))
    norms = {s["norm"] for s in exp.snapshots}
    assert norms == {0.0}


def test_empty_events_run_cleanly():
    exp = run_experiment(
        ExperimentConfig(
            seed=1,
            mechanism="leaky",
            params=MechanismParams(state_dim=32, decay=0.5),
            task=TaskConfig(d=32, n_objects=2, n_symbols=2, events=[]),
        )
    )
    assert exp.num_events == 0
    assert len(exp.snapshots) == 1
    assert exp.metrics["update_magnitude"] == 0.0


def test_dim_one_runs():
    exp = run_experiment(
        _cfg(params=MechanismParams(state_dim=1), task=TaskConfig(d=1, n_objects=2, n_symbols=2, n_conflicts=1))
    )
    assert all(len(s["state_vector"]) == 1 for s in exp.snapshots)


def test_sparsity_zero_is_clamped():
    exp = run_experiment(
        _cfg(mechanism="competitive", params=MechanismParams(state_dim=64, sparsity=0.0))
    )
    assert exp.metrics["update_magnitude"] > 0.0


def test_unknown_mechanism_raises():
    with pytest.raises(KeyError):
        run_experiment(_cfg(mechanism="teleport"))


def test_high_similarity_degrades_recall():
    def run(rho):
        return run_experiment(
            _cfg(
                params=MechanismParams(state_dim=128),
                task=TaskConfig(
                    d=128, n_objects=4, n_symbols=3, n_conflicts=2, object_similarity=rho
                ),
            )
        ).metrics

    clean, noisy = run(0.0), run(0.9)
    assert noisy["recall_accuracy"] < clean["recall_accuracy"]


def test_input_noise_degrades_recall():
    def run(noise):
        return run_experiment(
            _cfg(
                params=MechanismParams(state_dim=128),
                task=TaskConfig(
                    d=128, n_objects=4, n_symbols=3, n_conflicts=2, input_noise=noise
                ),
            )
        ).metrics

    clean, noisy = run(0.0), run(1.0)
    assert noisy["recall_quality"] < clean["recall_quality"]


def test_extra_update_steps_amplify_decay():
    steps1 = run_experiment(
        _cfg(mechanism="leaky", params=MechanismParams(state_dim=64, decay=0.5), update_steps_per_event=1)
    ).metrics
    steps5 = run_experiment(
        _cfg(mechanism="leaky", params=MechanismParams(state_dim=64, decay=0.5), update_steps_per_event=5)
    ).metrics
    assert steps5["memory_retention"] < steps1["memory_retention"]