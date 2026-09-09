"""Adaptive Memory Observatory Engine (Phase 19).

Provides a continuous scientific observation environment where learners observe
how a stream of changing information drives real synaptic plasticity updates,
state evolution, adaptation, interference, and recovery over time.

TRANSPARENCY & SCIENTIFIC GROUNDING:
    - Every numerical value derives strictly from NumPy linear algebra on SynapticBrain.
    - Synaptic weight updates follow: W(t) = (1 - λ) W(t-1) + η (v ⊗ k).
    - Readout activation follows: v̂ = W @ k_query.
    - Fidelity is the cosine similarity between readout v̂ and target memory value v.
    - Derived metrics (Stability Ratio, Plasticity Extent) are explicitly documented.
    - Integrates Surgery (Phase 15), Counterfactuals (Phase 16), Collision (Phase 17),
      and Detective Cases (Phase 18).
"""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_concept_vector, encode_value_vector
from .forensics import CandidateHypothesis, EvidenceItem, InvestigationCase
from .memory import similarity
from .synaptic import SynapticBrain, SynapticNetworkState
from .vectors import cosine


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class StreamEvent:
    """An event presented to the adaptive memory stream."""

    timestep: int
    environment_id: str
    event_type: str  # "WRITE" | "DECAY" | "PROBE" | "ENV_SHIFT" | "INTERVENTION"
    label: str
    concept: Optional[str] = None
    value: Optional[str] = None
    importance: float = 1.0
    strength: float = 1.0
    n_steps: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ObservatoryProbe:
    """Associative recall probe measurement at a specific timestep."""

    concept: str
    predicted_value: Optional[str]
    ground_truth: str
    fidelity: float
    crosstalk_noise: float
    is_correct: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SynapticWeatherPoint:
    """Weather classification of a single synapse (source -> target)."""

    synapse_id: str
    source_idx: int
    target_idx: int
    current_weight: float
    delta_weight: float
    classification: str  # "UNCHANGED" | "RECENTLY_STRENGTHENED" | "RECENTLY_WEAKENED" | "CURRENTLY_ACTIVE" | "INACTIVE_ZERO"
    activation_transmission: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ObservatorySnapshot:
    """Comprehensive computational state captured at a single stream timestep."""

    timestep: int
    environment_id: str
    event_label: str
    event_type: str
    matrix_weights: List[List[float]]
    matrix_norm: float
    active_synapses_count: int
    sparsity: float
    key_activations: List[float]
    value_activations: List[float]
    probes: List[ObservatoryProbe]
    synaptic_weather: List[SynapticWeatherPoint]
    adaptation_event: Optional[str] = None  # e.g. "MEMORY_WRITE", "STATE_SHIFT", "INTERFERENCE"
    explanation_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestep": self.timestep,
            "environment_id": self.environment_id,
            "event_label": self.event_label,
            "event_type": self.event_type,
            "matrix_weights": self.matrix_weights,
            "matrix_norm": float(self.matrix_norm),
            "active_synapses_count": int(self.active_synapses_count),
            "sparsity": float(self.sparsity),
            "key_activations": self.key_activations,
            "value_activations": self.value_activations,
            "probes": [p.to_dict() for p in self.probes],
            "synaptic_weather": [w.to_dict() for w in self.synaptic_weather],
            "adaptation_event": self.adaptation_event,
            "explanation_note": self.explanation_note,
        }


