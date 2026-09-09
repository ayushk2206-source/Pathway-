"""Pydantic validation schemas for Phase 23: Scientific Evidence & Research Layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PaperQuerySchema(BaseModel):
    tag: Optional[str] = Field(None, description="Filter papers by concept tag")


class MethodologyRequestSchema(BaseModel):
    experiment_type: str = Field("INTERFERENCE", description="Type of experiment")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters")


class EvidenceCheckRequestSchema(BaseModel):
    claim_id: str = Field(..., description="ID of claim to verify")
    experiment_id: Optional[str] = Field(None, description="Optional experiment result to bind")
