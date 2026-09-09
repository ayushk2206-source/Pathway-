"""Tests for Memory X-Ray query engine, inspector, replay, surgery, divergence, and REST APIs (Phase 05)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore
from core import ExperimentConfig, run_experiment
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.interventions import create_change_strength_intervention
from core.mechanisms.base import MechanismParams
from core.task import TaskConfig
from core.xray import (
    MemoryReplayController,
    PlaybackStatus,
    build_memory_explanation,
    compare_xray_surgery,
    execute_xray_query,
    generate_visualization_contracts,
    generate_xray_report,
    get_state_checkpoint,
    inspect_event_before_after,
    trace_divergence_xray,
)


@pytest.fixture
def integrated_setup(tmp_path):
    """Setup experiment, counterfactual branch, and TestClient."""
    store = ExperimentStore(directory=tmp_path)
    app = create_app(store)
    client = TestClient(app)

    cfg = ExperimentConfig(
        seed=200,
        mechanism="interference",
        params=MechanismParams(state_dim=64, update_strength=0.9, memory_strength=1.0),
        task=TaskConfig(seed=200, d=64, n_objects=4, n_symbols=4, n_conflicts=2, cycles=1),
    )
    exp = run_experiment(cfg)
    store.save(exp)

    # Counterfactual intervention
    intv = create_change_strength_intervention(new_strength=0.2, target_timestep=1)
    cf_res = run_counterfactual(exp, intv)
    cf_exp = cf_res.to_experiment()
    store.save(cf_exp)

    return {
        "client": client,
        "store": store,
        "exp": exp,
        "cf_exp": cf_exp,
    }


def test_query_engine(integrated_setup):
    """Verify deterministic query engine without LLM calls."""
    exp = integrated_setup["exp"]

    res1 = execute_xray_query(exp, "Why did this memory become weaker?")
    assert "query_type" in res1
    assert "finding" in res1

    res2 = execute_xray_query(exp, "Which memories compete with this one?")
    assert "total_competing_pairs" in res2

    res3 = execute_xray_query(exp, "Which event had the largest effect?")
    assert "top_event" in res3

    res4 = execute_xray_query(exp, "Where did the memory state change most?")
    assert "highest_change_step" in res4


def test_inspector(integrated_setup):
    """Verify before/after microscopic state inspection."""
    exp = integrated_setup["exp"]
    insp = inspect_event_before_after(exp, 1)

    assert "state_before" in insp
    assert "state_after" in insp
    assert "diff" in insp
    assert insp["diff"]["l2_distance"] > 0.0
    assert "total_units_changed" in insp["diff"]


def test_surgery_integration(integrated_setup):
    """Verify X-Ray topological diff between original and counterfactual surgery."""
    exp = integrated_setup["exp"]
    cf_exp = integrated_setup["cf_exp"]

    surgery_diff = compare_xray_surgery(exp, cf_exp)
    assert surgery_diff["original_experiment_id"] == exp.experiment_id
    assert surgery_diff["counterfactual_experiment_id"] == cf_exp.experiment_id
    assert "point_shifts" in surgery_diff
    assert len(surgery_diff["point_shifts"]) > 0


def test_divergence_integration(integrated_setup):
    """Verify state divergence trajectory tracing."""
    exp = integrated_setup["exp"]
    cf_exp = integrated_setup["cf_exp"]

    div_res = trace_divergence_xray(exp, cf_exp)
    assert div_res["divergence_onset_step"] is not None
    assert div_res["final_l2_distance"] > 0.0
    assert len(div_res["steps"]) == len(exp.snapshots)


def test_replay_controller(integrated_setup):
    """Verify event-by-event playback state controller."""
    exp = integrated_setup["exp"]
    controller = MemoryReplayController(exp)

    state = controller.start()
    assert state["playback_status"] == PlaybackStatus.PLAYING.value
    assert state["current_step"] == 0

    state = controller.step_forward()
    assert state["current_step"] == 1

    state = controller.step_backward()
    assert state["current_step"] == 0

    state = controller.jump_to_event(3)
    assert state["current_step"] == 3


def test_checkpoint_access(integrated_setup):
    """Verify state checkpoint access."""
    exp = integrated_setup["exp"]
    chk = get_state_checkpoint(exp, 1)
    assert chk["timeline_step"] == 1
    assert chk["state_norm"] > 0.0
    assert len(chk["state_vector"]) == 64


def test_xray_report(integrated_setup):
    """Verify comprehensive X-Ray report generation."""
    exp = integrated_setup["exp"]
    report = generate_xray_report(exp)
    assert report.experiment_id == exp.experiment_id
    assert "overview" in report.to_dict()
    assert "state_dynamics" in report.to_dict()
    assert "limitations" in report.to_dict()


def test_visualization_contracts(integrated_setup):
    """Verify all 10 visual targets in data contract."""
    exp = integrated_setup["exp"]
    contracts = generate_visualization_contracts(exp)

    assert "timeline" in contracts
    assert "heatmap" in contracts
    assert "strength_curves" in contracts
    assert "memory_map" in contracts
    assert "competition_graph" in contracts
    assert "state_difference" in contracts
    assert "divergence" in contracts
    assert "event_impact" in contracts
    assert "sparsity" in contracts
    assert "anomalies" in contracts


def test_xray_rest_apis(integrated_setup):
    """Verify FastAPI endpoints mounted at /api/xray."""
    client = integrated_setup["client"]
    exp_id = integrated_setup["exp"].experiment_id

    # 1. Snapshots
    r = client.get(f"/api/xray/{exp_id}/snapshots")
    assert r.status_code == 200
    assert r.json()["total_snapshots"] > 0

    # 2. Trajectory
    r = client.get(f"/api/xray/{exp_id}/trajectory")
    assert r.status_code == 200

    # 3. Heatmaps
    r = client.get(f"/api/xray/{exp_id}/heatmaps")
    assert r.status_code == 200

    # 4. Map (2D PCA)
    r = client.get(f"/api/xray/{exp_id}/map")
    assert r.status_code == 200

    # 5. Competition
    r = client.get(f"/api/xray/{exp_id}/competition")
    assert r.status_code == 200

    # 6. Report
    r = client.get(f"/api/xray/{exp_id}/report")
    assert r.status_code == 200

    # 7. Compare states
    r = client.post("/api/xray/compare-states", json={"state_a": [1.0, 0.0], "state_b": [0.0, 1.0]})
    assert r.status_code == 200
    assert r.json()["cosine_distance"] == 1.0

    # 8. Query
    r = client.post("/api/xray/query", json={"experiment_id": exp_id, "query": "Which event had the largest effect?"})
    assert r.status_code == 200
