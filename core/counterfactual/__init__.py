"""Counterfactual Memory Archaeology subsystem (Phase 04).

Provides mechanisms for branching historical memory trajectories, evaluating counterfactual
interventions (ablations, surgeries, temporal operations), analyzing step-by-step divergence
propagation, forensic forgetting reconstruction, and minimal intervention search.
"""

from .contribution import estimate_event_contribution
from .diff import diff_histories
from .divergence import (
    DivergenceProfile,
    DivergenceStep,
    classify_divergence,
    compute_divergence_profile,
)
from .explanation import generate_counterfactual_explanation
from .export import export_counterfactual_json, export_divergence_csv
from .interventions import (
    CounterfactualValidationError,
    CounterfactualValidator,
    Intervention,
    ValidationResult,
    create_ablation_intervention,
    create_change_similarity_intervention,
    create_change_strength_intervention,
    create_duplicate_intervention,
    create_freeze_memory_intervention,
    create_inject_memory_intervention,
    create_modify_intervention,
    create_move_intervention,
    create_remove_intervention,
    create_replace_intervention,
    create_reset_memory_intervention,
    create_temporal_surgery_intervention,
    validate_intervention,
)
from .models import CounterfactualExperiment
from .replay import prepare_counterfactual_task, replay_counterfactual_engine
from .runner import (
    compare_multiple_histories,
    create_ablation,
    create_surgery,
    reproduce_counterfactual,
    run_counterfactual,
)
from .search import find_minimal_intervention, search_counterfactuals
from .timeline import CounterfactualTree, Timeline, TimelineNode
from .types import (
    BranchType,
    CounterfactualStatus,
    DivergenceClassification,
    InterventionType,
    ReplayStrategy,
)

__all__ = [
    # Types
    "InterventionType",
    "DivergenceClassification",
    "ReplayStrategy",
    "CounterfactualStatus",
    "BranchType",
    # Interventions
    "Intervention",
    "CounterfactualValidationError",
    "validate_intervention",
    "create_remove_intervention",
    "create_duplicate_intervention",
    "create_replace_intervention",
    "create_modify_intervention",
    "create_move_intervention",
    "create_change_strength_intervention",
    "create_change_similarity_intervention",
    "create_reset_memory_intervention",
    "create_freeze_memory_intervention",
    "create_inject_memory_intervention",
    "create_temporal_surgery_intervention",
    # Timeline
    "Timeline",
    "TimelineNode",
    "CounterfactualTree",
    # Divergence
    "DivergenceStep",
    "DivergenceProfile",
    "compute_divergence_profile",
    "classify_divergence",
    # Replay & Runner
    "prepare_counterfactual_task",
    "replay_counterfactual_engine",
    "CounterfactualExperiment",
    "run_counterfactual",
    "create_ablation",
    "create_surgery",
    "reproduce_counterfactual",
    "compare_multiple_histories",
    # Diff & Explanation
    "diff_histories",
    "generate_counterfactual_explanation",
    # Contribution & Search
    "estimate_event_contribution",
    "search_counterfactuals",
    "find_minimal_intervention",
    # Export
    "export_counterfactual_json",
    "export_divergence_csv",
]
