"""Agent provenance data models for multi-agent research orchestration (Phase 05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentProvenance:
    """Detailed audit record guaranteeing provenance for every agent action."""
    agent_name: str
    agent_slug: str
    mission_id: str
    agent_source: str = "msitarzewski/agency-agents"
    agent_version: str = "1.0.0"
    model_provider: str = "deterministic_local_engine"
    prompt_version: str = "1.0.0"
    input_experiment_id: Optional[str] = None
    input_counterfactual_id: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_slug": self.agent_slug,
            "mission_id": self.mission_id,
            "agent_source": self.agent_source,
            "agent_version": self.agent_version,
            "model_provider": self.model_provider,
            "prompt_version": self.prompt_version,
            "input_experiment_id": self.input_experiment_id,
            "input_counterfactual_id": self.input_counterfactual_id,
            "tools_used": self.tools_used,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentProvenance":
        return cls(
            agent_name=d["agent_name"],
            agent_slug=d["agent_slug"],
            mission_id=d["mission_id"],
            agent_source=d.get("agent_source", "msitarzewski/agency-agents"),
            agent_version=d.get("agent_version", "1.0.0"),
            model_provider=d.get("model_provider", "deterministic_local_engine"),
            prompt_version=d.get("prompt_version", "1.0.0"),
            input_experiment_id=d.get("input_experiment_id"),
            input_counterfactual_id=d.get("input_counterfactual_id"),
            tools_used=d.get("tools_used", []),
            parameters=d.get("parameters", {}),
            timestamp=d.get("timestamp", _now_iso()),
        )
