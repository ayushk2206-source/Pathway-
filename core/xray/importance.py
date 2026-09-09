"""Multidimensional memory importance evaluation (Phase 05)."""

from __future__ import annotations

from typing import Dict, List
import numpy as np

from core import Experiment
from .competition import build_competition_graph
from .models import MemoryImportance
from .strength import _extract_memory_cues, compute_memory_strengths


def compute_memory_importance(experiment: Experiment) -> Dict[str, MemoryImportance]:
    """Calculate multi-criteria importance metrics for each memory without arbitrary single scores.

    Evaluates:
    1. Counterfactual contribution
    2. State change magnitude
    3. Retrieval relevance
    4. Reinforcement frequency
    5. Persistence
    6. Connectivity
    """
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    comp_graph = build_competition_graph(experiment)
    snapshots = experiment.snapshots
    total_steps = len(snapshots)

    # Calculate graph degree per memory
    degrees: Dict[str, int] = {m["memory_id"]: 0 for m in memories}
    for e in comp_graph.edges:
        if e.source in degrees:
            degrees[e.source] += 1
        if e.target in degrees:
            degrees[e.target] += 1

    max_deg = max(degrees.values()) if degrees and max(degrees.values()) > 0 else 1

    importance_profiles: Dict[str, MemoryImportance] = {}

    for mem in memories:
        m_id = mem["memory_id"]
        c_label = mem["concept_label"]
        enc_step = mem["timestep"] + 1
        prof = strengths_map.get(m_id)

        # 1. State change magnitude when encoded
        if enc_step < len(snapshots) and enc_step > 0:
            s_before = np.asarray(snapshots[enc_step - 1].get("state_vector", []), dtype=np.float64)
            s_after = np.asarray(snapshots[enc_step].get("state_vector", []), dtype=np.float64)
            delta = s_after - s_before
            norm_after = float(np.linalg.norm(s_after))
            state_change = float(np.linalg.norm(delta) / norm_after) if norm_after > 1e-12 else 1.0
        else:
            state_change = 0.5

        # 2. Counterfactual contribution estimation: write magnitude relative to final state
        k_vec = mem["key_vector"]
        v_vec = mem["value_vector"]
        b_norm = float(np.linalg.norm(k_vec) * np.linalg.norm(v_vec))
        final_norm = float(np.linalg.norm(snapshots[-1].get("state_vector", []))) if snapshots else 1.0
        cf_contrib = float(b_norm / (final_norm * len(memories))) if final_norm > 1e-12 and memories else 0.5
        cf_contrib = min(1.0, max(0.05, cf_contrib))

        # 3. Retrieval relevance: was it queried?
        query_hits = 0
        for snap in snapshots:
            for qr in snap.get("query_results", []):
                if qr.get("object_label") == c_label:
                    query_hits += 1
        retrieval_rel = min(1.0, float(query_hits / 3.0)) if query_hits > 0 else 0.1

        # 4. Reinforcement frequency
        remaining_steps = max(1, total_steps - enc_step)
        reinf_count = prof.reinforcement_count if prof else 0
        reinf_freq = min(1.0, float(reinf_count / remaining_steps))

        # 5. Persistence: final strength relative to peak
        if prof and prof.peak_strength > 1e-6:
            persistence = float(prof.final_strength / prof.peak_strength)
        else:
            persistence = 0.0

        # 6. Connectivity in competition/similarity graph
        connectivity = float(degrees.get(m_id, 0) / max_deg)

        importance_profiles[m_id] = MemoryImportance(
            memory_id=m_id,
            counterfactual_contribution=cf_contrib,
            state_change_magnitude=state_change,
            retrieval_relevance=retrieval_rel,
            reinforcement_frequency=reinf_freq,
            persistence=persistence,
            connectivity=connectivity,
        )

    return importance_profiles
