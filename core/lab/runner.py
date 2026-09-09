"""Controlled experiment runner for Experiment Lab (Phase 03).

Orchestrates real execution against the underlying Phase 01 / Phase 02 memory engine.
Provides multi-trial repeated execution with deterministic derived seeds, 1D sweeps,
2D grids, baseline vs treatment comparisons, and exact reproduction verification.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from ..analysis import compare_states
from ..experiment import Experiment, ExperimentConfig
from ..mechanisms import MechanismParams
from ..runner import run_experiment
from ..task import TaskConfig
from .analysis import (
    aggregate_metric_samples,
    analyze_sweep_relationship,
    cohens_d,
    detect_nonlinear_patterns,
)
from .models import (
    ComparisonResult,
    ConditionResult,
    ExperimentStatus,
    GridResult,
    LabExperiment,
    SweepResult,
    TrialRecord,
)
from .validation import ExperimentValidationError, ExperimentValidator


def derive_trial_seed(master_seed: int, trial_index: int) -> int:
    """Deterministically derive a pseudo-random seed for a specific trial index."""
    payload = f"{int(master_seed)}:trial:{int(trial_index)}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()[:8]
    return int.from_bytes(digest, "big") % 2_147_483_647


def _build_core_config(
    params_dict: Dict[str, Any],
    seed: int,
) -> ExperimentConfig:
    """Translate high-level experimental knobs into a deterministic ExperimentConfig."""
    merged = dict(params_dict)

    mech_name = str(merged.get("mechanism", "leaky"))

    # Mechanism parameters
    m_params = MechanismParams(
        state_dim=int(merged.get("state_dim", 128)),
        update_strength=float(merged.get("update_strength", 1.0)),
        memory_strength=float(merged.get("memory_strength", 1.0)),
        decay=float(merged.get("decay", 0.2 if mech_name == "leaky" else 0.0)),
        interference_strength=float(merged.get("interference_strength", 0.5)),
        sparsity=float(merged.get("sparsity", 0.1)),
        normalize_state=bool(merged.get("normalize_state", False)),
        input_noise=float(merged.get("input_noise", 0.0)),
    )

    # Task parameters
    sim = float(merged.get("memory_similarity", merged.get("object_similarity", 0.0)))
    sym_sim = float(merged.get("symbol_similarity", 0.0))

    t_config = TaskConfig(
        seed=seed,
        d=m_params.state_dim,
        n_objects=int(merged.get("n_objects", 6)),
        n_symbols=int(merged.get("n_symbols", 4)),
        n_conflicts=int(merged.get("n_conflicts", 2)),
        object_similarity=sim,
        symbol_similarity=sym_sim,
        cycles=int(merged.get("cycles", 1)),
        order=str(merged.get("order", "interleaved")),
        probe_original=bool(merged.get("probe_original", True)),
        input_noise=float(merged.get("input_noise", 0.0)),
        vector_source="random",
    )

    # If explicit text events/queries or vector source is specified
    if "vector_source" in merged:
        t_config.vector_source = str(merged["vector_source"])
    if "events" in merged:
        t_config.events = merged["events"]
    if "queries" in merged:
        t_config.queries = merged["queries"]

    return ExperimentConfig(
        seed=seed,
        mechanism=mech_name,
        params=m_params,
        task=t_config,
        update_steps_per_event=int(merged.get("update_steps_per_event", 1)),
    )


def run_condition_trials(
    condition_label: str,
    parameter_values: Dict[str, Any],
    master_seed: int = 42,
    trials: int = 1,
) -> ConditionResult:
    """Run an experimental condition across 1 or more trials with derived seeds."""
    trial_records: List[TrialRecord] = []
    metrics_accumulator: Dict[str, List[float]] = {}
    representative_exp: Optional[Experiment] = None

    for t_idx in range(trials):
        trial_seed = derive_trial_seed(master_seed, t_idx) if trials > 1 else master_seed
        cfg = _build_core_config(parameter_values, seed=trial_seed)

        # Run real Phase 01/02 computation
        exp = run_experiment(cfg)
        if representative_exp is None:
            representative_exp = exp

        # Filter out details from metrics dict for scalar stats
        clean_metrics = {
            k: float(v)
            for k, v in exp.metrics.items()
            if isinstance(v, (int, float)) and not np.isnan(v)
        }

        for k, v in clean_metrics.items():
            metrics_accumulator.setdefault(k, []).append(v)

        trial_records.append(
            TrialRecord(
                trial_index=t_idx,
                seed=trial_seed,
                underlying_experiment_id=exp.experiment_id,
                metrics=clean_metrics,
                provenance={
                    "master_seed": master_seed,
                    "condition": condition_label,
                    "mechanism": exp.mechanism,
                    "version": exp.version,
                    "created_at": exp.created_at,
                },
            )
        )

    # Calculate statistics across trials
    aggregated: Dict[str, Dict[str, float]] = {}
    for m_name, samples in metrics_accumulator.items():
        aggregated[m_name] = aggregate_metric_samples(samples)

    return ConditionResult(
        condition_label=condition_label,
        parameter_values=parameter_values,
        trials=trial_records,
        aggregated_metrics=aggregated,
        representative_experiment_id=representative_exp.experiment_id if representative_exp else None,
    )


def run_parameter_sweep(
    parameter: str,
    values: Sequence[Any],
    base_config: Optional[Dict[str, Any]] = None,
    trials: int = 1,
    seed: int = 42,
    **kwargs: Any,
) -> SweepResult:
    """Execute a 1-dimensional parameter sweep with controlled variables held constant."""
    if base_config is None and "base_params" in kwargs:
        base_config = kwargs["base_params"]
    if "master_seed" in kwargs:
        seed = kwargs["master_seed"]

    val_res = ExperimentValidator.validate_parameter_sweep(parameter, values, base_config, trials=trials)
    if not val_res.valid:
        raise ExperimentValidationError(val_res.errors)

    base = dict(base_config or {})
    conditions: List[ConditionResult] = []

    for val in values:
        cond_params = dict(base)
        cond_params[parameter] = val
        label = f"{parameter}={val}"
        cond_result = run_condition_trials(
            condition_label=label,
            parameter_values=cond_params,
            master_seed=seed,
            trials=trials,
        )
        conditions.append(cond_result)

    # Numeric relationship & pattern detection for primary metrics
    analysis_results: Dict[str, Any] = {}
    pattern_results: Dict[str, Any] = {}

    numeric_x = []
    try:
        numeric_x = [float(v) for v in values]
    except (ValueError, TypeError):
        numeric_x = []

    if len(numeric_x) == len(values) and len(numeric_x) >= 2:
        candidate_metrics = [
            "memory_retention",
            "interference_score",
            "recall_accuracy",
            "recovery_score",
            "state_drift",
        ]
        for metric_key in candidate_metrics:
            if conditions and metric_key in conditions[0].aggregated_metrics:
                y_series = [c.aggregated_metrics[metric_key]["mean"] for c in conditions]
                analysis_results[metric_key] = analyze_sweep_relationship(
                    numeric_x, y_series, x_name=parameter, y_name=metric_key
                )
                pattern_results[metric_key] = detect_nonlinear_patterns(numeric_x, y_series)

    return SweepResult(
        parameter=parameter,
        tested_values=list(values),
        conditions=conditions,
        relationship_analysis=analysis_results,
        detected_pattern=pattern_results,
    )


def run_grid_sweep(
    param_x: str,
    values_x: Sequence[Any],
    param_y: str,
    values_y: Sequence[Any],
    base_config: Optional[Dict[str, Any]] = None,
    trials: int = 1,
    seed: int = 42,
) -> GridResult:
    """Execute a 2-dimensional parameter landscape sweep."""
    val_res = ExperimentValidator.validate_grid_sweep(param_x, values_x, param_y, values_y, trials=trials)
    if not val_res.valid:
        raise ExperimentValidationError(val_res.errors)

    base = dict(base_config or {})
    cells: List[Dict[str, Any]] = []

    # Map of metric -> 2D array [len(values_y)][len(values_x)]
    matrix_metrics: Dict[str, List[List[Optional[float]]]] = {}

    for j, vy in enumerate(values_y):
        for i, vx in enumerate(values_x):
            cond_params = dict(base)
            cond_params[param_x] = vx
            cond_params[param_y] = vy
            label = f"{param_x}={vx};{param_y}={vy}"

            cond_res = run_condition_trials(
                condition_label=label,
                parameter_values=cond_params,
                master_seed=seed,
                trials=trials,
            )
            cells.append({"x": vx, "y": vy, "condition": cond_res})

            for m_key, stat in cond_res.aggregated_metrics.items():
                if m_key not in matrix_metrics:
                    matrix_metrics[m_key] = [
                        [None for _ in range(len(values_x))] for _ in range(len(values_y))
                    ]
                matrix_metrics[m_key][j][i] = stat["mean"]

    return GridResult(
        param_x=param_x,
        values_x=list(values_x),
        param_y=param_y,
        values_y=list(values_y),
        cells=cells,
        matrix_metrics=matrix_metrics,
    )


def run_controlled_comparison(
    baseline_config: Dict[str, Any],
    treatment_config: Dict[str, Any],
    trials: int = 1,
    seed: int = 42,
) -> ComparisonResult:
    """Execute a controlled baseline vs treatment comparison."""
    # Identify variables that differ
    all_keys = sorted(set(baseline_config.keys()) | set(treatment_config.keys()))
    diff_vars: Dict[str, Dict[str, Any]] = {}
    for k in all_keys:
        b_val = baseline_config.get(k)
        t_val = treatment_config.get(k)
        if b_val != t_val:
            diff_vars[k] = {"baseline": b_val, "treatment": t_val}

    base_res = run_condition_trials("baseline", baseline_config, master_seed=seed, trials=trials)
    treat_res = run_condition_trials("treatment", treatment_config, master_seed=seed, trials=trials)

    deltas: Dict[str, float] = {}
    pct_changes: Dict[str, Optional[float]] = {}

    common_metrics = sorted(set(base_res.aggregated_metrics.keys()) & set(treat_res.aggregated_metrics.keys()))
    for m in common_metrics:
        b_mean = base_res.aggregated_metrics[m]["mean"]
        t_mean = treat_res.aggregated_metrics[m]["mean"]
        d = t_mean - b_mean
        deltas[m] = float(d)
        if abs(b_mean) > 1e-6:
            pct_changes[m] = float((d / abs(b_mean)) * 100.0)
        else:
            pct_changes[m] = None

    # Compare representative states if available
    state_diff = None
    if base_res.trials and treat_res.trials:
        exp_b = run_experiment(_build_core_config(baseline_config, seed=seed))
        exp_t = run_experiment(_build_core_config(treatment_config, seed=seed))
        vb = exp_b.snapshots[-1]["state_vector"]
        vt = exp_t.snapshots[-1]["state_vector"]
        state_diff = compare_states(vb, vt)

    return ComparisonResult(
        baseline_condition=base_res,
        treatment_condition=treat_res,
        differing_variables=diff_vars,
        metric_deltas=deltas,
        percentage_changes=pct_changes,
        state_difference=state_diff,
    )


def reproduce_lab_experiment(
    original_config: Dict[str, Any],
    expected_metrics: Dict[str, Any],
    seed: int,
    trials: int = 1,
    tolerance: float = 1e-9,
) -> Dict[str, Any]:
    """Rerun an experiment and strictly verify deterministic bit/numerical equivalence."""
    cfg = _build_core_config(original_config, seed=seed)
    reproduced_exp = run_experiment(cfg)
    actual_metrics = reproduced_exp.metrics

    metric_matches: Dict[str, Dict[str, Any]] = {}
    exact_match = True

    for k, v in expected_metrics.items():
        if isinstance(v, (int, float)) and not np.isnan(v):
            if k in actual_metrics:
                act = actual_metrics[k]
                diff = abs(float(act) - float(v))
                is_match = diff <= tolerance
                metric_matches[k] = {
                    "expected": float(v),
                    "actual": float(act),
                    "difference": diff,
                    "matched": is_match,
                }
                if not is_match:
                    exact_match = False
            else:
                exact_match = False
                metric_matches[k] = {"expected": float(v), "actual": None, "matched": False}

    explanation = (
        "Reproduction verified: identical deterministic metrics reproduced exactly within defined numerical tolerance."
        if exact_match
        else "Reproduction failed: metrics deviated from recorded values."
    )

    return {
        "reproduced": exact_match,
        "exact_match": exact_match,
        "tolerance": tolerance,
        "metric_matches": metric_matches,
        "explanation": explanation,
        "reproduced_experiment_id": reproduced_exp.experiment_id,
    }
