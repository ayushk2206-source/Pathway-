"""Vector mathematics and binding/unbinding tests."""

import numpy as np
import pytest

from core.vectors import (
    bind,
    correlated_flat_vectors,
    correlated_vectors,
    cosine,
    flat_spectrum_vector,
    normalize,
    reverse,
    top_k_mask,
    unbind,
)


def test_reverse_is_involution():
    rng = np.random.default_rng(0)
    v = rng.standard_normal(8)
    assert np.allclose(reverse(reverse(v)), v)


def test_bind_commutative():
    rng = np.random.default_rng(1)
    a = normalize(rng.standard_normal(16))
    b = normalize(rng.standard_normal(16))
    assert np.allclose(bind(a, b), bind(b, a))


def test_bind_delta_key_is_identity():
    rng = np.random.default_rng(2)
    v = normalize(rng.standard_normal(16))
    e0 = np.zeros(16)
    e0[0] = 1.0
    assert np.allclose(bind(e0, v), v)


def test_flat_key_unbind_is_exact():
    rng = np.random.default_rng(3)
    d = 64
    k = flat_spectrum_vector(rng, d)
    v = normalize(rng.standard_normal(d))
    x = bind(k, v)
    rec = unbind(x, k)
    assert np.allclose(rec, v, atol=1e-9)
    assert cosine(rec, v) == pytest.approx(1.0, abs=1e-9)


def test_wrong_key_returns_nothing():
    rng = np.random.default_rng(4)
    d = 64
    k1, k2 = flat_spectrum_vector(rng, d), flat_spectrum_vector(rng, d)
    v = normalize(rng.standard_normal(d))
    rec = unbind(bind(k1, v), k2)
    assert cosine(rec, v) < 0.3  # random cross-talk, not the value


def test_superposition_cross_talk_degrades_with_pairs():
    rng = np.random.default_rng(5)
    d = 128
    keys = [flat_spectrum_vector(rng, d) for _ in range(6)]
    vals = [normalize(rng.standard_normal(d)) for _ in range(6)]
    # quality of pair 0 with n stored pairs
    qualities = []
    x = np.zeros(d)
    for i in range(6):
        x = x + bind(keys[i], vals[i])
        qualities.append(cosine(unbind(x, keys[0]), vals[0]))
    assert qualities[0] == pytest.approx(1.0, abs=1e-9)
    assert qualities[-1] < qualities[1]  # more pairs → noisier readout


def test_correlated_flat_vectors_control_similarity():
    rng = np.random.default_rng(6)
    d = 256
    for target in (0.0, 0.5, 0.9):
        keys = correlated_flat_vectors(rng, 8, d, target)
        sims = [cosine(keys[i], keys[j]) for i in range(8) for j in range(i)]
        assert abs(float(np.mean(sims)) - target) < 0.12
        # flatness is preserved for every key: single-pair recall exact
        v = normalize(rng.standard_normal(d))
        x = bind(keys[0], v)
        assert cosine(unbind(x, keys[0]), v) == pytest.approx(1.0, abs=1e-9)


def test_correlated_vectors_control_similarity():
    rng = np.random.default_rng(7)
    d = 256
    vals = correlated_vectors(rng, 8, d, 0.7)
    sims = [cosine(vals[i], vals[j]) for i in range(8) for j in range(i)]
    assert abs(float(np.mean(sims)) - 0.7) < 0.12


def test_top_k_mask_counts_and_tiebreak():
    rng = np.random.default_rng(8)
    x = rng.standard_normal(32)
    mask = top_k_mask(x, 5)
    assert int(mask.sum()) == 5
    # ties break by lower index deterministically
    x2 = np.array([1.0, -1.0, 0.5, 0.5])
    m = top_k_mask(x2, 2)
    assert m.tolist() == [True, True, False, False]
    assert np.array_equal(top_k_mask(x2, 2), top_k_mask(x2, 2))


def test_top_k_mask_clamps():
    x = np.ones(8)
    assert top_k_mask(x, 0).sum() == 1
    assert top_k_mask(x, 100).sum() == 8