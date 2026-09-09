"""Tests for Memory X-Ray analytics, competition graphs, clustering, and importance (Phase 05)."""

import pytest

from core import ExperimentConfig, run_experiment
from core.mechanisms.base import MechanismParams
from core.task import TaskConfig
from core.xray import (
    analyze_decay_curves,
    build_competition_graph,
    cluster_memory_representations,
    compute_event_impact,
    compute_memory_importance,
    compute_memory_strengths,
    detect_interference,
    detect_reinforcement,
    detect_state_anomalies,
    find_nearest_memories,
    get_memory_trace,
    project_memory_map_2d,
)


@pytest.fixture
def complex_experiment():
    """Create a structured experiment with multiple objects, interference, and cycles."""
    cfg = ExperimentConfig(
        seed=101,
        mechanism="interference",
        params=MechanismParams(
            state_dim=128,
            update_strength=0.9,
            memory_strength=1.0,
            interference_strength=0.6,
        ),
        task=TaskConfig(
            seed=101,
            d=128,
            n_objects=6,
            n_symbols=4,
            n_conflicts=3,
            object_similarity=0.4,
            cycles=2,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_memory_strength_evolution(complex_experiment):
    """Verify empirical readout strength trajectory for each memory."""
    strengths_map = compute_memory_strengths(complex_experiment)
    assert len(strengths_map) > 0

    for m_id, prof in strengths_map.items():
        assert prof.peak_strength >= prof.initial_strength
        assert len(prof.timeline_strengths) == len(complex_experiment.snapshots)
        assert prof.initial_strength >= 0.0
        assert prof.final_strength >= 0.0


def test_decay_curves(complex_experiment):
    """Verify decay curve analysis across the timeline."""
    decay_info = analyze_decay_curves(complex_experiment)
    assert "curves" in decay_info
    assert len(decay_info["curves"]) > 0
    assert "pattern_distribution" in decay_info
    assert "most_persistent_memory" in decay_info


def test_reinforcement_detection(complex_experiment):
    """Verify detection of memory strengthening by subsequent events."""
    reinf = detect_reinforcement(complex_experiment)
    assert isinstance(reinf, list)
    for r in reinf:
        assert r.net_change > 0.0
        assert len(r.reinforcement_events) > 0


def test_interference_detection(complex_experiment):
    """Verify detection of competing memory pairs with vector overlap."""
    interf = detect_interference(complex_experiment)
    assert isinstance(interf, list)
    if interf:
        top = interf[0]
        assert top.overlap > 0.0
        assert top.interference_score >= 0.0
        assert len(top.affected_steps) > 0


def test_competition_graph(complex_experiment):
    """Verify network construction of memory relationships."""
    graph = build_competition_graph(complex_experiment)
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0

    edge_types = {e.relationship.value for e in graph.edges}
    assert "similarity" in edge_types or "competition" in edge_types
    assert graph.density >= 0.0


def test_clustering(complex_experiment):
    """Verify geometric clustering of memory representations."""
    clusters = cluster_memory_representations(complex_experiment, max_clusters=3)
    assert len(clusters) <= 3
    for c in clusters:
        assert len(c.members) > 0
        assert c.cohesion > 0.0
        assert c.separation >= 0.0


def test_2d_projection_map(complex_experiment):
    """Verify PCA 2D projection and presence of epistemic disclaimer."""
    mmap = project_memory_map_2d(complex_experiment)
    assert len(mmap.points) > 0
    assert len(mmap.variance_explained) == 2
    assert "visualization" in mmap.epistemic_disclaimer.lower()

    for p in mmap.points:
        assert isinstance(p.x, float)
        assert isinstance(p.y, float)
        assert p.label


def test_nearest_neighbors(complex_experiment):
    """Verify nearest neighbor lookup in representation space."""
    strengths_map = compute_memory_strengths(complex_experiment)
    first_mem = list(strengths_map.keys())[0]

    neighbors = find_nearest_memories(complex_experiment, first_mem, k=3)
    assert len(neighbors) <= 3
    if len(neighbors) >= 2:
        # Must be sorted by similarity descending
        assert neighbors[0]["cosine_similarity"] >= neighbors[1]["cosine_similarity"]


def test_memory_trace(complex_experiment):
    """Verify lifecycle reconstruction for a single memory."""
    strengths_map = compute_memory_strengths(complex_experiment)
    first_mem = list(strengths_map.keys())[0]

    trace = get_memory_trace(complex_experiment, first_mem)
    assert trace is not None
    assert trace.memory_id == first_mem
    assert len(trace.stages) >= 1
    assert trace.stages[0]["stage"] == "ENCODED"


def test_event_impact(complex_experiment):
    """Verify connecting events to state transformations."""
    impacts = compute_event_impact(complex_experiment)
    assert len(impacts) == len(complex_experiment.events)
    for im in impacts:
        assert im.change_magnitude >= 0.0
        assert im.state_norm_after > 0.0


def test_memory_importance(complex_experiment):
    """Verify 6-dimensional importance profile."""
    imp_map = compute_memory_importance(complex_experiment)
    assert len(imp_map) > 0
    for m_id, imp in imp_map.items():
        assert 0.0 <= imp.counterfactual_contribution <= 1.0
        assert 0.0 <= imp.retrieval_relevance <= 1.0
        assert 0.0 <= imp.persistence <= 1.0


def test_anomaly_detection(complex_experiment):
    """Verify statistical anomaly detection."""
    anomalies = detect_state_anomalies(complex_experiment)
    assert isinstance(anomalies, list)
    for a in anomalies:
        assert a.deviation_z_score > 0.0
        assert a.metric
        assert a.evidence
