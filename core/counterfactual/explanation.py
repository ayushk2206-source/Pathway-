"""Deterministic natural language explanations for counterfactual divergence (Phase 04)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .divergence import DivergenceProfile
from .interventions import Intervention


def generate_counterfactual_explanation(
    intervention: Intervention,
    divergence: DivergenceProfile,
    original_metrics: Dict[str, Any],
    counterfactual_metrics: Dict[str, Any],
    target_event_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a deterministic, scientifically safe explanation from measured simulation data."""
    itype = intervention.intervention_type.value
    target = intervention.target_event_id or f"timestep {intervention.target_timestep}"
    if target_event_summary:
        c = target_event_summary.get("concept") or target_event_summary.get("concept_label")
        v = target_event_summary.get("value") or target_event_summary.get("attribute_label")
        if c and v:
            target += f" ({c}={v})"

    # Narrative explanation parts
    parts = []

    # 1. State divergence onset
    first_step = divergence.first_divergence_step
    if first_step is not None:
        ev_label = f"event '{divergence.first_divergence_event_id}'" if divergence.first_divergence_event_id else f"timestep {first_step}"
        parts.append(
            f"Applying {itype.replace('_', ' ')} on {target} produced an observed trajectory divergence "
            f"starting at {ev_label} (initial state distance L2={divergence.timeline[first_step].state_distance_l2:.4f})."
        )
    else:
        parts.append(f"Applying {itype.replace('_', ' ')} on {target} produced no measurable divergence across the observed horizon.")

    # 2. Propagation shape
    parts.append(
        f"The divergence exhibited a {divergence.classification.value} propagation pattern "
        f"(confidence {divergence.classification_confidence:.2f}): {divergence.classification_rationale}"
    )

    # 3. Final state & metric shifts
    ret_orig = original_metrics.get("memory_retention")
    ret_cf = counterfactual_metrics.get("memory_retention")
    inter_orig = original_metrics.get("interference_score")
    inter_cf = counterfactual_metrics.get("interference_score")
    acc_orig = original_metrics.get("recall_accuracy")
    acc_cf = counterfactual_metrics.get("recall_accuracy")

    metric_summaries = []
    if ret_orig is not None and ret_cf is not None:
        d_ret = float(ret_cf - ret_orig)
        metric_summaries.append(f"retention shifted by {d_ret:+.4f} (from {ret_orig:.4f} to {ret_cf:.4f})")

    if inter_orig is not None and inter_cf is not None:
        d_inter = float(inter_cf - inter_orig)
        metric_summaries.append(f"interference shifted by {d_inter:+.4f} (from {inter_orig:.4f} to {inter_cf:.4f})")

    if acc_orig is not None and acc_cf is not None:
        d_acc = float(acc_cf - acc_orig)
        metric_summaries.append(f"accuracy shifted by {d_acc:+.4f} (from {acc_orig:.4f} to {acc_cf:.4f})")

    if metric_summaries:
        parts.append(f"At the final state, simulated intervention effects included: {'; '.join(metric_summaries)}.")

    # 4. Memory impact summary
    num_aff = len(divergence.affected_memories)
    num_unaff = len(divergence.unaffected_memories)
    parts.append(
        f"In total, {num_aff} memory queries were altered by the counterfactual branch, "
        f"while {num_unaff} memories remained invariant."
    )

    # 5. Causal safety note
    parts.append(
        "Note: These measurements represent simulated intervention effects within the discrete mathematical "
        "memory model, holding all secondary parameters invariant."
    )

    full_narrative = " ".join(parts)

    return {
        "summary": parts[0],
        "detailed_narrative": full_narrative,
        "first_divergence_onset": f"timestep {first_step}" if first_step is not None else "none",
        "divergence_pattern": divergence.classification.value,
        "affected_memory_count": num_aff,
        "unaffected_memory_count": num_unaff,
        "final_state_distance": divergence.final_state_distance_l2,
        "final_cosine_similarity": divergence.final_cosine_similarity,
    }
