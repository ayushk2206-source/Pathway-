"""Tests for UI backend endpoints (Phase 06 Command Center integration)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore


@pytest.fixture
def ui_client(tmp_path):
    store = ExperimentStore(directory=tmp_path)
    app = create_app(store)
    return TestClient(app)


def test_list_and_demo_experiments(ui_client):
    # Initially empty or default
    r = ui_client.get("/api/experiments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Launch demo experiment
    r_demo = ui_client.post("/api/experiments/demo")
    assert r_demo.status_code == 200
    data = r_demo.json()
    assert "experiment_id" in data
    assert data["mechanism"] == "interference"
    assert len(data["events"]) > 0
    assert len(data["snapshots"]) > 0

    # List experiments now contains it
    r_list = ui_client.get("/api/experiments")
    assert r_list.status_code == 200
    items = r_list.json()
    assert any(it["experiment_id"] == data["experiment_id"] for it in items)
