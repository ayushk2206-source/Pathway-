"""API endpoint tests for Phase 18 Forensics & Research Lab routes."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_learning_objectives_endpoint(client):
    res = client.get("/api/forensics/learning-objectives")
    assert res.status_code == 200
    data = res.json()
    assert "objectives" in data
    assert len(data["objectives"]) >= 5


def test_sources_and_claim_traceability_endpoint(client):
    res = client.get("/api/forensics/sources")
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert len(data["sources"]) >= 3
    assert "claims" in data
    assert len(data["claims"]) > 0


def test_list_cases_endpoint(client):
    res = client.get("/api/forensics/cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) == 6
    case_ids = [c["case_id"] for c in cases]
    assert "CASE-001" in case_ids
    assert "CASE-002" in case_ids


def test_get_case_blind_mode(client):
    res = client.get("/api/forensics/cases/CASE-002?blind=true")
    assert res.status_code == 200
    case = res.json()
    assert case["case_id"] == "CASE-002"
    # Ground truth must be obscured in blind mode
    assert case["ground_truth_hypothesis_id"] is None
    assert case["ground_truth_explanation"] is None
    for h in case["candidate_hypotheses"]:
        assert h["is_correct"] is None


def test_test_hypothesis_endpoint(client):
    payload = {
        "case_id": "CASE-002",
        "hypothesis_id": "HYP-B1",
        "learner_confidence": "HIGH",
        "chosen_tool": "collision",
    }
    res = client.post("/api/forensics/cases/CASE-002/test-hypothesis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "CASE-002"
    assert data["outcome"] == "CONFIRMED"
    assert "measured_result" in data
    assert "unlocked_evidence" in data


def test_submit_verdict_endpoint(client):
    payload = {
        "case_id": "CASE-002",
        "chosen_hypothesis_id": "HYP-B1",
        "collected_evidence_ids": ["EV-B1", "EV-B2", "EV-B3"],
        "tests_run_count": 2,
        "learner_confidence": "HIGH",
        "explanation_chain": ["MEMORY_WRITE", "COLLISION", "CROSSTALK", "RECALL_DROP"],
    }
    res = client.post("/api/forensics/cases/CASE-002/submit-verdict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_correct"] is True
    assert data["scorecard"]["score"] >= 90
    assert "case_conclusion" in data


def test_research_lab_lifecycle_endpoints(client):
    # 1. Run first custom experiment
    exp1_payload = {
        "name": "Exp 1 - Baseline",
        "dimension": 16,
        "decay": 0.02,
        "plasticity_eta": 1.0,
        "memories": [{"concept": "a", "value": "1"}, {"concept": "b", "value": "2"}],
        "concept_similarity": 0.1,
        "seed": 42,
        "notes": "Testing low decay",
    }
    res1 = client.post("/api/forensics/research/run", json=exp1_payload)
    assert res1.status_code == 200
    exp1_data = res1.json()
    assert exp1_data["run_id"].startswith("EXP-")

    # 2. Run second custom experiment with high decay
    exp2_payload = {
        "name": "Exp 2 - High Decay",
        "dimension": 16,
        "decay": 0.25,
        "plasticity_eta": 1.0,
        "memories": [{"concept": "a", "value": "1"}, {"concept": "b", "value": "2"}],
        "concept_similarity": 0.1,
        "seed": 42,
        "notes": "Testing high decay",
    }
    res2 = client.post("/api/forensics/research/run", json=exp2_payload)
    assert res2.status_code == 200
    exp2_data = res2.json()

    # 3. Check history endpoint
    hist_res = client.get("/api/forensics/research/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2

    # 4. Compare experiments
    comp_payload = {
        "run_id_a": exp1_data["run_id"],
        "run_id_b": exp2_data["run_id"],
    }
    comp_res = client.post("/api/forensics/research/compare", json=comp_payload)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "matrix_frobenius_distance" in comp_data
    assert comp_data["fidelity_delta"] <= 0.0
