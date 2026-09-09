"""Runtime types, schemas, and resource limits for Agency Agents (Phase 05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Strict Computational & Agent Quotas
# ---------------------------------------------------------------------------
MAX_AGENTS_PER_INVESTIGATION: int = 10
MAX_AGENT_ROUNDS: int = 5
MAX_RESEARCH_DEPTH: int = 3
MAX_EXPERIMENTS_PER_INVESTIGATION: int = 5


class InvestigationStatus(str, Enum):
    """Lifecycle status of a multi-agent research investigation."""
    PLANNING = "planning"
    RUNNING = "running"
    ANALYZING = "analyzing"
    CHALLENGING = "challenging"
    REQUIRES_EXPERIMENT = "requires_experiment"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"
    FAILED = "failed"
    PARTIALLY_COMPLETE = "partially_complete"


class Verdict(str, Enum):
    """Evaluation verdict for empirical hypotheses and claims."""
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    QUESTIONABLE = "questionable"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNKNOWN = "unknown"


class ConsensusStatus(str, Enum):
    """Status of research consensus across specialists."""
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass
class AgentMission:
    """Structured mission dispatched to a specialist agent."""
    mission_id: str
    research_question: str
    target_agent: str
    hypothesis: Optional[str] = None
    experiment_id: Optional[str] = None
    available_evidence: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    required_deliverable: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "research_question": self.research_question,
            "target_agent": self.target_agent,
            "hypothesis": self.hypothesis,
            "experiment_id": self.experiment_id,
            "available_evidence": self.available_evidence,
            "constraints": self.constraints,
            "required_deliverable": self.required_deliverable,
            "provenance": self.provenance,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentMission":
        return cls(
            mission_id=d["mission_id"],
            research_question=d["research_question"],
            target_agent=d.get("target_agent", "unknown"),
            hypothesis=d.get("hypothesis"),
            experiment_id=d.get("experiment_id"),
            available_evidence=d.get("available_evidence", []),
            constraints=d.get("constraints", []),
            required_deliverable=d.get("required_deliverable", ""),
            provenance=d.get("provenance", {}),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class SpecialistOutput:
    """Standard structured output contract returned by every specialist agent."""
    agent: str
    mission_id: str
    assumptions: List[str] = field(default_factory=list)
    analysis: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)
    recommendation: str = ""
    verdict: Verdict = Verdict.UNKNOWN
    confidence: float = 0.5
    proposed_next_action: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "mission_id": self.mission_id,
            "assumptions": self.assumptions,
            "analysis": self.analysis,
            "evidence": self.evidence,
            "objections": self.objections,
            "recommendation": self.recommendation,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "proposed_next_action": self.proposed_next_action,
            "provenance": self.provenance,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SpecialistOutput":
        verdict_str = d.get("verdict", Verdict.UNKNOWN.value)
        try:
            verdict = Verdict(verdict_str)
        except ValueError:
            verdict = Verdict.UNKNOWN

        return cls(
            agent=d["agent"],
            mission_id=d["mission_id"],
            assumptions=d.get("assumptions", []),
            analysis=d.get("analysis", ""),
            evidence=d.get("evidence", []),
            objections=d.get("objections", []),
            recommendation=d.get("recommendation", ""),
            verdict=verdict,
            confidence=float(d.get("confidence", 0.5)),
            proposed_next_action=d.get("proposed_next_action"),
            provenance=d.get("provenance", {}),
            created_at=d.get("created_at", _now_iso()),
        )
