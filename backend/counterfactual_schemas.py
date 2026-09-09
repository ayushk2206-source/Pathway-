"""Pydantic schemas for Counterfactual Memory Archaeology endpoints (Phase 04)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class InterventionPayload(BaseModel):
    intervention_type: str = Field(..., description="Type of intervention (e.g. remove_event, modify_event)")
    target_timestep: Optional[int] = Field(None, description="0-indexed timestep to target")
    target_event_id: Optional[str] = Field(None, description="Event ID to target")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Intervention parameters")
    description: Optional[str] = Field(None, description="Human description of intervention")


class RunCounterfactualRequest(BaseModel):
    experiment_id: str = Field(..., description="Base experiment ID to branch from")
    intervention: InterventionPayload = Field(..., description="Intervention specification")
    strategy: Optional[str] = Field("full_replay", description="full_replay or checkpoint")
    title: Optional[str] = Field(None, description="Title for counterfactual branch")
    description: Optional[str] = Field(None, description="Description notes")


class AblationRequest(BaseModel):
    experiment_id: str = Field(..., description="Base experiment ID")
    event_id_or_timestep: Union[int, str] = Field(..., description="Target event ID or timestep")
    title: Optional[str] = Field(None, description="Optional ablation title")


class SurgeryRequest(BaseModel):
    experiment_id: str = Field(..., description="Base experiment ID")
    event_id_or_timestep: Union[int, str] = Field(..., description="Target event ID or timestep")
    modifications: Dict[str, Any] = Field(..., description="Dict of modifications (strength, importance, labels)")
    title: Optional[str] = Field(None, description="Optional surgery title")


class CompareHistoriesRequest(BaseModel):
    original_experiment_id: str = Field(..., description="Root original experiment ID")
    counterfactual_experiment_id: str = Field(..., description="Counterfactual experiment ID to compare against")


class CompareMultipleHistoriesRequest(BaseModel):
    experiment_ids: List[str] = Field(..., min_length=2, description="List of experiment IDs to compare together")


class DiffHistoriesRequest(BaseModel):
    experiment_id_a: str = Field(..., description="First experiment ID")
    experiment_id_b: str = Field(..., description="Second experiment ID")


class SearchCounterfactualsRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID to search over")
    target_metric: str = Field("interference_score", description="Target metric to optimize")
    target_direction: str = Field("decrease", description="decrease or increase")
    allowed_interventions: Optional[List[str]] = Field(None, description="List of allowed intervention types")
    max_candidates: int = Field(36, ge=1, le=144, description="Maximum candidate interventions to test")


class MinimalInterventionRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    target_metric: str = Field("interference_score", description="Target metric")
    target_improvement: float = Field(0.10, ge=0.001, description="Desired metric delta threshold")
    target_direction: str = Field("decrease", description="decrease or increase")
    allowed_interventions: Optional[List[str]] = Field(None, description="Allowed intervention types")
    max_candidates: int = Field(50, ge=1, le=144, description="Max search candidates")


class ContributionRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID to analyze")
    target_metric: Optional[str] = Field("interference_score", description="Target metric (or None if targeting object)")
    target_object: Optional[str] = Field(None, description="Specific object label to investigate recovery/recall for")
    max_candidates: int = Field(50, ge=1, le=100, description="Max history events to evaluate")


class ReproduceCounterfactualRequest(BaseModel):
    experiment_id: str = Field(..., description="Base experiment ID")
    intervention: InterventionPayload = Field(..., description="Intervention specification")
    expected_metrics: Dict[str, float] = Field(..., description="Expected metrics to verify match against")
    tolerance: float = Field(1e-9, ge=0.0, description="Numerical match tolerance")
