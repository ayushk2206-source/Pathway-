"""Tests for Synaptic Brain engine and API routes (Phase 01)."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from core.synaptic import SynapticBrain, extract_synaptic_state_from_experiment
from core.runner import run_experiment
from core.experiment import ExperimentConfig
from core.task import TaskConfig
from core.mechanisms import MechanismParams


def test_synaptic_brain_initial_state():
    brain = SynapticBrain(seed=42, d=8, decay=0.1)
    state = brain.get_state()
    assert state.dimension == 8
    assert state.total_synapses == 64
    assert state.matrix_norm == 0.0
    assert len(state.neurons) == 16  # 8 key + 8 value
    assert state.timestep == 0


def test_hebbian_write_and_plasticity():
    brain = SynapticBrain(seed=42, d=8, decay=0.1, update_strength=1.5)
    state = brain.write("color", "blue", importance=1.0, strength=1.0)

    assert state.timestep == 1
    assert state.matrix_norm > 0.0
    assert state.last_explanation is not None
    assert "COLOR" in state.last_explanation.event_label
    assert state.last_explanation.write_gain == pytest.approx(1.5)
    assert state.last_pathway is not None
    assert len(state.last_pathway.active_key_indices) > 0
    assert len(state.last_pathway.active_value_indices) > 0


def test_synaptic_recall_and_readout():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("color", "blue")
    brain.write("shape", "triangle")

    state = brain.recall("color", expected_value="blue")
    assert state.last_recall is not None
    assert state.last_recall.query_concept == "color"
    assert state.last_recall.predicted_value == "blue"
    assert state.last_recall.is_correct is True
    assert state.last_recall.confidence > 0.5


def test_synaptic_decay_fades_weights():
    brain = SynapticBrain(seed=42, d=8, decay=0.2)
    brain.write("secret", "vault_key")
    initial_norm = brain.get_state().matrix_norm

    # Apply 3 decay steps
    decayed_state = brain.decay_step(n_steps=3)
    expected_factor = (1.0 - 0.2) ** 3
    assert decayed_state.matrix_norm == pytest.approx(initial_norm * expected_factor, rel=1e-5)


def test_interference_and_competition():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    # Write initial association
    brain.write("role", "admin")
    state1 = brain.recall("role", expected_value="admin")
    assert state1.last_recall.predicted_value == "admin"

    # Write conflicting memory with higher strength
    brain.write("role", "guest", strength=2.0)
    state2 = brain.recall("role", expected_value="guest")
    # Latest/stronger memory dominates
    assert state2.last_recall.predicted_value == "guest"


def test_scenarios():
    brain = SynapticBrain(seed=42, d=8)
    state = brain.load_scenario("hebbian_formation")
    assert len(state.history_timeline) >= 3


def test_extract_synaptic_state_from_experiment():
    cfg = ExperimentConfig(
        seed=42,
        mechanism="hebbian",
        params=MechanismParams(state_dim=8, decay=0.05),
        task=TaskConfig(d=8, n_objects=3, n_symbols=2, n_conflicts=1, cycles=1),
    )
    exp = run_experiment(cfg)
    syn_state = extract_synaptic_state_from_experiment(exp, step_idx=1, display_dim=8)
    assert syn_state.dimension == 8
    assert len(syn_state.neurons) == 16


def test_synaptic_api_endpoints():
    app = create_app()
    client = TestClient(app)

    # Info
    r = client.get("/api/synaptic/info")
    assert r.status_code == 200
    assert "Live Synaptic Brain" in r.json()["title"]

    # Reset
    r = client.post("/api/synaptic/reset", params={"dimension": 8})
    assert r.status_code == 200
    assert r.json()["matrix_norm"] == 0.0

    # Write
    r = client.post(
        "/api/synaptic/write",
        json={
            "concept": "item",
            "value": "sword",
            "importance": 1.0,
            "strength": 1.0,
            "dimension": 8,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["matrix_norm"] > 0.0

    # Recall
    r = client.post(
        "/api/synaptic/recall",
        json={
            "query_concept": "item",
            "expected_value": "sword",
            "dimension": 8,
        },
    )
    assert r.status_code == 200
    recall_data = r.json()
    assert recall_data["last_recall"]["predicted_value"] == "sword"

    # Decay
    r = client.post("/api/synaptic/decay", json={"steps": 2, "decay": 0.1})
    assert r.status_code == 200
    decay_data = r.json()
    assert decay_data["last_explanation"]["event_type"] == "DECAY"

    # Scenario
    r = client.post("/api/synaptic/scenario", json={"scenario": "hebbian_formation", "dimension": 8})
    assert r.status_code == 200
