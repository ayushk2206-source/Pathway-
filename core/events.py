"""Memory event model (section 5).

An event is one atomic write to the memory state:

    "The symbol associated with object A is RED."

represented as a key–value pair of vectors plus the controls that scale the
write. The complete event history is always preserved inside an
``Experiment`` so that any state transition can be reproduced exactly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_id(timestep: int) -> str:
    # Deterministic ids when the caller does not supply one.
    return f"e{timestep:04d}"


@dataclass
class Event:
    """One write to the memory state.

    Fields
    ------
    id:            stable identifier (default ``e{timestep:04d}``)
    timestep:      position in the event sequence (0-indexed)
    concept_label: the "object" being written about (e.g. "obj_A")
    attribute_label: the "symbol" bound to the concept (e.g. "sym_RED")
    key_vector:    vector encoding of the concept (the cue / address)
    value_vector:  vector encoding of the attribute (the payload)
    importance:    write weight ∈ [0, 1] (global memory-strength scale)
    strength:      write weight ∈ [0, 1] (per-event gain)
    noise:         σ added to key/value vectors at write time (0 = none)
    seed:          explicit per-event RNG seed (None → derived from timestep)
    metadata:      free-form experimenter notes
    timestamp:     wall-clock ISO string (informational only; never part of
                   the computation, so it cannot break determinism)
    """

    id: str = ""
    timestep: int = 0
    concept_label: str = ""
    attribute_label: str = ""
    key_vector: Optional[np.ndarray] = None
    value_vector: Optional[np.ndarray] = None
    importance: float = 1.0
    strength: float = 1.0
    noise: Optional[float] = None  # None → use mechanism-level input_noise
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _default_id(self.timestep)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestep": int(self.timestep),
            "concept_label": self.concept_label,
            "attribute_label": self.attribute_label,
            "key_vector": None if self.key_vector is None else self.key_vector.tolist(),
            "value_vector": None if self.value_vector is None else self.value_vector.tolist(),
            "importance": float(self.importance),
            "strength": float(self.strength),
            "noise": None if self.noise is None else float(self.noise),
            "seed": self.seed,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        kv = d.get("key_vector")
        vv = d.get("value_vector")
        return cls(
            id=d.get("id", ""),
            timestep=int(d.get("timestep", 0)),
            concept_label=d.get("concept_label", ""),
            attribute_label=d.get("attribute_label", ""),
            key_vector=None if kv is None else np.asarray(kv, dtype=np.float64),
            value_vector=None if vv is None else np.asarray(vv, dtype=np.float64),
            importance=float(d.get("importance", 1.0)),
            strength=float(d.get("strength", 1.0)),
            noise=(
                None if d.get("noise") is None else float(d.get("noise", 0.0))
            ),
            seed=d.get("seed"),
            metadata=dict(d.get("metadata", {})),
            timestamp=d.get("timestamp", ""),
        )

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex[:12]