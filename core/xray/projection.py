"""2D memory projection map generation (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core import Experiment
from core.vectors import normalize, unbind
from .clustering import cluster_memory_representations
from .models import MemoryMap2D, MemoryMapPoint
from .strength import _extract_memory_cues, compute_memory_strengths


def project_memory_map_2d(experiment: Experiment) -> MemoryMap2D:
    """Project memory vectors into 2D coordinates using Principal Component Analysis (PCA).

    CRITICAL INVARIANT:
    2D projection is purely a visualization approximation. Projected distances must
    never be interpreted as exact Euclidean distances in the high-dimensional substrate.
    """
    memories = _extract_memory_cues(experiment)
    strengths_map = compute_memory_strengths(experiment)
    clusters = cluster_memory_representations(experiment)

    # Map memory_id -> cluster_id
    cluster_map: Dict[str, int] = {}
    for c in clusters:
        for m_id in c.members:
            cluster_map[m_id] = c.cluster_id

    if not memories:
        return MemoryMap2D(points=[], variance_explained=[0.0, 0.0])

    # Extract final memory state vector if available
    final_state: Optional[np.ndarray] = None
    if experiment.snapshots:
        raw_s = experiment.snapshots[-1].get("state_vector")
        if raw_s is not None and len(raw_s) > 0:
            final_state = np.asarray(raw_s, dtype=np.float64)

    # Build matrix of memory representation vectors in state space [n_memories, d]
    rep_vectors: List[np.ndarray] = []
    for m in memories:
        k = m["key_vector"]
        if final_state is not None and np.linalg.norm(final_state) > 1e-9:
            v_rep = unbind(final_state, k)
            if np.linalg.norm(v_rep) > 1e-9:
                rep_vectors.append(v_rep)
            else:
                rep_vectors.append(k)
        else:
            rep_vectors.append(k)

    X_raw = np.array(rep_vectors, dtype=np.float64)
    n, d = X_raw.shape

    if n < 2:
        m = memories[0]
        prof = strengths_map.get(m["memory_id"])
        pts = [
            MemoryMapPoint(
                x=0.0,
                y=0.0,
                memory_id=m["memory_id"],
                label=m["concept_label"],
                strength=prof.final_strength if prof else 0.0,
                cluster=cluster_map.get(m["memory_id"], 0),
                trajectory_tail=[],
            )
        ]
        return MemoryMap2D(points=pts, variance_explained=[1.0, 0.0])

    # Center data
    mean_vec = np.mean(X_raw, axis=0)
    X_centered = X_raw - mean_vec

    # SVD for PCA
    try:
        u, s, vt = np.linalg.svd(X_centered, full_matrices=False)
        total_var = float(np.sum(s ** 2)) if np.sum(s ** 2) > 1e-12 else 1.0

        pc1_var = float((s[0] ** 2) / total_var) if len(s) > 0 else 0.0
        pc2_var = float((s[1] ** 2) / total_var) if len(s) > 1 else 0.0
        var_explained = [pc1_var, pc2_var]

        # Projection basis [d, 2]
        v2 = vt[:2].T
        coords_2d = np.dot(X_centered, v2)
    except Exception:
        coords_2d = np.zeros((n, 2))
        var_explained = [0.5, 0.5]
        v2 = None

    # Compute trajectory tail across timeline snapshots
    trajectory_tails: Dict[str, List[List[float]]] = {m["memory_id"]: [] for m in memories}
    if v2 is not None and experiment.snapshots:
        # Sample snapshots (up to 8 chronological milestones)
        total_snaps = len(experiment.snapshots)
        step_indices = list(range(0, total_snaps, max(1, total_snaps // 8)))
        if total_snaps - 1 not in step_indices:
            step_indices.append(total_snaps - 1)

        for s_idx in step_indices:
            snap_s = np.asarray(experiment.snapshots[s_idx].get("state_vector", []), dtype=np.float64)
            if snap_s.size == d and np.linalg.norm(snap_s) > 1e-9:
                for m in memories:
                    m_id = m["memory_id"]
                    r_t = unbind(snap_s, m["key_vector"])
                    if np.linalg.norm(r_t) > 1e-9:
                        r_centered = r_t - mean_vec
                        proj_t = np.dot(r_centered, v2)
                        trajectory_tails[m_id].append([float(proj_t[0]), float(proj_t[1])])

    points: List[MemoryMapPoint] = []
    for idx, m in enumerate(memories):
        m_id = m["memory_id"]
        prof = strengths_map.get(m_id)
        s_val = prof.final_strength if prof else 0.0
        c_id = cluster_map.get(m_id, 0)

        points.append(
            MemoryMapPoint(
                x=float(coords_2d[idx, 0]),
                y=float(coords_2d[idx, 1]),
                memory_id=m_id,
                label=m["concept_label"],
                strength=s_val,
                cluster=c_id,
                trajectory_tail=trajectory_tails.get(m_id, []),
            )
        )

    return MemoryMap2D(
        points=points,
        variance_explained=var_explained,
        projection_method="PCA",
    )
