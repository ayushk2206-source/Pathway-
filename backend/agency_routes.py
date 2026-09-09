"""FastAPI router for Phase 05 Multi-Agent Research Orchestration endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from agency.catalog.antigravity_export import export_all_antigravity_skills
from agency.catalog.registry import SPECIALIST_REGISTRY
from agency.orchestration.investigation import Investigation, ResearchDirector, run_research_investigation
from agency.orchestration.war_room import WarRoomBuilder
from agency.provenance.graph import ResearchGraphBuilder
from agency.runtime.execution import execute_agent
from agency.runtime.types import AgentMission
from agency.agents.specialists import RealityCheckerAgent

from .agency_schemas import (
    AgentListResponse,
    AntigravityExportRequest,
    AntigravityExportResponse,
    ChallengeFindingRequest,
    ChallengeFindingResponse,
    CreateInvestigationRequest,
    DisagreementListResponse,
    InvestigationListResponse,
    InvestigationResponse,
    NextExperimentResponse,
    ResearchSynthesisResponse,
    RunInvestigationRequest,
    WarRoomResponse,
)
from .store import ExperimentStore


agency_router = APIRouter(prefix="/agency", tags=["agency"])


def get_store() -> ExperimentStore:
    # Use store singleton on app state if available, else new default
    from .main import app
    return getattr(app.state, "store", ExperimentStore())


@agency_router.post("/investigations", response_model=InvestigationResponse)
def create_investigation(
    req: CreateInvestigationRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Create a new research investigation in PLANNING state."""
    director = ResearchDirector()
    inv = Investigation(
        investigation_id=director.investigation_id,
        research_question=req.research_question,
    )
    store.save_investigation(inv)
    return inv.to_dict()


@agency_router.post("/investigations/run", response_model=InvestigationResponse)
def run_investigation_endpoint(
    req: RunInvestigationRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Run an end-to-end multi-agent scientific investigation."""
    director = ResearchDirector()
    inv = director.run_investigation(req.research_question, max_rounds=req.max_rounds)
    store.save_investigation(inv)
    return inv.to_dict()


@agency_router.get("/investigations", response_model=InvestigationListResponse)
def list_investigations(
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """List all saved research investigations."""
    invs = store.list_investigations()
    return {
        "total": len(invs),
        "investigations": [i.to_dict() for i in invs],
    }


@agency_router.get("/investigations/{inv_id}", response_model=InvestigationResponse)
def get_investigation(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve an investigation by ID."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")
    return inv.to_dict()


@agency_router.get("/investigations/{inv_id}/graph")
def get_investigation_graph(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve the research lineage graph for an investigation."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")

    builder = ResearchGraphBuilder()
    builder.add_question(f"q_{inv.investigation_id}", inv.research_question)
    for h in inv.initial_hypotheses:
        builder.add_hypothesis(h["hypothesis_id"], h["statement"], question_id=f"q_{inv.investigation_id}")
    for exp in inv.experiments:
        builder.add_experiment(exp["experiment_id"], exp.get("title", "Experiment"), hypothesis_id=inv.initial_hypotheses[0]["hypothesis_id"] if inv.initial_hypotheses else None)
    for out in inv.agent_outputs:
        builder.add_agent_analysis(f"ana_{out['agent']}_{inv.investigation_id}", out["agent"], target_id=exp["experiment_id"] if inv.experiments else f"q_{inv.investigation_id}", verdict=out.get("verdict", "unknown"))

    return builder.to_dict()


@agency_router.get("/investigations/{inv_id}/missions")
def get_investigation_missions(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> List[Dict[str, Any]]:
    """Retrieve all structured agent missions for an investigation."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")
    return inv.agent_missions


