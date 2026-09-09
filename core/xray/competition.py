"""Memory competition and relationship graph builder (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from .interference import detect_interference
from .models import CompetitionEdge, CompetitionGraph
from .reinforcement import detect_reinforcement
from .strength import _extract_memory_cues, compute_memory_strengths
from .types import RelationshipType


def build_competition_graph(experiment: Experiment) -> CompetitionGraph:
    """Build a graph representing similarity, association, competition, and reinforcement."""
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    interference_records = detect_interference(experiment)
    reinforcement_records = detect_reinforcement(experiment)

    nodes: List[Dict[str, Any]] = []
    for mem in memories:
        m_id = mem["memory_id"]
        prof = strengths_map.get(m_id)
        nodes.append({
            "id": m_id,
            "label": mem["concept_label"],
            "attribute": mem.get("attribute_label", ""),
            "timestep": mem["timestep"],
            "final_strength": prof.final_strength if prof else 0.0,
            "peak_strength": prof.peak_strength if prof else 0.0,
            "pattern": prof.pattern.value if prof else "unknown",
        })

    edges: List[CompetitionEdge] = []
    seen_edge_keys = set()

    def _add_edge(src: str, tgt: str, rel: RelationshipType, strength: float, evidence: str):
        key = (src, tgt, rel.value)
        if key not in seen_edge_keys:
            seen_edge_keys.add(key)
            edges.append(CompetitionEdge(
                source=src,
                target=tgt,
                relationship=rel,
                strength=float(strength),
                evidence=evidence,
            ))

    # 1. Similarity & Association edges
    for i, m_a in enumerate(memories):
        for j, m_b in enumerate(memories):
            if i >= j:
                continue

            sim = float(cosine(m_a["key_vector"], m_b["key_vector"]))
            if sim > 0.2:
                _add_edge(
                    m_a["memory_id"],
                    m_b["memory_id"],
                    RelationshipType.SIMILARITY,
                    sim,
                    f"Cosine similarity in address vector space: {sim:.3f}",
                )

            # Association if they bind the same or similar attribute/symbol
            if m_a.get("attribute_label") and m_a["attribute_label"] == m_b.get("attribute_label"):
                _add_edge(
                    m_a["memory_id"],
                    m_b["memory_id"],
                    RelationshipType.ASSOCIATION,
                    0.8,
                    f"Shared attribute association: '{m_a['attribute_label']}'",
                )

    # 2. Competition edges
    for ir in interference_records:
        _add_edge(
            ir.memory_a,
            ir.memory_b,
            RelationshipType.COMPETITION,
            ir.interference_score,
            ir.evidence_notes,
        )

    # 3. Reinforcement edges
    for rr in reinforcement_records:
        for r_ev in rr.reinforcement_events:
            _add_edge(
                r_ev,
                rr.memory_id,
                RelationshipType.REINFORCEMENT,
                rr.net_change,
                f"Reinforced memory by +{rr.net_change:.3f} strength increase",
            )

    n_nodes = len(nodes)
    n_edges = len(edges)
    density = float(n_edges / (n_nodes * (n_nodes - 1))) if n_nodes > 1 else 0.0
    avg_deg = float(2.0 * n_edges / n_nodes) if n_nodes > 0 else 0.0

    return CompetitionGraph(
        nodes=nodes,
        edges=edges,
        density=density,
        average_degree=avg_deg,
    )
