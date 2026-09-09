"""Experiment Lab — Phase 03 public API.

A computational laboratory system for asking scientific questions, formulating
hypotheses, running controlled experiments, detecting non-linear behaviors,
discriminating competing explanations, and tracking research lineage.
"""

from .analysis import (
    aggregate_metric_samples,
    analyze_sweep_relationship,
    cohens_d,
    detect_nonlinear_patterns,
    pearson_correlation,
    spearman_correlation,
)
from .diff import diff_lab_experiments
from .discovery import find_discriminating_experiment, suggest_next_experiment
from .export import export_experiment_csv, export_experiment_json
from .hypotheses import (
    CompetingHypothesesGroup,
    Hypothesis,
    HypothesisStatus,
    PredictedDirection,
    Prediction,
    PredictionEvaluation,
    evaluate_prediction,
    update_hypothesis_with_evidence,
)
from .lineage import EdgeType, ExperimentGraph, GraphEdge, GraphNode, NodeType
from .models import (
    ComparisonResult,
    ConditionResult,
    ExperimentStatus,
    GridResult,
    LabExperiment,
    SweepResult,
    TrialRecord,
)
from .queue import ExperimentQueue, QueueItem
from .reporting import generate_scientific_report
from .runner import (
    derive_trial_seed,
    reproduce_lab_experiment,
    run_condition_trials,
    run_controlled_comparison,
    run_grid_sweep,
    run_parameter_sweep,
)
from .validation import (
    MAX_PARAMETER_COMBINATIONS,
    MAX_SEQUENCE_LENGTH,
    MAX_STATE_DIMENSION,
    MAX_TRIALS,
    ExperimentValidationError,
    ExperimentValidator,
    ValidationResult,
)
from .variables import (
    VARIABLE_REGISTRY,
    Variable,
    VariableRegistry,
    VariableRole,
    VariableType,
    get_variable,
    validate_variable_value,
)

__all__ = [
    # Variables
    "Variable",
    "VariableRole",
    "VariableType",
    "VARIABLE_REGISTRY",
    "VariableRegistry",
    "get_variable",
    "validate_variable_value",
    # Validation
    "ExperimentValidator",
    "ExperimentValidationError",
    "ValidationResult",
    "MAX_TRIALS",
    "MAX_PARAMETER_COMBINATIONS",
    "MAX_STATE_DIMENSION",
    "MAX_SEQUENCE_LENGTH",
    # Models
    "LabExperiment",
    "ExperimentStatus",
    "TrialRecord",
    "ConditionResult",
    "ComparisonResult",
    "SweepResult",
    "GridResult",
    # Hypotheses
    "Hypothesis",
    "HypothesisStatus",
    "Prediction",
    "PredictedDirection",
    "PredictionEvaluation",
    "CompetingHypothesesGroup",
    "evaluate_prediction",
    "update_hypothesis_with_evidence",
    # Runner
    "derive_trial_seed",
    "run_condition_trials",
    "run_parameter_sweep",
    "run_grid_sweep",
    "run_controlled_comparison",
    "reproduce_lab_experiment",
    # Analysis
    "aggregate_metric_samples",
    "pearson_correlation",
    "spearman_correlation",
    "cohens_d",
    "analyze_sweep_relationship",
    "detect_nonlinear_patterns",
    # Discovery
    "suggest_next_experiment",
    "find_discriminating_experiment",
    # Lineage & Diff
    "ExperimentGraph",
    "GraphNode",
    "GraphEdge",
    "NodeType",
    "EdgeType",
    "diff_lab_experiments",
    # Reporting & Export & Queue
    "generate_scientific_report",
    "export_experiment_json",
    "export_experiment_csv",
    "ExperimentQueue",
    "QueueItem",
]
