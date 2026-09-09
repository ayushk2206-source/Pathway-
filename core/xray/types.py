"""Enumerations and type constants for Phase 05 Memory X-Ray & Causal Memory Map."""

from __future__ import annotations

from enum import Enum


class StateChangeClassification(str, Enum):
    """Classification of consecutive state change magnitude."""
    STABLE = "STABLE"
    SHIFT = "SHIFT"
    MAJOR_SHIFT = "MAJOR_SHIFT"


class DecayPattern(str, Enum):
    """Empirical pattern of memory persistence/decay over time."""
    STABLE = "stable"
    DECAYING = "decaying"
    REINFORCED = "reinforced"
    RAPIDLY_LOST = "rapidly_lost"
    RECOVERED = "recovered"


class MemoryLifecycleStage(str, Enum):
    """Inferred state of an individual memory through the timeline."""
    ENCODED = "ENCODED"
    REINFORCED = "REINFORCED"
    RETRIEVED = "RETRIEVED"
    COMPETED = "COMPETED"
    WEAKENED = "WEAKENED"
    RECALLED = "RECALLED"
    FADED = "FADED"


class RelationshipType(str, Enum):
    """Relationship between two memories in the competition graph."""
    SIMILARITY = "similarity"
    ASSOCIATION = "association"
    COMPETITION = "competition"
    REINFORCEMENT = "reinforcement"


class AnomalyType(str, Enum):
    """Categorization of detected state anomalies."""
    STATE_JUMP = "STATE_JUMP"
    ACTIVATION_COLLAPSE = "ACTIVATION_COLLAPSE"
    SPARSITY_SHIFT = "SPARSITY_SHIFT"
    UNEXPECTED_STRENGTHENING = "UNEXPECTED_STRENGTHENING"
    HIGH_INTERFERENCE = "HIGH_INTERFERENCE"
