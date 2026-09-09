"""Pydantic schemas for Phase 08: Memory Genome + Cascade Engine."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CascadeRunRequest(BaseModel):
    experiment_id: str = Field(..., description="ID of the experiment")
    target_memory: str = Field(..., description="Target memory ID or concept label")
    intervention: str = Field("remove", description="Intervention type: remove, weaken, strengthen")
    dose: float = Field(1.0, ge=0.0, le=2.0, description="Dose factor for weaken/strengthen interventions")


class DoseResponseRequest(BaseModel):
    experiment_id: str = Field(..., description="ID of the experiment")
    target_memory: str = Field(..., description="Target memory ID or concept label")


class RecoveryTestRequest(BaseModel):
    experiment_id: str = Field(..., description="ID of the experiment")
    target_memory: str = Field(..., description="Target memory ID or concept label")


class BranchCreateRequest(BaseModel):
    experiment_id: str = Field(..., description="Parent experiment ID")
    parent_id: str = Field("base", description="Parent branch identifier")
    intervention: Dict[str, Any] = Field(..., description="Intervention dictionary")


class BranchCompareRequest(BaseModel):
    experiment_id: str = Field(..., description="ID of the base experiment")
    intervention_a: Dict[str, Any] = Field(..., description="Intervention specification for branch A")
    intervention_b: Dict[str, Any] = Field(..., description="Intervention specification for branch B")


class MutationRequest(BaseModel):
    experiment_id: str = Field(..., description="ID of the experiment")
    target_memory: str = Field(..., description="Target memory ID or concept label")
    mutation_factor: float = Field(0.5, ge=0.0, le=3.0, description="Amplitude scaling factor")
