"""Divergence calculation, propagation analysis, and classification (Phase 04)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.experiment import Experiment
from core.vectors import cosine
from .types import DivergenceClassification


def _sanitize(val: Any) -> Any:
    if isinstance(val, (np.floating, float)):
        return float(val) if not np.isnan(val) else None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, dict):
        return {k: _sanitize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize(v) for v in val]
    return val


@dataclass
class DivergenceStep:
    """State distance and divergence metrics at one point in time."""

    step: int
    event_id: Optional[str]
    state_distance_l2: float
    cosine_similarity: float
    relative_l2: float
    metric_delta: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "event_id": self.event_id,
            "state_distance_l2": float(self.state_distance_l2),
            "cosine_similarity": float(self.cosine_similarity),
            "relative_l2": float(self.relative_l2),
            "metric_delta": _sanitize(self.metric_delta),
        }


@dataclass
class DivergenceProfile:
    """Complete temporal divergence profile between original and counterfactual histories."""

    first_divergence_step: Optional[int]
    first_divergence_event_id: Optional[str]
    final_state_distance_l2: float
    final_cosine_similarity: float
    final_relative_l2: float
    cumulative_divergence: float
    max_divergence_step: int
    max_divergence_l2: float
    classification: DivergenceClassification
    classification_confidence: float
    classification_rationale: str
    affected_memories: List[Dict[str, Any]] = field(default_factory=list)
    unaffected_memories: List[str] = field(default_factory=list)
    timeline: List[DivergenceStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_divergence_step": self.first_divergence_step,
            "first_divergence_event_id": self.first_divergence_event_id,
            "final_state_distance_l2": float(self.final_state_distance_l2),
            "final_cosine_similarity": float(self.final_cosine_similarity),
            "final_relative_l2": float(self.final_relative_l2),
            "cumulative_divergence": float(self.cumulative_divergence),
            "max_divergence_step": int(self.max_divergence_step),
            "max_divergence_l2": float(self.max_divergence_l2),
            "classification": self.classification.value if isinstance(self.classification, DivergenceClassification) else str(self.classification),
            "classification_confidence": float(self.classification_confidence),
            "classification_rationale": self.classification_rationale,
            "affected_memories": _sanitize(self.affected_memories),
            "unaffected_memories": list(self.unaffected_memories),
            "timeline": [t.to_dict() for t in self.timeline],
        }


def classify_divergence(
    distances: List[float],
    cosines: List[float],
    affected_count: int,
    total_memories: int,
    first_step: Optional[int],
    intervention_step: Optional[int],
) -> Tuple[DivergenceClassification, float, str]:
    """Classify the empirical shape of divergence propagation from measured metrics."""
    if not distances:
        return (
            DivergenceClassification.LOCALIZED,
            0.5,
            "No distance measurements recorded.",
        )

    arr = np.asarray(distances, dtype=np.float64)
    max_d = float(np.max(arr))
    final_d = float(arr[-1])
    n = len(arr)

    # 1. Zero or negligible divergence
    if max_d < 1e-6:
        return (
            DivergenceClassification.CONVERGENT,
            0.95,
            "Counterfactual trajectory remained identical within numerical tolerance.",
        )

    # 2. Transient (diverged then returned to near-zero)
    if final_d < 1e-4 and max_d > 0.05:
        return (
            DivergenceClassification.TRANSIENT,
            0.9,
            f"Divergence surged to {max_d:.3f} but decayed back to zero ({final_d:.4f}) before the end of the history.",
        )

    # 3. Convergent (cosine similarity returns near 1.0)
    if cosines and cosines[-1] > 0.99 and min(cosines) < 0.90:
        return (
            DivergenceClassification.CONVERGENT,
            0.88,
            f"Original and counterfactual state directions reconverged (final cosine={cosines[-1]:.4f}).",
        )

    # 4. Delayed (intervention happened at t_int, but divergence didn't emerge until later)
    if intervention_step is not None and first_step is not None and (first_step - intervention_step) >= 2:
        return (
            DivergenceClassification.DELAYED,
            0.85,
            f"Intervention at step {intervention_step} produced no immediate difference; divergence surfaced at step {first_step}.",
        )

    # 5. Damped (peak reached, then monotonic or steady attenuation)
    peak_idx = int(np.argmax(arr))
    if 0 < peak_idx < n - 1 and final_d < 0.5 * max_d:
        return (
            DivergenceClassification.DAMPED,
            0.85,
            f"Divergence peaked at step {peak_idx} ({max_d:.3f}) and was subsequently damped to {final_d:.3f}.",
        )

    # 6. Oscillating (multiple fluctuations in trajectory)
    diffs = np.diff(arr)
    sign_changes = np.count_nonzero(np.diff(np.sign(diffs[np.abs(diffs) > 1e-5])) != 0)
    if sign_changes >= 3:
        return (
            DivergenceClassification.OSCILLATING,
            0.8,
            f"State distance oscillated ({sign_changes} inflection points) across subsequent writes.",
        )

    # 7. Explosive (super-linear exponential acceleration downstream)
    if len(arr) >= 4 and first_step is not None:
        sub = arr[first_step:]
        if len(sub) >= 4 and sub[-1] > 4.0 * sub[0] and np.all(np.diff(sub) >= -1e-5):
            diffs = np.diff(sub)
            if np.all(diffs[1:] > 1.5 * diffs[:-1]) and np.mean(np.diff(diffs)) > 0.1:
                return (
                    DivergenceClassification.EXPLOSIVE,
                    0.85,
                    f"Divergence accelerated exponentially downstream (initial delta={sub[0]:.3f} -> final={sub[-1]:.3f}).",
                )

    # 8. Cumulative (strictly non-decreasing from first divergence)
    if first_step is not None and first_step < n - 1:
        tail = arr[first_step:]
        if np.all(np.diff(tail) >= -1e-5) and tail[-1] > tail[0]:
            return (
                DivergenceClassification.CUMULATIVE,
                0.9,
                f"Divergence accumulated monotonically across subsequent writes (final distance={final_d:.3f}).",
            )

    # 9. Immediate (jumps to peak value immediately at intervention and stays relatively constant)
    if first_step is not None and first_step == intervention_step:
        tail = arr[first_step:]
        if len(tail) >= 2 and np.var(tail) < 0.01:
            return (
                DivergenceClassification.IMMEDIATE,
                0.85,
                f"State divergence appeared immediately at intervention step {first_step} and remained stable.",
            )

    # 10. Localized vs Global
    if total_memories > 0:
        if affected_count <= 1 and (affected_count / total_memories) < 0.3:
            return (
                DivergenceClassification.LOCALIZED,
                0.8,
                f"Divergence was localized to {affected_count}/{total_memories} memories; overall memory manifold remained stable.",
            )
        if (affected_count / total_memories) >= 0.7:
            return (
                DivergenceClassification.GLOBAL,
                0.85,
                f"Intervention globally disrupted memory retention ({affected_count}/{total_memories} memories altered).",
            )

    # Fallback: Persistent
    return (
        DivergenceClassification.PERSISTENT,
        0.75,
        f"Divergence persisted through the final timestep with distance={final_d:.3f}.",
    )


def compute_divergence_profile(
    original_exp: Experiment,
    counterfactual_exp: Experiment,
    intervention_step: Optional[int] = None,
) -> DivergenceProfile:
    """Compute step-by-step state divergence and classify its temporal propagation."""
    orig_snaps = original_exp.snapshots
    cf_snaps = counterfactual_exp.snapshots

    max_steps = min(len(orig_snaps), len(cf_snaps))
    timeline: List[DivergenceStep] = []
    distances: List[float] = []
    cosines: List[float] = []

    first_step: Optional[int] = None
    first_event_id: Optional[str] = None
    max_d = -1.0
    max_step = 0
    cum_d = 0.0

    for t in range(max_steps):
        s_orig = np.asarray(orig_snaps[t].get("state_vector", []), dtype=np.float64).reshape(-1)
        s_cf = np.asarray(cf_snaps[t].get("state_vector", []), dtype=np.float64).reshape(-1)

        if s_orig.size != s_cf.size or s_orig.size == 0:
            d_l2 = 0.0
            cos_val = 1.0
            rel_l2 = 0.0
        else:
            diff = s_cf - s_orig
            d_l2 = float(np.linalg.norm(diff))
            norm_orig = float(np.linalg.norm(s_orig))
            norm_cf = float(np.linalg.norm(s_cf))
            if norm_orig < 1e-12 and norm_cf < 1e-12:
                cos_val = 1.0
            else:
                cos_val = float(cosine(s_orig, s_cf))
            rel_l2 = float(d_l2 / (norm_orig + 1e-12))

        distances.append(d_l2)
        cosines.append(cos_val)
        cum_d += d_l2

        ev_id = cf_snaps[t].get("event_id") or orig_snaps[t].get("event_id")

        if d_l2 > 1e-9 and first_step is None:
            first_step = t
            first_event_id = ev_id

        if d_l2 > max_d:
            max_d = d_l2
            max_step = t

        step_metric_delta: Dict[str, float] = {}
        # If query results exist on this snapshot
        q_orig = orig_snaps[t].get("query_results", [])
        q_cf = cf_snaps[t].get("query_results", [])
        if q_orig and q_cf:
            q_acc_o = np.mean([1.0 if q.get("correctness") else 0.0 for q in q_orig])
            q_acc_c = np.mean([1.0 if q.get("correctness") else 0.0 for q in q_cf])
            step_metric_delta["recall_accuracy_delta"] = float(q_acc_c - q_acc_o)

        timeline.append(
            DivergenceStep(
                step=t,
                event_id=ev_id,
                state_distance_l2=d_l2,
                cosine_similarity=cos_val,
                relative_l2=rel_l2,
                metric_delta=step_metric_delta,
            )
        )

    final_d = distances[-1] if distances else 0.0
    final_cos = cosines[-1] if cosines else 1.0
    final_rel = timeline[-1].relative_l2 if timeline else 0.0

    # Analyze affected vs unaffected memories
    orig_queries = {q.get("object_label"): q for q in original_exp.queries}
    cf_queries = {q.get("object_label"): q for q in counterfactual_exp.queries}
    all_objects = sorted(set(orig_queries.keys()) | set(cf_queries.keys()))

    affected: List[Dict[str, Any]] = []
    unaffected: List[str] = []

    for obj in all_objects:
        qo = orig_queries.get(obj)
        qc = cf_queries.get(obj)
        if not qo or not qc:
            affected.append({
                "object_label": obj,
                "status": "query_missing_in_one_timeline",
                "outcome_changed": True,
            })
            continue

        q_diff = abs(float(qo.get("quality", 0.0)) - float(qc.get("quality", 0.0)))
        pred_changed = qo.get("predicted_label") != qc.get("predicted_label")
        correctness_changed = qo.get("correctness") != qc.get("correctness")

        if q_diff > 1e-5 or pred_changed or correctness_changed:
            affected.append({
                "object_label": obj,
                "original_predicted": qo.get("predicted_label"),
                "counterfactual_predicted": qc.get("predicted_label"),
                "truth_label": qo.get("truth_label"),
                "original_correctness": bool(qo.get("correctness")),
                "counterfactual_correctness": bool(qc.get("correctness")),
                "original_quality": float(qo.get("quality", 0.0)),
                "counterfactual_quality": float(qc.get("quality", 0.0)),
                "quality_delta": float(qc.get("quality", 0.0) - qo.get("quality", 0.0)),
                "outcome_changed": bool(pred_changed or correctness_changed),
            })
        else:
            unaffected.append(obj)

    classification, confidence, rationale = classify_divergence(
        distances=distances,
        cosines=cosines,
        affected_count=len(affected),
        total_memories=len(all_objects),
        first_step=first_step,
        intervention_step=intervention_step,
    )

    return DivergenceProfile(
        first_divergence_step=first_step,
        first_divergence_event_id=first_event_id,
        final_state_distance_l2=final_d,
        final_cosine_similarity=final_cos,
        final_relative_l2=final_rel,
        cumulative_divergence=cum_d,
        max_divergence_step=max_step,
        max_divergence_l2=max_d if max_d >= 0 else 0.0,
        classification=classification,
        classification_confidence=confidence,
        classification_rationale=rationale,
        affected_memories=affected,
        unaffected_memories=unaffected,
        timeline=timeline,
    )
