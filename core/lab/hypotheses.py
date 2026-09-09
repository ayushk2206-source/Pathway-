"""Hypothesis and prediction system for Experiment Lab (Phase 03).

Provides formal hypothesis representations, pre-experiment predictions, empirical
evidence evaluation, and competing hypothesis comparisons with scientific rigor.
Never claims a hypothesis is universally "true" — adheres to falsifiable terminology.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


class PredictedDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    NO_CHANGE = "no_change"
    NON_MONOTONIC = "non_monotonic"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Prediction:
    """Pre-experiment prediction made before executing the computational test."""

    prediction_id: str
    hypothesis_id: str
    independent_variable: str
    dependent_variable: str
    predicted_direction: PredictedDirection
    expected_magnitude: Optional[float] = None
    rationale: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "hypothesis_id": self.hypothesis_id,
            "independent_variable": self.independent_variable,
            "dependent_variable": self.dependent_variable,
            "predicted_direction": self.predicted_direction.value,
            "expected_magnitude": self.expected_magnitude,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Prediction":
        return cls(
            prediction_id=d["prediction_id"],
            hypothesis_id=d["hypothesis_id"],
            independent_variable=d["independent_variable"],
            dependent_variable=d["dependent_variable"],
            predicted_direction=PredictedDirection(d["predicted_direction"]),
            expected_magnitude=d.get("expected_magnitude"),
            rationale=d.get("rationale", ""),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class PredictionEvaluation:
    """Rigorous evaluation comparing learner prediction against empirical observation."""

    prediction: Prediction
    observed_direction: PredictedDirection
    prediction_correct: bool
    observed_delta: float
    observed_correlation: Optional[float]
    evidence_strength: str  # "strong", "moderate", "weak", "inconclusive"
    verdict: str  # Cautious scientific synthesis statement

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": self.prediction.to_dict(),
            "observed_direction": self.observed_direction.value,
            "prediction_correct": self.prediction_correct,
            "observed_delta": float(self.observed_delta),
            "observed_correlation": self.observed_correlation,
            "evidence_strength": self.evidence_strength,
            "verdict": self.verdict,
        }


@dataclass
class Hypothesis:
    """A scientific hypothesis explaining memory dynamics."""

    hypothesis_id: str
    statement: str
    independent_variable: str
    dependent_variable: str
    predicted_direction: PredictedDirection
    expected_relationship: str = ""
    confidence_before: float = 0.5  # Prior confidence ∈ [0.0, 1.0]
    confidence_after: float = 0.5   # Updated confidence based on evidence
    experiments: List[str] = field(default_factory=list)  # Experiment IDs testing this
    supporting_evidence: List[str] = field(default_factory=list)
    contradictory_evidence: List[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    predictions: List[Prediction] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "statement": self.statement,
            "independent_variable": self.independent_variable,
            "dependent_variable": self.dependent_variable,
            "predicted_direction": self.predicted_direction.value,
            "expected_relationship": self.expected_relationship,
            "confidence_before": float(self.confidence_before),
            "confidence_after": float(self.confidence_after),
            "experiments": self.experiments,
            "supporting_evidence": self.supporting_evidence,
            "contradictory_evidence": self.contradictory_evidence,
            "status": self.status.value,
            "predictions": [p.to_dict() for p in self.predictions],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Hypothesis":
        return cls(
            hypothesis_id=d["hypothesis_id"],
            statement=d["statement"],
            independent_variable=d["independent_variable"],
            dependent_variable=d["dependent_variable"],
            predicted_direction=PredictedDirection(d["predicted_direction"]),
            expected_relationship=d.get("expected_relationship", ""),
            confidence_before=float(d.get("confidence_before", 0.5)),
            confidence_after=float(d.get("confidence_after", 0.5)),
            experiments=d.get("experiments", []),
            supporting_evidence=d.get("supporting_evidence", []),
            contradictory_evidence=d.get("contradictory_evidence", []),
            status=HypothesisStatus(d.get("status", "proposed")),
            predictions=[Prediction.from_dict(p) for p in d.get("predictions", [])],
            created_at=d.get("created_at", _now_iso()),
        )


def evaluate_prediction(
    prediction: Prediction,
    baseline_value: float,
    treatment_value: float,
    correlation: Optional[float] = None,
) -> PredictionEvaluation:
    """Evaluate a pre-experiment prediction against observed results."""
    delta = treatment_value - baseline_value

    if abs(delta) < 1e-4:
        obs_dir = PredictedDirection.NO_CHANGE
    elif delta > 0:
        obs_dir = PredictedDirection.INCREASE
    else:
        obs_dir = PredictedDirection.DECREASE

    # Check match
    is_correct = bool(obs_dir == prediction.predicted_direction)

    # Determine evidence strength
    mag = abs(delta)
    if mag > 0.3 or (correlation is not None and abs(correlation) > 0.8):
        strength = "strong"
    elif mag > 0.1 or (correlation is not None and abs(correlation) > 0.5):
        strength = "moderate"
    elif mag > 0.02:
        strength = "weak"
    else:
        strength = "inconclusive"

    if is_correct:
        verdict = (
            f"Observation supported the prediction: {prediction.dependent_variable} "
            f"showed an {obs_dir.value} (delta={delta:+.4f}) as expected."
        )
    else:
        verdict = (
            f"Observation conflicted with prediction: expected {prediction.predicted_direction.value}, "
            f"but observed {obs_dir.value} (delta={delta:+.4f})."
        )

    return PredictionEvaluation(
        prediction=prediction,
        observed_direction=obs_dir,
        prediction_correct=is_correct,
        observed_delta=delta,
        observed_correlation=correlation,
        evidence_strength=strength,
        verdict=verdict,
    )


def update_hypothesis_with_evidence(
    hypothesis: Hypothesis,
    experiment_id: str,
    evaluation: PredictionEvaluation,
) -> Hypothesis:
    """Update a hypothesis record with findings from an experiment run."""
    if experiment_id not in hypothesis.experiments:
        hypothesis.experiments.append(experiment_id)

    if evaluation.prediction_correct:
        evidence_note = (
            f"Exp {experiment_id}: supported by current evidence — {evaluation.verdict} "
            f"(evidence strength: {evaluation.evidence_strength})"
        )
        hypothesis.supporting_evidence.append(evidence_note)
        # Bayesian-style confidence update
        boost = 0.2 if evaluation.evidence_strength == "strong" else 0.1
        hypothesis.confidence_after = min(0.95, hypothesis.confidence_after + boost)
        hypothesis.status = HypothesisStatus.SUPPORTED
    else:
        evidence_note = (
            f"Exp {experiment_id}: hypothesis weakened by observation — {evaluation.verdict} "
            f"(evidence strength: {evaluation.evidence_strength})"
        )
        hypothesis.contradictory_evidence.append(evidence_note)
        penalty = 0.25 if evaluation.evidence_strength == "strong" else 0.12
        hypothesis.confidence_after = max(0.05, hypothesis.confidence_after - penalty)
        if len(hypothesis.contradictory_evidence) > len(hypothesis.supporting_evidence):
            hypothesis.status = HypothesisStatus.WEAKENED
        else:
            hypothesis.status = HypothesisStatus.INCONCLUSIVE

    return hypothesis


@dataclass
class CompetingHypothesesGroup:
    """Collection of competing hypotheses explaining the same target phenomenon."""

    group_id: str
    topic: str
    phenomenon: str
    hypotheses: List[Hypothesis]

    def evaluate_experiment_results(
        self,
        experiment_id: str,
        observed_deltas: Dict[str, float],
        observed_correlations: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Evaluate evidence from one experiment across all competing hypotheses."""
        results: List[Dict[str, Any]] = []

        for hyp in self.hypotheses:
            target_dep = hyp.dependent_variable
            delta = observed_deltas.get(target_dep, 0.0)
            corr = (observed_correlations or {}).get(target_dep)

            # Determine observed direction
            if abs(delta) < 1e-4:
                obs_dir = PredictedDirection.NO_CHANGE
            elif delta > 0:
                obs_dir = PredictedDirection.INCREASE
            else:
                obs_dir = PredictedDirection.DECREASE

            matches = bool(obs_dir == hyp.predicted_direction)
            evidence_label = "supported by current evidence" if matches else "weakened by evidence"

            results.append({
                "hypothesis_id": hyp.hypothesis_id,
                "statement": hyp.statement,
                "predicted_direction": hyp.predicted_direction.value,
                "observed_direction": obs_dir.value,
                "delta": delta,
                "correlation": corr,
                "supports": matches,
                "status": evidence_label,
            })

        return {
            "group_id": self.group_id,
            "experiment_id": experiment_id,
            "phenomenon": self.phenomenon,
            "evaluations": results,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "topic": self.topic,
            "phenomenon": self.phenomenon,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
        }
