"""Report Generation and Automatic Research Question Engine for Phase 08."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from .cascade import CascadeEngine
from .experiments import DoseResponseEngine, RecoveryEngine
from .fragility import FragilityAnalyzer
from .genome import MemoryGenomeBuilder
from .models import CascadeReport, GenomeReport
from .types import CascadeEffectType, FragilityClassification


class ReportGenerator:
    """Generates structured, quantitative research reports for Genomes and Cascades."""

    @classmethod
    def generate_genome_report(cls, experiment: Experiment, target_query: str) -> GenomeReport:
        """Produce the comprehensive Memory Genome Report."""
        genome = MemoryGenomeBuilder.build(experiment, target_query)
        fragility = FragilityAnalyzer.analyze_fragility(experiment, genome.memory_id)
        recovery = RecoveryEngine.test_recovery(experiment, genome.memory_id)

        summary = (
            f"Computational genome audit for memory item '{genome.concept_label}' (ID: {genome.memory_id}). "
            f"First consolidated at step {genome.origin_step} with final readout strength {genome.current_strength:.2f}. "
            f"Classification: {fragility.classification.value}. Stability: {genome.stability:.0%}, "
            f"Recovery potential: {recovery.status.value}."
        )

        sections: Dict[str, Any] = {
            "ORIGIN": {
                "origin_event": genome.origin_event,
                "origin_step": genome.origin_step,
                "formation_events": genome.formation_events,
            },
            "ASSOCIATIONS": [a.to_dict() for a in genome.associations[:4]],
            "COMPETITORS": [c.to_dict() for c in genome.competitors[:4]],
            "REINFORCEMENT": {
                "count": len(genome.reinforcement_history),
                "history": [r.to_dict() for r in genome.reinforcement_history],
            },
            "TRAJECTORY": {
                "initial_strength": genome.trajectory[0] if genome.trajectory else 0.0,
                "final_strength": genome.current_strength,
                "length": len(genome.trajectory),
            },
            "RESILIENCE": {
                "stability": genome.stability,
                "sensitivity": genome.sensitivity,
                "fragility_classification": fragility.classification.value,
                "recovery_status": recovery.status.value,
            },
            "INFLUENCE": {
                "influence_score": genome.influence_score,
                "downstream_memories": genome.downstream_influence,
            },
            "LIMITATIONS": [
                "Analysis reflects computational representation dynamics within this discrete experiment.",
                "Zero claims of biological equivalence or cognitive universality are made.",
                "Metrics are deterministic and reproducible across replay runs.",
            ],
        }

        return GenomeReport(
            memory_id=genome.memory_id,
            summary=summary,
            sections=sections,
        )

    @classmethod
    def generate_cascade_report(
        cls,
        experiment: Experiment,
        target_query: str,
        intervention: str = "remove",
    ) -> CascadeReport:
        """Produce the quantitative Cascade Simulation Report."""
        cmap = CascadeEngine.run_cascade(experiment, target_query, intervention_type=intervention)

        affected = [n.concept_label for n in cmap.nodes if n.effect_type != CascadeEffectType.UNCHANGED]
        unchanged = [n.concept_label for n in cmap.nodes if n.effect_type == CascadeEffectType.UNCHANGED]

        summary = (
            f"Cascade simulation report for intervention '{intervention}' on '{cmap.target_memory}'. "
            f"First divergence observed at step {cmap.first_divergence_step}. "
            f"Propagated across {len(affected)} memory nodes with maximum depth {cmap.total_cascade_depth}. "
            f"Total cascade impact magnitude: {cmap.total_cascade_impact:.4f}."
        )

        return CascadeReport(
            target_memory=cmap.target_memory,
            intervention=intervention,
            first_divergence=cmap.first_divergence_step,
            cascade_depth=cmap.total_cascade_depth,
            total_impact=cmap.total_cascade_impact,
            affected_nodes=affected,
            unchanged_nodes=unchanged,
            summary=summary,
        )


class AutomaticResearchQuestionGenerator:
    """Generates grounded research inquiries based on empirical findings."""

    @classmethod
    def generate_questions(cls, experiment: Experiment, target_query: str) -> List[str]:
        """Generate verifiable research questions from detected anomalies and dynamics."""
        questions: List[str] = []

        try:
            genome = MemoryGenomeBuilder.build(experiment, target_query)
            dose_res = DoseResponseEngine.run_dose_response(experiment, target_query)
            fragility = FragilityAnalyzer.analyze_fragility(experiment, target_query)

            if dose_res.inflection_detected and dose_res.threshold_dose is not None:
                questions.append(
                    f"Why does Memory '{genome.concept_label}' exhibit a threshold response "
                    f"around {dose_res.threshold_dose:.0%} intervention strength?"
                )

            if fragility.classification == FragilityClassification.HIGHLY_FRAGILE:
                questions.append(
                    f"Why does ablating Memory '{genome.concept_label}' trigger a disproportionate "
                    f"system-wide cascade ({fragility.impact_ratio:.1f}x baseline)?"
                )

            if genome.competitors:
                top_comp = genome.competitors[0]
                questions.append(
                    f"Does cross-talk interference between '{genome.concept_label}' and '{top_comp.concept_label}' "
                    f"(overlap {top_comp.overlap_score:.2f}) restrict mutual retrieval fidelity?"
                )

            if len(genome.downstream_influence) >= 2:
                questions.append(
                    f"Does weakening '{genome.concept_label}' selectively degrade downstream representations "
                    f"without disturbing unassociated memories?"
                )
        except Exception:
            pass

        if not questions:
            questions.append(
                f"How does targeted perturbation of memory '{target_query}' propagate through vector superposition?"
            )

        return questions
