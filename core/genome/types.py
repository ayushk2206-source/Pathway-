"""Enums and type definitions for Phase 08: Memory Genome + Cascade Engine."""

from __future__ import annotations

from enum import Enum


class CascadeEffectType(str, Enum):
    """Categorization of cascade propagation effects on memory items."""

    DIRECT = "DIRECT"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"
    UNCHANGED = "UNCHANGED"


class DoseResponsePattern(str, Enum):
    """Classification of dose-response downstream effect curves."""

    LINEAR = "LINEAR"
    THRESHOLD_LIKE = "THRESHOLD_LIKE"
    NONLINEAR = "NONLINEAR"
    SATURATING = "SATURATING"
    UNSTABLE = "UNSTABLE"


class FragilityClassification(str, Enum):
    """System-level fragility classification under memory perturbation."""

    ROBUST = "ROBUST"
    MODERATELY_FRAGILE = "MODERATELY_FRAGILE"
    HIGHLY_FRAGILE = "HIGHLY_FRAGILE"
    INCONCLUSIVE = "INCONCLUSIVE"


class RecoveryStatus(str, Enum):
    """Classification of state return fidelity after memory restoration."""

    FULL_RECOVERY = "FULL_RECOVERY"
    PARTIAL_RECOVERY = "PARTIAL_RECOVERY"
    PATH_DEPENDENT_RECOVERY = "PATH_DEPENDENT_RECOVERY"
    NO_RECOVERY = "NO_RECOVERY"


class OrderSensitivity(str, Enum):
    """Evaluation of whether operation sequence order alters the final memory state."""

    ORDER_SENSITIVE = "ORDER_SENSITIVE"
    ORDER_ROBUST = "ORDER_ROBUST"


class GenomeSection(str, Enum):
    """The 8 measurable computational facets comprising the Memory DNA strip."""

    ORIGIN = "ORIGIN"
    REINFORCEMENT = "REINFORCEMENT"
    ASSOCIATION = "ASSOCIATION"
    COMPETITION = "COMPETITION"
    RETRIEVAL = "RETRIEVAL"
    DRIFT = "DRIFT"
    STABILITY = "STABILITY"
    INFLUENCE = "INFLUENCE"


class GenomeInterventionType(str, Enum):
    """Supported non-destructive interventions in the Cascade Engine."""

    REMOVE = "remove"
    WEAKEN = "weaken"
    STRENGTHEN = "strengthen"
    SUPPRESS_REINFORCEMENT = "suppress_reinforcement"
    RESTORE_PREVIOUS_STATE = "restore_previous_state"
