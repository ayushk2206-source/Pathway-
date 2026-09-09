"""Data-driven experiment discovery and recommendation for Experiment Lab (Phase 03).

Provides deterministic heuristics to recommend next informative experiments (gradient zoom,
gap filling, transition refinement) and to design discriminating experiments capable of
distinguishing competing hypotheses.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .hypotheses import Hypothesis, PredictedDirection
from .variables import get_variable


def suggest_next_experiment(
    parameter: str,
    tested_values: Sequence[float],
    observed_metrics: Sequence[float],
    metric_name: str = "metric",
    parameter_min: Optional[float] = None,
    parameter_max: Optional[float] = None,
    num_suggestions: int = 3,
) -> Dict[str, Any]:
    """Identify the most informative unexplored parameter configurations using deterministic heuristics.

    Heuristics:
    1. Rapid transition zoom: locates maximum metric gradient |Δy / Δx| and samples within it.
    2. Unexplored space / gap filling: finds the widest unprobed interval.
    3. Boundary exploration: tests proximity to physical limits if unexplored.
    """
    pts = list(zip(tested_values, observed_metrics))
    pts.sort(key=lambda p: p[0])

    if not pts:
        var = get_variable(parameter)
        lo = parameter_min if parameter_min is not None else (var.minimum if var and var.minimum is not None else 0.0)
        hi = parameter_max if parameter_max is not None else (var.maximum if var and var.maximum is not None else 1.0)
        default_suggestions = [lo, (lo + hi) / 2.0, hi]
        return {
            "parameter": parameter,
            "metric_name": metric_name,
            "suggested_values": default_suggestions,
            "heuristic": "initial_exploration",
            "rationale": f"No previous data found for '{parameter}'. Probing minimum, midpoint, and maximum.",
            "expected_insight": "Establish initial baseline response curve across full range.",
        }

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    var = get_variable(parameter)
    p_min = parameter_min if parameter_min is not None else (var.minimum if var and var.minimum is not None else min(xs))
    p_max = parameter_max if parameter_max is not None else (var.maximum if var and var.maximum is not None else max(xs))

    suggestions: List[float] = []
    heuristic_used = ""
    rationale = ""

    # Strategy 1: Find steepest gradient interval if we have >= 2 points
    if len(xs) >= 2:
        grads: List[float] = []
        intervals: List[Tuple[float, float]] = []

        for i in range(len(xs) - 1):
            dx = xs[i + 1] - xs[i]
            if dx > 1e-6:
                dy = abs(ys[i + 1] - ys[i])
                grads.append(dy / dx)
                intervals.append((xs[i], xs[i + 1]))

        if grads:
            max_grad = max(grads)
            median_grad = float(np.median(grads))
            best_idx = int(np.argmax(grads))
            best_interval = intervals[best_idx]

            # A sharp localized transition requires a gradient spike compared to median gradient
            is_sharp_spike = (len(grads) >= 3 and max_grad > 1.5 * (median_grad + 1e-6) and max_grad > 0.3) or (len(grads) < 3 and max_grad > 0.5)

            if is_sharp_spike and best_interval:
                x0, x1 = best_interval
                span = x1 - x0
                # Sample points inside the transition zone
                candidates = [
                    round(x0 + 0.25 * span, 4),
                    round(x0 + 0.50 * span, 4),
                    round(x0 + 0.75 * span, 4),
                ]
                suggestions = [c for c in candidates if c not in xs][:num_suggestions]
                if suggestions:
                    heuristic_used = "transition_gradient_zoom"
                    rationale = (
                        f"Sharpest change in '{metric_name}' (|slope|={max_grad:.2f}) occurred between "
                        f"{x0} and {x1}. Probing interior points to resolve the transition region."
                    )

    # Strategy 2: If no steep gradient or suggestions empty, find the widest gap
    if not suggestions and len(xs) >= 2:
        widest_gap = -1.0
        widest_interval: Optional[Tuple[float, float]] = None
        for i in range(len(xs) - 1):
            gap = xs[i + 1] - xs[i]
            if gap > widest_gap:
                widest_gap = gap
                widest_interval = (xs[i], xs[i + 1])

        if widest_interval and widest_gap > 0.05:
            x0, x1 = widest_interval
            mid = round((x0 + x1) / 2.0, 4)
            suggestions = [mid]
            heuristic_used = "unexplored_gap_filling"
            rationale = f"Largest unexplored gap in '{parameter}' is [{x0}, {x1}] (width={widest_gap:.3f}). Probing midpoint."

    # Strategy 3: Boundary exploration
    if len(suggestions) < num_suggestions:
        if p_min is not None and abs(min(xs) - p_min) > 0.1:
            boundary_probe = round(p_min + 0.05 * (p_max - p_min), 4)
            if boundary_probe not in xs and boundary_probe not in suggestions:
                suggestions.append(boundary_probe)
        if p_max is not None and abs(p_max - max(xs)) > 0.1:
            boundary_probe = round(p_max - 0.05 * (p_max - p_min), 4)
            if boundary_probe not in xs and boundary_probe not in suggestions:
                suggestions.append(boundary_probe)

    if not suggestions:
        # Fallback fine perturbation
        suggestions = [round(xs[0] + 0.05, 4), round(xs[-1] - 0.05, 4)]
        heuristic_used = "fine_grid_perturbation"
        rationale = "Previous parameter space densely sampled; suggesting micro-perturbations."

    return {
        "parameter": parameter,
        "metric_name": metric_name,
        "suggested_values": suggestions[:num_suggestions],
        "heuristic": heuristic_used or "adaptive_sampling",
        "rationale": rationale,
        "expected_insight": (
            f"Clarify non-linear response boundaries and inflection points for '{metric_name}'."
        ),
    }


def find_discriminating_experiment(
    hypotheses: Sequence[Hypothesis],
    base_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Design a controlled experiment where competing hypotheses make diverging predictions.

    Example:
    Hypothesis 1 predicts: memory_similarity drives interference.
    Hypothesis 2 predicts: update_strength drives interference.
    Discriminating Experiment:
    Test Condition A: High similarity (0.8), low update strength (0.2).
    Test Condition B: Low similarity (0.1), high update strength (1.8).
    If H1 is dominant, Condition A will exhibit higher interference.
    If H2 is dominant, Condition B will exhibit higher interference.
    """
    if len(hypotheses) < 2:
        return {
            "valid": False,
            "message": "At least two competing hypotheses are required to find a discriminating experiment.",
        }

    h1, h2 = hypotheses[0], hypotheses[1]
    base = dict(base_config or {})

    var1 = h1.independent_variable
    var2 = h2.independent_variable

    # Case 1: Competing hypotheses test DIFFERENT independent variables on the same dependent metric
    if var1 != var2 and h1.dependent_variable == h2.dependent_variable:
        metric = h1.dependent_variable
        # Design a 2x2 counterbalanced factorial condition
        cond_A = dict(base)
        cond_A[var1] = 0.8  # high var1
        cond_A[var2] = 0.2  # low var2

        cond_B = dict(base)
        cond_B[var1] = 0.1  # low var1
        cond_B[var2] = 1.5  # high var2

        predicted_H1 = f"Condition A will show higher '{metric}' than Condition B because '{var1}' is high."
        predicted_H2 = f"Condition B will show higher '{metric}' than Condition A because '{var2}' is high."
        explanation = (
            f"This experiment counterbalances '{var1}' and '{var2}'. "
            f"Because '{h1.statement}' relies on '{var1}' while '{h2.statement}' relies on '{var2}', "
            f"the two hypotheses predict opposing relative outcomes between Condition A and Condition B."
        )

        return {
            "valid": True,
            "discriminating_strategy": "counterbalanced_variable_orthogonalization",
            "hypotheses_tested": [h1.hypothesis_id, h2.hypothesis_id],
            "target_metric": metric,
            "condition_a": {"label": f"high_{var1}_low_{var2}", "parameters": cond_A},
            "condition_b": {"label": f"low_{var1}_high_{var2}", "parameters": cond_B},
            "predicted_outcomes": {
                h1.hypothesis_id: predicted_H1,
                h2.hypothesis_id: predicted_H2,
            },
            "scientific_rationale": explanation,
            "expected_information_gain": "Distinguishes primary causal driver versus confounding covariate.",
        }

    # Case 2: Same independent variable, but conflicting predicted direction
    if var1 == var2 and h1.predicted_direction != h2.predicted_direction:
        metric = h1.dependent_variable
        cond_A = dict(base)
        cond_A[var1] = 0.1
        cond_B = dict(base)
        cond_B[var1] = 0.9

        return {
            "valid": True,
            "discriminating_strategy": "directional_falsification_sweep",
            "hypotheses_tested": [h1.hypothesis_id, h2.hypothesis_id],
            "target_metric": metric,
            "condition_a": {"label": f"{var1}_low", "parameters": cond_A},
            "condition_b": {"label": f"{var1}_high", "parameters": cond_B},
            "predicted_outcomes": {
                h1.hypothesis_id: f"{h1.hypothesis_id} predicts metric will {h1.predicted_direction.value}",
                h2.hypothesis_id: f"{h2.hypothesis_id} predicts metric will {h2.predicted_direction.value}",
            },
            "scientific_rationale": (
                f"Hypotheses make directly opposing directional predictions for '{metric}' as '{var1}' increases."
            ),
            "expected_information_gain": "Falsifies the hypothesis whose predicted sign does not match empirical delta.",
        }

    # Default general fallback
    return {
        "valid": True,
        "discriminating_strategy": "controlled_isolation",
        "hypotheses_tested": [h.hypothesis_id for h in hypotheses],
        "target_metric": h1.dependent_variable,
        "scientific_rationale": "Holding all secondary parameters strictly invariant while isolating independent variables.",
        "expected_information_gain": "Measures differential effect size between conditions.",
    }
