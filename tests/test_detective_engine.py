"""Unit tests for Memory Detective / Hypothesis Engine core components (Phase 07)."""

import pytest
import numpy as np

from core.detective import (
    CausalSupportStatus,
    DeterministicQuestionParser,
    DiscoveryEngine,
    HypothesisClassification,
    HypothesisGenerator,
    Investigation,
    InvestigationStatus,
    InvestigationStore,
    MemoryAutopsyEngine,
    ObservationBuilder,
    QuestionIntent,
    SensitivityEngine,
    TestDesigner,
    TestRunner,
)
from core import Experiment, ExperimentConfig, run_experiment


@pytest.fixture
def sample_experiment():
    """Build a deterministic small interference experiment."""
    config = ExperimentConfig.from_api({
        "seed": 42,
        "mechanism": "interference",
        "params": {
            "state_dim": 64,
            "update_strength": 0.8,
            "decay": 0.1,
            "interference_strength": 0.5,
        },
        "task": {
            "d": 64,
            "n_objects": 4,
            "n_symbols": 3,
            "n_conflicts": 2,
            "object_similarity": 0.3,
            "cycles": 1,
            "order": "interleaved",
        },
    })
    return run_experiment(config)


def test_question_parser_intents():
    p1 = DeterministicQuestionParser.parse("Why did this memory weaken so quickly?")
    assert p1["intent"] == QuestionIntent.MEMORY_DECAY.value
    assert "memory_strength_trajectory" in p1["required_data"]

    p2 = DeterministicQuestionParser.parse("Why did these two memories interfere?")
    assert p2["intent"] == QuestionIntent.INTERFERENCE.value
    assert "competition_graph" in p2["required_data"]

    p3 = DeterministicQuestionParser.parse("Why did Memory obj_A survive despite conflicts?")
    assert p3["intent"] == QuestionIntent.PERSISTENCE.value
    assert p3["target_memory"] is not None

    p4 = DeterministicQuestionParser.parse("What caused this state transition at event E12?")
    assert p4["intent"] == QuestionIntent.STATE_SHIFT.value or p4["intent"] == QuestionIntent.EVENT_IMPACT.value
    assert p4["target_event"] is not None

    p5 = DeterministicQuestionParser.parse("Why did the counterfactual diverge here?")
    assert p5["intent"] == QuestionIntent.COUNTERFACTUAL.value


def test_observation_builder(sample_experiment):
    observations = ObservationBuilder.extract_observations(sample_experiment)
    assert len(observations) >= 2

    # Check metric names
    metric_names = [o.metric_name for o in observations]
    assert "representation_strength" in metric_names
    assert "substrate_state_shift" in metric_names

    # Check that it displays OBSERVED data
    first_obs = observations[0]
    assert first_obs.target_memory is not None
    assert isinstance(first_obs.initial_value, float)
    assert isinstance(first_obs.final_value, float)
    assert first_obs.summary != ""


def test_hypothesis_generator_competing_explanations(sample_experiment):
    observations = ObservationBuilder.extract_observations(sample_experiment)
    hyps = HypothesisGenerator.generate_hypotheses(observations, sample_experiment, QuestionIntent.INTERFERENCE)

    # Must provide MULTIPLE competing explanations, never just one
    assert len(hyps) >= 3
    primary = [h for h in hyps if h.is_primary]
    assert len(primary) == 1

    # Check that alternatives are linked
    for h in hyps:
        assert len(h.alternative_explanations) == len(hyps) - 1
        assert h.required_test != ""
        assert h.status == CausalSupportStatus.CORRELATED or h.status == CausalSupportStatus.OBSERVED


def test_test_designer_and_runner(sample_experiment):
    observations = ObservationBuilder.extract_observations(sample_experiment)
    hyps = HypothesisGenerator.generate_hypotheses(observations, sample_experiment, QuestionIntent.INTERFERENCE)
    primary_hyp = next(h for h in hyps if h.is_primary)

    # Design test
    test_design = TestDesigner.design_test(sample_experiment, primary_hyp, observations)
    assert test_design.hypothesis_id == primary_hyp.hypothesis_id
    assert test_design.control_description != ""
    assert test_design.intervention_description != ""

    # Run test
    test_result, evidence_chain = TestRunner.run_test(sample_experiment, primary_hyp, test_design)
    assert test_result.test_id == test_design.test_id
    assert len(test_result.control_trajectory) > 0
    assert len(test_result.intervention_trajectory) > 0
    assert test_result.causal_support in [
        CausalSupportStatus.COUNTERFACTUALLY_SUPPORTED,
        CausalSupportStatus.UNSUPPORTED,
        CausalSupportStatus.CONTRADICTED,
    ]
    assert len(evidence_chain.steps) >= 4


