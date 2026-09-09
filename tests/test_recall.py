"""Recall quality and interference tests (the scientific core)."""

import numpy as np
import pytest

from core import ExperimentConfig, MechanismParams, TaskConfig, run_experiment
from core.events import Event
from core.mechanisms import BaselineAccumulation
from core.task import EventSpec, QuerySpec
from core.vectors import bind, cosine, correlated_flat_vectors, normalize, unbind


def _pairs(rng, d, n, rho):
    keys = correlated_flat_vectors(rng, n, d, rho)
    vals = [normalize(rng.standard_normal(d)) for _ in range(n)]
    return keys, vals


def test_single_pair_recall_is_exact_through_mechanism():
    rng = np.random.default_rng(0)
    d = 128
    keys, vals = _pairs(rng, d, 1, 0.0)
    mech = BaselineAccumulation(MechanismParams(state_dim=d), seed=1)
    mech.update(
        Event(timestep=0, concept_label="A", attribute_label="RED",
              key_vector=keys[0], value_vector=vals[0])
    )
    rec = mech.recall(keys[0])
    assert cosine(rec, vals[0]) == pytest.approx(1.0, abs=1e-9)


def test_similar_keys_cause_value_leakage():
    rng = np.random.default_rng(2)
    d = 256
    keys_hi, vals = _pairs(rng, d, 2, 0.9)
    keys_lo, _ = _pairs(rng, d, 2, 0.0)

    def leak(keys):
        mech = BaselineAccumulation(MechanismParams(state_dim=d), seed=3)
        for i in range(2):
            mech.update(
                Event(timestep=i, concept_label=f"o{i}", attribute_label=f"s{i}",
                      key_vector=keys[i], value_vector=vals[i])
            )
        v_hat = mech.recall(keys[0])
        return cosine(v_hat, vals[1])  # leakage of the competing value

    leak_hi, leak_lo = leak(keys_hi), leak(keys_lo)
    assert leak_hi > leak_lo + 0.3  # similar keys bleed the wrong value in


def test_interference_mechanism_saturates_repeated_writes():
    rng = np.random.default_rng(4)
    d = 256
    keys, vals = _pairs(rng, d, 1, 0.0)
    k, v = keys[0], vals[0]

    from core.mechanisms import InterferenceSensitive

    # γ = 1: re-writing the SAME memory erases its old projection first,
    # so the state saturates at ||b|| instead of accumulating (baseline → 2b)
    baseline = BaselineAccumulation(MechanismParams(state_dim=d), seed=5)
    inter = InterferenceSensitive(
        MechanismParams(state_dim=d, interference_strength=1.0), seed=5
    )
    for mech in (baseline, inter):
        for t in range(3):
            mech.update(
                Event(timestep=t, concept_label="A", attribute_label="RED",
                      key_vector=k, value_vector=v)
            )
    assert baseline.get_state_snapshot()["norm"] == pytest.approx(3.0, rel=1e-6)
    assert inter.get_state_snapshot()["norm"] == pytest.approx(1.0, rel=1e-6)

    # orthogonal content is barely erased (interference requires alignment):
    # two orthogonal bindings coexist at norm ≈ √2, like superposition
    rng2 = np.random.default_rng(6)
    _, vals2 = _pairs(rng2, d, 1, 0.0)
    inter2 = InterferenceSensitive(
        MechanismParams(state_dim=d, interference_strength=1.0), seed=7
    )
    inter2.update(
        Event(timestep=0, concept_label="A", attribute_label="RED",
              key_vector=k, value_vector=v)
    )
    inter2.update(
        Event(timestep=1, concept_label="A", attribute_label="BLUE",
              key_vector=k, value_vector=vals2[0])
    )
    assert inter2.get_state_snapshot()["norm"] == pytest.approx(
        np.sqrt(2.0), rel=0.02
    )


def test_conflicting_memories_latest_wins_for_leaky():
    cfg = ExperimentConfig(
        seed=21,
        mechanism="leaky",
        params=MechanismParams(state_dim=128, decay=0.8),
        task=TaskConfig(d=128, n_objects=1, n_symbols=2, n_conflicts=1),
    )
    exp = run_experiment(cfg)
    latest = [q for q in exp.queries if q["kind"] == "latest"]
    assert all(q["correctness"] for q in latest)  # recency wins
    original = [q for q in exp.queries if q["kind"] == "original"]
    # decay should have faded the old binding: quality is near zero
    assert original[0]["quality"] < 0.3


def test_baseline_ties_conflicts_no_recency():
    """Superposition stores both sides of a conflict with equal strength:
    the readout cannot prefer the newer binding (no recency mechanism), so
    'latest' and 'original' probes retrieve both values equally well."""
    cfg = ExperimentConfig(
        seed=21,
        mechanism="baseline",
        params=MechanismParams(state_dim=128),
        task=TaskConfig(d=128, n_objects=1, n_symbols=2, n_conflicts=1),
    )
    exp = run_experiment(cfg)
    latest = [q for q in exp.queries if q["kind"] == "latest"][0]
    original = [q for q in exp.queries if q["kind"] == "original"][0]
    # both bindings are equally retrievable: quality is symmetric
    assert latest["quality"] == pytest.approx(original["quality"], abs=0.05)
    assert latest["quality"] > 0.3  # and both are well above chance


def test_leaky_interference_lower_than_baseline():
    base_cfg = ExperimentConfig(
        seed=31,
        mechanism="baseline",
        params=MechanismParams(state_dim=128),
        task=TaskConfig(d=128, n_objects=4, n_symbols=3, n_conflicts=2),
    )
    leaky_cfg = ExperimentConfig(
        seed=31,
        mechanism="leaky",
        params=MechanismParams(state_dim=128, decay=0.5),
        task=TaskConfig(d=128, n_objects=4, n_symbols=3, n_conflicts=2),
    )
    base = run_experiment(base_cfg).metrics
    leaky = run_experiment(leaky_cfg).metrics
    assert leaky["interference_score"] < base["interference_score"]


def test_query_timing_changes_result():
    # Ask about A right after its conflict vs. after many unrelated events:
    # decay erodes the answer over time.
    task = TaskConfig(
        d=128,
        n_objects=5,
        n_symbols=3,
        n_conflicts=1,
        queries=[
            QuerySpec("obj_A", timestep=1, kind="latest"),
            QuerySpec("obj_A", timestep=-1, kind="latest"),
        ],
        seed=41,
    )
    cfg = ExperimentConfig(
        seed=41,
        mechanism="leaky",
        params=MechanismParams(state_dim=128, decay=0.7),
        task=task,
    )
    exp = run_experiment(cfg)
    by_ts = {q["timestep"]: q for q in exp.queries}
    early, late = by_ts[1], by_ts[max(by_ts)]
    assert early["quality"] > late["quality"]