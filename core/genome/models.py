"""Data models for Phase 08: Memory Genome + Cascade Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .types import (
    CascadeEffectType,
    DoseResponsePattern,
    FragilityClassification,
    GenomeInterventionType,
    GenomeSection,
    OrderSensitivity,
    RecoveryStatus,
)


def _clean_numpy(val: Any) -> Any:
    """Recursively convert numpy types to standard Python types."""
    if hasattr(val, "item"):
        return val.item()
    if hasattr(val, "tolist"):
        return val.tolist()
    if isinstance(val, dict):
        return {k: _clean_numpy(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_clean_numpy(item) for item in val]
    return val


@dataclass
class AssociationEntry:
    target_memory: str
    concept_label: str
    similarity: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssociationEntry:
        return cls(
            target_memory=str(data.get("target_memory", "")),
            concept_label=str(data.get("concept_label", "")),
            similarity=float(data.get("similarity", 0.0)),
        )


@dataclass
class CompetitorEntry:
    target_memory: str
    concept_label: str
    similarity: float
    overlap_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompetitorEntry:
        return cls(
            target_memory=str(data.get("target_memory", "")),
            concept_label=str(data.get("concept_label", "")),
            similarity=float(data.get("similarity", 0.0)),
            overlap_score=float(data.get("overlap_score", 0.0)),
        )


@dataclass
class ReinforcementRecord:
    step: int
    event_id: str
    strength_before: float
    strength_after: float
    delta: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReinforcementRecord:
        return cls(
            step=int(data.get("step", 0)),
            event_id=str(data.get("event_id", "")),
            strength_before=float(data.get("strength_before", 0.0)),
            strength_after=float(data.get("strength_after", 0.0)),
            delta=float(data.get("delta", 0.0)),
        )


@dataclass
class RetrievalRecord:
    step: int
    event_id: str
    fidelity: float
    success: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalRecord:
        return cls(
            step=int(data.get("step", 0)),
            event_id=str(data.get("event_id", "")),
            fidelity=float(data.get("fidelity", 0.0)),
            success=bool(data.get("success", False)),
        )


@dataclass
class GenomeDNAStrip:
    origin_score: float
    reinforcement_score: float
    association_score: float
    competition_score: float
    retrieval_score: float
    drift_score: float
    stability_score: float
    influence_score: float
    evidence: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenomeDNAStrip:
        return cls(
            origin_score=float(data.get("origin_score", 0.0)),
            reinforcement_score=float(data.get("reinforcement_score", 0.0)),
            association_score=float(data.get("association_score", 0.0)),
            competition_score=float(data.get("competition_score", 0.0)),
            retrieval_score=float(data.get("retrieval_score", 0.0)),
            drift_score=float(data.get("drift_score", 0.0)),
            stability_score=float(data.get("stability_score", 0.0)),
            influence_score=float(data.get("influence_score", 0.0)),
            evidence=data.get("evidence", {}),
        )


@dataclass
class MemoryGenome:
    memory_id: str
    concept_label: str
    origin_event: str
    origin_step: int
    formation_events: list[str]
    associations: list[AssociationEntry]
    competitors: list[CompetitorEntry]
    reinforcement_history: list[ReinforcementRecord]
    retrieval_history: list[RetrievalRecord]
    state_dependencies: list[str]
    downstream_influence: list[str]
    trajectory: list[float]
    current_strength: float
    stability: float
    sensitivity: float
    influence_score: float
    dna_strip: GenomeDNAStrip
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _clean_numpy({
            "memory_id": self.memory_id,
            "concept_label": self.concept_label,
            "origin_event": self.origin_event,
            "origin_step": self.origin_step,
            "formation_events": self.formation_events,
            "associations": [a.to_dict() for a in self.associations],
            "competitors": [c.to_dict() for c in self.competitors],
            "reinforcement_history": [r.to_dict() for r in self.reinforcement_history],
            "retrieval_history": [rt.to_dict() for rt in self.retrieval_history],
            "state_dependencies": self.state_dependencies,
            "downstream_influence": self.downstream_influence,
            "trajectory": self.trajectory,
            "current_strength": self.current_strength,
            "stability": self.stability,
            "sensitivity": self.sensitivity,
            "influence_score": self.influence_score,
            "dna_strip": self.dna_strip.to_dict(),
            "provenance": self.provenance,
        })

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryGenome:
        return cls(
            memory_id=str(data.get("memory_id", "")),
            concept_label=str(data.get("concept_label", "")),
            origin_event=str(data.get("origin_event", "")),
            origin_step=int(data.get("origin_step", 0)),
            formation_events=list(data.get("formation_events", [])),
            associations=[AssociationEntry.from_dict(a) for a in data.get("associations", [])],
            competitors=[CompetitorEntry.from_dict(c) for c in data.get("competitors", [])],
            reinforcement_history=[
                ReinforcementRecord.from_dict(r) for r in data.get("reinforcement_history", [])
            ],
            retrieval_history=[
                RetrievalRecord.from_dict(rt) for rt in data.get("retrieval_history", [])
            ],
            state_dependencies=list(data.get("state_dependencies", [])),
            downstream_influence=list(data.get("downstream_influence", [])),
            trajectory=list(data.get("trajectory", [])),
            current_strength=float(data.get("current_strength", 0.0)),
            stability=float(data.get("stability", 0.0)),
            sensitivity=float(data.get("sensitivity", 0.0)),
            influence_score=float(data.get("influence_score", 0.0)),
            dna_strip=GenomeDNAStrip.from_dict(data.get("dna_strip", {})),
            provenance=data.get("provenance", {}),
        )


@dataclass
class MemoryLineageNode:
    id: str
    label: str
    node_type: str
    step: int
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryLineageEdge:
    source: str
    target: str
    label: str
    operation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryLineageGraph:
    memory_id: str
    nodes: list[MemoryLineageNode]
    edges: list[MemoryLineageEdge]

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class CascadeNode:
    memory_id: str
    concept_label: str
    depth: int
    effect_type: CascadeEffectType
    strength_before: float
    strength_after: float
    delta: float
    relative_delta: float
    first_divergence_step: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["effect_type"] = self.effect_type.value if hasattr(self.effect_type, "value") else str(self.effect_type)
        return d


@dataclass
class CascadeEdge:
    source: str
    target: str
    strength: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CascadeMap:
    target_memory: str
    intervention: str
    total_cascade_depth: int
    total_cascade_impact: float
    first_divergence_step: int | None
    nodes: list[CascadeNode]
    edges: list[CascadeEdge]
    divergence_order: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_memory": self.target_memory,
            "intervention": self.intervention,
            "total_cascade_depth": self.total_cascade_depth,
            "total_cascade_impact": self.total_cascade_impact,
            "first_divergence_step": self.first_divergence_step,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "divergence_order": self.divergence_order,
        }


@dataclass
class InfluenceScoreBreakdown:
    direct_effect: float
    downstream_effect: float
    persistence: float
    depth_score: float
    total_influence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryCentralityRecord:
    memory_id: str
    concept_label: str
    degree: int
    weighted_degree: float
    downstream_reach: int
    eigenvector_centrality: float
    influence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriticalMemoryRank:
    memory_id: str
    concept_label: str
    impact_level: str  # HIGH, MEDIUM, LOW
    total_cascade_impact: float
    affected_count: int
    max_depth: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FragilityReport:
    target_memory: str
    classification: FragilityClassification
    impact_ratio: float
    mean_system_impact: float
    measured_impact: float
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["classification"] = self.classification.value if hasattr(self.classification, "value") else str(self.classification)
        return d


@dataclass
class RedundancyRecord:
    target_memory: str
    redundancy_paths: list[dict[str, Any]]
    compensation_score: float
    has_viable_backup: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DoseResponsePoint:
    dose: float
    downstream_effect: float
    final_state_distance: float
    target_strength: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DoseResponseEvaluation:
    target_memory: str
    points: list[DoseResponsePoint]
    pattern: DoseResponsePattern
    threshold_dose: float | None
    inflection_detected: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pattern"] = self.pattern.value if hasattr(self.pattern, "value") else str(self.pattern)
        return d


@dataclass
class RecoveryEvaluation:
    target_memory: str
    status: RecoveryStatus
    baseline_strength: float
    during_strength: float
    restored_strength: float
    recovery_delta: float
    state_divergence_l2: float

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if hasattr(self.status, "value") else str(self.status)
        return d


@dataclass
class PathDependenceEvaluation:
    sequence_a: list[str]
    sequence_b: list[str]
    final_distance_l2: float
    order_sensitivity: OrderSensitivity
    diverging_memories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["order_sensitivity"] = self.order_sensitivity.value if hasattr(self.order_sensitivity, "value") else str(self.order_sensitivity)
        return d


@dataclass
class SandboxBranch:
    branch_id: str
    parent_id: str
    experiment_id: str
    intervention: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyMatrix:
    memories: list[str]
    matrix: list[list[float]]
    metric: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenomeReport:
    memory_id: str
    summary: str
    sections: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CascadeReport:
    target_memory: str
    intervention: str
    first_divergence: int | None
    cascade_depth: int
    total_impact: float
    affected_nodes: list[str]
    unchanged_nodes: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
