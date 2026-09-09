"""Agent execution engine supporting sequential and parallel specialist execution (Phase 05)."""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from ..agents.base import SpecialistAgent
from ..agents.specialists import (
    AIEngineerAgent,
    CodeReviewerAgent,
    CodebaseArchaeologistAgent,
    DataVisualizationEngineerAgent,
    RealityCheckerAgent,
    ResearchDirectorAgent,
    ResearchSynthesistAgent,
    StatisticianAgent,
    TestResultsAnalyzerAgent,
)
from .types import AgentMission, SpecialistOutput, Verdict


class AgentExecutionError(RuntimeError):
    """Raised when an agent execution fails critically."""
    pass


class SpecialistFactory:
    """Instantiates concrete specialist agents by name or slug."""

    _SPECIALISTS = {
        "agents-orchestrator": ResearchDirectorAgent,
        "research director": ResearchDirectorAgent,
        "director": ResearchDirectorAgent,
        "academic-statistician": StatisticianAgent,
        "statistician": StatisticianAgent,
        "testing-test-results-analyzer": TestResultsAnalyzerAgent,
        "data analyst": TestResultsAnalyzerAgent,
        "analyst": TestResultsAnalyzerAgent,
        "testing-reality-checker": RealityCheckerAgent,
        "red team": RealityCheckerAgent,
        "reality checker": RealityCheckerAgent,
        "research-synthesist": ResearchSynthesistAgent,
        "research synthesist": ResearchSynthesistAgent,
        "synthesist": ResearchSynthesistAgent,
        "engineering-ai-engineer": AIEngineerAgent,
        "ai engineer": AIEngineerAgent,
        "specialized-codebase-archaeologist": CodebaseArchaeologistAgent,
        "codebase archaeologist": CodebaseArchaeologistAgent,
        "engineering-data-visualization-engineer": DataVisualizationEngineerAgent,
        "visualization engineer": DataVisualizationEngineerAgent,
        "engineering-code-reviewer": CodeReviewerAgent,
        "code reviewer": CodeReviewerAgent,
    }

    @classmethod
    def get_agent(cls, name_or_slug: str) -> SpecialistAgent:
        clean = name_or_slug.lower().strip()
        agent_cls = cls._SPECIALISTS.get(clean)
        if agent_cls:
            return agent_cls()
        # Fallback to general ResearchDirector if unrecognized
        return ResearchDirectorAgent()


def execute_agent(
    agent: Union[str, SpecialistAgent, Any],
    mission: AgentMission,
    context: Optional[Dict[str, Any]] = None,
) -> SpecialistOutput:
    """Execute a single specialist agent safely with error catching."""
    if hasattr(agent, "execute_mission"):
        specialist = agent
    elif isinstance(agent, str):
        specialist = SpecialistFactory.get_agent(agent)
    else:
        specialist = SpecialistFactory.get_agent(getattr(agent, "name", str(agent)))

    try:
        return specialist.execute_mission(mission, context=context)
    except Exception as exc:
        # Fallback output on agent failure
        agent_name = getattr(specialist, "name", "Specialist")
        agent_slug = getattr(specialist, "slug", "unknown")
        return SpecialistOutput(
            agent=agent_name,
            mission_id=mission.mission_id,
            assumptions=["Agent encountered execution error"],
            analysis=f"Execution failed: {str(exc)}",
            evidence=[],
            objections=[f"Agent failed with error: {str(exc)}"],
            recommendation="Review agent logs and retry mission.",
            verdict=Verdict.UNKNOWN,
            confidence=0.0,
            proposed_next_action="fail_gracefully",
            provenance={
                "agent_name": agent_name,
                "agent_slug": agent_slug,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "failed": True,
            },
        )


def run_parallel_agents(
    tasks: List[Tuple[Union[str, SpecialistAgent], AgentMission, Optional[Dict[str, Any]]]],
    max_workers: int = 4,
) -> List[SpecialistOutput]:
    """Execute multiple independent specialist agents in parallel."""
    if not tasks:
        return []

    outputs: List[SpecialistOutput] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(execute_agent, agent, mission, ctx): (agent, mission)
            for agent, mission, ctx in tasks
        }
        for future in concurrent.futures.as_completed(future_to_task):
            try:
                out = future.result()
                outputs.append(out)
            except Exception as exc:
                agent, mission = future_to_task[future]
                agent_name = agent.name if isinstance(agent, SpecialistAgent) else str(agent)
                outputs.append(
                    SpecialistOutput(
                        agent=agent_name,
                        mission_id=mission.mission_id,
                        analysis=f"Parallel worker failure: {str(exc)}",
                        verdict=Verdict.UNKNOWN,
                        confidence=0.0,
                        provenance={"error": str(exc), "failed": True},
                    )
                )

    return outputs
