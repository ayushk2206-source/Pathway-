"""FastAPI Route Handlers for Phase 23: Scientific Evidence & Research Layer."""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from core.research import ScientificResearchEngine
from .research_schemas import MethodologyRequestSchema

research_router = APIRouter(prefix="/api/research", tags=["Scientific Evidence & Research"])

# Singleton engine instance
_research_engine = ScientificResearchEngine()


@research_router.get("/papers")
def get_papers_endpoint(tag: Optional[str] = Query(None, description="Concept tag filter")) -> Dict[str, Any]:
    """Retrieve verified peer-reviewed literature citations (2022-2026)."""
    papers = _research_engine.get_papers(tag)
    return {
        "papers": [p.to_dict() for p in papers],
        "total": len(papers),
        "available_tags": [
            "ALL",
            "synaptic memory",
            "plasticity",
            "recurrent memory",
            "Hebbian learning",
            "capacity limits",
            "key-value binding",
            "decay",
        ],
    }


@research_router.get("/papers/{paper_id}")
def get_paper_detail_endpoint(paper_id: str) -> Dict[str, Any]:
    """Retrieve detailed research paper profile by ID."""
    paper = _research_engine.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found.")
    return {"paper": paper.to_dict()}


@research_router.get("/claims")
def get_claims_endpoint() -> Dict[str, Any]:
    """Retrieve traceable claims linking literature, Pathway experiments, and empirical evidence."""
    claims = _research_engine.get_claims()
    return {"claims": [c.to_dict() for c in claims], "total": len(claims)}


@research_router.get("/metrics")
def get_metric_glossary_endpoint() -> Dict[str, Any]:
    """Retrieve metric definitions with formulas, units, interpretations, and limitations."""
    metrics = _research_engine.get_metric_glossary()
    return {"metrics": [m.to_dict() for m in metrics], "total": len(metrics)}


@research_router.get("/graph")
def get_research_graph_endpoint() -> Dict[str, Any]:
    """Retrieve research lineage graph (Concept -> Paper -> Implementation -> Experiment -> Observation)."""
    return _research_engine.get_research_graph()


@research_router.get("/disclosures")
def get_disclosures_endpoint() -> Dict[str, Any]:
    """Retrieve AI assistance, data, prerequisites, learning objectives, and model limitations."""
    return _research_engine.get_disclosures()


@research_router.get("/licenses")
def get_licenses_endpoint() -> Dict[str, Any]:
    """Retrieve full software, asset, and data license registry."""
    records = _research_engine.get_licenses()
    return {"licenses": [r.to_dict() for r in records], "total": len(records)}


@research_router.post("/methodology")
def generate_methodology_endpoint(req: MethodologyRequestSchema) -> Dict[str, Any]:
    """Generate structured experimental methodology for a specific parameter configuration."""
    methodology = _research_engine.generate_methodology(
        experiment_type=req.experiment_type,
        config=req.config,
    )
    return {"methodology": methodology}
