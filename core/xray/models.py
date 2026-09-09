"""Data models for Memory X-Ray & Causal Memory Map (Phase 05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from .types import (
    AnomalyType,
    DecayPattern,
    MemoryLifecycleStage,
    RelationshipType,
    StateChangeClassification,
)


def _sanitize_numeric(obj: Any) -> Any:
    """Recursively convert numpy types and non-finite floats to standard Python types."""
    if isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.ndarray, list, tuple)):
        return [_sanitize_numeric(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _sanitize_numeric(v) for k, v in obj.items()}
    return obj


@dataclass
class MemorySnapshot:
    """Reusable memory state snapshot capturing the real internal representation."""
    snapshot_id: str
    experiment_id: str
    timeline_step: int
    event_id: Optional[str]
    timestamp: str
    state_vector: List[float]
    active_units: List[int]
    inactive_units: List[int]
    sparsity: float
    memory_strength: Dict[str, float]  # memory_id -> strength in this state
    associations: Dict[str, List[str]]  # memory_id -> related memory_ids
    similarity_statistics: Dict[str, float]  # mean_sim, max_sim, min_sim, std_sim
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "snapshot_id": self.snapshot_id,
            "experiment_id": self.experiment_id,
            "timeline_step": self.timeline_step,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "state_vector": self.state_vector,
            "active_units": self.active_units,
            "inactive_units": self.inactive_units,
            "sparsity": self.sparsity,
            "memory_strength": self.memory_strength,
            "associations": self.associations,
            "similarity_statistics": self.similarity_statistics,
            "metadata": self.metadata,
        })


@dataclass
class StateTrajectory:
    """Chronological state progression across an experiment."""
    experiment_id: str
    steps: List[int]
    event_ids: List[Optional[str]]
    state_norms: List[float]
    state_vectors: List[List[float]]
    metrics: List[Dict[str, float]]
    total_steps: int

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "experiment_id": self.experiment_id,
            "steps": self.steps,
            "event_ids": self.event_ids,
            "state_norms": self.state_norms,
            "state_vectors": self.state_vectors,
            "metrics": self.metrics,
            "total_steps": self.total_steps,
        })


@dataclass
class StateComparison:
    """Mathematical comparison between two memory states."""
    l1_distance: float
    l2_distance: float
    cosine_distance: float
    normalized_difference: float
    dimension_count: int
    metrics_summary: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "l1_distance": self.l1_distance,
            "l2_distance": self.l2_distance,
            "cosine_distance": self.cosine_distance,
            "normalized_difference": self.normalized_difference,
            "dimension_count": self.dimension_count,
            "metrics_summary": self.metrics_summary,
        })


@dataclass
class StateChangeRecord:
    """Quantification of consecutive state shift."""
    step: int
    event_id: Optional[str]
    change_magnitude: float
    l2_delta: float
    cosine_delta: float
    classification: StateChangeClassification

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "step": self.step,
            "event_id": self.event_id,
            "change_magnitude": self.change_magnitude,
            "l2_delta": self.l2_delta,
            "cosine_delta": self.cosine_delta,
            "classification": self.classification.value,
        })


@dataclass
class ActivationProfile:
    """Unit activation distribution and entropy at a given step."""
    step: int
    active_units_count: int
    total_units: int
    mean_activation: float
    max_activation: float
    min_activation: float
    std_activation: float
    sparsity_ratio: float
    activation_entropy: float
    distribution_quantiles: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "step": self.step,
            "active_units_count": self.active_units_count,
            "total_units": self.total_units,
            "mean_activation": self.mean_activation,
            "max_activation": self.max_activation,
            "min_activation": self.min_activation,
            "std_activation": self.std_activation,
            "sparsity_ratio": self.sparsity_ratio,
            "activation_entropy": self.activation_entropy,
            "distribution_quantiles": self.distribution_quantiles,
        })


@dataclass
class SparsityAnalysis:
    """Detailed sparsity characteristics of the computational substrate."""
    experiment_id: str
    active_units_per_step: List[int]
    total_units: int
    sparsity_ratio_per_step: List[float]
    mean_sparsity: float
    min_sparsity: float
    max_sparsity: float
    sparsity_distribution: Dict[str, float]
    supports_non_negative: bool

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "experiment_id": self.experiment_id,
            "active_units_per_step": self.active_units_per_step,
            "total_units": self.total_units,
            "sparsity_ratio_per_step": self.sparsity_ratio_per_step,
            "mean_sparsity": self.mean_sparsity,
            "min_sparsity": self.min_sparsity,
            "max_sparsity": self.max_sparsity,
            "sparsity_distribution": self.sparsity_distribution,
            "supports_non_negative": self.supports_non_negative,
        })


@dataclass
class MemoryStrengthProfile:
    """Evolution of strength for a specific memory item across time."""
    memory_id: str
    concept_label: str
    initial_strength: float
    peak_strength: float
    final_strength: float
    timeline_strengths: List[float]
    decay_rate: Optional[float]
    reinforcement_count: int
    pattern: DecayPattern

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "memory_id": self.memory_id,
            "concept_label": self.concept_label,
            "initial_strength": self.initial_strength,
            "peak_strength": self.peak_strength,
            "final_strength": self.final_strength,
            "timeline_strengths": self.timeline_strengths,
            "decay_rate": self.decay_rate,
            "reinforcement_count": self.reinforcement_count,
            "pattern": self.pattern.value,
        })


@dataclass
class ReinforcementRecord:
    """Detected memory reinforcement event."""
    memory_id: str
    reinforcement_events: List[str]
    strength_before: float
    strength_after: float
    net_change: float
    strengthening_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "memory_id": self.memory_id,
            "reinforcement_events": self.reinforcement_events,
            "strength_before": self.strength_before,
            "strength_after": self.strength_after,
            "net_change": self.net_change,
            "strengthening_ratio": self.strengthening_ratio,
        })


@dataclass
class InterferenceRecord:
    """Empirically detected interference between competing memories."""
    memory_a: str
    memory_b: str
    overlap: float  # cosine similarity in cue/address space
    interference_score: float
    affected_steps: List[int]
    evidence_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "memory_a": self.memory_a,
            "memory_b": self.memory_b,
            "overlap": self.overlap,
            "interference_score": self.interference_score,
            "affected_steps": self.affected_steps,
            "evidence_notes": self.evidence_notes,
        })


@dataclass
class CompetitionEdge:
    """Weighted relationship between memories."""
    source: str
    target: str
    relationship: RelationshipType
    strength: float
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship.value,
            "strength": self.strength,
            "evidence": self.evidence,
        })


@dataclass
class CompetitionGraph:
    """Network of memory competition, similarity, and association."""
    nodes: List[Dict[str, Any]]
    edges: List[CompetitionEdge]
    density: float
    average_degree: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "nodes": self.nodes,
            "edges": [e.to_dict() for e in self.edges],
            "density": self.density,
            "average_degree": self.average_degree,
        })


@dataclass
class ClusterResult:
    """Group of functionally/representationally related memories."""
    cluster_id: int
    members: List[str]
    centroid: List[float]
    cohesion: float
    separation: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "cluster_id": self.cluster_id,
            "members": self.members,
            "centroid": self.centroid,
            "cohesion": self.cohesion,
            "separation": self.separation,
        })


@dataclass
class MemoryMapPoint:
    """Single point in projected 2D memory space."""
    x: float
    y: float
    memory_id: str
    label: str
    strength: float
    cluster: int
    trajectory_tail: List[List[float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "x": self.x,
            "y": self.y,
            "memory_id": self.memory_id,
            "label": self.label,
            "strength": self.strength,
            "cluster": self.cluster,
            "trajectory_tail": self.trajectory_tail,
        })


@dataclass
class MemoryMap2D:
    """2D visualization-ready projection of memory state space."""
    points: List[MemoryMapPoint]
    variance_explained: List[float]
    projection_method: str = "PCA"
    epistemic_disclaimer: str = (
        "Projected 2D coordinates are visualization aids only. Distances in "
        "projected space do not equal exact distances in original dimensional space."
    )

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "points": [p.to_dict() for p in self.points],
            "variance_explained": self.variance_explained,
            "projection_method": self.projection_method,
            "epistemic_disclaimer": self.epistemic_disclaimer,
        })


@dataclass
class MemoryTrace:
    """Complete chronological trace of a single memory across the experiment."""
    memory_id: str
    concept_label: str
    encoded_timestep: int
    stages: List[Dict[str, Any]]
    final_stage: MemoryLifecycleStage
    final_strength: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "memory_id": self.memory_id,
            "concept_label": self.concept_label,
            "encoded_timestep": self.encoded_timestep,
            "stages": self.stages,
            "final_stage": self.final_stage.value,
            "final_strength": self.final_strength,
        })


@dataclass
class EventImpact:
    """Impact of an atomic event on internal state."""
    event_id: str
    timestep: int
    change_magnitude: float
    affected_memories: List[Dict[str, Any]]
    affected_units_count: int
    state_norm_before: float
    state_norm_after: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "event_id": self.event_id,
            "timestep": self.timestep,
            "change_magnitude": self.change_magnitude,
            "affected_memories": self.affected_memories,
            "affected_units_count": self.affected_units_count,
            "state_norm_before": self.state_norm_before,
            "state_norm_after": self.state_norm_after,
        })


@dataclass
class MemoryImportance:
    """Multidimensional importance evaluation for an individual memory."""
    memory_id: str
    counterfactual_contribution: float
    state_change_magnitude: float
    retrieval_relevance: float
    reinforcement_frequency: float
    persistence: float
    connectivity: float

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "memory_id": self.memory_id,
            "counterfactual_contribution": self.counterfactual_contribution,
            "state_change_magnitude": self.state_change_magnitude,
            "retrieval_relevance": self.retrieval_relevance,
            "reinforcement_frequency": self.reinforcement_frequency,
            "persistence": self.persistence,
            "connectivity": self.connectivity,
        })


@dataclass
class MemoryExplanation:
    """Structured empirical evidence explaining a memory's state."""
    memory_id: str
    label: str
    encoded_at: int
    reinforcement_count: int
    strongest_representation_step: int
    peak_strength: float
    final_strength: float
    competing_memory_count: int
    counterfactual_contribution: float
    lifecycle_history: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "memory_id": self.memory_id,
            "label": self.label,
            "encoded_at": self.encoded_at,
            "reinforcement_count": self.reinforcement_count,
            "strongest_representation_step": self.strongest_representation_step,
            "peak_strength": self.peak_strength,
            "final_strength": self.final_strength,
            "competing_memory_count": self.competing_memory_count,
            "counterfactual_contribution": self.counterfactual_contribution,
            "lifecycle_history": self.lifecycle_history,
        })


