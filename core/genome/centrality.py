"""Memory Centrality Analysis and Dependency Matrix for Phase 08."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np

from core import Experiment
from core.vectors import cosine
from core.xray.strength import _extract_memory_cues
from .models import DependencyMatrix, MemoryCentralityRecord


class CentralityAnalyzer:
    """Calculates graph centrality metrics for memories within an experiment."""

    @classmethod
    def analyze_centrality(cls, experiment: Experiment) -> List[MemoryCentralityRecord]:
        """Compute degree, weighted degree, downstream reach, and eigenvector centrality."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            return []

        n = len(memories)
        labels = [m["concept_label"] for m in memories]
        ids = [m["memory_id"] for m in memories]
        keys = [m["key_vector"] for m in memories]

        # 1. Build adjacency matrix based on key vector cosine similarity
        adj = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(i + 1, n):
                sim = max(0.0, float(cosine(keys[i], keys[j])))
                if sim > 0.15:
                    adj[i, j] = sim
                    adj[j, i] = sim

        # 2. Eigenvector Centrality via Power Iteration
        v = np.ones(n, dtype=np.float64) / np.sqrt(n)
        for _ in range(50):
            v_next = adj @ v
            norm = np.linalg.norm(v_next)
            if norm > 1e-12:
                v = v_next / norm
            else:
                break
        eig_centrality = v / (np.max(v) if np.max(v) > 0 else 1.0)

        # 3. Assemble per-memory records
        records: List[MemoryCentralityRecord] = []
        for i in range(n):
            degree = int(np.sum(adj[i] > 0))
            weighted_degree = float(np.sum(adj[i]))

            # Downstream reach: items written at subsequent timesteps that share associations
            target_step = int(memories[i]["timestep"])
            downstream_reach = sum(
                1 for j in range(n) if int(memories[j]["timestep"]) > target_step and adj[i, j] > 0
            )

            influence = float(round(0.4 * (degree / max(1, n - 1)) + 0.3 * (weighted_degree / max(1.0, float(np.max(np.sum(adj, axis=1))))) + 0.3 * float(eig_centrality[i]), 4))

            records.append(
                MemoryCentralityRecord(
                    memory_id=ids[i],
                    concept_label=labels[i],
                    degree=degree,
                    weighted_degree=round(weighted_degree, 4),
                    downstream_reach=downstream_reach,
                    eigenvector_centrality=round(float(eig_centrality[i]), 4),
                    influence=influence,
                )
            )

        records.sort(key=lambda r: r.influence, reverse=True)
        return records


class DependencyMatrixBuilder:
    """Builds the pairwise N x N Memory Dependency Matrix."""

    @classmethod
    def build_matrix(cls, experiment: Experiment, metric: str = "association") -> DependencyMatrix:
        """Construct the dependency matrix for memories in the experiment."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            return DependencyMatrix(memories=[], matrix=[], metric=metric)

        n = len(memories)
        labels = [m["concept_label"] for m in memories]
        keys = [m["key_vector"] for m in memories]

        matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        metric_clean = metric.strip().lower()

        if metric_clean == "influence":
            # Directed influence: earlier memory influences subsequent memory
            for i in range(n):
                for j in range(n):
                    if i == j:
                        matrix[i][j] = 1.0
                    else:
                        sim = max(0.0, float(cosine(keys[i], keys[j])))
                        step_i = int(memories[i]["timestep"])
                        step_j = int(memories[j]["timestep"])
                        if step_j >= step_i:
                            # Forward propagation influence
                            matrix[i][j] = round(sim * (1.0 - (step_j - step_i) * 0.05), 4)
                        else:
                            matrix[i][j] = round(sim * 0.3, 4)

        elif metric_clean == "sensitivity":
            # Pairwise sensitivity: cross-talk interference vulnerability
            for i in range(n):
                for j in range(n):
                    if i == j:
                        matrix[i][j] = 0.0
                    else:
                        sim = float(cosine(keys[i], keys[j]))
                        matrix[i][j] = round(max(0.0, sim), 4)

        else:
            # Default: Symmetric Association Cosine Similarity
            for i in range(n):
                for j in range(n):
                    if i == j:
                        matrix[i][j] = 1.0
                    else:
                        sim = float(cosine(keys[i], keys[j]))
                        matrix[i][j] = round(max(-1.0, min(1.0, sim)), 4)

        return DependencyMatrix(
            memories=labels,
            matrix=matrix,
            metric=metric,
        )
