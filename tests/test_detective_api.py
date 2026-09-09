"""API tests for Detective & Hypothesis Engine routes (Phase 07)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore
from core import ExperimentConfig, run_experiment
from core.mechanisms.base import MechanismParams
from core.task import TaskConfig


@pytest.fixture
def detective_api_client(tmp_path):
    store = ExperimentStore(directory=tmp_path)
    app = create_app(store)
    client = TestClient(app)

    cfg = ExperimentConfig(
        seed=300,
        mechanism="interference",
        params=MechanismParams(state_dim=64, update_strength=0.85, memory_strength=1.0),
        task=TaskConfig(seed=300, d=64, n_objects=4, n_symbols=4, n_conflicts=2, cycles=1),
    )
    exp = run_experiment(cfg)
    store.save(exp)

    return {
        "client": client,
        "store": store,
        "exp": exp,
    }


def test_api_parse_question(detective_api_client):
    client = detective_api_client["client"]
    resp = client.post("/api/detective/parse-question", json={"question": "Why did memory obj_A weaken?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"].lower() in ["interference", "memory_decay", "decay", "overwritten"]
    assert data["target_memory"] == "obj_A"
    assert len(data["suggested_tests"]) > 0


def test_api_investigate(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    resp = client.post(
        "/api/detective/investigate",
        json={
            "experiment_id": exp.experiment_id,
            "question": "Why did memory obj_A weaken?",
            "target_memory": "obj_A",
            "execute_tests": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "investigation_id" in data
    assert len(data["observations"]) > 0
    assert len(data["candidate_hypotheses"]) >= 3
    assert len(data["tests"]) > 0
    assert "scorecard" in data
    assert data["scorecard"]["verdict"] in [
        "COUNTERFACTUALLY_SUPPORTED",
        "UNSUPPORTED",
        "CONTRADICTED",
        "INCONCLUSIVE",
    ]


def test_api_hypotheses_and_test(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    # Generate hypotheses
    h_resp = client.post(
        "/api/detective/hypotheses",
        json={
            "experiment_id": exp.experiment_id,
            "target_memory": "obj_A",
            "intent": "interference",
        },
    )
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert len(h_data["hypotheses"]) >= 3

    hyp = h_data["hypotheses"][0]

    # Execute specific test
    t_resp = client.post(
        "/api/detective/test",
        json={
            "experiment_id": exp.experiment_id,
            "hypothesis_id": hyp["hypothesis_id"],
            "test_design": {
                "test_id": "test-custom-1",
                "hypothesis_id": hyp["hypothesis_id"],
                "description": "Test removal",
                "intervention_type": "remove_event",
                "target_timestep": 1,
                "target_event_id": "e0001",
                "target_memory": "obj_A",
            },
        },
    )
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert "test_result" in t_data
    assert "evidence_chain" in t_data
    assert t_data["test_result"]["causal_support"] in [
        "COUNTERFACTUALLY_SUPPORTED",
        "UNSUPPORTED",
        "CONTRADICTED",
    ]


def test_api_autopsy(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    resp = client.get(f"/api/detective/autopsy/{exp.experiment_id}/obj_A")
    assert resp.status_code == 200
    data = resp.json()
    assert "autopsy" in data
    assert "formation" in data["autopsy"]
    assert "reinforcement" in data["autopsy"]
    assert "competition" in data["autopsy"]
    assert len(data["autopsy"]["supporting_evidence"]) > 0


def test_api_sensitivity(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    resp = client.get(f"/api/detective/sensitivity/{exp.experiment_id}/obj_A")
    assert resp.status_code == 200
    data = resp.json()
    assert "sensitivity" in data
    assert "minimum_intervention" in data
    assert "robustness" in data
    assert data["sensitivity"]["memory_id"] == "obj_A"


def test_api_discovery_feed(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    resp = client.get(f"/api/detective/discovery/{exp.experiment_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "discoveries" in data
    assert data["discoveries_count"] >= 0


def test_api_investigations_lifecycle(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    # 1. Run investigation
    inv_resp = client.post(
        "/api/detective/investigate",
        json={
            "experiment_id": exp.experiment_id,
            "question": "Why did memory obj_A weaken?",
            "target_memory": "obj_A",
        },
    )
    inv_id = inv_resp.json()["investigation_id"]

    # 2. List investigations
    list_resp = client.get(f"/api/detective/investigations?experiment_id={exp.experiment_id}")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 3. Get single investigation
    get_resp = client.get(f"/api/detective/investigations/{inv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["investigation_id"] == inv_id

    # 4. Get Scorecard
    sc_resp = client.get(f"/api/detective/investigations/{inv_id}/scorecard")
    assert sc_resp.status_code == 200
    assert "primary_hypothesis" in sc_resp.json()

    # 5. Reproduce
    repro_resp = client.post(f"/api/detective/investigations/{inv_id}/reproduce", json={})
    assert repro_resp.status_code == 200
    repro_id = repro_resp.json()["investigation_id"]
    assert repro_id != inv_id

    # 6. Diff
    diff_resp = client.get(f"/api/detective/investigations/{inv_id}/diff/{repro_id}")
    assert diff_resp.status_code == 200
    diff_data = diff_resp.json()
    assert diff_data["question_match"] is True


def test_api_notebook_crud(detective_api_client):
    client = detective_api_client["client"]
    exp = detective_api_client["exp"]

    # Create note
    post_resp = client.post(
        "/api/detective/notebook",
        json={
            "experiment_id": exp.experiment_id,
            "title": "Cross-talk verification note",
            "content": "Observed sharp drop in cosine readout at step 2 after sequence overlap write.",
            "author": "Forensic Agent",
            "tags": ["interference", "cross-talk"],
        },
    )
    assert post_resp.status_code == 200
    entry_id = post_resp.json()["entry_id"]

    # List notes
    list_resp = client.get(f"/api/detective/notebook?experiment_id={exp.experiment_id}")
    assert list_resp.status_code == 200
    entries = list_resp.json()["entries"]
    assert any(e["entry_id"] == entry_id for e in entries)

    # Delete note
    del_resp = client.delete(f"/api/detective/notebook/{exp.experiment_id}/{entry_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"
