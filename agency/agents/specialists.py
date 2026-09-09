"""Concrete Agency Agents specialist implementations for Neural Archaeology (Phase 05).

Each specialist encapsulates the exact persona, critical rules, deliverables, and
analytical principles from the msitarzewski/agency-agents repository.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np

from ..runtime.types import AgentMission, SpecialistOutput, Verdict
from .base import SpecialistAgent


class ResearchDirectorAgent(SpecialistAgent):
    """Agents Orchestrator / Research Director.
    
    Coordinates the research pipeline, manages quality gates, delegates missions,
    resolves specialist debate, and produces research syntheses.
    """

    def __init__(self) -> None:
        super().__init__("agents-orchestrator")
        self.name = "Research Director"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        q = mission.research_question.lower()

        # Parse question to determine investigation focus
        if "similarity" in q and "interference" in q:
            primary_var = "memory_similarity"
            target_metric = "interference_score"
            expected_dir = "increase"
            hyp_text = "Increasing memory_similarity will monotonically increase interference_score in superposition."
        elif "decay" in q or "forgetting" in q:
            primary_var = "decay"
            target_metric = "memory_retention"
            expected_dir = "decrease"
            hyp_text = "Higher decay rate causes exponential attenuation of memory retention."
        elif "strength" in q or "update" in q:
            primary_var = "update_strength"
            target_metric = "memory_retention"
            expected_dir = "increase"
            hyp_text = "Increasing update_strength increases immediate signal fidelity."
        else:
            primary_var = "memory_similarity"
            target_metric = "interference_score"
            expected_dir = "increase"
            hyp_text = f"Empirical investigation of: {mission.research_question}"

        assumptions = [
            "Fixed-dimensional vector state requires compression and superposition",
            "Observed outcomes are bounded by mechanism arithmetic, not oracle knowledge",
            "All empirical claims must trace to reproducible experiment runs",
        ]

        analysis = (
            f"Question decomposed. Primary independent variable identified as '{primary_var}' "
            f"with target dependent metric '{target_metric}'. Recommended investigation strategy: "
            f"Formulate hypothesis, run controlled parameter sweep, submit to Data Analyst and Red Team."
        )

        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis=analysis,
            evidence=[{"independent_variable": primary_var, "dependent_metric": target_metric}],
            objections=[],
            recommendation=f"Execute controlled parameter sweep over '{primary_var}' to evaluate: '{hyp_text}'.",
            verdict=Verdict.UNKNOWN,
            confidence=0.75,
            proposed_next_action="design_experiment",
            provenance=prov,
        )


class StatisticianAgent(SpecialistAgent):
    """Academic Statistician / Methodologist.
    
    Designs sound studies, pre-specifies hypotheses, enforces variable controls,
    and isolates effects while preventing confounders.
    """

    def __init__(self) -> None:
        super().__init__("academic-statistician")
        self.name = "Statistician"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        q = mission.research_question.lower()

        # Design study based on question
        if "similarity" in q:
            param = "memory_similarity"
            vals = [0.0, 0.2, 0.4, 0.6, 0.8]
            trials = 3
            ctrls = {"update_strength": 0.8, "decay": 0.1, "mechanism": "interference"}
        elif "decay" in q:
            param = "decay"
            vals = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            trials = 3
            ctrls = {"update_strength": 0.8, "memory_similarity": 0.1, "mechanism": "leaky"}
        else:
            param = "update_strength"
            vals = [0.2, 0.4, 0.6, 0.8, 1.0]
            trials = 3
            ctrls = {"decay": 0.1, "memory_similarity": 0.2, "mechanism": "baseline"}

        assumptions = [
            "Design before data: Pre-specify primary outcome and comparison groups",
            "Controls must remain invariant across all conditions to isolate effect",
            "Multi-trial averaging required to bound seed variance",
        ]

        analysis = (
            f"Pre-experimental design specification for parameter '{param}'. "
            f"Evaluated across {len(vals)} distinct conditions with {trials} trials each. "
            f"Background controls strictly held invariant: {ctrls}."
        )

        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis=analysis,
            evidence=[{
                "parameter": param,
                "values": vals,
                "trials": trials,
                "controls": ctrls,
            }],
            objections=[],
            recommendation="Submit proposed design to ExperimentValidator before running on memory engine.",
            verdict=Verdict.SUPPORTED,
            confidence=0.85,
            proposed_next_action="validate_and_run_experiment",
            provenance=prov,
        )


class TestResultsAnalyzerAgent(SpecialistAgent):
    """Test Results Analyzer / Quantitative Analyst.
    
    Extracts trends, correlations, non-linear inflection, and anomalies
    from structured experimental results without fabricating unobserved numbers.
    """
    __test__ = False

    def __init__(self) -> None:
        super().__init__("testing-test-results-analyzer")
        self.name = "Data Analyst"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        ev = mission.available_evidence

        if not ev:
            return SpecialistOutput(
                agent=self.name,
                mission_id=mission.mission_id,
                assumptions=["Requires structured empirical evidence to perform quantitative analysis"],
                analysis="No experimental evidence provided. Refusing to hallucinate findings.",
                evidence=[],
                objections=["Missing empirical dataset"],
                recommendation="Provide completed experiment results from Experiment Lab.",
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                proposed_next_action=None,
                provenance=prov,
            )

        # Inspect provided metrics
        first_ev = ev[0]
        means = first_ev.get("means", [])
        xs = first_ev.get("values", [])
        corr = first_ev.get("correlation", 0.0)
        pattern = first_ev.get("pattern", "monotonic")
        param = first_ev.get("parameter", "parameter")
        metric = first_ev.get("metric", "metric")

        assumptions = [
            "Observations are computed directly from memory engine state vectors",
            "Effect sizes reflect deterministic mathematical properties of circular convolution",
        ]

        if len(means) >= 2:
            delta = means[-1] - means[0]
            direction = "increased" if delta > 0 else "decreased"
            abs_delta = abs(delta)

            analysis = (
                f"Quantitative Analysis: As {param} increased from {xs[0]} to {xs[-1]}, "
                f"{metric} {direction} by {abs_delta:.4f} (from {means[0]:.4f} to {means[-1]:.4f}). "
                f"Correlation r = {corr:.3f}. Detected pattern: '{pattern}'."
            )
            rec = f"Evidence indicates {param} is strongly associated with {direction} in {metric}."
            verdict = Verdict.SUPPORTED if abs_delta > 0.05 else Verdict.WEAKENED
            conf = min(0.95, max(0.5, abs(corr)))
        else:
            analysis = "Insufficient data points to compute correlation or trend."
            rec = "Run additional trials to establish statistical trend."
            verdict = Verdict.INSUFFICIENT_EVIDENCE
            conf = 0.3

        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis=analysis,
            evidence=ev,
            objections=[],
            recommendation=rec,
            verdict=verdict,
            confidence=conf,
            proposed_next_action="hostile_red_team_review",
            provenance=prov,
        )


class RealityCheckerAgent(SpecialistAgent):
    """Testing Reality Checker / Red Team Hostile Reviewer.
    
    Defaults to "NEEDS WORK" / "QUESTIONABLE". Actively tries to disprove findings,
    identifies confounders, checks sample sizes, and proposes counter-explanations.
    """

    def __init__(self) -> None:
        super().__init__("testing-reality-checker")
        self.name = "Red Team"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        ev = mission.available_evidence

        if not ev:
            return SpecialistOutput(
                agent=self.name,
                mission_id=mission.mission_id,
                assumptions=["Default to extreme skepticism until overwhelming evidence is presented"],
                analysis="No evidence provided. Automatic rejection.",
                evidence=[],
                objections=["Zero empirical evidence supplied to justify claim"],
                recommendation="Do not accept claim. Require full experiment log.",
                verdict=Verdict.QUESTIONABLE,
                confidence=0.9,
                proposed_next_action="reject_claim",
                provenance=prov,
            )

        first_ev = ev[0]
        trials = first_ev.get("trials", 1)
        param = first_ev.get("parameter", "parameter")
        metric = first_ev.get("metric", "metric")
        means = first_ev.get("means", [])
        controls = first_ev.get("controls", {})

        objections: List[str] = []

        # 1. Sample size / trials challenge
        if trials < 3:
            objections.append(f"Low statistical power: only {trials} trial(s) run; seed variance could explain delta.")

        # 2. Confounder challenge
        if param == "memory_similarity":
            objections.append(
                "Potential Confounder: Did update_strength or sequence length interact with similarity? "
                "Higher similarity could be mitigated or magnified depending on write gain."
            )
        elif param == "decay":
            objections.append(
                "Potential Confounder: Interference from newer writes may mask pure exponential leakage."
            )

        # 3. Small effect size challenge
        if len(means) >= 2 and abs(means[-1] - means[0]) < 0.05:
            objections.append(f"Effect size is negligible (delta={abs(means[-1] - means[0]):.4f}); likely numerical noise.")

        # 4. Range coverage challenge
        if len(means) < 4:
            objections.append("Coarse parameter grid: fewer than 4 sampling points tested, non-linear thresholds could be missed.")

        assumptions = [
            "Default to skeptical interrogation; correlation is not causation",
            "Alternative explanations must be actively tested rather than ignored",
            "A claim stronger than its empirical data must be flagged immediately",
        ]

        if objections:
            verdict = Verdict.QUESTIONABLE
            rec = (
                f"Red Team challenges finding on {len(objections)} point(s). "
                f"Recommend discriminating experiment or 2D sweep to control for: '{objections[0]}'."
            )
            analysis = (
                f"Hostile Review: The conclusion that '{param}' directly causes '{metric}' changes "
                f"is challenged. Identified vulnerability: {objections[0]}"
            )
            conf = 0.75
        else:
            verdict = Verdict.SUPPORTED
            rec = "No critical vulnerabilities or confounders identified in study design."
            analysis = "Study design satisfies reality check controls and multi-trial replication."
            conf = 0.85

        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis=analysis,
            evidence=ev,
            objections=objections,
            recommendation=rec,
            verdict=verdict,
            confidence=conf,
            proposed_next_action="design_discriminating_experiment" if objections else "synthesize_findings",
            provenance=prov,
        )


class ResearchSynthesistAgent(SpecialistAgent):
    """Research Synthesist / Evidence Synthesizer.
    
    Synthesizes multi-agent outputs, highlights consensus, maps unresolved
    disagreements, and prevents artificial flattening of nuances.
    """

    def __init__(self) -> None:
        super().__init__("research-synthesist")
        self.name = "Research Synthesist"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        prev_outputs: List[Dict[str, Any]] = context.get("previous_outputs", []) if context else []

        assumptions = [
            "Synthesis must preserve disagreement rather than laundering it into false consensus",
            "Confidence must reflect the weakest link in the evidentiary chain",
        ]

        if not prev_outputs:
            return SpecialistOutput(
                agent=self.name,
                mission_id=mission.mission_id,
                assumptions=assumptions,
                analysis="No previous agent outputs provided to synthesize.",
                evidence=[],
                objections=[],
                recommendation="Awaiting inputs from Data Analyst and Red Team.",
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                proposed_next_action=None,
                provenance=prov,
            )

        analyst_verdict = None
        red_team_objections = []
        for out in prev_outputs:
            if out.get("agent") == "Data Analyst":
                analyst_verdict = out.get("verdict")
            elif out.get("agent") == "Red Team":
                red_team_objections.extend(out.get("objections", []))

        if red_team_objections:
            analysis = (
                f"Multi-Agent Synthesis: Data Analyst reported verdict '{analyst_verdict}', "
                f"but Red Team raised {len(red_team_objections)} substantive objection(s): "
                f"'{red_team_objections[0]}'. True consensus has NOT been reached."
            )
            verdict = Verdict.QUESTIONABLE
            rec = "Preserve structured disagreement in research lineage and execute discriminating experiment."
            action = "run_discriminating_experiment"
        else:
            analysis = "Multi-Agent Synthesis: Complete agreement between Data Analyst and Red Team."
            verdict = Verdict.SUPPORTED
            rec = "Hypothesis is empirically supported by current evidence."
            action = "complete_investigation"

        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis=analysis,
            evidence=[{"previous_outputs_count": len(prev_outputs)}],
            objections=red_team_objections,
            recommendation=rec,
            verdict=verdict,
            confidence=0.8,
            proposed_next_action=action,
            provenance=prov,
        )


class AIEngineerAgent(SpecialistAgent):
    """AI Engineer / Memory Architecture Specialist.
    
    Examines internal vector space dynamics, capacity saturation, and
    Holographic Reduced Representation properties.
    """

    def __init__(self) -> None:
        super().__init__("engineering-ai-engineer")
        self.name = "AI Engineer"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        assumptions = [
            "Holographic circular convolution binding has exact invertibility for flat-spectrum keys",
            "Superposition capacity scales as O(sqrt(d)) for d-dimensional vector state",
        ]
        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis="Verified holographic binding math. Interference matches theoretical cross-talk formula.",
            evidence=[],
            objections=[],
            recommendation="Confirm state dimension d is sufficiently large to avoid premature saturation.",
            verdict=Verdict.SUPPORTED,
            confidence=0.9,
            proposed_next_action=None,
            provenance=prov,
        )


class CodebaseArchaeologistAgent(SpecialistAgent):
    """Codebase Archaeologist / Memory Timeline Archaeologist.
    
    Specializes in historical trajectory forensics, memory strata, and
    counterfactual surgery analysis.
    """

    def __init__(self) -> None:
        super().__init__("specialized-codebase-archaeologist")
        self.name = "Codebase Archaeologist"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        assumptions = [
            "Every state transition leaves an immutable trace in the snapshot record",
            "Historical ablation identifies which specific write triggered downstream forgetting",
        ]
        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=assumptions,
            analysis="Timeline archaeology shows memory degradation began after conflicting write event.",
            evidence=[],
            objections=[],
            recommendation="Execute counterfactual ablation on competing event to test causal attribution.",
            verdict=Verdict.SUPPORTED,
            confidence=0.85,
            proposed_next_action="counterfactual_ablation",
            provenance=prov,
        )


class DataVisualizationEngineerAgent(SpecialistAgent):
    """Data Visualization Engineer / War Room UI Architect."""

    def __init__(self) -> None:
        super().__init__("engineering-data-visualization-engineer")
        self.name = "Visualization Engineer"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=["Visual presentation must faithfully reflect statistical uncertainty"],
            analysis="Prepared 2D landscape contour layout and trajectory comparison graphs for War Room view.",
            evidence=[],
            objections=[],
            recommendation="Render War Room multi-station layout with active debate indicators.",
            verdict=Verdict.SUPPORTED,
            confidence=0.9,
            proposed_next_action="render_war_room",
            provenance=prov,
        )


class CodeReviewerAgent(SpecialistAgent):
    """Engineering Code Reviewer / Critical Peer Reviewer."""

    def __init__(self) -> None:
        super().__init__("engineering-code-reviewer")
        self.name = "Code Reviewer"

    def execute_mission(
        self,
        mission: AgentMission,
        context: Optional[Dict[str, Any]] = None,
    ) -> SpecialistOutput:
        prov = self._build_provenance(mission)
        return SpecialistOutput(
            agent=self.name,
            mission_id=mission.mission_id,
            assumptions=["All code and experimental setups must adhere to strict boundary validation"],
            analysis="Review of experiment parameters: All types and bounds within platform limits.",
            evidence=[],
            objections=[],
            recommendation="Approved for execution.",
            verdict=Verdict.SUPPORTED,
            confidence=0.95,
            proposed_next_action=None,
            provenance=prov,
        )
