"""FastAPI Route Handlers for Phase 22: Experiment Studio."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from core.studio import (
    ExperimentConfig,
    ExperimentHypothesis,
    ExperimentNote,
    ExperimentStudioEngine,
)
from .studio_schemas import (
    ABCompareRequest,
    BranchExperimentRequest,
    ParameterSweepRequest,
    RunExperimentRequest,
    SaveNotesRequest,
)

studio_router = APIRouter(prefix="/api/studio", tags=["Experiment Studio"])

# Singleton engine instance
_studio_engine = ExperimentStudioEngine()


@studio_router.get("/templates")
def get_templates() -> Dict[str, Any]:
    """Retrieve 5 starter experiment templates grounded in real computation."""
    templates = _studio_engine.get_templates()
    return {"templates": templates, "count": len(templates)}


@studio_router.get("/guided-journey")
def get_guided_journey() -> Dict[str, Any]:
    """Retrieve the 8-step guided learner journey."""
    journey = _studio_engine.get_starter_journey()
    return {"journey": journey}


@studio_router.post("/run")
def run_experiment_endpoint(req: RunExperimentRequest) -> Dict[str, Any]:
    """Execute a single configured experiment with baseline vs experiment comparison."""
    try:
        cfg_dict = req.config.model_dump()
        exp_id = cfg_dict.pop("experiment_id", None) or f"EXP-{len(_studio_engine.history) + 1:03d}"
        cfg = ExperimentConfig(experiment_id=exp_id, **cfg_dict)

        hypo = None
        if req.hypothesis:
            hypo = ExperimentHypothesis(
                hypothesis_text=req.hypothesis.hypothesis_text,
                predicted_outcome=req.hypothesis.predicted_outcome,
                predicted_challenge_choice=req.hypothesis.predicted_challenge_choice,
            )

        notes = None
        if req.notes:
            notes = ExperimentNote(**req.notes)

        result = _studio_engine.run_experiment(cfg, hypo, notes)
        return {"result": result.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment execution error: {str(e)}")


@studio_router.post("/ab-compare")
def ab_compare_endpoint(req: ABCompareRequest) -> Dict[str, Any]:
    """Execute two experiment configurations side-by-side and calculate delta matrix."""
    try:
        dict_a = req.config_a.model_dump()
        id_a = dict_a.pop("experiment_id", None) or "EXP-A"
        cfg_a = ExperimentConfig(experiment_id=id_a, **dict_a)

        dict_b = req.config_b.model_dump()
        id_b = dict_b.pop("experiment_id", None) or "EXP-B"
        cfg_b = ExperimentConfig(experiment_id=id_b, **dict_b)

        comparison = _studio_engine.run_ab_comparison(cfg_a, cfg_b)
        return {"comparison": comparison.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A/B comparison error: {str(e)}")


@studio_router.post("/sweep")
def parameter_sweep_endpoint(req: ParameterSweepRequest) -> Dict[str, Any]:
    """Execute a 1D parameter sweep and return empirical non-linear response curve."""
    try:
        dict_base = req.base_config.model_dump()
        dict_base.pop("experiment_id", None)
        base_cfg = ExperimentConfig(experiment_id="EXP-SWEEP-BASE", **dict_base)

        sweep_res = _studio_engine.run_parameter_sweep(
            base_config=base_cfg,
            param_name=req.param_name,
            param_values=req.param_values,
        )
        return {"sweep": sweep_res.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sweep error: {str(e)}")


@studio_router.get("/history")
def get_history() -> Dict[str, Any]:
    """List all completed experiments in session history."""
    items = [
        {
            "experiment_id": e.experiment_id,
            "name": e.config.name,
            "experiment_type": e.config.experiment_type,
            "concept_a": e.config.concept_a,
            "value_a": e.config.value_a,
            "fidelity": e.experiment_metrics["fidelity"],
            "delta_fidelity": e.delta_metrics["fidelity_delta"],
            "hypothesis_status": e.hypothesis.support_status,
            "timestamp": e.timestamp,
        }
        for e in reversed(_studio_engine.history)
    ]
    return {"history": items, "total": len(items)}


@studio_router.get("/experiment/{experiment_id}")
def get_experiment_endpoint(experiment_id: str) -> Dict[str, Any]:
    """Retrieve full result payload for an experiment."""
    exp = next((e for e in _studio_engine.history if e.experiment_id == experiment_id), None)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")
    note = _studio_engine.saved_notes.get(experiment_id, ExperimentNote())
    return {"experiment": exp.to_dict(), "notes": note.to_dict()}


@studio_router.post("/branch")
def branch_experiment_endpoint(req: BranchExperimentRequest) -> Dict[str, Any]:
    """Duplicate an experiment, modify one parameter, and execute."""
    try:
        branched_result = _studio_engine.duplicate_and_branch(
            experiment_id=req.experiment_id,
            modified_param=req.modified_param,
            new_value=req.new_value,
        )
        return {"result": branched_result.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Branch error: {str(e)}")


@studio_router.post("/save-notes")
def save_notes_endpoint(req: SaveNotesRequest) -> Dict[str, Any]:
    """Save learner notes for an experiment."""
    note = ExperimentNote(
        question=req.question,
        hypothesis=req.hypothesis,
        observation=req.observation,
        conclusion=req.conclusion,
    )
    _studio_engine.saved_notes[req.experiment_id] = note
    return {"status": "saved", "notes": note.to_dict()}


@studio_router.get("/export/{experiment_id}")
def export_experiment_endpoint(experiment_id: str) -> Dict[str, Any]:
    """Export complete reproducible JSON research artifact."""
    try:
        artifact = _studio_engine.export_experiment_json(experiment_id)
        return artifact
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
