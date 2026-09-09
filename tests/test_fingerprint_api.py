"""Tests for Phase 20 FastAPI Endpoints (backend/fingerprint_routes.py)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_get_demo(client):
    res = client.get("/api/fingerprint/demo")
    assert res.status_code == 200
    data = res.json()
    assert "fingerprints" in data
    assert len(data["fingerprints"]) >= 3
    assert "distance_map" in data
    assert "outliers" in data
    assert "challenges" in data


def test_compute_fingerprint(client):
    res = client.post(
        "/api/fingerprint/compute",
        json={
            "concept": "Test Memory API",
            "value": "Test Value API",
            "dimension": 16,
            "seed": 42,
            "update_strength": 0.35,
            "decay": 0.01,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "fingerprint" in data
    assert data["fingerprint"]["concept"] == "Test Memory API"


def test_compare_fingerprints(client):
    res = client.post(
        "/api/fingerprint/compare",
        json={
            "concept_a": "Concept A",
            "concept_b": "Concept B",
            "dimension": 16,
            "seed": 42,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "fingerprint_a" in data
    assert "fingerprint_b" in data
    assert "comparison" in data
    assert "similarity_discrepancy" in data["comparison"]


def test_surface_vs_internal(client):
    res = client.post(
        "/api/fingerprint/surface-vs-internal",
        json={
            "concepts": ["Concept 1", "Concept 2", "Concept 3"],
            "dimension": 16,
            "seed": 42,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "comparisons" in data
    assert data["total_pairs"] == 3


def test_cloning_test(client):
    res = client.post(
        "/api/fingerprint/cloning-test",
        json={
            "target_concept": "Alpha",
            "target_value": "Val Alpha",
            "intervening_concept": "Beta",
            "intervening_value": "Val Beta",
            "dimension": 16,
            "seed": 42,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "fingerprint_before" in data
    assert "fingerprint_after" in data
    assert "stability_conclusion" in data


def test_collision_mutation(client):
    res = client.post(
        "/api/fingerprint/collision-mutation",
        json={
            "concept_a": "Alpha",
            "value_a": "Val Alpha",
            "concept_b": "Beta",
            "value_b": "Val Beta",
            "dimension": 16,
            "seed": 42,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "mutation_comparison" in data


def test_surgery(client):
    res = client.post(
        "/api/fingerprint/surgery",
        json={
            "concept": "Surgery Memory",
            "value": "Surgery Val",
            "target_synapse": [0, 1],
            "new_weight": 0.0,
            "dimension": 16,
            "seed": 42,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "weight_before" in data
    assert data["weight_after"] == 0.0


def test_counterfactual(client):
    res = client.post(
        "/api/fingerprint/counterfactual",
        json={
            "concept": "CF Memory",
            "value": "CF Val",
            "cf_update_strength": 0.05,
            "dimension": 16,
            "seed": 42,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "original_fingerprint" in data
    assert "counterfactual_fingerprint" in data


def test_distance_map_and_outliers(client):
    res_map = client.get("/api/fingerprint/distance-map?dimension=16&seed=42")
    assert res_map.status_code == 200
    data_map = res_map.json()
    assert "distance_map" in data_map

    res_out = client.get("/api/fingerprint/outliers?dimension=16&seed=42")
    assert res_out.status_code == 200
    data_out = res_out.json()
    assert "outliers" in data_out


def test_family_tree(client):
    res = client.get("/api/fingerprint/family-tree/Concept%20Alpha?dimension=16&seed=42")
    assert res.status_code == 200
    data = res.json()
    assert "family_tree" in data
    assert data["family_tree"]["branch_type"] == "ORIGINAL"


def test_challenges_flow(client):
    res = client.get("/api/fingerprint/challenges")
    assert res.status_code == 200
    data = res.json()
    assert len(data["challenges"]) >= 1

    ch = data["challenges"][0]
    res_verify = client.post(
        "/api/fingerprint/challenges/verify",
        json={
            "challenge_id": ch["challenge_id"],
            "selected_option": ch["correct_option"],
        },
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["is_correct"] is True


def test_export_json(client):
    res = client.post(
        "/api/fingerprint/export",
        json={
            "concept": "Export Concept",
            "value": "Export Value",
            "dimension": 16,
            "seed": 42,
            "update_strength": 0.35,
            "decay": 0.01,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "pathway_synaptic_fingerprint_v1"
    assert "statistics" in data
