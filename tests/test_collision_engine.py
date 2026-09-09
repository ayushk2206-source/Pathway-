"""Tests for Phase 17: Memory Collision & Interference Lab Core Engine."""

import pytest
import numpy as np

from core.collision import (
    CollisionConfig,
    CollisionMemory,
    CollisionResult,
    perform_collision_counterfactual,
    perform_collision_surgery,
    run_collision_experiment,
    run_order_comparison,
    run_three_condition_suite,
)


def test_collision_isolated_baselines():
    """Verify that isolated baseline runs produce clean, uncorrupted recall."""
    cfg = CollisionConfig(
        seed=42,
        dimension=16,
        memory_a=CollisionMemory("alpha", "val_alpha"),
        memory_b=CollisionMemory("beta", "val_beta"),
        concept_similarity=0.0,
    )
    res = run_collision_experiment(cfg)

    assert res.isolated_recall_a["fidelity"] > 0.95
    assert res.isolated_recall_b["fidelity"] > 0.95
    assert res.isolated_recall_a["is_correct"] is True
    assert res.isolated_recall_b["is_correct"] is True


def test_collision_overlap_gradient():
    """Verify that higher representational overlap causes higher computational interference and more shared synapses."""
    suite = run_three_condition_suite(
        CollisionConfig(
            seed=42,
            dimension=16,
            memory_a=CollisionMemory("cue_a", "target_a"),
            memory_b=CollisionMemory("cue_b", "target_b"),
        )
    )

    rows = suite["recall_matrix"]
    assert len(rows) == 3

    low = rows[0]
    mod = rows[1]
    high = rows[2]

    # Representational overlap should increase across conditions
    assert low["representational_overlap"] < mod["representational_overlap"] < high["representational_overlap"]

    # Higher representational overlap causes higher computational interference
    assert low["interference"] < mod["interference"] < high["interference"]


def test_order_comparison_asymmetry():
    """Verify that write sequence order A->B vs B->A results in state asymmetry due to temporal decay and sequential updates."""
    cfg = CollisionConfig(
        seed=42,
        dimension=16,
        decay=0.08,
        concept_similarity=0.45,
    )
    order_res = run_order_comparison(cfg)

    assert order_res["order_asymmetry_detected"] is True
    assert order_res["matrix_frobenius_difference"] > 1e-4

    # The more recent memory in A->B (Memory B) should have higher recall than Memory A due to decay
    ab = order_res["order_a_then_b"]
    assert ab["recall_b"] >= ab["recall_a"]

    # In B->A, Memory A is written second and should have higher recall than Memory B
    ba = order_res["order_b_then_a"]
    assert ba["recall_a"] >= ba["recall_b"]


def test_temporal_delay_decay():
    """Verify that increasing temporal delay between writes weakens Memory A further before Memory B writes."""
    cfg_no_delay = CollisionConfig(
        seed=42,
        dimension=16,
        decay=0.1,
        temporal_delay=0,
    )
    res_no_delay = run_collision_experiment(cfg_no_delay)

    cfg_with_delay = CollisionConfig(
        seed=42,
        dimension=16,
        decay=0.1,
        temporal_delay=3,
    )
    res_with_delay = run_collision_experiment(cfg_with_delay)

    # Delay should decay Memory A's contribution, leading to lower final recall fidelity for A
    assert res_with_delay.combined_recall_a["fidelity"] <= res_no_delay.combined_recall_a["fidelity"]


def test_pathway_classifications_and_overlap_fraction():
    """Verify that synapses are accurately classified into A_ONLY, B_ONLY, SHARED, and UNCHANGED."""
    cfg = CollisionConfig(
        seed=42,
        dimension=16,
        concept_similarity=0.5,
    )
    res = run_collision_experiment(cfg)

    assert len(res.collision_map) == 16 * 16
    assert len(res.shared_synapses) > 0
    assert len(res.a_only_synapses) > 0
    assert len(res.b_only_synapses) > 0

    # Synaptic overlap fraction should be in [0, 1]
    assert 0.0 <= res.synaptic_overlap_fraction <= 1.0


def test_multi_memory_collision_abc():
    """Verify 3-memory collision A + B + C operates cleanly."""
    cfg = CollisionConfig(
        seed=42,
        dimension=16,
        memory_a=CollisionMemory("mem1", "val1"),
        memory_b=CollisionMemory("mem2", "val2"),
        memory_c=CollisionMemory("mem3", "val3"),
        concept_similarity=0.3,
    )
    res = run_collision_experiment(cfg)

    assert res.isolated_recall_c is not None
    assert res.combined_recall_c is not None
    assert "fidelity" in res.combined_recall_c


def test_collision_synaptic_surgery():
    """Verify that surgical modification of a shared synapse alters recall metrics."""
    cfg = CollisionConfig(seed=42, dimension=16, concept_similarity=0.5)
    base_res = run_collision_experiment(cfg)

    target_syn = base_res.shared_synapses[0]
    surg_res = perform_collision_surgery(base_res, target_syn, operation="silence")

    assert surg_res["status"] == "success"
    assert surg_res["target_synapse"] == target_syn
    assert surg_res["post_surgery_weight"] == 0.0
    assert surg_res["matrix_frobenius_delta"] > 0.0


def test_collision_counterfactual():
    """Verify counterfactual branch evaluating: What if Memory B never touched shared synapses?"""
    cfg = CollisionConfig(seed=42, dimension=16, concept_similarity=0.6)
    base_res = run_collision_experiment(cfg)

    cf_res = perform_collision_counterfactual(base_res)

    assert cf_res["status"] == "success"
    assert cf_res["protected_synapses_count"] == len(base_res.shared_synapses)
    # Memory A should be better preserved or equal in the counterfactual where B didn't overwrite shared synapses
    assert cf_res["counterfactual_recall_a"] >= base_res.combined_recall_a["fidelity"] - 1e-4
