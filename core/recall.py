"""Recall execution (sections 5, 8).

A query "what is the symbol of <object>?" is answered by:

1. reading the mechanism's predicted value vector for the object's key,
2. comparing it against the known symbol library (cosine similarity),
3. predicting the best-matching symbol label.

The same pipeline works for every mechanism because every mechanism
exposes ``recall(key_vector) -> value_vector``. The *quality* of that
readout is exactly what differs between mechanisms.

``QueryResult`` records the full answer: prediction, ground truth,
confidence, correctness, and the similarity to the true value — the raw
material for the metrics and, later, forensic reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np

from .mechanisms.base import Mechanism
from .task import Query
from .vectors import cosine


@dataclass
class QueryResult:
    query_id: str
    timestep: int
    object_label: str
    kind: str  # "latest" | "original"
    predicted_vector: np.ndarray
    predicted_label: str
    truth_label: str
    confidence: float  # max cosine over the symbol library
    correctness: bool
    quality: float  # cosine(predicted_vector, truth_vector)
    top_matches: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "timestep": int(self.timestep),
            "object_label": self.object_label,
            "kind": self.kind,
            "predicted_vector": self.predicted_vector.tolist(),
            "predicted_label": self.predicted_label,
            "truth_label": self.truth_label,
            "confidence": float(self.confidence),
            "correctness": bool(self.correctness),
            "quality": float(self.quality),
            "top_matches": self.top_matches,
        }


def execute_query(
    mechanism: Mechanism,
    query: Query,
    symbols: Dict[str, np.ndarray],
) -> QueryResult:
    """Answer one query against the mechanism's *current* state."""
    v_hat = mechanism.recall(query.key_vector)
    matches = [
        {
            "label": label,
            "similarity": cosine(v_hat, vec),
        }
        for label, vec in symbols.items()
    ]
    matches.sort(key=lambda m: m["similarity"], reverse=True)
    predicted = matches[0]["label"]
    truth_vec = query.expected_value_vector
    return QueryResult(
        query_id=query.id,
        timestep=query.timestep,
        object_label=query.object_label,
        kind=query.kind,
        predicted_vector=v_hat,
        predicted_label=predicted,
        truth_label=query.expected_attribute_label,
        confidence=float(matches[0]["similarity"]),
        correctness=predicted == query.expected_attribute_label,
        quality=cosine(v_hat, truth_vec) if truth_vec is not None else 0.0,
        top_matches=matches,
    )