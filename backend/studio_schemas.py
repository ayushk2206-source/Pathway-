"""Pydantic validation schemas for Phase 22: Experiment Studio."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExperimentConfigRequestSchema(BaseModel):
    experiment_id: Optional[str] = Field(None, description="Optional custom ID")
    name: str = Field("Custom Synaptic Experiment", description="Title of experiment")
    experiment_type: str = Field("INTERFERENCE", description="ENCODING, INTERFERENCE, SURGERY, COUNTERFACTUAL, PERSISTENCE, COMPARISON")
    seed: int = Field(42, description="Random seed for deterministic initialization")
    d: int = Field(16, description="Synaptic dimension (8, 16, 32, 64)")
    decay: float = Field(0.05, ge=0.0, le=0.95, description="Synaptic decay rate λ")
    update_strength: float = Field(1.0, ge=0.1, le=2.5, description="Plasticity learning rate η")
    mechanism: str = Field("hebbian", description="Computational mechanism")

    concept_a: str = Field("cat", description="Target cue string")
    value_a: str = Field("whiskers", description="Target value string")
    importance_a: float = Field(1.0, ge=0.1, le=2.0)
    strength_a: float = Field(1.0, ge=0.1, le=2.0)

    interfering_concept: str = Field("tiger", description="Interfering cue")
    interfering_value: str = Field("stripes", description="Interfering value")
    interfering_strength: float = Field(0.8, ge=0.0, le=2.5)
    intervening_steps: int = Field(1, ge=0, le=20)

    surgery_target_row: int = Field(0, ge=0)
    surgery_target_col: int = Field(0, ge=0)
    surgery_action: str = Field("zero", description="zero, clamp_high, invert, attenuate")

    cf_param_name: str = Field("decay", description="decay, update_strength")
    cf_param_value: float = Field(0.3)

    decay_cycles: int = Field(5, ge=0, le=50)

    comparison_concept: str = Field("dog")
    comparison_value: str = Field("bark")

    controlled_variables: List[str] = Field(default_factory=list)
    changed_variable: Optional[str] = Field(None)


class ExperimentHypothesisRequestSchema(BaseModel):
    hypothesis_text: str = Field(..., min_length=3, description="Hypothesis statement")
    predicted_outcome: str = Field("RETENTION_DROP", description="Predicted outcome category")
    predicted_challenge_choice: Optional[str] = Field(None, description="A, B, C, or D")


class RunExperimentRequest(BaseModel):
    config: ExperimentConfigRequestSchema
    hypothesis: Optional[ExperimentHypothesisRequestSchema] = None
    notes: Optional[Dict[str, str]] = None


class ABCompareRequest(BaseModel):
    config_a: ExperimentConfigRequestSchema
    config_b: ExperimentConfigRequestSchema


class ParameterSweepRequest(BaseModel):
    base_config: ExperimentConfigRequestSchema
    param_name: str = Field(..., description="Parameter to sweep: decay, update_strength, interfering_strength, decay_cycles")
    param_values: Optional[List[float]] = Field(None, description="Optional custom values array")


class BranchExperimentRequest(BaseModel):
    experiment_id: str = Field(..., description="Existing experiment ID to duplicate")
    modified_param: str = Field(..., description="Single parameter name to modify")
    new_value: Any = Field(..., description="New value for the modified parameter")


class SaveNotesRequest(BaseModel):
    experiment_id: str
    question: str
    hypothesis: str
    observation: str
    conclusion: str
