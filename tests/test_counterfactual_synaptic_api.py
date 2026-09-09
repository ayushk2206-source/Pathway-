"""API integration tests for Phase 16: Counterfactual Synaptic Endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def seeded_experiment(client):
    """Seed a standard experiment directly in the app store."""
    cfg = ExperimentConfig(
        seed=42,
        mechanism="hebbian",
        params=MechanismParams(decay=0.05, update_strength=1.0, state_dim=16),
        task=TaskConfig(
            seed=42,
            n_objects=3,
            n_symbols=3,
            n_conflicts=1,
            cycles=2,
            order="interleaved",
            d=16,
        ),
    )
    exp = run_experiment(cfg)
    client.app.state.store.save(exp)
    return exp


def test_synaptic_intervention_endpoint(client, seeded_experiment):
    """Test POST /api/counterfactual/synaptic-intervention creates valid counterfactual branch."""
    exp_id = seeded_experiment.experiment_id

    # 1. Run signature counterfactual: What if synapse never strengthened?
    payload = {
        "experiment_id": exp_id,
        "intervention_type": "synapse_prevent_strengthen",
        "synapse_id": "syn_k1_v2",
        "target_timestep": 1,
        "title": "What if syn_k1_v2 never strengthened?",
        "hypothesis": "Preventing syn_k1_v2 strengthening will decrease cue recall",
    }
    res = client.post("/api/counterfactual/synaptic-intervention", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert "counterfactual_id" in data
    assert data["branch_point"] == 1
    cf_id = data["counterfactual_id"]

    # 2. Query branches endpoint
    branches_res = client.get(f"/api/counterfactual/branches/{exp_id}")
    assert branches_res.status_code == 200
    b_data = branches_res.json()
    assert b_data["total_branches"] >= 1
    matching = [b for b in b_data["branches"] if b["branch_id"] == cf_id]
    assert len(matching) == 1
    assert matching[0]["intervention_type"] == "synapse_prevent_strengthen"
    assert matching[0]["target_synapse"] == "syn_k1_v2"

    # 3. Synchronized comparison endpoint at T=1 and T=2
    comp_res_1 = client.post("/api/counterfactual/synaptic-compare", json={
        "original_experiment_id": exp_id,
        "counterfactual_id": cf_id,
        "step_idx": 1,
        "display_dim": 16,
    })
    assert comp_res_1.status_code == 200
    c_data_1 = comp_res_1.json()
    assert c_data_1["step_idx"] == 1
    assert "original_network" in c_data_1
    assert "counterfactual_network" in c_data_1
    assert "synaptic_deltas" in c_data_1

    comp_res_2 = client.post("/api/counterfactual/synaptic-compare", json={
        "original_experiment_id": exp_id,
        "counterfactual_id": cf_id,
        "step_idx": 2,
        "display_dim": 16,
    })
    assert comp_res_2.status_code == 200
    c_data_2 = comp_res_2.json()
    assert c_data_2["step_idx"] == 2
    assert "outcome_deltas" in c_data_2
    assert "query_comparison" in c_data_2


def test_synaptic_intervention_decay_and_silence(client, seeded_experiment):
    """Test silence and decay intervention endpoints."""
    exp_id = seeded_experiment.experiment_id

    # Silence
    res_silence = client.post("/api/counterfactual/synaptic-intervention", json={
        "experiment_id": exp_id,
        "intervention_type": "synapse_silence",
        "synapse_id": "syn_k0_v0",
        "target_timestep": 2,
    })
    assert res_silence.status_code == 200
    assert res_silence.json()["status"] == "success"

    # Decay
    res_decay = client.post("/api/counterfactual/synaptic-intervention", json={
        "experiment_id": exp_id,
        "intervention_type": "change_decay",
        "new_decay": 0.5,
        "target_timestep": 0,
    })
    assert res_decay.status_code == 200
    assert res_decay.json()["status"] == "success"


def test_invalid_intervention_requests(client, seeded_experiment):
    """Verify validation handling on bad inputs."""
    exp_id = seeded_experiment.experiment_id

    # Non-existent experiment
    res = client.post("/api/counterfactual/synaptic-intervention", json={
        "experiment_id": "non_existent_exp_999",
        "intervention_type": "synapse_silence",
        "synapse_id": "syn_k0_v0",
    })
    assert res.status_code == 404

    # Unsupported intervention type
    res = client.post("/api/counterfactual/synaptic-intervention", json={
        "experiment_id": exp_id,
        "intervention_type": "magic_unsupported_op",
    })
    assert res.status_code == 400
