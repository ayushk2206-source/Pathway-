"""Tests for Phase 21 Ecosystem Experiments: Branching, Replay, State Comparison."""

import pytest
from core.ecosystem import MemoryEcosystemEngine, MemoryBranch


def test_memory_branch_tree_structure():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    tree = engine.get_memory_branch_tree("M-001")

    assert isinstance(tree, MemoryBranch)
    assert tree.branch_type == "ORIGINAL"
    assert tree.memory_id == "M-001"
    assert len(tree.children) >= 1

    coll_branch = tree.children[0]
    assert coll_branch.branch_type == "COLLISION"
    assert len(coll_branch.children) >= 2

    child_types = {c.branch_type for c in coll_branch.children}
    assert "SURGERY" in child_types
    assert "COUNTERFACTUAL" in child_types

    d = tree.to_dict()
    assert d["branch_type"] == "ORIGINAL"
    assert len(d["children"]) > 0


def test_replay_memory_reconstruction():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    replay = engine.replay_memory("M-001")

    assert replay["memory_id"] == "M-001"
    assert replay["concept"] == "Concept Alpha"
    assert replay["total_steps"] >= 2
    assert len(replay["playback_steps"]) == replay["total_steps"]

    step0 = replay["playback_steps"][0]
    assert "step_index" in step0
    assert "event_type" in step0
    assert "metrics" in step0
    assert step0["label"] == "OBSERVED COMPUTATION"
    assert "TEACHING SIMPLIFICATION" in replay["disclaimer"]


def test_cross_memory_comparison():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    p1 = engine.get_memory_passport("M-001")
    p2 = engine.get_memory_passport("M-002")

    state1 = {"W_norm": p1.fingerprint_norm, "active_ratio": p1.active_units / 16.0}
    state2 = {"W_norm": p2.fingerprint_norm, "active_ratio": p2.active_units / 16.0}

    diff = engine.compare_states(state1, state2)
    assert "frobenius_drift" in diff
    assert "shared_stability" in diff
    assert diff["shared_stability"] >= 0.0


def test_ecosystem_checkpoint_timeline_integration():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    initial_timeline_len = len(engine.get_unified_timeline("M-001"))

    cp = engine.create_checkpoint("M-001", "Timeline Integration Checkpoint")
    new_timeline = engine.get_unified_timeline("M-001")

    assert len(new_timeline) == initial_timeline_len + 1
    last_event = new_timeline[-1]
    assert last_event.event_type == "INSPECTION"
    assert cp.label in last_event.title