@dataclass
class MemoryDiagnostics:
    """Computational diagnostics summarizing memory state health."""
    total_memories: int
    active_memories: int
    average_strength: float
    strongest_memory: Optional[str]
    weakest_memory: Optional[str]
    interference_pairs_count: int
    high_change_regions_count: int
    mean_sparsity: float
    cluster_count: int
    state_stability: float
    retrieval_accuracy: float
    computational_disclaimer: str = (
        "Memory Diagnostics represents computational vector state stability "
        "and simulation dynamics, not medical or biological assertions."
    )

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "total_memories": self.total_memories,
            "active_memories": self.active_memories,
            "average_strength": self.average_strength,
            "strongest_memory": self.strongest_memory,
            "weakest_memory": self.weakest_memory,
            "interference_pairs_count": self.interference_pairs_count,
            "high_change_regions_count": self.high_change_regions_count,
            "mean_sparsity": self.mean_sparsity,
            "cluster_count": self.cluster_count,
            "state_stability": self.state_stability,
            "retrieval_accuracy": self.retrieval_accuracy,
            "computational_disclaimer": self.computational_disclaimer,
        })


@dataclass
class AnomalyRecord:
    """Statistically unexpected state transition."""
    step: int
    anomaly_type: AnomalyType
    metric: str
    expected_value: float
    observed_value: float
    deviation_z_score: float
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "step": self.step,
            "anomaly_type": self.anomaly_type.value,
            "metric": self.metric,
            "expected_value": self.expected_value,
            "observed_value": self.observed_value,
            "deviation_z_score": self.deviation_z_score,
            "evidence": self.evidence,
        })


@dataclass
class XRayReport:
    """Comprehensive, evidence-based Memory X-Ray report."""
    experiment_id: str
    overview: Dict[str, Any]
    state_dynamics: Dict[str, Any]
    memory_strength: Dict[str, Any]
    interference: Dict[str, Any]
    reinforcement: Dict[str, Any]
    sparsity: Dict[str, Any]
    clusters: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    important_events: List[Dict[str, Any]]
    counterfactual_effects: Dict[str, Any]
    limitations: List[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_numeric({
            "experiment_id": self.experiment_id,
            "overview": self.overview,
            "state_dynamics": self.state_dynamics,
            "memory_strength": self.memory_strength,
            "interference": self.interference,
            "reinforcement": self.reinforcement,
            "sparsity": self.sparsity,
            "clusters": self.clusters,
            "anomalies": self.anomalies,
            "important_events": self.important_events,
            "counterfactual_effects": self.counterfactual_effects,
            "limitations": self.limitations,
            "created_at": self.created_at,
        })
