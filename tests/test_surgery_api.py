"""API tests for Synaptic Surgery routes (Phase 15)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.surgery_routes import set_active_surgery_session
from backend.synaptic_routes import get_live_brain


@pytest.fixture
def client():
    set_active_surgery_session(None)
    app = create_app()
    return TestClient(app)


def test_surgery_state_unlocked(client):
    res = client.get("/api/surgery/state")
    assert res.status_code == 200
    data = res.json()
    assert data["locked"] is False
    assert data["session"] is None


def test_surgery_requires_lock_first(client):
    res = client.post("/api/surgery/weaken", json={"synapse_ids": ["syn_k0_v0"], "factor": 0.5})
    assert res.status_code == 400
    assert "No active surgery session" in res.json()["detail"]


def test_lock_and_operations_lifecycle(client):
    # 1. Write something to live brain first
    write_res = client.post("/api/synaptic/write", json={"concept": "gold", "value": "metal"})
    assert write_res.status_code == 200

    # 2. Lock baseline
    lock_res = client.post("/api/surgery/lock", json={"dimension": 16, "seed": 42, "decay": 0.05})
    assert lock_res.status_code == 200
    lock_data = lock_res.json()
    assert lock_data["status"] == "locked"
    session_id = lock_data["session"]["session_id"]

    # 3. Check surgery state
    state_res = client.get("/api/surgery/state")
    assert state_res.status_code == 200
    assert state_res.json()["locked"] is True
    assert state_res.json()["session"]["session_id"] == session_id

    # 4. Weaken synapses
    weaken_res = client.post("/api/surgery/weaken", json={"synapse_ids": ["syn_k0_v0"], "factor": 0.3})
    assert weaken_res.status_code == 200
    assert weaken_res.json()["operation"]["operation"] == "weaken"

    # 5. Strengthen synapses
    strengthen_res = client.post("/api/surgery/strengthen", json={"synapse_ids": ["syn_k1_v1"], "factor": 2.5})
    assert strengthen_res.status_code == 200
    assert strengthen_res.json()["operation"]["operation"] == "strengthen"

    # 6. Silence synapses (controlled ablation)
    silence_res = client.post("/api/surgery/silence", json={"synapse_ids": ["syn_k2_v2"]})
    assert silence_res.status_code == 200
    assert silence_res.json()["operation"]["operation"] == "silence"

    # 7. Check synapse xray
    xray_res = client.get("/api/surgery/synapse/syn_k2_v2/xray")
    assert xray_res.status_code == 200
    xray_data = xray_res.json()
    assert xray_data["synapse_id"] == "syn_k2_v2"
    assert xray_data["surgery_weight"] == 0.0
    assert xray_data["is_modified"] is True

    # 8. Restore synapse
    restore_res = client.post("/api/surgery/restore", json={"synapse_ids": ["syn_k2_v2"]})
    assert restore_res.status_code == 200
    assert restore_res.json()["operation"]["operation"] == "restore"

    # 9. Run side-by-side recall comparison
    recall_res = client.post("/api/surgery/recall", json={"query_concept": "gold", "expected_value": "metal"})
    assert recall_res.status_code == 200
    comp = recall_res.json()["comparison"]
    assert comp["query_concept"] == "gold"
    assert "baseline" in comp
    assert "surgery" in comp
    assert "change" in comp
    assert comp["caution_note"] != ""

    # 10. Reset session
    reset_res = client.post("/api/surgery/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["operation"]["operation"] == "restore_all"


def test_memory_xray_endpoint(client):
    client.post("/api/synaptic/write", json={"concept": "ocean", "value": "blue"})
    res = client.post("/api/surgery/xray/memory", json={"query_concept": "ocean", "expected_value": "blue"})
    assert res.status_code == 200
    data = res.json()
    assert data["query_concept"] == "ocean"
    assert "summary" in data
    assert data["summary"]["total_synapses_analyzed"] > 0
    assert len(data["synapses"]) > 0
    assert "relevance_score" in data["synapses"][0]
    assert "transparency" in data
