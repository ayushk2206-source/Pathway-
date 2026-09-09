"""Memory neighborhood and nearest neighbor lookup (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from .strength import _extract_memory_cues, compute_memory_strengths


def find_nearest_memories(
    experiment: Experiment,
    memory_id: str,
    k: int = 5,
) -> List[Dict[str, Any]]:
    """Find the k nearest memories to a target memory in vector representation space.

    Returns:
    - target memory details
    - cosine similarity
    - L2 Euclidean distance
    - empirical relationship evidence
    """
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)

    target_mem = next((m for m in memories if m["memory_id"] == memory_id), None)
    if not target_mem:
        return []

    target_vec = target_mem["key_vector"]
    neighbors: List[Dict[str, Any]] = []

    for m in memories:
        if m["memory_id"] == memory_id:
            continue

        vec = m["key_vector"]
        sim = max(-1.0, min(1.0, float(cosine(target_vec, vec))))
        l2 = float(np.linalg.norm(target_vec - vec))

        prof = strengths_map.get(m["memory_id"])
        evidence = []
        if sim > 0.4:
            evidence.append(f"High cue overlap ({sim:.3f})")
        if m.get("attribute_label") == target_mem.get("attribute_label"):
            evidence.append(f"Shared attribute '{m.get('attribute_label')}'")
        if not evidence:
            evidence.append(f"Cosine distance: {1.0 - sim:.3f}")

        neighbors.append({
            "memory_id": m["memory_id"],
            "concept_label": m["concept_label"],
            "attribute_label": m.get("attribute_label", ""),
            "cosine_similarity": sim,
            "l2_distance": l2,
            "final_strength": prof.final_strength if prof else 0.0,
            "relationship_evidence": "; ".join(evidence),
        })

    # Sort by similarity descending (closest first)
    neighbors.sort(key=lambda x: x["cosine_similarity"], reverse=True)
    return neighbors[:k]
