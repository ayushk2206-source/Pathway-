"""Memory X-Ray & Causal Memory Map (Phase 05).

Provides deterministic internal state introspection, activation profiles,
memory competition graphs, 2D PCA projections, change detection, and counterfactual
topological surgery analysis.
"""

from .activation import compute_activation_profile
from .anomalies import detect_state_anomalies
from .changes import detect_state_changes
from .checkpoints import get_state_checkpoint
from .clustering import cluster_memory_representations
from .competition import build_competition_graph
from .contracts import generate_visualization_contracts
from .decay import analyze_decay_curves
from .diagnostics import compute_memory_diagnostics
from .diff import compare_states
from .divergence_integration import trace_divergence_xray
from .event_impact import compute_event_impact
from .explanation import build_memory_explanation
from .heatmaps import generate_heatmap_matrices
from .importance import compute_memory_importance
from .inspector import inspect_event_before_after
from .interference import detect_interference
from .models import (
    ActivationProfile,
    AnomalyRecord,
    ClusterResult,
    CompetitionEdge,
    CompetitionGraph,
    EventImpact,
    InterferenceRecord,
    MemoryDiagnostics,
    MemoryExplanation,
    MemoryImportance,
    MemoryMap2D,
    MemoryMapPoint,
    MemorySnapshot,
    MemoryStrengthProfile,
    MemoryTrace,
    ReinforcementRecord,
    SparsityAnalysis,
    StateChangeRecord,
    StateComparison,
    StateTrajectory,
    XRayReport,
)
from .neighborhood import find_nearest_memories
from .projection import project_memory_map_2d
from .query import execute_xray_query
from .reinforcement import detect_reinforcement
from .replay_controller import MemoryReplayController, PlaybackStatus
from .report import generate_xray_report
from .snapshot import create_memory_snapshots
from .sparsity import analyze_sparsity
from .strength import compute_memory_strengths
from .surgery_integration import compare_xray_surgery
from .trace import get_memory_trace
from .trajectory import get_state_trajectory
from .types import (
    AnomalyType,
    DecayPattern,
    MemoryLifecycleStage,
    RelationshipType,
    StateChangeClassification,
)

__all__ = [
    # Models & types
    "MemorySnapshot",
    "StateTrajectory",
    "StateComparison",
    "StateChangeRecord",
    "ActivationProfile",
    "SparsityAnalysis",
    "MemoryStrengthProfile",
    "ReinforcementRecord",
    "InterferenceRecord",
    "CompetitionEdge",
    "CompetitionGraph",
    "ClusterResult",
    "MemoryMapPoint",
    "MemoryMap2D",
    "MemoryTrace",
    "EventImpact",
    "MemoryImportance",
    "MemoryExplanation",
    "MemoryDiagnostics",
    "AnomalyRecord",
    "XRayReport",
    "PlaybackStatus",
    "StateChangeClassification",
    "DecayPattern",
    "MemoryLifecycleStage",
    "RelationshipType",
    "AnomalyType",
    # Functions
    "create_memory_snapshots",
    "get_state_trajectory",
    "compare_states",
    "compute_activation_profile",
    "detect_state_changes",
    "generate_heatmap_matrices",
    "analyze_sparsity",
    "compute_memory_strengths",
    "analyze_decay_curves",
    "detect_reinforcement",
    "detect_interference",
    "build_competition_graph",
    "cluster_memory_representations",
    "project_memory_map_2d",
    "find_nearest_memories",
    "get_memory_trace",
    "compute_event_impact",
    "compute_memory_importance",
    "build_memory_explanation",
    "execute_xray_query",
    "inspect_event_before_after",
    "compare_xray_surgery",
    "trace_divergence_xray",
    "compute_memory_diagnostics",
    "detect_state_anomalies",
    "MemoryReplayController",
    "get_state_checkpoint",
    "generate_xray_report",
    "generate_visualization_contracts",
]
