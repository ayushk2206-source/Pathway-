"""Variable abstraction and registry for the Experiment Lab (Phase 03).

Provides a formal, reusable variable system categorizing experimental knobs and
observed metrics into INDEPENDENT, DEPENDENT, and CONTROLLED roles, along with
types, units, ranges, and validation rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class VariableRole(str, Enum):
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"
    CONTROLLED = "controlled"


class VariableType(str, Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"
    CHOICE = "choice"


@dataclass
class Variable:
    """A formal experimental variable definition.

    Fields
    ------
    name:           Unique programmatic identifier (e.g. "memory_similarity")
    description:    Human-readable explanation of what this variable represents
    type:           Data type (float, int, string, boolean, choice)
    role:           Role in the experimental design (independent, dependent, controlled)
    default:        Standard baseline value
    minimum:        Lower bound (numeric types)
    maximum:        Upper bound (numeric types)
    allowed_values: Permitted values (categorical / choice types)
    unit:           Scientific / measurement unit if applicable
    target_layer:   Where in the system this knob applies: "mechanism", "task", "metric", "meta"
    """

    name: str
    description: str
    type: VariableType
    role: VariableRole
    default: Any
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    unit: str = ""
    target_layer: str = "mechanism"

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate whether a value conforms to this variable's definition."""
        if value is None:
            return False, f"Variable '{self.name}' cannot be None"

        if self.type == VariableType.FLOAT:
            try:
                val = float(value)
            except (TypeError, ValueError):
                return False, f"Variable '{self.name}' must be a float, got {type(value).__name__}"
            if self.minimum is not None and val < self.minimum:
                return False, f"Variable '{self.name}' must be >= {self.minimum}, got {val}"
            if self.maximum is not None and val > self.maximum:
                return False, f"Variable '{self.name}' must be <= {self.maximum}, got {val}"
            return True, None

        if self.type == VariableType.INT:
            if isinstance(value, bool):
                return False, f"Variable '{self.name}' must be an integer, got bool"
            try:
                val = int(value)
            except (TypeError, ValueError):
                return False, f"Variable '{self.name}' must be an integer, got {type(value).__name__}"
            if self.minimum is not None and val < self.minimum:
                return False, f"Variable '{self.name}' must be >= {int(self.minimum)}, got {val}"
            if self.maximum is not None and val > self.maximum:
                return False, f"Variable '{self.name}' must be <= {int(self.maximum)}, got {val}"
            return True, None

        if self.type == VariableType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Variable '{self.name}' must be a boolean"
            return True, None

        if self.type in (VariableType.STRING, VariableType.CHOICE):
            sval = str(value)
            if self.allowed_values and sval not in self.allowed_values:
                return (
                    False,
                    f"Variable '{self.name}' value '{sval}' not in allowed values: {self.allowed_values}",
                )
            return True, None

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "role": self.role.value,
            "default": self.default,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "allowed_values": self.allowed_values,
            "unit": self.unit,
            "target_layer": self.target_layer,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Variable":
        return cls(
            name=d["name"],
            description=d["description"],
            type=VariableType(d["type"]),
            role=VariableRole(d["role"]),
            default=d["default"],
            minimum=d.get("minimum"),
            maximum=d.get("maximum"),
            allowed_values=d.get("allowed_values"),
            unit=d.get("unit", ""),
            target_layer=d.get("target_layer", "mechanism"),
        )


