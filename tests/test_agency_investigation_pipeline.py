"""Tests for multi-agent investigation pipeline, parallel workers, war room, and REST APIs (Phase 05)."""

import pytest
from fastapi.testclient import TestClient

from agency.orchestration.investigation import Investigation, ResearchDirector, run_research_investigation
from agency.orchestration.war_room import WarRoomBuilder
from agency.provenance.research_memory import ResearchMemory
from agency.runtime.execution import execute_agent, run_parallel_agents
from agency.runtime.types import AgentMission, InvestigationStatus, Verdict
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_parallel_agent_execution():
    """Verify that independent specialist agents can run concurrently in parallel worker pool."""
    from agency.agents.specialists import AIEngineerAgent, TestResultsAnalyzerAgent

    analyst = TestResultsAnalyzerAgent()
    ai_eng = AIEngineerAgent()

    ev = [{
        "parameter": "decay",
        "values": [0.0, 0.5, 1.0],
        "metric": "memory_retention",
        "means": [0.95, 0.50, 0.05],
        "correlation": -0.99,
        "pattern": "monotonic",
    }]

    m1 = AgentMission(
        mission_id="m_par_1",
        research_question="Analyze decay trend",
        target_agent=analyst.name,
        available_evidence=ev,
    )
    m2 = AgentMission(
        mission_id="m_par_2",
        research_question="Evaluate vector bounds",
        target_agent=ai_eng.name,
        available_evidence=ev,
    )

    outputs = run_parallel_agents([
        (analyst, m1, None),
        (ai_eng, m2, None),
    ])

    assert len(outputs) == 2
    agents = {o.agent for o in outputs}
    assert "Data Analyst" in agents
    assert "AI Engineer" in agents


def test_failed_agent_graceful_handling():
    """Verify that an agent failure does not crash the pipeline and produces fallback output."""
    class FailingAgent:
        name = "Buggy Agent"
        slug = "buggy-agent"

        def execute_mission(self, mission, context=None):
            raise RuntimeError("Simulated unexpected agent crash!")

    mission = AgentMission(
        mission_id="m_fail",
        research_question="Will this crash?",
        target_agent="Buggy Agent",
    )

    out = execute_agent(FailingAgent(), mission)
    assert out.verdict == Verdict.UNKNOWN
    assert out.confidence == 0.0
    assert "Execution failed" in out.analysis
    assert out.provenance.get("failed") is True


def test_war_room_state_construction():
    """Verify Research War Room station data model."""
    war_room = WarRoomBuilder.build_state(
        investigation_id="inv_war_room_test",
        question="Does interference decay over time?",
        status="completed",
        round_number=1,
        agent_outputs=[
            {"agent": "Data Analyst", "analysis": "Decay observed.", "confidence": 0.88, "verdict": "supported"},
            {"agent": "Red Team", "objections": []},
        ],
        experiments=[{"experiment_id": "exp_1", "title": "Decay Sweep"}],
        disagreements=[],
    )

    assert war_room.investigation_id == "inv_war_room_test"
    assert "director" in war_room.stations
    assert "experiment_lab" in war_room.stations
    assert "memory_engine" in war_room.stations
    assert "analyst" in war_room.stations
    assert "red_team" in war_room.stations
    assert "debate" in war_room.stations
    assert war_room.consensus_meter >= 0.8


def test_agency_rest_api_lifecycle(client):
    """Test full REST API lifecycle for investigations."""
    # 1. List available agents
    r_agents = client.get("/api/agency/agents")
    assert r_agents.status_code == 200
    agents_data = r_agents.json()
    assert agents_data["total"] >= 9

    # 2. Get specific agent details
    r_agent = client.get("/api/agency/agents/testing-reality-checker")
    assert r_agent.status_code == 200
    assert r_agent.json()["name"] == "Reality Checker"

    # 3. Create investigation
    r_create = client.post(
        "/api/agency/investigations",
        json={"research_question": "Does memory similarity cause interference?"},
    )
    assert r_create.status_code == 200
    inv = r_create.json()
    inv_id = inv["investigation_id"]
    assert inv["status"] == "planning"

    # 4. List investigations
    r_list = client.get("/api/agency/investigations")
    assert r_list.status_code == 200
    assert any(i["investigation_id"] == inv_id for i in r_list.json()["investigations"])

    # 5. Export Antigravity skills
    r_export = client.post("/api/agency/antigravity/export", json={})
    assert r_export.status_code == 200
    assert r_export.json()["total_exported"] >= 9
