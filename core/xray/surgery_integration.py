"""Memory surgery and X-Ray topological diff integration (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from .competition import build_competition_graph
from .projection import project_memory_map_2d
from .strength import compute_memory_strengths


def compare_xray_surgery(
    original_experiment: Experiment,
    counterfactual_experiment: Experiment,
) -> Dict[str, Any]:
    """Compare memory X-Ray topological maps and competition graphs before and after intervention."""
    orig_map = project_memory_map_2d(original_experiment)
    cf_map = project_memory_map_2d(counterfactual_experiment)

    orig_graph = build_competition_graph(original_experiment)
    cf_graph = build_competition_graph(counterfactual_experiment)

    orig_strengths = compute_memory_strengths(original_experiment)
    cf_strengths = compute_memory_strengths(counterfactual_experiment)

    # Coordinate shifts in 2D projected space
    cf_pts_by_id = {p.memory_id: p for p in cf_map.points}
    point_shifts: List[Dict[str, Any]] = []

    for orig_p in orig_map.points:
        m_id = orig_p.memory_id
        if m_id in cf_pts_by_id:
            cf_p = cf_pts_by_id[m_id]
            dx = cf_p.x - orig_p.x
            dy = cf_p.y - orig_p.y
            dist_shift = float(np.hypot(dx, dy))

            orig_s = orig_strengths.get(m_id)
            cf_s = cf_strengths.get(m_id)
            s_delta = (cf_s.final_strength - orig_s.final_strength) if (orig_s and cf_s) else 0.0

            point_shifts.append({
                "memory_id": m_id,
                "label": orig_p.label,
                "orig_coords": [orig_p.x, orig_p.y],
                "cf_coords": [cf_p.x, cf_p.y],
                "shift_magnitude": dist_shift,
                "strength_delta": float(s_delta),
            })

    # Graph edge differences (competition/similarity)
    orig_edge_tuples = {(e.source, e.target, e.relationship.value) for e in orig_graph.edges}
    cf_edge_tuples = {(e.source, e.target, e.relationship.value) for e in cf_graph.edges}

    added_edges = [
        e.to_dict() for e in cf_graph.edges
        if (e.source, e.target, e.relationship.value) not in orig_edge_tuples
    ]
    removed_edges = [
        e.to_dict() for e in orig_graph.edges
        if (e.source, e.target, e.relationship.value) not in cf_edge_tuples
    ]

    return {
        "original_experiment_id": original_experiment.experiment_id,
        "counterfactual_experiment_id": counterfactual_experiment.experiment_id,
        "original_map": orig_map.to_dict(),
        "counterfactual_map": cf_map.to_dict(),
        "point_shifts": point_shifts,
        "topological_edges": {
            "original_edge_count": len(orig_graph.edges),
            "counterfactual_edge_count": len(cf_graph.edges),
            "added_edges": added_edges,
            "removed_edges": removed_edges,
        },
        "summary": (
            f"Intervention altered {len(point_shifts)} memory positions. "
            f"{len(added_edges)} relationships emerged, {len(removed_edges)} severed."
        ),
    }
