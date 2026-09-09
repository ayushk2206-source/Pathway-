"""Unit tests for Phase 10: Causal Memory Lab computational engine.

Tests scenario compilation, cost estimation, first divergence detection,
critical window detection, causal graph creation, causal edge testing,
multi-intervention interactions, memory swap, recovery curve, causality matrix,
ledger with claim versioning, and contradiction engine.
"""

import pytest
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig

from core.causal import (
    CausalEdgeStatus,
    CausalInterventionType,
    CausalLedger,
    CausalQueueManager,
    CausalReportGenerator,
    CausalScenario,
    CausalScenarioCompiler,
    ClaimStatus,
    ContradictionEngine,
    InteractionClassification,
    QueueStatus,
    build_causal_graph,
    build_causality_matrix,
    build_recovery_curve,
    build_temporal_causality_map,
    compute_first_divergence,
    run_memory_swap,
    run_multi_intervention,
    run_timing_sensitivity,
    test_causal_edge as evaluate_causal_edge,
)
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import ReplayStrategy


@pytest.fixture(scope="module")
def sample_experiment():
    """Generates a reproducible experiment with rich memory associations."""
    cfg = ExperimentConfig(
        seed=123,
        mechanism="leaky",
        params=MechanismParams(decay=0.15, update_strength=0.9),
        task=TaskConfig(
            seed=123,
            n_objects=6,
            n_symbols=6,
            n_conflicts=4,
            cycles=2,
            order="interleaved",
        ),
    )
    return run_experiment(cfg)


def test_scenario_validation_and_cost(sample_experiment):
    first_mem = sample_experiment.events[3]["concept_label"]
    scn = CausalScenario(
        experiment_id=sample_experiment.experiment_id,
        target_memory=first_mem,
        intervention=CausalInterventionType.REMOVE,
        timing=3,
        strength=1.0,
    )
    val = CausalScenarioCompiler.validate(sample_experiment, scn)
    assert val.valid is True
    assert val.cost_estimate is not None
    assert val.cost_estimate.runs_required == 1
    assert val.cost_estimate.within_budget is True

    # Test invalid target
    invalid_scn = CausalScenario(
        experiment_id=sample_experiment.experiment_id,
        target_memory="nonexistent_concept_xyz",
        intervention=CausalInterventionType.REMOVE,
    )
    val_invalid = CausalScenarioCompiler.validate(sample_experiment, invalid_scn)
    assert val_invalid.valid is False
    assert len(val_invalid.errors) > 0


def test_scenario_compilation_and_counterfactual(sample_experiment):
    target_mem = sample_experiment.events[4]["concept_label"]
    scn = CausalScenario(
        experiment_id=sample_experiment.experiment_id,
        target_memory=target_mem,
        intervention=CausalInterventionType.WEAKEN,
        strength=0.95,
    )
    intv = CausalScenarioCompiler.compile(sample_experiment, scn)
    assert intv is not None

    cf = run_counterfactual(sample_experiment, intv, strategy=ReplayStrategy.FULL_REPLAY)
    assert cf is not None
    assert cf.divergence is not None

    first_div = compute_first_divergence(cf)
    assert first_div.counterfactual_id == cf.counterfactual_id
    assert first_div.divergence_magnitude >= 0.0
    assert len(first_div.trace) > 0


def test_timing_sensitivity_and_critical_windows(sample_experiment):
    target_mem = sample_experiment.events[4]["concept_label"]
    sensitivity = run_timing_sensitivity(sample_experiment, target_mem, candidate_timesteps=[2, 8, 15, 25])
    assert sensitivity.experiment_id == sample_experiment.experiment_id
    assert sensitivity.target_memory is not None
    assert len(sensitivity.points) > 0


def test_causal_graph_and_edge_testing(sample_experiment):
    target_mem = sample_experiment.events[2]["concept_label"]
    graph = build_causal_graph(sample_experiment, target_mem, intervention_type="remove")
    assert graph.experiment_id == sample_experiment.experiment_id
    assert len(graph.nodes) > 0

    if len(graph.nodes) >= 2:
        src = graph.nodes[0].concept_label
        tgt = graph.nodes[1].concept_label
        edge_test = evaluate_causal_edge(sample_experiment, src, tgt)
        assert edge_test.source is not None
        assert edge_test.target is not None
        assert edge_test.status in [
            CausalEdgeStatus.SUPPORTED,
            CausalEdgeStatus.WEAK,
            CausalEdgeStatus.INCONCLUSIVE,
            CausalEdgeStatus.CONTRADICTED,
        ]


def test_multi_intervention_and_interaction(sample_experiment):
    m1 = sample_experiment.events[3]["concept_label"]
    m2 = sample_experiment.events[7]["concept_label"]
    specs = [
        {"target_memory": m1, "intervention_type": "remove", "dose": 1.0},
        {"target_memory": m2, "intervention_type": "weaken", "dose": 0.5},
    ]
    res = run_multi_intervention(sample_experiment, specs)
    assert res.experiment_id == sample_experiment.experiment_id
    assert len(res.interaction.individual_effects) == 2
    assert res.interaction.classification in [
        InteractionClassification.ADDITIVE,
        InteractionClassification.SYNERGY,
        InteractionClassification.ANTAGONISM,
        InteractionClassification.UNKNOWN,
    ]