# Standard Variable Registry for Neural Archaeology
_BUILTIN_VARIABLES: Dict[str, Variable] = {
    # Independent / Controlled Variables
    "memory_similarity": Variable(
        name="memory_similarity",
        description="Pairwise cosine similarity between competing concept cue vectors",
        type=VariableType.FLOAT,
        role=VariableRole.INDEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=1.0,
        unit="cosine",
        target_layer="task",
    ),
    "update_strength": Variable(
        name="update_strength",
        description="Write gain / learning rate eta applied to each memory state absorption",
        type=VariableType.FLOAT,
        role=VariableRole.INDEPENDENT,
        default=1.0,
        minimum=0.0,
        maximum=10.0,
        unit="gain",
        target_layer="mechanism",
    ),
    "decay": Variable(
        name="decay",
        description="Exponential forgetting rate lambda applied per step (0 = no decay)",
        type=VariableType.FLOAT,
        role=VariableRole.INDEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=1.0,
        unit="rate/step",
        target_layer="mechanism",
    ),
    "interference_strength": Variable(
        name="interference_strength",
        description="Erasure intensity gamma of content aligned with incoming writes (Mechanism E)",
        type=VariableType.FLOAT,
        role=VariableRole.INDEPENDENT,
        default=0.5,
        minimum=0.0,
        maximum=2.0,
        unit="scale",
        target_layer="mechanism",
    ),
    "sparsity": Variable(
        name="sparsity",
        description="Fraction kappa of dimensions retained by competitive k-WTA sparsification",
        type=VariableType.FLOAT,
        role=VariableRole.INDEPENDENT,
        default=0.1,
        minimum=0.01,
        maximum=1.0,
        unit="fraction",
        target_layer="mechanism",
    ),
    "state_dim": Variable(
        name="state_dim",
        description="Fixed dimensionality d of the memory substrate vector/matrix",
        type=VariableType.INT,
        role=VariableRole.CONTROLLED,
        default=128,
        minimum=8,
        maximum=1024,
        unit="dimensions",
        target_layer="mechanism",
    ),
    "mechanism": Variable(
        name="mechanism",
        description="State-update mechanism architecture",
        type=VariableType.CHOICE,
        role=VariableRole.CONTROLLED,
        default="leaky",
        allowed_values=["baseline", "leaky", "competitive", "hebbian", "interference"],
        unit="model",
        target_layer="mechanism",
    ),
    "n_conflicts": Variable(
        name="n_conflicts",
        description="Number of conflicting reassignment events injected into task sequence",
        type=VariableType.INT,
        role=VariableRole.CONTROLLED,
        default=2,
        minimum=0,
        maximum=50,
        unit="events",
        target_layer="task",
    ),
    "input_noise": Variable(
        name="input_noise",
        description="Gaussian noise sigma injected into key/value vectors at write time",
        type=VariableType.FLOAT,
        role=VariableRole.CONTROLLED,
        default=0.0,
        minimum=0.0,
        maximum=5.0,
        unit="std_dev",
        target_layer="mechanism",
    ),
    "cycles": Variable(
        name="cycles",
        description="Repetition cycles for the task sequence",
        type=VariableType.INT,
        role=VariableRole.CONTROLLED,
        default=1,
        minimum=1,
        maximum=20,
        unit="cycles",
        target_layer="task",
    ),
    "seed": Variable(
        name="seed",
        description="Master pseudo-random generator seed governing determinism",
        type=VariableType.INT,
        role=VariableRole.CONTROLLED,
        default=42,
        minimum=0,
        maximum=2_147_483_647,
        unit="seed",
        target_layer="meta",
    ),
    # Dependent Variables (Observed Metrics)
    "recall_accuracy": Variable(
        name="recall_accuracy",
        description="Fraction of queries whose readout matches ground-truth symbol label",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=1.0,
        unit="fraction",
        target_layer="metric",
    ),
    "recall_quality": Variable(
        name="recall_quality",
        description="Mean cosine similarity between predicted vector and true value vector",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=-1.0,
        maximum=1.0,
        unit="cosine",
        target_layer="metric",
    ),
    "memory_retention": Variable(
        name="memory_retention",
        description="Mean quality of the final latest query across all stored concepts",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=-1.0,
        maximum=1.0,
        unit="cosine",
        target_layer="metric",
    ),
    "interference_score": Variable(
        name="interference_score",
        description="Cross-talk or superseded binding leakage contaminating recall readouts",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=2.0,
        unit="score",
        target_layer="metric",
    ),
    "recovery_score": Variable(
        name="recovery_score",
        description="Ratio of final quality to immediate post-conflict write quality (>1 strengthens, <1 erodes)",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=10.0,
        unit="ratio",
        target_layer="metric",
    ),
    "state_drift": Variable(
        name="state_drift",
        description="Mean directional change (1 - cosine) between consecutive state snapshots",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=2.0,
        unit="angular",
        target_layer="metric",
    ),
    "update_magnitude": Variable(
        name="update_magnitude",
        description="Mean L2 norm of state displacement vectors per update step",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=100.0,
        unit="L2 norm",
        target_layer="metric",
    ),
    "error_rate": Variable(
        name="error_rate",
        description="1 - recall_accuracy",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=1.0,
        unit="fraction",
        target_layer="metric",
    ),
    "mean_squared_error": Variable(
        name="mean_squared_error",
        description="Mean squared Euclidean distance ||v_hat - v_true||^2 over queries",
        type=VariableType.FLOAT,
        role=VariableRole.DEPENDENT,
        default=0.0,
        minimum=0.0,
        maximum=10.0,
        unit="MSE",
        target_layer="metric",
    ),
}


class VariableRegistry:
    """Registry maintaining known variables and providing lookup and validation."""

    def __init__(self, initial: Optional[Dict[str, Variable]] = None) -> None:
        self._vars: Dict[str, Variable] = dict(initial or _BUILTIN_VARIABLES)

    def get(self, name: str) -> Optional[Variable]:
        return self._vars.get(name)

    def register(self, var: Variable) -> None:
        self._vars[var.name] = var

    def list_all(self) -> List[Variable]:
        return list(self._vars.values())

    def list_by_role(self, role: VariableRole) -> List[Variable]:
        return [v for v in self._vars.values() if v.role == role]

    def validate_variable(self, name: str, value: Any) -> tuple[bool, Optional[str]]:
        var = self.get(name)
        if var is None:
            # allow custom unmodeled variables if type matches basic scalars
            if not isinstance(value, (int, float, str, bool)):
                return False, f"Unknown variable '{name}' must have scalar value"
            return True, None
        return var.validate_value(value)


VARIABLE_REGISTRY = VariableRegistry()


def get_variable(name: str) -> Optional[Variable]:
    """Retrieve variable metadata from the standard registry."""
    return VARIABLE_REGISTRY.get(name)


def validate_variable_value(name: str, value: Any) -> tuple[bool, Optional[str]]:
    """Convenience helper to validate a value against the registry."""
    return VARIABLE_REGISTRY.validate_variable(name, value)
