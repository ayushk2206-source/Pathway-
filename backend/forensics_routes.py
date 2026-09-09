"""FastAPI endpoints for Memory Detective & Research Lab (Phase 18)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from core.forensics import (
    CORE_LEARNING_OBJECTIVES,
    VERIFIED_SOURCES,
    CaseGenerator,
    CustomExperimentConfig,
    InvestigationCase,
    ResearchLabEngine,
    score_investigation,
)
from .forensics_schemas import (
    CompareExperimentsRequest,
    CustomExperimentRequest,
    SubmitVerdictRequest,
    TestHypothesisRequest,
)

forensics_router = APIRouter(prefix="/forensics", tags=["forensics"])

# Global session singleton for Research Lab
_RESEARCH_ENGINE = ResearchLabEngine()

# Cache generated cases
_CASES_CACHE: Dict[str, InvestigationCase] = {}


def _get_cases() -> Dict[str, InvestigationCase]:
    global _CASES_CACHE
    if not _CASES_CACHE:
        cases = CaseGenerator.generate_all_cases()
        _CASES_CACHE = {c.case_id: c for c in cases}
    return _CASES_CACHE


@forensics_router.get("/learning-objectives")
def get_learning_objectives() -> Dict[str, Any]:
    """Retrieve the core conceptual principles taught in the lab."""
    return {
        "title": "What You Are Learning",
        "objectives": CORE_LEARNING_OBJECTIVES,
    }


@forensics_router.get("/sources")
def get_scientific_sources() -> Dict[str, Any]:
    """Retrieve verified peer-reviewed primary scientific literature (2022-2026)."""
    cases = _get_cases()
    claims: List[Dict[str, str]] = []
    for c in cases.values():
        claims.extend(c.claim_traceability)

    return {
        "title": "Scientific Literature & Claim Traceability",
        "sources": [s.to_dict() for s in VERIFIED_SOURCES],
        "claims": claims,
    }


@forensics_router.get("/cases")
def list_cases() -> List[Dict[str, Any]]:
    """List all bounded investigation cases with blind summaries."""
    cases = _get_cases()
    summaries = []
    for c in cases.values():
        summaries.append({
            "case_id": c.case_id,
            "case_code": c.case_code,
            "title": c.title,
            "difficulty": c.difficulty,
            "briefing": c.briefing,
            "target_memory": c.target_memory,
            "initial_recall": c.initial_recall,
            "final_recall": c.final_recall,
            "available_tools": c.available_tools,
        })
    return summaries


@forensics_router.get("/cases/{case_id}")
def get_case(case_id: str, blind: bool = Query(default=True)) -> Dict[str, Any]:
    """Retrieve an investigation case. In blind mode, ground truth answers are obscured."""
    cases = _get_cases()
    c = cases.get(case_id.upper())
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    case_dict = c.to_dict()
    if blind:
        case_dict["ground_truth_hypothesis_id"] = None
        case_dict["ground_truth_explanation"] = None
        for h in case_dict["candidate_hypotheses"]:
            h["is_correct"] = None
            h["explanation"] = None
    return case_dict


@forensics_router.post("/cases/{case_id}/test-hypothesis")
def test_hypothesis_endpoint(case_id: str, req: TestHypothesisRequest) -> Dict[str, Any]:
    """Test a learner's hypothesis with assigned confidence against real experiment computation."""
    cases = _get_cases()
    c = cases.get(case_id.upper())
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    target_hyp = next((h for h in c.candidate_hypotheses if h.hypothesis_id == req.hypothesis_id), None)
    if not target_hyp:
        raise HTTPException(status_code=400, detail=f"Hypothesis '{req.hypothesis_id}' not valid for case.")

    is_confirmed = target_hyp.is_correct

    # Find relevant evidence items to unlock
    unlocked_evidence = [e.to_dict() for e in c.available_evidence]

    return {
        "case_id": c.case_id,
        "tested_hypothesis_id": req.hypothesis_id,
        "hypothesis_label": target_hyp.label,
        "learner_confidence": req.learner_confidence,
        "chosen_tool": req.chosen_tool or target_hyp.recommended_tool,
        "outcome": "CONFIRMED" if is_confirmed else "REFUTED",
        "measured_result": {
            "initial_recall": c.initial_recall,
            "final_recall": c.final_recall,
            "fidelity_delta": c.final_recall - c.initial_recall,
        },
        "scientific_feedback": target_hyp.explanation,
        "unlocked_evidence": unlocked_evidence,
    }


@forensics_router.post("/cases/{case_id}/submit-verdict")
def submit_verdict_endpoint(case_id: str, req: SubmitVerdictRequest) -> Dict[str, Any]:
    """Score the investigation and produce the automated result conclusion."""
    cases = _get_cases()
    c = cases.get(case_id.upper())
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    score = score_investigation(
        case=c,
        chosen_hypothesis_id=req.chosen_hypothesis_id,
        collected_evidence_ids=req.collected_evidence_ids,
        tests_run_count=req.tests_run_count,
        learner_confidence=req.learner_confidence,
        explanation_chain=req.explanation_chain,
    )

    is_correct = req.chosen_hypothesis_id == c.ground_truth_hypothesis_id

    verdict_statement = (
        f"Evidence {'confirms' if is_correct else 'is inconsistent with'} the proposed explanation. "
        + c.ground_truth_explanation
    )

    return {
        "case_id": c.case_id,
        "case_title": c.title,
        "scorecard": score.to_dict(),
        "is_correct": is_correct,
        "ground_truth_hypothesis_id": c.ground_truth_hypothesis_id,
        "case_conclusion": {
            "question": c.question,
            "target_memory": c.target_memory,
            "measured_effect": f"Fidelity changed from {c.initial_recall:.3f} -> {c.final_recall:.3f}",
            "verdict_statement": verdict_statement,
            "chain_submitted": req.explanation_chain,
        },
    }


# ---------------------------------------------------------------------------
# Research Lab Endpoints
# ---------------------------------------------------------------------------

@forensics_router.post("/research/run")
def run_custom_research(req: CustomExperimentRequest) -> Dict[str, Any]:
    """Execute a custom reproducible research experiment."""
    try:
        mem_dicts = [{"concept": m.concept, "value": m.value} for m in req.memories]
        cfg = CustomExperimentConfig(
            name=req.name,
            dimension=req.dimension,
            decay=req.decay,
            plasticity_eta=req.plasticity_eta,
            memories=mem_dicts,
            write_order=req.write_order,
            concept_similarity=req.concept_similarity,
            temporal_delay=req.temporal_delay,
            synaptic_silencing_id=req.synaptic_silencing_id,
            seed=req.seed,
            notes=req.notes,
        )
        res = _RESEARCH_ENGINE.run_experiment(cfg)
        return res.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research experiment execution failed: {str(e)}")


@forensics_router.get("/research/history")
def get_research_history() -> List[Dict[str, Any]]:
    """Retrieve session research log of all executed experiments."""
    return [exp.to_dict() for exp in _RESEARCH_ENGINE.get_history()]


@forensics_router.post("/research/compare")
def compare_research_experiments(req: CompareExperimentsRequest) -> Dict[str, Any]:
    """Side-by-side comparative inspection of two experiments."""
    try:
        return _RESEARCH_ENGINE.compare_experiments(req.run_id_a, req.run_id_b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