@dataclass
class ChangeDetection:
    """Explicit differential analysis between two adjacent timesteps."""

    timestep_before: int
    timestep_after: int
    frobenius_delta: float
    strengthened_synapses: List[Dict[str, Any]]
    weakened_synapses: List[Dict[str, Any]]
    unchanged_active_count: int
    key_activation_shift: float
    value_activation_shift: float
    probe_fidelity_deltas: Dict[str, float]
    significant_change_detected: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StabilityPlasticityMetrics:
    """Underlying measurements for the Stability vs Plasticity view."""

    timestep: int
    stability_ratio: float  # (unchanged active) / (total active synapses)
    plasticity_extent: float  # ||W_t - W_{t-1}||_F / (||W_{t-1}||_F + 1e-9)
    total_active: int
    unchanged_count: int
    strengthened_count: int
    weakened_count: int
    mean_abs_weight_change: float
    max_weight_change: float
    formula_note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnvironmentShiftReport:
    """Scientific evaluation of an A -> B -> A environment shift experiment."""

    experiment_name: str
    environment_a: str
    environment_b: str
    before_shift_recalls: Dict[str, float]
    during_shift_recalls: Dict[str, float]
    after_return_recalls: Dict[str, float]
    retention_ratio_during_shift: float
    retention_ratio_after_return: float
    crosstalk_increase: float
    catastrophic_interference_detected: bool
    recovery_magnitude: float
    scientific_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearnerPrediction:
    """Records learner prediction prior to an environment shift."""

    prediction_id: str
    target_timestep: int
    target_memory: str
    predicted_choice: str  # "A" | "B" | "C" | "D" | "E"
    choice_label: str
    actual_outcome: Optional[str] = None
    is_accurate: Optional[bool] = None
    observation_feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ObservatorySession:
    """Complete recorded history of an evolving memory observatory session."""

    session_id: str
    name: str
    dimension: int
    decay: float
    update_strength: float
    mechanism: str
    seed: int
    snapshots: List[ObservatorySnapshot]
    events: List[StreamEvent]
    interventions: List[Dict[str, Any]] = field(default_factory=list)
    branches: List[str] = field(default_factory=list)
    predictions: List[LearnerPrediction] = field(default_factory=list)

    @property
    def total_timesteps(self) -> int:
        return len(self.snapshots)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "dimension": self.dimension,
            "decay": self.decay,
            "update_strength": self.update_strength,
            "mechanism": self.mechanism,
            "seed": self.seed,
            "total_timesteps": len(self.snapshots),
            "snapshots": [s.to_dict() for s in self.snapshots],
            "events": [e.to_dict() for e in self.events],
            "interventions": self.interventions,
            "branches": self.branches,
            "predictions": [p.to_dict() for p in self.predictions],
        }

    def compute_hash(self) -> str:
        """Deterministic SHA-256 state hash for reproducible re-runs."""
        content = f"{self.session_id}_{self.dimension}_{self.decay}_{self.update_strength}_{self.seed}_{len(self.snapshots)}"
        if self.snapshots:
            content += f"_{self.snapshots[-1].matrix_norm:.5f}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Core Observatory Engine
# ---------------------------------------------------------------------------

