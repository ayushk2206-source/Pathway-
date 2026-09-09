"""API Integration Tests for Phase 21: Memory Ecosystem."""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_api_ecosystem_overview(client):
    res = client.get("/api/ecosystem/overview")
    assert res.status_code == 200
    data = res.json()
    assert "active_memory_id" in data
    assert "active_passport" in data
    assert "passports" in data
    assert data["total_memories"] >= 4
    assert "Recent activity temporarily changes synaptic connections" in data["scientific_claim"]


def test_api_ecosystem_memory_details(client):
    res = client.get("/api/ecosystem/memory/M-001")
    assert res.status_code == 200
    data = res.json()
    assert data["passport"]["memory_id"] == "M-001"
    assert len(data["lifecycle"]["stages"]) == 8
    assert data["branch_tree"]["branch_type"] == "ORIGINAL"
    assert "ledger" in data


def test_api_ecosystem_select_memory(client):
    res = client.post("/api/ecosystem/select-memory", json={"memory_id": "M-002", "follow": True})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["active_memory_id"] == "M-002"
    assert data["is_following"] is True


def test_api_ecosystem_timeline(client):
    res = client.get("/api/ecosystem/timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["total_events"] > 0
    assert len(data["events"]) == data["total_events"]

    # Filtered
    res_m1 = client.get("/api/ecosystem/timeline?memory_id=M-001")
    assert res_m1.status_code == 200
    data_m1 = res_m1.json()
    assert data_m1["memory_id"] == "M-001"
    assert all(e["memory_id"] == "M-001" for e in data_m1["events"])


def test_api_ecosystem_relationships(client):
    res = client.get("/api/ecosystem/relationships")
    assert res.status_code == 200
    data = res.json()
    assert data["total_relationships"] > 0
    assert len(data["relationships"]) == data["total_relationships"]


def test_api_ecosystem_ledger(client):
    res = client.get("/api/ecosystem/ledger/M-001?transition=SYNAPTIC%20WRITE")
    assert res.status_code == 200
    data = res.json()
    assert data["ledger"]["transition_name"] == "SYNAPTIC WRITE"
    assert "before" in data["ledger"]
    assert "after" in data["ledger"]


def test_api_ecosystem_hypothesis(client):
    res = client.post("/api/ecosystem/hypothesis", json={
        "memory_id": "M-001",
        "experiment_type": "INTERFERENCE",
        "prediction_text": "Interference will degrade retention.",
        "predicted_outcome": "RETENTION_DROP",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["hypothesis"]["memory_id"] == "M-001"
    assert data["hypothesis"]["is_match"] is True

    # List
    list_res = client.get("/api/ecosystem/hypotheses?memory_id=M-001")
    assert list_res.status_code == 200
    assert len(list_res.json()["hypotheses"]) >= 1


def test_api_ecosystem_checkpoints(client):
    res = client.post("/api/ecosystem/checkpoint", json={
        "memory_id": "M-001",
        "label": "Test REST Checkpoint",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["checkpoint"]["memory_id"] == "M-001"
    assert data["checkpoint"]["label"] == "Test REST Checkpoint"

    list_res = client.get("/api/ecosystem/checkpoints/M-001")
    assert list_res.status_code == 200
    assert any(cp["label"] == "Test REST Checkpoint" for cp in list_res.json()["checkpoints"])


def test_api_ecosystem_compare_states(client):
    res = client.post("/api/ecosystem/compare-states", json={
        "state_a": {"W_norm": 0.85, "active_ratio": 0.6},
        "state_b": {"W_norm": 1.15, "active_ratio": 0.75},
    })
    assert res.status_code == 200
    data = res.json()
    assert data["comparison"]["frobenius_drift"] == 0.3


def test_api_ecosystem_replay(client):
    res = client.get("/api/ecosystem/replay/M-001")
    assert res.status_code == 200
    data = res.json()
    assert data["memory_id"] == "M-001"
    assert data["total_steps"] >= 2
    assert "TEACHING SIMPLIFICATION" in data["disclaimer"]
