"""Experiment domain models for the Experiment Lab (Phase 03).

Provides the primary LabExperiment abstraction, condition results, multi-trial
aggregates, sweeps, grids, and comparison records.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_numeric(val: Any) -> Any:
    """Convert numpy scalar types to native Python types recursively."""
    if isinstance(val, (np.floating, float)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, dict):
        return {k: _sanitize_numeric(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize_numeric(v) for v in val]
    return val


@dataclass
class TrialRecord:
    """The execution record of one repeated trial in an experimental condition."""

    trial_index: int
    seed: int
    underlying_experiment_id: str
    metrics: Dict[str, float]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_index": int(self.trial_index),
            "seed": int(self.seed),
            "underlying_experiment_id": self.underlying_experiment_id,
            "metrics": _sanitize_numeric(self.metrics),
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TrialRecord":
        return cls(
            trial_index=d["trial_index"],
            seed=d["seed"],
            underlying_experiment_id=d["underlying_experiment_id"],
            metrics=d["metrics"],
            provenance=d.get("provenance", {}),
        )


@dataclass
class ConditionResult:
    """Results from one parameter configuration condition across 1 or more trials."""

    condition_label: str
    parameter_values: Dict[str, Any]
    trials: List[TrialRecord] = field(default_factory=list)
    aggregated_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # aggregated_metrics maps: metric_name -> {mean, median, std, min, max, ci_lower, ci_upper}
    representative_experiment_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_label": self.condition_label,
            "parameter_values": _sanitize_numeric(self.parameter_values),
            "trials": [t.to_dict() for t in self.trials],
            "aggregated_metrics": _sanitize_numeric(self.aggregated_metrics),
            "representative_experiment_id": self.representative_experiment_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConditionResult":
        return cls(
            condition_label=d["condition_label"],
            parameter_values=d["parameter_values"],
            trials=[TrialRecord.from_dict(t) for t in d.get("trials", [])],
            aggregated_metrics=d.get("aggregated_metrics", {}),
            representative_experiment_id=d.get("representative_experiment_id"),
        )


@dataclass
class ComparisonResult:
    """Controlled comparison between a baseline and a treatment condition."""

    baseline_condition: ConditionResult
    treatment_condition: ConditionResult
    differing_variables: Dict[str, Dict[str, Any]]
    # differing_variables: {var_name: {"baseline": val1, "treatment": val2}}
    metric_deltas: Dict[str, float]  # treatment - baseline
    percentage_changes: Dict[str, Optional[float]]
    state_difference: Optional[Dict[str, Any]] = None
    recall_difference: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_condition": self.baseline_condition.to_dict(),
            "treatment_condition": self.treatment_condition.to_dict(),
            "differing_variables": self.differing_variables,
            "metric_deltas": _sanitize_numeric(self.metric_deltas),
            "percentage_changes": _sanitize_numeric(self.percentage_changes),
            "state_difference": _sanitize_numeric(self.state_difference),
            "recall_difference": _sanitize_numeric(self.recall_difference),
        }


@dataclass
class SweepResult:
    """Result of a 1-dimensional parameter sweep across a range of values."""

    parameter: str
    tested_values: List[Any]
    conditions: List[ConditionResult]
    relationship_analysis: Dict[str, Any] = field(default_factory=dict)
    detected_pattern: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "tested_values": _sanitize_numeric(self.tested_values),
            "conditions": [c.to_dict() for c in self.conditions],
            "relationship_analysis": _sanitize_numeric(self.relationship_analysis),
            "detected_pattern": _sanitize_numeric(self.detected_pattern),
        }


@dataclass
class GridResult:
    """Result of a 2-dimensional parameter sweep grid."""

    param_x: str
    values_x: List[Any]
    param_y: str
    values_y: List[Any]
    cells: List[Dict[str, Any]]  # [{x, y, condition: ConditionResult}]
    matrix_metrics: Dict[str, List[List[Optional[float]]]]
    # metric_name -> 2D matrix [len(values_y)][len(values_x)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "param_x": self.param_x,
            "values_x": _sanitize_numeric(self.values_x),
            "param_y": self.param_y,
            "values_y": _sanitize_numeric(self.values_y),
            "cells": [
                {
                    "x": _sanitize_numeric(c["x"]),
                    "y": _sanitize_numeric(c["y"]),
                    "condition": c["condition"].to_dict() if isinstance(c["condition"], ConditionResult) else c["condition"],
                }
                for c in self.cells
            ],
            "matrix_metrics": _sanitize_numeric(self.matrix_metrics),
        }


@dataclass
class LabExperiment:
    """The canonical Experiment Lab research experiment domain entity.

    Stands as a complete, immutable unit of scientific investigation.
    """

    experiment_id: str
    title: str
    research_question: str
    hypothesis: Optional[str] = None
    hypothesis_id: Optional[str] = None
    objective: str = ""
    mechanism: str = "leaky"
    independent_variables: List[str] = field(default_factory=list)
    dependent_variables: List[str] = field(default_factory=list)
    controlled_variables: Dict[str, Any] = field(default_factory=dict)
    baseline_configuration: Dict[str, Any] = field(default_factory=dict)
    treatment_configurations: List[Dict[str, Any]] = field(default_factory=list)
    seed: int = 42
    trials: int = 1
    results: Optional[Union[SweepResult, GridResult, ComparisonResult, List[ConditionResult]]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)
    conclusion: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    parent_experiment_id: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    status: ExperimentStatus = ExperimentStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        res_dict = None
        if self.results is not None:
            if hasattr(self.results, "to_dict"):
                res_dict = self.results.to_dict()
            elif isinstance(self.results, list):
                res_dict = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.results]
            else:
                res_dict = _sanitize_numeric(self.results)

        return {
            "experiment_id": self.experiment_id,
            "version": int(self.version),
            "parent_experiment_id": self.parent_experiment_id,
            "title": self.title,
            "research_question": self.research_question,
            "hypothesis": self.hypothesis,
            "hypothesis_id": self.hypothesis_id,
            "objective": self.objective,
            "mechanism": self.mechanism,
            "independent_variables": self.independent_variables,
            "dependent_variables": self.dependent_variables,
            "controlled_variables": _sanitize_numeric(self.controlled_variables),
            "baseline_configuration": _sanitize_numeric(self.baseline_configuration),
            "treatment_configurations": _sanitize_numeric(self.treatment_configurations),
            "seed": int(self.seed),
            "trials": int(self.trials),
            "results": res_dict,
            "metrics": _sanitize_numeric(self.metrics),
            "observations": self.observations,
            "conclusion": self.conclusion,
            "provenance": self.provenance,
            "created_at": self.created_at,
            "status": self.status.value if isinstance(self.status, ExperimentStatus) else str(self.status),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LabExperiment":
        raw_res = d.get("results")
        parsed_res = None
        if isinstance(raw_res, dict):
            if "parameter" in raw_res and "tested_values" in raw_res:
                parsed_res = SweepResult(
                    parameter=raw_res["parameter"],
                    tested_values=raw_res["tested_values"],
                    conditions=[ConditionResult.from_dict(c) for c in raw_res.get("conditions", [])],
                    relationship_analysis=raw_res.get("relationship_analysis", {}),
                    detected_pattern=raw_res.get("detected_pattern", {}),
                )
            elif "param_x" in raw_res and "matrix_metrics" in raw_res:
                parsed_res = GridResult(
                    param_x=raw_res["param_x"],
                    values_x=raw_res["values_x"],
                    param_y=raw_res["param_y"],
                    values_y=raw_res["values_y"],
                    cells=raw_res.get("cells", []),
                    matrix_metrics=raw_res.get("matrix_metrics", {}),
                )
            elif "baseline_condition" in raw_res:
                parsed_res = ComparisonResult(
                    baseline_condition=ConditionResult.from_dict(raw_res["baseline_condition"]),
                    treatment_condition=ConditionResult.from_dict(raw_res["treatment_condition"]),
                    differing_variables=raw_res.get("differing_variables", {}),
                    metric_deltas=raw_res.get("metric_deltas", {}),
                    percentage_changes=raw_res.get("percentage_changes", {}),
                    state_difference=raw_res.get("state_difference"),
                    recall_difference=raw_res.get("recall_difference"),
                )
            else:
                parsed_res = raw_res
        elif isinstance(raw_res, list):
            parsed_res = [ConditionResult.from_dict(c) if isinstance(c, dict) and "condition_label" in c else c for c in raw_res]

        return cls(
            experiment_id=d["experiment_id"],
            title=d["title"],
            research_question=d["research_question"],
            hypothesis=d.get("hypothesis"),
            hypothesis_id=d.get("hypothesis_id"),
            objective=d.get("objective", ""),
            mechanism=d.get("mechanism", "leaky"),
            independent_variables=d.get("independent_variables", []),
            dependent_variables=d.get("dependent_variables", []),
            controlled_variables=d.get("controlled_variables", {}),
            baseline_configuration=d.get("baseline_configuration", {}),
            treatment_configurations=d.get("treatment_configurations", []),
            seed=int(d.get("seed", 42)),
            trials=int(d.get("trials", 1)),
            results=parsed_res,
            metrics=d.get("metrics", {}),
            observations=d.get("observations", []),
            conclusion=d.get("conclusion"),
            provenance=d.get("provenance", {}),
            version=int(d.get("version", 1)),
            parent_experiment_id=d.get("parent_experiment_id"),
            created_at=d.get("created_at", _now_iso()),
            status=ExperimentStatus(d.get("status", "draft")),
        )
