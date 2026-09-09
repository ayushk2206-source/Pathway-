"""Automatic discovery engine and novelty detector (Phase 07).

Scans experiments for measurable phenomena and generates an actionable Discovery Feed.
Surfaces verifiable observations, never fabricated explanations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core.experiment import Experiment
from core.vectors import cosine
from core.xray.anomalies import detect_state_anomalies
from core.xray.interference import detect_interference
from core.xray.strength import _extract_memory_cues, compute_memory_strengths
from .models import DiscoveryObservation
from .types import DiscoveryNovelty


def _get_event_id(ev: Any, default: str = "") -> str:
    if hasattr(ev, "id"):
        return str(ev.id)
    if isinstance(ev, dict):
        return str(ev.get("id") or default)
    return default


class DiscoveryEngine:
    """Surfaces interesting measurable phenomena from completed experiments."""

    @classmethod
    def scan_experiment(
        cls,
        experiment: Experiment,
        historical_discoveries: Optional[List[DiscoveryObservation]] = None,
    ) -> List[DiscoveryObservation]:
        """Scan a single experiment and return discovered observations with 1-click investigation seeds."""
        discoveries: List[DiscoveryObservation] = []
        memories = _extract_memory_cues(experiment)
        if not memories:
            return discoveries

        strengths_map = compute_memory_strengths(experiment)
        interferences = detect_interference(experiment)
        anomalies = detect_state_anomalies(experiment)

        # 1. Check for Unexpected Persistence
        for mem in memories:
            m_id = mem["memory_id"]
            prof = strengths_map.get(m_id)
            if not prof:
                continue

            # Check if this memory faces high similarity from others
            high_sim_count = 0
            max_sim = 0.0
            for other in memories:
                if other["memory_id"] != m_id:
                    sim = float(cosine(mem["key_vector"], other["key_vector"]))
                    if sim > 0.30:
                        high_sim_count += 1
                        if sim > max_sim:
                            max_sim = sim

            # If faced competition but maintained strong readout (> 0.42)
            if high_sim_count >= 1 and prof.final_strength >= 0.42:
                disc = DiscoveryObservation(
                    experiment_id=experiment.experiment_id,
                    title=f"Unexpected Persistence: {mem['concept_label']}",
                    description=(
                        f"Memory {mem['concept_label']} maintained robust representation strength "
                        f"({prof.final_strength:.3f}) despite {high_sim_count} competing cue(s) "
                        f"(max cosine similarity: {max_sim:.2f})."
                    ),
                    category="persistence",
                    target_memory=m_id,
                    relevant_events=[f"e{mem['timestep']:04d}"],
                    metrics={
                        "final_strength": float(prof.final_strength),
                        "competing_cues": float(high_sim_count),
                        "max_similarity": float(max_sim),
                    },
                    seed_question=f"Why did Memory {mem['concept_label']} survive despite competing writes?",
                )
                discoveries.append(disc)

        # 2. Check for Severe Cross-Talk Degradation
        for rec in interferences:
            deg = float(getattr(rec, "degradation", getattr(rec, "interference_score", 0.0)))
            sim = float(getattr(rec, "similarity", getattr(rec, "overlap", 0.0)))
            target_id = getattr(rec, "target_memory_id", getattr(rec, "memory_a", ""))
            comp_id = getattr(rec, "competing_memory_id", getattr(rec, "memory_b", ""))
            ev_id = getattr(rec, "event_id", "")

            if deg > 0.15 or sim > 0.35:
                t_mem = next((m for m in memories if m["memory_id"] == target_id), None)
                c_label = t_mem["concept_label"] if t_mem else target_id
                disc = DiscoveryObservation(
                    experiment_id=experiment.experiment_id,
                    title=f"Severe Interference Loss: {c_label}",
                    description=(
                        f"Memory {c_label} suffered significant cross-talk degradation ({deg:.3f}) "
                        f"with competitor {comp_id} (sim: {sim:.2f})."
                    ),
                    category="interference",
                    target_memory=target_id,
                    relevant_events=[ev_id] if ev_id else [],
                    metrics={
                        "degradation": deg,
                        "similarity": sim,
                    },
                    seed_question=f"Why did Memory {c_label} weaken due to competition?",
                )
                discoveries.append(disc)

        # 3. Check for Large Substrate State Jumps
        snapshots = experiment.snapshots
        for s in range(1, len(snapshots)):
            s_prev = np.asarray(snapshots[s - 1].get("state_vector", []), dtype=np.float64)
            s_curr = np.asarray(snapshots[s].get("state_vector", []), dtype=np.float64)
            if len(s_prev) > 0 and len(s_curr) > 0:
                l2_jump = float(np.linalg.norm(s_curr - s_prev))
                cos_dist = float(1.0 - cosine(s_prev, s_curr))
                if l2_jump > 0.8 or cos_dist > 0.35:
                    ev_id = _get_event_id(experiment.events[s - 1], f"step_{s}") if s - 1 < len(experiment.events) else f"step_{s}"
                    disc = DiscoveryObservation(
                        experiment_id=experiment.experiment_id,
                        title=f"Abrupt State Transition at Step {s}",
                        description=(
                            f"Step {s} induced large directional shift (cos distance: {cos_dist:.3f}, L2: {l2_jump:.3f}) "
                            f"associated with event {ev_id}."
                        ),
                        category="state_shift",
                        relevant_events=[ev_id] if ev_id else [],
                        metrics={"l2_jump": l2_jump, "cosine_distance": cos_dist, "step": float(s)},
                        seed_question="What caused this sudden state transition?",
                    )
                    discoveries.append(disc)

        # 4. Novelty Classification relative to history
        past_categories = [d.category for d in (historical_discoveries or [])]
        for d in discoveries:
            count = past_categories.count(d.category)
            if count == 0:
                d.novelty = DiscoveryNovelty.POTENTIALLY_NOVEL
            elif count <= 2:
                d.novelty = DiscoveryNovelty.VARIATION
            else:
                d.novelty = DiscoveryNovelty.KNOWN_PATTERN

        return discoveries
