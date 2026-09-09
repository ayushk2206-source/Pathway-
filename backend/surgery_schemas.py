"""Pydantic schemas for Synaptic Surgery API (Phase 15)."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class LockBaselineRequest(BaseModel):
    """Request to lock the current brain state as the surgery baseline."""
    dimension: int = Field(16, ge=4, le=256, description="Brain dimension (must match live brain)")
    seed: int = Field(42, ge=0)
    decay: float = Field(0.05, ge=0.0, le=1.0)


class SynapseOperationRequest(BaseModel):
    """Request to apply a surgery operation to specific synapses."""
    synapse_ids: List[str] = Field(..., min_length=1, description="List of 'syn_kJ_vI' IDs")
    factor: Optional[float] = Field(None, description="Multiplicative factor for weaken/strengthen")


class SurgeryRecallRequest(BaseModel):
    """Request to run recall on both baseline and surgery branches."""
    query_concept: str = Field(..., min_length=1)
    expected_value: Optional[str] = None
    measure: str = Field("cosine", pattern="^(cosine|dot)$")
    top_k: int = Field(5, ge=1, le=20)


class MemoryXRayRequest(BaseModel):
    """Request Memory X-Ray for a specific concept."""
    query_concept: str = Field(..., min_length=1)
    expected_value: Optional[str] = None
    dimension: int = Field(16, ge=4, le=256)
    seed: int = Field(42, ge=0)
    decay: float = Field(0.05, ge=0.0, le=1.0)
    branch: Optional[str] = Field("live", description="'live', 'baseline', or 'surgery'")
