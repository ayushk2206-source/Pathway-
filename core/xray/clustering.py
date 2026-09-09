"""Memory representation clustering (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine, normalize
from .models import ClusterResult
from .strength import _extract_memory_cues


def cluster_memory_representations(
    experiment: Experiment,
    max_clusters: int = 4,
    distance_threshold: float = 0.6,
) -> List[ClusterResult]:
    """Cluster memory representations based on vector geometry using agglomerative clustering.

    Evaluates intra-cluster cohesion and inter-cluster separation metrics.
    """
    memories = _extract_memory_cues(experiment)
    if not memories:
        return []

    # Represent each memory by its normalized key/binding vector
    vectors = [normalize(m["key_vector"]) for m in memories]
    n = len(memories)

    if n == 1:
        return [
            ClusterResult(
                cluster_id=0,
                members=[memories[0]["memory_id"]],
                centroid=vectors[0].tolist(),
                cohesion=1.0,
                separation=1.0,
            )
        ]

    # Distance matrix (cosine distance: 1 - cosine_sim)
    dist_matrix = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d = 1.0 - max(-1.0, min(1.0, float(cosine(vectors[i], vectors[j]))))
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d

    # Agglomerative clustering with complete linkage
    # Start with each item in its own cluster
    clusters: Dict[int, List[int]] = {i: [i] for i in range(n)}

    while len(clusters) > 1 and len(clusters) > max_clusters:
        # Find pair with smallest maximum distance
        best_pair = None
        min_dist = float("inf")
        c_keys = list(clusters.keys())

        for idx_a in range(len(c_keys)):
            c_a = c_keys[idx_a]
            for idx_b in range(idx_a + 1, len(c_keys)):
                c_b = c_keys[idx_b]
                # Complete linkage distance
                max_d = max(dist_matrix[i, j] for i in clusters[c_a] for j in clusters[c_b])
                if max_d < min_dist:
                    min_dist = max_d
                    best_pair = (c_a, c_b)

        if best_pair is None or (len(clusters) <= max_clusters and min_dist > distance_threshold):
            break

        # Merge best pair
        c1, c2 = best_pair
        clusters[c1].extend(clusters[c2])
        del clusters[c2]

    results: List[ClusterResult] = []
    centroids: List[np.ndarray] = []

    for c_id, (old_key, member_indices) in enumerate(clusters.items()):
        member_vecs = [vectors[idx] for idx in member_indices]
        centroid = np.mean(member_vecs, axis=0)
        norm_c = np.linalg.norm(centroid)
        if norm_c > 1e-12:
            centroid = centroid / norm_c
        centroids.append(centroid)

        # Cohesion: mean cosine similarity to centroid
        cohesions = [float(cosine(v, centroid)) for v in member_vecs]
        mean_cohesion = float(np.mean(cohesions)) if cohesions else 1.0

        member_ids = [memories[idx]["memory_id"] for idx in member_indices]
        results.append(
            ClusterResult(
                cluster_id=c_id,
                members=member_ids,
                centroid=centroid.tolist(),
                cohesion=mean_cohesion,
                separation=1.0,  # Computed below
            )
        )

    # Compute inter-cluster separation
    for i, res in enumerate(results):
        if len(centroids) > 1:
            sep_dists = [
                float(1.0 - cosine(centroids[i], centroids[j]))
                for j in range(len(centroids))
                if i != j
            ]
            res.separation = float(np.mean(sep_dists)) if sep_dists else 1.0
        else:
            res.separation = 1.0

    return results