def test_multi_hypothesis_testing(sample_experiment):
    observations = ObservationBuilder.extract_observations(sample_experiment)
    hyps = HypothesisGenerator.generate_hypotheses(observations, sample_experiment, QuestionIntent.INTERFERENCE)

    results, chains = TestRunner.test_all_hypotheses(sample_experiment, hyps, observations)
    assert len(results) == len(hyps)
    assert len(chains) == len(hyps)


def test_memory_autopsy_engine(sample_experiment):
    # Birth Record
    birth = MemoryAutopsyEngine.get_birth_record(sample_experiment, "obj_A")
    assert birth.first_appearance_step >= 1
    assert birth.initial_strength > 0.0

    # Death Record
    death = MemoryAutopsyEngine.get_death_record(sample_experiment, "obj_A")
    assert death.last_strong_step >= 1

    # Survival and Failure Analyses
    survival = MemoryAutopsyEngine.get_survival_analysis(sample_experiment, "obj_A")
    assert "isolation_index" in survival
    failure = MemoryAutopsyEngine.get_failure_analysis(sample_experiment, "obj_A")
    assert "failure_causes" in failure

    # Signature Autopsy
    autopsy = MemoryAutopsyEngine.perform_autopsy(sample_experiment, "obj_A")
    assert autopsy.memory_id != ""
    assert "initial_strength" in autopsy.formation
    assert "competing_count" in autopsy.competition
    assert len(autopsy.supporting_evidence) >= 2


def test_sensitivity_and_robustness(sample_experiment):
    events = sample_experiment.events
    ev1 = events[1] if len(events) > 1 else None
    ev_id = getattr(ev1, "id", None) or (ev1.get("id") if isinstance(ev1, dict) else "e0001") if ev1 else "e0000"

    # Sensitivity
    sens = SensitivityEngine.measure_sensitivity(sample_experiment, "obj_A", ev_id)
    assert sens.memory_id == "obj_A"
    assert isinstance(sens.effect_size, float)

    # Minimum Intervention
    min_intv = SensitivityEngine.find_minimum_intervention(sample_experiment, "obj_A", threshold_delta=0.01)
    assert min_intv.target_memory == "obj_A"
    assert min_intv.smallest_intervention_type != ""

    # Robustness
    robust = SensitivityEngine.test_robustness(sample_experiment, "obj_A", num_variations=2)
    assert robust.classification in ["stable", "sensitive", "unstable", "inconclusive"]


def test_discovery_engine(sample_experiment):
    discoveries = DiscoveryEngine.scan_experiment(sample_experiment)
    assert isinstance(discoveries, list)
    if discoveries:
        first_disc = discoveries[0]
        assert first_disc.seed_question != ""
        assert first_disc.title != ""
        assert first_disc.category in ["persistence", "interference", "state_shift", "recovery"]


def test_investigation_store_and_reproduce(sample_experiment):
    store = InvestigationStore()

    inv = Investigation(
        experiment_id=sample_experiment.experiment_id,
        question="Why did memory obj_A weaken?",
        intent=QuestionIntent.INTERFERENCE,
        target_memory="obj_A",
    )
    obs = ObservationBuilder.extract_observations(sample_experiment, "obj_A")
    inv.observations = obs
    inv.candidate_hypotheses = HypothesisGenerator.generate_hypotheses(obs, sample_experiment, QuestionIntent.INTERFERENCE)
    test_design = TestDesigner.design_test(sample_experiment, inv.candidate_hypotheses[0], obs)
    inv.tests = [test_design]

    store.save_investigation(inv)
    fetched = store.get_investigation(inv.investigation_id)
    assert fetched is not None
    assert fetched.question == inv.question

    # Reproduce
    reproduced = store.reproduce_investigation(inv.investigation_id, sample_experiment)
    assert reproduced.investigation_id != inv.investigation_id
    assert reproduced.status in [InvestigationStatus.CONFIRMED, InvestigationStatus.INCONCLUSIVE]
    assert "scorecard" in reproduced.to_dict()

    # Scorecard
    scorecard = store.build_scorecard(reproduced)
    assert "primary_hypothesis" in scorecard
    assert "verdict" in scorecard
