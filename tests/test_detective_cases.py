"""Tests for Phase 18 Memory Detective Cases & Forensics Scoring."""

import pytest
from core.forensics import (
    CaseGenerator,
    InvestigationCase,
    score_investigation,
    VERIFIED_SOURCES,
    CORE_LEARNING_OBJECTIVES,
)


def test_case_generator_all_cases():
    """Verify CaseGenerator produces all 6 required bounded investigation cases."""
    cases = CaseGenerator.generate_all_cases()
    assert len(cases) == 6

    case_codes = [c.case_code for c in cases]
    assert "CASE_A_NORMAL_SURVIVAL" in case_codes
    assert "CASE_B_INTERFERENCE_WEAKENED" in case_codes
    assert "CASE_C_SYNAPTIC_ABLATION" in case_codes
    assert "CASE_D_COUNTERFACTUAL_RECOVERY" in case_codes
    assert "CASE_E_COLLISION_OVERLAP" in case_codes
    assert "CASE_F_TEMPORAL_DECAY" in case_codes


def test_case_metrics_real_computation():
    """Verify that case metrics reflect real linear algebra rather than arbitrary hardcoding."""
    case_b = CaseGenerator.generate_case_b()
    assert case_b.initial_recall > 0.90
    assert case_b.final_recall < case_b.initial_recall
    assert len(case_b.available_evidence) >= 3

    case_c = CaseGenerator.generate_case_c()
    assert case_c.intervention_step == 2
    assert case_c.initial_recall > case_c.final_recall

    case_d = CaseGenerator.generate_case_d()
    assert case_d.final_recall > case_d.initial_recall  # Counterfactual recovery


def test_verified_sources_and_claim_traceability():
    """Verify verified sources registry and claim traceability."""
    assert len(VERIFIED_SOURCES) >= 3
    for src in VERIFIED_SOURCES:
        assert src.year >= 2022
        assert src.doi != ""
        assert src.authors != ""

    cases = CaseGenerator.generate_all_cases()
    for c in cases:
        assert len(c.claim_traceability) > 0
        claim = c.claim_traceability[0]
        assert "paper_citation" in claim
        assert "claim" in claim
        assert "observation" in claim


def test_investigation_scoring():
    """Verify that scientific detective scoring accurately rewards correct hypotheses and critical evidence."""
    case = CaseGenerator.generate_case_b()

    # Perfect run
    critical_ids = [e.evidence_id for e in case.available_evidence if e.is_critical]
    score_perfect = score_investigation(
        case=case,
        chosen_hypothesis_id=case.ground_truth_hypothesis_id,
        collected_evidence_ids=critical_ids,
        tests_run_count=2,
        learner_confidence="HIGH",
        explanation_chain=["MEMORY_WRITE", "SYNAPTIC_UPDATE", "INTERFERENCE", "RECALL_DROP"],
    )
    assert score_perfect.score >= 90
    assert score_perfect.rating == "MASTER_DETECTIVE"
    assert score_perfect.hypothesis_correct is True

    # Flawed run
    wrong_hyp = next(h.hypothesis_id for h in case.candidate_hypotheses if not h.is_correct)
    score_flawed = score_investigation(
        case=case,
        chosen_hypothesis_id=wrong_hyp,
        collected_evidence_ids=[],
        tests_run_count=7,  # Excessive unguided tests
        learner_confidence="HIGH",
        explanation_chain=[],
    )
    assert score_flawed.score < 50
    assert score_flawed.rating == "NEEDS_WORK"
    assert score_flawed.hypothesis_correct is False
