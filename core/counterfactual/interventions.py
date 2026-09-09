"""Intervention definitions and validation for Counterfactual Memory Archaeology (Phase 04)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .types import (
    MAX_REPLAY_LENGTH,
    InterventionType,
)


class CounterfactualValidationError(ValueError):
    """Raised when an intervention specification is invalid or exceeds quotas."""
    pass


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


class CounterfactualValidator:
    """Validator class for counterfactual interventions matching ExperimentValidator."""

    @classmethod
    def validate(cls, intervention: Intervention, history: Any) -> ValidationResult:
        h_len = len(history) if isinstance(history, list) else int(history)
        try:
            validate_intervention(intervention, h_len)
            return ValidationResult(valid=True, errors=[])
        except CounterfactualValidationError as exc:
            return ValidationResult(valid=False, errors=[str(exc)])


@dataclass
class Intervention:
    """A concrete intervention specification applied to a historical timeline."""

    intervention_id: str = field(default_factory=lambda: f"intv-{uuid.uuid4().hex[:8]}")
    intervention_type: InterventionType = InterventionType.REMOVE_EVENT
    target_timestep: Optional[int] = None
    target_event_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type.value if isinstance(self.intervention_type, InterventionType) else str(self.intervention_type),
            "target_timestep": self.target_timestep,
            "target_event_id": self.target_event_id,
            "parameters": self.parameters,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Intervention":
        itype = d.get("intervention_type", InterventionType.REMOVE_EVENT)
        if isinstance(itype, str):
            itype = InterventionType(itype)
        return cls(
            intervention_id=d.get("intervention_id", f"intv-{uuid.uuid4().hex[:8]}"),
            intervention_type=itype,
            target_timestep=d.get("target_timestep"),
            target_event_id=d.get("target_event_id"),
            parameters=dict(d.get("parameters", {})),
            description=d.get("description", ""),
            metadata=dict(d.get("metadata", {})),
        )


def validate_intervention(intervention: Intervention, history_length: int) -> None:
    """Validate intervention against bounds and current history length."""
    if history_length > MAX_REPLAY_LENGTH:
        raise CounterfactualValidationError(
            f"History length {history_length} exceeds MAX_REPLAY_LENGTH ({MAX_REPLAY_LENGTH})"
        )

    itype = intervention.intervention_type
    p = intervention.parameters
    tt = intervention.target_timestep
    te = intervention.target_event_id

    # Pointwise interventions requiring a target event or timestep
    point_types = {
        InterventionType.REMOVE_EVENT,
        InterventionType.DUPLICATE_EVENT,
        InterventionType.REPLACE_EVENT,
        InterventionType.MODIFY_EVENT,
        InterventionType.MOVE_EVENT,
        InterventionType.CHANGE_STRENGTH,
        InterventionType.CHANGE_SIMILARITY,
        InterventionType.RESET_MEMORY,
    }

    if itype in point_types:
        if tt is None and not te:
            raise CounterfactualValidationError(
                f"Intervention '{itype.value}' requires either 'target_timestep' or 'target_event_id'"
            )
        if tt is not None and not (0 <= tt < history_length):
            raise CounterfactualValidationError(
                f"target_timestep {tt} out of bounds for history length {history_length} [0, {history_length - 1}]"
            )

    if itype == InterventionType.MOVE_EVENT:
        dest = p.get("destination_timestep")
        if dest is None:
            raise CounterfactualValidationError("MOVE_EVENT requires 'destination_timestep' parameter")
        if not (0 <= dest < history_length):
            raise CounterfactualValidationError(
                f"destination_timestep {dest} out of bounds for history length {history_length}"
            )

    elif itype == InterventionType.REPLACE_EVENT:
        spec = p.get("replacement_spec")
        if not spec or not isinstance(spec, dict):
            raise CounterfactualValidationError("REPLACE_EVENT requires a valid 'replacement_spec' dict")
        if not spec.get("concept_label") or not spec.get("attribute_label"):
            raise CounterfactualValidationError("replacement_spec must provide 'concept_label' and 'attribute_label'")

    elif itype == InterventionType.MODIFY_EVENT:
        mods = p.get("modifications")
        if not mods or not isinstance(mods, dict):
            raise CounterfactualValidationError("MODIFY_EVENT requires a non-empty 'modifications' dict")
        if "strength" in mods and not (0.0 <= float(mods["strength"]) <= 10.0):
            raise CounterfactualValidationError("strength modification must be in [0.0, 10.0]")
        if "importance" in mods and not (0.0 <= float(mods["importance"]) <= 10.0):
            raise CounterfactualValidationError("importance modification must be in [0.0, 10.0]")

    elif itype == InterventionType.CHANGE_STRENGTH:
        strength = p.get("new_strength")
        factor = p.get("factor")
        if strength is None and factor is None:
            raise CounterfactualValidationError("CHANGE_STRENGTH requires either 'new_strength' or 'factor'")
        if strength is not None and not (0.0 <= float(strength) <= 10.0):
            raise CounterfactualValidationError("new_strength must be in [0.0, 10.0]")
        if factor is not None and not (0.0 <= float(factor) <= 10.0):
            raise CounterfactualValidationError("factor must be in [0.0, 10.0]")

    elif itype == InterventionType.INJECT_MEMORY:
        spec = p.get("event_spec")
        if not spec or not isinstance(spec, dict):
            raise CounterfactualValidationError("INJECT_MEMORY requires a valid 'event_spec' dict")
        if not spec.get("concept_label") or not spec.get("attribute_label"):
            raise CounterfactualValidationError("INJECT_MEMORY event_spec must contain 'concept_label' and 'attribute_label'")
        inj_time = intervention.target_timestep if intervention.target_timestep is not None else p.get("timestep")
        if inj_time is None:
            raise CounterfactualValidationError("INJECT_MEMORY requires an injection timestep")
        if not (0 <= int(inj_time) <= history_length):
            raise CounterfactualValidationError(
                f"Injection timestep {inj_time} out of bounds for insertion [0, {history_length}]"
            )

    elif itype in {InterventionType.FREEZE_MEMORY, InterventionType.TEMPORAL_FREEZE, InterventionType.TEMPORAL_DELETE, InterventionType.TEMPORAL_SCALE}:
        t_start = p.get("start_timestep", 0)
        t_end = p.get("end_timestep", history_length - 1)
        if t_start > t_end:
            raise CounterfactualValidationError(f"Temporal interval start ({t_start}) > end ({t_end})")
        if not (0 <= t_start < history_length) or not (0 <= t_end < history_length):
            raise CounterfactualValidationError(
                f"Temporal interval [{t_start}, {t_end}] out of bounds for history length {history_length}"
            )


# ---------------------------------------------------------------------------
# Intervention Factory Helpers
# ---------------------------------------------------------------------------

def create_remove_intervention(
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.REMOVE_EVENT,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        description=description or f"Remove event at {target_timestep or target_event_id}",
    )


create_ablation_intervention = create_remove_intervention


def create_duplicate_intervention(
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.DUPLICATE_EVENT,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        description=description or f"Duplicate event at {target_timestep or target_event_id}",
    )


def create_replace_intervention(
    replacement_spec: Dict[str, Any],
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.REPLACE_EVENT,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        parameters={"replacement_spec": replacement_spec},
        description=description or f"Replace event at {target_timestep or target_event_id}",
    )


def create_modify_intervention(
    modifications: Dict[str, Any],
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.MODIFY_EVENT,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        parameters={"modifications": modifications},
        description=description or f"Modify event properties at {target_timestep or target_event_id}",
    )


def create_move_intervention(
    destination_timestep: int,
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.MOVE_EVENT,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        parameters={"destination_timestep": destination_timestep},
        description=description or f"Move event {target_timestep or target_event_id} to t={destination_timestep}",
    )


def create_change_strength_intervention(
    new_strength: Optional[float] = None,
    factor: Optional[float] = None,
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.CHANGE_STRENGTH,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        parameters={"new_strength": new_strength, "factor": factor},
        description=description or f"Change strength of event at {target_timestep or target_event_id}",
    )


def create_change_similarity_intervention(
    delta_similarity: float = 0.0,
    target_timestep: Optional[int] = None,
    target_event_id: Optional[str] = None,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.CHANGE_SIMILARITY,
        target_timestep=target_timestep,
        target_event_id=target_event_id,
        parameters={"delta_similarity": delta_similarity},
        description=description or f"Change similarity around event at {target_timestep or target_event_id}",
    )


def create_reset_memory_intervention(
    target_timestep: int,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.RESET_MEMORY,
        target_timestep=target_timestep,
        description=description or f"Reset memory state to zero at t={target_timestep}",
    )


def create_freeze_memory_intervention(
    start_timestep: int,
    end_timestep: int,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.FREEZE_MEMORY,
        parameters={"start_timestep": start_timestep, "end_timestep": end_timestep},
        description=description or f"Freeze memory updates between t={start_timestep} and t={end_timestep}",
    )


def create_inject_memory_intervention(
    timestep: int,
    concept_label: str,
    attribute_label: str,
    strength: float = 1.0,
    importance: float = 1.0,
    description: str = "",
) -> Intervention:
    return Intervention(
        intervention_type=InterventionType.INJECT_MEMORY,
        target_timestep=timestep,
        parameters={
            "timestep": timestep,
            "event_spec": {
                "concept_label": concept_label,
                "attribute_label": attribute_label,
                "strength": strength,
                "importance": importance,
            },
        },
        description=description or f"Inject memory ({concept_label}={attribute_label}) at t={timestep}",
    )


def create_temporal_surgery_intervention(
    operation: str,
    start_timestep: int,
    end_timestep: int,
    factor: float = 1.0,
    description: str = "",
) -> Intervention:
    op_map = {
        "delete": InterventionType.TEMPORAL_DELETE,
        "freeze": InterventionType.TEMPORAL_FREEZE,
        "scale": InterventionType.TEMPORAL_SCALE,
    }
    itype = op_map.get(operation.lower(), InterventionType.TEMPORAL_SCALE)
    return Intervention(
        intervention_type=itype,
        parameters={
            "operation": operation,
            "start_timestep": start_timestep,
            "end_timestep": end_timestep,
            "factor": factor,
        },
        description=description or f"Temporal surgery ({operation}) on [{start_timestep}, {end_timestep}]",
    )
