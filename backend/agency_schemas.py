"""Pydantic v2 schemas for Phase 05 Multi-Agent Research Orchestration APIs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateInvestigationRequest(BaseModel):
    research_question: str = Field(..., description="Scientific inquiry question to investigate")
    max_rounds: int = Field(default=2, ge=1, le=5, description="Maximum research investigation rounds")


class RunInvestigationRequest(BaseModel):
    research_question: str = Field(..., description="Scientific inquiry question to investigate")
    max_rounds: int = Field(default=2, ge=1, le=5, description="Maximum research investigation rounds")


class InvestigationResponse(BaseModel):
    investigation_id: str
    research_question: str
    status: str
    round_number: int
    initial_hypotheses: List[Dict[str, Any]] = []
    active_hypotheses: List[Dict[str, Any]] = []
    experiments: List[Dict[str, Any]] = []
    counterfactuals: List[Dict[str, Any]] = []
    agent_missions: List[Dict[str, Any]] = []
    agent_outputs: List[Dict[str, Any]] = []
    observations: List[Dict[str, Any]] = []
    disagreements: List[Dict[str, Any]] = []
    synthesis: Dict[str, Any] = {}
    unresolved_questions: List[str] = []
    next_actions: List[str] = []
    provenance: Dict[str, Any] = {}
    created_at: str
    updated_at: str


class InvestigationListResponse(BaseModel):
    total: int
    investigations: List[Dict[str, Any]]


class ResearchSynthesisResponse(BaseModel):
    investigation_id: str
    status: str
    synthesis: Dict[str, Any]
    next_actions: List[str]


class DisagreementListResponse(BaseModel):
    investigation_id: str
    total_disagreements: int
    disagreements: List[Dict[str, Any]]


class NextExperimentResponse(BaseModel):
    investigation_id: str
    next_actions: List[str]
    suggested_experiments: List[Dict[str, Any]] = []


class ChallengeFindingRequest(BaseModel):
    finding_id: str = Field(..., description="ID of finding or observation to challenge")
    challenge_focus: Optional[str] = Field(default=None, description="Specific focus for hostile review")


class ChallengeFindingResponse(BaseModel):
    investigation_id: str
    finding_id: str
    red_team_output: Dict[str, Any]
    new_disagreement: Optional[Dict[str, Any]] = None


class WarRoomResponse(BaseModel):
    investigation_id: str
    research_question: str
    round_number: int
    investigation_status: str
    stations: Dict[str, Any]
    consensus_meter: float
    live_event_log: List[Dict[str, Any]] = []
    updated_at: str


class AgentListResponse(BaseModel):
    total: int
    agents: List[Dict[str, Any]]


class AntigravityExportRequest(BaseModel):
    output_dir: Optional[str] = Field(default=None, description="Custom export destination directory")


class AntigravityExportResponse(BaseModel):
    output_directory: str
    total_exported: int
    skills: List[Dict[str, Any]]
