"""Data models for Phase 10: Causal Memory Lab."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .types import (
    CausalEdgeStatus,
    CausalInterventionType,
    ClaimStatus,
    InteractionClassification,
    QueueStatus,
    WindowSensitivity,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(val: Any) -> Any:
    if hasattr(val, "item"):
        return val.item()
    if hasattr(val, "tolist"):
        return val.tolist()
    if isinstance(val, dict):
        return {k: _clean(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_clean(v) for v in val]
    return val


def _enum_val(v: Any) -> Any:
    return v.value if hasattr(v, "value") else v


# ---------------------------------------------------------------------------
# Section 2/16 -- Scenario Builder / CausalScenarioCompiler
# ---------------------------------------------------------------------------


@dataclass
class CausalScenario:
    """A validated, executable specification for a counterfactual run."""

    scenario_id: str = field(default_factory=lambda: f"scn-{uuid.uuid4().hex[:8]}")
    experiment_id: str = ""
    target_memory: str = ""
    intervention: CausalInterventionType = CausalInterventionType.REMOVE
    timing: Optional[int] = None
    strength: float = 1.0
    duration: Optional[int] = None
    label: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["intervention"] = _enum_val(self.intervention)
        return _clean(d)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalScenario":
        itv = d.get("intervention", CausalInterventionType.REMOVE)
        if isinstance(itv, str):
            itv = CausalInterventionType(itv)
        return cls(
            scenario_id=d.get("scenario_id", f"scn-{uuid.uuid4().hex[:8]}"),
            experiment_id=d.get("experiment_id", ""),
            target_memory=d.get("target_memory", ""),
            intervention=itv,
            timing=d.get("timing"),
            strength=float(d.get("strength", 1.0)),
            duration=d.get("duration"),
            label=d.get("label", ""),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class CausalCostEstimate:
    runs_required: int
    estimated_compute_units: float
    estimated_memory_mb: float
    estimated_time_seconds: float
    within_budget: bool
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class ScenarioValidation:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cost_estimate: Optional[CausalCostEstimate] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "cost_estimate": self.cost_estimate.to_dict() if self.cost_estimate else None,
        }
        return _clean(d)


# ---------------------------------------------------------------------------
# Section 3-6 -- Temporal intervention / critical window / first divergence
# ---------------------------------------------------------------------------


@dataclass
class TimingSensitivityPoint:
    candidate_timestep: int
    divergence_magnitude: float
    phase: WindowSensitivity

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phase"] = _enum_val(self.phase)
        return _clean(d)


@dataclass
class CriticalWindow:
    start_timestep: int
    end_timestep: int
    peak_timestep: int
    peak_magnitude: float
    baseline_magnitude: float
    sensitivity_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class TemporalSensitivityResult:
    experiment_id: str
    target_memory: str
    points: List[TimingSensitivityPoint]
    critical_window: Optional[CriticalWindow]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "target_memory": self.target_memory,
            "points": [p.to_dict() for p in self.points],
            "critical_window": self.critical_window.to_dict() if self.critical_window else None,
            "explanation": self.explanation,
        }


@dataclass
class DivergenceTraceEvent:
    step: int
    label: str
    memory_id: Optional[str] = None
    delta: float = 0.0
    is_first_divergence: bool = False
    is_cascade_point: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class FirstDivergenceResult:
    counterfactual_id: str
    first_divergence_step: Optional[int]
    cause_candidate: str
    divergence_magnitude: float
    trace: List[DivergenceTraceEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counterfactual_id": self.counterfactual_id,
            "first_divergence_step": self.first_divergence_step,
            "cause_candidate": self.cause_candidate,
            "divergence_magnitude": self.divergence_magnitude,
            "trace": [t.to_dict() for t in self.trace],
        }


# ---------------------------------------------------------------------------
# Section 8/9 -- Causal graph + edge testing
# ---------------------------------------------------------------------------


@dataclass
class CausalGraphNodeVM:
    memory_id: str
    concept_label: str
    node_type: str  # "MEMORY" | "STATE" | "OUTPUT"
    depth: int
    delta: float

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class CausalGraphEdgeVM:
    source: str
    target: str
    effect: float
    status: CausalEdgeStatus = CausalEdgeStatus.INCONCLUSIVE
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = _enum_val(self.status)
        return _clean(d)


@dataclass
class CausalGraphVM:
    experiment_id: str
    target_memory: str
    nodes: List[CausalGraphNodeVM]
    edges: List[CausalGraphEdgeVM]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "target_memory": self.target_memory,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class CausalEdgeTestResult:
    source: str
    target: str
    observed_difference: float
    counterfactual_difference: float
    status: CausalEdgeStatus
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = _enum_val(self.status)
        return _clean(d)


# ---------------------------------------------------------------------------
# Section 11-13 -- Multi-intervention / interaction effects
# ---------------------------------------------------------------------------


@dataclass
class SingleEffect:
    target_memory: str
    intervention: str
    effect: float

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class InteractionEffectResult:
    individual_effects: List[SingleEffect]
    expected_combined_effect: float
    observed_combined_effect: float
    observed_interaction: float
    classification: InteractionClassification
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "individual_effects": [e.to_dict() for e in self.individual_effects],
            "expected_combined_effect": self.expected_combined_effect,
            "observed_combined_effect": self.observed_combined_effect,
            "observed_interaction": self.observed_interaction,
            "classification": _enum_val(self.classification),
            "explanation": self.explanation,
        }


@dataclass
class MultiInterventionResult:
    experiment_id: str
    interventions: List[Dict[str, Any]]
    combined_counterfactual_id: str
    interaction: InteractionEffectResult

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "interventions": self.interventions,
            "combined_counterfactual_id": self.combined_counterfactual_id,
            "interaction": self.interaction.to_dict(),
        }


# ---------------------------------------------------------------------------
# Section 14 -- Memory swap
# ---------------------------------------------------------------------------


@dataclass
class MemorySwapResult:
    experiment_id: str
    memory_a: str
    memory_b: str
    swapped_counterfactual_id: str
    state_distance_l2: float
    output_changed: bool
    identity_dependent: bool
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


# ---------------------------------------------------------------------------
# Section 19-21 -- Causality matrix / temporal causality map
# ---------------------------------------------------------------------------


@dataclass
class CausalityMatrix:
    experiment_id: str
    memories: List[str]
    labels: List[str]
    matrix: List[List[Optional[float]]]
    metric: str = "measured_removal_effect"

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class TemporalCausalityBin:
    window_start: int
    window_end: int
    effect: float

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class TemporalCausalityMap:
    experiment_id: str
    target_memory: str
    bins: List[TemporalCausalityBin]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "target_memory": self.target_memory,
            "bins": [b.to_dict() for b in self.bins],
        }


# ---------------------------------------------------------------------------
# Section 22, 26 -- Confidence / fragility (thin VM wrappers, real data only)
# ---------------------------------------------------------------------------


@dataclass
class EvidenceQuality:
    interventions: int
    replications: int
    effect_consistency: str
    alternatives_tested: int
    status: ClaimStatus

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = _enum_val(self.status)
        return _clean(d)


# ---------------------------------------------------------------------------
# Section 27/28 -- Recovery experiment / curve
# ---------------------------------------------------------------------------


@dataclass
class RecoveryCurvePoint:
    phase: str  # PRE-DELETE | POST-DELETE | RECOVERY | FINAL
    strength: float

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class RecoveryCurveResult:
    experiment_id: str
    target_memory: str
    points: List[RecoveryCurvePoint]
    status: str
    recovery_delta: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "target_memory": self.target_memory,
            "points": [p.to_dict() for p in self.points],
            "status": self.status,
            "recovery_delta": self.recovery_delta,
        }


# ---------------------------------------------------------------------------
# Section 17/18 -- Causal experiment queue
# ---------------------------------------------------------------------------


@dataclass
class CausalQueueItem:
    queue_id: str = field(default_factory=lambda: f"cq-{uuid.uuid4().hex[:8]}")
    scenario: Dict[str, Any] = field(default_factory=dict)
    estimated_cost: Dict[str, Any] = field(default_factory=dict)
    status: QueueStatus = QueueStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = _enum_val(self.status)
        return _clean(d)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalQueueItem":
        st = d.get("status", QueueStatus.QUEUED)
        if isinstance(st, str):
            st = QueueStatus(st)
        return cls(
            queue_id=d.get("queue_id", f"cq-{uuid.uuid4().hex[:8]}"),
            scenario=dict(d.get("scenario", {})),
            estimated_cost=dict(d.get("estimated_cost", {})),
            status=st,
            result=d.get("result"),
            error=d.get("error"),
            created_at=d.get("created_at", _now_iso()),
            updated_at=d.get("updated_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Section 37/38 -- Causality Ledger + claim versioning
# ---------------------------------------------------------------------------


@dataclass
class CausalClaimVersion:
    version: int
    statement: str
    status: ClaimStatus
    evidence_experiment_ids: List[str]
    interventions: int
    replications: int
    effect_consistency: str
    changed_because: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = _enum_val(self.status)
        return _clean(d)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalClaimVersion":
        st = d.get("status", ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT)
        if isinstance(st, str):
            st = ClaimStatus(st)
        return cls(
            version=int(d.get("version", 1)),
            statement=d.get("statement", ""),
            status=st,
            evidence_experiment_ids=list(d.get("evidence_experiment_ids", [])),
            interventions=int(d.get("interventions", 0)),
            replications=int(d.get("replications", 0)),
            effect_consistency=d.get("effect_consistency", "unknown"),
            changed_because=d.get("changed_because", ""),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class CausalClaim:
    claim_id: str
    source_memory: str
    target_memory: str
    versions: List[CausalClaimVersion] = field(default_factory=list)

    @property
    def current(self) -> Optional[CausalClaimVersion]:
        return self.versions[-1] if self.versions else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "source_memory": self.source_memory,
            "target_memory": self.target_memory,
            "current_version": self.current.version if self.current else None,
            "versions": [v.to_dict() for v in self.versions],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalClaim":
        return cls(
            claim_id=d["claim_id"],
            source_memory=d.get("source_memory", ""),
            target_memory=d.get("target_memory", ""),
            versions=[CausalClaimVersion.from_dict(v) for v in d.get("versions", [])],
        )


# ---------------------------------------------------------------------------
# Section 39 -- Contradiction engine
# ---------------------------------------------------------------------------


@dataclass
class CausalityConflict:
    conflict_id: str = field(default_factory=lambda: f"conf-{uuid.uuid4().hex[:8]}")
    claim_id: str = ""
    source_memory: str = ""
    target_memory: str = ""
    experiment_a: str = ""
    experiment_b: str = ""
    effect_a: float = 0.0
    effect_b: float = 0.0
    comparison: Dict[str, Any] = field(default_factory=dict)
    suggested_controlled_test: str = ""
    detected_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalityConflict":
        return cls(
            conflict_id=d.get("conflict_id", f"conf-{uuid.uuid4().hex[:8]}"),
            claim_id=d.get("claim_id", ""),
            source_memory=d.get("source_memory", ""),
            target_memory=d.get("target_memory", ""),
            experiment_a=d.get("experiment_a", ""),
            experiment_b=d.get("experiment_b", ""),
            effect_a=float(d.get("effect_a", 0.0)),
            effect_b=float(d.get("effect_b", 0.0)),
            comparison=dict(d.get("comparison", {})),
            suggested_controlled_test=d.get("suggested_controlled_test", ""),
            detected_at=d.get("detected_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Section 33 -- Causal investigation report
# ---------------------------------------------------------------------------


@dataclass
class CausalReport:
    report_id: str = field(default_factory=lambda: f"crep-{uuid.uuid4().hex[:8]}")
    experiment_id: str = ""
    question: str = ""
    scenario: Dict[str, Any] = field(default_factory=dict)
    baseline: Dict[str, Any] = field(default_factory=dict)
    intervention: Dict[str, Any] = field(default_factory=dict)
    temporal_window: Optional[Dict[str, Any]] = None
    first_divergence: Optional[Dict[str, Any]] = None
    cascade: Dict[str, Any] = field(default_factory=dict)
    effect: Dict[str, Any] = field(default_factory=dict)
    alternative_paths: List[Dict[str, Any]] = field(default_factory=list)
    replication: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    conclusion: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))
