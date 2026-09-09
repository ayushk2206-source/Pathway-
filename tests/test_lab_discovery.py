"""Tests for Next Experiment Suggestion and Discriminating Experiments (Phase 03)."""

import pytest

from core.lab.discovery import (
    find_discriminating_experiment,
    suggest_next_experiment,
)
from core.lab.hypotheses import Hypothesis, PredictedDirection


def test_suggest_next_experiment_transition_zoom():
    # Steep transition between 0.4 and 0.6 (metric jumps from 0.15 to 0.85)
    tested_x = [0.1, 0.4, 0.6, 0.9]
    observed_y = [0.1, 0.15, 0.85, 0.9]

    sugg = suggest_next_experiment(
        parameter="memory_similarity",
        tested_values=tested_x,
        observed_metrics=observed_y,
        metric_name="interference_score",
        parameter_min=0.0,
        parameter_max=1.0,
    )

    assert sugg["heuristic"] == "transition_gradient_zoom"
    # Suggested values must fall between 0.4 and 0.6
    for val in sugg["suggested_values"]:
        assert 0.4 <= val <= 0.6
    assert "Sharpest change" in sugg["rationale"]


def test_suggest_next_experiment_gap_filling():
    # Linear data with an obvious gap between 0.2 and 0.8
    tested_x = [0.0, 0.1, 0.2, 0.8, 0.9, 1.0]
    observed_y = [0.0, 0.1, 0.2, 0.8, 0.9, 1.0]

    sugg = suggest_next_experiment(
        parameter="decay",
        tested_values=tested_x,
        observed_metrics=observed_y,
        metric_name="memory_retention",
        parameter_min=0.0,
        parameter_max=1.0,
    )

    assert sugg["heuristic"] == "unexplored_gap_filling"
    # Should recommend midpoint around 0.5
    assert any(0.4 <= v <= 0.6 for v in sugg["suggested_values"])


def test_find_discriminating_experiment_orthogonal_drivers():
    h1 = Hypothesis(
        hypothesis_id="h-sim",
        statement="Similarity drives interference",
        independent_variable="memory_similarity",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
    )
    h2 = Hypothesis(
        hypothesis_id="h-strength",
        statement="Update strength drives interference",
        independent_variable="update_strength",
        dependent_variable="interference_score",
        predicted_direction=PredictedDirection.INCREASE,
    )

    disc = find_discriminating_experiment([h1, h2], base_config={"mechanism": "interference"})

    assert disc["valid"] is True
    assert disc["discriminating_strategy"] == "counterbalanced_variable_orthogonalization"
    assert "condition_a" in disc
    assert "condition_b" in disc

    cond_a = disc["condition_a"]["parameters"]
    cond_b = disc["condition_b"]["parameters"]

    # Condition A: high similarity, low update strength
    # Condition B: low similarity, high update strength
    assert cond_a["memory_similarity"] > cond_b["memory_similarity"]
    assert cond_a["update_strength"] < cond_b["update_strength"]
    assert "scientific_rationale" in disc
