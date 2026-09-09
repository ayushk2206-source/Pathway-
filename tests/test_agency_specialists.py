"""Tests for Agency specialist execution and structured output contracts (Phase 05)."""

import pytest

from agency.agents.specialists import (
    AIEngineerAgent,
    RealityCheckerAgent,
    ResearchDirectorAgent,
    ResearchSynthesistAgent,
    StatisticianAgent,
    TestResultsAnalyzerAgent,
)
from agency.runtime.execution import execute_agent
from agency.runtime.types import AgentMission, Verdict


def test_research_director_mission():
    """Verify Research Director decomposes questions and recommends parameter sweeps."""
    agent = ResearchDirectorAgent()
    mission = AgentMission(
        mission_id="m1",
        research_question="Does increasing memory similarity increase interference?",
        target_agent=agent.name,
    )
    out = execute_agent(agent, mission)

    assert out.agent == "Research Director"
    assert out.mission_id == "m1"
    assert len(out.assumptions) >= 2
    assert "memory_similarity" in out.analysis
    assert "interference_score" in out.analysis
    assert out.verdict == Verdict.UNKNOWN  # Director plans before data
    assert out.confidence > 0.5
    assert out.provenance["upstream_source"] == "msitarzewski/agency-agents"


def test_statistician_study_design():
    """Verify Statistician creates pre-specified study designs with controls."""
    agent = StatisticianAgent()
    mission = AgentMission(
        mission_id="m2",
        research_question="Does increasing memory similarity increase interference?",
        target_agent=agent.name,
        hypothesis="Increasing similarity increases interference.",
    )
    out = execute_agent(agent, mission)

    assert out.agent == "Statistician"
    assert len(out.evidence) == 1
    design = out.evidence[0]
    assert design["parameter"] == "memory_similarity"
    assert len(design["values"]) >= 4
    assert design["trials"] >= 2
    assert "update_strength" in design["controls"]
    assert out.proposed_next_action == "validate_and_run_experiment"


def test_data_analyst_with_and_without_evidence():
    """Verify Data Analyst produces real quantitative metrics with evidence and returns UNKNOWN without."""
    agent = TestResultsAnalyzerAgent()

    # 1. Without evidence -> UNKNOWN
    empty_mission = AgentMission(
        mission_id="m3_empty",
        research_question="What is the trend?",
        target_agent=agent.name,
        available_evidence=[],
    )
    empty_out = execute_agent(agent, empty_mission)
    assert empty_out.verdict == Verdict.UNKNOWN
    assert empty_out.confidence == 0.0
    assert "No experimental evidence provided" in empty_out.analysis

    # 2. With real evidence -> calculates delta, correlation, pattern
    ev = [{
        "parameter": "memory_similarity",
        "values": [0.0, 0.2, 0.4, 0.6, 0.8],
        "metric": "interference_score",
        "means": [0.12, 0.24, 0.38, 0.55, 0.74],
        "correlation": 0.985,
        "pattern": "monotonic",
    }]
    full_mission = AgentMission(
        mission_id="m3_full",
        research_question="Analyze similarity vs interference",
        target_agent=agent.name,
        available_evidence=ev,
    )
    full_out = execute_agent(agent, full_mission)
    assert full_out.verdict == Verdict.SUPPORTED
    assert full_out.confidence >= 0.8
    assert "0.74" in full_out.analysis or "increased" in full_out.analysis


def test_reality_checker_hostile_review():
    """Verify Red Team reality checker identifies potential confounders and defaults to skepticism."""
    agent = RealityCheckerAgent()

    # Evidence with coarse sampling and potential confounder
    ev = [{
        "parameter": "memory_similarity",
        "values": [0.1, 0.5],
        "metric": "interference_score",
        "means": [0.2, 0.5],
        "trials": 1,  # Low sample size trigger
    }]
    mission = AgentMission(
        mission_id="m4",
        research_question="Check claim validity",
        target_agent=agent.name,
        available_evidence=ev,
    )
    out = execute_agent(agent, mission)

    assert out.agent == "Red Team"
    assert out.verdict == Verdict.QUESTIONABLE
    assert len(out.objections) >= 1
    # Check that sample size or confounder objection was raised
    assert any("power" in obj.lower() or "confounder" in obj.lower() or "trial" in obj.lower() for obj in out.objections)
