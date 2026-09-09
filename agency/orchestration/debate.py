"""Specialist debate, disagreement capture, and consensus determination (Phase 05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..runtime.types import ConsensusStatus, SpecialistOutput, Verdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DisagreementRecord:
    """Explicit structured record of a scientific disagreement between specialists."""
    disagreement_id: str
    topic: str
    agent_a: str
    claim_a: str
    verdict_a: str
    agent_b: str
    claim_b: str
    verdict_b: str
    underlying_issue: str
    proposed_resolution: str
    resolved: bool = False
    resolution_experiment_id: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disagreement_id": self.disagreement_id,
            "topic": self.topic,
            "agent_a": self.agent_a,
            "claim_a": self.claim_a,
            "verdict_a": self.verdict_a,
            "agent_b": self.agent_b,
            "claim_b": self.claim_b,
            "verdict_b": self.verdict_b,
            "underlying_issue": self.underlying_issue,
            "proposed_resolution": self.proposed_resolution,
            "resolved": self.resolved,
            "resolution_experiment_id": self.resolution_experiment_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DisagreementRecord":
        return cls(
            disagreement_id=d["disagreement_id"],
            topic=d["topic"],
            agent_a=d["agent_a"],
            claim_a=d["claim_a"],
            verdict_a=d["verdict_a"],
            agent_b=d["agent_b"],
            claim_b=d["claim_b"],
            verdict_b=d["verdict_b"],
            underlying_issue=d["underlying_issue"],
            proposed_resolution=d["proposed_resolution"],
            resolved=d.get("resolved", False),
            resolution_experiment_id=d.get("resolution_experiment_id"),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class ResearchConsensus:
    """Current synthesized consensus across specialists."""
    status: ConsensusStatus
    synthesized_verdict: Verdict
    primary_finding: str
    supporting_agents: List[str] = field(default_factory=list)
    dissenting_agents: List[str] = field(default_factory=list)
    active_objections: List[str] = field(default_factory=list)
    confidence: float = 0.5
    recommended_next_action: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "synthesized_verdict": self.synthesized_verdict.value,
            "primary_finding": self.primary_finding,
            "supporting_agents": self.supporting_agents,
            "dissenting_agents": self.dissenting_agents,
            "active_objections": self.active_objections,
            "confidence": self.confidence,
            "recommended_next_action": self.recommended_next_action,
            "timestamp": self.timestamp,
        }


class ResearchDebateManager:
    """Detects contradictions between specialists and manages structured disagreements."""

    @classmethod
    def evaluate_outputs(
        cls,
        outputs: List[SpecialistOutput],
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[DisagreementRecord], ResearchConsensus]:
        """Analyze specialist outputs, detect disagreements, and formulate honest consensus."""
        if not outputs:
            return [], ResearchConsensus(
                status=ConsensusStatus.UNKNOWN,
                synthesized_verdict=Verdict.UNKNOWN,
                primary_finding="No specialist outputs available for debate.",
                confidence=0.0,
                recommended_next_action="dispatch_specialists",
            )

        disagreements: List[DisagreementRecord] = []
        analyst_out: Optional[SpecialistOutput] = None
        red_team_out: Optional[SpecialistOutput] = None

        for out in outputs:
            name_lower = out.agent.lower()
            if "analyst" in name_lower or "test results" in name_lower:
                analyst_out = out
            elif "red team" in name_lower or "reality checker" in name_lower:
                red_team_out = out

        # Detect specific Analyst vs Red Team contradiction
        if analyst_out and red_team_out:
            analyst_supports = analyst_out.verdict == Verdict.SUPPORTED
            red_team_challenges = red_team_out.verdict in (Verdict.QUESTIONABLE, Verdict.WEAKENED)

            if analyst_supports and red_team_challenges:
                objection_text = red_team_out.objections[0] if red_team_out.objections else "Uncontrolled variables"
                disagreements.append(
                    DisagreementRecord(
                        disagreement_id=f"disagree_{len(disagreements) + 1}",
                        topic="Causal attribution vs Confounding variables",
                        agent_a=analyst_out.agent,
                        claim_a=analyst_out.analysis,
                        verdict_a=analyst_out.verdict.value,
                        agent_b=red_team_out.agent,
                        claim_b=red_team_out.analysis,
                        verdict_b=red_team_out.verdict.value,
                        underlying_issue=objection_text,
                        proposed_resolution="Execute discriminating experiment or 2D sweep to isolate parameter interaction.",
                    )
                )

        # Formulate consensus
        supporting = [o.agent for o in outputs if o.verdict == Verdict.SUPPORTED]
        dissenting = [o.agent for o in outputs if o.verdict in (Verdict.QUESTIONABLE, Verdict.WEAKENED)]
        all_objections = [obj for o in outputs for obj in o.objections]

        if disagreements:
            status = ConsensusStatus.DISAGREEMENT
            verdict = Verdict.QUESTIONABLE
            finding = (
                f"Disagreement active between {disagreements[0].agent_a} and {disagreements[0].agent_b}. "
                f"Red Team raised objection: '{disagreements[0].underlying_issue}'."
            )
            rec_action = "run_discriminating_experiment"
            confidence = 0.55
        elif dissenting:
            status = ConsensusStatus.DISAGREEMENT
            verdict = Verdict.QUESTIONABLE
            finding = f"Hypothesis questioned by dissenting agents: {', '.join(dissenting)}."
            rec_action = "redesign_experiment"
            confidence = 0.6
        elif supporting and not dissenting:
            status = ConsensusStatus.AGREEMENT
            verdict = Verdict.SUPPORTED
            finding = "All specialists agree: Empirical results support the research hypothesis."
            rec_action = "synthesize_and_complete"
            confidence = 0.85
        else:
            status = ConsensusStatus.INSUFFICIENT_EVIDENCE
            verdict = Verdict.INSUFFICIENT_EVIDENCE
            finding = "Insufficient evidence to establish conclusive support or refutation."
            rec_action = "gather_additional_evidence"
            confidence = 0.3

        consensus = ResearchConsensus(
            status=status,
            synthesized_verdict=verdict,
            primary_finding=finding,
            supporting_agents=supporting,
            dissenting_agents=dissenting,
            active_objections=all_objections,
            confidence=confidence,
            recommended_next_action=rec_action,
        )

        return disagreements, consensus
