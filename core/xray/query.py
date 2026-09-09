"""Deterministic analytical query engine for Memory X-Ray (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, Optional
from core import Experiment
from .changes import detect_state_changes
from .competition import build_competition_graph
from .decay import analyze_decay_curves
from .event_impact import compute_event_impact
from .explanation import build_memory_explanation
from .interference import detect_interference
from .neighborhood import find_nearest_memories
from .trajectory import get_state_trajectory


def execute_xray_query(
    experiment: Experiment,
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a deterministic analytical query over memory state and history.

    Maps natural scientific questions directly onto verified numerical functions.
    Does NOT invoke an LLM.
    """
    p = params or {}
    q_norm = query.lower().strip()

    # 1. "Why did this memory become weaker?"
    if "why" in q_norm or "weaker" in q_norm or "faded" in q_norm:
        mem_id = p.get("memory_id")
        if not mem_id:
            # Pick the memory with largest drop
            decay_data = analyze_decay_curves(experiment)
            mem_id = decay_data.get("least_persistent_memory")

        if not mem_id:
            return {"error": "No memory specified or found to analyze."}

        expl = build_memory_explanation(experiment, mem_id)
        interf = [ir.to_dict() for ir in detect_interference(experiment) if ir.memory_a == mem_id or ir.memory_b == mem_id]

        return {
            "query_type": "why_memory_weakened",
            "memory_id": mem_id,
            "explanation": expl.to_dict() if expl else None,
            "interference_causes": interf,
            "finding": (
                f"Memory '{mem_id}' was weakened by cross-talk interference from {len(interf)} "
                f"competing memory writes and continuous state superposition degradation."
            ),
        }

    # 2. "Which memories compete with this one?"
    if "compete" in q_norm or "competition" in q_norm:
        mem_id = p.get("memory_id")
        interf_all = detect_interference(experiment)
        if mem_id:
            matching = [ir.to_dict() for ir in interf_all if ir.memory_a == mem_id or ir.memory_b == mem_id]
        else:
            matching = [ir.to_dict() for ir in interf_all]

        return {
            "query_type": "competing_memories",
            "memory_id": mem_id,
            "total_competing_pairs": len(matching),
            "competition_evidence": matching,
        }

    # 3. "What changed after this event?"
    if "what changed" in q_norm or "after event" in q_norm:
        ev_id = p.get("event_id")
        impacts = compute_event_impact(experiment)
        target_impact = next((im for im in impacts if im.event_id == ev_id), impacts[0] if impacts else None)

        return {
            "query_type": "what_changed_after_event",
            "event_id": target_impact.event_id if target_impact else ev_id,
            "impact": target_impact.to_dict() if target_impact else None,
        }

    # 4. "Which event had the largest effect?"
    if "largest effect" in q_norm or "biggest effect" in q_norm or "largest impact" in q_norm:
        impacts = compute_event_impact(experiment)
        if not impacts:
            return {"query_type": "largest_effect_event", "result": None}

        top_event = max(impacts, key=lambda im: im.change_magnitude)
        return {
            "query_type": "largest_effect_event",
            "top_event": top_event.to_dict(),
            "finding": f"Event '{top_event.event_id}' induced the largest state vector shift (magnitude {top_event.change_magnitude:.3f}).",
        }

    # 5. "Where did the memory state change most?"
    if "where" in q_norm and ("change" in q_norm or "transition" in q_norm):
        traj = get_state_trajectory(experiment)
        changes = detect_state_changes(traj)
        top_shift = max(changes["records"], key=lambda r: r["change_magnitude"]) if changes["records"] else None

        return {
            "query_type": "where_state_changed_most",
            "highest_change_step": top_shift,
            "sudden_transitions": changes["sudden_transitions"],
            "high_change_regions": changes["high_change_regions"],
        }

    # 6. "Which memory persisted longest?"
    if "persisted" in q_norm or "persistent" in q_norm or "longest" in q_norm:
        decay_data = analyze_decay_curves(experiment)
        best_id = decay_data.get("most_persistent_memory")
        expl = build_memory_explanation(experiment, best_id) if best_id else None

        return {
            "query_type": "longest_persisting_memory",
            "memory_id": best_id,
            "explanation": expl.to_dict() if expl else None,
            "decay_overview": decay_data,
        }

    # 7. "Which memories are strongly related?"
    if "related" in q_norm or "neighbors" in q_norm or "similar" in q_norm:
        mem_id = p.get("memory_id")
        if mem_id:
            neighbors = find_nearest_memories(experiment, mem_id, k=p.get("k", 5))
            return {
                "query_type": "strongly_related_memories",
                "memory_id": mem_id,
                "neighbors": neighbors,
            }
        else:
            comp_graph = build_competition_graph(experiment)
            strong_edges = [
                e.to_dict() for e in comp_graph.edges
                if e.strength > 0.4
            ]
            return {
                "query_type": "strongly_related_memories",
                "strong_relationships": strong_edges,
            }

    # Fallback default: general state summary
    traj = get_state_trajectory(experiment)
    changes = detect_state_changes(traj)
    return {
        "query_type": "general_inquiry",
        "total_steps": traj.total_steps,
        "mean_change": changes["mean_change_magnitude"],
        "message": "Deterministic query executed; specify parameters for deeper targeted inspection.",
    }
