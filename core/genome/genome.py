"""Memory Genome Builder and Lineage Generator for Phase 08."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from core import Experiment
from core.vectors import cosine, unbind
from core.xray.interference import detect_interference
from core.xray.strength import _extract_memory_cues, compute_memory_strengths
from .models import (
    AssociationEntry,
    CompetitorEntry,
    GenomeDNAStrip,
    MemoryGenome,
    MemoryLineageEdge,
    MemoryLineageGraph,
    MemoryLineageNode,
    ReinforcementRecord,
    RetrievalRecord,
)


def resolve_memory(experiment: Experiment, target_query: str) -> Optional[Dict[str, Any]]:
    """Resolve a target memory by ID, concept label, or case-insensitive matching."""
    memories = _extract_memory_cues(experiment)
    if not memories:
        return None

    target_clean = target_query.strip().lower()

    # 1. Exact ID match
    for m in memories:
        if m["memory_id"].lower() == target_clean:
            return m

    # 2. Exact concept label match
    for m in memories:
        if m["concept_label"].lower() == target_clean:
            return m

    # 3. Substring match
    for m in memories:
        if target_clean in m["concept_label"].lower() or target_clean in m["memory_id"].lower():
            return m

    return memories[0]


class MemoryGenomeBuilder:
    """Builds the comprehensive computational genome of a memory item."""

    @classmethod
    def build(cls, experiment: Experiment, target_query: str) -> MemoryGenome:
        """Construct the MemoryGenome object for the specified target memory."""
        memories = _extract_memory_cues(experiment)
        if not memories:
            raise ValueError(f"Experiment {experiment.experiment_id} contains no valid memory events.")

        target_mem = resolve_memory(experiment, target_query)
        if not target_mem:
            target_mem = memories[0]

        target_id = target_mem["memory_id"]
        target_concept = target_mem["concept_label"]
        k_target = target_mem["key_vector"]
        v_target = target_mem["value_vector"]
        origin_step = int(target_mem["timestep"])

        # Find origin event ID
        origin_event = target_id
        for ev in experiment.events:
            if ev.get("id") == target_id or ev.get("concept_label") == target_concept:
                origin_event = ev.get("id", target_id)
                break

        # Compute trajectory and strengths
        strengths_map = compute_memory_strengths(experiment)
        strength_profile = strengths_map.get(target_id)
        if strength_profile:
            trajectory = [float(s) for s in strength_profile.timeline_strengths]
            current_strength = float(strength_profile.final_strength)
        else:
            # Fallback trajectory from snapshots
            trajectory = []
            for snap in experiment.snapshots:
                raw_state = snap.get("state_vector") or snap.get("state")
                s_t = np.asarray(raw_state, dtype=np.float64)
                unbound = unbind(s_t, k_target)
                score = float(cosine(unbound, v_target))
                trajectory.append(max(-1.0, min(1.0, score)))
            current_strength = trajectory[-1] if trajectory else 0.5

        total_steps = len(experiment.snapshots) if experiment.snapshots else len(trajectory)

        # 1. Associations (Key Cosine Similarity)
        associations: List[AssociationEntry] = []
        for other in memories:
            if other["memory_id"] == target_id:
                continue
            sim = float(cosine(k_target, other["key_vector"]))
            associations.append(
                AssociationEntry(
                    target_memory=other["memory_id"],
                    concept_label=other["concept_label"],
                    similarity=round(sim, 4),
                )
            )
        associations.sort(key=lambda a: a.similarity, reverse=True)

        # 2. Competitors (Interference & high key overlap)
        competitors: List[CompetitorEntry] = []
        interferences = detect_interference(experiment)
        interf_mems = set()
        for rec in interferences:
            if getattr(rec, "memory_a", None) == target_id:
                interf_mems.add(getattr(rec, "memory_b", ""))
            elif getattr(rec, "memory_b", None) == target_id:
                interf_mems.add(getattr(rec, "memory_a", ""))

        for other in memories:
            if other["memory_id"] == target_id:
                continue
            sim = float(cosine(k_target, other["key_vector"]))
            if sim > 0.15 or other["memory_id"] in interf_mems:
                overlap = sim if sim > 0 else 0.1
                competitors.append(
                    CompetitorEntry(
                        target_memory=other["memory_id"],
                        concept_label=other["concept_label"],
                        similarity=round(sim, 4),
                        overlap_score=round(overlap, 4),
                    )
                )
        competitors.sort(key=lambda c: c.overlap_score, reverse=True)

        # 3. Reinforcement History
        reinforcement_history: List[ReinforcementRecord] = []
        formation_events: List[str] = [origin_event]
        if len(trajectory) > 1:
            for step_idx in range(1, len(trajectory)):
                delta = trajectory[step_idx] - trajectory[step_idx - 1]
                if delta > 0.03:
                    ev_id = (
                        experiment.events[step_idx - 1].get("id")
                        if step_idx - 1 < len(experiment.events)
                        else f"e{step_idx:04d}"
                    )
                    reinforcement_history.append(
                        ReinforcementRecord(
                            step=step_idx,
                            event_id=ev_id,
                            strength_before=round(trajectory[step_idx - 1], 4),
                            strength_after=round(trajectory[step_idx], 4),
                            delta=round(delta, 4),
                        )
                    )
                    if ev_id not in formation_events:
                        formation_events.append(ev_id)

        # 4. Retrieval History
        retrieval_history: List[RetrievalRecord] = []
        for idx, ev in enumerate(experiment.events):
            if ev.get("type") in ("query", "recall") or ev.get("concept_label") == target_concept:
                step = int(ev.get("timestep", idx))
                fid = trajectory[step] if step < len(trajectory) else current_strength
                retrieval_history.append(
                    RetrievalRecord(
                        step=step,
                        event_id=ev.get("id", f"e{idx:04d}"),
                        fidelity=round(fid, 4),
                        success=fid >= 0.35,
                    )
                )

        # 5. State Dependencies (Memories written prior to target)
        state_dependencies: List[str] = [
            m["memory_id"] for m in memories if m["timestep"] < origin_step
        ]

        # 6. Downstream Influence (Memories written after target)
        downstream_influence: List[str] = [
            m["memory_id"] for m in memories if m["timestep"] > origin_step
        ]

        # 7. Stability & Sensitivity
        if len(trajectory) > 1:
            std_dev = float(np.std(trajectory))
            stability = max(0.0, min(1.0, 1.0 - (std_dev * 2.0)))
        else:
            stability = 0.95

        # Sensitivity: susceptibility to interference and drops
        drop_count = sum(1 for i in range(1, len(trajectory)) if trajectory[i] < trajectory[i - 1] - 0.03)
        sensitivity = max(0.0, min(1.0, (drop_count * 0.25) + (len(competitors) * 0.1)))

        # 8. Influence Score
        # derived transparently from downstream count, associations, and persistence
        downstream_ratio = len(downstream_influence) / max(1, len(memories))
        top_assoc_mean = np.mean([a.similarity for a in associations[:3]]) if associations else 0.0
        influence_score = float(
            max(0.0, min(1.0, 0.4 * downstream_ratio + 0.3 * max(0.0, top_assoc_mean) + 0.3 * current_strength))
        )

        # 9. DNA Strip
        dna_strip = cls._build_dna_strip(
            origin_step=origin_step,
            total_steps=total_steps,
            reinforcement_count=len(reinforcement_history),
            associations=associations,
            competitors=competitors,
            current_strength=current_strength,
            trajectory=trajectory,
            stability=stability,
            influence_score=influence_score,
        )

        dim = 128
        if hasattr(experiment, "task") and isinstance(experiment.task, dict):
            dim = experiment.task.get("d", 128)
        elif hasattr(experiment, "task") and hasattr(experiment.task, "d"):
            dim = getattr(experiment.task, "d", 128)
        elif experiment.parameters and isinstance(experiment.parameters, dict):
            dim = experiment.parameters.get("state_dim", 128)

        provenance = {
            "experiment_id": experiment.experiment_id,
            "dimension": dim,
            "total_memories": len(memories),
            "mechanism": getattr(experiment, "mechanism", "interference"),
            "created_at": getattr(experiment, "created_at", ""),
        }

        return MemoryGenome(
            memory_id=target_id,
            concept_label=target_concept,
            origin_event=origin_event,
            origin_step=origin_step,
            formation_events=formation_events,
            associations=associations,
            competitors=competitors,
            reinforcement_history=reinforcement_history,
            retrieval_history=retrieval_history,
            state_dependencies=state_dependencies,
            downstream_influence=downstream_influence,
            trajectory=[round(float(s), 4) for s in trajectory],
            current_strength=round(current_strength, 4),
            stability=round(stability, 4),
            sensitivity=round(sensitivity, 4),
            influence_score=round(influence_score, 4),
            dna_strip=dna_strip,
            provenance=provenance,
        )

    @classmethod
    def _build_dna_strip(
        cls,
        origin_step: int,
        total_steps: int,
        reinforcement_count: int,
        associations: List[AssociationEntry],
        competitors: List[CompetitorEntry],
        current_strength: float,
        trajectory: List[float],
        stability: float,
        influence_score: float,
    ) -> GenomeDNAStrip:
        """Compute the 8 measurable computational facets comprising the DNA strip."""
        # Origin score: normalized relative step (1.0 = earliest, 0.0 = latest)
        origin_score = max(0.0, min(1.0, 1.0 - (origin_step / max(1, total_steps))))

        # Reinforcement score: ratio of reinforcement opportunities
        reinforce_score = max(0.0, min(1.0, reinforcement_count / 3.0))

        # Association score: top 3 mean similarity
        assoc_score = (
            max(0.0, min(1.0, float(np.mean([a.similarity for a in associations[:3]]))))
            if associations
            else 0.0
        )

        # Competition score: max competitor overlap
        comp_score = (
            max(0.0, min(1.0, competitors[0].overlap_score))
            if competitors
            else 0.0
        )

        # Retrieval score: final readout strength
        retrieval_score = max(0.0, min(1.0, current_strength))

        # Drift score: cumulative trajectory drift
        drift = 0.0
        if len(trajectory) > 1:
            drift = float(sum(abs(trajectory[i] - trajectory[i - 1]) for i in range(1, len(trajectory))))
        drift_score = max(0.0, min(1.0, drift / 2.0))

        stability_score = stability

        evidence = {
            "ORIGIN": f"Formed at step {origin_step} of {total_steps} (score: {origin_score:.2f})",
            "REINFORCEMENT": f"{reinforcement_count} reinforcement write events detected",
            "ASSOCIATION": f"{len(associations)} associated items; top similarity: {assoc_score:.2f}",
            "COMPETITION": f"{len(competitors)} competing items; peak overlap: {comp_score:.2f}",
            "RETRIEVAL": f"Readout fidelity cosine: {retrieval_score:.2f}",
            "DRIFT": f"Cumulative trajectory variation: {drift:.2f}",
            "STABILITY": f"Representation resilience: {stability_score:.2f}",
            "INFLUENCE": f"Downstream state cascade influence: {influence_score:.2f}",
        }

        return GenomeDNAStrip(
            origin_score=round(origin_score, 4),
            reinforcement_score=round(reinforce_score, 4),
            association_score=round(assoc_score, 4),
            competition_score=round(comp_score, 4),
            retrieval_score=round(retrieval_score, 4),
            drift_score=round(drift_score, 4),
            stability_score=round(stability_score, 4),
            influence_score=round(influence_score, 4),
            evidence=evidence,
        )


class LineageBuilder:
    """Constructs the causal lineage directed acyclic graph for a memory."""

    @classmethod
    def build(cls, experiment: Experiment, target_query: str) -> MemoryLineageGraph:
        """Construct the MemoryLineageGraph for the given memory."""
        genome = MemoryGenomeBuilder.build(experiment, target_query)

        nodes: List[MemoryLineageNode] = []
        edges: List[MemoryLineageEdge] = []

        # 1. Origin Event Node
        nodes.append(
            MemoryLineageNode(
                id=f"evt_{genome.origin_event}",
                label=f"EVENT {genome.origin_event}",
                node_type="EVENT",
                step=genome.origin_step,
                details={"event_id": genome.origin_event},
            )
        )

        # 2. Formation Node
        formation_node_id = f"op_form_{genome.memory_id}"
        nodes.append(
            MemoryLineageNode(
                id=formation_node_id,
                label="FORMATION",
                node_type="OPERATION",
                step=genome.origin_step,
                details={"step": genome.origin_step},
            )
        )
        edges.append(
            MemoryLineageEdge(
                source=f"evt_{genome.origin_event}",
                target=formation_node_id,
                label="initiates",
                operation="FORMATION",
            )
        )

        # 3. Target Memory Node
        target_node_id = f"mem_{genome.memory_id}"
        nodes.append(
            MemoryLineageNode(
                id=target_node_id,
                label=f"MEMORY {genome.concept_label}",
                node_type="TARGET_MEMORY",
                step=genome.origin_step,
                details={"strength": genome.current_strength},
            )
        )
        edges.append(
            MemoryLineageEdge(
                source=formation_node_id,
                target=target_node_id,
                label="consolidates",
                operation="CONSOLIDATION",
            )
        )

        # 4. Reinforcement nodes (if any)
        last_anchor = target_node_id
        for r in genome.reinforcement_history[:2]:
            reinf_id = f"op_reinf_{r.step}"
            nodes.append(
                MemoryLineageNode(
                    id=reinf_id,
                    label=f"REINFORCEMENT (+{r.delta:.2f})",
                    node_type="OPERATION",
                    step=r.step,
                    details={"delta": r.delta, "event_id": r.event_id},
                )
            )
            edges.append(
                MemoryLineageEdge(
                    source=last_anchor,
                    target=reinf_id,
                    label=f"step {r.step}",
                    operation="REINFORCEMENT",
                )
            )
            last_anchor = reinf_id

        # 5. Top Associations
        for assoc in genome.associations[:2]:
            assoc_node_id = f"mem_{assoc.target_memory}"
            nodes.append(
                MemoryLineageNode(
                    id=assoc_node_id,
                    label=f"ASSOC {assoc.concept_label}",
                    node_type="ASSOCIATED_MEMORY",
                    step=genome.origin_step,
                    details={"similarity": assoc.similarity},
                )
            )
            edges.append(
                MemoryLineageEdge(
                    source=last_anchor,
                    target=assoc_node_id,
                    label=f"sim {assoc.similarity:.2f}",
                    operation="ASSOCIATION",
                )
            )

        # 6. Downstream retrieval / influence
        for down_id in genome.downstream_influence[:2]:
            down_node_id = f"mem_{down_id}"
            if not any(n.id == down_node_id for n in nodes):
                nodes.append(
                    MemoryLineageNode(
                        id=down_node_id,
                        label=f"DOWNSTREAM {down_id}",
                        node_type="DOWNSTREAM_MEMORY",
                        step=genome.origin_step + 1,
                        details={"memory_id": down_id},
                    )
                )
                edges.append(
                    MemoryLineageEdge(
                        source=last_anchor,
                        target=down_node_id,
                        label="propagates to",
                        operation="PROPAGATION",
                    )
                )

        return MemoryLineageGraph(memory_id=genome.memory_id, nodes=nodes, edges=edges)
