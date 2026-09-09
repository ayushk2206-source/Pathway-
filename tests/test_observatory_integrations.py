"""Integration tests for Phase 19 with Phases 15, 16, 17, and 18."""

import pytest
from core.observatory import (
    AdaptiveObservatoryEngine,
    StreamEvent,
)


def test_surgery_intervention_branching():
    """Verify Phase 15 integration: branching forward after synaptic ablation."""
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    branch_session, record = AdaptiveObservatoryEngine.branch_intervention(
        session=session,
        intervention_step=2,
        operation="silence",
        synapse_ids=["syn_k0_v0", "syn_k1_v1"],
    )

    assert branch_session.session_id != session.session_id
    assert len(session.branches) >= 1
    assert record["operation"] == "silence"
    assert "syn_k0_v0" in record["weight_deltas"]


def test_counterfactual_branching():
    """Verify Phase 16 integration: counterfactual branching from an observatory timestep."""
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    cf_session, cf_record = AdaptiveObservatoryEngine.branch_counterfactual(
        session=session,
        intervention_step=5,
        counterfactual_label="Counterfactual: Protected Weights",
    )

    assert cf_session.session_id != session.session_id
    assert "Counterfactual" in cf_record.get("counterfactual_title", "")


def test_session_comparison():
    """Verify side-by-side comparison of two sessions."""
    session_a, _ = AdaptiveObservatoryEngine.run_env_shift_protocol(decay=0.01, update_strength=1.5)
    session_b, _ = AdaptiveObservatoryEngine.run_env_shift_protocol(decay=0.08, update_strength=0.5)

    comp = AdaptiveObservatoryEngine.compare_sessions(session_a, session_b)
    assert comp["session_a_id"] == session_a.session_id
    assert comp["session_b_id"] == session_b.session_id
    assert comp["matrix_frobenius_divergence"] > 0.0
    assert len(comp["divergence_trajectory"]) > 0
    assert len(comp["recall_comparison"]) > 0


def test_export_to_detective_case():
    """Verify Phase 18 integration: exporting an observatory anomaly as a Detective Case."""
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    case = AdaptiveObservatoryEngine.export_to_detective_case(
        session=session,
        anomaly_step=6,
        target_memory="solaris",
    )

    assert case.case_id.startswith("CASE-OBS-")
    assert case.case_code == "CASE_OBSERVATORY_STREAM_ANOMALY"
    assert case.target_memory == "solaris"
    assert len(case.candidate_hypotheses) == 3
    assert len(case.available_evidence) == 3
    assert case.ground_truth_hypothesis_id == "HYP-OBS-1"
    assert len(case.claim_traceability) > 0
