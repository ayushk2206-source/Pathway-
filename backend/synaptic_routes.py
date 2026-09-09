"""Synaptic Brain API routes (Phase 01).

Exposes the Live Synaptic Brain for interactive scientific exploration of
synaptic plasticity and associative short-term memory.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request

from core.synaptic import SynapticBrain, extract_synaptic_state_from_experiment
from .schemas import (
    SynapticDecayRequest,
    SynapticRecallRequest,
    SynapticScenarioRequest,
    SynapticWriteRequest,
)

synaptic_router = APIRouter(tags=["synaptic"])

# Global in-memory interactive brain instance for the active session
_LIVE_BRAIN: Optional[SynapticBrain] = None


def get_live_brain(dimension: int = 16, decay: float = 0.05, seed: int = 42) -> SynapticBrain:
    global _LIVE_BRAIN
    if _LIVE_BRAIN is None or _LIVE_BRAIN.d != dimension:
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
