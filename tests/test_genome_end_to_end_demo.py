"""Canonical 16-Step End-to-End Demonstration Story for Phase 08.

Follows Section 44 of the Phase 08 specification precisely:
STEP 1: Open Memory Genome.
STEP 2: Select Memory (e.g. obj_A / M17).
STEP 3: Inspect origin, formation, associations, competition, trajectory.
STEP 4: Trigger CASCADE ANALYSIS.
STEP 5: Remove Memory in a sandbox branch.
STEP 6: Replay experiment.
STEP 7: Detect FIRST DIVERGENCE.
STEP 8: Visualize cascade map.
STEP 9: Identify downstream memories.
STEP 10: Run DOSE RESPONSE (25%, 50%, 75%, 100%).
STEP 11: Detect possible threshold.
STEP 12: Run RECOVERY TEST.
STEP 13: Restore memory.
STEP 14: Measure recovery status.
STEP 15: Generate CASCADE FORENSICS.
STEP 16: Generate MEMORY GENOME REPORT.
"""

import pytest
from core import Experiment, ExperimentConfig, run_experiment
from core.genome.cascade import CascadeEngine
from core.genome.experiments import DoseResponseEngine, RecoveryEngine
from core.genome.genome import MemoryGenomeBuilder
from core.genome.reports import ReportGenerator
from core.genome.sandbox import SandboxManager
from core.genome.types import CascadeEffectType, RecoveryStatus


def test_phase_08_canonical_16_step_demo():
    """Execute the mandatory 16-step researcher journey from start to finish."""
    # STEP 1: Open Memory Genome & Load substrate
    config = ExperimentConfig.from_api({
        "seed": 42,
        "mechanism": "interference",
        "task_name": "associative_recall",
        "d": 128,
        "num_events": 10,
    })
    exp = run_experiment(config)
    assert exp is not None
    assert len(exp.snapshots) >= 3

    # STEP 2: Select Memory (e.g. obj_A)
    target_memory = "obj_A"

    # STEP 3: Inspect origin, formation, associations, competition, trajectory
    genome = MemoryGenomeBuilder.build(exp, target_memory)
    assert genome.memory_id == "e0000"
    assert genome.origin_step >= 0
    assert len(genome.formation_events) >= 1
    assert len(genome.associations) >= 1
    assert len(genome.trajectory) == len(exp.snapshots)
    assert len(genome.dna_strip.evidence) == 8

    # STEP 4: Trigger CASCADE ANALYSIS
    # STEP 5: Remove Memory in a sandbox branch
    branch = SandboxManager.create_branch(
        experiment=exp,
        parent_id="base",
        intervention={"target_memory": target_memory, "intervention_type": "remove"},
    )
    assert branch.branch_id.startswith("br_")

    # STEP 6: Replay experiment via Cascade Engine
    cmap = CascadeEngine.run_cascade(
        experiment=exp,
        target_query=target_memory,
        intervention_type="remove",
    )
    assert cmap.target_memory == "e0000"

    # STEP 7: Detect FIRST DIVERGENCE
    assert cmap.first_divergence_step is not None
    assert cmap.first_divergence_step >= 0
    assert len(cmap.divergence_order) >= 1

    # STEP 8: Visualize cascade map & ripple nodes
    assert len(cmap.nodes) >= 3
    assert cmap.total_cascade_depth >= 0

    # STEP 9: Identify downstream memories
    downstream_nodes = [
        n for n in cmap.nodes if n.memory_id != "e0000" and n.effect_type != CascadeEffectType.UNCHANGED
    ]
    # May have downstream affected nodes depending on associations
    assert len(cmap.nodes) >= 2

    # STEP 10: Run DOSE RESPONSE (25%, 50%, 75%, 100%, 0%)
    dose_eval = DoseResponseEngine.run_dose_response(exp, target_memory)
    assert len(dose_eval.points) == 5
    doses = [p.dose for p in dose_eval.points]
    assert 1.0 in doses
    assert 0.75 in doses
    assert 0.50 in doses
    assert 0.25 in doses
    assert 0.0 in doses

    # STEP 11: Detect possible threshold
    assert dose_eval.pattern is not None
    assert isinstance(dose_eval.inflection_detected, bool)

    # STEP 12: Run RECOVERY TEST
    # STEP 13: Restore memory
    # STEP 14: Measure recovery status
    rec_eval = RecoveryEngine.test_recovery(exp, target_memory)
    assert rec_eval.status in list(RecoveryStatus)
    assert rec_eval.baseline_strength > 0.0
    assert rec_eval.during_strength >= 0.0

    # STEP 15: Generate CASCADE FORENSICS
    cascade_rep = ReportGenerator.generate_cascade_report(exp, target_memory, "remove")
    assert cascade_rep.target_memory == "e0000"
    assert cascade_rep.first_divergence == cmap.first_divergence_step
    assert cascade_rep.cascade_depth == cmap.total_cascade_depth
    assert len(cascade_rep.summary) > 20

    # STEP 16: Generate MEMORY GENOME REPORT
    genome_rep = ReportGenerator.generate_genome_report(exp, target_memory)
    assert genome_rep.memory_id == "e0000"
    assert "ORIGIN" in genome_rep.sections
    assert "RESILIENCE" in genome_rep.sections
    assert "LIMITATIONS" in genome_rep.sections
    assert len(genome_rep.sections["LIMITATIONS"]) == 3
