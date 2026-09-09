"""Memory Detective / Hypothesis Engine (Phase 07).

Educational computational-memory investigator:
Observe -> Hypothesize -> Intervene -> Replay -> Measure -> Compare -> Conclude.
"""

from __future__ import annotations

from .autopsy import MemoryAutopsyEngine
from .discovery import DiscoveryEngine
from .hypotheses import HypothesisGenerator
from .models import (
    CandidateHypothesis,
    DiscoveryObservation,
    EvidenceChain,
    Investigation,
    MeasurableObservation,
    MemoryAutopsy,
    MemoryBirthRecord,
    MemoryDeathRecord,
    MinimumIntervention,
    NotebookEntry,
    RobustnessEvaluation,
    SensitivityRecord,
    TestDesign,
    TestResult,
)
from .parser import DeterministicQuestionParser
from .observations import ObservationBuilder
from .sensitivity import SensitivityEngine
from .store import InvestigationStore
from .testing import TestDesigner, TestRunner
from .types import (
    CausalSupportStatus,
    DiscoveryNovelty,
    HypothesisClassification,
    InvestigationStatus,
    MemoryLifecycleStage,
    QuestionIntent,
)

__all__ = [
    "CausalSupportStatus",
    "DiscoveryNovelty",
    "HypothesisClassification",
    "InvestigationStatus",
    "MemoryLifecycleStage",
    "QuestionIntent",
    "MeasurableObservation",
    "CandidateHypothesis",
    "TestDesign",
    "TestResult",
    "EvidenceChain",
    "MemoryBirthRecord",
    "MemoryDeathRecord",
    "MemoryAutopsy",
    "SensitivityRecord",
    "RobustnessEvaluation",
    "MinimumIntervention",
    "DiscoveryObservation",
    "NotebookEntry",
    "Investigation",
    "DeterministicQuestionParser",
    "ObservationBuilder",
    "HypothesisGenerator",
    "TestDesigner",
    "TestRunner",
    "MemoryAutopsyEngine",
    "SensitivityEngine",
    "DiscoveryEngine",
    "InvestigationStore",
]
