"""Phase 02 memory engine API tests."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore


@pytest.fixture()
def client(tmp_path):
    app = create_app(store=ExperimentStore(tmp_path / "store"))
    with TestClient(app) as c:
        yield c


MEMORY_BODY = {
    "seed": 5,
    "mechanism": "baseline",
    "params": {"state_dim": 64},
    "memories": [
        {"concept": "capital_of_france", "value": "Paris"},
        {"concept": "capital_of_spain", "value": "Madrid"},
    ],
}


def test_memory_write(client):
    r = client.post(
        "/api/memory/write",
        json={"seed": 5, "mechanism": "baseline", "params": {"state_dim": 64},
              "memory": {"concept": "capital_of_france", "value": "Paris"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["memory"]["concept"] == "capital_of_france"
    assert len(body["memory"]["key_vector"]) == 64
    u = body["update_result"]
    assert u["memory_contribution"] == pytest.approx(1.0, abs=1e-9)
    assert u["interference_contribution"] == pytest.approx(0.0, abs=1e-9)
    assert u["num_affected"] > 0


def test_memory_recall(client):
    r = client.post(
        "/api/memory/recall",
        json={**MEMORY_BODY,
              "query": {"concept": "capital_of_france"},
              "expected_value": "Paris"},
    )
    assert r.status_code == 200
    body = r.json()
    recall = body["recall"]
    assert recall["predicted_value"] == "Paris"
    assert recall["correct"] is True
    assert recall["ground_truth"] == "Paris"
    assert len(recall["candidate_memories"]) >= 2
    assert len(body["writes"]) == 2


def test_memory_recall_conflict(client):
    r = client.post(
        "/api/memory/recall",
        json={"seed": 5, "mechanism": "leaky", "params": {"state_dim": 64, "decay": 0.5},
              "memories": [
                  {"concept": "vault_a", "value": "BLUE"},
                  {"concept": "vault_a", "value": "GREEN"},
              ],
              "query": {"concept": "vault_a"},
              "expected_value": "GREEN"},
    )
    assert r.status_code == 200
    assert r.json()["recall"]["correct"] is True


def test_memory_recall_pure_probe(client):
    r = client.post(
        "/api/memory/recall",
        json={**MEMORY_BODY, "query": {"concept": "capital_of_spain"}},
    )
    body = r.json()["recall"]
    assert body["ground_truth"] is None
    assert body["correct"] is None


def test_memory_experiment_persisted_and_replayable(client):
    r = client.post("/api/experiments/memory", json=MEMORY_BODY)
    assert r.status_code == 200
    exp = r.json()
    eid = exp["experiment_id"]
    assert exp["config"]["task"]["vector_source"] == "text"
    # exact replay reproduces the record
    replayed = client.post(f"/api/experiments/{eid}/replay", json={}).json()
    assert replayed["experiment_id"] != eid
    assert replayed["metrics"] == exp["metrics"]


def test_memory_experiment_custom_queries(client):
    r = client.post(
        "/api/experiments/memory",
        json={**MEMORY_BODY,
              "queries": [{"concept": "capital_of_france", "timestep": -1, "kind": "original"}]},
    )
    assert r.status_code == 200
    assert len(r.json()["queries"]) == 1
    assert r.json()["queries"][0]["kind"] == "original"


def test_collision_endpoint(client):
    r = client.post(
        "/api/experiments/collision",
        json={"seed": 16, "mechanism": "interference",
              "params": {"state_dim": 64, "interference_strength": 0.8},
              "concept": "enclosure_7", "value_a": "TIGER", "value_b": "LION",
              "similarity": 0.8},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["experiment_id"]
    assert body["representation_similarity"]["key_similarity"] > 0.6
    assert body["interference_score"]["measured"] >= 0.0
    assert "recall" in body


def test_retention_endpoint(client):
    r = client.post(
        "/api/experiments/retention",
        json={"seed": 11, "mechanism": "leaky", "params": {"state_dim": 64, "decay": 0.3},
              "lags": [0, 5, 10]},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert [row["steps"] for row in data] == [0, 5, 10]
    assert data[0]["retention"] > data[-1]["retention"]


def test_ablation_endpoint(client):
    created = client.post("/api/experiments/memory", json={
        "seed": 7, "mechanism": "leaky", "params": {"state_dim": 64, "decay": 0.3},
        "memories": [
            {"concept": "vault_a", "value": "BLUE"},
            {"concept": "locker_b", "value": "GREEN"},
            {"concept": "vault_a", "value": "RED"},
        ],
        "queries": [
            {"concept": "vault_a", "timestep": -1, "kind": "latest"},
            {"concept": "vault_a", "timestep": -1, "kind": "original"},
        ],
    }).json()
    eid = created["experiment_id"]
    r = client.post("/api/experiments/ablation", json={"experiment_id": eid, "event_id": "e0002"})
    assert r.status_code == 200
    body = r.json()
    assert body["reproduced_from_config"] is True
    assert body["counterfactual"]["num_events"] == 2
    assert body["difference"]["state"]["l2_distance"] > 0.0


def test_ablation_missing_experiment_404(client):
    r = client.post("/api/experiments/ablation",
                    json={"experiment_id": "nope", "event_id": "e0000"})
    assert r.status_code == 404


def test_compare_stored_experiments(client):
    a = client.post("/api/experiments/memory", json={
        **MEMORY_BODY, "mechanism": "leaky", "params": {"state_dim": 64, "decay": 0.4}}).json()
    b = client.post("/api/experiments/memory", json={
        **MEMORY_BODY, "mechanism": "baseline", "params": {"state_dim": 64}}).json()
    r = client.post("/api/experiments/compare", json={
        "experiment_id_a": a["experiment_id"], "experiment_id_b": b["experiment_id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["configuration_differences"]["mechanism"] == {"a": "leaky", "b": "baseline"}
    assert "recall_accuracy" in body["metric_differences"]


def test_state_and_timeline_endpoints(client):
    created = client.post("/api/experiments/memory", json=MEMORY_BODY).json()
    eid = created["experiment_id"]
    s = client.get(f"/api/experiments/{eid}/state/1")
    assert s.status_code == 200
    body = s.json()
    assert body["timestep"] == 1
    assert body["state_norm"] == pytest.approx(1.0, abs=1e-9)
    assert body["memory_contributions"][0]["memory_id"] == "capital_of_france:Paris"
    assert client.get(f"/api/experiments/{eid}/state/99").status_code == 404

    tl = client.get(f"/api/experiments/{eid}/timeline")
    assert tl.status_code == 200
    assert len(tl.json()["timeline"]) == 3


def test_memory_contribution_endpoint(client):
    created = client.post("/api/experiments/memory", json={
        **MEMORY_BODY,
        "queries": [{"concept": "capital_of_france", "timestep": -1, "kind": "latest"}],
    }).json()
    eid = created["experiment_id"]
    r = client.post(
        f"/api/experiments/{eid}/memory-contribution",
        json={"memory_id": "capital_of_france:Paris"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["method"] == "replay-based contribution estimate"
    assert "NOT true causal attribution" in body["limitation"]


def test_capacity_order_matrix_endpoints(client):
    cap = client.post("/api/experiments/capacity", json={
        "seed": 12, "mechanism": "baseline", "params": {"state_dim": 128},
        "dimensions": [8, 32, 64]})
    assert cap.status_code == 200
    assert [row["d"] for row in cap.json()["data"]] == [8, 32, 64]

    order = client.post("/api/experiments/order", json={
        "seed": 13, "mechanism": "leaky", "params": {"state_dim": 64, "decay": 0.2}})
    assert order.status_code == 200
    assert len(order.json()["orders"]) == 3

    matrix = client.post("/api/experiments/interference-matrix", json={
        "seed": 15, "mechanism": "baseline", "params": {"state_dim": 64},
        "similarities": [0.0, 0.9], "update_strengths": [0.2, 1.0]})
    assert matrix.status_code == 200
    assert len(matrix.json()["data"]) == 4


def test_scenarios_endpoints(client):
    listing = client.get("/api/scenarios")
    assert listing.status_code == 200
    assert "conflicting_memory" in listing.json()["scenarios"]

    out = client.post("/api/experiments/scenario", json={"name": "conflicting_memory"})
    assert out.status_code == 200
    assert out.json()["experiment_id"]

    missing = client.post("/api/experiments/scenario", json={"name": "nope"})
    assert missing.status_code == 404


def test_parameter_sensitivity_through_api(client):
    """Changing a meaningful parameter must change the result (section 24)."""
    def retention(decay):
        r = client.post("/api/experiments/retention", json={
            "seed": 11, "mechanism": "leaky",
            "params": {"state_dim": 64, "decay": decay}, "lags": [20]})
        return r.json()["data"][0]["retention"]

    assert retention(0.1) > retention(0.9)  # stronger decay → worse retention

    def strength_effect(s):
        r = client.post("/api/memory/write", json={
            "seed": 5, "mechanism": "baseline", "params": {"state_dim": 64},
            "memory": {"concept": "x", "value": "y", "strength": s}})
        return r.json()["update_result"]["update_magnitude"]

    assert strength_effect(0.1) < strength_effect(1.0)  # strength scales the write


def test_memory_write_invalid_params_400(client):
    r = client.post("/api/memory/write", json={
        "seed": 1, "mechanism": "baseline", "params": {"state_dim": 64, "decay": 5.0},
        "memory": {"concept": "a", "value": "b"}})
    assert r.status_code == 400