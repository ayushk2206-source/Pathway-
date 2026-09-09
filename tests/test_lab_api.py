"""Integration tests for Experiment Lab FastAPI endpoints (Phase 03)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore


@pytest.fixture()
def client(tmp_path):
    app = create_app(store=ExperimentStore(tmp_path / "store"))
    with TestClient(app) as c:
        yield c


def test_api_list_variables(client):
    r = client.get("/api/lab/variables")
    assert r.status_code == 200
    data = r.json()
    assert "variables" in data
    assert "independent" in data
    assert "dependent" in data
    assert "memory_similarity" in data["independent"]


def test_api_create_and_get_experiment(client):
    req = {
        "title": "API Test Study",
        "research_question": "Does decay reduce retention?",
        "mechanism": "leaky",
        "baseline_configuration": {"decay": 0.2, "state_dim": 64},
        "run_immediately": True,
        "trials": 1,
    }
    r = client.post("/api/lab/experiments", json=req)
    assert r.status_code == 200
    exp = r.json()
    exp_id = exp["experiment_id"]
    assert exp["status"] == "completed"

    # Get by ID
    r_get = client.get(f"/api/lab/experiments/{exp_id}")
    assert r_get.status_code == 200
    assert r_get.json()["experiment_id"] == exp_id

    # List
    r_list = client.get("/api/lab/experiments")
    assert r_list.status_code == 200
    assert any(e["experiment_id"] == exp_id for e in r_list.json()["experiments"])


def test_api_parameter_sweep(client):
    req = {
        "parameter": "update_strength",
        "values": [0.2, 0.6, 1.0],
        "base_config": {"state_dim": 64, "mechanism": "baseline"},
        "trials": 1,
    }
    r = client.post("/api/lab/sweep", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["parameter"] == "update_strength"
    assert len(body["conditions"]) == 3
    assert "experiment_id" in body


def test_api_grid_sweep(client):
    req = {
        "param_x": "memory_similarity",
        "values_x": [0.0, 0.6],
        "param_y": "update_strength",
        "values_y": [0.5, 1.0],
        "base_config": {"state_dim": 64, "mechanism": "interference"},
        "trials": 1,
    }
    r = client.post("/api/lab/grid", json=req)
    assert r.status_code == 200
    body = r.json()
    assert len(body["cells"]) == 4
    assert "matrix_metrics" in body


def test_api_controlled_comparison(client):
    req = {
        "baseline_config": {"mechanism": "baseline", "state_dim": 64, "update_strength": 0.2},
        "treatment_config": {"mechanism": "baseline", "state_dim": 64, "update_strength": 1.0},
        "trials": 1,
    }
    r = client.post("/api/lab/compare", json=req)
    assert r.status_code == 200
    body = r.json()
    assert "metric_deltas" in body
    assert "percentage_changes" in body


def test_api_hypothesis_lifecycle_and_evaluation(client):
    # 1. Create hypothesis
    hyp_req = {
        "statement": "Higher update strength yields greater update magnitude",
        "independent_variable": "update_strength",
        "dependent_variable": "update_magnitude",
        "predicted_direction": "increase",
        "confidence_before": 0.6,
    }
    r_hyp = client.post("/api/lab/hypotheses", json=hyp_req)
    assert r_hyp.status_code == 200
    hyp_id = r_hyp.json()["hypothesis_id"]

    # 2. Run experiment
    comp_req = {
        "baseline_config": {"mechanism": "baseline", "state_dim": 64, "update_strength": 0.2},
        "treatment_config": {"mechanism": "baseline", "state_dim": 64, "update_strength": 1.0},
        "trials": 1,
    }
    r_exp = client.post("/api/lab/compare", json=comp_req)
    exp_id = r_exp.json()["experiment_id"]

    # 3. Evaluate hypothesis against experiment
    eval_req = {"experiment_id": exp_id}
    r_eval = client.post(f"/api/lab/hypotheses/{hyp_id}/evaluate", json=eval_req)
    assert r_eval.status_code == 200
    eval_res = r_eval.json()
    assert eval_res["evaluation"]["prediction_correct"] is True
    assert eval_res["hypothesis"]["status"] == "supported"


def test_api_suggest_next_and_discriminating(client):
    # Suggest next
    sugg_req = {
        "parameter": "memory_similarity",
        "tested_values": [0.1, 0.4, 0.6, 0.9],
        "observed_metrics": [0.1, 0.2, 0.8, 0.9],
        "metric_name": "interference_score",
    }
    r_sugg = client.post("/api/lab/suggest-next", json=sugg_req)
    assert r_sugg.status_code == 200
    assert len(r_sugg.json()["suggested_values"]) > 0

    # Discriminating experiment
    disc_req = {
        "hypotheses": [
            {
                "statement": "H1",
                "independent_variable": "memory_similarity",
                "dependent_variable": "interference_score",
                "predicted_direction": "increase",
            },
            {
                "statement": "H2",
                "independent_variable": "update_strength",
                "dependent_variable": "interference_score",
                "predicted_direction": "increase",
            },
        ],
        "base_config": {"mechanism": "interference"},
    }
    r_disc = client.post("/api/lab/discriminating-experiment", json=disc_req)
    assert r_disc.status_code == 200
    assert r_disc.json()["valid"] is True


def test_api_report_and_export(client):
    # Run a quick experiment first
    sweep_req = {
        "parameter": "decay",
        "values": [0.0, 0.4],
        "base_config": {"state_dim": 64, "mechanism": "leaky"},
    }
    r_sw = client.post("/api/lab/sweep", json=sweep_req)
    exp_id = r_sw.json()["experiment_id"]

    # 10-section report
    r_rep = client.get(f"/api/lab/experiments/{exp_id}/report")
    assert r_rep.status_code == 200
    rep_md = r_rep.json()["report_markdown"]
    assert "## 1. Research Question" in rep_md
    assert "## 10. Conclusion" in rep_md

    # JSON export
    r_exp_json = client.get(f"/api/lab/experiments/{exp_id}/export?format=json")
    assert r_exp_json.status_code == 200
    assert "application/json" in r_exp_json.headers["content-type"]

    # CSV export
    r_exp_csv = client.get(f"/api/lab/experiments/{exp_id}/export?format=csv")
    assert r_exp_csv.status_code == 200
    assert "text/csv" in r_exp_csv.headers["content-type"]
    assert "param_decay" in r_exp_csv.text


def test_api_reproduce_experiment(client):
    req = {
        "title": "Repro Test",
        "research_question": "Can we reproduce?",
        "mechanism": "leaky",
        "baseline_configuration": {"decay": 0.2, "state_dim": 64},
        "run_immediately": True,
        "trials": 1,
    }
    r_create = client.post("/api/lab/experiments", json=req)
    exp_id = r_create.json()["experiment_id"]

    r_repro = client.post(f"/api/lab/experiments/{exp_id}/reproduce", json={"tolerance": 1e-9})
    assert r_repro.status_code == 200
    assert r_repro.json()["reproduced"] is True
    assert r_repro.json()["exact_match"] is True
