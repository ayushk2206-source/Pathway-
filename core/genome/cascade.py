"""Cascade Simulation Engine and Propagation Analysis for Phase 08."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from core import Experiment
from core.counterfactual.interventions import (
    Intervention,
    create_modify_intervention,
    create_remove_intervention,
)
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import InterventionType, ReplayStrategy
from core.vectors import cosine
from core.xray.strength import _extract_memory_cues, compute_memory_strengths
from .genome import resolve_memory
from .models import (
    CascadeEdge,
    CascadeMap,
    CascadeNode,
    InfluenceScoreBreakdown,
)
from .types import CascadeEffectType, GenomeInterventionType


class CascadeEngine:
    """Simulates targeted memory interventions and tracks cascade propagation."""

    @classmethod
    def run_cascade(
        cls,
        experiment: Experiment,
        target_query: str,
        intervention_type: str = "remove",
        dose: float = 1.0,
    ) -> CascadeMap:
        """Run a counterfactual cascade simulation and return the dynamic CascadeMap."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            raise ValueError(f"Experiment {experiment.experiment_id} has no valid memories.")

        target_mem = resolve_memory(experiment, target_query)
        if not target_mem:
            target_mem = memories[0]

        target_id = target_mem["memory_id"]
        target_concept = target_mem["concept_label"]
        origin_step = int(target_mem["timestep"])

        # 1. Build the intervention
        intervention = cls._build_intervention(
            experiment=experiment,
            target_mem=target_mem,
            intervention_type=intervention_type,
            dose=dose,
        )

        # 2. Replay counterfactual experiment
        cf_record = run_counterfactual(
            experiment=experiment,
            intervention=intervention,
            strategy=ReplayStrategy.FULL_REPLAY,
            title=f"Cascade: {intervention_type} {target_concept}",
            description=f"Cascade test with intervention '{intervention_type}' on memory {target_id}",
        )

        cf_experiment = cf_record.to_experiment()

        # 3. Compute control and counterfactual strength profiles
        ctrl_strengths = compute_memory_strengths(experiment)
        cf_strengths = compute_memory_strengths(cf_experiment)

        # 4. Detect per-memory divergence and first divergence step
        nodes: List[CascadeNode] = []
        divergence_events: List[Dict[str, Any]] = []
        global_first_step: Optional[int] = None

        for mem in memories:
            m_id = mem["memory_id"]
            label = mem["concept_label"]

            ctrl_prof = ctrl_strengths.get(m_id)
            cf_prof = cf_strengths.get(m_id)

            ctrl_traj = (
                getattr(ctrl_prof, "timeline_strengths", getattr(ctrl_prof, "strength_trajectory", []))
                if ctrl_prof
                else []
            )
            cf_traj = (
                getattr(cf_prof, "timeline_strengths", getattr(cf_prof, "strength_trajectory", []))
                if cf_prof
                else []
            )

            ctrl_final = float(ctrl_prof.final_strength) if ctrl_prof else 0.5
            cf_final = float(cf_prof.final_strength) if cf_prof else (0.0 if m_id == target_id else 0.5)

            delta = round(cf_final - ctrl_final, 4)
            rel_delta = round(delta / (abs(ctrl_final) + 1e-6), 4)

            # Find first timestep of divergence for this memory
            first_div: Optional[int] = None
            min_len = min(len(ctrl_traj), len(cf_traj))
            for t in range(min_len):
                if abs(ctrl_traj[t] - cf_traj[t]) > 0.03:
                    first_div = t
                    if global_first_step is None or t < global_first_step:
                        global_first_step = t
                    break

            if first_div is not None:
                divergence_events.append({
                    "step": first_div,
                    "memory_id": m_id,
                    "concept_label": label,
                    "delta": delta,
                })

            # Determine depth and classification
            if m_id == target_id:
                depth = 0
                effect_type = CascadeEffectType.DIRECT
            elif abs(delta) <= 0.02:
                depth = 99
                effect_type = CascadeEffectType.UNCHANGED
            elif first_div is not None and global_first_step is not None and first_div <= global_first_step + 1:
                depth = 1
                effect_type = CascadeEffectType.DIRECT
            elif first_div is not None and global_first_step is not None and first_div <= global_first_step + 3:
                depth = 2
                effect_type = CascadeEffectType.SECONDARY
            else:
                depth = 3
                effect_type = CascadeEffectType.TERTIARY

            nodes.append(
                CascadeNode(
                    memory_id=m_id,
                    concept_label=label,
                    depth=depth if depth != 99 else 4,
                    effect_type=effect_type,
                    strength_before=round(ctrl_final, 4),
                    strength_after=round(cf_final, 4),
                    delta=delta,
                    relative_delta=rel_delta,
                    first_divergence_step=first_div,
                )
            )

        # Sort divergence events chronologically
        divergence_events.sort(key=lambda d: d["step"])

        # Calculate max depth and total impact
        active_depths = [n.depth for n in nodes if n.effect_type != CascadeEffectType.UNCHANGED]
        max_depth = max(active_depths) if active_depths else 0

        final_dist_l2 = 0.0
        if cf_record.divergence:
            if isinstance(cf_record.divergence, dict):
                final_dist_l2 = float(cf_record.divergence.get("final_state_distance_l2", 0.0))
            else:
                final_dist_l2 = float(getattr(cf_record.divergence, "final_state_distance_l2", 0.0))

        total_impact = round(sum(abs(n.delta) for n in nodes) + final_dist_l2, 4)

        # 5. Build cascade edges (associations between affected memories)
        edges: List[CascadeEdge] = []
        for i, n1 in enumerate(nodes):
            if n1.effect_type == CascadeEffectType.UNCHANGED:
                continue
            m1_cue = next((m for m in memories if m["memory_id"] == n1.memory_id), None)
            if not m1_cue:
                continue

            for n2 in nodes[i + 1 :]:
                if n2.effect_type == CascadeEffectType.UNCHANGED:
                    continue
                m2_cue = next((m for m in memories if m["memory_id"] == n2.memory_id), None)
                if not m2_cue:
                    continue

                sim = float(cosine(m1_cue["key_vector"], m2_cue["key_vector"]))
                if sim > 0.15:
                    edges.append(
                        CascadeEdge(
                            source=n1.memory_id,
                            target=n2.memory_id,
                            strength=round(sim, 4),
                        )
                    )

        return CascadeMap(
            target_memory=target_id,
            intervention=intervention_type,
            total_cascade_depth=max_depth,
            total_cascade_impact=total_impact,
            first_divergence_step=global_first_step,
            nodes=nodes,
            edges=edges,
            divergence_order=divergence_events,
        )

    @classmethod
    def _build_intervention(
        cls,
        experiment: Experiment,
        target_mem: Dict[str, Any],
        intervention_type: str,
        dose: float,
    ) -> Intervention:
        """Construct the appropriate Counterfactual Intervention object."""
        target_id = target_mem["memory_id"]
        target_step = int(target_mem["timestep"])

        # Normalize intervention name
        inv_clean = intervention_type.strip().lower()

        if "weaken" in inv_clean:
            scale = max(0.05, min(0.99, dose if dose < 1.0 else 0.5))
            return create_modify_intervention(
                target_timestep=target_step,
                target_event_id=target_id,
                modifications={"strength": scale},
                description=f"Weaken memory {target_id} with dose factor {scale:.2f}",
            )
        elif "strengthen" in inv_clean:
            scale = 1.5
            return create_modify_intervention(
                target_timestep=target_step,
                target_event_id=target_id,
                modifications={"strength": scale},
                description=f"Strengthen memory {target_id} with factor {scale:.2f}",
            )
        else:
            # Default: Remove event
            return create_remove_intervention(
                target_timestep=target_step,
                target_event_id=target_id,
                description=f"Ablate memory event {target_id} from timeline",
            )

    @classmethod
    def compute_influence_breakdown(cls, cascade_map: CascadeMap) -> InfluenceScoreBreakdown:
        """Calculate the transparent, 4-component influence score."""
        target_node = next(
            (n for n in cascade_map.nodes if n.memory_id == cascade_map.target_memory), None
        )
        direct_effect = abs(target_node.delta) if target_node else 0.5

        downstream_nodes = [
            n for n in cascade_map.nodes if n.memory_id != cascade_map.target_memory and n.effect_type != CascadeEffectType.UNCHANGED
        ]

        downstream_effect = (
            float(np.mean([abs(n.delta) for n in downstream_nodes]))
            if downstream_nodes
            else 0.0
        )

        persistence = min(1.0, len(downstream_nodes) / max(1, len(cascade_map.nodes) - 1))
        depth_score = min(1.0, cascade_map.total_cascade_depth / 4.0)

        total_influence = float(
            round(0.3 * direct_effect + 0.35 * downstream_effect + 0.2 * persistence + 0.15 * depth_score, 4)
        )

        return InfluenceScoreBreakdown(
            direct_effect=round(direct_effect, 4),
            downstream_effect=round(downstream_effect, 4),
            persistence=round(persistence, 4),
            depth_score=round(depth_score, 4),
            total_influence=total_influence,
        )

    @classmethod
    def detect_surprise(cls, cascade_map: CascadeMap, intervention_dose: float) -> str:
        """Identify unexpected phenomena: AMPLIFIED RESPONSE vs DAMPED RESPONSE."""
        target_node = next(
            (n for n in cascade_map.nodes if n.memory_id == cascade_map.target_memory), None
        )
        target_delta = abs(target_node.delta) if target_node else 0.5

        downstream_deltas = [
            abs(n.delta)
            for n in cascade_map.nodes
            if n.memory_id != cascade_map.target_memory
        ]
        mean_downstream = float(np.mean(downstream_deltas)) if downstream_deltas else 0.0

        if target_delta < 0.15 and mean_downstream > 0.25:
            return "AMPLIFIED RESPONSE"
        elif target_delta > 0.5 and mean_downstream < 0.04:
            return "DAMPED RESPONSE"
        return "EXPECTED RESPONSE"
