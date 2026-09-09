"""Integration tests for Phase 22 Experiment Studio HTTP API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_get_templates_api(client):
    res = client.get("/api/studio/templates")
    assert res.status_code == 200
    data = res.json()
    assert "templates" in data
    assert len(data["templates"]) == 5


def test_get_guided_journey_api(client):
    res = client.get("/api/studio/guided-journey")
    assert res.status_code == 200
    data = res.json()
    assert "journey" in data
    assert data["journey"]["total_steps"] == 8


def test_run_experiment_api(client):
    payload = {
        "config": {
            "name": "API Test Experiment",
            "experiment_type": "INTERFERENCE",
            "seed": 42,
            "d": 16,
            "decay": 0.05,
            "update_strength": 1.0,
            "concept_a": "hawk",
            "value_a": "talons",
            "interfering_concept": "eagle",
            "interfering_value": "prey",
            "interfering_strength": 0.9,
        },
        "hypothesis": {
            "hypothesis_text": "Interfering eagle will modify shared synapses.",
            "predicted_outcome": "RETENTION_DROP",
            "predicted_challenge_choice": "B",
        },
    }
    res = client.post("/api/studio/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "result" in data
    res_data = data["result"]
    assert "baseline_metrics" in res_data
    assert "experiment_metrics" in res_data
    assert "delta_metrics" in res_data
    assert len(res_data["pipeline_steps"]) == 6


def test_ab_compare_api(client):
    payload = {
        "config_a": {
            "name": "Config Low",
            "experiment_type": "PERSISTENCE",
            "concept_a": "cat",
            "value_a": "whiskers",
            "decay_cycles": 1,
            "decay": 0.1,
        },
        "config_b": {
            "name": "Config High",
            "experiment_type": "PERSISTENCE",
            "concept_a": "cat",
            "value_a": "whiskers",
            "decay_cycles": 10,
            "decay": 0.1,
        },
    }
    res = client.post("/api/studio/ab-compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "comparison" in data
    assert "diff_summary" in data["comparison"]
    assert "decay_cycles" in data["comparison"]["differing_parameters"]


def test_sweep_api(client):
    payload = {
        "base_config": {
            "name": "Sweep Test",
            "experiment_type": "INTERFERENCE",
            "concept_a": "cat",
            "value_a": "whiskers",
            "interfering_concept": "tiger",
            "interfering_value": "stripes",
        },
        "param_name": "decay",
        "param_values": [0.0, 0.1, 0.2, 0.3, 0.5],
    }
    res = client.post("/api/studio/sweep", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "sweep" in data
    assert len(data["sweep"]["points"]) == 5


def test_history_and_detail_api(client):
    res = client.get("/api/studio/history")
    assert res.status_code == 200
    data = res.json()
    assert "history" in data
    assert len(data["history"]) >= 1

    first_id = data["history"][0]["experiment_id"]
    res_detail = client.get(f"/api/studio/experiment/{first_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["experiment"]["experiment_id"] == first_id


def test_branch_api(client):
    # Get history first
    h_res = client.get("/api/studio/history")
    first_id = h_res.json()["history"][0]["experiment_id"]

    branch_payload = {
        "experiment_id": first_id,
        "modified_param": "update_strength",
        "new_value": 1.8,
    }
    res = client.post("/api/studio/branch", json=branch_payload)
    assert res.status_code == 200
    assert res.json()["result"]["config"]["update_strength"] == 1.8


def test_notes_and_export_api(client):
    h_res = client.get("/api/studio/history")
    first_id = h_res.json()["history"][0]["experiment_id"]

    notes_payload = {
        "experiment_id": first_id,
        "question": "Can memories survive decay?",
        "hypothesis": "Low decay preserves recall.",
        "observation": "Measured retention > 90%.",
        "conclusion": "Synaptic weight matrix retained structure.",
    }
    res_notes = client.post("/api/studio/save-notes", json=notes_payload)
    assert res_notes.status_code == 200

    res_export = client.get(f"/api/studio/export/{first_id}")
    assert res_export.status_code == 200
    export_data = res_export.json()
    assert export_data["schema_version"] == "pathway.phase22.experiment_studio.v1"
    assert export_data["notes"]["question"] == "Can memories survive decay?"
