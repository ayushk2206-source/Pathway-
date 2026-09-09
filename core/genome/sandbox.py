"""Intervention Sandbox, Experiment Branch Trees, and Branch Comparison for Phase 08."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid

from core import Experiment
from .cascade import CascadeEngine
from .models import SandboxBranch
from .types import CascadeEffectType


class SandboxManager:
    """Manages non-destructive experiment branch trees and multi-branch comparison."""

    _branch_store: Dict[str, List[SandboxBranch]] = {}

    @classmethod
    def create_branch(
        cls,
        experiment: Experiment,
        parent_id: str,
        intervention: Dict[str, Any],
    ) -> SandboxBranch:
        """Create a new replayable sandbox branch from an experiment without mutating the parent."""
        exp_id = experiment.experiment_id
        branch_id = f"br_{uuid.uuid4().hex[:8]}"

        branch = SandboxBranch(
            branch_id=branch_id,
            parent_id=parent_id,
            experiment_id=exp_id,
            intervention=intervention,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        if exp_id not in cls._branch_store:
            cls._branch_store[exp_id] = []
        cls._branch_store[exp_id].append(branch)

        return branch

    @classmethod
    def list_branches(cls, experiment_id: str) -> List[SandboxBranch]:
        """List all registered sandbox branches for an experiment."""
        return cls._branch_store.get(experiment_id, [])

    @classmethod
    def compare_branches(
        cls,
        experiment: Experiment,
        intervention_a: Dict[str, Any],
        intervention_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare two branch interventions side-by-side."""
        target_a = intervention_a.get("target_memory", "obj_A")
        type_a = intervention_a.get("intervention_type", "remove")
        dose_a = float(intervention_a.get("dose", 1.0))

        target_b = intervention_b.get("target_memory", "obj_B")
        type_b = intervention_b.get("intervention_type", "remove")
        dose_b = float(intervention_b.get("dose", 1.0))

        cmap_a = CascadeEngine.run_cascade(
            experiment=experiment,
            target_query=target_a,
            intervention_type=type_a,
            dose=dose_a,
        )

        cmap_b = CascadeEngine.run_cascade(
            experiment=experiment,
            target_query=target_b,
            intervention_type=type_b,
            dose=dose_b,
        )

        nodes_a = {n.memory_id: n for n in cmap_a.nodes if n.effect_type != CascadeEffectType.UNCHANGED}
        nodes_b = {n.memory_id: n for n in cmap_b.nodes if n.effect_type != CascadeEffectType.UNCHANGED}

        common_effects: List[Dict[str, Any]] = []
        opposite_effects: List[Dict[str, Any]] = []
        unique_a: List[Dict[str, Any]] = []
        unique_b: List[Dict[str, Any]] = []

        all_ids = set(nodes_a.keys()).union(set(nodes_b.keys()))

        for m_id in all_ids:
            na = nodes_a.get(m_id)
            nb = nodes_b.get(m_id)

            if na and nb:
                if (na.delta > 0 and nb.delta > 0) or (na.delta < 0 and nb.delta < 0):
                    common_effects.append({
                        "memory_id": m_id,
                        "concept_label": na.concept_label,
                        "delta_branch_a": na.delta,
                        "delta_branch_b": nb.delta,
                    })
                else:
                    opposite_effects.append({
                        "memory_id": m_id,
                        "concept_label": na.concept_label,
                        "delta_branch_a": na.delta,
                        "delta_branch_b": nb.delta,
                    })
            elif na and not nb:
                unique_a.append({
                    "memory_id": m_id,
                    "concept_label": na.concept_label,
                    "delta": na.delta,
                })
            elif nb and not na:
                unique_b.append({
                    "memory_id": m_id,
                    "concept_label": nb.concept_label,
                    "delta": nb.delta,
                })

        return {
            "branch_a": {
                "intervention": intervention_a,
                "total_impact": cmap_a.total_cascade_impact,
                "max_depth": cmap_a.total_cascade_depth,
                "affected_count": len(nodes_a),
            },
            "branch_b": {
                "intervention": intervention_b,
                "total_impact": cmap_b.total_cascade_impact,
                "max_depth": cmap_b.total_cascade_depth,
                "affected_count": len(nodes_b),
            },
            "common_effects": common_effects,
            "opposite_effects": opposite_effects,
            "unique_effects_a": unique_a,
            "unique_effects_b": unique_b,
            "comparative_impact_diff": round(abs(cmap_a.total_cascade_impact - cmap_b.total_cascade_impact), 4),
        }
