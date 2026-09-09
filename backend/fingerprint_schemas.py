"""Pydantic schemas for Phase 20: Memory Genome & Synaptic Fingerprint API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComputeFingerprintRequest(BaseModel):
    concept: str = Field(..., description="Concept label to compute fingerprint for")
    value: Optional[str] = Field(None, description="Optional target value")
    dimension: int = Field(16, ge=4, le=128, description="Substrate dimension")
    seed: int = Field(42, description="Random seed")
    update_strength: float = Field(0.35, ge=0.01, le=2.0, description="Hebbian learning rate")
    decay: float = Field(0.01, ge=0.0, le=0.5, description="Passive decay rate")


class CompareFingerprintsRequest(BaseModel):
    concept_a: str = Field(..., description="First concept label")
    concept_b: str = Field(..., description="Second concept label")
    value_a: Optional[str] = Field(None, description="First target value")
    value_b: Optional[str] = Field(None, description="Second target value")
    dimension: int = Field(16, ge=4, le=128)
    seed: int = Field(42)


class SurfaceVsInternalRequest(BaseModel):
    concepts: List[str] = Field(default_factory=lambda: [
        "Concept Alpha", "Concept Beta", "Concept Gamma", "Concept Delta"
    ], min_length=2)
    dimension: int = Field(16, ge=4, le=128)
    seed: int = Field(42)


class CloningTestRequest(BaseModel):
    target_concept: str = Field("Concept Alpha")
    target_value: str = Field("Value Alpha")
    intervening_concept: str = Field("Intervening Beta")
    intervening_value: str = Field("Value Beta")
    dimension: int = Field(16, ge=4, le=128)
    seed: int = Field(42)


class CollisionMutationRequest(BaseModel):
    concept_a: str = Field("Memory A")
    value_a: str = Field("Target A")
    concept_b: str = Field("Memory B (Comp)")
    value_b: str = Field("Target B")
    dimension: int = Field(16, ge=4, le=128)
    seed: int = Field(42)


class FingerprintSurgeryRequest(BaseModel):
    concept: str = Field("Memory Surgery Test")
    value: str = Field("Value Surgery")
    target_synapse: List[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)
    new_weight: float = Field(0.0)
    dimension: int = Field(16, ge=4, le=128)
    seed: int = Field(42)


class CounterfactualFingerprintRequest(BaseModel):
    concept: str = Field("Memory CF")
    value: str = Field("Value CF")
    cf_update_strength: float = Field(0.05, ge=0.0, le=2.0)
    dimension: int = Field(16, ge=4, le=128)
    seed: int = Field(42)


class VerifyChallengeRequest(BaseModel):
    challenge_id: str = Field(...)
    selected_option: str = Field(...)
