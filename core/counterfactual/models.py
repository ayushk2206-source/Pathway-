"""Counterfactual experiment domain model (Phase 04)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np

from .types import CounterfactualStatus, InterventionType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize(val: Any) -> Any:
    if isinstance(val, (np.floating, float)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, dict):
        return {k: _sanitize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize(v) for v in val]
    return val


@dataclass
class CounterfactualExperiment:
    """The complete record of an empirical counterfactual investigation."""

    counterfactual_id: str = field(default_factory=lambda: f"cf-{uuid.uuid4().hex[:8]}")
    parent_experiment_id: str = ""
    parent_history_id: Optional[str] = None
    title: str = "Counterfactual Memory Branch"
    description: str = ""
    original_configuration: Dict[str, Any] = field(default_factory=dict)
    intervention: Dict[str, Any] = field(default_factory=dict)
    intervention_type: str = InterventionType.REMOVE_EVENT.value
    intervention_target: Optional[Any] = None
    intervention_parameters: Dict[str, Any] = field(default_factory=dict)
    original_result: Dict[str, Any] = field(default_factory=dict)
    counterfactual_result: Dict[str, Any] = field(default_factory=dict)
    comparison: Dict[str, Any] = field(default_factory=dict)
    divergence: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    status: CounterfactualStatus = CounterfactualStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counterfactual_id": self.counterfactual_id,
            "parent_experiment_id": self.parent_experiment_id,
            "parent_history_id": self.parent_history_id,
            "title": self.title,
            "description": self.description,
            "original_configuration": _sanitize(self.original_configuration),
            "intervention": _sanitize(self.intervention),
            "intervention_type": self.intervention_type,
            "intervention_target": self.intervention_target,
            "intervention_parameters": _sanitize(self.intervention_parameters),
            "original_result": _sanitize(self.original_result),
            "counterfactual_result": _sanitize(self.counterfactual_result),
            "comparison": _sanitize(self.comparison),
            "divergence": _sanitize(self.divergence),
            "provenance": _sanitize(self.provenance),
            "created_at": self.created_at,
            "status": self.status.value if isinstance(self.status, CounterfactualStatus) else str(self.status),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CounterfactualExperiment":
        st = d.get("status", CounterfactualStatus.COMPLETED)
        if isinstance(st, str):
            st = CounterfactualStatus(st)
        return cls(
            counterfactual_id=d["counterfactual_id"],
            parent_experiment_id=d.get("parent_experiment_id", ""),
            parent_history_id=d.get("parent_history_id"),
            title=d.get("title", "Counterfactual Memory Branch"),
            description=d.get("description", ""),
            original_configuration=dict(d.get("original_configuration", {})),
            intervention=dict(d.get("intervention", {})),
            intervention_type=str(d.get("intervention_type", InterventionType.REMOVE_EVENT.value)),
            intervention_target=d.get("intervention_target"),
            intervention_parameters=dict(d.get("intervention_parameters", {})),
            original_result=dict(d.get("original_result", {})),
            counterfactual_result=dict(d.get("counterfactual_result", {})),
            comparison=dict(d.get("comparison", {})),
            divergence=dict(d.get("divergence", {})),
            provenance=dict(d.get("provenance", {})),
            created_at=d.get("created_at", _now_iso()),
            status=st,
        )

    def to_experiment(self) -> Any:
        """Convert counterfactual_result payload back into an Experiment domain object."""
        from core.experiment import Experiment
        if not self.counterfactual_result:
            raise ValueError(f"Counterfactual '{self.counterfactual_id}' has no counterfactual_result.")
        if "experiment" in self.counterfactual_result and isinstance(self.counterfactual_result["experiment"], dict):
            return Experiment.from_dict(self.counterfactual_result["experiment"])
        if "seed" in self.counterfactual_result:
            return Experiment.from_dict(self.counterfactual_result)
        raise ValueError(f"Counterfactual '{self.counterfactual_id}' counterfactual_result does not contain full experiment serialization.")
