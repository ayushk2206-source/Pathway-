"""Pydantic schemas for Memory Detective & Research Lab (Phase 18)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestHypothesisRequest(BaseModel):
    """Request payload to test a learner's hypothesis with assigned confidence."""

    case_id: str = Field(..., description="Investigation case identifier")
    hypothesis_id: str = Field(..., description="Hypothesis being evaluated")
    learner_confidence: str = Field(
        default="MEDIUM",
        description="Learner's self-assessed confidence: 'LOW', 'MEDIUM', or 'HIGH'",
    )
    chosen_tool: Optional[str] = Field(
        default=None,
        description="Experimental tool chosen: 'xray', 'timemachine', 'collision', 'surgery', 'counterfactual'",
    )


class SubmitVerdictRequest(BaseModel):
    """Request payload to submit final verdict, evidence board, and causal chain."""

    case_id: str = Field(..., description="Investigation case identifier")
    chosen_hypothesis_id: str = Field(..., description="Selected conclusion hypothesis")
    collected_evidence_ids: List[str] = Field(default_factory=list, description="Evidence items gathered")
    tests_run_count: int = Field(default=1, ge=0, description="Total experiments/tests launched")
    learner_confidence: str = Field(default="HIGH", description="Confidence level upon submission")
    explanation_chain: List[str] = Field(
        default_factory=list,
        description="Causal chain: e.g. ['MEMORY_WRITE', 'SYNAPTIC_UPDATE', 'INTERFERENCE', 'RECALL_DROP']",
    )


class MemoryInputSchema(BaseModel):
    """Single memory pattern specification."""

    concept: str
    value: str


class CustomExperimentRequest(BaseModel):
    """Request to configure and execute a custom reproducible research experiment."""

    name: str = Field(default="Custom Experiment", description="Experiment title")
    dimension: int = Field(default=16, ge=4, le=64, description="Vector state dimension")
    decay: float = Field(default=0.05, ge=0.0, le=0.5, description="Synaptic decay per step (λ)")
    plasticity_eta: float = Field(default=1.0, ge=0.1, le=5.0, description="Learning rate / plasticity (η)")
    memories: List[MemoryInputSchema] = Field(
        default_factory=lambda: [
            MemoryInputSchema(concept="concept_1", value="target_1"),
            MemoryInputSchema(concept="concept_2", value="target_2"),
        ],
        description="Ordered memory inputs",
    )
    write_order: str = Field(default="SEQUENTIAL", description="'SEQUENTIAL' or 'INTERLEAVED'")
    concept_similarity: float = Field(default=0.2, ge=0.0, le=0.95, description="Representational key overlap")
    temporal_delay: int = Field(default=0, ge=0, le=20, description="Idle decay steps between writes")
    synaptic_silencing_id: Optional[str] = Field(
        default=None, description="Optional target synapse to surgically silence (e.g. syn_k2_v5)"
    )
    seed: int = Field(default=42, description="Random seed for 100% deterministic reproducibility")
    notes: str = Field(default="", description="Researcher hypothesis and observations")


class CompareExperimentsRequest(BaseModel):
    """Request payload to perform side-by-side comparative inspection of two experiments."""

    run_id_a: str = Field(..., description="First experiment ID (e.g. EXP-001)")
    run_id_b: str = Field(..., description="Second experiment ID (e.g. EXP-002)")
