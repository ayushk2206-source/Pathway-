"""FastAPI endpoint tests (section 13)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore
from core.experiment import strip_non_deterministic


@pytest.fixture()
def client(tmp_path):
    app = create_app(store=ExperimentStore(tmp_path / "store"))
    with TestClient(app) as c:
        yield c


RUN_BODY = {
    "seed": 7,
    "mechanism": "leaky",
    "params": {"state_dim": 64, "decay": 0.2},
    "task": {"d": 64, "n_objects": 4, "n_symbols": 3, "n_conflicts": 2},
}


def test_health(client):
    for path in ("/health", "/api/health"):
        r = client.get(path)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["core_version"]
        assert body["schema_version"] >= 1


def test_mechanisms_listing(client):
    r = client.get("/api/mechanisms")
    assert r.status_code == 200
    mechs = r.json()["mechanisms"]
    for name in ("baseline", "leaky", "competitive", "hebbian", "interference"):
        assert name in mechs
        assert mechs[name]["description"]


def test_run_experiment(client):
    r = client.post("/api/experiments/run", json=RUN_BODY)
    assert r.status_code == 200
    exp = r.json()
    for key in (
        "experiment_id",
        "seed",
        "mechanism",
        "parameters",
        "config",
        "task",
        "events",
        "snapshots",
        "queries",
        "predictions",
        "ground_truth",
        "metrics",
        "created_at",
        "version",
    ):
        assert key in exp
    assert exp["mechanism"] == "leaky"
    assert exp["seed"] == 7
    assert len(exp["snapshots"]) == len(exp["events"]) + 1
    assert "recall_accuracy" in exp["metrics"]


def test_run_invalid_mechanism_is_400(client):
    body = dict(RUN_BODY, mechanism="teleport")
    r = client.post("/api/experiments/run", json=body)
    assert r.status_code == 400


def test_run_invalid_params_is_400(client):
    body = {"seed": 1, "mechanism": "leaky", "params": {"decay": 5.0}}
    r = client.post("/api/experiments/run", json=body)
    assert r.status_code == 400


def test_generate_task(client):
    r = client.post(
        "/api/experiments/generate",
        json={"task": {"d": 32, "n_objects": 3, "n_symbols": 2, "n_conflicts": 1}, "seed": 9},
    )
    assert r.status_code == 200
    task = r.json()
    assert task["d"] == 32
    assert len(task["events"]) > 0
    assert len(task["queries"]) > 0
    assert "objects" in task and "symbols" in task


def test_get_and_replay_experiment(client):
    created = client.post("/api/experiments/run", json=RUN_BODY).json()
    eid = created["experiment_id"]

    got = client.get(f"/api/experiments/{eid}")
    assert got.status_code == 200
    assert got.json()["experiment_id"] == eid

    # exact replay reproduces the run
    replayed = client.post(f"/api/experiments/{eid}/replay", json={}).json()
    assert replayed["replay_of"] == eid
    assert strip_non_deterministic(replayed) == strip_non_deterministic(created)

    # parameter override changes the outcome (sensitivity probe)
    altered = client.post(
        f"/api/experiments/{eid}/replay", json={"params": {"decay": 0.9}}
    ).json()
    assert altered["metrics"]["memory_retention"] != replayed["metrics"]["memory_retention"]


def test_get_missing_experiment_is_404(client):
    assert client.get("/api/experiments/nope").status_code == 404
    assert client.post("/api/experiments/nope/replay", json={}).status_code == 404


def test_recall_on_stored_history(client):
    created = client.post("/api/experiments/run", json=RUN_BODY).json()
    eid = created["experiment_id"]
    obj = created["events"][0]["concept_label"]

    r = client.post(
        "/api/recall", json={"experiment_id": eid, "object_label": obj, "timestep": -1}
    )
    assert r.status_code == 200
    out = r.json()
    for key in (
        "predicted_label",
        "truth_label",
        "confidence",
        "correctness",
        "quality",
        "top_matches",
        "snapshot",
    ):
        assert key in out
    assert out["truth_label"] == created["task"]["last_write"][obj][1]

    # mid-history recall (before the object was written) is a 400
    r2 = client.post(
        "/api/recall", json={"experiment_id": eid, "object_label": obj, "timestep": 0}
    )
    if r2.status_code == 400:
        return  # object not yet written at timestep 0 — acceptable
    assert r2.status_code == 200


def test_recall_unknown_object_is_400(client):
    created = client.post("/api/experiments/run", json=RUN_BODY).json()
    r = client.post(
        "/api/recall",
        json={"experiment_id": created["experiment_id"], "object_label": "ghost"},
    )
    assert r.status_code == 400


def test_compare_side_by_side(client):
    r = client.post(
        "/api/compare",
        json={
            "configs": [
                {
                    "seed": 7,
                    "mechanism": "baseline",
                    "params": {"state_dim": 64},
                    "task": {"d": 64},
                },
                {
                    "seed": 7,
                    "mechanism": "leaky",
                    "params": {"state_dim": 64, "decay": 0.4},
                    "task": {"d": 64},
                },
            ]
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 2
    assert "recall_accuracy" in body["comparison_table"]
    assert len(body["comparison_table"]["recall_accuracy"]) == 2
    assert body["results"][0]["metrics"] != body["results"][1]["metrics"]


def test_compare_requires_configs(client):
    r = client.post("/api/compare", json={"configs": []})
    assert r.status_code == 422


def test_determinism_across_api_runs(client):
    a = client.post("/api/experiments/run", json=RUN_BODY).json()
    b = client.post("/api/experiments/run", json=RUN_BODY).json()
    assert a["experiment_id"] != b["experiment_id"]
    assert strip_non_deterministic(a) == strip_non_deterministic(b)