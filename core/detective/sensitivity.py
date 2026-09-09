"""Minimum intervention search, sensitivity analysis, and robustness testing (Phase 07)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core.counterfactual.interventions import (
    create_modify_intervention,
    create_remove_intervention,
)
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import ReplayStrategy
from core.experiment import Experiment
from core.xray.strength import _extract_memory_cues, compute_memory_strengths
from .models import MinimumIntervention, RobustnessEvaluation, SensitivityRecord


def _get_event_id(ev: Any, default: str = "") -> str:
    if hasattr(ev, "id"):
        return str(ev.id)
    if isinstance(ev, dict):
        return str(ev.get("id") or default)
    return default


class SensitivityEngine:
    """Explores minimum interventions, perturbation sensitivity, and robustness."""

    @classmethod
    def _resolve_profile(cls, strengths_map: Dict[str, Any], memory_id: str):
        prof = strengths_map.get(memory_id)
        if prof:
            return prof
        for k, p in strengths_map.items():
            c_lbl = getattr(p, "concept_label", "")
            if memory_id.lower() in c_lbl.lower() or memory_id.lower() in k.lower():
                return p
        return next(iter(strengths_map.values()), None)

    @classmethod
    def find_minimum_intervention(
        cls,
        experiment: Experiment,
        target_memory_id: str,
        threshold_delta: float = 0.04,
    ) -> MinimumIntervention:
        """Search incrementally for the smallest intervention that alters target memory outcome."""
        orig_strengths = compute_memory_strengths(experiment)
        orig_prof = cls._resolve_profile(orig_strengths, target_memory_id)
        base_val = orig_prof.final_strength if orig_prof else 0.5

        events = experiment.events
        if len(events) < 2:
            return MinimumIntervention(
                target_memory=target_memory_id,
                target_outcome=f"Change strength by ≥ {threshold_delta:.3f}",
                smallest_intervention_type="none_available",
                parameter_threshold=0.0,
                effect_size=0.0,
            )

        # Candidate event: find second or third event
        target_ev_idx = min(1, len(events) - 1)
        target_ev = events[target_ev_idx]
        target_ev_id = _get_event_id(target_ev, f"e{target_ev_idx:04d}")

        # Ladder 1: Scale update strength of target event from 0.8 down to 0.0
        scale_steps = [0.8, 0.6, 0.4, 0.2, 0.0]
        for scale in scale_steps:
            intv = create_modify_intervention(
                modifications={"strength": scale},
                target_timestep=target_ev_idx,
                target_event_id=target_ev_id,
                description=f"Minimum intervention probe: scale strength={scale}",
            )
            try:
                cf = run_counterfactual(experiment, intv, strategy=ReplayStrategy.FULL_REPLAY)
                cf_strengths = compute_memory_strengths(cf.to_experiment())
                cf_prof = cls._resolve_profile(cf_strengths, target_memory_id)
                new_val = cf_prof.final_strength if cf_prof else base_val
                delta = abs(new_val - base_val)

                if delta >= threshold_delta:
                    return MinimumIntervention(
                        target_memory=target_memory_id,
                        target_outcome=f"Altered representation strength by {delta:.4f} (threshold: {threshold_delta:.3f})",
                        smallest_intervention_type="scale_update_strength",
                        parameter_threshold=scale,
                        effect_size=float(delta),
                        intervention_details={
                            "target_event_id": target_ev_id,
                            "scale": scale,
                            "original_strength": base_val,
                            "counterfactual_strength": new_val,
                        },
                    )
            except Exception:
                continue

        # Ladder 2: Single event removal
        try:
            rm_intv = create_remove_intervention(
                target_timestep=target_ev_idx,
                target_event_id=target_ev_id,
                description=f"Minimum intervention fallback: remove event {target_ev_id}",
            )
            cf = run_counterfactual(experiment, rm_intv, strategy=ReplayStrategy.FULL_REPLAY)
            cf_strengths = compute_memory_strengths(cf.to_experiment())
            cf_prof = cls._resolve_profile(cf_strengths, target_memory_id)
            new_val = cf_prof.final_strength if cf_prof else base_val
            delta = abs(new_val - base_val)

            return MinimumIntervention(
                target_memory=target_memory_id,
                target_outcome=f"Altered representation strength by {delta:.4f} via event removal",
                smallest_intervention_type="remove_event",
                parameter_threshold=1.0,
                effect_size=float(delta),
                intervention_details={
                    "target_event_id": target_ev_id,
                    "original_strength": base_val,
                    "counterfactual_strength": new_val,
                },
            )
        except Exception:
            pass

        return MinimumIntervention(
            target_memory=target_memory_id,
            target_outcome=f"Change strength by ≥ {threshold_delta:.3f}",
            smallest_intervention_type="unreachable",
            parameter_threshold=0.0,
            effect_size=0.0,
        )

    @classmethod
    def measure_sensitivity(
        cls,
        experiment: Experiment,
        target_memory_id: str,
        target_event_id: str,
    ) -> SensitivityRecord:
        """Measure how sensitive a target memory is to perturbations of a specific event."""
        orig_strengths = compute_memory_strengths(experiment)
        orig_prof = cls._resolve_profile(orig_strengths, target_memory_id)
        base_val = orig_prof.final_strength if orig_prof else 0.5

        # Find event step
        ev_step = 0
        for i, ev in enumerate(experiment.events):
            if _get_event_id(ev, f"e{i:04d}") == target_event_id:
                ev_step = i
                break

        intv = create_modify_intervention(
            modifications={"strength": 0.5},
            target_timestep=ev_step,
            target_event_id=target_event_id,
            description=f"Sensitivity perturbation on {target_event_id}",
        )

        try:
            cf = run_counterfactual(experiment, intv, strategy=ReplayStrategy.FULL_REPLAY)
            cf_strengths = compute_memory_strengths(cf.to_experiment())
            cf_prof = cls._resolve_profile(cf_strengths, target_memory_id)
            new_val = cf_prof.final_strength if cf_prof else base_val
            effect_size = new_val - base_val

            # Count downstream affected memories
            downstream = 0
            for k, p in cf_strengths.items():
                if k != target_memory_id and k in orig_strengths:
                    if abs(p.final_strength - orig_strengths[k].final_strength) > 0.02:
                        downstream += 1

            direction = "positive" if effect_size > 0.01 else ("negative" if effect_size < -0.01 else "neutral")

            return SensitivityRecord(
                memory_id=target_memory_id,
                perturbation=f"50% write attenuation at {target_event_id}",
                interfering_event_id=target_event_id,
                effect_size=float(effect_size),
                direction=direction,
                isolated_cause=bool(abs(effect_size) > 0.05 and downstream <= 1),
                downstream_affected_count=downstream,
                counterfactual_tested=True,
            )
        except Exception:
            return SensitivityRecord(
                memory_id=target_memory_id,
                perturbation=f"50% write attenuation at {target_event_id}",
                interfering_event_id=target_event_id,
                effect_size=0.0,
                direction="neutral",
                isolated_cause=False,
                downstream_affected_count=0,
                counterfactual_tested=False,
            )

    @classmethod
    def evaluate_robustness(
        cls,
        experiment: Experiment,
        target_memory_id: str,
        num_variations: int = 3,
    ) -> RobustnessEvaluation:
        """Evaluate outcome stability across controlled variations."""
        orig_strengths = compute_memory_strengths(experiment)
        orig_prof = cls._resolve_profile(orig_strengths, target_memory_id)
        base_val = orig_prof.final_strength if orig_prof else 0.5

        variations_tested = 0
        persisted_count = 0
        deltas: List[float] = []

        scales = [0.95, 0.90, 0.85][:num_variations]
        for scale in scales:
            if len(experiment.events) > 1:
                intv = create_modify_intervention(
                    modifications={"strength": scale},
                    target_timestep=1,
                    target_event_id=_get_event_id(experiment.events[1], "e0001"),
                    description=f"Robustness probe scale={scale}",
                )
                try:
                    cf = run_counterfactual(experiment, intv, strategy=ReplayStrategy.FULL_REPLAY)
                    cf_strengths = compute_memory_strengths(cf.to_experiment())
                    cf_prof = cls._resolve_profile(cf_strengths, target_memory_id)
                    new_val = cf_prof.final_strength if cf_prof else base_val
                    diff = abs(new_val - base_val)
                    deltas.append(diff)
                    variations_tested += 1
                    if diff < 0.05:
                        persisted_count += 1
                except Exception:
                    continue

        if not variations_tested:
            return RobustnessEvaluation(
                memory_id=target_memory_id,
                classification="inconclusive",
                variations_tested=0,
                variance=0.0,
                persistence_rate=0.0,
            )

        variance = float(np.var(deltas)) if deltas else 0.0
        persist_rate = persisted_count / variations_tested

        if persist_rate >= 0.80 and variance < 0.005:
            classification = "stable"
        elif persist_rate >= 0.50:
            classification = "sensitive"
        else:
            classification = "unstable"

        return RobustnessEvaluation(
            memory_id=target_memory_id,
            classification=classification,
            variations_tested=variations_tested,
            variance=variance,
            persistence_rate=float(persist_rate),
        )

    test_robustness = evaluate_robustness
