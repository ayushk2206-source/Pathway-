"""Automatic test design, control creation, counterfactual testing, and scoring (Phase 07).

Strictly distinguishes between CORRELATED and COUNTERFACTUALLY SUPPORTED.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from core.counterfactual.interventions import (
    Intervention,
    create_modify_intervention,
    create_remove_intervention,
)
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import InterventionType, ReplayStrategy
from core.experiment import Experiment
from core.xray.strength import compute_memory_strengths
from .models import (
    CandidateHypothesis,
    EvidenceChain,
    MeasurableObservation,
    TestDesign,
    TestResult,
)
from .types import CausalSupportStatus, HypothesisClassification


class TestDesigner:
    """Designs the minimal controlled experiment to test a specific candidate hypothesis."""

    __test__ = False

    @classmethod
    def design_test(
        cls,
        experiment: Experiment,
        hypothesis: CandidateHypothesis,
        observations: List[MeasurableObservation],
    ) -> TestDesign:
        target_mem = observations[0].target_memory if observations else "target_memory"

        # Extract competing events from observations
        rel_events = []
        for obs in observations:
            if obs.relevant_events:
                rel_events.extend(obs.relevant_events)
        rel_events = list(dict.fromkeys(rel_events))

        # Find target event and timestep
        events = experiment.events
        ev1 = events[1] if len(events) > 1 else None
        ev1_id = getattr(ev1, "id", None) or (ev1.get("id") if isinstance(ev1, dict) else "e0001") if ev1 else "e0001"
        target_event_id = rel_events[0] if rel_events else str(ev1_id)
        target_step = 1
        for idx, ev in enumerate(events):
            e_id = getattr(ev, "id", None) or (ev.get("id") if isinstance(ev, dict) else f"e{idx:04d}")
            if str(e_id) == target_event_id:
                target_step = idx
                break

        if "INTERFERENCE" in hypothesis.hypothesis_id or "interference" in hypothesis.mechanism.lower():
            return TestDesign(
                hypothesis_id=hypothesis.hypothesis_id,
                description=f"Remove suspected interfering event {target_event_id} and replay memory trajectory.",
                control_description=f"Control: Full sequence including {target_event_id} (conflicting write present).",
                intervention_description=f"Intervention: Sequence with {target_event_id} removed (competitor ablated).",
                intervention_type=InterventionType.REMOVE_EVENT.value,
                target_timestep=target_step,
                target_event_id=target_event_id,
                target_memory=target_mem,
            )

        elif "PASSIVE-DECAY" in hypothesis.hypothesis_id or "decay" in hypothesis.mechanism.lower():
            # Test decay by modifying decay factor or adding early reinforcement
            return TestDesign(
                hypothesis_id=hypothesis.hypothesis_id,
                description=f"Modify temporal update parameter to evaluate decay impact on Memory {target_mem}.",
                control_description=f"Control: Baseline sequence with default decay parameter λ.",
                intervention_description=f"Intervention: Modify event {target_event_id} strength parameter to 0.0.",
                intervention_type=InterventionType.MODIFY_EVENT.value,
                target_timestep=target_step,
                target_event_id=target_event_id,
                parameters={"update_strength": 0.0},
                target_memory=target_mem,
            )

        elif "DISPLACEMENT" in hypothesis.hypothesis_id or "displacement" in hypothesis.mechanism.lower():
            return TestDesign(
                hypothesis_id=hypothesis.hypothesis_id,
                description=f"Scale down update strength of subsequent event {target_event_id} to test displacement.",
                control_description=f"Control: Standard event write magnitude (1.0).",
                intervention_description=f"Intervention: Scaled write magnitude (0.2) at event {target_event_id}.",
                intervention_type=InterventionType.MODIFY_EVENT.value,
                target_timestep=target_step,
                target_event_id=target_event_id,
                parameters={"update_strength": 0.2},
                target_memory=target_mem,
            )

        else:
            # Fallback minimal intervention
            return TestDesign(
                hypothesis_id=hypothesis.hypothesis_id,
                description=f"Ablate event {target_event_id} to observe causal sensitivity.",
                control_description="Control: Unmodified original experiment sequence.",
                intervention_description=f"Intervention: Event {target_event_id} removed from timeline.",
                intervention_type=InterventionType.REMOVE_EVENT.value,
                target_timestep=target_step,
                target_event_id=target_event_id,
                target_memory=target_mem,
            )


class TestRunner:
    """Executes controlled tests against the deterministic memory engine and derives evidence."""

    __test__ = False

    @classmethod
    def run_test(
        cls,
        experiment: Experiment,
        hypothesis: CandidateHypothesis,
        test_design: TestDesign,
    ) -> Tuple[TestResult, EvidenceChain]:
        """Run control vs counterfactual intervention, calculate causal support, and update hypothesis."""
        target_mem = test_design.target_memory or "target_memory"

        # 1. Build Intervention
        intv_type = InterventionType(test_design.intervention_type)
        if intv_type == InterventionType.REMOVE_EVENT:
            intervention = create_remove_intervention(
                target_timestep=test_design.target_timestep,
                target_event_id=test_design.target_event_id,
                description=test_design.description,
            )
        elif intv_type == InterventionType.MODIFY_EVENT:
            mods = test_design.parameters.get("modifications") if isinstance(test_design.parameters.get("modifications"), dict) else test_design.parameters
            if not mods:
                mods = {"strength": 0.5}
            intervention = create_modify_intervention(
                modifications=mods,
                target_timestep=test_design.target_timestep,
                target_event_id=test_design.target_event_id,
                description=test_design.description,
            )
        else:
            intervention = Intervention(
                intervention_type=intv_type,
                target_timestep=test_design.target_timestep,
                target_event_id=test_design.target_event_id,
                parameters=test_design.parameters,
                description=test_design.description,
            )

        # 2. Execute Counterfactual Replay
        cf_record = run_counterfactual(
            experiment=experiment,
            intervention=intervention,
            strategy=ReplayStrategy.FULL_REPLAY,
            title=f"Detective Test: {hypothesis.hypothesis_id}",
            description=test_design.description,
        )

        # 3. Extract Control vs Intervention Trajectories
        orig_strengths = compute_memory_strengths(experiment)
        cf_exp = cf_record.to_experiment()
        cf_strengths = compute_memory_strengths(cf_exp)

        orig_prof = orig_strengths.get(target_mem)
        cf_prof = cf_strengths.get(target_mem)

        # Fallback if target_mem was concept label instead of id
        if not orig_prof:
            for k, p in orig_strengths.items():
                if target_mem.lower() in k.lower():
                    orig_prof = p
                    cf_prof = cf_strengths.get(k)
                    target_mem = k
                    break

        control_traj = (
            getattr(orig_prof, "timeline_strengths", getattr(orig_prof, "strength_history", []))
            if orig_prof
            else [0.5] * len(experiment.snapshots)
        )
        intervention_traj = (
            getattr(cf_prof, "timeline_strengths", getattr(cf_prof, "strength_history", []))
            if cf_prof
            else [0.5] * len(cf_exp.snapshots)
        )

        ctrl_final = float(control_traj[-1]) if control_traj else 0.0
        intv_final = float(intervention_traj[-1]) if intervention_traj else 0.0
        recovery_delta = intv_final - ctrl_final

        # Find first point where trajectories diverge
        first_div = None
        min_len = min(len(control_traj), len(intervention_traj))
        for t in range(min_len):
            if abs(control_traj[t] - intervention_traj[t]) > 0.01:
                first_div = t
                break

        div_profile = cf_record.divergence
        div_mag = float(
            div_profile.get("final_state_distance_l2", 0.0)
            if isinstance(div_profile, dict)
            else getattr(div_profile, "final_state_distance_l2", 0.0)
        )

        # 4. Evaluate Causal Support (Strictly Grounded)
        if recovery_delta > 0.03:
            causal_status = CausalSupportStatus.COUNTERFACTUALLY_SUPPORTED
            classification = HypothesisClassification.SUPPORTED
            summary = (
                f"Removing {test_design.target_event_id} recovered +{recovery_delta:.4f} representation strength "
                f"for Memory {target_mem} ({ctrl_final:.3f} → {intv_final:.3f}). "
                f"Hypothesis is COUNTERFACTUALLY SUPPORTED."
            )
        elif recovery_delta < -0.03:
            causal_status = CausalSupportStatus.CONTRADICTED
            classification = HypothesisClassification.REFUTED
            summary = (
                f"Removing {test_design.target_event_id} further degraded representation strength by {recovery_delta:.4f}. "
                f"Hypothesis is CONTRADICTED."
            )
        else:
            causal_status = CausalSupportStatus.UNSUPPORTED
            classification = HypothesisClassification.REFUTED
            summary = (
                f"Removing {test_design.target_event_id} produced negligible change (Δ = {recovery_delta:+.4f}). "
                f"Counterfactual intervention does NOT support this hypothesis."
            )

        # Update hypothesis state in place
        hypothesis.status = causal_status
        hypothesis.classification = classification
        hypothesis.counterfactual_support = float(recovery_delta)
        if causal_status == CausalSupportStatus.COUNTERFACTUALLY_SUPPORTED:
            hypothesis.supporting_evidence.append(summary)
            hypothesis.supporting_evidence_count += 1
            hypothesis.explanation_score = min(1.0, hypothesis.explanation_score + 0.15)
        else:
            hypothesis.contradicting_evidence.append(summary)
            hypothesis.contradicting_evidence_count += 1
            hypothesis.explanation_score = max(0.0, hypothesis.explanation_score - 0.20)

        # 5. Build Step-by-Step Evidence Chain
        chain_steps: List[Dict[str, Any]] = [
            {
                "step": 1,
                "type": "OBSERVATION",
                "content": f"Memory {target_mem} initial strength observed at {control_traj[0] if control_traj else 0.0:.3f}.",
            },
            {
                "step": 2,
                "type": "INTERFERENCE_WRITE",
                "content": f"Event {test_design.target_event_id} executed at step {test_design.target_timestep}.",
            },
            {
                "step": 3,
                "type": "DEGRADATION",
                "content": f"Memory {target_mem} strength dropped to {ctrl_final:.3f} in control baseline.",
            },
            {
                "step": 4,
                "type": "COUNTERFACTUAL_INTERVENTION",
                "content": f"Ablated {test_design.target_event_id} and replayed computational state trajectory.",
            },
            {
                "step": 5,
                "type": "DIVERGENCE_MEASUREMENT",
                "content": f"First divergence at step {first_div}; state L2 distance reached {div_mag:.4f}.",
            },
            {
                "step": 6,
                "type": "OUTCOME_COMPARISON",
                "content": f"Intervention outcome: {intv_final:.3f} vs Control: {ctrl_final:.3f} (Δ = {recovery_delta:+.4f}).",
            },
        ]

        evidence_chain = EvidenceChain(
            hypothesis_id=hypothesis.hypothesis_id,
            steps=chain_steps,
            verdict=causal_status.value,
        )

        test_result = TestResult(
            test_id=test_design.test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            control_trajectory=[float(v) for v in control_traj],
            intervention_trajectory=[float(v) for v in intervention_traj],
            first_divergence_step=first_div,
            divergence_magnitude=div_mag,
            control_outcome_strength=ctrl_final,
            intervention_outcome_strength=intv_final,
            recovery_delta=recovery_delta,
            causal_support=causal_status,
            evidence_summary=summary,
            affected_memories=[target_mem],
            divergence_classification="localized" if div_mag < 1.0 else "global",
        )

        return test_result, evidence_chain

    @classmethod
    def test_all_hypotheses(
        cls,
        experiment: Experiment,
        hypotheses: List[CandidateHypothesis],
        observations: List[MeasurableObservation],
    ) -> Tuple[List[TestResult], List[EvidenceChain]]:
        """Run controlled tests across all candidate hypotheses and rank by evidence quality."""
        results: List[TestResult] = []
        chains: List[EvidenceChain] = []

        for h in hypotheses:
            test_design = TestDesigner.design_test(experiment, h, observations)
            res, chain = cls.run_test(experiment, h, test_design)
            results.append(res)
            chains.append(chain)

        # Sort hypotheses by counterfactual support and supporting evidence
        hypotheses.sort(
            key=lambda hyp: (
                1 if hyp.status == CausalSupportStatus.COUNTERFACTUALLY_SUPPORTED else 0,
                hyp.counterfactual_support,
                hyp.supporting_evidence_count,
                -hyp.contradicting_evidence_count,
            ),
            reverse=True,
        )

        return results, chains

    @classmethod
    def test_hypotheses(
        cls,
        experiment: Experiment,
        hypotheses: List[CandidateHypothesis],
        observations: List[MeasurableObservation],
    ) -> List[CandidateHypothesis]:
        cls.test_all_hypotheses(experiment, hypotheses, observations)
        return hypotheses
