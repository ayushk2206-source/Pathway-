"""Section 2/16 -- Causal Scenario Builder + CausalScenarioCompiler (Phase 10).

Translates a (target, intervention, timing, strength, duration) request from the
UI into a concrete, validated ``core.counterfactual.Intervention`` that the
existing Phase 04 replay engine can execute. No new replay mechanism is
introduced here -- this module only *compiles* scenarios into the primitives
that already exist.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core import Experiment
from core.counterfactual.interventions import (
    Intervention,
    create_change_similarity_intervention,
    create_change_strength_intervention,
    create_duplicate_intervention,
    create_freeze_memory_intervention,
    create_inject_memory_intervention,
    create_modify_intervention,
    create_move_intervention,
    create_remove_intervention,
    create_replace_intervention,
)
from core.genome.genome import resolve_memory

from .models import CausalCostEstimate, CausalScenario, ScenarioValidation
from .types import CausalInterventionType, CausalScenarioValidationError


class CausalScenarioCompiler:
    """Validates a CausalScenario and compiles it into an executable Intervention."""

    @classmethod
    def validate(cls, experiment: Experiment, scenario: CausalScenario) -> ScenarioValidation:
        errors = []
        warnings = []

        target = resolve_memory(experiment, scenario.target_memory) if scenario.target_memory else None
        target_clean = scenario.target_memory.strip().lower() if scenario.target_memory else ""
        matched = False
        if target and target_clean:
            matched = (
                target_clean == target["memory_id"].lower()
                or target_clean == target["concept_label"].lower()
                or target_clean in target["concept_label"].lower()
                or target_clean in target["memory_id"].lower()
            )
        if scenario.intervention != CausalInterventionType.ADD and (not target or not matched):
            errors.append(f"Target memory '{scenario.target_memory}' does not exist in this experiment.")

        n_events = len(experiment.events)
        if scenario.timing is not None and not (0 <= scenario.timing < max(n_events, 1)):
            errors.append(f"Timing t={scenario.timing} is out of bounds for a {n_events}-event timeline.")

        if scenario.duration is not None and scenario.duration < 0:
            errors.append("Duration must be non-negative.")

        if not (0.0 <= scenario.strength <= 10.0):
            errors.append("Strength must be within [0.0, 10.0].")

        if scenario.intervention == CausalInterventionType.REPLACE and target is None:
            warnings.append("REPLACE without an existing target will fall back to the first available memory.")

        cost = cls.estimate_cost(experiment)
        valid = len(errors) == 0
        return ScenarioValidation(valid=valid, errors=errors, warnings=warnings, cost_estimate=cost)

    @classmethod
    def estimate_cost(cls, experiment: Experiment, runs_required: int = 1) -> CausalCostEstimate:
        n_events = max(1, len(experiment.events))
        d = int(experiment.task.get("d", 128)) if isinstance(experiment.task, dict) else 128
        compute_units = round((n_events * d) / 10000.0 * runs_required, 4)
        memory_mb = round((n_events * d * 8) / (1024 * 1024) * runs_required, 4)
        # Empirically full replays of this substrate's demo-sized experiments take well
        # under a second each on commodity hardware; this is a conservative proxy, not
        # a live profiler measurement.
        time_seconds = round(0.02 * n_events * runs_required, 4)
        within_budget = runs_required <= 32 and compute_units < 500
        return CausalCostEstimate(
            runs_required=runs_required,
            estimated_compute_units=compute_units,
            estimated_memory_mb=memory_mb,
            estimated_time_seconds=time_seconds,
            within_budget=within_budget,
            notes="Proxy estimate derived from event count x state dimension; not a live profiler measurement.",
        )

    @classmethod
    def compile(cls, experiment: Experiment, scenario: CausalScenario) -> Intervention:
        """Compile a validated scenario into a concrete Intervention."""
        validation = cls.validate(experiment, scenario)
        if not validation.valid:
            raise CausalScenarioValidationError("; ".join(validation.errors))

        target = resolve_memory(experiment, scenario.target_memory) if scenario.target_memory else None
        target_id = target["memory_id"] if target else None
        origin_step = int(target["timestep"]) if target else max(0, len(experiment.events) - 1)
        concept_label = target["concept_label"] if target else "injected_concept"

        itype = scenario.intervention
        strength = scenario.strength
        duration = scenario.duration if scenario.duration is not None else 5
        timing = scenario.timing if scenario.timing is not None else origin_step

        if itype == CausalInterventionType.REMOVE:
            return create_remove_intervention(
                target_event_id=target_id,
                description=f"Causal Lab: REMOVE {concept_label}",
            )

        if itype == CausalInterventionType.ADD:
            return create_inject_memory_intervention(
                timestep=timing,
                concept_label=f"{concept_label}_causal_add",
                attribute_label=target.get("concept_label", "value") if target else "value",
                strength=strength,
                description=f"Causal Lab: ADD variant of {concept_label} at t={timing}",
            )

        if itype == CausalInterventionType.STRENGTHEN:
            return create_modify_intervention(
                target_event_id=target_id,
                modifications={"strength": max(strength, 1.0) * 1.5 if strength <= 1.0 else strength},
                description=f"Causal Lab: STRENGTHEN {concept_label}",
            )

        if itype == CausalInterventionType.WEAKEN:
            scale = strength if 0.0 < strength < 1.0 else 0.3
            return create_modify_intervention(
                target_event_id=target_id,
                modifications={"strength": scale},
                description=f"Causal Lab: WEAKEN {concept_label} to {scale:.2f}x",
            )

        if itype == CausalInterventionType.DELAY:
            dest = min(len(experiment.events) - 1, origin_step + duration)
            return create_move_intervention(
                target_event_id=target_id,
                destination_timestep=dest,
                description=f"Causal Lab: DELAY {concept_label} to t={dest}",
            )

        if itype == CausalInterventionType.ACCELERATE:
            dest = max(0, origin_step - duration)
            return create_move_intervention(
                target_event_id=target_id,
                destination_timestep=dest,
                description=f"Causal Lab: ACCELERATE {concept_label} to t={dest}",
            )

        if itype == CausalInterventionType.FREEZE:
            end = min(len(experiment.events) - 1, timing + duration)
            return create_freeze_memory_intervention(
                start_timestep=timing,
                end_timestep=end,
                description=f"Causal Lab: FREEZE substrate updates [{timing}, {end}]",
            )

        if itype == CausalInterventionType.RESTORE:
            return create_change_strength_intervention(
                new_strength=max(strength, 1.0),
                target_event_id=target_id,
                description=f"Causal Lab: RESTORE {concept_label} to full strength",
            )

        if itype == CausalInterventionType.DUPLICATE:
            return create_duplicate_intervention(
                target_event_id=target_id,
                description=f"Causal Lab: DUPLICATE {concept_label}",
            )

        if itype == CausalInterventionType.REPLACE:
            replacement = scenario_replacement_spec(scenario, concept_label)
            return create_replace_intervention(
                replacement_spec=replacement,
                target_event_id=target_id,
                description=f"Causal Lab: REPLACE {concept_label}",
            )

        if itype == CausalInterventionType.ISOLATE:
            return create_change_similarity_intervention(
                delta_similarity=-abs(strength if strength <= 1.0 else 0.3),
                target_event_id=target_id,
                description=f"Causal Lab: ISOLATE {concept_label} from competing cues",
            )

        raise CausalScenarioValidationError(f"Unsupported causal intervention type: {itype}")


def scenario_replacement_spec(scenario: CausalScenario, concept_label: str) -> Dict[str, Any]:
    """Build a REPLACE_EVENT replacement_spec, defaulting to a clearly-labeled synthetic swap target."""
    return {
        "concept_label": f"{concept_label}_replacement",
        "attribute_label": "synthetic_replacement_value",
        "strength": scenario.strength if scenario.strength else 1.0,
        "importance": 1.0,
    }
