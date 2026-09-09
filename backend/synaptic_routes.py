"""Synaptic Brain API routes (Phase 01).

Exposes the Live Synaptic Brain for interactive scientific exploration of
synaptic plasticity and associative short-term memory.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request

from core.synaptic import (
    SynapticBrain,
    extract_synaptic_history_from_experiment,
    extract_synaptic_state_from_experiment,
)
from .schemas import (
    SynapticDecayRequest,
    SynapticDiffRequest,
    SynapticProtocolRequest,
    SynapticRecallRequest,
    SynapticScenarioRequest,
    SynapticWriteRequest,
)

synaptic_router = APIRouter(tags=["synaptic"])

# Global in-memory interactive brain instance for the active session
_LIVE_BRAIN: Optional[SynapticBrain] = None


def get_live_brain(dimension: Optional[int] = None, decay: float = 0.05, seed: int = 42) -> SynapticBrain:
    global _LIVE_BRAIN
    if _LIVE_BRAIN is None:
        dim = 16 if dimension is None else dimension
        _LIVE_BRAIN = SynapticBrain(seed=seed, d=dim, decay=decay)
    elif dimension is not None and _LIVE_BRAIN.d != dimension:
        _LIVE_BRAIN = SynapticBrain(seed=seed, d=dimension, decay=decay)
    return _LIVE_BRAIN


@synaptic_router.get("/synaptic/info")
def synaptic_info() -> Dict[str, Any]:
    """Educational scientific overview and methodology statement."""
    return {
        "title": "Live Synaptic Brain",
        "topic": "Synaptic Plasticity as Short-Term Memory",
        "description": (
            "Interactive scientific laboratory simulating Hebbian synaptic plasticity "
            "as working memory on a matrix substrate. Neural activity temporarily strengthens "
            "synapses via outer products W <- (1-λ)W + η(v⊗k), and queries recall memories "
            "via linear readout v̂ = W @ k."
        ),
        "mathematical_model": {
            "hebbian_write": "W(t+1) = (1 - λ) · W(t) + η · (v ⊗ k)",
            "associative_recall": "v̂ = W @ k_query",
            "decay_rule": "W(t+n) = (1 - λ)^n · W(t)",
            "similarity_metric": "cosine(v̂, v_target) = <v̂, v_target> / (||v̂|| ||v_target||)",
        },
        "disclaimer": (
            "Educational computational model of associative memory and synaptic plasticity. "
            "This demonstrates mathematical principles of dynamic neural wiring, NOT a literal "
            "biological brain simulation or proprietary LLM internals."
        ),
    }


@synaptic_router.get("/synaptic/state")
def get_synaptic_state(dimension: int = 16, decay: float = 0.05, seed: int = 42) -> Dict[str, Any]:
    """Retrieve the current state of the Live Synaptic Brain."""
    brain = get_live_brain(dimension=dimension, decay=decay, seed=seed)
    return brain.get_state().to_dict()


@synaptic_router.post("/synaptic/write")
def write_synaptic_memory(req: SynapticWriteRequest) -> Dict[str, Any]:
    """Write a new memory into the synaptic network using Hebbian plasticity."""
    brain = get_live_brain(dimension=req.dimension, decay=req.decay, seed=req.seed)
    brain.decay = req.decay
    brain.update_strength = req.update_strength
    brain.memory_strength = req.memory_strength

    state = brain.write(
        concept=req.concept,
        value=req.value,
        importance=req.importance,
        strength=req.strength,
    )
    return state.to_dict()


@synaptic_router.post("/synaptic/recall")
def recall_synaptic_memory(req: SynapticRecallRequest) -> Dict[str, Any]:
    """Probe the synaptic network with a concept key vector."""
    brain = get_live_brain(dimension=req.dimension, seed=req.seed)
    state = brain.recall(
        query_concept=req.query_concept,
        expected_value=req.expected_value,
        measure=req.measure,
        top_k=req.top_k,
    )
    return state.to_dict()


@synaptic_router.post("/synaptic/decay")
def step_synaptic_decay(req: SynapticDecayRequest) -> Dict[str, Any]:
    """Advance time without input, decaying synaptic strengths."""
    brain = get_live_brain()
    brain.decay = req.decay
    state = brain.decay_step(n_steps=req.steps)
    return state.to_dict()


@synaptic_router.post("/synaptic/reset")
def reset_synaptic_brain(dimension: int = 16, decay: float = 0.05, seed: int = 42) -> Dict[str, Any]:
    """Reset the synaptic network state to zero weights."""
    global _LIVE_BRAIN
    _LIVE_BRAIN = SynapticBrain(seed=seed, d=dimension, decay=decay)
    return _LIVE_BRAIN.get_state().to_dict()


@synaptic_router.post("/synaptic/scenario")
def run_synaptic_scenario(req: SynapticScenarioRequest) -> Dict[str, Any]:
    """Run an educational scenario preset on the synaptic brain."""
    brain = get_live_brain(dimension=req.dimension, decay=req.decay, seed=req.seed)
    state = brain.load_scenario(req.scenario)
    return state.to_dict()


@synaptic_router.get("/synaptic/experiment/{experiment_id}/step/{step_idx}")
def get_synaptic_from_experiment(
    experiment_id: str,
    step_idx: int,
    request: Request,
    display_dim: int = 16,
) -> Dict[str, Any]:
    """Extract synaptic network topology from an archived experiment snapshot."""
    store = request.app.state.store
    exp = store.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")

    state = extract_synaptic_state_from_experiment(exp, step_idx=step_idx, display_dim=display_dim)
    return state.to_dict()


@synaptic_router.get("/synaptic/history")
def get_synaptic_history() -> Dict[str, Any]:
    """Retrieve full chronological timeline and metadata of all captured states."""
    brain = get_live_brain()
    timeline = list(brain.history_timeline)
    return {
        "total_steps": len(brain.snapshots),
        "current_timestep": brain.timestep,
        "timeline": timeline,
        "active_synapses_count": int(brain.get_state().active_synapses_count),
        "matrix_norm": float(brain.get_state().matrix_norm),
    }


@synaptic_router.get("/synaptic/snapshot/{step_idx}")
def get_synaptic_snapshot(step_idx: int) -> Dict[str, Any]:
    """Scrub to exact historical state at timestep step_idx."""
    brain = get_live_brain()
    snap = brain.get_state_at_step(step_idx)
    return snap.to_dict()


@synaptic_router.get("/synaptic/synapse/{synapse_id}/history")
def get_synapse_evolution(synapse_id: str) -> Dict[str, Any]:
    """Retrieve historical trajectory of weights and polarity for a specific synapse."""
    brain = get_live_brain()
    return brain.get_synapse_history(synapse_id)


@synaptic_router.get("/synaptic/memory/{concept}/history")
def get_memory_trajectory(concept: str) -> Dict[str, Any]:
    """Retrieve historical retention, active pathway, and recall fidelity for a concept."""
    brain = get_live_brain()
    return brain.get_memory_history(concept)


@synaptic_router.post("/synaptic/diff")
def diff_synaptic_states(req: SynapticDiffRequest, request: Request) -> Dict[str, Any]:
    """Forensic Before/After state comparison between two timesteps."""
    if req.experiment_id:
        store = request.app.state.store
        exp = store.get(req.experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment '{req.experiment_id}' not found.")
        # Construct temporary brain from experiment snapshots to run diff
        snap_a = extract_synaptic_state_from_experiment(exp, req.step_a)
        snap_b = extract_synaptic_state_from_experiment(exp, req.step_b)
        temp_brain = SynapticBrain(seed=exp.seed, d=snap_a.dimension)
        temp_brain.snapshots = [snap_a, snap_b]
        return temp_brain.diff_states(0, 1)

    brain = get_live_brain()
    return brain.diff_states(req.step_a, req.step_b)


@synaptic_router.post("/synaptic/protocol")
def run_synaptic_protocol(req: SynapticProtocolRequest) -> Dict[str, Any]:
    """Execute guided multi-step temporary memory demonstration protocol."""
    brain = get_live_brain(dimension=req.dimension, decay=req.decay, seed=req.seed)
    return brain.run_temporary_memory_protocol()


@synaptic_router.get("/synaptic/experiment/{experiment_id}/history")
def get_experiment_synaptic_history(
    experiment_id: str,
    request: Request,
    display_dim: int = 16,
) -> Dict[str, Any]:
    """Extract complete multi-step synaptic timeline history for an archived experiment."""
    store = request.app.state.store
    exp = store.get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")

    states = extract_synaptic_history_from_experiment(exp, display_dim=display_dim)
    return {
        "experiment_id": experiment_id,
        "total_steps": len(states),
        "states": states,
    }

