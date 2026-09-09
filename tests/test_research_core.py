"""Unit tests for Phase 23 Scientific Evidence & Research Layer core engine."""

import pytest
from core.research import (
    CLAIM_TRACES,
    METRIC_GLOSSARY,
    PRIMARY_PAPERS,
    SOURCE_LICENSES,
    ClaimTrace,
    MetricDefinition,
    PrimaryResearchPaper,
    ScientificResearchEngine,
)


def test_primary_papers_integrity():
    # Verify at least 3 primary papers from 2022-2026
    assert len(PRIMARY_PAPERS) >= 3
    for p in PRIMARY_PAPERS:
        assert p.year >= 2022 and p.year <= 2026
        assert p.doi.startswith("10.")
        assert p.url.startswith("https://")
        assert len(p.authors) > 0
        assert len(p.journal) > 0
        assert len(p.tags) > 0
        assert len(p.supported_claim) > 0
        assert len(p.pathway_connection) > 0
        assert len(p.model_limitations) > 0


def test_claim_traceability_integrity():
    assert len(CLAIM_TRACES) >= 5
    for c in CLAIM_TRACES:
        assert c.claim_id.startswith("CLAIM-")
        assert len(c.source_paper_ids) >= 1
        # Ensure paper IDs exist in PRIMARY_PAPERS
        known_ids = {p.paper_id for p in PRIMARY_PAPERS}
        assert all(pid in known_ids for pid in c.source_paper_ids)
        assert len(c.measured_metrics) >= 1
        assert len(c.observed_finding) > 0
        assert len(c.scientific_interpretation) > 0
        assert len(c.what_this_does_not_prove) > 0


def test_metric_glossary_integrity():
    assert len(METRIC_GLOSSARY) >= 5
    for m in METRIC_GLOSSARY:
        assert len(m.metric_id) > 0
        assert len(m.name) > 0
        assert len(m.formula) > 0
        assert len(m.unit) > 0
        assert len(m.definition) > 0
        assert len(m.interpretation) > 0
        assert len(m.limitation) > 0


def test_source_licenses_registry():
    assert len(SOURCE_LICENSES) >= 5
    categories = {l.category for l in SOURCE_LICENSES}
    assert "CODE" in categories
    assert "LIBRARIES" in categories
    assert "DATA" in categories
    assert "PAPERS" in categories


def test_research_engine_graph():
    engine = ScientificResearchEngine()
    graph = engine.get_research_graph()
    assert "nodes" in graph
    assert "edges" in graph
    assert graph["total_nodes"] > 10
    assert graph["total_edges"] > 10

    node_types = {n["node_type"] for n in graph["nodes"]}
    assert "CONCEPT" in node_types
    assert "PAPER" in node_types
    assert "IMPLEMENTATION" in node_types
    assert "OBSERVATION" in node_types


def test_research_engine_disclosures_and_methodology():
    engine = ScientificResearchEngine()
    disclosures = engine.get_disclosures()
    assert "ai_assistance" in disclosures
    assert "data_disclosure" in disclosures
    assert "prerequisites" in disclosures
    assert len(disclosures["learning_objectives"]) == 7
    assert len(disclosures["limitations"]) >= 5

    methodology = engine.generate_methodology(
        experiment_type="INTERFERENCE",
        config={"d": 16, "seed": 42, "decay": 0.05, "update_strength": 1.0, "concept_a": "cat"},
    )
    assert methodology["experiment_type"] == "INTERFERENCE"
    assert "Hebbian" in methodology["mathematical_operation"]
    assert len(methodology["evaluation_metrics"]) >= 4
