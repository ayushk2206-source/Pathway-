"""Pydantic request and response schemas for Experiment Lab API (Phase 03)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LabExperimentCreateRequest(BaseModel):
    title: str = Field(..., description="Descriptive title of the research study")
    research_question: str = Field(..., description="Core scientific question being investigated")
    hypothesis: Optional[str] = Field(None, description="Hypothesis statement being tested")
    hypothesis_id: Optional[str] = Field(None, description="Linked hypothesis ID")
    objective: str = Field("", description="Specific empirical target or milestone")
    mechanism: str = Field("leaky", description="Baseline mechanism architecture")
    independent_variables: List[str] = Field(default_factory=list)
    dependent_variables: List[str] = Field(default_factory=list)
    controlled_variables: Dict[str, Any] = Field(default_factory=dict)
    baseline_configuration: Dict[str, Any] = Field(default_factory=dict)
    treatment_configurations: List[Dict[str, Any]] = Field(default_factory=list)
    seed: int = 42
    trials: int = Field(1, ge=1, le=100)
    run_immediately: bool = True


class ParameterSweepRequest(BaseModel):
    parameter: str = Field(..., description="Name of independent variable to sweep")
    values: List[Any] = Field(..., min_length=1, max_length=144, description="Array of parameter values")
    base_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    trials: int = Field(1, ge=1, le=100)
    seed: int = 42
    title: Optional[str] = None
    research_question: Optional[str] = None


class GridSweepRequest(BaseModel):
    param_x: str = Field(..., description="First independent variable (X axis)")
    values_x: List[Any] = Field(..., min_length=1, max_length=24)
    param_y: str = Field(..., description="Second independent variable (Y axis)")
    values_y: List[Any] = Field(..., min_length=1, max_length=24)
    base_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    trials: int = Field(1, ge=1, le=100)
    seed: int = 42
    title: Optional[str] = None
    research_question: Optional[str] = None


class ControlledComparisonRequest(BaseModel):
    baseline_config: Dict[str, Any] = Field(..., description="Reference control condition parameters")
    treatment_config: Dict[str, Any] = Field(..., description="Treatment condition parameters")
    trials: int = Field(1, ge=1, le=100)
    seed: int = 42
    title: Optional[str] = None
    research_question: Optional[str] = None


class CreateHypothesisRequest(BaseModel):
    statement: str = Field(..., description="Falsifiable scientific statement")
    independent_variable: str
    dependent_variable: str
    predicted_direction: str = Field("increase", description="increase | decrease | no_change | non_monotonic")
    expected_relationship: str = ""
    confidence_before: float = Field(0.5, ge=0.0, le=1.0)


class EvaluateHypothesisRequest(BaseModel):
    experiment_id: str
    baseline_value: Optional[float] = None
    treatment_value: Optional[float] = None
    correlation: Optional[float] = None


class CompetingHypothesesRequest(BaseModel):
    topic: str
    phenomenon: str
    hypotheses: List[CreateHypothesisRequest] = Field(..., min_length=2)
    experiment_id: Optional[str] = None
    observed_deltas: Optional[Dict[str, float]] = None


class DiscriminatingExperimentRequest(BaseModel):
    hypotheses: List[CreateHypothesisRequest] = Field(..., min_length=2)
    base_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SuggestNextRequest(BaseModel):
    parameter: str
    tested_values: List[float] = Field(..., min_length=1)
    observed_metrics: List[float] = Field(..., min_length=1)
    metric_name: str = "metric"
    parameter_min: Optional[float] = None
    parameter_max: Optional[float] = None
    num_suggestions: int = Field(3, ge=1, le=10)


class DiffExperimentsRequest(BaseModel):
    experiment_id_a: str
    experiment_id_b: str


class ReproduceExperimentRequest(BaseModel):
    tolerance: float = 1e-9
