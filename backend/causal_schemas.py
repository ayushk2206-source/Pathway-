"""Pydantic schemas for Phase 10: Causal Memory Lab endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateCausalScenarioRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    target_memory: str = Field(..., description="Memory ID or concept query")
    intervention: str = Field("REMOVE", description="Intervention type (REMOVE, ADD, STRENGTHEN, etc.)")
    timing: Optional[int] = Field(None, description="Event index or timestep")
    strength: float = Field(1.0, description="Intervention dose or strength multiplier")
    duration: Optional[int] = Field(5, description="Duration in steps where applicable")
    label: Optional[str] = Field("", description="Human-readable scenario description")


class ValidateCausalScenarioRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    target_memory: Optional[str] = Field("", description="Memory ID or concept query")
    intervention: str = Field("REMOVE", description="Intervention type")
    timing: Optional[int] = Field(None, description="Event index or timestep")
    strength: float = Field(1.0, description="Intervention strength")
    duration: Optional[int] = Field(5, description="Duration in steps")
    label: Optional[str] = Field("", description="Human-readable label")


class EstimateCostRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    runs_required: int = Field(1, ge=1, le=64, description="Number of replays required")


class RunCausalCounterfactualRequest(BaseModel):
    experiment_id: str = Field(..., description="Base experiment ID")
    target_memory: str = Field(..., description="Target memory ID or query")
    intervention: str = Field("REMOVE", description="Intervention verb")
    timing: Optional[int] = Field(None, description="Timing timestep")
    strength: float = Field(1.0, description="Strength magnitude")
    duration: Optional[int] = Field(5, description="Intervention duration")
    label: Optional[str] = Field("", description="Scenario label")


class TestCausalEdgeRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    source_memory: str = Field(..., description="Source memory ID or query")
    target_memory: str = Field(..., description="Target memory ID or query")


class SingleInterventionSpec(BaseModel):
    target_memory: str = Field(..., description="Memory ID or query")
    intervention_type: str = Field("remove", description="remove, modify, etc.")
    dose: float = Field(1.0, description="Dose or multiplier")


class MultiInterventionRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    interventions: List[SingleInterventionSpec] = Field(..., min_length=1, description="List of interventions to combine")


class MemorySwapRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    memory_a: str = Field(..., description="First memory ID or query")
    memory_b: str = Field(..., description="Second memory ID or query")


class RecoveryExperimentRequest(BaseModel):
    experiment_id: str = Field(..., description="Target experiment ID")
    target_memory: str = Field(..., description="Target memory ID or query")


class RegisterClaimRequest(BaseModel):
    source_memory: str = Field(..., description="Source memory ID")
    target_memory: str = Field(..., description="Target memory ID")
    statement: str = Field(..., description="Causal claim statement")
    status: Optional[str] = Field("SUPPORTED WITHIN EXPERIMENT", description="ClaimStatus")
    evidence_experiment_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of experiments providing evidence")
    interventions: Optional[int] = Field(1, description="Number of distinct interventions tested")
    replications: Optional[int] = Field(1, description="Number of replications")
    effect_consistency: Optional[str] = Field("HIGH", description="Effect consistency classification")


class UpdateClaimRequest(BaseModel):
    statement: str = Field(..., description="Updated claim statement")
    status: str = Field(..., description="Updated ClaimStatus")
    evidence_experiment_ids: List[str] = Field(..., description="All supporting experiment IDs")
    interventions: int = Field(..., description="Total interventions tested")
    replications: int = Field(..., description="Total replications")
    effect_consistency: str = Field("HIGH", description="Consistency assessment")
    changed_because: str = Field(..., description="Reason for versioning")


class CreateReportRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    question: str = Field(..., description="Research question investigated")
    scenario: Dict[str, Any] = Field(default_factory=dict, description="Scenario details")
    baseline: Dict[str, Any] = Field(default_factory=dict, description="Baseline experiment summary")
    intervention: Dict[str, Any] = Field(default_factory=dict, description="Intervention specifications")
    temporal_window: Optional[Dict[str, Any]] = Field(None, description="Critical window metadata")
    first_divergence: Optional[Dict[str, Any]] = Field(None, description="First divergence metadata")
    cascade: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Cascade details")
    effect: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Measured effect details")
    alternative_paths: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Alternative pathways")
    replication: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Replication results")
    limitations: Optional[List[str]] = Field(None, description="Epistemic limitations")
    conclusion: Optional[str] = Field(None, description="Concluding summary")


class QueueControlRequest(BaseModel):
    action: str = Field(..., description="pause, resume, stop, clear")


class DiscoveryHandoffRequest(BaseModel):
    experiment_id: str = Field(..., description="Source experiment ID")
    title: str = Field(..., description="Observation title")
    description: str = Field(..., description="Detailed description")
    pattern_type: str = Field("CASCADE_AMPLIFICATION", description="Discovery pattern category")
    memory_id: Optional[str] = Field(None, description="Primary memory involved")
    evidence: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Evidence payload")
