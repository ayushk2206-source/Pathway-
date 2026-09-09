"""Enums and constant types for Memory Detective / Hypothesis Engine (Phase 07)."""

from __future__ import annotations

from enum import Enum


class InvestigationStatus(str, Enum):
    """Lifecycle status of a memory investigation."""

    OBSERVING = "OBSERVING"
    HYPOTHESIZING = "HYPOTHESIZING"
    TESTING = "TESTING"
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class QuestionIntent(str, Enum):
    """Deterministic classification of researcher question intents."""

    MEMORY_DECAY = "MEMORY_DECAY"
    MEMORY_REINFORCEMENT = "MEMORY_REINFORCEMENT"
    INTERFERENCE = "INTERFERENCE"
    STATE_SHIFT = "STATE_SHIFT"
    RETRIEVAL = "RETRIEVAL"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    EVENT_IMPACT = "EVENT_IMPACT"
    PERSISTENCE = "PERSISTENCE"
    SPARSITY = "SPARSITY"
    ASSOCIATION = "ASSOCIATION"
    ANOMALY = "ANOMALY"


class CausalSupportStatus(str, Enum):
    """Epistemic evidence status of a causal assertion."""

    OBSERVED = "OBSERVED"
    CORRELATED = "CORRELATED"
    COUNTERFACTUALLY_SUPPORTED = "COUNTERFACTUALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class HypothesisClassification(str, Enum):
    """Overall outcome of a multi-evidence hypothesis evaluation."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class DiscoveryNovelty(str, Enum):
    """Novelty classification of an observation relative to the experiment library."""

    KNOWN_PATTERN = "KNOWN_PATTERN"
    VARIATION = "VARIATION"
    POTENTIALLY_NOVEL = "POTENTIALLY_NOVEL"
    UNKNOWN = "UNKNOWN"


class MemoryLifecycleStage(str, Enum):
    """Metaphorical lifecycle stages for memory representation traces."""

    BIRTH = "BIRTH"
    STABLE = "STABLE"
    REINFORCED = "REINFORCED"
    COMPETITIVE = "COMPETITIVE"
    DECAYING = "DECAYING"
    DEAD = "DEAD"
