"""Mechanism update rules — hand-computed expectations.

Keys here are one-hot (delta) vectors so that ``bind(e0, v) == v`` exactly
(see ``test_vectors``), making every expectation trivially checkable by
hand: with a delta key the binding IS the value vector.
"""

import numpy as np
import pytest

from core.events import Event
from core.mechanisms import (
    BaselineAccumulation,
    CompetitiveUpdate,
    HebbianAssociative,
    InterferenceSensitive,
    LeakyRecurrent,
    MechanismParams,
    create_mechanism,
)
from core.vectors import cosine, normalize


def _delta(d: int, i: int = 0) -> np.ndarray:
    e = np.zeros(d)
    e[i] = 1.0
    return e


def _event(t: int, key: np.ndarray, value: np.ndarray, **kw) -> Event:
    return Event(
        timestep=t,
        concept_label=f"o{t}",
        attribute_label=f"s{t}",
        key_vector=key,
        value_vector=value,
        **kw,
    )


def test_baseline_accumulates_exactly():
    d = 8
    mech = BaselineAccumulation(MechanismParams(state_dim=d), seed=1)
    v1 = normalize(np.arange(1, d + 1, dtype=float))
    v2 = normalize(np.arange(d, 0, -1, dtype=float))
    mech.update(_event(0, _delta(d), v1))
    assert np.allclose(mech.state_vector(), v1)  # gain 1, delta key
    mech.update(_event(1, _delta(d, 1), v2))
    # e1 ⊛ v2 = roll(v2, 1): a delta key shifts the value, exactly
    assert np.allclose(mech.state_vector(), v1 + np.roll(v2, 1))


def test_baseline_update_strength_scales_write():
    d = 8
    mech = BaselineAccumulation(
        MechanismParams(state_dim=d, update_strength=0.5, memory_strength=2.0), seed=1
    )
    v = normalize(np.arange(1, d + 1, dtype=float))
    mech.update(_event(0, _delta(d), v, importance=0.5, strength=0.5))
    # gain = 0.5 * 2.0 * 0.5 * 0.5 = 0.25
    assert np.allclose(mech.state_vector(), 0.25 * v)


def test_leaky_decay_exact():
    d = 8
    mech = LeakyRecurrent(MechanismParams(state_dim=d, decay=0.25), seed=2)
    v1 = normalize(np.arange(1, d + 1, dtype=float))
    v2 = normalize(np.arange(d, 0, -1, dtype=float))
    mech.update(_event(0, _delta(d), v1))
    assert np.allclose(mech.state_vector(), v1)
    mech.update(_event(1, _delta(d, 1), v2))
    assert np.allclose(mech.state_vector(), 0.75 * v1 + np.roll(v2, 1))


def test_leaky_step_no_input_forgets():
    d = 8
    mech = LeakyRecurrent(MechanismParams(state_dim=d, decay=0.5), seed=3)
    v = normalize(np.arange(1, d + 1, dtype=float))
    mech.update(_event(0, _delta(d), v))
    mech.step_no_input(3)
    assert np.allclose(mech.state_vector(), 0.5**3 * v)


def test_competitive_keeps_top_k():
    d = 8
    k = 2
    mech = CompetitiveUpdate(MechanismParams(state_dim=d, sparsity=k / d), seed=4)
    v = np.array([1.0, -2.0, 0.5, 3.0, -0.1, 0.0, 2.5, -0.4])
    mech.update(_event(0, _delta(d), v))
    state = mech.state_vector()
    assert int(np.count_nonzero(state)) == k
    assert set(np.where(state != 0)[0]) == {3, 6}  # |3.0| and |2.5| win
    assert np.allclose(state[[3, 6]], [3.0, 2.5])


def test_hebbian_outer_product_and_recall():
    d = 8
    mech = HebbianAssociative(MechanismParams(state_dim=d), seed=5)
    v1 = normalize(np.arange(1, d + 1, dtype=float))
    k1 = normalize(np.arange(d, 0, -1, dtype=float))
    mech.update(_event(0, k1, v1))
    M = mech._state
    assert np.allclose(M, np.outer(v1, k1))
    rec = mech.recall(k1)
    assert np.allclose(rec, v1 * float(k1 @ k1))  # M @ k1 = v1 (k1·k1)


