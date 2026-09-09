"""Pydantic validation schemas for Phase 21: Memory Ecosystem."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SelectMemoryRequest(BaseModel):
    memory_id: str = Field(..., description="ID of memory to activate across ecosystem")
    follow: Optional[bool] = Field(None, description="Whether to enable Follow Memory mode")


class CreateCheckpointRequest(BaseModel):
    memory_id: str = Field(..., description="ID of memory to snapshot")
    label: str = Field(..., min_length=2, max_length=100, description="Scientific label for checkpoint")


class CompareStatesRequest(BaseModel):
    state_a: Dict[str, Any] = Field(..., description="First state dictionary (e.g. checkpoint weights)")
    state_b: Dict[str, Any] = Field(..., description="Second state dictionary to compare against")


class SubmitHypothesisRequest(BaseModel):
    memory_id: str = Field(..., description="Target memory ID for prediction")
    experiment_type: str = Field(..., description="Type of experiment: INTERFERENCE, SURGERY, COUNTERFACTUAL, DECAY")
    prediction_text: str = Field(..., min_length=3, description="Learner hypothesis rationale")
    predicted_outcome: str = Field(..., description="Expected outcome enum e.g. RETENTION_DROP, STABLE, COMPLETE_LOSS")
