"""Base specialist agent class for Agency Agents integration (Phase 05)."""

from __future__ import annotations

import abc
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..catalog.registry import AgentDefinition, SPECIALIST_REGISTRY
from ..runtime.types import AgentMission, SpecialistOutput, Verdict


class SpecialistAgent(abc.ABC):
    """Abstract base class for Agency Agents specialist personas."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.definition: Optional[AgentDefinition] = SPECIALIST_REGISTRY.get(slug)
        if self.definition:
            self.name = self.definition.name
            self.division = self.definition.division
            self.vibe = self.definition.vibe
            self.description = self.definition.description
            self.instructions = self.definition.instructions
        else:
            self.name = slug.replace("-", " ").title()
            self.division = "general"
            self.vibe = ""
            self.description = ""
            self.instructions = ""

    def _build_provenance(self, mission: AgentMission) -> Dict[str, Any]:
        """Record complete agent provenance for this execution."""
        return {
            "agent_name": self.name,
            "agent_slug": self.slug,
            "agent_division": self.division,
            "upstream_source": "msitarzewski/agency-agents",
            "mission_id": mission.mission_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "deterministic_execution": True,
        }

    @abc.abstractmethod
    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        """Process structured mission and return structured output adhering to contract."""
        raise NotImplementedError
