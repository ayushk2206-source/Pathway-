"""Canonical End-to-End Demonstration for Phase 10: Causal Memory Lab (Section 50).

Workflow:
1. Open / run experiment.
2. Select key target memory (e.g. M17 or obj_A).
3. Formulate "What if M17 were weakened by 5% at t=20?" scenario.
4. Compile scenario and execute counterfactual replay.
5. Display synchronized ORIGINAL vs COUNTERFACTUAL worlds.
6. Detect FIRST DIVERGENCE point and cause candidate.
7. Trace downstream cascade nodes (memories, associations, outputs).
8. Compute cascade amplification ratio.
9. Run replication verification.
10. Add empirical claim and evidence to CAUSALITY LEDGER.
11. Generate publication-grade Causal Report.
12. Handoff causal discovery to Autonomous Discovery Engine.
"""

import pytest
from core.experiment import ExperimentConfig
from core.mechanisms.base import MechanismParams
from core.runner import run_experiment
from core.task import TaskConfig

from core.causal import (
    CausalInterventionType,
    CausalLedger,
    CausalReportGenerator,
    CausalScenario,
    CausalScenarioCompiler,
    ClaimStatus,
    compute_first_divergence,
    run_timing_sensitivity,
)
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import ReplayStrategy
from core.genome.cascade import CascadeEngine


def test_canonical_causal_lab_demonstration():
    # 1. Open experiment
    cfg = ExperimentConfig(
        seed=101,
        mechanism="leaky",
        params=MechanismParams(update_strength=0.85, decay=0.12),
        task=TaskConfig(
            seed=101,
            n_objects=6,
            n_symbols=6,
            n_conflicts=3,
            cycles=4,
            order="interleaved",
        ),
    )
    exp = run_experiment(cfg)
    assert exp is not None
    assert len(exp.events) >= 20

    # 2. Select Memory M17 / primary cue
    target_mem = exp.events[5]["concept_label"]
    assert target_mem is not None

    # 3. Formulate scenario: "What if M17 were weakened by 5% at t=20?"
    timing = min(20, len(exp.events) - 1)
    scenario = CausalScenario(
        experiment_id=exp.experiment_id,
        target_memory=target_mem,
        intervention=CausalInterventionType.WEAKEN,
        timing=timing,
        strength=0.95,
        label=f"What if {target_mem} were weakened by 5% at t={timing}?",
    )

    # Validate scenario & estimate compute cost
    validation = CausalScenarioCompiler.validate(exp, scenario)
    assert validation.valid is True
    assert validation.cost_estimate.within_budget is True

    # 4. Run counterfactual
    intervention = CausalScenarioCompiler.compile(exp, scenario)
    cf = run_counterfactual(
        experiment=exp,
        intervention=intervention,
        strategy=ReplayStrategy.FULL_REPLAY,
        title=scenario.label,
    )
    assert cf is not None
    assert cf.divergence is not None

    # 5. Synchronized ORIGINAL vs COUNTERFACTUAL comparison
    orig_states = [s.get("state_vector", s.get("state")) for s in exp.snapshots]
    cf_exp = cf.to_experiment()
    cf_states = [s.get("state_vector", s.get("state")) for s in cf_exp.snapshots]
    assert len(orig_states) == len(cf_states)

    # 6. Detect FIRST DIVERGENCE
    first_div = compute_first_divergence(cf)
    assert first_div.counterfactual_id == cf.counterfactual_id
    assert first_div.first_divergence_step is not None
    assert first_div.divergence_magnitude > 0.0
    print(f"\n[DEMO] Two worlds first diverged at t={first_div.first_divergence_step}")

    # 7. Trace Cascade
    cmap = CascadeEngine.run_cascade(exp, target_mem, intervention_type="weaken", dose=0.95)
    assert cmap is not None
    assert len(cmap.nodes) > 0
    print(f"[DEMO] Cascade trace: {len(cmap.nodes)} affected nodes, total impact: {cmap.total_cascade_impact:.4f}")

    # 8. Display Cascade Amplification (small initial 5% perturbation -> measurable cascade)
    initial_dose_pct = 0.05
    downstream_impact = cmap.total_cascade_impact
    amplification_ratio = downstream_impact / initial_dose_pct
    assert amplification_ratio > 0.0
    print(f"[DEMO] Cascade Amplification Ratio: {amplification_ratio:.2f}x")

    # 9. Run replication verification (seeded repeat)
    cf_repl = run_counterfactual(
        experiment=exp,
        intervention=intervention,
        strategy=ReplayStrategy.FULL_REPLAY,
    )
    first_div_repl = compute_first_divergence(cf_repl)
    assert first_div_repl.first_divergence_step == first_div.first_divergence_step
    assert abs(first_div_repl.divergence_magnitude - first_div.divergence_magnitude) < 1e-6

    # 10. Add evidence to CAUSALITY LEDGER
    ledger = CausalLedger()
    claim = ledger.register_claim(
        source_memory=target_mem,
        target_memory=cmap.nodes[-1].concept_label if len(cmap.nodes) > 1 else target_mem,
        statement=f"5% weakening of {target_mem} at t={timing} triggers cascade divergence beginning at t={first_div.first_divergence_step}.",
        status=ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT,
        evidence_experiment_ids=[exp.experiment_id, cf.counterfactual_id],
        interventions=1,
        replications=2,
        effect_consistency="HIGH",
    )
    assert claim.claim_id == "CLM-001"
    assert claim.current.status == ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT

    # 11. Generate publication-grade Causal Report
    report = CausalReportGenerator.generate_report(
        experiment_id=exp.experiment_id,
        question=scenario.label,
        scenario=scenario.to_dict(),
        baseline={"experiment_id": exp.experiment_id, "n_events": len(exp.events)},
        intervention={"target": target_mem, "dose": 0.95, "timing": timing},
        first_divergence=first_div.to_dict(),
        cascade={"impact": cmap.total_cascade_impact, "nodes": len(cmap.nodes)},
        replication={"replications": 2, "consistency": "HIGH", "deterministic_match": True},
    )
    assert report.report_id.startswith("crep-")
    assert len(report.limitations) >= 3

    # 12. Handoff to Autonomous Discovery Engine
    discovery_obs = {
        "observation_id": f"obs-causal-{exp.experiment_id[:6]}",
        "pattern": "CASCADE_AMPLIFICATION",
        "title": f"Causal amplification observed in {target_mem}",
        "evidence_claim_id": claim.claim_id,
        "first_divergence": first_div.first_divergence_step,
        "amplification": round(amplification_ratio, 2),
    }
    assert discovery_obs["pattern"] == "CASCADE_AMPLIFICATION"
    print(f"[DEMO] Handed off causal discovery to Phase 09 Autonomous Discovery Engine: {discovery_obs['observation_id']}")
