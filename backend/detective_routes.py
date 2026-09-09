"""FastAPI endpoints for Memory Detective & Hypothesis Engine (Phase 07)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.detective import (
    DeterministicQuestionParser,
    DiscoveryEngine,
    HypothesisGenerator,
    Investigation,
    InvestigationStatus,
    InvestigationStore,
    MemoryAutopsyEngine,
    NotebookEntry,
    ObservationBuilder,
    QuestionIntent,
    SensitivityEngine,
    TestDesign,
    TestDesigner,
    TestRunner,
)
from core.experiment import Experiment
from .detective_schemas import (
    ExecuteTestRequest,
    HypothesesRequest,
    InvestigateRequest,
    QuestionParseRequest,
    ReproduceRequest,
    SaveNotebookRequest,
)
from .store import ExperimentStore

detective_router = APIRouter(prefix="/detective", tags=["detective"])

# Default in-memory investigation store
_default_store = InvestigationStore()


def get_exp_store(request: Request) -> ExperimentStore:
    return getattr(request.app.state, "store", None) or ExperimentStore()


def get_detective_store(request: Request) -> InvestigationStore:
    if hasattr(request.app.state, "detective_store") and request.app.state.detective_store:
        return request.app.state.detective_store
    request.app.state.detective_store = _default_store
    return _default_store


def _resolve_experiment(exp_id: str, store: ExperimentStore) -> Experiment:
    exp = store.get(exp_id)
    if not exp:
        cf = store._counterfactuals.get(exp_id)
        if cf:
            exp = cf.to_experiment()
        else:
            raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return exp


def _parse_intent(val: Optional[str]) -> QuestionIntent:
    if not val:
        return QuestionIntent.INTERFERENCE
    val_clean = val.strip().upper()
    try:
        return QuestionIntent(val_clean)
    except Exception:
        return QuestionIntent.INTERFERENCE


# ---------------------------------------------------------------------------
# Question Parsing & Hypothesis Engine Endpoints
# ---------------------------------------------------------------------------


@detective_router.post("/parse-question")
def parse_question_endpoint(req: QuestionParseRequest) -> Dict[str, Any]:
    """Parse a researcher query deterministically without LLMs."""
    parsed = DeterministicQuestionParser.parse(req.question)
    return {
        "question": req.question,
        "intent": parsed.get("intent", "INTERFERENCE"),
        "target_memory": parsed.get("target_memory"),
        "target_event": parsed.get("target_event"),
        "parameters": {},
        "suggested_tests": parsed.get("available_tests", []),
        "required_data": parsed.get("required_data", []),
        "confidence": 1.0,
    }


@detective_router.post("/investigate")
def investigate_endpoint(
    req: InvestigateRequest,
    exp_store: ExperimentStore = Depends(get_exp_store),
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Run full automated forensic investigation from question to counterfactual proof."""
    experiment = _resolve_experiment(req.experiment_id, exp_store)

    # 1. Parse Question
    parsed = DeterministicQuestionParser.parse(req.question)
    intent = _parse_intent(parsed.get("intent"))
    target_mem = req.target_memory or parsed.get("target_memory")
    target_ev = parsed.get("target_event")

    # 2. Extract Measurable Observations
    obs = ObservationBuilder.extract_observations(experiment, target_mem)

    # 3. Generate Competing Hypotheses (Primary + Alt 1 + Alt 2 + Unknown)
    hypotheses = HypothesisGenerator.generate_hypotheses(obs, experiment, intent)

    # 4. Design & Execute Minimal Tests
    tests: List[TestDesign] = []
    results: List[Any] = []
    chains: List[Any] = []

    if req.execute_tests and hypotheses:
        # Design test for the leading candidate hypothesis
        test_design = TestDesigner.design_test(experiment, hypotheses[0], obs)
        tests.append(test_design)

        res, chain = TestRunner.run_test(experiment, hypotheses[0], test_design)
        results.append(res)
        chains.append(chain)

    # 5. Build Investigation Record
    inv = Investigation(
        experiment_id=req.experiment_id,
        question=req.question,
        intent=intent,
        target_memory=target_mem,
        target_event=target_ev,
        observations=obs,
        candidate_hypotheses=hypotheses,
        tests=tests,
        results=results,
        evidence_chain=chains,
        status=InvestigationStatus.CONFIRMED if results else InvestigationStatus.PROPOSED,
    )
    inv.scorecard = InvestigationStore.build_scorecard(inv)

    det_store.save_investigation(inv)
    return inv.to_dict()


