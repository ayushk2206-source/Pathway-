"""Deterministic text encoder tests (Phase 02, section 1)."""

import numpy as np
import pytest

from core.encoder import (
    encode_concept_vector,
    encode_texts,
    encode_value_vector,
)
from core.vectors import bind, cosine, unbind


def test_encode_is_reproducible_from_text_seed_dim():
    a = encode_concept_vector("capital_of_france", seed=5, d=64)
    b = encode_concept_vector("capital_of_france", seed=5, d=64)
    assert np.array_equal(a, b)
    # same text, different seed → different vector
    assert not np.array_equal(a, encode_concept_vector("capital_of_france", seed=6, d=64))
    # same text, different dimension → different vector
    assert encode_concept_vector("capital_of_france", seed=5, d=128).shape == (128,)
    assert not np.allclose(a, encode_concept_vector("capital_of_france", seed=5, d=128)[:64])


def test_different_texts_get_different_vectors():
    a = encode_concept_vector("alpha", seed=1, d=64)
    b = encode_concept_vector("beta", seed=1, d=64)
    assert cosine(a, b) < 0.3  # no semantic similarity (synthetic encoder)


def test_concept_keys_are_flat_spectrum():
    """The exact-binding property must survive text encoding."""
    k = encode_concept_vector("vault_a", seed=3, d=128)
    v = encode_value_vector("BLUE", seed=3, d=128)
    rec = unbind(bind(k, v), k)
    assert cosine(rec, v) == pytest.approx(1.0, abs=1e-9)


def test_same_value_text_same_vector():
    a = encode_value_vector("RED", seed=1, d=64)
    b = encode_value_vector("RED", seed=1, d=64)
    assert np.array_equal(a, b)


def test_encode_texts_batch_correlated():
    concepts = [f"c_{i}" for i in range(8)]
    values = [f"v_{i}" for i in range(8)]
    objects, symbols = encode_texts(concepts, values, seed=9, d=256, concept_similarity=0.8)
    sims = [cosine(objects[f"c_{i}"], objects[f"c_{j}"]) for i in range(8) for j in range(i)]
    assert abs(float(np.mean(sims)) - 0.8) < 0.15
    # flatness preserved under correlation → exact recall still works
    rec = unbind(bind(objects["c_0"], symbols["v_0"]), objects["c_0"])
    assert cosine(rec, symbols["v_0"]) == pytest.approx(1.0, abs=1e-9)


def test_encode_texts_independent_ignores_batch_membership():
    a1, s1 = encode_texts(["x", "y"], ["p", "q"], seed=4, d=64)
    a2, s2 = encode_texts(["x"], ["p"], seed=4, d=64)
    # independent mode: a text's vector does not depend on the batch
    assert np.array_equal(a1["x"], a2["x"])
    assert np.array_equal(s1["p"], s2["p"])


def test_encode_texts_deterministic():
    a = encode_texts(["a", "b"], ["1", "2"], seed=4, d=64)
    b = encode_texts(["a", "b"], ["1", "2"], seed=4, d=64)
    assert np.array_equal(a[0]["a"], b[0]["a"])
    assert np.array_equal(a[1]["2"], b[1]["2"])