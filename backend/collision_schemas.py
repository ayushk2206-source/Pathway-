"""Pydantic schemas for the Phase 17 Memory Collision & Interference Lab API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CollisionMemorySchema(BaseModel):
    """Specification of a memory to be encoded in the collision lab."""

    concept: str = Field(..., description="Concept/cue identifier")
    value: str = Field(..., description="Target value to associate")
    importance: float = Field(default=1.0, ge=0.0, le=5.0, description="Memory importance multiplier")
    strength: float = Field(default=1.0, ge=0.0, le=5.0, description="Memory write strength factor")


class CollisionRunRequest(BaseModel):
    """Request payload to execute a controlled memory collision experiment."""

    seed: int = Field(default=42, description="RNG seed for deterministic reproducibility")
    dimension: int = Field(default=16, ge=4, le=64, description="Vector dimension of neural state")
    decay: float = Field(default=0.05, ge=0.0, le=1.0, description="Synaptic decay per time step (λ)")
    update_strength: float = Field(default=1.0, ge=0.1, le=5.0, description="Base learning rate (η)")
    memory_a: CollisionMemorySchema = Field(
        default_factory=lambda: CollisionMemorySchema(concept="alpha_cue", value="target_alpha"),
        description="First memory",
    )
    memory_b: CollisionMemorySchema = Field(
        default_factory=lambda: CollisionMemorySchema(concept="beta_cue", value="target_beta"),
        description="Second memory competing for synaptic coordinates",
    )
    memory_c: Optional[CollisionMemorySchema] = Field(
        default=None, description="Optional third memory for multi-collision dynamics"
    )
    order: str = Field(
        default="A_THEN_B",
        description="Sequence of writes: 'A_THEN_B' or 'B_THEN_A'",
    )
    temporal_delay: int = Field(
        default=0, ge=0, le=20, description="Idle decay steps between Memory A and Memory B"
    )
    overlap_preset: str = Field(
        default="CUSTOM",
        description="Preset similarity: 'LOW' (0.0), 'MODERATE' (0.45), 'HIGH' (0.85), or 'CUSTOM'",
    )
    concept_similarity: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Representational key vector correlation"
    )


class ThreeConditionRequest(BaseModel):
    """Request payload to run Low, Moderate, and High overlap conditions simultaneously."""

    seed: int = Field(default=42)
    dimension: int = Field(default=16, ge=4, le=64)
    decay: float = Field(default=0.05, ge=0.0, le=1.0)
    update_strength: float = Field(default=1.0, ge=0.1, le=5.0)
    memory_a: CollisionMemorySchema = Field(
        default_factory=lambda: CollisionMemorySchema(concept="alpha_cue", value="target_alpha")
    )
    memory_b: CollisionMemorySchema = Field(
        default_factory=lambda: CollisionMemorySchema(concept="beta_cue", value="target_beta")
    )
    order: str = Field(default="A_THEN_B")
    temporal_delay: int = Field(default=0, ge=0, le=20)


class OrderComparisonRequest(BaseModel):
    """Request payload to compare write order A -> B versus B -> A."""

    seed: int = Field(default=42)
    dimension: int = Field(default=16, ge=4, le=64)
    decay: float = Field(default=0.05, ge=0.0, le=1.0)
    update_strength: float = Field(default=1.0, ge=0.1, le=5.0)
    memory_a: CollisionMemorySchema = Field(
        default_factory=lambda: CollisionMemorySchema(concept="alpha_cue", value="target_alpha")
    )
    memory_b: CollisionMemorySchema = Field(
        default_factory=lambda: CollisionMemorySchema(concept="beta_cue", value="target_beta")
    )
    overlap_preset: str = Field(default="MODERATE")
    concept_similarity: float = Field(default=0.45, ge=0.0, le=1.0)
    temporal_delay: int = Field(default=0, ge=0, le=20)


class CollisionSurgeryRequest(BaseModel):
    """Request payload to surgically silence, weaken, or strengthen a shared synapse."""

    config: CollisionRunRequest
    synapse_id: str = Field(..., description="Target synapse identifier e.g. syn_k2_v5")
    operation: str = Field(default="silence", description="'silence', 'weaken', or 'strengthen'")
    factor: float = Field(default=0.0, ge=0.0, le=5.0, description="Scaling factor for weaken/strengthen")


class CollisionCounterfactualRequest(BaseModel):
    """Request payload to test the counterfactual: What if Memory B never touched shared synapses?"""

    config: CollisionRunRequest
    shared_synapse_ids: Optional[List[str]] = Field(
        default=None, description="Optional explicit list of synapses to protect"
    )