@detective_router.post("/hypotheses")
def generate_hypotheses_endpoint(
    req: HypothesesRequest,
    exp_store: ExperimentStore = Depends(get_exp_store),
) -> Dict[str, Any]:
    """Generate structured candidate hypotheses for an experiment & memory."""
    experiment = _resolve_experiment(req.experiment_id, exp_store)
    intent = _parse_intent(req.intent)
    obs = ObservationBuilder.extract_observations(experiment, req.target_memory)
    hypotheses = HypothesisGenerator.generate_hypotheses(obs, experiment, intent)
    return {
        "experiment_id": req.experiment_id,
        "target_memory": req.target_memory,
        "hypotheses": [h.to_dict() for h in hypotheses],
    }


@detective_router.post("/test")
def execute_test_endpoint(
    req: ExecuteTestRequest,
    exp_store: ExperimentStore = Depends(get_exp_store),
) -> Dict[str, Any]:
    """Execute a single counterfactual test against a specific hypothesis."""
    experiment = _resolve_experiment(req.experiment_id, exp_store)
    test_design = TestDesign.from_dict(req.test_design)

    obs = ObservationBuilder.extract_observations(experiment, test_design.target_memory)
    hyps = HypothesisGenerator.generate_hypotheses(obs, experiment, QuestionIntent.INTERFERENCE)
    target_hyp = next((h for h in hyps if h.hypothesis_id == req.hypothesis_id), hyps[0])

    res, chain = TestRunner.run_test(experiment, target_hyp, test_design)
    return {
        "test_result": res.to_dict(),
        "evidence_chain": chain.to_dict(),
        "updated_hypothesis": target_hyp.to_dict(),
    }


# ---------------------------------------------------------------------------
# Autopsy & Sensitivity Endpoints
# ---------------------------------------------------------------------------


@detective_router.get("/autopsy/{experiment_id}/{memory_id}")
def get_autopsy_endpoint(
    experiment_id: str,
    memory_id: str,
    exp_store: ExperimentStore = Depends(get_exp_store),
) -> Dict[str, Any]:
    """Perform a comprehensive memory autopsy answering the 7 lifecycle questions."""
    experiment = _resolve_experiment(experiment_id, exp_store)
    autopsy = MemoryAutopsyEngine.perform_autopsy(experiment, memory_id)
    birth = MemoryAutopsyEngine.get_birth_record(experiment, memory_id)
    death = MemoryAutopsyEngine.get_death_record(experiment, memory_id)
    survival = MemoryAutopsyEngine.get_survival_analysis(experiment, memory_id)
    failure = MemoryAutopsyEngine.get_failure_analysis(experiment, memory_id)

    return {
        "autopsy": autopsy.to_dict(),
        "birth_record": birth.to_dict() if birth else None,
        "death_record": death.to_dict() if death else None,
        "survival_analysis": survival,
        "failure_analysis": failure,
    }


@detective_router.get("/sensitivity/{experiment_id}/{memory_id}")
def get_sensitivity_endpoint(
    experiment_id: str,
    memory_id: str,
    interfering_event_id: Optional[str] = Query(None, description="Suspected interfering event ID"),
    exp_store: ExperimentStore = Depends(get_exp_store),
) -> Dict[str, Any]:
    """Measure sensitivity, search for minimum intervention, and evaluate robustness."""
    experiment = _resolve_experiment(experiment_id, exp_store)

    ev_id = interfering_event_id
    if not ev_id:
        events = experiment.events
        ev_id = "e0001" if len(events) > 1 else "e0000"
        if len(events) > 1:
            e1 = events[1]
            ev_id = getattr(e1, "id", None) or (e1.get("id") if isinstance(e1, dict) else "e0001")

    sensitivity = SensitivityEngine.measure_sensitivity(experiment, memory_id, ev_id)
    min_intv = SensitivityEngine.find_minimum_intervention(experiment, memory_id)
    robustness = SensitivityEngine.evaluate_robustness(experiment, memory_id)

    return {
        "experiment_id": experiment_id,
        "memory_id": memory_id,
        "sensitivity": sensitivity.to_dict(),
        "minimum_intervention": min_intv.to_dict(),
        "robustness": robustness.to_dict(),
    }


