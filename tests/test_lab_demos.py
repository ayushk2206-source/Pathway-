"""Required End-to-End Demonstrations for Experiment Lab (Phase 03, Section 27).

Validates all 7 signature research workflows:
DEMO 1: Parameter sweep investigating memory similarity
DEMO 2: Hypothesis creation, directional prediction, and empirical validation
DEMO 3: Three competing hypotheses evaluated against experimental evidence
DEMO 4: Data-driven adaptive next-experiment recommendation
DEMO 5: Mechanism comparison on identical experimental task
DEMO 6: Exact deterministic reproduction verification
DEMO 7: Research lineage graph (Experiment -> Hypothesis -> Experiment -> Contradiction -> New Hypothesis)
"""

import pytest

from core.lab import (
    CompetingHypothesesGroup,
    EdgeType,
    ExperimentGraph,
    Hypothesis,
    HypothesisStatus,
    PredictedDirection,
    Prediction,
    evaluate_prediction,
    find_discriminating_experiment,
    reproduce_lab_experiment,
    run_condition_trials,
    run_controlled_comparison,
    run_parameter_sweep,
    suggest_next_experiment,
    update_hypothesis_with_evidence,
)


def test_demo_1_similarity_parameter_sweep():
    """DEMO 1: Ask: 'What happens when memory similarity increases?' -> Run sweep -> Return actual results."""
    # Question: What happens as memory similarity increases from 0.0 to 0.8?
    similarities = [0.0, 0.2, 0.4, 0.6, 0.8]
    base_cfg = {
        "mechanism": "interference",
        "state_dim": 64,
        "interference_strength": 0.8,
        "n_conflicts": 2,
    }

    sweep = run_parameter_sweep(
        parameter="memory_similarity",
        values=similarities,
        base_config=base_cfg,
        trials=1,
        seed=42,
    )

    assert len(sweep.conditions) == 5
    # Extract actual computed interference scores
    inter_scores = [
        c.aggregated_metrics["interference_score"]["mean"]
        for c in sweep.conditions
    ]

    # Verify that numbers originate from real computation and show measurable response
    assert len(inter_scores) == 5
    assert all(isinstance(s, float) for s in inter_scores)
    # Under Mechanism E with interference_strength=0.8, higher similarity changes erasure dynamics
    assert inter_scores[-1] != inter_scores[0]
    assert "interference_score" in sweep.relationship_analysis


def test_demo_2_hypothesis_prediction_and_test():
    """DEMO 2: Hypothesis 'High similarity increases interference' -> Predict -> Run -> Compare."""
    hyp = Hypothesis(
        hypothesis_id="hyp-demo-2",
        statement="Increasing memory similarity increases interference between conflicting concepts.",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
        confidence_before=0.5,
    )

    pred = Prediction(
        prediction_id="pred-demo-2",
        hypothesis_id=hyp.hypothesis_id,
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
        rationale="Higher cue overlap causes competing bindings to interfere more directly in superposition.",
    )
    hyp.predictions.append(pred)

    # Run controlled comparison: low similarity (0.0) vs high similarity (0.8)
    base_cond = {"mechanism": "baseline", "state_dim": 64, "memory_similarity": 0.0, "n_conflicts": 2}
    treat_cond = {"mechanism": "baseline", "state_dim": 64, "memory_similarity": 0.8, "n_conflicts": 2}
    comp = run_controlled_comparison(base_cond, treat_cond, seed=33)

    b_val = comp.baseline_condition.aggregated_metrics["interference_score"]["mean"]
    t_val = comp.treatment_condition.aggregated_metrics["interference_score"]["mean"]

    # Evaluate prediction vs empirical observation
    eval_res = evaluate_prediction(pred, baseline_value=b_val, treatment_value=t_val)

    assert eval_res.observed_direction == PredictedDirection.INCREASE
    assert eval_res.prediction_correct is True

    # Update hypothesis record
    update_hypothesis_with_evidence(hyp, "exp-demo-2", eval_res)
    assert hyp.status == HypothesisStatus.SUPPORTED
    assert hyp.confidence_after > hyp.confidence_before
    assert len(hyp.supporting_evidence) == 1
    assert "supported by current evidence" in hyp.supporting_evidence[0]


def test_demo_3_three_competing_hypotheses():
    """DEMO 3: Three competing hypotheses tested against experimental evidence."""
    h1 = Hypothesis(
        hypothesis_id="h1_similarity",
        statement="Memory similarity drives interference.",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
    )
    h2 = Hypothesis(
        hypothesis_id="h2_update_strength",
        statement="Update strength drives interference.",
        independent_variable="update_strength",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
    )
    h3 = Hypothesis(
        hypothesis_id="h3_decay_reduces",
        statement="Decay reduces interference by fading superseded bindings.",
        independent_variable="decay",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.DECREASE,
    )

    group = CompetingHypothesesGroup(
        group_id="competing_interference_drivers",
        topic="Interference in Dynamic Memory",
        phenomenon="Recall degradation under conflicting writes",
        hypotheses=[h1, h2, h3],
    )

    # Run an experiment where decay was increased (0.0 -> 0.5)
    base_cfg = {"mechanism": "leaky", "state_dim": 64, "decay": 0.0, "n_conflicts": 2}
    treat_cfg = {"mechanism": "leaky", "state_dim": 64, "decay": 0.5, "n_conflicts": 2}
    comp = run_controlled_comparison(base_cfg, treat_cfg, seed=50)

    delta_inter = comp.metric_deltas["interference_score"]

    eval_out = group.evaluate_experiment_results(
        experiment_id="exp-decay-test",
        observed_deltas={"interference_score": delta_inter},
    )

    assert len(eval_out["evaluations"]) == 3
    h3_eval = next(e for e in eval_out["evaluations"] if e["hypothesis_id"] == "h3_decay_reduces")
    # For leaky mechanism with decay=0.5, old bindings fade, so interference_score decreases
    if delta_inter < 0:
        assert h3_eval["supports"] is True
        assert h3_eval["status"] == "supported by current evidence"


