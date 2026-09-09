"""API tests for Phase 19: Adaptive Memory Observatory."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_observatory_presets(client):
    res = client.get("/api/observatory/presets")
    assert res.status_code == 200
    data = res.json()
    assert "presets" in data
    assert len(data["presets"]) >= 3
    preset_ids = [p["preset_id"] for p in data["presets"]]
    assert "env_shift" in preset_ids


def test_observatory_stream_run_preset(client):
    res = client.post("/api/observatory/stream/run", json={"preset_id": "env_shift", "dimension": 16})
    assert res.status_code == 200
    data = res.json()
    assert "session" in data
    assert "environment_shift_report" in data
    session = data["session"]
    assert len(session["snapshots"]) >= 10
    assert session["session_id"].startswith("OBS-")


def test_observatory_diff_and_stability(client):
    # First run stream
    run_res = client.post("/api/observatory/stream/run", json={"preset_id": "env_shift"})
    session_id = run_res.json()["session"]["session_id"]

    # Test diff
    diff_res = client.post("/api/observatory/diff", json={
        "session_id": session_id,
        "timestep_before": 1,
        "timestep_after": 2,
    })
    assert diff_res.status_code == 200
    diff = diff_res.json()["diff"]
    assert diff["timestep_before"] == 1
    assert diff["timestep_after"] == 2

    # Test stability-plasticity
    sp_res = client.post("/api/observatory/stability-plasticity", json={
        "session_id": session_id,
        "timestep_before": 1,
        "timestep_after": 2,
    })
    assert sp_res.status_code == 200
    metrics = sp_res.json()["metrics"]
    assert "stability_ratio" in metrics
    assert "plasticity_extent" in metrics


def test_observatory_intervention_and_counterfactual(client):
    run_res = client.post("/api/observatory/stream/run", json={"preset_id": "env_shift"})
    session_id = run_res.json()["session"]["session_id"]

    # Surgery intervention
    intv_res = client.post("/api/observatory/intervention", json={
        "session_id": session_id,
        "step": 2,
        "operation": "silence",
        "synapse_ids": ["syn_k0_v0"],
    })
    assert intv_res.status_code == 200
    assert "branch_session" in intv_res.json()

    # Counterfactual
    cf_res = client.post("/api/observatory/counterfactual", json={
        "session_id": session_id,
        "step": 5,
        "label": "Test CF",
    })
    assert cf_res.status_code == 200
    assert "branch_session" in cf_res.json()


def test_observatory_predict_and_export(client):
    run_res = client.post("/api/observatory/stream/run", json={"preset_id": "env_shift"})
    session_id = run_res.json()["session"]["session_id"]

    # Prediction test
    pred_res = client.post("/api/observatory/predict", json={
        "session_id": session_id,
        "target_timestep": 6,
        "target_memory": "solaris",
        "predicted_choice": "B",
        "choice_label": "Memory will weaken due to competing write",
    })
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert "prediction" in pred_data
    assert "is_accurate" in pred_data

    # Export Detective Case
    case_res = client.post("/api/observatory/export-case", json={
        "session_id": session_id,
        "anomaly_step": 6,
        "target_memory": "solaris",
    })
    assert case_res.status_code == 200
    case_data = case_res.json()["case"]
    assert case_data["case_code"] == "CASE_OBSERVATORY_STREAM_ANOMALY"

    # Export Session JSON
    export_res = client.get(f"/api/observatory/export/{session_id}")
    assert export_res.status_code == 200
    exp_json = export_res.json()
    assert exp_json["export_format"] == "PATHWAY_OBSERVATORY_V1"
    assert "sha256" in exp_json