def test_hebbian_state_shape_is_fixed():
    d = 8
    mech = HebbianAssociative(MechanismParams(state_dim=d), seed=6)
    mech.update(_event(0, _delta(d), normalize(np.ones(d))))
    assert mech.state_vector().shape == (d * d,)
    assert mech.get_state_snapshot()["shape"] == [d, d]


def test_interference_erases_aligned_content_exactly():
    d = 8
    mech = InterferenceSensitive(
        MechanismParams(state_dim=d, interference_strength=1.0), seed=7
    )
    v1 = normalize(np.arange(1, d + 1, dtype=float))
    v2 = normalize(np.arange(d, 0, -1, dtype=float))
    mech.update(_event(0, _delta(d), v1))
    mech.update(_event(1, _delta(d, 1), v2))
    b2 = np.roll(v2, 1)  # e1 ⊛ v2 = roll(v2, 1)
    b2_hat = b2 / np.linalg.norm(b2)
    # the state's component along the second binding is exactly ||b2||
    assert float(np.dot(mech.state_vector(), b2_hat)) == pytest.approx(
        float(np.linalg.norm(b2))
    )


def test_interference_gamma_zero_is_baseline():
    d = 8
    g0 = InterferenceSensitive(MechanismParams(state_dim=d, interference_strength=0.0), seed=8)
    g1 = BaselineAccumulation(MechanismParams(state_dim=d), seed=8)
    for t in range(3):
        v = normalize(np.arange(1, d + 1, dtype=float) + t)
        g0.update(_event(t, _delta(d, t % d), v))
        g1.update(_event(t, _delta(d, t % d), v))
    assert np.allclose(g0.state_vector(), g1.state_vector())


def test_baseline_commutative_leaky_is_not():
    d = 8
    v1 = normalize(np.arange(1, d + 1, dtype=float))
    v2 = normalize(np.arange(d, 0, -1, dtype=float))
    e1, e2 = _event(0, _delta(d), v1), _event(1, _delta(d, 1), v2)

    b_ab = BaselineAccumulation(MechanismParams(state_dim=d), seed=9)
    b_ba = BaselineAccumulation(MechanismParams(state_dim=d), seed=9)
    for mech, order in ((b_ab, (e1, e2)), (b_ba, (e2, e1))):
        for e in order:
            mech.update(e)
    assert np.allclose(b_ab.state_vector(), b_ba.state_vector())

    l_ab = LeakyRecurrent(MechanismParams(state_dim=d, decay=0.2), seed=9)
    l_ba = LeakyRecurrent(MechanismParams(state_dim=d, decay=0.2), seed=9)
    for mech, order in ((l_ab, (e1, e2)), (l_ba, (e2, e1))):
        for e in order:
            mech.update(e)
    assert not np.allclose(l_ab.state_vector(), l_ba.state_vector())


def test_restore_state_round_trip():
    d = 8
    mech = LeakyRecurrent(MechanismParams(state_dim=d, decay=0.1), seed=10)
    v = normalize(np.arange(1, d + 1, dtype=float))
    mech.update(_event(0, _delta(d), v))
    snap = mech.get_state_snapshot()
    mech2 = create_mechanism("leaky", MechanismParams(state_dim=d, decay=0.1), seed=10)
    mech2.restore_state(snap["state_vector"])
    assert np.allclose(mech2.state_vector(), mech.state_vector())
    assert cosine(mech2.recall(_delta(d)), v) == pytest.approx(1.0, abs=1e-9)


def test_update_returns_explanatory_trace():
    d = 8
    mech = InterferenceSensitive(
        MechanismParams(state_dim=d, interference_strength=0.5), seed=11
    )
    trace = mech.update(_event(0, _delta(d), normalize(np.ones(d))))
    for key in (
        "mechanism",
        "write_gain",
        "interference_strength",
        "projection_onto_new_binding",
        "note",
    ):
        assert key in trace


def test_input_noise_is_deterministic_per_event():
    d = 32
    v = normalize(np.arange(1, d + 1, dtype=float))
    traces = []
    for _ in range(2):
        mech = BaselineAccumulation(
            MechanismParams(state_dim=d, input_noise=0.5), seed=12
        )
        mech.update(_event(3, _delta(d), v))  # same timestep → same noise
        traces.append(mech.state_vector().copy())
    assert np.allclose(traces[0], traces[1])
    # different timestep → different noise
    mech2 = BaselineAccumulation(MechanismParams(state_dim=d, input_noise=0.5), seed=12)
    mech2.update(_event(4, _delta(d), v))
    assert not np.allclose(traces[0], mech2.state_vector())