# ---------------------------------------------------------------------------
# Discovery Feed Endpoints
# ---------------------------------------------------------------------------


@detective_router.get("/discovery/{experiment_id}")
def get_discovery_endpoint(
    experiment_id: str,
    exp_store: ExperimentStore = Depends(get_exp_store),
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Run automated discovery scan to detect anomalies, unexpected competition, and surprises."""
    experiment = _resolve_experiment(experiment_id, exp_store)
    discoveries = DiscoveryEngine.scan_experiment(experiment)
    det_store.add_discoveries(discoveries)

    return {
        "experiment_id": experiment_id,
        "discoveries_count": len(discoveries),
        "discoveries": [d.to_dict() for d in discoveries],
    }


# ---------------------------------------------------------------------------
# Investigations & Reproducibility Endpoints
# ---------------------------------------------------------------------------


@detective_router.get("/investigations")
def list_investigations_endpoint(
    experiment_id: Optional[str] = Query(None, description="Filter by experiment ID"),
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """List all saved investigations."""
    invs = det_store.list_investigations(experiment_id)
    return {
        "total": len(invs),
        "investigations": [i.to_dict() for i in invs],
    }


@detective_router.get("/investigations/{investigation_id}")
def get_investigation_endpoint(
    investigation_id: str,
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Get a saved investigation by ID."""
    inv = det_store.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")
    return inv.to_dict()


@detective_router.post("/investigations/{investigation_id}/reproduce")
def reproduce_investigation_endpoint(
    investigation_id: str,
    req: ReproduceRequest = ReproduceRequest(),
    exp_store: ExperimentStore = Depends(get_exp_store),
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Deterministically reproduce an investigation and rerun all counterfactual proofs."""
    orig_inv = det_store.get_investigation(investigation_id)
    if not orig_inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    target_exp_id = req.target_experiment_id or orig_inv.experiment_id
    target_exp = _resolve_experiment(target_exp_id, exp_store)

    reproduced = det_store.reproduce_investigation(investigation_id, target_exp)
    return reproduced.to_dict()


@detective_router.get("/investigations/{id1}/diff/{id2}")
def diff_investigations_endpoint(
    id1: str,
    id2: str,
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Diff two investigations side-by-side."""
    try:
        diff_data = det_store.diff_investigations(id1, id2)
        return diff_data
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@detective_router.get("/investigations/{investigation_id}/scorecard")
def get_scorecard_endpoint(
    investigation_id: str,
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Export an executive research scorecard for an investigation."""
    inv = det_store.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")
    return InvestigationStore.build_scorecard(inv)


# ---------------------------------------------------------------------------
# Research Notebook Endpoints
# ---------------------------------------------------------------------------


@detective_router.get("/notebook")
def get_notebook_endpoint(
    experiment_id: str = Query(..., description="Experiment ID"),
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Get research notebook entries for an experiment."""
    entries = det_store.get_notebook_entries(experiment_id)
    return {
        "experiment_id": experiment_id,
        "entries": [e.to_dict() for e in entries],
    }


@detective_router.post("/notebook")
def save_notebook_entry_endpoint(
    req: SaveNotebookRequest,
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Add a new entry to the research notebook."""
    entry = NotebookEntry(
        experiment_id=req.experiment_id,
        title=req.title,
        notes=req.content,
        content=req.content,
        author=req.author,
        investigation_id=req.linked_investigation_id,
        tags=req.tags,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    det_store.save_notebook_entry(entry)
    return entry.to_dict()


@detective_router.delete("/notebook/{experiment_id}/{entry_id}")
def delete_notebook_entry_endpoint(
    experiment_id: str,
    entry_id: str,
    det_store: InvestigationStore = Depends(get_detective_store),
) -> Dict[str, Any]:
    """Delete a notebook entry."""
    entries = det_store.get_notebook_entries(experiment_id)
    filtered = [e for e in entries if e.entry_id != entry_id]
    det_store._notebooks[experiment_id] = filtered
    return {"status": "deleted", "entry_id": entry_id}
