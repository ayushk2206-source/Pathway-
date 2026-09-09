"""Research memory layer strictly separated from simulated memory (Phase 05).

Stores the meta-cognitive record of scientific inquiry: questions, hypotheses,
experiments, counterfactuals, findings, disagreements, failed attempts, and reproductions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FailedAttempt:
    """Record of an invalid or failed experiment / hypothesis attempt."""
    attempt_id: str
    stage: str
    configuration: Dict[str, Any]
    error_message: str
    underlying_hypothesis: Optional[str] = None
    lesson_learned: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "stage": self.stage,
            "configuration": self.configuration,
            "error_message": self.error_message,
            "underlying_hypothesis": self.underlying_hypothesis,
            "lesson_learned": self.lesson_learned,
            "timestamp": self.timestamp,
        }


@dataclass
class ResearchMemory:
    """Persistent meta-memory of research questions, hypotheses, and empirical evidence."""
    investigation_id: str
    questions: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    experiments: List[str] = field(default_factory=list)  # experiment IDs
    counterfactuals: List[str] = field(default_factory=list)  # counterfactual IDs
    findings: List[Dict[str, Any]] = field(default_factory=list)
    disagreements: List[Dict[str, Any]] = field(default_factory=list)
    failed_attempts: List[FailedAttempt] = field(default_factory=list)
    reproductions: List[Dict[str, Any]] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def record_question(self, question_text: str, context: Optional[Dict[str, Any]] = None) -> None:
        self.questions.append({
            "text": question_text,
            "context": context or {},
            "timestamp": _now_iso(),
        })
        self.updated_at = _now_iso()

    def record_hypothesis(self, hypothesis_dict: Dict[str, Any]) -> None:
        self.hypotheses.append(hypothesis_dict)
        self.updated_at = _now_iso()

    def record_experiment(self, experiment_id: str) -> None:
        if experiment_id not in self.experiments:
            self.experiments.append(experiment_id)
        self.updated_at = _now_iso()

    def record_counterfactual(self, counterfactual_id: str) -> None:
        if counterfactual_id not in self.counterfactuals:
            self.counterfactuals.append(counterfactual_id)
        self.updated_at = _now_iso()

    def record_finding(self, finding: Dict[str, Any]) -> None:
        self.findings.append(finding)
        self.updated_at = _now_iso()

    def record_disagreement(self, disagreement: Dict[str, Any]) -> None:
        self.disagreements.append(disagreement)
        self.updated_at = _now_iso()

    def record_failed_attempt(
        self,
        stage: str,
        config: Dict[str, Any],
        error: str,
        hypothesis: Optional[str] = None,
        lesson: str = "",
    ) -> None:
        att = FailedAttempt(
            attempt_id=f"fail_{len(self.failed_attempts) + 1}",
            stage=stage,
            configuration=config,
            error_message=error,
            underlying_hypothesis=hypothesis,
            lesson_learned=lesson,
        )
        self.failed_attempts.append(att)
        self.updated_at = _now_iso()

    def record_reproduction(self, repro_result: Dict[str, Any]) -> None:
        self.reproductions.append(repro_result)
        self.updated_at = _now_iso()

    def record_unresolved_question(self, q: str) -> None:
        if q not in self.unresolved_questions:
            self.unresolved_questions.append(q)
        self.updated_at = _now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "questions": self.questions,
            "hypotheses": self.hypotheses,
            "experiments": self.experiments,
            "counterfactuals": self.counterfactuals,
            "findings": self.findings,
            "disagreements": self.disagreements,
            "failed_attempts": [a.to_dict() for a in self.failed_attempts],
            "reproductions": self.reproductions,
            "unresolved_questions": self.unresolved_questions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResearchMemory":
        fails = [FailedAttempt(**f) if isinstance(f, dict) else f for f in d.get("failed_attempts", [])]
        return cls(
            investigation_id=d["investigation_id"],
            questions=d.get("questions", []),
            hypotheses=d.get("hypotheses", []),
            experiments=d.get("experiments", []),
            counterfactuals=d.get("counterfactuals", []),
            findings=d.get("findings", []),
            disagreements=d.get("disagreements", []),
            failed_attempts=fails,
            reproductions=d.get("reproductions", []),
            unresolved_questions=d.get("unresolved_questions", []),
            created_at=d.get("created_at", _now_iso()),
            updated_at=d.get("updated_at", _now_iso()),
        )
