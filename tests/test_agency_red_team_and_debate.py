"""Tests for Red Team hostile challenges, structured research debates, and consensus determination (Phase 05)."""

import pytest

from agency.orchestration.debate import ResearchDebateManager
from agency.runtime.types import ConsensusStatus, SpecialistOutput, Verdict


def test_structured_disagreement_detection():
    """Verify that contradiction between Data Analyst and Red Team creates a structured disagreement."""
    analyst_out = SpecialistOutput(
        agent="Data Analyst",
        mission_id="m_analyst",
        analysis="Similarity strongly correlates with increased interference score (r=0.98).",
        verdict=Verdict.SUPPORTED,
        confidence=0.9,
    )

    red_team_out = SpecialistOutput(
        agent="Red Team",
        mission_id="m_redteam",
        analysis="Alternative explanation: Write strength interacts with similarity; write gain is a confounder.",
        objections=["Write strength is an uncontrolled confounder that could produce identical interference."],
        verdict=Verdict.QUESTIONABLE,
        confidence=0.85,
    )

    outputs = [analyst_out, red_team_out]
    disagreements, consensus = ResearchDebateManager.evaluate_outputs(outputs)

    # 1. Disagreement must be captured explicitly
    assert len(disagreements) == 1
    d = disagreements[0]
    assert d.agent_a == "Data Analyst"
    assert d.agent_b == "Red Team"
    assert "confounder" in d.underlying_issue.lower()
    assert d.resolved is False

    # 2. Consensus must NOT launder disagreement into false majority agreement
    assert consensus.status == ConsensusStatus.DISAGREEMENT
    assert consensus.synthesized_verdict == Verdict.QUESTIONABLE
    assert "run_discriminating_experiment" in consensus.recommended_next_action


def test_unanimous_agreement_consensus():
    """Verify that when all specialists agree, consensus status is AGREEMENT."""
    analyst_out = SpecialistOutput(
        agent="Data Analyst",
        mission_id="m1",
        analysis="Monotonic decay confirmed across 6 conditions.",
        verdict=Verdict.SUPPORTED,
        confidence=0.9,
    )
    red_team_out = SpecialistOutput(
        agent="Red Team",
        mission_id="m2",
        analysis="All controls verified, multi-trial variance bounded, effect size is large.",
        objections=[],
        verdict=Verdict.SUPPORTED,
        confidence=0.85,
    )

    disagreements, consensus = ResearchDebateManager.evaluate_outputs([analyst_out, red_team_out])
    assert len(disagreements) == 0
    assert consensus.status == ConsensusStatus.AGREEMENT
    assert consensus.synthesized_verdict == Verdict.SUPPORTED


def test_insufficient_evidence_consensus():
    """Verify that when evidence is inadequate, consensus reflects INSUFFICIENT_EVIDENCE."""
    analyst_out = SpecialistOutput(
        agent="Data Analyst",
        mission_id="m1",
        analysis="Data is too sparse to evaluate.",
        verdict=Verdict.INSUFFICIENT_EVIDENCE,
        confidence=0.2,
    )
    disagreements, consensus = ResearchDebateManager.evaluate_outputs([analyst_out])
    assert consensus.status == ConsensusStatus.INSUFFICIENT_EVIDENCE
    assert consensus.synthesized_verdict == Verdict.INSUFFICIENT_EVIDENCE
