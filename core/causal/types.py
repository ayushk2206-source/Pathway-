"""Enums and type definitions for Phase 10: Causal Memory Lab.

Extends (never replaces) the Phase 04 CounterfactualExperiment machinery and the
Phase 08 Memory Genome / Cascade Engine. Every enum here maps onto real,
already-computed quantities produced by those engines -- nothing here is a
label applied to fabricated data.
"""

from __future__ import annotations

from enum import Enum


class CausalInterventionType(str, Enum):
    """The 11 intervention verbs exposed by the Causal Scenario Builder.

    Each maps to one or more concrete ``core.counterfactual.Intervention``
    primitives (see ``core.causal.scenario.CausalScenarioCompiler``).
    """

    REMOVE = "REMOVE"
    ADD = "ADD"
    STRENGTHEN = "STRENGTHEN"
    WEAKEN = "WEAKEN"
    DELAY = "DELAY"
    ACCELERATE = "ACCELERATE"
    FREEZE = "FREEZE"
    RESTORE = "RESTORE"
    DUPLICATE = "DUPLICATE"
    REPLACE = "REPLACE"
    ISOLATE = "ISOLATE"


class CausalEdgeStatus(str, Enum):
    """Result of testing a claimed causal edge with a real intervention."""

    SUPPORTED = "SUPPORTED"
    WEAK = "WEAK"
    INCONCLUSIVE = "INCONCLUSIVE"
    CONTRADICTED = "CONTRADICTED"


class InteractionClassification(str, Enum):
    """Classification of a multi-intervention combined effect vs. the additive expectation."""

    SYNERGY = "SYNERGY"
    ANTAGONISM = "ANTAGONISM"
    ADDITIVE = "ADDITIVE"
    UNKNOWN = "UNKNOWN"


class ClaimStatus(str, Enum):
    """Status of a Causality Ledger claim."""

    SUPPORTED_WITHIN_EXPERIMENT = "SUPPORTED WITHIN EXPERIMENT"
    SUPPORTED_WITHIN_TESTED_CONDITIONS = "SUPPORTED WITHIN TESTED CONDITIONS"
    WEAK_EVIDENCE = "WEAK EVIDENCE"
    CONTESTED = "CONTESTED"
    RETRACTED = "RETRACTED"


class QueueStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResearcherMode(str, Enum):
    """Section 41 -- who is choosing the next scenario."""

    MANUAL = "MANUAL"
    ASSISTED = "ASSISTED"
    AUTONOMOUS = "AUTONOMOUS"


class WindowSensitivity(str, Enum):
    """Section 4 -- Critical Window Detector phase labels."""

    EARLY = "EARLY"
    STABLE = "STABLE"
    SENSITIVE = "SENSITIVE"
    RECOVERY = "RECOVERY"


class CausalScenarioValidationError(ValueError):
    """Raised by CausalScenarioCompiler when a scenario is not executable."""


# Resource guard defaults (Section 18 / 42) -- deliberately conservative so a
# careless multi-intervention or matrix request cannot silently trigger an
# unbounded number of full experiment replays.
MAX_MULTI_INTERVENTIONS = 5
MAX_MATRIX_MEMORIES = 8
MAX_TIMING_CANDIDATES = 12
MAX_QUEUE_SIZE = 200
