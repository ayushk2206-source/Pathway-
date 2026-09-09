"""Memory Autopsy, Birth/Death records, and Survival/Failure profiles (Phase 07).

Answers the signature investigative questions:
- How was this memory formed?
- How was it reinforced?
- What competed with it?
- When did it weaken?
- What kept it alive?
- What happens if it is removed?
- What evidence supports each answer?
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core.counterfactual.interventions import create_remove_intervention
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import ReplayStrategy
from core.experiment import Experiment
from core.vectors import cosine
from core.xray.competition import build_competition_graph
from core.xray.interference import detect_interference
from core.xray.reinforcement import detect_reinforcement
from core.xray.strength import _extract_memory_cues, compute_memory_strengths
from .models import MemoryAutopsy, MemoryBirthRecord, MemoryDeathRecord


def _get_event_id(ev: Any, default: str = "") -> str:
    if hasattr(ev, "id"):
        return str(ev.id)
    if isinstance(ev, dict):
        return str(ev.get("id") or default)
    return default


class MemoryAutopsyEngine:
    """Computes comprehensive forensic life-cycle autopsies and birth/death profiles."""

    @classmethod
    def _find_memory(cls, experiment: Experiment, memory_id: str) -> Optional[Dict[str, Any]]:
        memories = _extract_memory_cues(experiment)
        for m in memories:
            if (
                m["memory_id"] == memory_id
                or m["concept_label"].lower() == memory_id.lower()
                or memory_id.lower() in m["concept_label"].lower()
            ):
                return m
        return memories[0] if memories else None

    @classmethod
    def get_birth_record(cls, experiment: Experiment, memory_id: str) -> MemoryBirthRecord:
        mem = cls._find_memory(experiment, memory_id)
        if not mem:
            return MemoryBirthRecord(
                memory_id=memory_id,
                concept_label="unknown",
                first_appearance_step=0,
                first_event_id="e0000",
                initial_strength=0.0,
                initial_state_norm=0.0,
            )

        m_id = mem["memory_id"]
        c_label = mem["concept_label"]
        step = mem["timestep"]
        ev_id = _get_event_id(experiment.events[step], f"e{step:04d}") if step < len(experiment.events) else "e0000"

        strengths_map = compute_memory_strengths(experiment)
        prof = strengths_map.get(m_id)
        init_str = prof.initial_strength if prof else 0.5
        traj = getattr(prof, "timeline_strengths", getattr(prof, "strength_history", [])) if prof else []

        snap = experiment.snapshots[min(step + 1, len(experiment.snapshots) - 1)]
        s_vec = snap.get("state_vector", [])
        init_norm = float(np.linalg.norm(s_vec)) if len(s_vec) > 0 else 1.0

        # Find early associations & competitors
        all_mems = _extract_memory_cues(experiment)
        associations = []
        competitors = []

        for other in all_mems:
            if other["memory_id"] == m_id:
                continue
            sim = float(cosine(mem["key_vector"], other["key_vector"]))
            if sim > 0.35:
                competitors.append(f"{other['concept_label']} (sim={sim:.2f})")
            elif sim > 0.15:
                associations.append(f"{other['concept_label']} (sim={sim:.2f})")

        return MemoryBirthRecord(
            memory_id=m_id,
            concept_label=c_label,
            first_appearance_step=step + 1,
            first_event_id=ev_id,
            initial_strength=float(init_str),
            initial_state_norm=float(init_norm),
            early_associations=associations[:4],
            early_competitors=competitors[:4],
            trajectory_preview=[float(x) for x in traj[:6]],
        )

    @classmethod
    def get_death_record(cls, experiment: Experiment, memory_id: str) -> MemoryDeathRecord:
        mem = cls._find_memory(experiment, memory_id)
        m_id = mem["memory_id"] if mem else memory_id
        c_label = mem["concept_label"] if mem else "unknown"

        strengths_map = compute_memory_strengths(experiment)
        prof = strengths_map.get(m_id)

        history = getattr(prof, "timeline_strengths", getattr(prof, "strength_history", [0.5])) if prof else [0.5]
        peak_str = prof.peak_strength if prof else 0.5
        final_str = prof.final_strength if prof else 0.5

        # Find last strong step (strength >= 0.35 or >= 0.7 * peak)
        threshold = max(0.25, peak_str * 0.5)
        last_strong_idx = 0
        loss_idx = len(history) - 1

        for idx, val in enumerate(history):
            if val >= threshold:
                last_strong_idx = idx
            elif last_strong_idx > 0 and loss_idx == len(history) - 1:
                loss_idx = idx

        events = experiment.events
        decline_evs = []
        for i in range(last_strong_idx, min(loss_idx + 2, len(events))):
            decline_evs.append(_get_event_id(events[i], f"e{i:04d}"))

        interferences = detect_interference(experiment)
        dominant_comp = "passive_temporal_decay"
        for rec in interferences:
            target_a = getattr(rec, "target_memory_id", getattr(rec, "memory_a", ""))
            comp_b = getattr(rec, "competing_memory_id", getattr(rec, "memory_b", ""))
            ev_id = getattr(rec, "event_id", "")
            if target_a == m_id:
                dominant_comp = f"competing write by {comp_b}" + (f" (event {ev_id})" if ev_id else "")
                break

        return MemoryDeathRecord(
            memory_id=m_id,
            concept_label=c_label,
            last_strong_step=last_strong_idx + 1,
            last_strong_strength=float(history[last_strong_idx]),
            effective_loss_step=loss_idx + 1,
            final_strength=float(final_str),
            decline_events=decline_evs[:4],
            dominant_contributor=dominant_comp,
            counterfactual_survival_possible=final_str < 0.30 and len(decline_evs) > 0,
            evidence=(
                f"Representation dropped below readout threshold {threshold:.2f} at step {loss_idx + 1}. "
                f"Dominant degrading factor: {dominant_comp}."
            ),
        )

    @classmethod
    def get_survival_analysis(cls, experiment: Experiment, memory_id: str) -> Dict[str, Any]:
        mem = cls._find_memory(experiment, memory_id)
        m_id = mem["memory_id"] if mem else memory_id
        strengths_map = compute_memory_strengths(experiment)
        prof = strengths_map.get(m_id)
        final_val = prof.final_strength if prof else 0.5

        all_mems = _extract_memory_cues(experiment)
        max_sim = 0.0
        for o in all_mems:
            if mem and o["memory_id"] != m_id:
                sim = float(cosine(mem["key_vector"], o["key_vector"]))
                if sim > max_sim:
                    max_sim = sim

        isolation_index = max(0.0, 1.0 - max_sim)
        reinf = detect_reinforcement(experiment)
        m_reinf = [r for r in reinf if r.memory_id == m_id]

        factors = []
        if isolation_index > 0.6:
            factors.append(f"High representational isolation (isolation index: {isolation_index:.2f}).")
        if m_reinf:
            factors.append(f"Received {len(m_reinf)} periodic reinforcement write(s).")
        if final_val > 0.4:
            factors.append(f"Robust circular convolution binding (final readout: {final_val:.3f}).")

        return {
            "memory_id": m_id,
            "final_strength": float(final_val),
            "isolation_index": float(isolation_index),
            "reinforcement_count": len(m_reinf),
            "survival_factors": factors,
            "is_surviving": final_val >= 0.25,
        }

    @classmethod
    def get_failure_analysis(cls, experiment: Experiment, memory_id: str) -> Dict[str, Any]:
        mem = cls._find_memory(experiment, memory_id)
        m_id = mem["memory_id"] if mem else memory_id
        strengths_map = compute_memory_strengths(experiment)
        prof = strengths_map.get(m_id)
        drop = (prof.peak_strength - prof.final_strength) if prof else 0.0

        interferences = detect_interference(experiment)
        relevant_intf = [
            r for r in interferences
            if getattr(r, "memory_a", "") == m_id or getattr(r, "target_memory_id", "") == m_id
        ]

        failure_causes = []
        if relevant_intf:
            failure_causes.append(
                f"Direct cross-talk interference from {len(relevant_intf)} conflicting write event(s)."
            )
        if experiment.parameters.get("decay", 0.0) > 0.1:
            failure_causes.append(
                f"Continuous exponential decay with parameter λ = {experiment.parameters.get('decay')}."
            )
        if drop > 0.3:
            failure_causes.append(f"Severe representational drop (-{drop:.3f}) following sequence writes.")

        return {
            "memory_id": m_id,
            "strength_drop": float(drop),
            "conflicting_writes_count": len(relevant_intf),
            "failure_causes": failure_causes,
            "is_failed": (prof.final_strength if prof else 0.5) < 0.25,
        }

    @classmethod
    def perform_autopsy(cls, experiment: Experiment, memory_id: str) -> MemoryAutopsy:
        mem = cls._find_memory(experiment, memory_id)
        m_id = mem["memory_id"] if mem else memory_id
        c_label = mem["concept_label"] if mem else "unknown"

        strengths_map = compute_memory_strengths(experiment)
        prof = strengths_map.get(m_id)
        history = getattr(prof, "timeline_strengths", getattr(prof, "strength_history", [0.5])) if prof else [0.5]

        birth = cls.get_birth_record(experiment, m_id)
        survival = cls.get_survival_analysis(experiment, m_id)
        failure = cls.get_failure_analysis(experiment, m_id)

        # 1. Formation
        formation = {
            "concept_label": mem["concept_label"] if mem else target_memory_id,
            "appearance_step": birth.first_appearance_step,
            "event_id": birth.first_event_id,
            "initial_strength": birth.initial_strength,
            "initial_state_norm": birth.initial_state_norm,
        }

        # 2. Reinforcement
        reinf = detect_reinforcement(experiment)
        m_reinf = [r for r in reinf if getattr(r, "memory_id", "") == m_id]
        reinforcement_events = []
        boosts = []
        for r in m_reinf:
            evs = getattr(r, "reinforcement_events", getattr(r, "events", []))
            if isinstance(evs, list):
                reinforcement_events.extend([str(x) for x in evs])
            elif evs:
                reinforcement_events.append(str(evs))
            b = float(getattr(r, "net_change", getattr(r, "boost", 0.0)))
            boosts.append(b)

        reinforcement = {
            "count": len(m_reinf),
            "reinforcement_count": len(m_reinf),
            "events": reinforcement_events,
            "average_boost": float(np.mean(boosts)) if boosts else 0.0,
        }

        # 3. Competition
        all_mems = _extract_memory_cues(experiment)
        competitors = []
        for o in all_mems:
            if mem and o["memory_id"] != m_id:
                sim = float(cosine(mem["key_vector"], o["key_vector"]))
                if sim > 0.25:
                    competitors.append({
                        "memory_id": o["memory_id"],
                        "label": o["concept_label"],
                        "similarity": sim,
                    })
        competitors.sort(key=lambda c: c["similarity"], reverse=True)

        competition = {
            "competing_count": len(competitors),
            "competing_memories_count": len(competitors),
            "primary_competitor": competitors[0] if competitors else None,
            "all_competitors": competitors,
        }

        # 4. Weakening Inflection Point
        max_step_drop = 0.0
        inflection_step = 0
        for s in range(1, len(history)):
            d_s = history[s - 1] - history[s]
            if d_s > max_step_drop:
                max_step_drop = d_s
                inflection_step = s

        weakening = None
        if max_step_drop > 0.04:
            culprit_ev = (
                _get_event_id(experiment.events[inflection_step - 1], f"e{inflection_step:04d}")
                if 0 < inflection_step <= len(experiment.events)
                else f"step_{inflection_step}"
            )
            weakening = {
                "step": inflection_step,
                "drop_magnitude": float(max_step_drop),
                "culprit_event": culprit_ev,
                "pre_strength": float(history[inflection_step - 1]),
                "post_strength": float(history[inflection_step]),
            }

        # 5. Counterfactual Removal Impact (What happens if this memory is removed at birth?)
        removal_impact: Dict[str, Any] = {}
        try:
            birth_intv = create_remove_intervention(
                target_timestep=max(0, birth.first_appearance_step - 1),
                target_event_id=birth.first_event_id,
                description=f"Autopsy ablation of {m_id} at birth",
            )
            cf_record = run_counterfactual(
                experiment=experiment,
                intervention=birth_intv,
                strategy=ReplayStrategy.FULL_REPLAY,
            )
            div = cf_record.divergence
            step_val = div.get("first_divergence_step") if isinstance(div, dict) else getattr(div, "first_divergence_step", 0)
            dist_val = div.get("final_state_distance_l2", 0.0) if isinstance(div, dict) else getattr(div, "final_state_distance_l2", 0.0)
            removal_impact = {
                "counterfactual_tested": True,
                "first_divergence_step": step_val,
                "final_substrate_divergence_l2": float(dist_val or 0.0),
                "affected_memories_count": len(all_mems) - 1,
            }
        except Exception as exc:
            removal_impact = {
                "counterfactual_tested": False,
                "error": str(exc),
            }

        # Evidence collection
        supporting_evidence = [
            f"Formed at step {birth.first_appearance_step} with strength {birth.initial_strength:.3f}.",
            f"Encountered {len(competitors)} competitor(s) with max cosine similarity {competitors[0]['similarity']:.3f}."
            if competitors
            else "Encountered zero high-similarity competing vectors.",
        ]
        if weakening:
            supporting_evidence.append(
                f"Sharpest inflection occurred at step {weakening['step']} (-{weakening['drop_magnitude']:.3f}) "
                f"coinciding with {weakening['culprit_event']}."
            )
        if survival["survival_factors"]:
            supporting_evidence.extend(survival["survival_factors"])

        return MemoryAutopsy(
            memory_id=m_id,
            concept_label=c_label,
            formation=formation,
            reinforcement=reinforcement,
            competition=competition,
            weakening_inflection=weakening,
            survival_factors=survival["survival_factors"],
            counterfactual_removal_impact=removal_impact,
            failure_profile=failure,
            survival_profile=survival,
            supporting_evidence=supporting_evidence,
        )
