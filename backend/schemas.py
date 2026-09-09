"""Pydantic request/response models for the HTTP API.

These mirror the core dataclasses (``MechanismParams``, ``TaskConfig``,
``ExperimentConfig``) so the API layer validates payloads without the core
ever depending on FastAPI/pydantic. Unknown fields are ignored by default;
validation errors surface as 422s.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MechanismParamsModel(BaseModel):
    state_dim: int = 128
    update_strength: float = 1.0
    memory_strength: float = 1.0
    decay: float = 0.0
    interference_strength: float = 0.5
    sparsity: float = 0.1
    normalize_state: bool = False
    input_noise: float = 0.0


class TaskConfigModel(BaseModel):
    seed: Optional[int] = None
    d: int = 128
    n_objects: int = 6
    n_symbols: int = 4
    n_conflicts: int = 2
    object_similarity: float = 0.0
    symbol_similarity: float = 0.0
    cycles: int = 1
    order: str = "interleaved"
    probe_original: bool = True
    input_noise: float = 0.0
    events: Optional[List[Dict[str, Any]]] = None
    queries: Optional[List[Dict[str, Any]]] = None


class ExperimentRunRequest(BaseModel):
    """Body of POST /api/experiments/run and each entry of /api/compare."""

    seed: int = 42
    mechanism: str = Field(default="baseline", description="key in the mechanism registry")
    params: MechanismParamsModel = MechanismParamsModel()
    task: TaskConfigModel = TaskConfigModel()
    update_steps_per_event: int = 1


class ReplayRequest(BaseModel):
    """Optional overrides for POST /api/experiments/{id}/replay.

    ``params`` re-runs the recorded experiment with modified mechanism
    parameters (a sensitivity probe). Editing the event history itself is
    a Phase-02 counterfactual feature and is not yet implemented.
    """

    params: Optional[MechanismParamsModel] = None


class RecallRequest(BaseModel):
    """Body of POST /api/recall — ask the stored state a question."""

    experiment_id: str
    object_label: str
    timestep: int = Field(
        default=-1, description="events processed (-1 = end of run)"
    )
    expected_symbol_label: Optional[str] = Field(
        default=None, description="optional ground truth to compare against"
    )


class CompareRequest(BaseModel):
    """Body of POST /api/compare — run several configs side by side."""

    configs: List[ExperimentRunRequest] = Field(min_length=1, max_length=12)


class GenerateRequest(BaseModel):
    """Body of POST /api/experiments/generate — materialize a task only."""

    task: TaskConfigModel = TaskConfigModel()
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Phase 02 — memory engine
# ---------------------------------------------------------------------------
class MemoryIn(BaseModel):
    """A text memory: "concept = value" (vectors are encoded deterministically).

    ``value`` may be empty for a pure query.
    """

    concept: str
    value: str = ""
    importance: float = 1.0
    strength: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryWriteRequest(BaseModel):
    """POST /api/memory/write — one atomic write into a fresh mechanism."""

    seed: int = 1
    mechanism: str = "baseline"
    params: MechanismParamsModel = MechanismParamsModel()
    memory: MemoryIn
    timestep: int = 0


class MemoryRecallRequest(BaseModel):
    """POST /api/memory/recall — write a list of memories, then query."""

    seed: int = 1
    mechanism: str = "baseline"
    params: MechanismParamsModel = MechanismParamsModel()
    memories: List[MemoryIn] = Field(min_length=1, max_length=64)
    query: MemoryIn
    expected_value: Optional[str] = None
    measure: str = "cosine"
    top_k: int = 5


class MemoryQuerySpec(BaseModel):
    concept: str
    timestep: int = -1
    kind: str = "latest"


class MemoryExperimentRequest(BaseModel):
    """POST /api/experiments/memory — a full memory experiment."""

    seed: int = 1
    mechanism: str = "baseline"
    params: MechanismParamsModel = MechanismParamsModel()
    memories: List[MemoryIn] = Field(min_length=1, max_length=64)
    queries: Optional[List[MemoryQuerySpec]] = None  # default: latest at end
    input_noise: float = 0.0


class CollisionRequest(BaseModel):
    """POST /api/experiments/collision."""

    seed: int = 16
    mechanism: str = "interference"
    params: MechanismParamsModel = MechanismParamsModel()
    concept: str = "enclosure_7"
    value_a: str = "TIGER"
    value_b: str = "LION"
    similarity: float = 0.8
    strength_a: float = 1.0
    strength_b: float = 1.0


class RetentionRequest(BaseModel):
    """POST /api/experiments/retention."""

    seed: int = 11
    mechanism: str = "leaky"
    params: MechanismParamsModel = MechanismParamsModel()
    lags: List[int] = Field(default_factory=lambda: [0, 5, 10, 20, 40, 80, 160])
    concept: str = "target"
    value: str = "RED"


class AblationRequest(BaseModel):
    """POST /api/experiments/ablation."""

    experiment_id: str
    event_id: str


class CompareStoredRequest(BaseModel):
    """POST /api/experiments/compare (stored experiments)."""

    experiment_id_a: str
    experiment_id_b: str


class ContributionRequest(BaseModel):
    """POST /api/experiments/{id}/memory-contribution."""

    memory_id: str


class CapacityRequest(BaseModel):
    """POST /api/experiments/capacity."""

    seed: int = 12
    mechanism: str = "baseline"
    params: MechanismParamsModel = MechanismParamsModel()
    dimensions: List[int] = Field(default_factory=lambda: [8, 16, 32, 64, 128])
    n_facts: int = 6


class OrderRequest(BaseModel):
    """POST /api/experiments/order."""

    seed: int = 13
    mechanism: str = "leaky"
    params: MechanismParamsModel = MechanismParamsModel()
    orders: List[List[str]] = Field(
        default_factory=lambda: [
            ["alpha_0", "beta_0", "gamma_0", "delta_0"],
            ["delta_0", "gamma_0", "beta_0", "alpha_0"],
            ["alpha_0", "gamma_0", "beta_0", "delta_0"],
        ]
    )


class MatrixRequest(BaseModel):
    """POST /api/experiments/interference-matrix."""

    seed: int = 15
    mechanism: str = "baseline"
    params: MechanismParamsModel = MechanismParamsModel()
    similarities: List[float] = Field(default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    update_strengths: List[float] = Field(
        default_factory=lambda: [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    )


class ScenarioRequest(BaseModel):
    """POST /api/experiments/scenario."""

    name: str
    overrides: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Live Synaptic Brain Schemas
# ---------------------------------------------------------------------------
class SynapticWriteRequest(BaseModel):
    """POST /api/synaptic/write — live Hebbian synaptic write."""

    concept: str
    value: str
    importance: float = 1.0
    strength: float = 1.0
    decay: float = 0.05
    update_strength: float = 1.0
    memory_strength: float = 1.0
    seed: int = 42
    dimension: int = 16


class SynapticRecallRequest(BaseModel):
    """POST /api/synaptic/recall — live associative recall probe."""

    query_concept: str
    expected_value: Optional[str] = None
    measure: str = "cosine"
    top_k: int = 5
    seed: int = 42
    dimension: int = 16


class SynapticDecayRequest(BaseModel):
    """POST /api/synaptic/decay — step dynamics without input."""

    steps: int = 1
    decay: float = 0.05


class SynapticScenarioRequest(BaseModel):
    """POST /api/synaptic/scenario — run educational plasticity preset."""

    scenario: str = "hebbian_formation"
    dimension: int = 16
    decay: float = 0.05
    seed: int = 42


class SynapticDiffRequest(BaseModel):
    """POST /api/synaptic/diff — forensic before/after state delta comparison."""

    step_a: int = 0
    step_b: int = 1
    experiment_id: Optional[str] = None


class SynapticProtocolRequest(BaseModel):
    """POST /api/synaptic/protocol — guided multi-step temporary memory demonstration."""

    protocol_name: str = "temporary_memory"
    dimension: int = 16
    decay: float = 0.05
    seed: int = 42