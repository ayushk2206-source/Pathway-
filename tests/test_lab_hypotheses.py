"""Tests for Hypothesis and Prediction system (Phase 03)."""

import pytest

from core.lab.hypotheses import (
    CompetingHypothesesGroup,
    Hypothesis,
    HypothesisStatus,
    PredictedDirection,
    Prediction,
    evaluate_prediction,
    update_hypothesis_with_evidence,
)


def test_hypothesis_creation_and_serialization():
    hyp = Hypothesis(
        hypothesis_id="h-001",
        statement="Increasing memory similarity will increase interference.",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
        confidence_before=0.6,
    )

    d = hyp.to_dict()
    assert d["hypothesis_id"] == "h-001"
    assert d["status"] == "proposed"
    assert d["predicted_direction"] == "increase"

    hyp_restored = Hypothesis.from_dict(d)
    assert hyp_restored.hypothesis_id == hyp.hypothesis_id
    assert hyp_restored.predicted_direction == hyp.predicted_direction


def test_prediction_evaluation_supported():
    pred = Prediction(
        prediction_id="p-001",
        hypothesis_id="h-001",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
    )

    # Observed increase (0.2 -> 0.7)
    eval_res = evaluate_prediction(pred, baseline_value=0.2, treatment_value=0.7)

    assert eval_res.prediction_correct is True
    assert eval_res.observed_direction == PredictedDirection.INCREASE
    assert "supported the prediction" in eval_res.verdict

    # Check hypothesis update
    hyp = Hypothesis(
        hypothesis_id="h-001",
        statement="Similarity increases interference",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
        confidence_before=0.5,
    )
    update_hypothesis_with_evidence(hyp, "exp-100", eval_res)

    assert hyp.status == HypothesisStatus.SUPPORTED
    assert hyp.confidence_after > hyp.confidence_before
    assert len(hyp.supporting_evidence) == 1
    assert "supported by current evidence" in hyp.supporting_evidence[0]


def test_prediction_evaluation_weakened():
    pred = Prediction(
        prediction_id="p-002",
        hypothesis_id="h-002",
        independent_variable="decay",
        dependent_variable="memory_retention",
        predicted_direction=PredictedDirection.INCREASE,  # Wrong prediction
    )

    # Observed decrease (retention drops with decay: 0.9 -> 0.3)
    eval_res = evaluate_prediction(pred, baseline_value=0.9, treatment_value=0.3)

    assert eval_res.prediction_correct is False
    assert eval_res.observed_direction == PredictedDirection.DECREASE
    assert "conflicted with prediction" in eval_res.verdict

    hyp = Hypothesis(
        hypothesis_id="h-002",
        statement="Decay increases retention",
        independent_variable="decay",
        dependent_variable="memory_retention",
        predicted_direction=PredictedDirection.INCREASE,
        confidence_before=0.5,
    )
    update_hypothesis_with_evidence(hyp, "exp-200", eval_res)

    assert hyp.status == HypothesisStatus.WEAKENED
    assert hyp.confidence_after < hyp.confidence_before
    assert len(hyp.contradictory_evidence) == 1


def test_competing_hypotheses_comparison():
    h1 = Hypothesis(
        hypothesis_id="h-sim",
        statement="Similarity drives interference",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
    )
    h2 = Hypothesis(
        hypothesis_id="h-decay",
        statement="Decay reduces interference",
        independent_variable="decay",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.DECREASE,
    )

    group = CompetingHypothesesGroup(
        group_id="grp-01",
        topic="Interference Drivers",
        phenomenon="Recall contamination under conflict",
        hypotheses=[h1, h2],
    )

    # Simulate experiment where interference increased
    evals = group.evaluate_experiment_results(
        experiment_id="exp-comp-01",
        observed_deltas={"interference_score": 0.45},
    )

    h1_eval = next(e for e in evals["evaluations"] if e["hypothesis_id"] == "h-sim")
    h2_eval = next(e for e in evals["evaluations"] if e["hypothesis_id"] == "h-decay")

    assert h1_eval["supports"] is True
    assert h2_eval["supports"] is False
