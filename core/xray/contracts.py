"""Visualization data contracts for frontend rendering (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from .anomalies import detect_state_anomalies
from .changes import detect_state_changes
from .competition import build_competition_graph
from .decay import analyze_decay_curves
from .event_impact import compute_event_impact
from .heatmaps import generate_heatmap_matrices
from .projection import project_memory_map_2d
from .sparsity import analyze_sparsity
from .strength import compute_memory_strengths
from .trajectory import get_state_trajectory


def generate_visualization_contracts(experiment: Experiment) -> Dict[str, Any]:
    """Compile clean frontend-ready data structures across all 10 visual targets.

    1. MEMORY TIMELINE
    2. MEMORY HEATMAP
    3. MEMORY STRENGTH CURVE
    4. MEMORY MAP
    5. MEMORY GRAPH
    6. STATE DIFFERENCE VIEW
    7. DIVERGENCE CURVE
    8. EVENT IMPACT GRAPH
    9. SPARSITY GRAPH
    10. ANOMALY MARKERS
    """
    traj = get_state_trajectory(experiment)
    changes = detect_state_changes(traj)
    heatmaps = generate_heatmap_matrices(experiment)
    strengths_map = compute_memory_strengths(experiment)
    decay_data = analyze_decay_curves(experiment)
    proj_map = project_memory_map_2d(experiment)
    comp_graph = build_competition_graph(experiment)
    impacts = compute_event_impact(experiment)
    sparsity_info = analyze_sparsity(experiment)
    anomalies = detect_state_anomalies(experiment)

    # 1. MEMORY TIMELINE
    timeline_nodes: List[Dict[str, Any]] = []
    for idx, snap in enumerate(experiment.snapshots):
        step = int(snap.get("timestep", idx))
        ev_id = snap.get("event_id")
        ev_obj = experiment.events[idx - 1] if (idx > 0 and idx - 1 < len(experiment.events)) else None
        timeline_nodes.append({
            "step": step,
            "event_id": ev_id,
            "concept_label": ev_obj.get("concept_label") if ev_obj else "INIT",
            "state_norm": float(np.linalg.norm(snap.get("state_vector", []))),
            "active_units": int(np.sum(np.abs(snap.get("state_vector", [])) > 1e-9)),
        })

    # 2. MEMORY HEATMAP
    heatmap_contract = {
        "time_x_memory": heatmaps["time_x_memory"],
        "time_x_unit": heatmaps["time_x_unit"],
        "time_axis": heatmaps["time_axis"],
        "memory_labels": heatmaps["memory_axis"]["labels"],
    }

    # 3. MEMORY STRENGTH CURVES
    strength_curves: List[Dict[str, Any]] = []
    for c in decay_data["curves"]:
        strength_curves.append({
            "memory_id": c["memory_id"],
            "label": c["concept_label"],
            "pattern": c["pattern"],
            "points": c["curve"],
        })

    # 4. MEMORY MAP
    memory_map_contract = proj_map.to_dict()

    # 5. MEMORY GRAPH
    graph_contract = comp_graph.to_dict()

    # 6. STATE DIFFERENCE VIEW
    state_diff_contract = {
        "consecutive_records": changes["records"],
        "high_change_regions": changes["high_change_regions"],
        "stabilization_periods": changes["stabilization_periods"],
    }

    # 7. DIVERGENCE CURVE
    divergence_contract = {
        "supported": True,
        "note": "Populated when comparing against counterfactual branch via /api/xray/divergence",
    }

    # 8. EVENT IMPACT GRAPH
    event_impact_contract = [im.to_dict() for im in impacts]

    # 9. SPARSITY GRAPH
    sparsity_contract = {
        "steps": list(range(len(sparsity_info.active_units_per_step))),
        "active_units": sparsity_info.active_units_per_step,
        "sparsity_ratio": sparsity_info.sparsity_ratio_per_step,
        "mean_sparsity": sparsity_info.mean_sparsity,
    }

    # 10. ANOMALY MARKERS
    anomaly_contract = [a.to_dict() for a in anomalies]

    return {
        "experiment_id": experiment.experiment_id,
        "timeline": timeline_nodes,
        "heatmap": heatmap_contract,
        "strength_curves": strength_curves,
        "memory_map": memory_map_contract,
        "competition_graph": graph_contract,
        "state_difference": state_diff_contract,
        "divergence": divergence_contract,
        "event_impact": event_impact_contract,
        "sparsity": sparsity_contract,
        "anomalies": anomaly_contract,
    }
