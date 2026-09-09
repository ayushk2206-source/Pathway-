"""Agency Agents multi-agent research orchestration layer for Neural Archaeology (Phase 05).

Integrates the open-source msitarzewski/agency-agents catalog as a specialist reasoning
and orchestration layer above the deterministic computational memory engine.
"""

from .catalog.antigravity_export import (
    export_agent_to_antigravity_skill,
    export_all_antigravity_skills,
)
from .catalog.registry import AgentDefinition, SPECIALIST_REGISTRY, SpecialistRegistry
from .orchestration.debate import DisagreementRecord, ResearchConsensus, ResearchDebateManager
from .orchestration.investigation import (
    Investigation,
    ResearchDirector,
    run_research_investigation,
)
from .orchestration.war_room import WarRoomBuilder, WarRoomState, WarRoomStation
from .provenance.graph import ResearchGraphBuilder
from .provenance.record import AgentProvenance
from .provenance.research_memory import FailedAttempt, ResearchMemory
from .runtime.execution import SpecialistFactory, execute_agent, run_parallel_agents
from .runtime.types import (
    AgentMission,
    ConsensusStatus,
    InvestigationStatus,
    MAX_AGENT_ROUNDS,
    MAX_AGENTS_PER_INVESTIGATION,
    MAX_EXPERIMENTS_PER_INVESTIGATION,
    MAX_RESEARCH_DEPTH,
    SpecialistOutput,
    Verdict,
)

__version__ = "0.5.0"

__all__ = [
    # Catalog
    "AgentDefinition",
    "SPECIALIST_REGISTRY",
    "SpecialistRegistry",
    "export_agent_to_antigravity_skill",
    "export_all_antigravity_skills",
    # Runtime
    "InvestigationStatus",
    "Verdict",
    "ConsensusStatus",
    "AgentMission",
    "SpecialistOutput",
    "SpecialistFactory",
    "execute_agent",
    "run_parallel_agents",
    "MAX_AGENTS_PER_INVESTIGATION",
    "MAX_AGENT_ROUNDS",
    "MAX_RESEARCH_DEPTH",
    "MAX_EXPERIMENTS_PER_INVESTIGATION",
    # Provenance
    "AgentProvenance",
    "FailedAttempt",
    "ResearchMemory",
    "ResearchGraphBuilder",
    # Orchestration
    "Investigation",
    "ResearchDirector",
    "run_research_investigation",
    "DisagreementRecord",
    "ResearchConsensus",
    "ResearchDebateManager",
    "WarRoomBuilder",
    "WarRoomState",
    "WarRoomStation",
]
