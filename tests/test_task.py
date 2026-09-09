"""Task generator tests."""

import numpy as np
import pytest

from core.task import EventSpec, QuerySpec, TaskConfig, generate_task


def test_generation_is_deterministic():
    def stripped(task):
        d = task.to_dict()
        for ev in d["events"]:
            ev.pop("timestamp", None)  # wall clock, not computation
        return d

    cfg = TaskConfig(seed=42, d=64, n_objects=6, n_symbols=4, n_conflicts=2)
    assert stripped(generate_task(cfg)) == stripped(generate_task(cfg))


def test_different_seed_gives_different_vectors():
    a = generate_task(TaskConfig(seed=1, d=64))
    b = generate_task(TaskConfig(seed=2, d=64))
    v_a = next(iter(a.objects.values()))
    v_b = next(iter(b.objects.values()))
    assert not np.allclose(v_a, v_b)


def test_events_carry_expected_fields():
    cfg = TaskConfig(seed=3, d=32, n_objects=2, n_symbols=2, n_conflicts=1)
    t = generate_task(cfg)
    for i, e in enumerate(t.events):
        assert e.timestep == i
        assert e.concept_label in t.objects
        assert e.attribute_label in t.symbols
        assert e.key_vector.shape == (32,)
        assert e.value_vector.shape == (32,)
        assert e.strength == 1.0 and e.importance == 1.0
        assert e.noise == 0.0


def test_conflicts_are_recorded():
    cfg = TaskConfig(seed=5, d=32, n_objects=3, n_symbols=3, n_conflicts=2)
    t = generate_task(cfg)
    assert len(t.conflicts) == 2
    for obj, recs in t.conflicts.items():
        assert recs[0]["old_symbol"] != recs[0]["new_symbol"]
        # conflict event appears in the sequence at the recorded timestep
        ev = t.events[recs[0]["timestep"]]
        assert ev.concept_label == obj
        assert ev.attribute_label == recs[0]["new_symbol"]
    # conflicted objects were initially assigned their first symbol
    for obj in t.conflicts:
        assert t.initial_assignment[obj] == t.conflicts[obj][0]["old_symbol"]


def test_query_ground_truth_latest_vs_original():
    cfg = TaskConfig(
        seed=7,
        d=32,
        n_objects=1,
        n_symbols=2,
        n_conflicts=1,
        probe_original=True,
    )
    t = generate_task(cfg)
    obj = list(t.objects)[0]
    kinds = {q.kind for q in t.queries}
    assert kinds == {"latest", "original"}
    for q in t.queries:
        if q.kind == "original":
            assert q.expected_attribute_label == t.conflicts[obj][0]["old_symbol"]
        else:
            assert q.expected_attribute_label == t.last_write[obj][1]


def test_query_timestep_semantics():
    cfg = TaskConfig(seed=11, d=32, n_objects=2, n_symbols=2, n_conflicts=1)
    t = generate_task(cfg)
    # auto-generated end queries point at the final event
    end = len(t.events) - 1
    for q in t.queries:
        assert 0 <= q.timestep <= end
    # the "latest after conflict" query sits exactly at the conflict
    for obj, recs in t.conflicts.items():
        cts = {q.timestep for q in t.queries if q.object_label == obj and q.kind == "latest"}
        assert recs[-1]["timestep"] in cts


def test_explicit_events_and_queries():
    cfg = TaskConfig(
        seed=0,
        d=16,
        events=[
            EventSpec("obj_A", "sym_RED"),
            EventSpec("obj_B", "sym_BLUE"),
            EventSpec("obj_A", "sym_GREEN"),
        ],
        queries=[QuerySpec("obj_A", timestep=2, kind="latest")],
    )
    t = generate_task(cfg)
    assert [e.attribute_label for e in t.events] == ["sym_RED", "sym_BLUE", "sym_GREEN"]
    assert len(t.queries) == 1
    assert t.queries[0].expected_attribute_label == "sym_GREEN"
    assert t.conflicts["obj_A"][0] == {
        "old_symbol": "sym_RED",
        "new_symbol": "sym_GREEN",
        "timestep": 2,
    }


def test_empty_events_produce_no_queries():
    cfg = TaskConfig(seed=0, d=16, events=[])
    t = generate_task(cfg)
    assert t.events == []
    assert t.queries == []


def test_invalid_configs_raise():
    with pytest.raises(ValueError):
        generate_task(TaskConfig(n_symbols=1, n_conflicts=1))
    with pytest.raises(ValueError):
        generate_task(TaskConfig(order="banana"))
    with pytest.raises(ValueError):
        generate_task(TaskConfig(vector_source="banana"))
    # querying an object that was never written is invalid
    with pytest.raises(ValueError):
        generate_task(TaskConfig(queries=[QuerySpec("ghost", timestep=0)]))


def test_order_modes_run():
    for order in ("structured", "interleaved", "randomized"):
        cfg = TaskConfig(seed=13, d=32, n_objects=4, n_symbols=3, n_conflicts=2, order=order)
        t = generate_task(cfg)
        assert len(t.events) > 0
        assert all(e.concept_label in t.objects for e in t.events)