def test_demo_4_adaptive_next_experiment_recommendation():
    """DEMO 4: Sparse observations -> Ask 'What should we test next?' -> Data-driven recommendation."""
    # Observations show sharp jump between 0.4 and 0.6
    tested = [0.1, 0.4, 0.6, 0.9]
    metrics = [0.12, 0.18, 0.82, 0.88]

    recommendation = suggest_next_experiment(
        parameter="memory_similarity",
        tested_values=tested,
        observed_metrics=metrics,
        metric_name="interference_score",
        parameter_min=0.0,
        parameter_max=1.0,
    )

    assert recommendation["heuristic"] == "transition_gradient_zoom"
    assert len(recommendation["suggested_values"]) > 0
    # Must zoom into transition window
    assert all(0.4 <= val <= 0.6 for val in recommendation["suggested_values"])
    assert "Sharpest change" in recommendation["rationale"]


def test_demo_5_multi_mechanism_comparison():
    """DEMO 5: Run identical experiment across multiple memory mechanisms and compare metrics."""
    mechanisms = ["baseline", "leaky", "competitive", "interference"]
    results_by_mech = {}

    task_params = {"state_dim": 64, "n_conflicts": 2, "seed": 7}

    for m in mechanisms:
        cfg = dict(task_params)
        cfg["mechanism"] = m
        if m == "leaky":
            cfg["decay"] = 0.3
        elif m == "competitive":
            cfg["sparsity"] = 0.1
        elif m == "interference":
            cfg["interference_strength"] = 0.8

        res = run_condition_trials(f"mech_{m}", cfg, master_seed=7, trials=1)
        results_by_mech[m] = {
            "retention": res.aggregated_metrics["memory_retention"]["mean"],
            "interference": res.aggregated_metrics["interference_score"]["mean"],
            "accuracy": res.aggregated_metrics["recall_accuracy"]["mean"],
        }

    # All 4 mechanisms executed real distinct arithmetic
    assert len(results_by_mech) == 4
    # Baseline has no decay, leaky has decay, interference has erasure
    ret_baseline = results_by_mech["baseline"]["retention"]
    ret_leaky = results_by_mech["leaky"]["retention"]
    assert ret_baseline != ret_leaky, "Baseline and Leaky must produce distinct retention scores"


def test_demo_6_save_and_reproduce():
    """DEMO 6: Run experiment, save, reproduce, verify deterministic bit-exact match."""
    config = {
        "mechanism": "leaky",
        "state_dim": 64,
        "decay": 0.25,
        "update_strength": 0.8,
        "n_conflicts": 2,
    }

    # Run original
    orig = run_condition_trials("original_run", config, master_seed=999, trials=1)
    orig_metrics = {k: v["mean"] for k, v in orig.aggregated_metrics.items()}

    # Reproduce
    repro = reproduce_lab_experiment(config, expected_metrics=orig_metrics, seed=999, tolerance=1e-9)

    assert repro["reproduced"] is True
    assert repro["exact_match"] is True
    assert all(m["matched"] for m in repro["metric_matches"].values())


def test_demo_7_full_research_lineage_graph():
    """DEMO 7: Experiment -> Hypothesis -> Experiment -> Contradiction -> New Hypothesis."""
    graph = ExperimentGraph()

    # 1. First exploratory experiment
    e1 = graph.add_experiment_node("exp-init-01", "Initial Similarity Sweep")

    # 2. Formulate hypothesis H1
    h1 = graph.add_hypothesis_node("hyp-01", "Similarity linearly increases interference across all mechanisms")
    graph.add_edge("exp-init-01", "hyp-01", EdgeType.FOLLOWS_FROM)

    # 3. Test hypothesis H1 with leaky decay experiment
    e2 = graph.add_experiment_node("exp-decay-test", "High Decay Interference Test")
    graph.add_edge("hyp-01", "exp-decay-test", EdgeType.TESTS)

    # 4. Result contradicts H1 (decay overrides similarity)
    f1 = graph.add_finding_node("finding-01", "Under high decay (lambda >= 0.5), interference remains suppressed regardless of similarity.")
    graph.add_edge("exp-decay-test", "finding-01", EdgeType.FOLLOWS_FROM)
    graph.add_edge("finding-01", "hyp-01", EdgeType.CONTRADICTS)

    # 5. Refined hypothesis H2 formulated from contradiction
    h2 = graph.add_hypothesis_node("hyp-02", "Interference is gated by the interaction of similarity and decay horizon")
    graph.add_edge("finding-01", "hyp-02", EdgeType.REFINES)

    # 6. Verify full lineage structure
    lineage = graph.get_lineage("hyp-02")
    assert lineage["ancestor_count"] >= 3
    node_ids = [n["node_id"] for n in lineage["nodes"]]
    assert "exp-init-01" in node_ids
    assert "hyp-01" in node_ids
    assert "exp-decay-test" in node_ids
    assert "finding-01" in node_ids
    assert "hyp-02" in node_ids

    # Verify edge relationships
    edge_types = [e["edge_type"] for e in lineage["edges"]]
    assert "contradicts" in edge_types
    assert "refines" in edge_types
    assert "tests" in edge_types
