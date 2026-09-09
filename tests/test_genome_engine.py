"""Unit and integration tests for core/genome engine components (Phase 08)."""

import pytest
from core import Experiment, ExperimentConfig, run_experiment
from core.genome.cascade import CascadeEngine
from core.genome.genome import LineageBuilder, MemoryGenomeBuilder, resolve_memory
from core.genome.models import MemoryGenome, MemoryLineageGraph
from core.genome.types import CascadeEffectType


@pytest.fixture
def canonical_experiment() -> Experiment:
    """Provides the standard 128D canonical demo experiment."""
    config = ExperimentConfig.from_api({
        "seed": 42,
        "mechanism": "interference",
        "task_name": "associative_recall",
        "d": 128,
        "num_events": 10,
    })
    return run_experiment(config)


def test_resolve_memory(canonical_experiment: Experiment):
    """Test resolving memory by ID, concept label, and case-insensitive matching."""
    mem_by_id = resolve_memory(canonical_experiment, "e0000")
    assert mem_by_id is not None
    assert mem_by_id["memory_id"] == "e0000"

    mem_by_concept = resolve_memory(canonical_experiment, "obj_A")
    assert mem_by_concept is not None
    assert "obj_A" in mem_by_concept["concept_label"]

    mem_case = resolve_memory(canonical_experiment, "OBJ_A")
    assert mem_case is not None


def test_memory_genome_builder(canonical_experiment: Experiment):
    """Test building a structured MemoryGenome with all 8 DNA facets."""
    genome = MemoryGenomeBuilder.build(canonical_experiment, "obj_A")
    assert isinstance(genome, MemoryGenome)
    assert genome.memory_id == "e0000"
    assert "obj_A" in genome.concept_label
    assert genome.origin_step >= 0
    assert len(genome.formation_events) >= 1
    assert len(genome.associations) >= 1
    assert len(genome.trajectory) == len(canonical_experiment.snapshots)
    assert 0.0 <= genome.current_strength <= 1.0
    assert 0.0 <= genome.stability <= 1.0

    # Test DNA strip
    dna = genome.dna_strip
    assert 0.0 <= dna.origin_score <= 1.0
    assert 0.0 <= dna.reinforcement_score <= 1.0
    assert 0.0 <= dna.association_score <= 1.0
    assert 0.0 <= dna.competition_score <= 1.0
    assert 0.0 <= dna.retrieval_score <= 1.0
    assert 0.0 <= dna.drift_score <= 1.0
    assert 0.0 <= dna.stability_score <= 1.0
    assert 0.0 <= dna.influence_score <= 1.0
    assert len(dna.evidence) == 8

    # Serialization
    g_dict = genome.to_dict()
    assert g_dict["memory_id"] == "e0000"
    assert "associations" in g_dict
    assert "dna_strip" in g_dict


def test_lineage_builder(canonical_experiment: Experiment):
    """Test generating a causal directed acyclic lineage graph."""
    lineage = LineageBuilder.build(canonical_experiment, "obj_A")
    assert isinstance(lineage, MemoryLineageGraph)
    assert lineage.memory_id == "e0000"
    assert len(lineage.nodes) >= 3
    assert len(lineage.edges) >= 2

    node_types = {n.node_type for n in lineage.nodes}
    assert "EVENT" in node_types
    assert "OPERATION" in node_types
    assert "TARGET_MEMORY" in node_types


def test_cascade_engine_simulation(canonical_experiment: Experiment):
    """Test running counterfactual cascade simulation with ablation."""
    cmap = CascadeEngine.run_cascade(
        experiment=canonical_experiment,
        target_query="obj_A",
        intervention_type="remove",
    )
    assert cmap.target_memory == "e0000"
    assert cmap.intervention == "remove"
    assert len(cmap.nodes) >= 3
    assert cmap.total_cascade_depth >= 0
    assert cmap.total_cascade_impact >= 0.0

    # Target node should be Depth 0 with DIRECT effect
    target_node = next((n for n in cmap.nodes if n.memory_id == "e0000"), None)
    assert target_node is not None
    assert target_node.depth == 0
    assert target_node.effect_type == CascadeEffectType.DIRECT

    # Influence breakdown
    breakdown = CascadeEngine.compute_influence_breakdown(cmap)
    assert 0.0 <= breakdown.direct_effect <= 2.0
    assert 0.0 <= breakdown.total_influence <= 1.0


def test_cascade_weaken_dose(canonical_experiment: Experiment):
    """Test running cascade simulation with dose scaling (50% weakening)."""
    cmap = CascadeEngine.run_cascade(
        experiment=canonical_experiment,
        target_query="obj_A",
        intervention_type="weaken",
        dose=0.5,
    )
    assert cmap.target_memory == "e0000"
    assert len(cmap.nodes) >= 1
    target_node = next((n for n in cmap.nodes if n.memory_id == "e0000"), None)
    assert target_node is not None
    assert target_node.strength_after < target_node.strength_before
