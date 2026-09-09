"""Measurable observation builder (Phase 07).

Collects real, quantified experimental facts before generating any hypotheses.
Strictly displays OBSERVED, never EXPLAINED.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core.experiment import Experiment
from core.vectors import cosine
from core.xray.anomalies import detect_state_anomalies
from core.xray.competition import build_competition_graph
from core.xray.interference import detect_interference
from core.xray.strength import _extract_memory_cues, compute_memory_strengths
from .models import MeasurableObservation


class ObservationBuilder:
    """Extracts verifiable numerical facts from experimental memory history."""

    @classmethod
    def extract_observations(
        cls,
        experiment: Experiment,
        target_memory_id: Optional[str] = None,
        target_event_id: Optional[str] = None,
    ) -> List[MeasurableObservation]:
        """Collect measurable observations for a target memory or event."""
        observations: List[MeasurableObservation] = []

        memories = _extract_memory_cues(experiment)
        if not memories:
            return observations

        strengths_map = compute_memory_strengths(experiment)
        interferences = detect_interference(experiment)
        anomalies = detect_state_anomalies(experiment)

        # 1. Resolve Target Memory
        target_mem = None
        if target_memory_id:
            # match by id or concept label
            for m in memories:
                if (
                    m["memory_id"] == target_memory_id
                    or m["concept_label"].lower() == target_memory_id.lower()
                    or target_memory_id.lower() in m["concept_label"].lower()
                ):
                    target_mem = m
                    break

        if not target_mem:
            # Default to the memory with the largest degradation or interference
            max_drop = -1.0
            for m in memories:
                prof = strengths_map.get(m["memory_id"])
                if prof:
                    drop = prof.peak_strength - prof.final_strength
                    if drop > max_drop:
                        max_drop = drop
                        target_mem = m

        if not target_mem:
            target_mem = memories[0]

        target_id = target_mem["memory_id"]
        target_label = target_mem["concept_label"]
        prof = strengths_map.get(target_id)

        # -------------------------------------------------------------
        # Observation 1: Representation Strength Trajectory
        # -------------------------------------------------------------
        if prof:
            init_val = prof.initial_strength
            final_val = prof.final_strength
            delta = final_val - init_val

            # Find step with largest drop
            history = getattr(prof, "timeline_strengths", getattr(prof, "strength_history", []))
            max_step_drop = 0.0
            inflection_step = 0
            for s in range(1, len(history)):
                d_s = history[s - 1] - history[s]
                if d_s > max_step_drop:
                    max_step_drop = d_s
                    inflection_step = s

            # Find relevant event around inflection step
            events = experiment.events
            rel_events = []
            if 0 < inflection_step <= len(events):
                ev = events[inflection_step - 1]
                ev_id = getattr(ev, "id", None) or (ev.get("id") if isinstance(ev, dict) else None) or f"e{inflection_step:04d}"
                rel_events.append(str(ev_id))

            obs1 = MeasurableObservation(
                target_memory=target_id,
                metric_name="representation_strength",
                initial_value=float(init_val),
                final_value=float(final_val),
                delta=float(delta),
                relevant_events=rel_events,
                summary=(
                    f"Memory {target_label} ({target_id}) strength changed from "
                    f"{init_val:.3f} to {final_val:.3f} (Δ = {delta:+.3f}). "
                    f"Largest single-step drop occurred at step {inflection_step} (-{max_step_drop:.3f})."
                ),
                raw_data={
                    "peak_strength": prof.peak_strength,
                    "final_strength": prof.final_strength,
                    "decay_pattern": prof.pattern.value,
                    "strength_history": history,
                    "inflection_step": inflection_step,
                },
            )
            observations.append(obs1)

        # -------------------------------------------------------------
        # Observation 2: Competition & Cue Cross-Talk
        # -------------------------------------------------------------
        comp_memories: List[str] = []
        max_sim = 0.0
        conflicting_evs = []

        for rec in interferences:
            m_a = getattr(rec, "memory_a", getattr(rec, "target_memory_id", ""))
            m_b = getattr(rec, "memory_b", getattr(rec, "competing_memory_id", ""))
            sim = float(getattr(rec, "overlap", getattr(rec, "similarity", 0.0)))
            ev_id = getattr(rec, "event_id", "")

            if m_a == target_id:
                if m_b and m_b not in comp_memories:
                    comp_memories.append(m_b)
                if sim > max_sim:
                    max_sim = sim
                if ev_id and ev_id not in conflicting_evs:
                    conflicting_evs.append(ev_id)
            elif m_b == target_id:
                if m_a and m_a not in comp_memories:
                    comp_memories.append(m_a)
                if sim > max_sim:
                    max_sim = sim
                if ev_id and ev_id not in conflicting_evs:
                    conflicting_evs.append(ev_id)

        # If no explicit interference record found, compute pairwise cosine similarities
        if not comp_memories:
            for other in memories:
                if other["memory_id"] != target_id:
                    sim = float(cosine(target_mem["key_vector"], other["key_vector"]))
                    if sim > 0.2:
                        comp_memories.append(other["memory_id"])
                        if sim > max_sim:
                            max_sim = sim

        if comp_memories:
            obs2 = MeasurableObservation(
                target_memory=target_id,
                metric_name="cue_competition",
                initial_value=0.0,
                final_value=float(max_sim),
                delta=float(max_sim),
                relevant_events=conflicting_evs,
                competing_memories=comp_memories,
                cue_similarity=float(max_sim),
                summary=(
                    f"Memory {target_label} overlaps with {len(comp_memories)} competing cue(s) "
                    f"(max cosine similarity = {max_sim:.3f}). Active conflicting writes detected: {len(conflicting_evs)}."
                ),
                raw_data={
                    "competing_count": len(comp_memories),
                    "max_similarity": max_sim,
                    "interference_count": len(conflicting_evs),
                },
            )
            observations.append(obs2)

        # -------------------------------------------------------------
        # Observation 3: State Vector Transition Dynamics
        # -------------------------------------------------------------
        snapshots = experiment.snapshots
        if len(snapshots) >= 2:
            s0 = np.asarray(snapshots[0].get("state_vector", []), dtype=np.float64)
            s_final = np.asarray(snapshots[-1].get("state_vector", []), dtype=np.float64)

            init_norm = float(np.linalg.norm(s0)) if len(s0) > 0 else 0.0
            final_norm = float(np.linalg.norm(s_final)) if len(s_final) > 0 else 0.0
            cos_shift = float(1.0 - cosine(s0, s_final)) if len(s0) > 0 and len(s_final) > 0 else 0.0

            obs3 = MeasurableObservation(
                target_memory=target_id,
                metric_name="substrate_state_shift",
                initial_value=init_norm,
                final_value=final_norm,
                delta=float(final_norm - init_norm),
                state_shift=cos_shift,
                summary=(
                    f"Substrate state norm shifted from {init_norm:.3f} to {final_norm:.3f} "
                    f"(cumulative directional shift: {cos_shift:.3f})."
                ),
                raw_data={
                    "initial_norm": init_norm,
                    "final_norm": final_norm,
                    "cumulative_cosine_shift": cos_shift,
                },
            )
            observations.append(obs3)

        # -------------------------------------------------------------
        # Observation 4: Statistical Anomalies
        # -------------------------------------------------------------
        if anomalies:
            anom_desc = [
                f"Step {getattr(a, 'step', 0)} ({getattr(a, 'anomaly_type', 'anomaly')}: {getattr(a, 'evidence', getattr(a, 'description', ''))})"
                for a in anomalies[:3]
            ]
            obs4 = MeasurableObservation(
                target_memory=target_id,
                metric_name="statistical_anomalies",
                initial_value=0.0,
                final_value=float(len(anomalies)),
                delta=float(len(anomalies)),
                relevant_events=[str(getattr(a, "event_id", "")) for a in anomalies if getattr(a, "event_id", None)],
                summary=f"Detected {len(anomalies)} statistical anomalies during execution: {'; '.join(anom_desc)}.",
                raw_data={"anomalies": [a.to_dict() if hasattr(a, "to_dict") else str(a) for a in anomalies]},
            )
            observations.append(obs4)

        return observations
