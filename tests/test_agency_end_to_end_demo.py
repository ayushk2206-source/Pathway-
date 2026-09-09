"""End-to-end canonical multi-agent scientific demonstration required for Phase 05."""

import pytest

from agency.orchestration.investigation import ResearchDirector, run_research_investigation
from agency.runtime.types import InvestigationStatus, Verdict


def test_canonical_multi_agent_demonstration():
    """Execute the complete 11-stage canonical demonstration for Phase 05:

    QUESTION: "Does increasing memory similarity increase interference?"
    1. Research Director creates hypotheses.
    2. Experiment Designer proposes experiment.
    3. Experiment Lab validates it.
    4. Memory Engine executes it.
    5. Data Analyst analyzes results.
    6. Red Team attempts to invalidate conclusion.
    7. Research Director identifies disagreement.
    8. Discriminating experiment / counterfactual investigation performed.
    9. Final synthesis produced with evidence.
    10. Next experiment recommended.
    """
    question = "Does increasing memory similarity increase interference?"

    director = ResearchDirector(investigation_id="inv_demo_canonical")
    inv = director.run_investigation(question, max_rounds=2)

    # 1. Pipeline reached completed status
    assert inv.status == InvestigationStatus.COMPLETED
    assert inv.round_number >= 2

    # 2. Hypothesis was formulated
    assert len(inv.initial_hypotheses) >= 1
    hyp = inv.initial_hypotheses[0]
    assert hyp["independent_variable"] == "memory_similarity"
    assert hyp["dependent_variable"] == "interference_score"
    assert hyp["predicted_direction"] == "increase"

    # 3. Experiment Lab executed real sweep on Memory Engine
    assert len(inv.experiments) >= 1
    exp = inv.experiments[0]
    assert exp["parameter"] == "memory_similarity"
    assert len(exp["values"]) >= 4
    assert len(exp["means"]) == len(exp["values"])
    # In circular convolution superposition, higher similarity monotonically increases interference!
    assert exp["means"][-1] > exp["means"][0]

    # 4. Data Analyst performed quantitative analysis
    analyst_outputs = [o for o in inv.agent_outputs if o["agent"] == "Data Analyst"]
    assert len(analyst_outputs) >= 1
    assert analyst_outputs[0]["verdict"] == Verdict.SUPPORTED.value
    assert analyst_outputs[0]["confidence"] >= 0.7

    # 5. Red Team performed hostile review and raised confounder objection
    red_team_outputs = [o for o in inv.agent_outputs if o["agent"] == "Red Team"]
    assert len(red_team_outputs) >= 1
    assert red_team_outputs[0]["verdict"] == Verdict.QUESTIONABLE.value
    assert len(red_team_outputs[0]["objections"]) >= 1

    # 6. Structured disagreement captured
    assert len(inv.disagreements) >= 1
    d = inv.disagreements[0]
    assert d["agent_a"] == "Data Analyst"
    assert d["agent_b"] == "Red Team"
    assert d["resolved"] is True  # Resolved by round 2 counterfactual!

    # 7. Counterfactual engine executed discriminating investigation
    assert len(inv.counterfactuals) >= 1
    cf = inv.counterfactuals[0]
    assert "divergence_l2" in cf
    assert cf["divergence_l2"] > 0.0

    # 8. Research Synthesis produced with honest evidence bounds
    synth = inv.synthesis
    assert synth["verdict"] == Verdict.SUPPORTED.value
    assert synth["supporting_evidence_count"] >= 2
    assert "interference" in synth["summary"].lower() or "similarity" in synth["summary"].lower()

    # 9. Next experiment recommended by specialists
    assert len(inv.next_actions) >= 1
    assert any("2d" in a.lower() or "landscape" in a.lower() or "sweep" in a.lower() for a in inv.next_actions)

    # 10. Research Memory and Graph populated
    assert len(director.memory.experiments) >= 1
    assert len(director.memory.counterfactuals) >= 1
    assert len(director.memory.disagreements) >= 1

    graph_dict = director.graph_builder.to_dict()
    node_types = {n["node_type"] for n in graph_dict["nodes"].values()}
    assert "question" in node_types
    assert "hypothesis" in node_types
    assert "experiment" in node_types
    assert "observation" in node_types
    assert "agent_analysis" in node_types
    assert "counterfactual" in node_types
    assert "conclusion" in node_types
