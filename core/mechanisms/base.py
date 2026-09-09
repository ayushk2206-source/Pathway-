"""Mechanism abstraction (section 6).

Every mechanism implements the same contract so the experiment engine can
run any mechanism interchangeably:

    initialize(seed)               — (re)set state to zeros
    update(event) -> trace dict    — apply the write rule to an Event
    step_no_input(n) -> trace dict — advance dynamics without an input
    recall(key_vector) -> vector   — read a value out of the current state
    get_state_snapshot() -> dict   — inspectable, serializable state

The five initial mechanisms are **independent educational toys**. They are
NOT implementations of BDH or of any production memory architecture; they
exist to let learners compare different state-update behaviors on the same
experiment harness.

Shared math
-----------
Each write binds the event's key and value into a vector
``b = bind(key, value)`` (circular convolution, see ``core/vectors.py``)
and applies an effective gain

    gain = update_strength * memory_strength * event.importance * event.strength

Mechanisms differ only in *how the state absorbs* ``gain * b`` — that is
precisely the scientific variable under study.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from ..events import Event
from ..vectors import bind, normalize, top_k_mask, unbind

# A single number streamed from a seeded generator per (seed, timestep) —
# deterministic and reproducible per event. numpy's default_rng no longer
# accepts string seeds, so we hash (seed, timestep) into a stable integer.
_SEED_SEPARATOR = "::"


def _per_event_rng(mech_seed: str, timestep: int) -> np.random.Generator:
    digest = hashlib.sha256(
        f"{mech_seed}{_SEED_SEPARATOR}{timestep}".encode("utf-8")
    ).digest()[:8]
    return np.random.default_rng(int.from_bytes(digest, "big"))


@dataclass
class MechanismParams:
    """All tunable knobs shared by the mechanism layer.

    Every parameter here changes the actual computation — none of them are
    cosmetic. Defaults describe a "moderate" configuration; the experiment
    engine lets learners sweep them.

    state_dim:             dimension d of the fixed-dimensional state
    update_strength:       η — global learning rate / write gain
    memory_strength:       μ — global scale on every write (multiplies η)
    decay:                 λ — forgetting rate applied per step (0 = none)
    interference_strength: γ — erasure of content aligned with a new write
                             (mechanisms C/E; 0 = none)
    sparsity:              κ — fraction of dimensions kept by competitive
                             sparsification, in (0, 1]
    normalize_state:       renormalize state to unit norm after each write
    input_noise:           σ — std-dev of noise injected into key/value
                             vectors at write time (0 = none)
    """

    state_dim: int = 128
    update_strength: float = 1.0
    memory_strength: float = 1.0
    decay: float = 0.0
    interference_strength: float = 0.5
    sparsity: float = 0.1
    normalize_state: bool = False
    input_noise: float = 0.0

    def validated(self) -> "MechanismParams":
        """Clamp fields into their meaningful domains (raises on nonsense)."""
        if self.state_dim < 1:
            raise ValueError("state_dim must be >= 1")
        for name, lo, hi in (
            ("update_strength", 0.0, 10.0),
            ("memory_strength", 0.0, 10.0),
            ("decay", 0.0, 1.0),
            ("interference_strength", 0.0, 2.0),
            ("sparsity", 0.0, 1.0),
            ("input_noise", 0.0, 10.0),
        ):
            v = float(getattr(self, name))
            if not (lo <= v <= hi):
                raise ValueError(f"{name} must be in [{lo}, {hi}], got {v}")
            setattr(self, name, v)
        return self

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state_dim"] = int(d["state_dim"])
        return d


class Mechanism(ABC):
    """Interface every state-update mechanism must implement."""

    #: short registry key, e.g. "baseline"
    name: str = "base"
    #: one-line human description (surfaced in the API and the UI)
    description: str = ""
    #: True when the state is a matrix (e.g. Hebbian) rather than a vector
    state_is_matrix: bool = False

    def __init__(self, params: MechanismParams, seed: int | str) -> None:
        self.params = params.validated()
        self._seed = str(seed)
        self._d = self.params.state_dim
        self.initialize()

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def initialize(self) -> None:
        """(Re)set the state to zeros. The initial state is always zero."""
        if self.state_is_matrix:
            self._state = np.zeros((self._d, self._d))
        else:
            self._state = np.zeros(self._d)

    # ------------------------------------------------------------------
    # core contract
    # ------------------------------------------------------------------
    def update(self, event: Event) -> Dict[str, Any]:
        """Write one event into the state; returns an explanation trace."""
        gain = self._gain(event)
        k, v = self._effective_vectors(event)
        b = bind(k, v)
        return self._absorb(b, gain, k, v, event)

    def step_no_input(self, n: int = 1) -> Dict[str, Any]:
        """Advance the dynamics ``n`` steps with no input (e.g. decay).

        Default behavior: apply the mechanism's decay (identity when decay
        is zero). Mechanisms may override to add richer idle dynamics.
        """
        lam = self.params.decay
        if lam > 0.0:
            self._state = self._state * ((1.0 - lam) ** n)
        return {
            "steps": n,
            "decay_applied": lam,
            "decay_factor_total": float((1.0 - lam) ** n),
            "state_norm": float(np.linalg.norm(self._state)),
        }

    @abstractmethod
    def _absorb(
        self,
        b: np.ndarray,
        gain: float,
        key: np.ndarray,
        value: np.ndarray,
        event: Event,
    ) -> Dict[str, Any]:
        """How this mechanism merges ``gain * b`` into the state."""

    def recall(self, key_vector: np.ndarray) -> np.ndarray:
        """Read a predicted value vector out of the current state."""
        raise NotImplementedError

    def restore_state(self, state_vector: np.ndarray) -> None:
        """Restore a previously snapshotted state (for /recall on history)."""
        arr = np.asarray(state_vector, dtype=np.float64)
        expected = self._state.size
        if arr.size != expected:
            raise ValueError(
                f"state vector has {arr.size} entries, mechanism needs {expected}"
            )
        self._state = arr.reshape(self._state.shape)

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------
    def state_vector(self) -> np.ndarray:
        """Flat numeric view of the state (matrix mechanisms: flattened)."""
        return self._state.reshape(-1)

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Serializable, inspectable snapshot of the current state."""
        flat = self.state_vector()
        mags = np.abs(flat)
        active = np.where(mags > 1e-9)[0]
        return {
            "state_vector": flat.tolist(),
            "shape": list(self._state.shape),
            "norm": float(np.linalg.norm(flat)),
            "active_dimensions": active.tolist(),
            "num_active": int(active.size),
            "sparsity": float(active.size / flat.size) if flat.size else 0.0,
            "params": self.params.to_dict(),
            "mechanism": self.name,
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _gain(self, event: Event) -> float:
        p = self.params
        return float(
            p.update_strength
            * p.memory_strength
            * event.importance
            * event.strength
        )

    def binding_vector(self, event: Event) -> np.ndarray:
        """The exact write pattern for an event (noise applied), ``bind(k, v)``.

        Exposed so analysis code can compute the memory's contribution to a
        state update exactly (Phase 02 memory engine).
        """
        k, v = self._effective_vectors(event)
        return bind(k, v)

    def _effective_vectors(self, event: Event) -> tuple[np.ndarray, np.ndarray]:
        """Apply input noise (seeded → deterministic).

        The event's own ``noise`` field is authoritative (task-level noise
        is copied there at generation time); ``params.input_noise`` is the
        fallback when a mechanism is driven directly with a noise-less event.
        """
        sigma = event.noise if event.noise is not None else self.params.input_noise
        k = np.asarray(event.key_vector, dtype=np.float64)
        v = np.asarray(event.value_vector, dtype=np.float64)
        if sigma > 0.0:
            rng = _per_event_rng(self._seed, event.timestep)
            k = k + sigma * rng.standard_normal(k.shape)
            v = v + sigma * rng.standard_normal(v.shape)
        return k, v

    def _maybe_normalize(self) -> None:
        if self.params.normalize_state:
            self._state = normalize(self._state)

    # ------------------------------------------------------------------
    # pure rule (exposed for forensics / tests / future mechanisms)
    # ------------------------------------------------------------------
    @staticmethod
    def rule(
        state: np.ndarray, b: np.ndarray, gain: float, params: MechanismParams
    ) -> np.ndarray:
        """Pure function of the update rule (state in → state out)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mechanism A — Baseline accumulation
# ---------------------------------------------------------------------------
class BaselineAccumulation(Mechanism):
    """Pure superposition: ``x <- x + gain * b``.

    Nothing is forgotten (no decay), nothing is normalized. New information
    piles onto old information; recall degrades only through cross-talk
    between bindings. Naive but instructive: it is the upper bound on
    retention for *any* individual event and the worst case for separation.
    """

    name = "baseline"
    description = (
        "Accumulation: add every binding to the state without decay or "
        "normalization (naive superposition)."
    )

    def _absorb(self, b, gain, key, value, event):
        self._state = self._state + gain * b
        self._maybe_normalize()
        return {
            "mechanism": self.name,
            "write_gain": float(gain),
            "binding_norm": float(np.linalg.norm(b)),
            "state_norm_after": float(np.linalg.norm(self._state)),
            "note": "superposed binding onto state (no decay, no competition)",
        }

    def recall(self, key_vector: np.ndarray) -> np.ndarray:
        return unbind(self._state, np.asarray(key_vector, dtype=np.float64))

    @staticmethod
    def rule(state, b, gain, params):
        return state + gain * b


# ---------------------------------------------------------------------------
# Mechanism B — Leaky recurrent state
# ---------------------------------------------------------------------------
class LeakyRecurrent(Mechanism):
    """Recurrent decay: ``x <- (1 - λ) * x + gain * b``.

    Old content fades exponentially; only information refreshed (or written
    recently) survives. Later events dominate, so conflicting information
    *replaces* earlier information. The effective memory horizon is
    ~1/λ events.
    """

    name = "leaky"
    description = (
        "Leaky recurrent: exponential forgetting (decay λ) with each write; "
        "recent content dominates and old content fades."
    )

    def _absorb(self, b, gain, key, value, event):
        lam = self.params.decay
        before = np.linalg.norm(self._state)
        self._state = (1.0 - lam) * self._state + gain * b
        self._maybe_normalize()
        return {
            "mechanism": self.name,
            "write_gain": float(gain),
            "decay_applied": float(lam),
            "old_state_norm": float(before),
            "binding_norm": float(np.linalg.norm(b)),
            "state_norm_after": float(np.linalg.norm(self._state)),
            "note": f"scaled state by (1-λ)={1.0 - lam:.4f}, then added binding",
        }

    def recall(self, key_vector: np.ndarray) -> np.ndarray:
        return unbind(self._state, np.asarray(key_vector, dtype=np.float64))

    @staticmethod
    def rule(state, b, gain, params):
        return (1.0 - params.decay) * state + gain * b


# ---------------------------------------------------------------------------
# Mechanism C — Competitive memory update (k-WTA sparsification)
# ---------------------------------------------------------------------------
class CompetitiveUpdate(Mechanism):
    """Superposition followed by top-k sparsification.

    ``x <- top_k(x + gain * b)`` where ``k = max(1, round(κ·d))`` keeps the
    largest-magnitude dimensions and zeros the rest. The state becomes a
    sparse distributed code: capacity grows with the number of available
    "slots", and two memories interfere when they compete for the same
    winning dimensions. Ties break by index, so this is fully deterministic.
    """

    name = "competitive"
    description = (
        "Competitive: after each write, keep only the top-κ·d dimensions "
        "(k-WTA sparsification) — memories compete for winning units."
    )

    def _k(self) -> int:
        return max(1, int(round(self.params.sparsity * self._d)))

    def _absorb(self, b, gain, key, value, event):
        k = self._k()
        self._state = self._state + gain * b
        mask = top_k_mask(self._state, k)
        kept = self._state[mask]
        self._state = np.where(mask, self._state, 0.0)
        self._maybe_normalize()
        return {
            "mechanism": self.name,
            "write_gain": float(gain),
            "k_kept": int(k),
            "binding_norm": float(np.linalg.norm(b)),
            "kept_magnitude_sum": float(np.sum(np.abs(kept))),
            "state_norm_after": float(np.linalg.norm(self._state)),
            "note": f"superposed binding, then kept top-{k} |dimensions|",
        }

    def recall(self, key_vector: np.ndarray) -> np.ndarray:
        return unbind(self._state, np.asarray(key_vector, dtype=np.float64))

    def step_no_input(self, n: int = 1) -> Dict[str, Any]:
        # Sparse code is already sparse; only decay applies.
        return super().step_no_input(n)

    @staticmethod
    def rule(state, b, gain, params):
        k = max(1, int(round(params.sparsity * state.shape[0])))
        return np.where(top_k_mask(state + gain * b, k), state + gain * b, 0.0)


# ---------------------------------------------------------------------------
# Mechanism D — Hebbian associative update (matrix outer-product memory)
# ---------------------------------------------------------------------------
class HebbianAssociative(Mechanism):
    """Outer-product correlation memory: ``M <- (1-λ) M + gain · v kᵀ``.

    The state is a fixed d×d matrix (flattened dimension d²). Recall is a
    matrix–vector product ``v̂ = M @ key`` — a genuine linear associative
    memory (Anderson/Kohonen style). Conflicting associations to the same
    key add competing rank-1 terms to the same row space; their interference
    shows up directly in the readout. Optional decay λ forgets old
    associations exponentially.
    """

    name = "hebbian"
    description = (
        "Hebbian associative: fixed d×d matrix state updated with outer "
        "products v⊗k; recall is a matrix–vector readout."
    )
    state_is_matrix = True

    def _absorb(self, b, gain, key, value, event):
        lam = self.params.decay
        self._state = (1.0 - lam) * self._state + gain * np.outer(value, key)
        return {
            "mechanism": self.name,
            "write_gain": float(gain),
            "decay_applied": float(lam),
            "rank1_norm": float(np.linalg.norm(np.outer(value, key))),
            "state_norm_after": float(np.linalg.norm(self._state)),
            "note": f"accumulated outer product v⊗k ((1-λ)={1.0 - lam:.4f} decay)",
        }

    def recall(self, key_vector: np.ndarray) -> np.ndarray:
        q = np.asarray(key_vector, dtype=np.float64)
        return self._state @ q

    def step_no_input(self, n: int = 1) -> Dict[str, Any]:
        return super().step_no_input(n)

    @staticmethod
    def rule(state, b, gain, params):
        raise NotImplementedError(
            "Hebbian rule needs (key, value); use _absorb instead"
        )


# ---------------------------------------------------------------------------
# Mechanism E — Interference-sensitive update
# ---------------------------------------------------------------------------
class InterferenceSensitive(Mechanism):
    """Similarity-gated overwrite: erase what aligns with the new memory.

    ``x <- (1-λ) x − γ · ⟨x, b̂⟩ · b̂ + gain · b``   with ``b̂ = b / ‖b‖``

    The new binding erases the projection of the *existing* state onto its
    own direction, scaled by the interference strength γ. When the incoming
    memory is similar to stored content (large ⟨x, b̂⟩) the old content is
    strongly overwritten — competing information interferes. When it is
    orthogonal, the old content survives untouched. This is the mechanism
    whose failure mode most closely mirrors catastrophic interference.
    """

    name = "interference"
    description = (
        "Interference-sensitive: a new write erases the projection of the "
        "old state onto its own direction (γ-scaled) before adding itself."
    )

    def _absorb(self, b, gain, key, value, event):
        lam = self.params.decay
        gamma = self.params.interference_strength
        nb = float(np.linalg.norm(b))
        if nb > 1e-12:
            b_hat = b / nb
            proj = float(np.dot(self._state, b_hat))
            erased = proj * b_hat
        else:
            b_hat, proj, erased = np.zeros_like(b), 0.0, np.zeros_like(b)
        self._state = (1.0 - lam) * self._state - gamma * erased + gain * b
        self._maybe_normalize()
        return {
            "mechanism": self.name,
            "write_gain": float(gain),
            "decay_applied": float(lam),
            "interference_strength": float(gamma),
            "projection_onto_new_binding": float(proj),
            "erased_norm": float(np.linalg.norm(gamma * erased)),
            "binding_norm": float(nb),
            "state_norm_after": float(np.linalg.norm(self._state)),
            "note": (
                f"erased {np.linalg.norm(gamma * erased):.4f} of old content "
                f"aligned with the new binding (γ={gamma:.2f})"
            ),
        }

    def recall(self, key_vector: np.ndarray) -> np.ndarray:
        return unbind(self._state, np.asarray(key_vector, dtype=np.float64))

    @staticmethod
    def rule(state, b, gain, params):
        nb = float(np.linalg.norm(b))
        if nb > 1e-12:
            b_hat = b / nb
            proj = float(np.dot(state, b_hat))
        else:
            b_hat, proj = np.zeros_like(b), 0.0
        return (1.0 - params.decay) * state - params.interference_strength * proj * b_hat + gain * b