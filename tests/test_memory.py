"""Memory engine tests (Phase 02, sections 2–8)."""

import numpy as np
import pytest

from core import (
    MechanismParams,
    Memory,
    TextMemory,
    create_mechanism,
    encode_memory,
    interference_model,
    recall_memory,
    similarity,
    write_memory,
    write_memories,
)
from core.vectors import cosine, normalize


def _m(concept: str, value: str, seed: int = 5, d: int = 64, **kw) -> Memory:
    return encode_memory(TextMemory(concept, value, **kw), seed=seed, d=d)


def test_write_memory_accounting_exact():
    mech = create_mechanism("baseline", MechanismParams(state_dim=64), seed=5)
    m = _m("capital_of_france", "Paris")
    u = write_memory(mech, m, timestep=0)
    assert u.update_magnitude == pytest.approx(1.0, abs=1e-9)
    # baseline: the whole update is the memory's write; zero interference
    assert u.memory_contribution == pytest.approx(1.0, abs=1e-9)
    assert u.interference_contribution == pytest.approx(0.0, abs=1e-9)
    assert np.allclose(u.update_vector, u.memory_contribution_vector)
    assert len(u.affected_dimensions) > 0
    assert u.decay_applied == 0.0
    # state accounting consistency
    assert np.allclose(
        np.asarray(u.state_after) - np.asarray(u.state_before), u.update_vector
    )


def test_write_strength_scales_contribution():
    mech = create_mechanism("baseline", MechanismParams(state_dim=64), seed=5)
    m = _m("x", "y", strength=0.5, importance=0.5)
    u = write_memory(mech, m, timestep=0)
    assert u.memory_contribution == pytest.approx(0.25, abs=1e-9)
    assert u.update_magnitude == pytest.approx(0.25, abs=1e-9)


def test_write_leaky_splits_memory_and_interference():
    mech = create_mechanism("leaky", MechanismParams(state_dim=64, decay=0.3), seed=5)
    m1 = _m("a", "1")
    m2 = _m("b", "2")
    write_memory(mech, m1, timestep=0)
    u = write_memory(mech, m2, timestep=1)
    # update = -λ·x_prev + gain·b → the interference contribution is the
    # decay of the old state (exactly, by construction)
    assert u.interference_contribution > 0.0
    assert u.decay_applied == pytest.approx(0.3)
    assert np.allclose(
        u.update_vector,
        np.asarray(u.memory_contribution_vector) + np.asarray(u.interference_contribution_vector),
    )
    # and the memory's own write term is the fresh binding at gain 1
    assert u.memory_contribution == pytest.approx(1.0, abs=1e-9)


def test_recall_single_memory_exact():
    mech = create_mechanism("baseline", MechanismParams(state_dim=64), seed=5)
    m = _m("capital_of_france", "Paris")
    write_memory(mech, m, timestep=0)
    r = recall_memory(mech, TextMemory("capital_of_france"), [m], seed=5, d=64, expected_value="Paris")
    assert r.predicted_value == "Paris"
    assert r.correct is True
    assert r.confidence == pytest.approx(1.0, abs=1e-9)
    assert r.state_similarity == pytest.approx(1.0, abs=1e-9)
    assert r.candidate_memories[0]["value"] == "Paris"
    assert len(r.relevant_dimensions) > 0


def test_recall_pure_probe_has_no_invented_truth():
    mech = create_mechanism("baseline", MechanismParams(state_dim=64), seed=5)
    m = _m("a", "1")
    write_memory(mech, m, timestep=0)
    r = recall_memory(mech, TextMemory("a"), [m], seed=5, d=64)
    assert r.ground_truth is None
    assert r.correct is None
    assert r.predicted_value == "1"


def test_conflicting_memories_recall():
    mech = create_mechanism("leaky", MechanismParams(state_dim=64, decay=0.5), seed=5)
    m_blue = _m("vault_a", "BLUE")
    m_green = _m("vault_a", "GREEN")
    write_memory(mech, m_blue, timestep=0)
    write_memory(mech, m_green, timestep=1)
    r = recall_memory(
        mech, TextMemory("vault_a"), [m_blue, m_green],
        seed=5, d=64, expected_value="GREEN",
    )
    assert r.correct is True  # recency wins under decay
    assert r.predicted_value == "GREEN"


def test_conflicting_memories_baseline_ties():
    mech = create_mechanism("baseline", MechanismParams(state_dim=64), seed=5)
    m_blue = _m("vault_a", "BLUE")
    m_green = _m("vault_a", "GREEN")
    write_memory(mech, m_blue, timestep=0)
    write_memory(mech, m_green, timestep=1)
    r = recall_memory(
        mech, TextMemory("vault_a"), [m_blue, m_green],
        seed=5, d=64, expected_value="GREEN",
    )
    # superposition stores both sides of the conflict with equal strength:
    # the two candidates score (near-)identically → no recency preference
    sims = {c["value"]: c["similarity"] for c in r.candidate_memories}
    assert abs(sims["BLUE"] - sims["GREEN"]) < 1e-9


def test_similarity_measures():
    a = normalize(np.array([1.0, 0.0]))
    b = normalize(np.array([1.0, 1.0]))
    assert similarity(a, b, "cosine") == pytest.approx(1 / np.sqrt(2))
    assert similarity(a, a, "euclidean") == pytest.approx(1.0)
    assert similarity(a, b, "euclidean") < 1.0
    assert similarity(a, b, "dot") == pytest.approx(1 / np.sqrt(2))
    # dot is magnitude-sensitive
    assert similarity(2 * a, b, "dot") > similarity(a, b, "dot")
    with pytest.raises(ValueError):
        similarity(a, b, "banana")


def test_interference_model_formula():
    a = normalize(np.array([1.0, 0.0]))
    b = normalize(np.array([1.0, 0.0]))
    assert interference_model(a, b, update_strength=1.0) == pytest.approx(1.0)
    assert interference_model(a, b, update_strength=0.5, competition_factor=2.0) == pytest.approx(1.0)
    c = normalize(np.array([0.0, 1.0]))
    assert interference_model(a, c, update_strength=1.0) == pytest.approx(0.0)


def test_deterministic_write_and_recall():
    results = []
    for _ in range(2):
        mech = create_mechanism("interference", MechanismParams(state_dim=64, interference_strength=0.8), seed=9)
        ms = [_m("a", "1"), _m("b", "2"), _m("c", "3")]
        write_memories(mech, ms, start_timestep=0)
        r = recall_memory(mech, TextMemory("a"), ms, seed=9, d=64, expected_value="1")
        results.append((mech.state_vector().copy(), r.to_dict()))
    assert np.array_equal(results[0][0], results[1][0])
    # memory ids are fresh uuids per encode; everything numeric is identical
    a, b = results[0][1], results[1][1]
    for key in ("predicted_value", "confidence", "similarity", "state_similarity",
                "prediction_vector", "correct", "ground_truth"):
        assert a[key] == b[key], key
    assert [c["similarity"] for c in a["candidate_memories"]] == [
        c["similarity"] for c in b["candidate_memories"]
    ]


def test_write_updates_access_metadata():
    mech = create_mechanism("baseline", MechanismParams(state_dim=64), seed=5)
    m = _m("a", "1")
    write_memory(mech, m, timestep=0)
    assert m.creation_timestep == 0
    assert m.last_accessed_timestep == 0
    assert m.access_count == 1


def test_memory_round_trip():
    m = _m("concept", "value")
    d = m.to_dict()
    m2 = Memory.from_dict(d)
    assert np.array_equal(m2.vector, m.vector)
    assert m2.concept == m.concept and m2.id == m.id