def test_memory_swap(sample_experiment):
    cues = [e["concept_label"] for e in sample_experiment.events if e.get("concept_label")]
    unique_cues = list(dict.fromkeys(cues))
    assert len(unique_cues) >= 2
    m1 = unique_cues[0]
    m2 = unique_cues[1]
    swap_res = run_memory_swap(sample_experiment, m1, m2)
    assert swap_res.experiment_id == sample_experiment.experiment_id
    assert swap_res.state_distance_l2 >= 0.0
    assert isinstance(swap_res.identity_dependent, bool)
    assert "Swapping" in swap_res.explanation


def test_recovery_curve_and_matrix(sample_experiment):
    m1 = sample_experiment.events[4]["concept_label"]
    rec = build_recovery_curve(sample_experiment, m1)
    assert len(rec.points) == 4
    phases = [p.phase for p in rec.points]
    assert phases == ["PRE-DELETE", "POST-DELETE", "RECOVERY", "FINAL"]

    matrix = build_causality_matrix(sample_experiment)
    assert matrix.experiment_id == sample_experiment.experiment_id
    assert len(matrix.memories) > 0
    assert len(matrix.matrix) == len(matrix.memories)

    tmap = build_temporal_causality_map(sample_experiment, m1, n_bins=4)
    assert len(tmap.bins) > 0


def test_causal_ledger_and_claim_versioning():
    ledger = CausalLedger()
    claim = ledger.register_claim(
        source_memory="M17",
        target_memory="M22",
        statement="M17 perturbation alters M22 representation.",
        status=ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT,
        evidence_experiment_ids=["exp_001"],
        interventions=2,
        replications=2,
    )
    assert claim.claim_id == "CLM-001"
    assert len(claim.versions) == 1
    assert claim.current.version == 1

    # Update version
    updated = ledger.update_claim(
        claim_id="CLM-001",
        statement="M17 perturbation alters M22 conditionally on t < 25.",
        status=ClaimStatus.SUPPORTED_WITHIN_TESTED_CONDITIONS,
        evidence_experiment_ids=["exp_001", "exp_002"],
        interventions=4,
        replications=3,
        effect_consistency="HIGH",
        changed_because="Temporal sensitivity sweep revealed critical window boundary at t=25.",
    )
    assert len(updated.versions) == 2
    assert updated.current.version == 2
    assert updated.versions[0].statement != updated.versions[1].statement
    assert updated.current.changed_because.startswith("Temporal sensitivity")


def test_contradiction_engine():
    engine = ContradictionEngine()
    ledger = CausalLedger()
    observations = [
        {"source_memory": "M17", "target_memory": "M22", "experiment_id": "exp_A", "effect": 0.45, "timing": 20},
        {"source_memory": "M17", "target_memory": "M22", "experiment_id": "exp_B", "effect": 0.02, "timing": 35},
    ]
    conflicts = engine.detect_conflicts(ledger, observations)
    assert len(conflicts) == 1
    conf = conflicts[0]
    assert conf.source_memory == "M17"
    assert conf.target_memory == "M22"
    assert conf.effect_a == 0.45
    assert conf.effect_b == 0.02
    assert "controlled" in conf.suggested_controlled_test.lower()


def test_causal_report_generator(sample_experiment):
    rep = CausalReportGenerator.generate_report(
        experiment_id=sample_experiment.experiment_id,
        question="Does weakening M17 reduce downstream cascade depth?",
        scenario={"target_memory": "M17", "intervention": "WEAKEN", "strength": 0.95},
        baseline={"experiment_id": sample_experiment.experiment_id, "n_events": 40},
        intervention={"type": "WEAKEN", "target": "M17"},
        first_divergence={"first_divergence_step": 37, "divergence_magnitude": 0.35},
    )
    assert rep.question.startswith("Does weakening")
    assert len(rep.limitations) >= 3
    assert "first_divergence_step" in rep.first_divergence
    assert "simulation configuration" in rep.conclusion


def test_causal_queue_manager():
    qm = CausalQueueManager(max_size=5)
    scn = CausalScenario(target_memory="M1")
    from core.causal.models import CausalCostEstimate
    c = CausalCostEstimate(runs_required=1, estimated_compute_units=1.0, estimated_memory_mb=1.0, estimated_time_seconds=0.1, within_budget=True)
    item = qm.enqueue(scn, c)
    assert item.status == QueueStatus.QUEUED

    qm.pause()
    assert qm.is_paused is True
    qm.resume()
    assert qm.is_paused is False

    qm.stop()
    assert qm.is_stopped is True
    assert item.status == QueueStatus.CANCELLED

    qm.clear()
    assert len(qm.list_items()) == 0
