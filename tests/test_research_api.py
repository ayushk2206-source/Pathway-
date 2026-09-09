"""Integration tests for Phase 23 Scientific Evidence & Research Layer API endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_list_papers():
    response = client.get("/api/research/papers")
    assert response.status_code == 200
    data = response.json()
    assert "papers" in data
    assert "available_tags" in data
    papers = data["papers"]
    assert isinstance(papers, list)
    assert len(papers) >= 3
    for p in papers:
        assert "paper_id" in p
        assert "title" in p
        assert "doi" in p
        assert "year" in p
        assert p["year"] >= 2022


def test_api_get_paper_by_id():
    response = client.get("/api/research/papers/tyulmankov_2022")
    assert response.status_code == 200
    data = response.json()
    assert "paper" in data
    paper = data["paper"]
    assert paper["paper_id"] == "tyulmankov_2022"
    assert "doi" in paper

    # Test 404
    missing_response = client.get("/api/research/papers/nonexistent_paper_999")
    assert missing_response.status_code == 404


def test_api_list_claims():
    response = client.get("/api/research/claims")
    assert response.status_code == 200
    data = response.json()
    assert "claims" in data
    claims = data["claims"]
    assert isinstance(claims, list)
    assert len(claims) >= 5
    for c in claims:
        assert "claim_id" in c
        assert "claim_text" in c
        assert "what_this_does_not_prove" in c
        assert len(c["source_paper_ids"]) >= 1


def test_api_list_metrics():
    response = client.get("/api/research/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    metrics = data["metrics"]
    assert isinstance(metrics, list)
    assert len(metrics) >= 5
    for m in metrics:
        assert "metric_id" in m
        assert "formula" in m
        assert "limitation" in m


def test_api_get_research_graph():
    response = client.get("/api/research/graph")
    assert response.status_code == 200
    graph = response.json()
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0


def test_api_get_disclosures():
    response = client.get("/api/research/disclosures")
    assert response.status_code == 200
    data = response.json()
    assert "ai_assistance" in data
    assert "data_disclosure" in data
    assert "limitations" in data
    assert "learning_objectives" in data
    assert len(data["learning_objectives"]) == 7


def test_api_get_licenses():
    response = client.get("/api/research/licenses")
    assert response.status_code == 200
    data = response.json()
    assert "licenses" in data
    licenses = data["licenses"]
    assert isinstance(licenses, list)
    assert len(licenses) >= 5


def test_api_post_methodology():
    payload = {
        "experiment_type": "INTERFERENCE",
        "config": {
            "d": 16,
            "seed": 42,
            "decay": 0.05,
            "update_strength": 1.0,
            "concept_a": "cat",
            "value_a": "whiskers"
        }
    }
    response = client.post("/api/research/methodology", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert "methodology" in res_json
    methodology = res_json["methodology"]
    assert "experiment_type" in methodology
    assert "mathematical_operation" in methodology
    assert "reproducibility" in methodology
    assert methodology["reproducibility"]["deterministic"] is True
