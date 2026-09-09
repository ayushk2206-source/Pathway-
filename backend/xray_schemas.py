"""Pydantic schemas for Memory X-Ray & Causal Memory Map endpoints (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CompareStatesRequest(BaseModel):
    state_a: List[float]
    state_b: List[float]


class CompareStatesResponse(BaseModel):
    l1_distance: float
    l2_distance: float
    cosine_distance: float
    normalized_difference: float
    dimension_count: int
    metrics_summary: Dict[str, float]


class XRayQueryRequest(BaseModel):
    experiment_id: str
    query: str
    params: Optional[Dict[str, Any]] = None


class SurgeryDiffRequest(BaseModel):
    original_experiment_id: str
    counterfactual_experiment_id: str


class DivergenceTraceRequest(BaseModel):
    original_experiment_id: str
    counterfactual_experiment_id: str


class ReplayActionRequest(BaseModel):
    action: str = Field(..., description="start, pause, resume, step_forward, step_backward, jump")
    step_or_event_id: Optional[Union[int, str]] = None