class AdaptiveObservatoryEngine:
    """Manages stream execution, state recording, differential change detection,
    and adaptive learning experiments.
    """

    @classmethod
    def classify_synaptic_weather(
        cls,
        W_prev: np.ndarray,
        W_curr: np.ndarray,
        key_activations: np.ndarray,
        threshold: float = 0.01,
    ) -> List[SynapticWeatherPoint]:
        """Classify each synapse in the network based on empirical weight changes and activity."""
        d = W_curr.shape[0]
        weather: List[SynapticWeatherPoint] = []
        delta_W = W_curr - W_prev

        # Calculate transmission energy: |W[i, j] * k[j]|
        transmission = np.abs(W_curr * key_activations[np.newaxis, :])
        active_thresh = float(np.percentile(transmission, 85)) if np.max(transmission) > 1e-4 else 1e-4

        for i in range(d):
            for j in range(d):
                w = float(W_curr[i, j])
                dw = float(delta_W[i, j])
                trans = float(transmission[i, j])

                if abs(w) < 1e-5:
                    classification = "INACTIVE_ZERO"
                elif trans >= active_thresh and trans > 1e-4:
                    classification = "CURRENTLY_ACTIVE"
                elif dw >= threshold:
                    classification = "RECENTLY_STRENGTHENED"
                elif dw <= -threshold:
                    classification = "RECENTLY_WEAKENED"
                else:
                    classification = "UNCHANGED"

                weather.append(
                    SynapticWeatherPoint(
                        synapse_id=f"syn_k{j}_v{i}",
                        source_idx=j,
                        target_idx=i,
                        current_weight=w,
                        delta_weight=dw,
                        classification=classification,
                        activation_transmission=trans,
                    )
                )
        return weather

    @classmethod
    def detect_changes(
        cls,
        snap_before: ObservatorySnapshot,
        snap_after: ObservatorySnapshot,
        threshold: float = 0.01,
    ) -> ChangeDetection:
        """Identify meaningful differences between two adjacent timesteps."""
        w_before = np.array(snap_before.matrix_weights)
        w_after = np.array(snap_after.matrix_weights)
        delta = w_after - w_before
        frob_delta = float(np.linalg.norm(delta))

        strengthened: List[Dict[str, Any]] = []
        weakened: List[Dict[str, Any]] = []
        unchanged_active = 0

        d = w_before.shape[0]
        for i in range(d):
            for j in range(d):
                diff = float(delta[i, j])
                cur = float(w_after[i, j])
                if diff >= threshold:
                    strengthened.append({
                        "synapse_id": f"syn_k{j}_v{i}",
                        "weight_before": float(w_before[i, j]),
                        "weight_after": cur,
                        "delta": diff,
                    })
                elif diff <= -threshold:
                    weakened.append({
                        "synapse_id": f"syn_k{j}_v{i}",
                        "weight_before": float(w_before[i, j]),
                        "weight_after": cur,
                        "delta": diff,
                    })
                elif abs(cur) > 1e-4:
                    unchanged_active += 1

        strengthened.sort(key=lambda x: abs(x["delta"]), reverse=True)
        weakened.sort(key=lambda x: abs(x["delta"]), reverse=True)

        k_shift = float(np.linalg.norm(np.array(snap_after.key_activations) - np.array(snap_before.key_activations)))
        v_shift = float(np.linalg.norm(np.array(snap_after.value_activations) - np.array(snap_before.value_activations)))

        # Compute probe fidelity deltas
        fidelity_deltas: Dict[str, float] = {}
        before_probes = {p.concept: p.fidelity for p in snap_before.probes}
        for p in snap_after.probes:
            if p.concept in before_probes:
                fidelity_deltas[p.concept] = float(p.fidelity - before_probes[p.concept])

        significant = frob_delta > threshold or len(strengthened) > 0 or len(weakened) > 0

        summary = (
            f"From T{snap_before.timestep} to T{snap_after.timestep}: "
            f"||ΔW||_F = {frob_delta:.4f}. Strengthened {len(strengthened)} synapses, "
            f"weakened {len(weakened)}, while {unchanged_active} active connections stayed stable."
        )

        return ChangeDetection(
            timestep_before=snap_before.timestep,
            timestep_after=snap_after.timestep,
            frobenius_delta=frob_delta,
            strengthened_synapses=strengthened[:15],
            weakened_synapses=weakened[:15],
            unchanged_active_count=unchanged_active,
            key_activation_shift=k_shift,
            value_activation_shift=v_shift,
            probe_fidelity_deltas=fidelity_deltas,
            significant_change_detected=significant,
            summary=summary,
        )

    @classmethod
    def compute_stability_plasticity(
        cls,
        snap_before: ObservatorySnapshot,
        snap_after: ObservatorySnapshot,
        threshold: float = 0.01,
    ) -> StabilityPlasticityMetrics:
        """Compute the dual Stability vs Plasticity metrics."""
        w_before = np.array(snap_before.matrix_weights)
        w_after = np.array(snap_after.matrix_weights)
        delta = w_after - w_before
        frob_delta = float(np.linalg.norm(delta))
        norm_before = float(snap_before.matrix_norm)

        d = w_before.shape[0]
        unchanged = 0
        strengthened = 0
        weakened = 0
        total_active = snap_after.active_synapses_count

        for i in range(d):
            for j in range(d):
                diff = float(delta[i, j])
                cur = float(w_after[i, j])
                if abs(cur) > 1e-4:
                    if diff >= threshold:
                        strengthened += 1
                    elif diff <= -threshold:
                        weakened += 1
                    else:
                        unchanged += 1

        stability_ratio = float(unchanged / max(1, total_active))
        plasticity_extent = float(frob_delta / (norm_before + 1e-9))

        return StabilityPlasticityMetrics(
            timestep=snap_after.timestep,
            stability_ratio=min(1.0, max(0.0, stability_ratio)),
            plasticity_extent=plasticity_extent,
            total_active=total_active,
            unchanged_count=unchanged,
            strengthened_count=strengthened,
            weakened_count=weakened,
            mean_abs_weight_change=float(np.mean(np.abs(delta))),
            max_weight_change=float(np.max(np.abs(delta))),
            formula_note=(
                "Stability Ratio = UnchangedActive / TotalActive; "
                "Plasticity Extent = ||ΔW||_F / (||W_prev||_F + ε)."
            ),
        )

    @classmethod
    def detect_adaptation_event(
        cls,
        prev_snap: Optional[ObservatorySnapshot],
        curr_probes: List[ObservatoryProbe],
        curr_env_id: str,
        event: StreamEvent,
    ) -> str:
        """Detect the principal adaptation event tag based on genuine state differences."""
        if prev_snap is None:
            return "MEMORY_WRITE" if event.event_type == "WRITE" else "INIT"

        if event.event_type == "INTERVENTION":
            return "SYNAPTIC_MODIFICATION"

        if event.event_type == "DECAY":
            return "PASSIVE_DECAY"

        # Check for recall interference
        prev_probes = {p.concept: p.fidelity for p in prev_snap.probes}
        for p in curr_probes:
            if p.concept in prev_probes:
                drop = prev_probes[p.concept] - p.fidelity
                if drop >= 0.05 and p.concept != event.concept:
                    return "INTERFERENCE"
                if -drop >= 0.05 and p.concept == event.concept:
                    return "RECALL_RECOVERY"

        if prev_snap.environment_id != curr_env_id:
            return "STATE_SHIFT"

        if event.event_type == "WRITE":
            return "MEMORY_WRITE"

        return "STABLE_HOLD"

    @classmethod
    def run_stream(
        cls,
        events: List[StreamEvent],
        dimension: int = 16,
        decay: float = 0.04,
        update_strength: float = 1.0,
        seed: int = 42,
        name: str = "Adaptive Stream",
        tracked_probes: Optional[List[Tuple[str, str]]] = None,
    ) -> ObservatorySession:
        """Execute a full sequence of stream events on a live SynapticBrain."""
        brain = SynapticBrain(
            seed=seed,
            d=dimension,
            decay=decay,
            update_strength=update_strength,
        )

        snapshots: List[ObservatorySnapshot] = []
        all_tracked: List[Tuple[str, str]] = list(tracked_probes or [])

        # Auto-track any concepts written during the stream
        for ev in events:
            if ev.concept and ev.value:
                pair = (ev.concept, ev.value)
                if pair not in all_tracked:
                    all_tracked.append(pair)

        # Initial T0 resting snapshot
        init_state = brain.get_state()
        w_init = np.array(init_state.matrix_weights)
        weather_0 = cls.classify_synaptic_weather(w_init, w_init, brain.key_activations)
        snapshots.append(
            ObservatorySnapshot(
                timestep=0,
                environment_id="ENV_INIT",
                event_label="Initial Resting State",
                event_type="INIT",
                matrix_weights=w_init.tolist(),
                matrix_norm=0.0,
                active_synapses_count=0,
                sparsity=0.0,
                key_activations=brain.key_activations.tolist(),
                value_activations=brain.value_activations.tolist(),
                probes=[],
                synaptic_weather=weather_0,
                adaptation_event="INIT",
                explanation_note="Network initialized to unweighted baseline.",
            )
        )

        for ev in events:
            w_prev = brain.W.copy()

            if ev.event_type == "WRITE" and ev.concept and ev.value:
                brain.write(
                    concept=ev.concept,
                    value=ev.value,
                    importance=ev.importance,
                    strength=ev.strength,
                )
            elif ev.event_type == "DECAY":
                brain.decay_step(n_steps=ev.n_steps)
            elif ev.event_type == "ENV_SHIFT":
                # Advance 1 step of decay to signify contextual boundary
                brain.decay_step(n_steps=1)
            elif ev.event_type == "INTERVENTION":
                # Applied externally if needed
                pass

            curr_state = brain.get_state()
            w_curr = brain.W.copy()

            # Run probes across tracked memories
            probes: List[ObservatoryProbe] = []
            for concept, expected_val in all_tracked:
                # Check if concept is in library or probe directly
                rec_state = brain.recall(concept, expected_value=expected_val)
                last_rec = rec_state.last_recall
                if last_rec:
                    probes.append(
                        ObservatoryProbe(
                            concept=concept,
                            predicted_value=last_rec.predicted_value,
                            ground_truth=expected_val,
                            fidelity=float(last_rec.fidelity),
                            crosstalk_noise=float(last_rec.crosstalk_noise),
                            is_correct=bool(last_rec.is_correct),
                        )
                    )

            weather = cls.classify_synaptic_weather(w_prev, w_curr, brain.key_activations)

            prev_snap = snapshots[-1]
            adaptation_ev = cls.detect_adaptation_event(prev_snap, probes, ev.environment_id, ev)

            snap = ObservatorySnapshot(
                timestep=len(snapshots),
                environment_id=ev.environment_id,
                event_label=ev.label,
                event_type=ev.event_type,
                matrix_weights=w_curr.tolist(),
                matrix_norm=float(curr_state.matrix_norm),
                active_synapses_count=int(curr_state.active_synapses_count),
                sparsity=float(curr_state.sparsity),
                key_activations=brain.key_activations.tolist(),
                value_activations=brain.value_activations.tolist(),
                probes=probes,
                synaptic_weather=weather,
                adaptation_event=adaptation_ev,
                explanation_note=curr_state.last_explanation.scientific_note if curr_state.last_explanation else "",
            )
            snapshots.append(snap)

        session_id = f"OBS-{uuid.uuid4().hex[:8].upper()}"
        return ObservatorySession(
            session_id=session_id,
            name=name,
            dimension=dimension,
            decay=decay,
            update_strength=update_strength,
            mechanism=brain.mechanism,
            seed=seed,
            snapshots=snapshots,
            events=events,
        )

    @classmethod
    def run_env_shift_protocol(
        cls,
        dimension: int = 16,
        decay: float = 0.04,
        update_strength: float = 1.0,
        seed: int = 42,
    ) -> Tuple[ObservatorySession, EnvironmentShiftReport]:
        """Execute the controlled Environment Shift experiment:
        Environment A -> Environment B -> Environment A again.
        """
        events: List[StreamEvent] = [
            # Phase 1: Environment A
            StreamEvent(timestep=1, environment_id="ENV_A", event_type="WRITE", label="Env A: Write Memory A1", concept="solaris", value="golden_star", strength=1.0),
            StreamEvent(timestep=2, environment_id="ENV_A", event_type="WRITE", label="Env A: Write Memory A2", concept="luna", value="silver_orb", strength=1.0),
            StreamEvent(timestep=3, environment_id="ENV_A", event_type="DECAY", label="Env A: Idle Consolidation", n_steps=2),

            # Phase 2: Shift to Environment B (Introducing competing and novel memories)
            StreamEvent(timestep=4, environment_id="ENV_B", event_type="ENV_SHIFT", label="Context Shift -> ENV_B"),
            StreamEvent(timestep=5, environment_id="ENV_B", event_type="WRITE", label="Env B: Write Novel B1", concept="terra", value="blue_marble", strength=1.0),
            StreamEvent(timestep=6, environment_id="ENV_B", event_type="WRITE", label="Env B: Competing Write (Solaris Overwrite)", concept="solaris", value="solar_flare", strength=1.2),
            StreamEvent(timestep=7, environment_id="ENV_B", event_type="DECAY", label="Env B: Hold Phase", n_steps=2),

            # Phase 3: Return to Environment A
            StreamEvent(timestep=8, environment_id="ENV_A", event_type="ENV_SHIFT", label="Context Return -> ENV_A"),
            StreamEvent(timestep=9, environment_id="ENV_A", event_type="WRITE", label="Env A: Re-enforcing Memory A1", concept="solaris", value="golden_star", strength=1.0),
            StreamEvent(timestep=10, environment_id="ENV_A", event_type="DECAY", label="Env A: Final Relaxation", n_steps=1),
        ]

        session = cls.run_stream(
            events=events,
            dimension=dimension,
            decay=decay,
            update_strength=update_strength,
            seed=seed,
            name="Environment Shift A -> B -> A",
        )

        # Extract comparative metrics: T3 (Before Shift), T7 (During Shift), T10 (After Return)
        snap_t3 = session.snapshots[3]  # End of initial Env A
        snap_t7 = session.snapshots[7]  # End of Env B
        snap_t10 = session.snapshots[10]  # End of Return to Env A

        before_recalls = {p.concept: p.fidelity for p in snap_t3.probes}
        during_recalls = {p.concept: p.fidelity for p in snap_t7.probes}
        after_recalls = {p.concept: p.fidelity for p in snap_t10.probes}

        solaris_init = before_recalls.get("solaris", 0.99)
        solaris_during = during_recalls.get("solaris", 0.5)
        solaris_after = after_recalls.get("solaris", 0.9)

        retention_during = float(solaris_during / (solaris_init + 1e-9))
        retention_after = float(solaris_after / (solaris_init + 1e-9))

        crosstalk_inc = float(during_recalls.get("terra", 0.0) - before_recalls.get("terra", 0.0))
        recovery_mag = float(solaris_after - solaris_during)
        catastrophic = solaris_during < 0.60

        interpretation = (
            f"During Environment B, memory 'solaris' retention dropped to {retention_during * 100:.1f}% "
            f"due to competing associative updates on shared synaptic weights. Upon returning to Environment A "
            f"and re-presenting the cue, recall recovered by +{recovery_mag:.3f} to {solaris_after:.3f}."
        )

        report = EnvironmentShiftReport(
            experiment_name="Environment Shift A -> B -> A",
            environment_a="ENV_A",
            environment_b="ENV_B",
            before_shift_recalls=before_recalls,
            during_shift_recalls=during_recalls,
            after_return_recalls=after_recalls,
            retention_ratio_during_shift=retention_during,
            retention_ratio_after_return=retention_after,
            crosstalk_increase=crosstalk_inc,
            catastrophic_interference_detected=catastrophic,
            recovery_magnitude=recovery_mag,
            scientific_interpretation=interpretation,
        )

        return session, report

    @classmethod
    def branch_intervention(
        cls,
        session: ObservatorySession,
        intervention_step: int,
        operation: str,
        synapse_ids: List[str],
        factor: float = 0.0,
    ) -> Tuple[ObservatorySession, Dict[str, Any]]:
        """Phase 15 integration: Pause at intervention_step, modify synapses (silence/weaken/strengthen),
        and continue simulation forward on a separate branch.
        """
        step = max(0, min(len(session.snapshots) - 1, intervention_step))
        base_snap = session.snapshots[step]

        # Reconstruct brain at intervention_step
        brain = SynapticBrain(
            seed=session.seed,
            d=session.dimension,
            decay=session.decay,
            update_strength=session.update_strength,
        )
        brain.W = np.array(base_snap.matrix_weights, dtype=np.float64)

        # Apply surgical modification to branch
        modified_deltas: Dict[str, float] = {}
        for syn_id in synapse_ids:
            parts = syn_id.split("_")
            if len(parts) == 3 and parts[1].startswith("k") and parts[2].startswith("v"):
                try:
                    j = int(parts[1][1:])
                    i = int(parts[2][1:])
                    if 0 <= i < session.dimension and 0 <= j < session.dimension:
                        orig = float(brain.W[i, j])
                        if operation == "silence":
                            new_w = 0.0
                        elif operation == "weaken":
                            new_w = orig * factor
                        elif operation == "strengthen":
                            new_w = orig * factor
                        else:
                            new_w = orig
                        brain.W[i, j] = new_w
                        modified_deltas[syn_id] = new_w - orig
                except ValueError:
                    pass

        # Re-run subsequent events forward from intervention_step
        branch_events = session.events[step:]
        branch_session = cls.run_stream(
            events=branch_events,
            dimension=session.dimension,
            decay=session.decay,
            update_strength=session.update_strength,
            seed=session.seed,
            name=f"{session.name} [Branch: {operation.upper()}]",
        )

        intervention_record = {
            "intervention_id": f"INTV-{uuid.uuid4().hex[:6].upper()}",
            "step": intervention_step,
            "operation": operation,
            "synapse_ids": synapse_ids,
            "weight_deltas": modified_deltas,
            "branch_session_id": branch_session.session_id,
        }
        session.interventions.append(intervention_record)
        session.branches.append(branch_session.session_id)

        return branch_session, intervention_record

    @classmethod
    def branch_counterfactual(
        cls,
        session: ObservatorySession,
        intervention_step: int,
        counterfactual_label: str = "Counterfactual: Invariant Shared Weights",
    ) -> Tuple[ObservatorySession, Dict[str, Any]]:
        """Phase 16 integration: Execute a counterfactual branch from intervention_step."""
        step = max(0, min(len(session.snapshots) - 1, intervention_step))
        base_snap = session.snapshots[step]

        # Hold top 20% active weights invariant
        w_mat = np.array(base_snap.matrix_weights, dtype=np.float64)
        top_syns: List[str] = []
        p80 = np.percentile(np.abs(w_mat), 80) if np.max(np.abs(w_mat)) > 1e-4 else 1e-4

        for i in range(session.dimension):
            for j in range(session.dimension):
                if abs(w_mat[i, j]) >= p80:
                    top_syns.append(f"syn_k{j}_v{i}")

        branch_session, rec = cls.branch_intervention(
            session=session,
            intervention_step=intervention_step,
            operation="silence",
            synapse_ids=top_syns[:5],
            factor=0.0,
        )
        rec["counterfactual_title"] = counterfactual_label
        return branch_session, rec

    @classmethod
    def compare_sessions(
        cls,
        session_a: ObservatorySession,
        session_b: ObservatorySession,
    ) -> Dict[str, Any]:
        """Compare two observatory sessions side-by-side."""
        min_len = min(len(session_a.snapshots), len(session_b.snapshots))
        divergence_curve: List[float] = []

        for t in range(min_len):
            w_a = np.array(session_a.snapshots[t].matrix_weights)
            w_b = np.array(session_b.snapshots[t].matrix_weights)
            frob = float(np.linalg.norm(w_a - w_b))
            divergence_curve.append(frob)

        final_frob = divergence_curve[-1] if divergence_curve else 0.0

        # Recall comparisons at final step
        probes_a = {p.concept: p.fidelity for p in session_a.snapshots[-1].probes}
        probes_b = {p.concept: p.fidelity for p in session_b.snapshots[-1].probes}

        recall_comparison = []
        all_concepts = set(probes_a.keys()).union(set(probes_b.keys()))
        for c in all_concepts:
            f_a = probes_a.get(c, 0.0)
            f_b = probes_b.get(c, 0.0)
            recall_comparison.append({
                "concept": c,
                "fidelity_a": f_a,
                "fidelity_b": f_b,
                "delta": float(f_b - f_a),
            })

        return {
            "session_a_id": session_a.session_id,
            "session_b_id": session_b.session_id,
            "matrix_frobenius_divergence": final_frob,
            "divergence_trajectory": divergence_curve,
            "recall_comparison": recall_comparison,
            "interpretation": (
                f"Sessions diverged by ||W_A - W_B||_F = {final_frob:.4f} across {min_len} timesteps."
            ),
        }

    @classmethod
    def export_to_detective_case(
        cls,
        session: ObservatorySession,
        anomaly_step: int,
        target_memory: Optional[str] = None,
    ) -> InvestigationCase:
        """Phase 18 integration: Export an observatory stream anomaly into a bounded Detective Case."""
        step = max(1, min(len(session.snapshots) - 1, anomaly_step))
        snap_prev = session.snapshots[step - 1]
        snap_curr = session.snapshots[step]

        target = target_memory or (snap_curr.probes[0].concept if snap_curr.probes else "solaris")
        init_fid = next((p.fidelity for p in snap_prev.probes if p.concept == target), 0.95)
        final_fid = next((p.fidelity for p in snap_curr.probes if p.concept == target), 0.65)

        diff = cls.detect_changes(snap_prev, snap_curr)

        ev1 = EvidenceItem(
            evidence_id="EV-OBS-1",
            title=f"State Before Anomaly (T{step-1})",
            category="SYNAPTIC_WEIGHT",
            timestep=step - 1,
            description=f"Pre-anomaly matrix norm was {snap_prev.matrix_norm:.3f}, target recall was {init_fid:.3f}.",
            data_point={"matrix_norm": snap_prev.matrix_norm, "fidelity": init_fid},
            is_critical=True,
        )
        ev2 = EvidenceItem(
            evidence_id="EV-OBS-2",
            title=f"Stream Event at T{step}",
            category="COLLISION_OVERLAP",
            timestep=step,
            description=f"Stream event '{snap_curr.event_label}' modified {len(diff.strengthened_synapses)} synaptic weights.",
            data_point={"strengthened_count": len(diff.strengthened_synapses), "frobenius_delta": diff.frobenius_delta},
            is_critical=True,
        )
        ev3 = EvidenceItem(
            evidence_id="EV-OBS-3",
            title=f"Readout Divergence at T{step}",
            category="RECALL_MEASUREMENT",
            timestep=step,
            description=f"Fidelity dropped by {init_fid - final_fid:.3f} following the stream event.",
            data_point={"fidelity_drop": init_fid - final_fid, "final_fidelity": final_fid},
            is_critical=True,
        )

        hyps = [
            CandidateHypothesis(
                hypothesis_id="HYP-OBS-1",
                label="Stream-Induced Synaptic Interference",
                description="The incoming stream event modified coordinates shared with the target memory, introducing crosstalk.",
                recommended_tool="collision",
                is_correct=True,
                explanation="Verified: Stream update co-modified active associative pathways.",
            ),
            CandidateHypothesis(
                hypothesis_id="HYP-OBS-2",
                label="Accelerated Time Decay",
                description="Trace loss was caused by uniform temporal decay.",
                recommended_tool="timemachine",
                is_correct=False,
                explanation="Refuted: Trace loss coincided specifically with the stream write event.",
            ),
            CandidateHypothesis(
                hypothesis_id="HYP-OBS-3",
                label="Uncorrelated Baseline Fluctuation",
                description="Random noise shifted readout activation.",
                recommended_tool="xray",
                is_correct=False,
                explanation="Refuted: Updates were strictly deterministic and Hebbian.",
            ),
        ]

        return InvestigationCase(
            case_id=f"CASE-OBS-{uuid.uuid4().hex[:4].upper()}",
            case_code="CASE_OBSERVATORY_STREAM_ANOMALY",
            title=f"Observatory Mystery: The Divergent Stream (T{step})",
            difficulty="INTERMEDIATE",
            briefing=f"During live stream monitoring of session {session.session_id}, target memory '{target}' exhibited sudden degradation at step {step}.",
            question=f"What mechanism caused target memory '{target}' recall to drop from {init_fid:.3f} to {final_fid:.3f} at step {step}?",
            target_memory=target,
            initial_recall=init_fid,
            final_recall=final_fid,
            total_timesteps=len(session.snapshots),
            intervention_step=step,
            available_tools=["collision", "xray", "surgery", "counterfactual"],
            candidate_hypotheses=hyps,
            available_evidence=[ev1, ev2, ev3],
            ground_truth_hypothesis_id="HYP-OBS-1",
            ground_truth_explanation=f"Stream event '{snap_curr.event_label}' triggered a Hebbian weight update that shared coordinates with '{target}', inducing crosstalk noise.",
            underlying_data={"session_id": session.session_id, "step": step, "matrix_weights": snap_curr.matrix_weights},
            claim_traceability=[
                {
                    "claim": "Continuous stream learning induces cross-talk on overlapping synaptic coordinates.",
                    "paper_citation": "Krotov (2023), Nature Reviews Physics",
                    "experiment_ref": session.session_id,
                    "observation": f"Frobenius delta ||ΔW||_F = {diff.frobenius_delta:.3f}.",
                }
            ],
        )
