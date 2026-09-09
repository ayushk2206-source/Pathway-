"""Critical Memory Detection, Fragility Analysis, and Redundancy for Phase 08."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from core.xray.strength import _extract_memory_cues
from .cascade import CascadeEngine
from .genome import resolve_memory
from .models import (
    CriticalMemoryRank,
    FragilityReport,
    RedundancyRecord,
)
from .types import CascadeEffectType, FragilityClassification


class CriticalMemoryDetector:
    """Detects and ranks memories based on system-wide cascade impact."""

    @classmethod
    def find_critical_memories(cls, experiment: Experiment) -> List[CriticalMemoryRank]:
        """Test each memory with a non-destructive ablation and rank by cascade impact."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            return []

        ranks: List[CriticalMemoryRank] = []
        all_impacts: List[float] = []

        # Run cascade test for each candidate memory
        cascade_results = []
        for mem in memories:
            cmap = CascadeEngine.run_cascade(
                experiment=experiment,
                target_query=mem["memory_id"],
                intervention_type="remove",
            )
            affected_count = sum(1 for n in cmap.nodes if n.effect_type != CascadeEffectType.UNCHANGED)
            cascade_results.append((mem, cmap, affected_count))
            all_impacts.append(cmap.total_cascade_impact)

        mean_impact = float(np.mean(all_impacts)) if all_impacts else 1.0
        std_impact = float(np.std(all_impacts)) if all_impacts else 0.5

        for mem, cmap, aff_count in cascade_results:
            impact = cmap.total_cascade_impact
            if impact >= mean_impact + (0.5 * std_impact):
                impact_level = "HIGH"
            elif impact >= mean_impact - (0.5 * std_impact):
                impact_level = "MEDIUM"
            else:
                impact_level = "LOW"

            ranks.append(
                CriticalMemoryRank(
                    memory_id=mem["memory_id"],
                    concept_label=mem["concept_label"],
                    impact_level=impact_level,
                    total_cascade_impact=round(impact, 4),
                    affected_count=aff_count,
                    max_depth=cmap.total_cascade_depth,
                )
            )

        ranks.sort(key=lambda r: r.total_cascade_impact, reverse=True)
        return ranks


class FragilityAnalyzer:
    """Assesses whether the system is disproportionately fragile to target memory loss."""

    @classmethod
    def analyze_fragility(cls, experiment: Experiment, target_query: str) -> FragilityReport:
        """Run single-point-of-failure analysis backed by quantitative measurements."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            return FragilityReport(
                target_memory=target_query,
                classification=FragilityClassification.INCONCLUSIVE,
                impact_ratio=1.0,
                mean_system_impact=0.0,
                measured_impact=0.0,
                evidence=["Insufficient memories to conduct fragility evaluation."],
            )

        target_mem = resolve_memory(experiment, target_query)
        if not target_mem:
            target_mem = memories[0]

        target_id = target_mem["memory_id"]
        target_concept = target_mem["concept_label"]

        # Run target cascade
        cmap = CascadeEngine.run_cascade(
            experiment=experiment,
            target_query=target_id,
            intervention_type="remove",
        )
        measured_impact = cmap.total_cascade_impact
        affected_count = sum(1 for n in cmap.nodes if n.effect_type != CascadeEffectType.UNCHANGED)

        # Baseline mean impact across memories (sample up to 5)
        sample_memories = [m for m in memories if m["memory_id"] != target_id][:4]
        sample_impacts = []
        for sm in sample_memories:
            c_sm = CascadeEngine.run_cascade(
                experiment=experiment,
                target_query=sm["memory_id"],
                intervention_type="remove",
            )
            sample_impacts.append(c_sm.total_cascade_impact)

        mean_system_impact = (
            float(np.mean(sample_impacts)) if sample_impacts else measured_impact
        )

        impact_ratio = round(measured_impact / (mean_system_impact + 1e-6), 4)

        if impact_ratio >= 1.5 and affected_count >= 2:
            classification = FragilityClassification.HIGHLY_FRAGILE
        elif impact_ratio >= 1.1:
            classification = FragilityClassification.MODERATELY_FRAGILE
        elif len(memories) <= 1:
            classification = FragilityClassification.INCONCLUSIVE
        else:
            classification = FragilityClassification.ROBUST

        evidence = [
            f"Measured cascade impact for {target_concept}: {measured_impact:.4f}",
            f"Mean system baseline ablation impact: {mean_system_impact:.4f}",
            f"Impact ratio relative to peer memories: {impact_ratio:.2f}x",
            f"Total downstream memory representations perturbed: {affected_count}",
            f"Maximum cascade propagation depth reached: {cmap.total_cascade_depth}",
        ]

        return FragilityReport(
            target_memory=target_id,
            classification=classification,
            impact_ratio=impact_ratio,
            mean_system_impact=round(mean_system_impact, 4),
            measured_impact=round(measured_impact, 4),
            evidence=evidence,
        )


class RedundancyAnalyzer:
    """Evaluates whether alternative memories can compensate for target ablation."""

    @classmethod
    def analyze_redundancy(cls, experiment: Experiment, target_query: str) -> RedundancyRecord:
        """Trace alternative representation paths that buffer target loss."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            return RedundancyRecord(
                target_memory=target_query,
                redundancy_paths=[],
                compensation_score=0.0,
                has_viable_backup=False,
            )

        target_mem = resolve_memory(experiment, target_query)
        if not target_mem:
            target_mem = memories[0]

        target_id = target_mem["memory_id"]
        target_concept = target_mem["concept_label"]
        k_target = target_mem["key_vector"]

        # Find candidates with substantial key cosine similarity
        redundancy_paths: List[Dict[str, Any]] = []
        for other in memories:
            if other["memory_id"] == target_id:
                continue
            sim = float(cosine(k_target, other["key_vector"]))
            if sim > 0.15:
                redundancy_paths.append({
                    "candidate_memory": other["memory_id"],
                    "concept_label": other["concept_label"],
                    "similarity": round(sim, 4),
                    "compensation_potential": round(max(0.0, sim), 4),
                    "path_label": f"REDUNDANCY PATH: {target_concept} ──({sim:.2f})──> {other['concept_label']}",
                })

        redundancy_paths.sort(key=lambda p: p["similarity"], reverse=True)

        compensation_score = (
            round(float(np.mean([p["compensation_potential"] for p in redundancy_paths[:2]])), 4)
            if redundancy_paths
            else 0.0
        )
        has_viable_backup = compensation_score >= 0.35

        return RedundancyRecord(
            target_memory=target_id,
            redundancy_paths=redundancy_paths,
            compensation_score=compensation_score,
            has_viable_backup=has_viable_backup,
        )
