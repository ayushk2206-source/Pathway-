"""Pydantic request schemas for Phase 19: Adaptive Memory Observatory."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StreamEventSchema(BaseModel):
    timestep: int = Field(..., ge=0)
    environment_id: str = Field(..., min_length=1)
    event_type: str = Field(..., pattern="^(WRITE|DECAY|PROBE|ENV_SHIFT|INTERVENTION)$")
    label: str = Field(..., min_length=1)
    concept: Optional[str] = None
    value: Optional[str] = None
    importance: float = Field(default=1.0, ge=0.0, le=5.0)
    strength: float = Field(default=1.0, ge=0.0, le=5.0)
    n_steps: int = Field(default=1, ge=1, le=50)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunStreamRequest(BaseModel):
    events: Optional[List[StreamEventSchema]] = None
    preset_id: Optional[str] = None  # "env_shift" | "collision_stream" | "decay_recovery"
    dimension: int = Field(default=16, ge=4, le=64)
    decay: float = Field(default=0.04, ge=0.0, le=0.5)
    update_strength: float = Field(default=1.0, ge=0.1, le=5.0)
    seed: int = Field(default=42, ge=0)
    name: str = Field(default="Adaptive Stream Session", min_length=1)
    tracked_probes: Optional[List[List[str]]] = None


class StepStreamRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    event: StreamEventSchema


class InterventionBranchRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    step: int = Field(..., ge=0)
    operation: str = Field(..., pattern="^(silence|weaken|strengthen|restore)$")
    synapse_ids: List[str] = Field(..., min_length=1)
    factor: float = Field(default=0.0, ge=0.0, le=10.0)


class CounterfactualBranchRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    step: int = Field(..., ge=0)
    label: str = Field(default="Counterfactual: Invariant Shared Weights")


class CompareSessionsRequest(BaseModel):
    session_a_id: str = Field(..., min_length=1)
    session_b_id: str = Field(..., min_length=1)


class SubmitPredictionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    target_timestep: int = Field(..., ge=0)
    target_memory: str = Field(..., min_length=1)
    predicted_choice: str = Field(..., pattern="^(A|B|C|D|E)$")
    choice_label: str = Field(..., min_length=1)


class ExportDetectiveCaseRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    anomaly_step: int = Field(..., ge=1)
    target_memory: Optional[str] = None


class ChangeDetectionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    timestep_before: int = Field(..., ge=0)
    timestep_after: int = Field(..., ge=0)
