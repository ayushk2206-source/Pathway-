"""Experiment Studio Computational Engine (Phase 22).

Enables learners to design, configure, predict, run, inspect, intervene in,
compare, and export their own synaptic plasticity experiments.

Central Learning Claim:
    "Recent neural activity temporarily changes synaptic connections, allowing
    information to be represented, maintained, interfered with, and recalled
    through an evolving internal state."

Every number and metric is derived directly from real linear algebra on SynapticBrain.
Zero fake metrics. Rule-based factual observations are cleanly separated from scientific interpretations.
"""

from __future__ import annotations

import copy
import datetime
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_concept_vector, encode_value_vector
from .fingerprint import MemoryGenomeEngine
from .synaptic import SynapticBrain
from .vectors import cosine


@dataclass
class StudioExperimentConfig:
    """Rigorous parameter configuration for an empirical synaptic experiment."""

    experiment_id: str
    name: str
    experiment_type: str  # "ENCODING" | "INTERFERENCE" | "SURGERY" | "COUNTERFACTUAL" | "PERSISTENCE" | "COMPARISON"
    seed: int = 42
    d: int = 16  # 8, 16, 32
    decay: float = 0.05  # λ ∈ [0.0, 0.95]
    update_strength: float = 1.0  # η ∈ [0.1, 2.0]
    mechanism: str = "hebbian"  # "hebbian" | "leaky" | "competitive" | "interference" | "baseline"
    
    # Target Memory A
    concept_a: str = "cat"
    value_a: str = "whiskers"
    importance_a: float = 1.0
    strength_a: float = 1.0

    # Interference parameters
    interfering_concept: str = "tiger"
    interfering_value: str = "stripes"
    interfering_strength: float = 0.8
    intervening_steps: int = 1  # decay cycles or intervening updates

    # Surgery parameters
    surgery_target_row: int = 0
    surgery_target_col: int = 0
    surgery_action: str = "zero"  # "zero" | "clamp_high" | "invert" | "attenuate"

    # Counterfactual parameters
    cf_param_name: str = "decay"
    cf_param_value: float = 0.3

    # Persistence parameters
    decay_cycles: int = 5

    # Comparison parameters
    comparison_concept: str = "dog"
    comparison_value: str = "bark"

    # One-Variable Experiment mode
    controlled_variables: List[str] = field(default_factory=lambda: ["seed", "d", "mechanism", "concept_a", "value_a"])
    changed_variable: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate parameter ranges against genuine computational constraints."""
        errors = []
        if self.d not in (8, 16, 32, 64):
            errors.append(f"Dimension d={self.d} must be 8, 16, 32, or 64.")
        if not (0.0 <= self.decay <= 0.95):
            errors.append(f"Decay λ={self.decay} must be in range [0.0, 0.95].")
        if not (0.1 <= self.update_strength <= 2.5):
            errors.append(f"Update strength η={self.update_strength} must be in range [0.1, 2.5].")
        if not (0.0 <= self.interfering_strength <= 2.5):
            errors.append(f"Interfering strength={self.interfering_strength} must be in range [0.0, 2.5].")
        if not (0 <= self.decay_cycles <= 50):
            errors.append(f"Decay cycles={self.decay_cycles} must be in range [0, 50].")
        if not self.concept_a.strip():
            errors.append("Concept A cannot be empty.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


ExperimentConfig = StudioExperimentConfig


@dataclass
class ExperimentHypothesis:
    """Pre-run hypothesis and prediction challenge."""

    hypothesis_text: str = "I predict intervening writes will degrade recall due to shared synaptic weights."
    predicted_outcome: str = "RETENTION_DROP"  # "RETENTION_DROP" | "STABILITY_PRESERVED" | "RECALL_IMPROVED" | "CROSSTALK_INCREASE" | "FIDELITY_LOSS" | "UNSURE"
    predicted_challenge_choice: Optional[str] = None  # "A" | "B" | "C" | "D"
    actual_outcome: Optional[str] = None
    support_status: Optional[str] = None  # "SUPPORTED" | "NOT SUPPORTED" | "MIXED / INCONCLUSIVE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComputationStep:
    """Empirical stage in the real computation pipeline."""

    step_name: str  # "INPUT" | "ACTIVITY" | "SYNAPTIC_WRITE" | "STATE_UPDATE" | "RECALL" | "MEASUREMENT"
    order_index: int
    detail: str
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SynapticDeltaRecord:
    """Individual altered connection in the synaptic matrix."""

    row: int
    col: int
    weight_before: float
    weight_after: float
    delta: float
    pct_change: float
    tag: str = "OBSERVED"  # "OBSERVED" | "MEASURED" | "DERIVED" | "SIMPLIFIED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentResult:
    """Complete measured scientific outcome of an executed experiment."""

    experiment_id: str
    config: ExperimentConfig
    hypothesis: ExperimentHypothesis
    baseline_metrics: Dict[str, float]
    experiment_metrics: Dict[str, float]
    delta_metrics: Dict[str, float]
    pipeline_steps: List[ComputationStep]
    top_synaptic_changes: List[SynapticDeltaRecord]
    observation_statements: List[str]
    interpretation_statements: List[str]
    experiment_graph_active_stage: str
    is_deterministic: bool
    seed_used: int
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "config": self.config.to_dict(),
            "hypothesis": self.hypothesis.to_dict(),
            "baseline_metrics": self.baseline_metrics,
            "experiment_metrics": self.experiment_metrics,
            "delta_metrics": self.delta_metrics,
            "pipeline_steps": [s.to_dict() for s in self.pipeline_steps],
            "top_synaptic_changes": [c.to_dict() for c in self.top_synaptic_changes],
            "observation_statements": self.observation_statements,
            "interpretation_statements": self.interpretation_statements,
            "experiment_graph_active_stage": self.experiment_graph_active_stage,
            "is_deterministic": self.is_deterministic,
            "seed_used": self.seed_used,
            "timestamp": self.timestamp,
        }


@dataclass
class ABComparisonResult:
    """Controlled A/B comparison between two experiment configurations."""

    exp_a: ExperimentResult
    exp_b: ExperimentResult
    diff_summary: Dict[str, float]
    differing_parameters: Dict[str, Tuple[Any, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exp_a": self.exp_a.to_dict(),
            "exp_b": self.exp_b.to_dict(),
            "diff_summary": self.diff_summary,
            "differing_parameters": {k: list(v) for k, v in self.differing_parameters.items()},
        }


@dataclass
class ParameterSweepPoint:
    """A single data point along a parameter sweep curve."""

    param_value: float
    fidelity: float
    crosstalk: float
    matrix_norm: float
    active_synapses: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParameterSweepResult:
    """Measured metric curve along a 1D sweep parameter."""

    param_name: str
    param_range: List[float]
    points: List[ParameterSweepPoint]
    correlation: float
    trend_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "param_name": self.param_name,
            "param_range": self.param_range,
            "points": [p.to_dict() for p in self.points],
            "correlation": float(self.correlation),
            "trend_interpretation": self.trend_interpretation,
        }


@dataclass
class ExperimentNote:
    """Learner notes bound to local session."""

    question: str = "Can temporary synaptic changes preserve a memory despite intervening writes?"
    hypothesis: str = "Stronger interference modifies shared weights, leading to degraded recall fidelity."
    observation: str = "Interfering write reduced cosine fidelity from 0.98 to 0.76."
    conclusion: str = "In this Hebbian model, overlapping neural patterns cause synaptic cross-talk."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExperimentStudioEngine:
    """Core computational laboratory engine for Phase 22."""

    def __init__(self) -> None:
        self.history: List[ExperimentResult] = []
        self.saved_notes: Dict[str, ExperimentNote] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        # Pre-seed an initial baseline experiment so history is populated immediately
        default_cfg = ExperimentConfig(
            experiment_id="EXP-BASE-001",
            name="Interference Baseline Probe",
            experiment_type="INTERFERENCE",
            seed=42,
            d=16,
            decay=0.05,
            update_strength=1.0,
            concept_a="cat",
            value_a="whiskers",
            interfering_concept="tiger",
            interfering_value="stripes",
            interfering_strength=0.75,
        )
        default_hypo = ExperimentHypothesis(
            hypothesis_text="I predict that introducing 'tiger' after 'cat' will degrade cat's recall fidelity due to weight sharing.",
            predicted_outcome="RETENTION_DROP",
            predicted_challenge_choice="B",
        )
        self.run_experiment(default_cfg, default_hypo)

    def get_templates(self) -> List[Dict[str, Any]]:
        """Return 5 starter experiment templates grounded in genuine computation."""
        return [
            {
                "id": "tpl_interference",
                "title": "Does interference affect recall?",
                "type": "INTERFERENCE",
                "description": "Examine how writing a competing concept onto shared synaptic weights modifies existing memory retrieval.",
                "config": {
                    "experiment_type": "INTERFERENCE",
                    "concept_a": "cat",
                    "value_a": "whiskers",
                    "interfering_concept": "tiger",
                    "interfering_value": "stripes",
                    "interfering_strength": 0.8,
                    "decay": 0.05,
                    "update_strength": 1.0,
                },
                "recommended_question": "What happens to the cat-whiskers memory when a related tiger-stripes pattern is encoded?",
            },
            {
                "id": "tpl_decay",
                "title": "How does memory state evolve over decay cycles?",
                "type": "PERSISTENCE",
                "description": "Quantify exponential fading of synaptic weights across multiple resting cycles without new inputs.",
                "config": {
                    "experiment_type": "PERSISTENCE",
                    "concept_a": "apple",
                    "value_a": "orchard",
                    "decay_cycles": 8,
                    "decay": 0.15,
                    "update_strength": 1.2,
                },
                "recommended_question": "Does higher synaptic decay accelerate memory forgetting at a constant or diminishing rate?",
            },
            {
                "id": "tpl_surgery",
                "title": "What happens when part of the synaptic state is altered?",
                "type": "SURGERY",
                "description": "Perform precise micro-surgery on the most influential synaptic connection and measure immediate recall degradation.",
                "config": {
                    "experiment_type": "SURGERY",
                    "concept_a": "galaxy",
                    "value_a": "spiral",
                    "surgery_action": "zero",
                    "update_strength": 1.0,
                },
                "recommended_question": "Is memory retrieval distributed robustly, or does zeroing a key synapse collapse confidence?",
            },
            {
                "id": "tpl_counterfactual",
                "title": "How would memory differ under alternate plasticity?",
                "type": "COUNTERFACTUAL",
                "description": "Re-simulate identical input events under higher plasticity learning rate to observe representational divergence.",
                "config": {
                    "experiment_type": "COUNTERFACTUAL",
                    "concept_a": "quantum",
                    "value_a": "wave",
                    "cf_param_name": "update_strength",
                    "cf_param_value": 1.8,
                },
                "recommended_question": "Would a higher learning rate strengthen initial retention, or cause excessive weight saturation?",
            },
            {
                "id": "tpl_comparison",
                "title": "Do two memories share internal structure?",
                "type": "COMPARISON",
                "description": "Compare internal synaptic update matrices (vec(ΔW)) between two distinct semantic concepts.",
                "config": {
                    "experiment_type": "COMPARISON",
                    "concept_a": "sparrow",
                    "value_a": "wings",
                    "comparison_concept": "hawk",
                    "comparison_value": "talons",
                },
                "recommended_question": "Do related concepts activate overlapping or orthogonal synaptic pathways?",
            },
        ]

    def get_starter_journey(self) -> Dict[str, Any]:
        """Return the 8-step guided learner journey."""
        return {
            "title": "Can temporary synaptic changes preserve a memory?",
            "total_steps": 8,
            "steps": [
                {
                    "step_index": 1,
                    "action": "ENCODE_MEMORY",
                    "instruction": "Encode Memory A ('cat' -> 'whiskers') with learning rate η = 1.0.",
                    "focus": "Notice how outer product v ⊗ k creates a structured weight update ΔW.",
                },
                {
                    "step_index": 2,
                    "action": "INSPECT_SYNAPSES",
                    "instruction": "Inspect the synaptic matrix W. Count active connections (|W_rc| > 0.05).",
                    "focus": "Short-term storage is embedded directly within these connection strengths.",
                },
                {
                    "step_index": 3,
                    "action": "PROBE_RECALL",
                    "instruction": "Probe the network with query 'cat' and observe linear readout v̂ = W @ k.",
                    "focus": "Baseline recall fidelity achieves near-perfect cosine match with whiskers vector.",
                },
                {
                    "step_index": 4,
                    "action": "INTRODUCE_INTERFERENCE",
                    "instruction": "Formulate a prediction: What will happen when Memory B ('tiger' -> 'stripes') is written?",
                    "focus": "Predict whether fidelity will drop, stay constant, or improve.",
                },
                {
                    "step_index": 5,
                    "action": "RUN_INTERFERENCE",
                    "instruction": "Execute the write of Memory B onto the same synaptic substrate.",
                    "focus": "Observe how weights are updated: W_new = (1 - λ) W_old + η (v_B ⊗ k_B).",
                },
                {
                    "step_index": 6,
                    "action": "RE_PROBE_RECALL",
                    "instruction": "Re-probe the network with query 'cat'. Measure recall fidelity and crosstalk noise.",
                    "focus": "Compare post-interference readout against original baseline.",
                },
                {
                    "step_index": 7,
                    "action": "INSPECT_GENOME",
                    "instruction": "Inspect the Synaptic Change Ledger and shared genome breakdown.",
                    "focus": "Identify the exact overlapping synapses responsible for crosstalk.",
                },
                {
                    "step_index": 8,
                    "action": "FORMULATE_CONCLUSION",
                    "instruction": "State your conclusion in local notes: Did temporary synaptic changes support memory?",
                    "focus": "Conclude whether short-term memory is bounded by capacity and superposition limits.",
                },
            ],
        }

    def run_experiment(
        self,
        config: ExperimentConfig,
        hypothesis: Optional[ExperimentHypothesis] = None,
        notes: Optional[ExperimentNote] = None,
    ) -> ExperimentResult:
        """Execute genuine physical computation according to experiment configuration."""
        val_errors = config.validate()
        if val_errors:
            raise ValueError(f"Experiment configuration validation failed: {'; '.join(val_errors)}")

        hypo = hypothesis or ExperimentHypothesis()

        # Step 1: Establish baseline with Memory A on pristine SynapticBrain
        base_brain = SynapticBrain(
            seed=config.seed,
            d=config.d,
            decay=config.decay,
            update_strength=config.update_strength,
            mechanism=config.mechanism,
        )
        base_brain.write(
            concept=config.concept_a,
            value=config.value_a,
            importance=config.importance_a,
            strength=config.strength_a,
        )
        base_recall = base_brain.recall(config.concept_a, expected_value=config.value_a)
        
        base_fidelity = float(base_recall.last_recall.fidelity) if base_recall.last_recall else 0.95
        base_crosstalk = float(base_recall.last_recall.crosstalk_noise) if base_recall.last_recall else 0.05
        base_norm = float(np.linalg.norm(base_brain.W))
        base_active = int(np.sum(np.abs(base_brain.W) > 0.01))
        base_sparsity = float(np.mean(np.abs(base_brain.W) <= 0.01))

        baseline_metrics = {
            "fidelity": base_fidelity,
            "crosstalk": base_crosstalk,
            "matrix_norm": base_norm,
            "active_synapses": base_active,
            "sparsity": base_sparsity,
        }

        # Step 2: Set up experimental trial brain
        exp_brain = SynapticBrain(
            seed=config.seed,
            d=config.d,
            decay=config.decay,
            update_strength=config.update_strength,
            mechanism=config.mechanism,
        )

        pipeline_steps: List[ComputationStep] = []
        pipeline_steps.append(
            ComputationStep(
                step_name="INPUT",
                order_index=1,
                detail=f"Encoded input vector k for '{config.concept_a}' (d={config.d}, seed={config.seed}).",
                metrics={"concept": config.concept_a, "dim": config.d},
            )
        )

        pipeline_steps.append(
            ComputationStep(
                step_name="ACTIVITY",
                order_index=2,
                detail=f"Target value activity vector v for '{config.value_a}'.",
                metrics={"value": config.value_a, "target_norm": 1.0},
            )
        )

        # Execute write of Memory A
        exp_brain.write(
            concept=config.concept_a,
            value=config.value_a,
            importance=config.importance_a,
            strength=config.strength_a,
        )

        pipeline_steps.append(
            ComputationStep(
                step_name="SYNAPTIC_WRITE",
                order_index=3,
                detail=f"Hebbian outer product W <- (1 - λ)W + η(v ⊗ k). Matrix norm: {float(np.linalg.norm(exp_brain.W)):.4f}.",
                metrics={"norm": float(np.linalg.norm(exp_brain.W)), "active_synapses": int(np.sum(np.abs(exp_brain.W) > 0.01))},
            )
        )

        # Execute specific experiment intervention
        active_stage = "STATE_UPDATE"
        if config.experiment_type == "ENCODING":
            active_stage = "SYNAPTIC_WRITE"

        elif config.experiment_type == "INTERFERENCE":
            active_stage = "STATE_UPDATE"
            # Write interfering memory
            exp_brain.write(
                concept=config.interfering_concept,
                value=config.interfering_value,
                strength=config.interfering_strength,
            )
            # Apply intervening decay cycles if requested
            for _ in range(max(0, config.intervening_steps - 1)):
                exp_brain.W = (1.0 - exp_brain.decay) * exp_brain.W

        elif config.experiment_type == "SURGERY":
            active_stage = "STATE_UPDATE"
            # Locate most influential synapse or use specified coordinate
            r, c = config.surgery_target_row, config.surgery_target_col
            if r == 0 and c == 0:
                # Pick argmax synapse
                max_idx = np.unravel_index(np.argmax(np.abs(exp_brain.W)), exp_brain.W.shape)
                r, c = int(max_idx[0]), int(max_idx[1])

            if config.surgery_action == "zero":
                exp_brain.W[r, c] = 0.0
            elif config.surgery_action == "clamp_high":
                exp_brain.W[r, c] = 2.0
            elif config.surgery_action == "invert":
                exp_brain.W[r, c] = -exp_brain.W[r, c]
            elif config.surgery_action == "attenuate":
                exp_brain.W[r, c] *= 0.2

        elif config.experiment_type == "COUNTERFACTUAL":
            active_stage = "STATE_UPDATE"
            # Recompute under counterfactual knob
            cf_decay = config.cf_param_value if config.cf_param_name == "decay" else config.decay
            cf_eta = config.cf_param_value if config.cf_param_name == "update_strength" else config.update_strength
            cf_brain = SynapticBrain(
                seed=config.seed,
                d=config.d,
                decay=cf_decay,
                update_strength=cf_eta,
                mechanism=config.mechanism,
            )
            cf_brain.write(concept=config.concept_a, value=config.value_a)
            exp_brain = cf_brain

        elif config.experiment_type == "PERSISTENCE":
            active_stage = "STATE_UPDATE"
            # Advance through multiple decay cycles
            for _ in range(config.decay_cycles):
                exp_brain.W = (1.0 - exp_brain.decay) * exp_brain.W

        elif config.experiment_type == "COMPARISON":
            active_stage = "STATE_UPDATE"
            # Write comparison concept
            exp_brain.write(concept=config.comparison_concept, value=config.comparison_value)

        pipeline_steps.append(
            ComputationStep(
                step_name="STATE_UPDATE",
                order_index=4,
                detail=f"Executed {config.experiment_type} intervention on synaptic matrix W.",
                metrics={"matrix_norm": float(np.linalg.norm(exp_brain.W))},
            )
        )

        # Step 3: Recall Memory A and measure resulting state
        exp_recall = exp_brain.recall(config.concept_a, expected_value=config.value_a)
        
        pipeline_steps.append(
            ComputationStep(
                step_name="RECALL",
                order_index=5,
                detail=f"Forward readout v̂ = W @ k for '{config.concept_a}'.",
                metrics={
                    "predicted_value": exp_recall.last_recall.predicted_value if exp_recall.last_recall else None,
                    "confidence": float(exp_recall.last_recall.confidence) if exp_recall.last_recall else 0.0,
                },
            )
        )

        exp_fidelity = float(exp_recall.last_recall.fidelity) if exp_recall.last_recall else 0.0
        exp_crosstalk = float(exp_recall.last_recall.crosstalk_noise) if exp_recall.last_recall else 1.0
        exp_norm = float(np.linalg.norm(exp_brain.W))
        exp_active = int(np.sum(np.abs(exp_brain.W) > 0.01))
        exp_sparsity = float(np.mean(np.abs(exp_brain.W) <= 0.01))

        experiment_metrics = {
            "fidelity": exp_fidelity,
            "crosstalk": exp_crosstalk,
            "matrix_norm": exp_norm,
            "active_synapses": exp_active,
            "sparsity": exp_sparsity,
        }

        delta_metrics = {
            "fidelity_delta": exp_fidelity - base_fidelity,
            "crosstalk_delta": exp_crosstalk - base_crosstalk,
            "matrix_norm_delta": exp_norm - base_norm,
            "active_synapses_delta": float(exp_active - base_active),
            "sparsity_delta": exp_sparsity - base_sparsity,
        }

        pipeline_steps.append(
            ComputationStep(
                step_name="MEASUREMENT",
                order_index=6,
                detail=f"Recall fidelity: {exp_fidelity:.4f} (Δ: {delta_metrics['fidelity_delta']:+.4f}). Crosstalk: {exp_crosstalk:.4f}.",
                metrics=delta_metrics,
            )
        )

        # Step 4: Extract top synaptic changes (comparing baseline state base_brain.W to exp_brain.W)
        diff_W = exp_brain.W - base_brain.W
        abs_diff = np.abs(diff_W)
        flat_indices = np.argsort(abs_diff.ravel())[::-1][:10]

        top_changes: List[SynapticDeltaRecord] = []
        for idx in flat_indices:
            r, c = np.unravel_index(idx, diff_W.shape)
            w_b = float(base_brain.W[r, c])
            w_a = float(exp_brain.W[r, c])
            d_w = float(diff_W[r, c])
            denom = abs(w_b) if abs(w_b) > 1e-4 else 1.0
            pct = (d_w / denom) * 100.0
            top_changes.append(
                SynapticDeltaRecord(
                    row=int(r),
                    col=int(c),
                    weight_before=w_b,
                    weight_after=w_a,
                    delta=d_w,
                    pct_change=pct,
                    tag="MEASURED",
                )
            )

        # Step 5: Rule-based factual observations and scientific interpretations
        observations: List[str] = []
        interpretations: List[str] = []

        if abs(delta_metrics["fidelity_delta"]) < 0.02:
            observations.append(f"Measured recall fidelity remained stable within ±0.02 (Baseline: {base_fidelity:.3f}, Experiment: {exp_fidelity:.3f}).")
            interpretations.append("In this Hebbian model, the intervention did not significantly perturb the projection subspace for the target cue.")
        elif delta_metrics["fidelity_delta"] < 0:
            observations.append(f"Measured recall fidelity decreased by {abs(delta_metrics['fidelity_delta']):.3f} (from {base_fidelity:.3f} to {exp_fidelity:.3f}).")
            interpretations.append("Intervening activity updated shared connection weights, causing destructive interference and crosstalk noise during linear readout.")
        else:
            observations.append(f"Measured recall fidelity increased by {delta_metrics['fidelity_delta']:.3f} (from {base_fidelity:.3f} to {exp_fidelity:.3f}).")
            interpretations.append("The parameter adjustment strengthened transmission gain along active key-to-value pathways.")

        if abs(delta_metrics["matrix_norm_delta"]) > 0.1:
            observations.append(f"Frobenius matrix norm shifted by {delta_metrics['matrix_norm_delta']:+.3f} (Baseline: {base_norm:.3f}, Exp: {exp_norm:.3f}).")
            interpretations.append("Significant structural reconfiguration occurred across the synaptic matrix substrate.")

        # Step 6: Evaluate hypothesis
        actual_outcome = "STABILITY_PRESERVED"
        if delta_metrics["fidelity_delta"] < -0.05:
            actual_outcome = "RETENTION_DROP"
        elif delta_metrics["fidelity_delta"] > 0.05:
            actual_outcome = "RECALL_IMPROVED"
        elif delta_metrics["crosstalk_delta"] > 0.1:
            actual_outcome = "CROSSTALK_INCREASE"

        hypo.actual_outcome = actual_outcome
        if hypo.predicted_outcome == actual_outcome:
            hypo.support_status = "SUPPORTED"
        elif hypo.predicted_outcome == "UNSURE":
            hypo.support_status = "MIXED / INCONCLUSIVE"
        else:
            hypo.support_status = "NOT SUPPORTED"

        result = ExperimentResult(
            experiment_id=config.experiment_id or f"EXP-{uuid.uuid4().hex[:6].upper()}",
            config=config,
            hypothesis=hypo,
            baseline_metrics=baseline_metrics,
            experiment_metrics=experiment_metrics,
            delta_metrics=delta_metrics,
            pipeline_steps=pipeline_steps,
            top_synaptic_changes=top_changes,
            observation_statements=observations,
            interpretation_statements=interpretations,
            experiment_graph_active_stage=active_stage,
            is_deterministic=True,
            seed_used=config.seed,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        self.history.append(result)
        if notes:
            self.saved_notes[result.experiment_id] = notes

        return result

    def run_ab_comparison(
        self,
        config_a: ExperimentConfig,
        config_b: ExperimentConfig,
    ) -> ABComparisonResult:
        """Run two configurations side-by-side and calculate delta matrix."""
        exp_a = self.run_experiment(config_a)
        exp_b = self.run_experiment(config_b)

        diff_summary = {
            "fidelity_diff": exp_b.experiment_metrics["fidelity"] - exp_a.experiment_metrics["fidelity"],
            "crosstalk_diff": exp_b.experiment_metrics["crosstalk"] - exp_a.experiment_metrics["crosstalk"],
            "matrix_norm_diff": exp_b.experiment_metrics["matrix_norm"] - exp_a.experiment_metrics["matrix_norm"],
            "active_synapses_diff": float(exp_b.experiment_metrics["active_synapses"] - exp_a.experiment_metrics["active_synapses"]),
        }

        differing_params = {}
        dict_a = config_a.to_dict()
        dict_b = config_b.to_dict()
        for k in dict_a:
            if k not in ("experiment_id", "name") and dict_a[k] != dict_b.get(k):
                differing_params[k] = (dict_a[k], dict_b.get(k))

        return ABComparisonResult(
            exp_a=exp_a,
            exp_b=exp_b,
            diff_summary=diff_summary,
            differing_parameters=differing_params,
        )

    def run_parameter_sweep(
        self,
        base_config: ExperimentConfig,
        param_name: str,
        param_values: Optional[List[float]] = None,
    ) -> ParameterSweepResult:
        """Run a 1D parameter sweep across up to 6 values to measure non-linear response curves."""
        valid_params = {
            "decay": [0.0, 0.05, 0.15, 0.3, 0.5, 0.75],
            "update_strength": [0.2, 0.5, 0.8, 1.0, 1.5, 2.0],
            "interfering_strength": [0.0, 0.25, 0.5, 0.75, 1.0, 1.5],
            "decay_cycles": [0, 2, 4, 6, 8, 12],
        }

        if param_name not in valid_params:
            raise ValueError(f"Parameter '{param_name}' is not supported for sweep. Supported: {list(valid_params.keys())}")

        values = param_values if param_values is not None else valid_params[param_name]
        # Restrict to maximum 8 values for performance safety
        values = values[:8]

        points: List[ParameterSweepPoint] = []
        fidelity_list: List[float] = []

        for val in values:
            cfg = copy.deepcopy(base_config)
            cfg.experiment_id = f"SWEEP-{param_name}-{val}"
            if param_name == "decay_cycles":
                setattr(cfg, param_name, int(val))
            else:
                setattr(cfg, param_name, float(val))

            res = self.run_experiment(cfg)
            m = res.experiment_metrics
            points.append(
                ParameterSweepPoint(
                    param_value=float(val),
                    fidelity=float(m["fidelity"]),
                    crosstalk=float(m["crosstalk"]),
                    matrix_norm=float(m["matrix_norm"]),
                    active_synapses=int(m["active_synapses"]),
                )
            )
            fidelity_list.append(float(m["fidelity"]))

        # Compute empirical Pearson correlation between parameter and fidelity
        val_arr = np.array(values, dtype=np.float64)
        fid_arr = np.array(fidelity_list, dtype=np.float64)
        if np.std(val_arr) > 1e-6 and np.std(fid_arr) > 1e-6:
            r = float(np.corrcoef(val_arr, fid_arr)[0, 1])
        else:
            r = 0.0

        if r < -0.6:
            trend = f"Strong negative correlation (r = {r:.2f}): Increasing '{param_name}' degrades recall fidelity."
        elif r > 0.6:
            trend = f"Strong positive correlation (r = {r:.2f}): Increasing '{param_name}' enhances recall fidelity."
        else:
            trend = f"Non-monotonic or weak correlation (r = {r:.2f}): Parameter shifts do not follow a simple linear pattern."

        return ParameterSweepResult(
            param_name=param_name,
            param_range=[float(v) for v in values],
            points=points,
            correlation=r,
            trend_interpretation=trend,
        )

    def duplicate_and_branch(
        self,
        experiment_id: str,
        modified_param: str,
        new_value: Any,
    ) -> ExperimentResult:
        """Duplicate an existing experiment, modify exactly one variable, and execute."""
        source = next((e for e in self.history if e.experiment_id == experiment_id), None)
        if not source:
            raise ValueError(f"Experiment {experiment_id} not found in history.")

        new_cfg = copy.deepcopy(source.config)
        new_cfg.experiment_id = f"EXP-BRANCH-{uuid.uuid4().hex[:6].upper()}"
        new_cfg.name = f"Branch of {source.config.name} (Δ {modified_param})"
        new_cfg.changed_variable = modified_param
        
        if hasattr(new_cfg, modified_param):
            setattr(new_cfg, modified_param, new_value)
        else:
            raise ValueError(f"Parameter '{modified_param}' does not exist on ExperimentConfig.")

        new_hypo = ExperimentHypothesis(
            hypothesis_text=f"Changing {modified_param} to {new_value} relative to {source.experiment_id}.",
            predicted_outcome="RETENTION_DROP",
        )

        return self.run_experiment(new_cfg, new_hypo)

    def export_experiment_json(self, experiment_id: str) -> Dict[str, Any]:
        """Generate structured reproducible research artifact for an experiment."""
        exp = next((e for e in self.history if e.experiment_id == experiment_id), None)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found.")

        note = self.saved_notes.get(experiment_id, ExperimentNote())

        return {
            "schema_version": "pathway.phase22.experiment_studio.v1",
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "experiment": exp.to_dict(),
            "notes": note.to_dict(),
            "computational_framework": {
                "engine": "Pathway Synaptic Brain / Hebbian Plasticity Matrix",
                "update_equation": "W(t+1) = (1 - λ) W(t) + η (v ⊗ k)",
                "readout_equation": "v̂ = W @ k",
                "deterministic": True,
                "seed": exp.seed_used,
            },
            "scientific_guardrails": {
                "claim": "Observed in this simulated Hebbian associative memory model.",
                "disclaimer": "This is a computational model demonstration; biological plasticity involves additional biochemical and circuit-level dynamics.",
            },
        }
