"""Integration tests for Phase 10 Causal Memory Lab REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.store import ExperimentStore
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig


@pytest.fixture(scope="module")
def api_test_setup(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("causal_store")
    store = ExperimentStore(directory=tmp_dir)

    cfg = ExperimentConfig(
        seed=42,
        mechanism="leaky",
        params=MechanismParams(update_strength=0.8, decay=0.1),
        task=TaskConfig(
            seed=42,
            n_objects=5,
            n_symbols=5,
            n_conflicts=3,
            cycles=2,
            order="interleaved",
        ),
    )
    exp = run_experiment(cfg)
    store.save(exp)

    app = create_app(store=store)
    client = TestClient(app)
    return client, exp, store


def test_scenario_and_cost_endpoints(api_test_setup):
    client, exp, _ = api_test_setup
    first_mem = exp.events[2]["concept_label"]

    # 1. CREATE_CAUSAL_SCENARIO
    res = client.post(
        "/api/causal/scenarios",
        json={
            "experiment_id": exp.experiment_id,
            "target_memory": first_mem,
            "intervention": "REMOVE",
            "timing": 2,
            "strength": 1.0,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert "scenario" in body
    assert body["scenario"]["target_memory"] == first_mem

    # 2. VALIDATE_CAUSAL_SCENARIO
    val_res = client.post(
        "/api/causal/scenarios/validate",
        json={
            "experiment_id": exp.experiment_id,
            "target_memory": first_mem,
            "intervention": "REMOVE",
            "timing": 2,
        },
    )
    assert val_res.status_code == 200
    assert val_res.json()["valid"] is True

    # 3. ESTIMATE_CAUSAL_COST
    cost_res = client.post(
        "/api/causal/scenarios/estimate-cost",
        json={
            "experiment_id": exp.experiment_id,
            "runs_required": 2,
        },
    )
    assert cost_res.status_code == 200
    assert cost_res.json()["runs_required"] == 2


def test_counterfactual_and_divergence_endpoints(api_test_setup):
    client, exp, _ = api_test_setup
    mem = exp.events[3]["concept_label"]

    # 4. RUN_COUNTERFACTUAL
    run_res = client.post(
        "/api/causal/counterfactual/run",
        json={
            "experiment_id": exp.experiment_id,
            "target_memory": mem,
            "intervention": "WEAKEN",
            "strength": 0.95,
        },
    )
    assert run_res.status_code == 200, run_res.text
    run_data = run_res.json()
    assert "counterfactual" in run_data
    assert "first_divergence" in run_data
    cf_id = run_data["counterfactual"]["counterfactual_id"]

    # 5. GET_DIVERGENCE
    div_res = client.get(f"/api/causal/divergence/{cf_id}")
    assert div_res.status_code == 200
    assert "divergence" in div_res.json()

    # 6. GET_FIRST_DIVERGENCE
    fdiv_res = client.get(f"/api/causal/first-divergence/{cf_id}")
    assert fdiv_res.status_code == 200
    fdiv_data = fdiv_res.json()
    assert fdiv_data["counterfactual_id"] == cf_id
    assert "trace" in fdiv_data

    # 22. REPLAY_CAUSAL_EXPERIMENT
    rep_res = client.get(f"/api/causal/replay/{exp.experiment_id}/{cf_id}")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["total_frames"] > 0
    assert "frames" in rep_data


def test_cascade_and_graph_endpoints(api_test_setup):
    client, exp, _ = api_test_setup
    mem = exp.events[1]["concept_label"]

    # 7. GET_CASCADE_TRACE
    casc_res = client.get(f"/api/causal/cascade-trace/{exp.experiment_id}/{mem}")
    assert casc_res.status_code == 200
    assert "nodes" in casc_res.json()

    # 8. GET_CRITICAL_WINDOWS
    cw_res = client.get(f"/api/causal/critical-windows/{exp.experiment_id}/{mem}")
    assert cw_res.status_code == 200
    assert "points" in cw_res.json()

    # 9. GET_CAUSAL_GRAPH
    graph_res = client.get(f"/api/causal/graph/{exp.experiment_id}/{mem}")
    assert graph_res.status_code == 200
    g_data = graph_res.json()
    assert "nodes" in g_data
    assert "edges" in g_data

    # 10. GET_CAUSAL_EDGE & 11. TEST_CAUSAL_EDGE
    if len(g_data["nodes"]) >= 2:
        src = g_data["nodes"][0]["concept_label"]
        tgt = g_data["nodes"][1]["concept_label"]

        edge_res = client.get(f"/api/causal/edge/{exp.experiment_id}?source={src}&target={tgt}")
        assert edge_res.status_code == 200

        test_edge_res = client.post(
            "/api/causal/edge/test",
            json={
                "experiment_id": exp.experiment_id,
                "source_memory": src,
                "target_memory": tgt,
            },
        )
        assert test_edge_res.status_code == 200
        assert "status" in test_edge_res.json()


def test_interaction_swap_and_recovery_endpoints(api_test_setup):
    client, exp, _ = api_test_setup
    cues = list(dict.fromkeys([e["concept_label"] for e in exp.events if e.get("concept_label")]))
    m1 = cues[0]
    m2 = cues[1]

    # 12. RUN_MULTI_INTERVENTION
    multi_res = client.post(
        "/api/causal/multi-intervention",
        json={
            "experiment_id": exp.experiment_id,
            "interventions": [
                {"target_memory": m1, "intervention_type": "remove", "dose": 1.0},
                {"target_memory": m2, "intervention_type": "weaken", "dose": 0.5},
            ],
        },
    )
    assert multi_res.status_code == 200
    assert "interaction" in multi_res.json()

    # 13. CALCULATE_INTERACTION_EFFECT
    eff_res = client.post(
        "/api/causal/interaction-effect",
        json={
            "experiment_id": exp.experiment_id,
            "interventions": [
                {"target_memory": m1, "intervention_type": "remove", "dose": 1.0},
                {"target_memory": m2, "intervention_type": "weaken", "dose": 0.5},
            ],
        },
    )
    assert eff_res.status_code == 200
    assert "classification" in eff_res.json()

    # 14. RUN_MEMORY_SWAP
    swap_res = client.post(
        "/api/causal/swap",
        json={
            "experiment_id": exp.experiment_id,
            "memory_a": m1,
            "memory_b": m2,
        },
    )
    assert swap_res.status_code == 200
    assert "identity_dependent" in swap_res.json()

    # 15. RUN_RECOVERY_EXPERIMENT
    rec_res = client.post(
        "/api/causal/recovery",
        json={
            "experiment_id": exp.experiment_id,
            "target_memory": m1,
        },
    )
    assert rec_res.status_code == 200

    # 16. GET_RECOVERY_CURVE
    curve_res = client.get(f"/api/causal/recovery-curve/{exp.experiment_id}/{m1}")
    assert curve_res.status_code == 200
    assert len(curve_res.json()["points"]) == 4

    # 17. GET_CAUSALITY_MATRIX
    mat_res = client.get(f"/api/causal/matrix/{exp.experiment_id}")
    assert mat_res.status_code == 200
    assert "matrix" in mat_res.json()


def test_ledger_conflicts_and_reports_endpoints(api_test_setup):
    client, exp, _ = api_test_setup

    # 18. GET_CAUSALITY_LEDGER
    led_res = client.get("/api/causal/ledger")
    assert led_res.status_code == 200

    # Register Claim
    cl_res = client.post(
        "/api/causal/claims",
        json={
            "source_memory": "M17",
            "target_memory": "M22",
            "statement": "M17 weakening triggers M22 representation shift.",
            "status": "SUPPORTED WITHIN EXPERIMENT",
            "evidence_experiment_ids": [exp.experiment_id],
        },
    )
    assert cl_res.status_code == 200
    claim_id = cl_res.json()["claim_id"]

    # 19. GET_CAUSAL_CLAIM
    get_cl_res = client.get(f"/api/causal/claims/{claim_id}")
    assert get_cl_res.status_code == 200
    assert get_cl_res.json()["claim_id"] == claim_id

    # Update Version
    ver_res = client.post(
        f"/api/causal/claims/{claim_id}/version",
        json={
            "statement": "M17 perturbation alters M22 with peak divergence around t=20.",
            "status": "SUPPORTED WITHIN TESTED CONDITIONS",
            "evidence_experiment_ids": [exp.experiment_id],
            "interventions": 2,
            "replications": 2,
            "effect_consistency": "HIGH",
            "changed_because": "Replication verified divergence boundary.",
        },
    )
    assert ver_res.status_code == 200
    assert len(ver_res.json()["versions"]) == 2

    # 20. GET_CAUSAL_CONFLICTS
    conf_res = client.get("/api/causal/conflicts")
    assert conf_res.status_code == 200
    assert isinstance(conf_res.json(), list)

    # 21. CREATE_CAUSAL_REPORT
    rep_res = client.post(
        "/api/causal/reports",
        json={
            "experiment_id": exp.experiment_id,
            "question": "What if M17 were weakened by 5% at t=20?",
            "scenario": {"target_memory": "M17", "intervention": "WEAKEN"},
            "baseline": {"experiment_id": exp.experiment_id},
            "intervention": {"dose": 0.95},
        },
    )
    assert rep_res.status_code == 200
    report_id = rep_res.json()["report_id"]

    get_rep_res = client.get(f"/api/causal/reports/{report_id}")
    assert get_rep_res.status_code == 200
    assert get_rep_res.json()["report_id"] == report_id


def test_queue_and_discovery_handoff(api_test_setup):
    client, exp, _ = api_test_setup

    # Queue controls
    q_res = client.get("/api/causal/queue")
    assert q_res.status_code == 200

    pause_res = client.post("/api/causal/queue/control", json={"action": "pause"})
    assert pause_res.status_code == 200
    assert pause_res.json()["is_paused"] is True

    resume_res = client.post("/api/causal/queue/control", json={"action": "resume"})
    assert resume_res.status_code == 200
    assert resume_res.json()["is_paused"] is False

    # Discovery Handoff (Section 34/35/36)
    ho_res = client.post(
        "/api/causal/discovery/handoff",
        json={
            "experiment_id": exp.experiment_id,
            "title": "Causal Divergence M17",
            "description": "5% weakening produced 32% downstream cascade.",
            "pattern_type": "CASCADE_AMPLIFICATION",
            "memory_id": "M17",
        },
    )
    assert ho_res.status_code == 200
    assert ho_res.json()["status"] == "HANDOFF_COMPLETED"