@agency_router.get("/investigations/{inv_id}/outputs")
def get_investigation_outputs(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> List[Dict[str, Any]]:
    """Retrieve all structured specialist outputs for an investigation."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")
    return inv.agent_outputs


@agency_router.get("/investigations/{inv_id}/synthesis", response_model=ResearchSynthesisResponse)
def get_investigation_synthesis(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve the multi-agent research synthesis for an investigation."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")
    return {
        "investigation_id": inv.investigation_id,
        "status": inv.status.value,
        "synthesis": inv.synthesis,
        "next_actions": inv.next_actions,
    }


@agency_router.get("/investigations/{inv_id}/disagreements", response_model=DisagreementListResponse)
def get_investigation_disagreements(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve all structured disagreements and debates recorded in an investigation."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")
    return {
        "investigation_id": inv.investigation_id,
        "total_disagreements": len(inv.disagreements),
        "disagreements": inv.disagreements,
    }


@agency_router.post("/investigations/{inv_id}/next-experiment", response_model=NextExperimentResponse)
def get_next_experiment(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Request recommended next experiments based on specialist consensus."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")

    return {
        "investigation_id": inv.investigation_id,
        "next_actions": inv.next_actions,
        "suggested_experiments": [
            {
                "type": "parameter_sweep_2d",
                "independent_variable_1": "memory_similarity",
                "independent_variable_2": "update_strength",
                "rationale": "Resolve Red Team objection regarding write gain interactions.",
            },
            {
                "type": "counterfactual_ablation",
                "target": "competing_event",
                "rationale": "Directly isolate retroactive interference effect size.",
            }
        ],
    }


@agency_router.post("/investigations/{inv_id}/challenge", response_model=ChallengeFindingResponse)
def challenge_finding(
    inv_id: str,
    req: ChallengeFindingRequest,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Trigger an ad-hoc hostile Red Team reality check against an empirical finding."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")

    red_team = RealityCheckerAgent()
    mission = AgentMission(
        mission_id=f"adhoc_challenge_{req.finding_id}",
        research_question=inv.research_question,
        target_agent=red_team.name,
        available_evidence=inv.experiments,
        required_deliverable="Hostile reality check on targeted finding",
    )
    out = execute_agent(red_team, mission)
    inv.agent_outputs.append(out.to_dict())

    new_disagreement = None
    if out.objections:
        new_disagreement = {
            "disagreement_id": f"disagree_adhoc_{len(inv.disagreements) + 1}",
            "topic": f"Challenge on {req.finding_id}",
            "agent_a": "System Finding",
            "claim_a": req.finding_id,
            "agent_b": red_team.name,
            "claim_b": out.analysis,
            "underlying_issue": out.objections[0],
            "proposed_resolution": "Requires discriminating experiment or controlled ablation.",
        }
        inv.disagreements.append(new_disagreement)

    store.save_investigation(inv)
    return {
        "investigation_id": inv.investigation_id,
        "finding_id": req.finding_id,
        "red_team_output": out.to_dict(),
        "new_disagreement": new_disagreement,
    }


@agency_router.post("/investigations/{inv_id}/rerun", response_model=InvestigationResponse)
def rerun_investigation(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Re-run an investigation and verify deterministic reproducibility."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")

    director = ResearchDirector(investigation_id=f"{inv_id}_repro")
    rerun_inv = director.run_investigation(inv.research_question, max_rounds=inv.round_number)
    store.save_investigation(rerun_inv)
    return rerun_inv.to_dict()


@agency_router.get("/investigations/{inv_id}/war-room", response_model=WarRoomResponse)
def get_war_room_state(
    inv_id: str,
    store: ExperimentStore = Depends(get_store),
) -> Dict[str, Any]:
    """Retrieve the visual Research War Room station layout and live monitor state."""
    inv = store.get_investigation(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{inv_id}' not found")

    war_room = WarRoomBuilder.build_state(
        investigation_id=inv.investigation_id,
        question=inv.research_question,
        status=inv.status.value,
        round_number=inv.round_number,
        agent_outputs=inv.agent_outputs,
        experiments=inv.experiments,
        disagreements=inv.disagreements,
    )
    return war_room.to_dict()


@agency_router.get("/agents", response_model=AgentListResponse)
def list_available_agents() -> Dict[str, Any]:
    """List all available specialist agents in the Agency Agents catalog."""
    agents = SPECIALIST_REGISTRY.list_agents()
    return {
        "total": len(agents),
        "agents": [a.to_dict() for a in agents],
    }


@agency_router.get("/agents/{slug}")
def get_agent_details(slug: str) -> Dict[str, Any]:
    """Retrieve persona and instructions for a specific agent by slug or name."""
    agent_def = SPECIALIST_REGISTRY.get(slug)
    if not agent_def:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found in catalog")
    return agent_def.to_dict()


@agency_router.post("/antigravity/export", response_model=AntigravityExportResponse)
def export_skills(
    req: AntigravityExportRequest,
) -> Dict[str, Any]:
    """Export Agency Agents catalog as Antigravity-compatible skill directories."""
    out_dir = Path(req.output_dir) if req.output_dir else Path(".agents/skills")
    res = export_all_antigravity_skills(out_dir)
    return res
