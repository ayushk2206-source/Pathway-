"""Data models for Memory Detective / Hypothesis Engine (Phase 07)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from .types import (
    CausalSupportStatus,
    DiscoveryNovelty,
    HypothesisClassification,
    InvestigationStatus,
    MemoryLifecycleStage,
    QuestionIntent,
)


def _sanitize(val: Any) -> Any:
    import numpy as np

    if isinstance(val, (np.floating, float)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, dict):
        return {k: _sanitize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize(v) for v in val]
    return val


@dataclass
class MeasurableObservation:
    """A strictly observed numerical fact extracted from experimental history."""

    observation_id: str = field(default_factory=lambda: f"obs-{uuid.uuid4().hex[:8]}")
    target_memory: Optional[str] = None
    target_event: Optional[str] = None
    metric_name: str = "strength"
    initial_value: float = 0.0
    final_value: float = 0.0
    delta: float = 0.0
    relevant_events: List[str] = field(default_factory=list)
    competing_memories: List[str] = field(default_factory=list)
    cue_similarity: Optional[float] = None
    state_shift: Optional[float] = None
    summary: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def baseline_value(self) -> float:
        return self.initial_value

    @property
    def observed_value(self) -> float:
        return self.final_value

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class CandidateHypothesis:
    """A candidate explanation derived strictly from verifiable computational mechanisms."""

    hypothesis_id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:8]}")
    statement: str = ""
    mechanism: str = ""
    is_primary: bool = False
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    required_test: str = ""
    status: CausalSupportStatus = CausalSupportStatus.OBSERVED
    classification: HypothesisClassification = HypothesisClassification.INCONCLUSIVE
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    counterfactual_support: float = 0.0
    alternative_explanations: List[str] = field(default_factory=list)
    data_quality: float = 1.0
    explanation_score: float = 0.0

    @property
    def competing_alternatives(self) -> List[str]:
        return self.alternative_explanations

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, CausalSupportStatus) else str(self.status)
        d["classification"] = (
            self.classification.value
            if isinstance(self.classification, HypothesisClassification)
            else str(self.classification)
        )
        return _sanitize(d)


@dataclass
class TestDesign:
    """Specification of the smallest controlled experiment to test a candidate hypothesis."""

    test_id: str = field(default_factory=lambda: f"test-{uuid.uuid4().hex[:8]}")
    hypothesis_id: str = ""
    description: str = ""
    control_description: str = ""
    intervention_description: str = ""
    intervention_type: str = "remove_event"
    target_timestep: Optional[int] = None
    target_event_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    target_memory: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TestDesign":
        return cls(
            test_id=d.get("test_id", f"test-{uuid.uuid4().hex[:8]}"),
            hypothesis_id=d.get("hypothesis_id", ""),
            description=d.get("description", ""),
            control_description=d.get("control_description", ""),
            intervention_description=d.get("intervention_description", ""),
            intervention_type=d.get("intervention_type", "remove_event"),
            target_timestep=d.get("target_timestep"),
            target_event_id=d.get("target_event_id"),
            parameters=dict(d.get("parameters", {})),
            target_memory=d.get("target_memory"),
        )


@dataclass
class TestResult:
    """Quantitative comparison between Control and Intervention trajectories."""

    test_id: str
    hypothesis_id: str
    control_trajectory: List[float] = field(default_factory=list)
    intervention_trajectory: List[float] = field(default_factory=list)
    first_divergence_step: Optional[int] = None
    divergence_magnitude: float = 0.0
    control_outcome_strength: float = 0.0
    intervention_outcome_strength: float = 0.0
    recovery_delta: float = 0.0
    causal_support: CausalSupportStatus = CausalSupportStatus.UNSUPPORTED
    evidence_summary: str = ""
    affected_memories: List[str] = field(default_factory=list)
    divergence_classification: str = "localized"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["causal_support"] = (
            self.causal_support.value
            if isinstance(self.causal_support, CausalSupportStatus)
            else str(self.causal_support)
        )
        return _sanitize(d)


@dataclass
class EvidenceChain:
    """Step-by-step causal derivation linking written events to measured outcomes."""

    hypothesis_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    verdict: str = "UNSUPPORTED"

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class MemoryBirthRecord:
    """Forensic creation details for a newly formed memory item."""

    memory_id: str
    concept_label: str
    first_appearance_step: int
    first_event_id: str
    initial_strength: float
    initial_state_norm: float
    early_associations: List[str] = field(default_factory=list)
    early_competitors: List[str] = field(default_factory=list)
    trajectory_preview: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class MemoryDeathRecord:
    """Forensic degradation record when a memory representation falls below readout threshold."""

    memory_id: str
    concept_label: str
    last_strong_step: int
    last_strong_strength: float
    effective_loss_step: int
    final_strength: float
    decline_events: List[str] = field(default_factory=list)
    dominant_contributor: str = ""
    counterfactual_survival_possible: bool = False
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class MemoryAutopsy:
    """Signature comprehensive diagnostic answering how a memory formed, competed, and died or survived."""

    memory_id: str
    concept_label: str
    formation: Dict[str, Any] = field(default_factory=dict)
    reinforcement: Dict[str, Any] = field(default_factory=dict)
    competition: Dict[str, Any] = field(default_factory=dict)
    weakening_inflection: Optional[Dict[str, Any]] = None
    survival_factors: List[str] = field(default_factory=list)
    counterfactual_removal_impact: Dict[str, Any] = field(default_factory=dict)
    failure_profile: Optional[Dict[str, Any]] = None
    survival_profile: Optional[Dict[str, Any]] = None
    supporting_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class SensitivityRecord:
    """Quantified sensitivity of a target memory to a specific event or perturbation."""

    memory_id: str
    perturbation: str = ""
    effect_size: float = 0.0
    direction: str = "neutral"  # positive, negative, neutral
    downstream_affected_count: int = 0
    interfering_event_id: Optional[str] = None
    isolated_cause: bool = False
    counterfactual_tested: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class RobustnessEvaluation:
    """Multi-trial robustness classification across parameter variations."""

    memory_id: str
    classification: str  # stable, sensitive, unstable, inconclusive
    variations_tested: int
    variance: float
    persistence_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class MinimumIntervention:
    """The smallest parameter or sequence modification required to alter an outcome."""

    target_memory: str
    target_outcome: str
    smallest_intervention_type: str
    parameter_threshold: float
    effect_size: float
    intervention_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class DiscoveryObservation:
    """Interesting measurable phenomenon surfaced automatically from an experiment."""

    discovery_id: str = field(default_factory=lambda: f"disc-{uuid.uuid4().hex[:8]}")
    experiment_id: str = ""
    title: str = ""
    description: str = ""
    category: str = "persistence"  # persistence, interference, state_shift, recovery, anomaly
    target_memory: Optional[str] = None
    relevant_events: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    novelty: DiscoveryNovelty = DiscoveryNovelty.KNOWN_PATTERN
    seed_question: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["novelty"] = self.novelty.value if isinstance(self.novelty, DiscoveryNovelty) else str(self.novelty)
        return _sanitize(d)


@dataclass
class NotebookEntry:
    """Researcher notebook note with bi-directional links to entities."""

    entry_id: str = field(default_factory=lambda: f"nb-{uuid.uuid4().hex[:8]}")
    experiment_id: str = ""
    investigation_id: Optional[str] = None
    timestamp: str = ""
    title: str = ""
    notes: str = ""
    content: str = ""
    author: str = "Researcher"
    tags: List[str] = field(default_factory=list)
    linked_entities: Dict[str, Any] = field(default_factory=dict)
    conclusion: str = ""

    def __post_init__(self) -> None:
        if self.content and not self.notes:
            self.notes = self.content
        elif self.notes and not self.content:
            self.content = self.notes

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize(asdict(self))


@dataclass
class Investigation:
    """Complete root investigation object."""

    investigation_id: str = field(default_factory=lambda: f"inv-{uuid.uuid4().hex[:8]}")
    experiment_id: str = ""
    question: str = ""
    intent: QuestionIntent = QuestionIntent.INTERFERENCE
    target_memory: Optional[str] = None
    target_event: Optional[str] = None
    observations: List[MeasurableObservation] = field(default_factory=list)
    candidate_hypotheses: List[CandidateHypothesis] = field(default_factory=list)
    tests: List[TestDesign] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    evidence_chain: List[EvidenceChain] = field(default_factory=list)
    status: InvestigationStatus = InvestigationStatus.OBSERVING
    scorecard: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "investigation_id": self.investigation_id,
            "experiment_id": self.experiment_id,
            "question": self.question,
            "intent": self.intent.value if isinstance(self.intent, QuestionIntent) else str(self.intent),
            "target_memory": self.target_memory,
            "target_event": self.target_event,
            "observations": [o.to_dict() for o in self.observations],
            "candidate_hypotheses": [h.to_dict() for h in self.candidate_hypotheses],
            "tests": [t.to_dict() for t in self.tests],
            "results": [r.to_dict() for r in self.results],
            "evidence_chain": [e.to_dict() for e in self.evidence_chain],
            "status": self.status.value if isinstance(self.status, InvestigationStatus) else str(self.status),
            "scorecard": self.scorecard,
            "created_at": self.created_at,
        }
        return _sanitize(d)
