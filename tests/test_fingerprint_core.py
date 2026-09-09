"""Tests for Phase 20 Core Mathematical Engine (core/fingerprint.py)."""

import pytest
import numpy as np

from core.fingerprint import (
    MemoryGenomeEngine,
    SynapticFingerprint,
    FingerprintComparison,
    MemoryDistanceMap,
    OutlierReport,
)
from core.synaptic import SynapticBrain


@pytest.fixture
def engine():
    return MemoryGenomeEngine(activation_threshold=0.05, synapse_threshold=0.01)


@pytest.fixture
def brain():
    b = SynapticBrain(seed=42, d=16, update_strength=0.35, decay=0.01)
    b.write("Concept Alpha", "Target Alpha")
    b.write("Concept Beta", "Target Beta")
    b.write("Concept Gamma", "Target Gamma")
    return b


def test_compute_fingerprint_structure(engine, brain):
    fp = engine.compute_fingerprint(brain, "Concept Alpha", "Target Alpha")

    assert isinstance(fp, SynapticFingerprint)
    assert fp.concept == "Concept Alpha"
    assert fp.value == "Target Alpha"
    assert fp.dimension == 16
    assert fp.active_unit_count > 0
    assert len(fp.active_key_units) > 0
    assert len(fp.active_value_units) > 0
    assert fp.modified_synapse_count > 0
    assert len(fp.modified_synapses) == fp.modified_synapse_count

    # Check strength stats
    stats = fp.synaptic_strength_stats
    assert "mean" in stats
    assert "std" in stats
    assert "frobenius_contribution" in stats
    assert stats["frobenius_contribution"] > 0

    # Check activation distribution
    dist = fp.activation_distribution
    assert "mean" in dist
    assert "variance" in dist
    assert "sparsity" in dist
    assert 0.0 <= fp.sparsity <= 1.0

    # Check representation vector length (d * d)
    assert len(fp.representation_vector) == 16 * 16
    # Check normalized L2 norm is ~1.0
    norm_rep = np.linalg.norm(fp.representation_vector)
    assert np.isclose(norm_rep, 1.0, atol=1e-3)


def test_compare_fingerprints_surface_vs_internal(engine, brain):
    fp_a = engine.compute_fingerprint(brain, "Concept Alpha")
    fp_b = engine.compute_fingerprint(brain, "Concept Beta")

    comp = engine.compare_fingerprints(fp_a, fp_b, seed=42)
    assert isinstance(comp, FingerprintComparison)
    assert comp.concept_a == "Concept Alpha"
    assert comp.concept_b == "Concept Beta"

    # Surface vs Internal values bounded in [-1, 1]
    assert -1.0 <= comp.surface_similarity <= 1.0
    assert -1.0 <= comp.internal_similarity <= 1.0
    assert 0.0 <= comp.synaptic_overlap_jaccard <= 1.0
    assert comp.similarity_discrepancy >= 0.0

    # Check synapse partition: total modified in A should equal shared + a_only
    total_a = len(comp.shared_synapses) + len(comp.a_only_synapses)
    assert total_a == fp_a.modified_synapse_count


def test_compare_surface_vs_internal_pairwise(engine, brain):
    concepts = ["Concept Alpha", "Concept Beta", "Concept Gamma"]
    comparisons = engine.compare_surface_vs_internal(brain, concepts)
    # 3 concepts -> 3 pairs
    assert len(comparisons) == 3
    for c in comparisons:
        assert isinstance(c, FingerprintComparison)
        assert c.explanation != ""


def test_track_evolution(engine):
    import copy
    brain = SynapticBrain(seed=42, d=16, update_strength=0.35, decay=0.05)
    snapshots = []

    # Step 1: Write A
    brain.write("Concept Alpha", "Target Alpha")
    snapshots.append(copy.deepcopy(brain))

    # Step 2: Write Competing B
    brain.write("Concept Beta", "Target Beta")
    snapshots.append(copy.deepcopy(brain))

    # Step 3: Decay step (decay applied)
    brain.write("Concept Gamma", "Target Gamma")
    snapshots.append(copy.deepcopy(brain))

    evol = engine.track_evolution(snapshots, "Concept Alpha")
    assert len(evol.timesteps) == 3
    assert len(evol.active_unit_trajectory) == 3
    assert len(evol.modified_synapse_trajectory) == 3
    assert len(evol.fidelity_trajectory) == 3


def test_compute_distance_map_2d(engine, brain):
    concepts = ["Concept Alpha", "Concept Beta", "Concept Gamma"]
    fingerprints = [engine.compute_fingerprint(brain, c) for c in concepts]

    d_map = engine.compute_distance_map(fingerprints)
    assert isinstance(d_map, MemoryDistanceMap)
    assert d_map.projection_method == "PCA_2D"
    assert len(d_map.points) == 3
    assert d_map.variance_explained is not None
    assert 0.0 <= d_map.variance_explained <= 1.0

    for pt in d_map.points:
        assert isinstance(pt.x, float)
        assert isinstance(pt.y, float)


def test_detect_outliers(engine, brain):
    concepts = ["Concept Alpha", "Concept Beta", "Concept Gamma"]
    fingerprints = [engine.compute_fingerprint(brain, c) for c in concepts]

    # Add an artificial skewed fingerprint to test outlier detector
    skewed_brain = SynapticBrain(seed=999, d=16, update_strength=1.8, decay=0.0)
    skewed_brain.write("Outlier Concept", "Outlier Value", importance=3.0, strength=2.5)
    fp_skewed = engine.compute_fingerprint(skewed_brain, "Outlier Concept")
    fingerprints.append(fp_skewed)

    reports = engine.detect_outliers(fingerprints)
    assert len(reports) == 4
    for r in reports:
        assert isinstance(r, OutlierReport)
        assert "active_units" in r.z_scores
        assert "frobenius_contribution" in r.z_scores
