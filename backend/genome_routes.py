"""FastAPI endpoints for Phase 08: Memory Genome + Cascade Engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request

from core import Experiment
from core.genome import (
    AutomaticResearchQuestionGenerator,
    CascadeEngine,
    CentralityAnalyzer,
    CriticalMemoryDetector,
    DependencyMatrixBuilder,
    DoseResponseEngine,
    FragilityAnalyzer,
    GenomeStore,
    LineageBuilder,
    MemoryGenomeBuilder,
    MutationEngine,
    PathDependenceEngine,
    RecoveryEngine,
    RedundancyAnalyzer,
    ReportGenerator,
    SandboxManager,
    resolve_memory,
)
from .genome_schemas import (
    BranchCompareRequest,
    BranchCreateRequest,
    CascadeRunRequest,
    DoseResponseRequest,
    MutationRequest,
    RecoveryTestRequest,
)
from .store import ExperimentStore

genome_router = APIRouter(prefix="/genome", tags=["genome"])


def get_exp_store(request: Request) -> ExperimentStore:
    return getattr(request.app.state, "store", None) or ExperimentStore()


def _resolve_experiment(exp_id: str, store: ExperimentStore) -> Experiment:
    exp = store.get(exp_id)
    if not exp:
        cf = store._counterfactuals.get(exp_id)
        if cf:
            exp = cf.to_experiment()
        else:
            raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return exp


@genome_router.get("/{exp_id}/centrality")
def get_memory_centrality(exp_id: str, request: Request) -> Dict[str, Any]:
    """Compute graph centrality metrics for all memories in experiment."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        records = CentralityAnalyzer.analyze_centrality(exp)
        return {"centrality": [r.to_dict() for r in records]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/critical-memories")
def find_critical_memories(exp_id: str, request: Request) -> Dict[str, Any]:
    """Test candidate memories and rank by system-wide cascade impact."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        ranks = CriticalMemoryDetector.find_critical_memories(exp)
        return {"critical_memories": [r.to_dict() for r in ranks]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/path-dependence")
def run_path_dependence(exp_id: str, request: Request) -> Dict[str, Any]:
    """Test sequence ordering sensitivity (A -> B -> C vs A -> C -> B)."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        path_res = PathDependenceEngine.test_path_dependence(exp)
        return {"path_dependence": path_res.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/dependency-matrix")
def get_dependency_matrix(
    exp_id: str,
    request: Request,
    metric: str = Query("association", description="Matrix metric: association, influence, sensitivity"),
) -> Dict[str, Any]:
    """Compute N x N memory dependency matrix."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        dep_matrix = DependencyMatrixBuilder.build_matrix(exp, metric)
        return {"dependency_matrix": dep_matrix.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}")
def get_memory_genome(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve structured computational Memory Genome."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    cached = GenomeStore.get_genome(exp_id, mem_id)
    if cached:
        return {"genome": cached.to_dict()}

    try:
        genome = MemoryGenomeBuilder.build(exp, mem_id)
        GenomeStore.put_genome(exp_id, mem_id, genome)
        return {"genome": genome.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/lineage")
def get_memory_lineage(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve causal lineage directed acyclic graph for target memory."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        lineage = LineageBuilder.build(exp, mem_id)
        return {"lineage": lineage.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/trajectory")
def get_memory_trajectory(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve historical strength trajectory for scrub replay."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        genome = MemoryGenomeBuilder.build(exp, mem_id)
        return {
            "memory_id": genome.memory_id,
            "concept_label": genome.concept_label,
            "trajectory": genome.trajectory,
            "current_strength": genome.current_strength,
            "origin_step": genome.origin_step,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.post("/cascade")
def run_cascade_analysis(req: CascadeRunRequest, request: Request) -> Dict[str, Any]:
    """Execute counterfactual cascade simulation and return dynamic CascadeMap."""
    store = get_exp_store(request)
    exp = _resolve_experiment(req.experiment_id, store)

    cached = GenomeStore.get_cascade(req.experiment_id, req.target_memory, req.intervention, req.dose)
    if cached:
        breakdown = CascadeEngine.compute_influence_breakdown(cached)
        surprise = CascadeEngine.detect_surprise(cached, req.dose)
        return {
            "cascade": cached.to_dict(),
            "influence_breakdown": breakdown.to_dict(),
            "surprise": surprise,
        }

    try:
        cmap = CascadeEngine.run_cascade(
            experiment=exp,
            target_query=req.target_memory,
            intervention_type=req.intervention,
            dose=req.dose,
        )
        GenomeStore.put_cascade(req.experiment_id, req.target_memory, req.intervention, req.dose, cmap)
        breakdown = CascadeEngine.compute_influence_breakdown(cmap)
        surprise = CascadeEngine.detect_surprise(cmap, req.dose)
        return {
            "cascade": cmap.to_dict(),
            "influence_breakdown": breakdown.to_dict(),
            "surprise": surprise,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/cascade-graph")
def get_cascade_graph(
    exp_id: str,
    mem_id: str,
    request: Request,
    intervention: str = Query("remove", description="Intervention type"),
    dose: float = Query(1.0, ge=0.0, le=2.0),
) -> Dict[str, Any]:
    """Retrieve cascade graph for memory item."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        cmap = CascadeEngine.run_cascade(exp, mem_id, intervention_type=intervention, dose=dose)
        return {"cascade_graph": cmap.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/first-divergence")
def get_cascade_divergence(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve first divergence sequence and propagation timeline."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        cmap = CascadeEngine.run_cascade(exp, mem_id, intervention_type="remove")
        return {
            "first_divergence_step": cmap.first_divergence_step,
            "divergence_order": cmap.divergence_order,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




@genome_router.get("/{exp_id}/{mem_id}/fragility")
def run_fragility_analysis(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Run single-point-of-failure fragility evaluation."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        report = FragilityAnalyzer.analyze_fragility(exp, mem_id)
        return {"fragility": report.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/redundancy")
def run_redundancy_analysis(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Discover alternative compensation paths that buffer memory loss."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        rec = RedundancyAnalyzer.analyze_redundancy(exp, mem_id)
        return {"redundancy": rec.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.post("/dose-response")
def run_dose_response(req: DoseResponseRequest, request: Request) -> Dict[str, Any]:
    """Run 5-point dose response experiment: 100%, 75%, 50%, 25%, 0%."""
    store = get_exp_store(request)
    exp = _resolve_experiment(req.experiment_id, store)

    try:
        eval_res = DoseResponseEngine.run_dose_response(exp, req.target_memory)
        return {"dose_response": eval_res.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/threshold")
def detect_threshold(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Detect critical dose threshold inflection points."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        eval_res = DoseResponseEngine.run_dose_response(exp, mem_id)
        return {
            "threshold_detected": eval_res.inflection_detected,
            "threshold_dose": eval_res.threshold_dose,
            "pattern": eval_res.pattern.value,
            "explanation": eval_res.explanation,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.post("/recovery-test")
def run_recovery_test(req: RecoveryTestRequest, request: Request) -> Dict[str, Any]:
    """Test before-during-after intervention recovery dynamics."""
    store = get_exp_store(request)
    exp = _resolve_experiment(req.experiment_id, store)

    try:
        rec_res = RecoveryEngine.test_recovery(exp, req.target_memory)
        return {"recovery": rec_res.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




@genome_router.post("/mutation")
def create_memory_mutation(req: MutationRequest, request: Request) -> Dict[str, Any]:
    """Clone experiment and apply an isolated, non-destructive memory mutation."""
    store = get_exp_store(request)
    exp = _resolve_experiment(req.experiment_id, store)

    try:
        mutated_exp = MutationEngine.mutate_memory(exp, req.target_memory, req.mutation_factor)
        store.save(mutated_exp)
        return {
            "mutated_experiment_id": mutated_exp.experiment_id,
            "target_memory": req.target_memory,
            "mutation_factor": req.mutation_factor,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.post("/sandbox/branch")
def create_sandbox_branch(req: BranchCreateRequest, request: Request) -> Dict[str, Any]:
    """Create a new replayable sandbox branch without mutating the parent."""
    store = get_exp_store(request)
    exp = _resolve_experiment(req.experiment_id, store)

    try:
        branch = SandboxManager.create_branch(exp, req.parent_id, req.intervention)
        return {"branch": branch.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/sandbox/branches/{exp_id}")
def list_sandbox_branches(exp_id: str) -> Dict[str, Any]:
    """List all registered sandbox branches for an experiment."""
    branches = SandboxManager.list_branches(exp_id)
    return {"branches": [b.to_dict() for b in branches]}


@genome_router.post("/sandbox/compare")
def compare_branches(req: BranchCompareRequest, request: Request) -> Dict[str, Any]:
    """Compare two branch interventions side-by-side."""
    store = get_exp_store(request)
    exp = _resolve_experiment(req.experiment_id, store)

    try:
        comparison = SandboxManager.compare_branches(exp, req.intervention_a, req.intervention_b)
        return {"comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




@genome_router.get("/{exp_id}/{mem_id}/report")
def get_genome_report(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Generate formal Memory Genome Report."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        report = ReportGenerator.generate_genome_report(exp, mem_id)
        return {"report": report.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/cascade-report")
def get_cascade_report(
    exp_id: str,
    mem_id: str,
    request: Request,
    intervention: str = Query("remove", description="Intervention type"),
) -> Dict[str, Any]:
    """Generate quantitative Cascade Simulation Report."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        report = ReportGenerator.generate_cascade_report(exp, mem_id, intervention)
        return {"cascade_report": report.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@genome_router.get("/{exp_id}/{mem_id}/questions")
def get_automatic_questions(exp_id: str, mem_id: str, request: Request) -> Dict[str, Any]:
    """Generate grounded, proactive research questions for a memory item."""
    store = get_exp_store(request)
    exp = _resolve_experiment(exp_id, store)

    try:
        questions = AutomaticResearchQuestionGenerator.generate_questions(exp, mem_id)
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
