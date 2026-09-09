"""Deterministic synthetic text encoder (Phase 02).

Converts a *text* memory — e.g. ``"capital_of_france = Paris"`` — into
deterministic key/value vectors, reproducible from:

    (text, seed, dimension d)

**This is a synthetic educational representation, not a production
language embedding model.** There is no semantics in these vectors: two
concepts with similar spellings get unrelated vectors. The encoder exists
so learners can work with readable labels ("Vault A access code → BLUE")
while the substrate stays fully deterministic and inspectable.

Vector families (reused from Phase 01, so the binding math is unchanged):

- concept (key) vectors are *flat-spectrum* vectors (random Fourier
  phases), which makes key→value binding exactly invertible;
- value vectors are unit Gaussian vectors.

Two encoding modes:

- independent (default): each text hashes to its own RNG stream, so a
  text's vector depends only on (text, seed, d) — adding memories never
  changes existing vectors;
- batch-correlated (``concept_similarity`` / ``value_similarity`` > 0):
  unique texts in a batch share a base and are perturbed away from it, so
  pairwise similarity ≈ the requested value (needed for collision /
  interference experiments). Batch membership matters in this mode.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Tuple

import numpy as np

from .vectors import (
    correlated_flat_vectors,
    correlated_vectors,
    flat_spectrum_vector,
    random_unit_vector,
)


def _text_seed(text: str, seed: int, d: int, salt: str) -> int:
    digest = hashlib.sha256(
        f"{int(seed)}:{int(d)}:{salt}:{text}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def encode_concept_vector(concept_text: str, seed: int, d: int) -> np.ndarray:
    """Deterministic flat-spectrum key vector for a concept text."""
    rng = np.random.default_rng(_text_seed(concept_text, seed, d, "concept"))
    return flat_spectrum_vector(rng, d)


def encode_value_vector(value_text: str, seed: int, d: int) -> np.ndarray:
    """Deterministic unit Gaussian value vector for a value text."""
    rng = np.random.default_rng(_text_seed(value_text, seed, d, "value"))
    return random_unit_vector(rng, d)


def encode_texts(
    concepts: List[str],
    values: List[str],
    seed: int,
    d: int,
    concept_similarity: float = 0.0,
    value_similarity: float = 0.0,
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """Build ``{text: vector}`` maps for unique concept/value texts.

    With similarity > 0 the batch is correlated (shared base + per-text
    perturbation); with similarity 0 each text encodes independently.
    Both modes are deterministic; ``concept_similarity``/``value_similarity``
    mirror Phase 01's ``object_similarity``/``symbol_similarity``.
    """
    unique_concepts = list(dict.fromkeys(concepts))
    unique_values = list(dict.fromkeys(values))

    if concept_similarity > 1e-9 and len(unique_concepts) > 1:
        rng = np.random.default_rng(_text_seed("__concept_base__", seed, d, "base"))
        cvecs = correlated_flat_vectors(
            rng, len(unique_concepts), d, concept_similarity
        )
        objects: Dict[str, np.ndarray] = dict(zip(unique_concepts, cvecs))
    else:
        objects = {
            c: encode_concept_vector(c, seed, d) for c in unique_concepts
        }

    if value_similarity > 1e-9 and len(unique_values) > 1:
        rng = np.random.default_rng(_text_seed("__value_base__", seed, d, "base"))
        vvecs = correlated_vectors(rng, len(unique_values), d, value_similarity)
        symbols: Dict[str, np.ndarray] = dict(zip(unique_values, vvecs))
    else:
        symbols = {v: encode_value_vector(v, seed, d) for v in unique_values}

    return objects, symbols