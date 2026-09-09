"""API endpoint tests for Phase 08 /api/genome routes."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore
from core import ExperimentConfig, run_experiment


@pytest.fixture
def client_with_demo() -> tuple[TestClient, str]:
    store = ExperimentStore()
    config = ExperimentConfig.from_api({
        "seed": 42,
        "mechanism": "interference",
        "task_name": "associative_recall",
        "d": 128,
        "num_events": 10,
    })
    demo_exp = run_experiment(config)
    store.save(demo_exp)
    app = create_app(store)
    return TestClient(app), demo_exp.experiment_id


def test_api_get_genome(client_with_demo):
    client, exp_id = client_with_demo
    resp = client.get(f"/api/genome/{exp_id}/obj_A")
    assert resp.status_code == 200
    data = resp.json()
    assert "genome" in data
    assert data["genome"]["memory_id"] == "e0000"
    assert "dna_strip" in data["genome"]


def test_api_get_lineage(client_with_demo):
    client, exp_id = client_with_demo
    resp = client.get(f"/api/genome/{exp_id}/obj_A/lineage")
    assert resp.status_code == 200
    data = resp.json()
    assert "lineage" in data
    assert len(data["lineage"]["nodes"]) >= 3


def test_api_run_cascade(client_with_demo):
    client, exp_id = client_with_demo
    payload = {
        "experiment_id": exp_id,
        "target_memory": "obj_A",
        "intervention": "remove",
        "dose": 1.0,
    }
    resp = client.post("/api/genome/cascade", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "cascade" in data
    assert "influence_breakdown" in data
    assert data["cascade"]["target_memory"] == "e0000"


def test_api_centrality_and_critical_memories(client_with_demo):
    client, exp_id = client_with_demo
    resp1 = client.get(f"/api/genome/{exp_id}/centrality")
    assert resp1.status_code == 200
    assert "centrality" in resp1.json()

    resp2 = client.get(f"/api/genome/{exp_id}/critical-memories")
    assert resp2.status_code == 200
    assert "critical_memories" in resp2.json()


def test_api_fragility_and_redundancy(client_with_demo):
    client, exp_id = client_with_demo
    resp1 = client.get(f"/api/genome/{exp_id}/obj_A/fragility")
    assert resp1.status_code == 200
    assert "fragility" in resp1.json()

    resp2 = client.get(f"/api/genome/{exp_id}/obj_A/redundancy")
    assert resp2.status_code == 200
    assert "redundancy" in resp2.json()


def test_api_dose_response(client_with_demo):
    client, exp_id = client_with_demo
    payload = {"experiment_id": exp_id, "target_memory": "obj_A"}
    resp = client.post("/api/genome/dose-response", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "dose_response" in data
    assert len(data["dose_response"]["points"]) == 5


def test_api_recovery_and_path_dependence(client_with_demo):
    client, exp_id = client_with_demo
    resp1 = client.post("/api/genome/recovery-test", json={"experiment_id": exp_id, "target_memory": "obj_A"})
    assert resp1.status_code == 200
    assert "recovery" in resp1.json()

    resp2 = client.get(f"/api/genome/{exp_id}/path-dependence")
    assert resp2.status_code == 200
    assert "path_dependence" in resp2.json()


def test_api_sandbox_and_dependency_matrix(client_with_demo):
    client, exp_id = client_with_demo
    resp1 = client.post(
        "/api/genome/sandbox/branch",
        json={
            "experiment_id": exp_id,
            "parent_id": "base",
            "intervention": {"target_memory": "obj_A", "intervention_type": "remove"},
        },
    )
    assert resp1.status_code == 200
    assert "branch" in resp1.json()

    resp2 = client.get(f"/api/genome/{exp_id}/dependency-matrix?metric=association")
    assert resp2.status_code == 200
    assert "dependency_matrix" in resp2.json()


def test_api_reports_and_questions(client_with_demo):
    client, exp_id = client_with_demo
    resp1 = client.get(f"/api/genome/{exp_id}/obj_A/report")
    assert resp1.status_code == 200
    assert "report" in resp1.json()

    resp2 = client.get(f"/api/genome/{exp_id}/obj_A/questions")
    assert resp2.status_code == 200
    assert "questions" in resp2.json()
