"""Enums and constant types for Counterfactual Memory Archaeology (Phase 04)."""

from __future__ import annotations

from enum import Enum


class InterventionType(str, Enum):
    """Supported intervention types on memory histories."""

    REMOVE_EVENT = "remove_event"
    DUPLICATE_EVENT = "duplicate_event"
    REPLACE_EVENT = "replace_event"
    MODIFY_EVENT = "modify_event"
    MOVE_EVENT = "move_event"
    CHANGE_STRENGTH = "change_strength"
    CHANGE_SIMILARITY = "change_similarity"
    RESET_MEMORY = "reset_memory"
    FREEZE_MEMORY = "freeze_memory"
    INJECT_MEMORY = "inject_memory"

    # Temporal surgery extensions
    TEMPORAL_DELETE = "temporal_delete"
    TEMPORAL_FREEZE = "temporal_freeze"
    TEMPORAL_SCALE = "temporal_scale"

    # Phase 16 Counterfactual Synaptic & Mechanism interventions
    SYNAPSE_PREVENT_STRENGTHEN = "synapse_prevent_strengthen"
    SYNAPSE_SILENCE = "synapse_silence"
    SYNAPSE_SCALE = "synapse_scale"
    CHANGE_DECAY = "change_decay"
    CHANGE_PLASTICITY = "change_plasticity"


class DivergenceClassification(str, Enum):
    """Empirical characterization of the divergence propagation shape."""

    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    CUMULATIVE = "cumulative"
    EXPLOSIVE = "explosive"
    DAMPED = "damped"
    OSCILLATING = "oscillating"
    LOCALIZED = "localized"
    GLOBAL = "global"
    TRANSIENT = "transient"
    PERSISTENT = "persistent"
    CONVERGENT = "convergent"


class ReplayStrategy(str, Enum):
    """Replay execution strategy for counterfactual timelines."""

    FULL_REPLAY = "full_replay"
    CHECKPOINT = "checkpoint"


class CounterfactualStatus(str, Enum):
    """Lifecycle status of a counterfactual experiment."""

    DRAFT = "draft"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BranchType(str, Enum):
    """Categorical type for a branch in a counterfactual timeline tree."""

    ROOT = "root"
    ABLATION = "ablation"
    SURGERY = "surgery"
    TEMPORAL = "temporal"
    EXPLORATORY = "exploratory"
    SYNAPTIC = "synaptic"


# Safety quotas
MAX_COUNTERFACTUALS = 100
MAX_REPLAY_LENGTH = 500
MAX_SEARCH_COMBINATIONS = 144
MAX_BRANCH_DEPTH = 20
