"""Statistical state anomaly detection (Phase 05)."""

from __future__ import annotations

from typing import List
import numpy as np

from core import Experiment
from .changes import detect_state_changes
from .interference import detect_interference
from .models import AnomalyRecord
from .strength import _extract_memory_cues, compute_memory_strengths
from .trajectory import get_state_trajectory
from .types import AnomalyType


def detect_state_anomalies(experiment: Experiment) -> List[AnomalyRecord]:
    """Detect statistically unusual state transitions using empirical mathematical thresholds."""
    anomalies: List[AnomalyRecord] = []
    traj = get_state_trajectory(experiment)
    changes = detect_state_changes(traj)
    strengths_map = compute_memory_strengths(experiment)
    memories = _extract_memory_cues(experiment)
    snapshots = experiment.snapshots

    # 1. State Jumps: outliers in consecutive change magnitude
    change_records = changes.get("records", [])
    if len(change_records) >= 3:
        mags = [r["change_magnitude"] for r in change_records]
        mean_mag = float(np.mean(mags))
        std_mag = float(np.std(mags))

        for r in change_records:
            if std_mag > 1e-6:
                z = (r["change_magnitude"] - mean_mag) / std_mag
                if z > 2.0 or r["change_magnitude"] > 1.4:
                    anomalies.append(
                        AnomalyRecord(
                            step=r["step"],
                            anomaly_type=AnomalyType.STATE_JUMP,
                            metric="change_magnitude",
                            expected_value=mean_mag,
                            observed_value=r["change_magnitude"],
                            deviation_z_score=float(z),
                            evidence=(
                                f"Observed state change magnitude {r['change_magnitude']:.3f} exceeds "
                                f"baseline mean {mean_mag:.3f} by {z:.2f} standard deviations."
                            ),
                        )
                    )

    # 2. Activation Collapse: sudden drop in active unit count
    active_counts = [int(np.sum(np.abs(np.asarray(v, dtype=np.float64)) > 1e-9)) for v in traj.state_vectors]
    for i in range(1, len(active_counts)):
        prev_cnt = active_counts[i - 1]
        curr_cnt = active_counts[i]
        if prev_cnt >= 10 and curr_cnt < 0.4 * prev_cnt:
            drop_ratio = float((prev_cnt - curr_cnt) / prev_cnt)
            anomalies.append(
                AnomalyRecord(
                    step=traj.steps[i],
                    anomaly_type=AnomalyType.ACTIVATION_COLLAPSE,
                    metric="active_units",
                    expected_value=float(prev_cnt),
                    observed_value=float(curr_cnt),
                    deviation_z_score=drop_ratio * 3.0,
                    evidence=(
                        f"Active unit count collapsed by {drop_ratio*100:.1f}% "
                        f"(from {prev_cnt} to {curr_cnt}) at step {traj.steps[i]}."
                    ),
                )
            )

    # 3. Unexpected Memory Strengthening without associated write
    for mem in memories:
        m_id = mem["memory_id"]
        c_label = mem["concept_label"]
        prof = strengths_map.get(m_id)
        if not prof:
            continue

        for s_idx in range(1, len(prof.timeline_strengths)):
            s_prev = prof.timeline_strengths[s_idx - 1]
            s_curr = prof.timeline_strengths[s_idx]
            gain = s_curr - s_prev

            # Check if this step was caused by an unrelated write
            ev_idx = s_idx - 1
            ev = experiment.events[ev_idx] if ev_idx < len(experiment.events) else {}
            is_same_concept = (ev.get("concept_label") == c_label)

            if gain > 0.15 and not is_same_concept:
                anomalies.append(
                    AnomalyRecord(
                        step=s_idx,
                        anomaly_type=AnomalyType.UNEXPECTED_STRENGTHENING,
                        metric="memory_strength",
                        expected_value=s_prev,
                        observed_value=s_curr,
                        deviation_z_score=float(gain / 0.05),
                        evidence=(
                            f"Memory '{c_label}' strengthened by +{gain:.3f} without direct reinforcement "
                            f"at step {s_idx} during write of '{ev.get('concept_label')}'."
                        ),
                    )
                )

    # 4. Severe High Interference Outliers
    interf_list = detect_interference(experiment)
    for ir in interf_list:
        if ir.interference_score > 0.4:
            anomalies.append(
                AnomalyRecord(
                    step=ir.affected_steps[0] if ir.affected_steps else 1,
                    anomaly_type=AnomalyType.HIGH_INTERFERENCE,
                    metric="interference_score",
                    expected_value=0.15,
                    observed_value=ir.interference_score,
                    deviation_z_score=float(ir.interference_score / 0.15),
                    evidence=ir.evidence_notes,
                )
            )

    return anomalies
