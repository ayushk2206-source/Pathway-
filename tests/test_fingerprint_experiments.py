"""Tests for Phase 20 Controlled Experiments and Integrations (core/fingerprint.py)."""

import pytest

from core.fingerprint import MemoryGenomeEngine, MemoryBranchNode


@pytest.fixture
def engine():
    return MemoryGenomeEngine()


def test_run_cloning_experiment(engine):
    res = engine.run_cloning_experiment(
        seed=42,
        dimension=16,
        target_concept="Concept Alpha",
        target_value="Target Alpha",
        intervening_concept="Intervening Beta",
        intervening_value="Target Beta",
    )

    assert "target_concept" in res
    assert "fingerprint_before" in res
    assert "fingerprint_after" in res
    assert "comparison" in res
    assert "stability_conclusion" in res

    comp = res["comparison"]
    assert "internal_similarity" in comp
    assert "surface_similarity" in comp
    assert comp["internal_similarity"] > 0.5


def test_run_collision_mutation(engine):
    res = engine.run_collision_mutation(
        seed=42,
        dimension=16,
        concept_a="Memory A",
        value_a="Target A",
        concept_b="Memory B Competing",
        value_b="Target B",
    )

    assert "fingerprint_a_before" in res
    assert "fingerprint_b" in res
    assert "fingerprint_a_after_collision" in res
    assert "mutation_comparison" in res
    assert "interpretation" in res

    comp = res["mutation_comparison"]
    assert comp["shared_synapses"] is not None


def test_run_surgery_and_remeasure(engine):
    res = engine.run_surgery_and_remeasure(
        seed=42,
        dimension=16,
        concept="Memory Surgery Test",
        value="Target Surgery",
        target_synapse=(0, 0),
        new_weight=0.0,
    )

    assert "fingerprint_before" in res
    assert "fingerprint_after" in res
    assert res["target_synapse"] == [0, 0]
    assert res["weight_after"] == 0.0
    assert "recall_fidelity_before" in res
    assert "recall_fidelity_after" in res


def test_run_counterfactual_comparison(engine):
    res = engine.run_counterfactual_comparison(
        seed=42,
        dimension=16,
        concept="Memory CF",
        value="Value CF",
        cf_update_strength=0.05,
    )

    assert "original_fingerprint" in res
    assert "counterfactual_fingerprint" in res
    assert "comparison" in res
    assert "divergence_summary" in res

    orig_frob = res["original_fingerprint"]["synaptic_strength_stats"]["frobenius_contribution"]
    cf_frob = res["counterfactual_fingerprint"]["synaptic_strength_stats"]["frobenius_contribution"]
    # Weaker plasticity leads to smaller Frobenius contribution
    assert cf_frob < orig_frob


def test_build_family_tree(engine):
    tree = engine.build_family_tree(target_concept="Concept Alpha", seed=42, dimension=16)

    assert isinstance(tree, MemoryBranchNode)
    assert tree.branch_type == "ORIGINAL"
    assert len(tree.children) == 2  # Collision and Counterfactual

    col_child = next((c for c in tree.children if c.branch_type == "COLLISION"), None)
    cf_child = next((c for c in tree.children if c.branch_type == "COUNTERFACTUAL"), None)

    assert col_child is not None
    assert cf_child is not None

    # Check surgery grandchild off collision
    assert len(col_child.children) >= 1
    surg_child = col_child.children[0]
    assert surg_child.branch_type == "SURGERY"


def test_export_fingerprint_json(engine):
    from core.synaptic import SynapticBrain

    brain = SynapticBrain(seed=42, d=16, update_strength=0.35, decay=0.01)
    brain.write("Concept Alpha", "Target Alpha")
    fp = engine.compute_fingerprint(brain, "Concept Alpha", "Target Alpha")

    data = engine.export_fingerprint_json(fp)
    assert data["format"] == "pathway_synaptic_fingerprint_v1"
    assert data["memory_id"] == fp.memory_id
    assert "statistics" in data
    assert "fingerprint" in data
