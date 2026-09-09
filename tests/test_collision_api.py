"""API tests for Phase 17 Collision Lab endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_collision_info_endpoint(client):
    res = client.get("/api/collision/info")
    assert res.status_code == 200
    data = res.json()
    assert "Memory Collision & Interference Lab" in data["title"]
    assert "collision_matrix" in data["equations"]


def test_collision_run_endpoint(client):
    payload = {
        "seed": 42,
        "dimension": 16,
        "decay": 0.05,
        "update_strength": 1.0,
        "memory_a": {"concept": "apple", "value": "fruit", "importance": 1.0, "strength": 1.0},
        "memory_b": {"concept": "orange", "value": "citrus", "importance": 1.0, "strength": 1.0},
        "order": "A_THEN_B",
        "temporal_delay": 0,
        "overlap_preset": "MODERATE",
        "concept_similarity": 0.45,
    }
    res = client.post("/api/collision/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "collision_id" in data
    assert "representational_overlap" in data
    assert "synaptic_overlap_fraction" in data
    assert "combined_recall_a" in data
    assert "combined_recall_b" in data
    assert "collision_map" in data
    assert len(data["collision_map"]) == 16 * 16


def test_collision_three_conditions_endpoint(client):
    payload = {
        "seed": 42,
        "dimension": 16,
        "decay": 0.05,
        "update_strength": 1.0,
        "memory_a": {"concept": "sun", "value": "hot"},
        "memory_b": {"concept": "star", "value": "bright"},
        "order": "A_THEN_B",
        "temporal_delay": 0,
    }
    res = client.post("/api/collision/three-conditions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recall_matrix" in data
    assert len(data["recall_matrix"]) == 3
    assert data["recall_matrix"][0]["condition"] == "LOW OVERLAP"
    assert data["recall_matrix"][1]["condition"] == "MODERATE OVERLAP"
    assert data["recall_matrix"][2]["condition"] == "HIGH OVERLAP"


def test_collision_order_comparison_endpoint(client):
    payload = {
        "seed": 42,
        "dimension": 16,
        "decay": 0.05,
        "update_strength": 1.0,
        "memory_a": {"concept": "dog", "value": "bark"},
        "memory_b": {"concept": "wolf", "value": "howl"},
        "overlap_preset": "MODERATE",
        "concept_similarity": 0.45,
        "temporal_delay": 1,
    }
    res = client.post("/api/collision/order-comparison", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "order_a_then_b" in data
    assert "order_b_then_a" in data
    assert "matrix_frobenius_difference" in data


def test_collision_surgery_endpoint(client):
    cfg_payload = {
        "seed": 42,
        "dimension": 16,
        "decay": 0.05,
        "update_strength": 1.0,
        "memory_a": {"concept": "king", "value": "crown"},
        "memory_b": {"concept": "queen", "value": "throne"},
        "order": "A_THEN_B",
        "temporal_delay": 0,
        "overlap_preset": "HIGH",
        "concept_similarity": 0.85,
    }
    run_res = client.post("/api/collision/run", json=cfg_payload)
    assert run_res.status_code == 200
    run_data = run_res.json()
    shared_syns = run_data["shared_synapses"]
    assert len(shared_syns) > 0

    surg_payload = {
        "config": cfg_payload,
        "synapse_id": shared_syns[0],
        "operation": "silence",
        "factor": 0.0,
    }
    surg_res = client.post("/api/collision/surgery", json=surg_payload)
    assert surg_res.status_code == 200
    surg_data = surg_res.json()
    assert surg_data["status"] == "success"
    assert surg_data["target_synapse"] == shared_syns[0]
    assert surg_data["post_surgery_weight"] == 0.0


def test_collision_counterfactual_endpoint(client):
    cfg_payload = {
        "seed": 42,
        "dimension": 16,
        "decay": 0.05,
        "update_strength": 1.0,
        "memory_a": {"concept": "ocean", "value": "water"},
        "memory_b": {"concept": "lake", "value": "fresh"},
        "order": "A_THEN_B",
        "temporal_delay": 0,
        "overlap_preset": "HIGH",
        "concept_similarity": 0.85,
    }
    cf_payload = {
        "config": cfg_payload,
    }
    cf_res = client.post("/api/collision/counterfactual", json=cf_payload)
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert cf_data["status"] == "success"
    assert "counterfactual_recall_a" in cf_data
    assert "scientific_conclusion" in cf_data
