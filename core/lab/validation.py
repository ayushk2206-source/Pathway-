"""Validation and resource limits for the Experiment Lab (Phase 03).

Enforces scientific safety constraints, parameter range checking, incompatible
setting detection, and computational resource quotas before any experiment runs.
Never silently clamps or truncates invalid requests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from ..mechanisms import MECHANISM_REGISTRY
from .variables import VARIABLE_REGISTRY, VariableRole

# ---------------------------------------------------------------------------
# Strict Resource Limits
# ---------------------------------------------------------------------------
MAX_TRIALS: int = 100
MAX_PARAMETER_COMBINATIONS: int = 144
MAX_STATE_DIMENSION: int = 1024
MAX_SEQUENCE_LENGTH: int = 500
MAX_GRID_DIMENSION: int = 24  # max points along any single grid axis


class ExperimentValidationError(ValueError):
    """Raised when an experimental design fails pre-flight validation."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "error_count": len(self.errors),
        }


class ExperimentValidator:
    """Validates lab experiments and parameter configurations before execution."""

    @classmethod
    def validate_variable_value(cls, name: str, value: Any) -> Optional[str]:
        valid, err = VARIABLE_REGISTRY.validate_variable(name, value)
        return err if not valid else None

    @classmethod
    def validate_parameter_sweep(
        cls,
        parameter: str,
        values: Sequence[Any],
        base_params: Optional[Dict[str, Any]] = None,
        trials: int = 1,
    ) -> ValidationResult:
        errors: List[str] = []

        if not parameter or not isinstance(parameter, str):
            errors.append("Parameter name must be a non-empty string")
            return ValidationResult(valid=False, errors=errors)

        if not values or len(values) == 0:
            errors.append("Sweep values list cannot be empty")
        elif len(values) > MAX_PARAMETER_COMBINATIONS:
            errors.append(
                f"Sweep values count ({len(values)}) exceeds maximum limit of {MAX_PARAMETER_COMBINATIONS}"
            )

        # Validate trials
        if trials < 1:
            errors.append(f"Trials must be >= 1, got {trials}")
        elif trials > MAX_TRIALS:
            errors.append(f"Trials ({trials}) exceeds maximum allowed ({MAX_TRIALS})")

        total_runs = len(values) * max(1, trials)
        if total_runs > (MAX_PARAMETER_COMBINATIONS * MAX_TRIALS):
            errors.append(
                f"Total experiment executions ({total_runs}) exceeds safety quota"
            )

        # Validate each sweep value
        for i, val in enumerate(values):
            err = cls.validate_variable_value(parameter, val)
            if err:
                errors.append(f"Value at index {i} ({val!r}): {err}")

        # Validate base params if provided
        if base_params:
            for k, v in base_params.items():
                if k != parameter:
                    err = cls.validate_variable_value(k, v)
                    if err:
                        errors.append(f"Base parameter '{k}' ({v!r}): {err}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    @classmethod
    def validate_grid_sweep(
        cls,
        param_x: str,
        values_x: Sequence[Any],
        param_y: str,
        values_y: Sequence[Any],
        trials: int = 1,
    ) -> ValidationResult:
        errors: List[str] = []

        if param_x == param_y:
            errors.append(f"Grid sweep requires two distinct parameters, got '{param_x}' for both")

        if not values_x or len(values_x) == 0:
            errors.append(f"Grid values for '{param_x}' cannot be empty")
        elif len(values_x) > MAX_GRID_DIMENSION:
            errors.append(f"Grid values count for '{param_x}' ({len(values_x)}) exceeds axis limit ({MAX_GRID_DIMENSION})")

        if not values_y or len(values_y) == 0:
            errors.append(f"Grid values for '{param_y}' cannot be empty")
        elif len(values_y) > MAX_GRID_DIMENSION:
            errors.append(f"Grid values count for '{param_y}' ({len(values_y)}) exceeds axis limit ({MAX_GRID_DIMENSION})")

        total_cells = len(values_x) * len(values_y)
        if total_cells > MAX_PARAMETER_COMBINATIONS:
            errors.append(
                f"Grid cells count ({total_cells} = {len(values_x)}x{len(values_y)}) exceeds maximum allowed ({MAX_PARAMETER_COMBINATIONS})"
            )

        if trials < 1 or trials > MAX_TRIALS:
            errors.append(f"Trials must be between 1 and {MAX_TRIALS}, got {trials}")

        for i, vx in enumerate(values_x):
            err = cls.validate_variable_value(param_x, vx)
            if err:
                errors.append(f"X-axis value [{i}] ({vx!r}): {err}")

        for j, vy in enumerate(values_y):
            err = cls.validate_variable_value(param_y, vy)
            if err:
                errors.append(f"Y-axis value [{j}] ({vy!r}): {err}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    @classmethod
    def validate_lab_experiment(cls, data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []

        # Required text fields
        title = data.get("title")
        if not title or not str(title).strip():
            errors.append("Experiment title is required")

        question = data.get("research_question")
        if not question or not str(question).strip():
            errors.append("Research question is required")

        # Mechanism validation
        mechanism = data.get("mechanism", "leaky")
        if mechanism not in MECHANISM_REGISTRY:
            errors.append(
                f"Unknown mechanism '{mechanism}'. Available: {sorted(MECHANISM_REGISTRY)}"
            )

        # Trials check
        trials = data.get("trials", 1)
        if not isinstance(trials, int) or trials < 1 or trials > MAX_TRIALS:
            errors.append(f"Trials must be an integer between 1 and {MAX_TRIALS}, got {trials}")

        # Variables checking
        indep = data.get("independent_variables", [])
        if not isinstance(indep, list):
            errors.append("independent_variables must be a list")

        # Check parameter combination bounds
        treatments = data.get("treatment_configurations", [])
        if len(treatments) > MAX_PARAMETER_COMBINATIONS:
            errors.append(
                f"Treatment configurations count ({len(treatments)}) exceeds limit of {MAX_PARAMETER_COMBINATIONS}"
            )

        # Check state dimension if specified
        ctrls = data.get("controlled_variables", {})
        if isinstance(ctrls, dict):
            sdim = ctrls.get("state_dim")
            if sdim is not None:
                try:
                    sdim_int = int(sdim)
                    if sdim_int < 8 or sdim_int > MAX_STATE_DIMENSION:
                        errors.append(
                            f"state_dim must be between 8 and {MAX_STATE_DIMENSION}, got {sdim_int}"
                        )
                except (ValueError, TypeError):
                    errors.append(f"state_dim must be an integer, got {sdim!r}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
