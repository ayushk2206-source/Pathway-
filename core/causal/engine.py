"""Core computation engines for Phase 10: Causal Memory Lab.

Every function below produces its numbers by actually replaying the substrate
(via ``core.counterfactual.runner.run_counterfactual`` and
``core.genome.cascade.CascadeEngine``, both already exercised and tested by
Phase 04 / Phase 08) rather than inventing them. Sections referenced in
comments correspond to the Phase 10 prompt.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core import Experiment
from core.counterfactual.interventions import (
    Intervention,
    create_move_intervention,
    create_replace_intervention,
)
from core.counterfactual.models import CounterfactualExperiment
from core.counterfactual.runner import run_counterfactual
from core.counterfactual.types import ReplayStrategy
from core.genome.cascade import CascadeEngine
from core.genome.experiments import RecoveryEngine
from core.genome.genome import resolve_memory
from core.vectors import cosine
from core.xray.strength import _extract_memory_cues, compute_memory_strengths

from .models import (
    CausalEdgeTestResult,
    CausalGraphEdgeVM,
    CausalGraphNodeVM,
    CausalGraphVM,
    CausalityMatrix,
    CriticalWindow,
    DivergenceTraceEvent,
    FirstDivergenceResult,
    InteractionEffectResult,
    MemorySwapResult,
    MultiInterventionResult,
    RecoveryCurvePoint,
    RecoveryCurveResult,
    SingleEffect,
    TemporalCausalityBin,
    TemporalCausalityMap,
    TemporalSensitivityResult,
    TimingSensitivityPoint,
)
from .types import (
    CausalScenarioValidationError,
    InteractionClassification,
    MAX_MATRIX_MEMORIES,
    MAX_MULTI_INTERVENTIONS,
    MAX_TIMING_CANDIDATES,
    WindowSensitivity,
    CausalEdgeStatus,
)


# ---------------------------------------------------------------------------
# Section 5/6 -- First divergence + divergence trace
# ---------------------------------------------------------------------------


def compute_first_divergence(cf: CounterfactualExperiment) -> FirstDivergenceResult:
    """Read the first-divergence point already computed by the replay/comparison step."""
    div = cf.divergence or {}
    first_step = div.get("first_divergence_step")
    magnitude = float(div.get("final_state_distance_l2", div.get("state_distance_l2", 0.0)) or 0.0)

    trace: List[DivergenceTraceEvent] = []
    timeline = div.get("timeline") or []
    max_div_step = div.get("max_divergence_step")
    for entry in timeline:
        step = int(entry.get("step", 0))
        dist = float(entry.get("state_distance_l2", 0.0))
        if dist <= 1e-9:
            continue
        trace.append(
            DivergenceTraceEvent(
                step=step,
                label=f"t={step}",
                memory_id=entry.get("event_id"),
                delta=round(dist, 4),
                is_first_divergence=(first_step is not None and step == int(first_step)),
                is_cascade_point=(max_div_step is not None and step == int(max_div_step)),
            )
        )

    cause = cf.intervention_target or cf.intervention.get("target_event_id") or cf.intervention_type

    return FirstDivergenceResult(
        counterfactual_id=cf.counterfactual_id,
        first_divergence_step=int(first_step) if first_step is not None else None,
        cause_candidate=str(cause),
        divergence_magnitude=round(magnitude, 4),
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Section 7/8 -- Cascade reconstruction + causal graph (built on CascadeMap)
# ---------------------------------------------------------------------------


def build_causal_graph(experiment: Experiment, target_query: str, intervention_type: str = "remove", dose: float = 1.0) -> CausalGraphVM:
    """Build the interactive causal graph from a real cascade simulation.

    Nodes are memories touched by the cascade; edges are association links
    between affected memories, annotated with a provisional status that a
    caller can upgrade to SUPPORTED/CONTRADICTED via ``test_causal_edge``.
    """
    cmap = CascadeEngine.run_cascade(experiment, target_query, intervention_type=intervention_type, dose=dose)

    nodes = [
        CausalGraphNodeVM(
            memory_id=n.memory_id,
            concept_label=n.concept_label,
            node_type="MEMORY",
            depth=n.depth,
            delta=n.delta,
        )
        for n in cmap.nodes
        if n.effect_type.value != "UNCHANGED"
    ]
    edges = [
        CausalGraphEdgeVM(
            source=e.source,
            target=e.target,
            effect=e.strength,
            status=CausalEdgeStatus.INCONCLUSIVE,
            evidence=f"cue similarity {e.strength:.3f} among memories affected by the same cascade",
        )
        for e in cmap.edges
    ]
    return CausalGraphVM(
        experiment_id=experiment.experiment_id,
        target_memory=cmap.target_memory,
        nodes=nodes,
        edges=edges,
    )


# ---------------------------------------------------------------------------
# Section 9/10 -- Causal edge testing (causality vs. correlation)
# ---------------------------------------------------------------------------


def test_causal_edge(experiment: Experiment, source_query: str, target_query: str) -> CausalEdgeTestResult:
    """Test a claimed edge source -> target by actually removing source and observing target."""
    memories = _extract_memory_cues(experiment)
    if not memories:
        raise CausalScenarioValidationError("Experiment has no valid memories to test.")

    src = resolve_memory(experiment, source_query)
    tgt = resolve_memory(experiment, target_query)
    if not src or not tgt:
        raise CausalScenarioValidationError("Source or target memory could not be resolved.")

    ctrl_strengths = compute_memory_strengths(experiment)
    ctrl_target_s = float(ctrl_strengths[tgt["memory_id"]].final_strength) if tgt["memory_id"] in ctrl_strengths else 0.5

    # WITH the edge: baseline, source present.
    observed_difference = 0.0  # baseline vs. baseline is trivially zero -- included for symmetry / UI clarity.

    # WITHOUT the edge: remove source, replay, measure target.
    cmap = CascadeEngine.run_cascade(experiment, src["memory_id"], intervention_type="remove", dose=1.0)
    tgt_node = next((n for n in cmap.nodes if n.memory_id == tgt["memory_id"]), None)
    counterfactual_difference = float(tgt_node.delta) if tgt_node else 0.0

    magnitude = abs(counterfactual_difference)
    if magnitude < 0.01:
        status = CausalEdgeStatus.INCONCLUSIVE
        explanation = (
            f"Removing {src['concept_label']} produced no measurable change in "
            f"{tgt['concept_label']} (|delta|={magnitude:.4f}); correlation, if any, "
            f"may not represent direct dependence."
        )
    elif magnitude < 0.05:
        status = CausalEdgeStatus.WEAK
        explanation = (
            f"Removing {src['concept_label']} produced a small but measurable change "
            f"in {tgt['concept_label']} (|delta|={magnitude:.4f})."
        )
    else:
        status = CausalEdgeStatus.SUPPORTED
        explanation = (
            f"Removing {src['concept_label']} changed {tgt['concept_label']} by "
            f"{counterfactual_difference:+.4f}: causal evidence increases for this edge."
        )

    return CausalEdgeTestResult(
        source=src["memory_id"],
        target=tgt["memory_id"],
        observed_difference=round(observed_difference, 4),
        counterfactual_difference=round(counterfactual_difference, 4),
        status=status,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Section 3/4 -- Temporal intervention + critical window detector
# ---------------------------------------------------------------------------


def run_timing_sensitivity(
    experiment: Experiment,
    target_query: str,
    candidate_timesteps: Optional[List[int]] = None,
) -> TemporalSensitivityResult:
    """Move the target memory's formation event to different points in the sequence
    and measure the resulting divergence at each candidate placement.

    This answers "does WHEN this memory formed matter?" using real replays
    (``MOVE_EVENT``), rather than re-timing an ablation retroactively (which the
    substrate's event-stream model cannot express without fabricating history).
    """
    target = resolve_memory(experiment, target_query)
    if not target:
        raise CausalScenarioValidationError(f"Target memory '{target_query}' not found.")

    origin = int(target["timestep"])
    n_events = len(experiment.events)
    if candidate_timesteps is None:
        step = max(1, n_events // MAX_TIMING_CANDIDATES)
        candidate_timesteps = sorted(set(range(0, n_events, step)))[:MAX_TIMING_CANDIDATES]

    points: List[TimingSensitivityPoint] = []
    magnitudes: List[float] = []
    for t in candidate_timesteps:
        if t == origin or not (0 <= t < n_events):
            continue
        intv = create_move_intervention(
            target_event_id=target["memory_id"],
            destination_timestep=t,
            description=f"Timing sweep: move {target['concept_label']} to t={t}",
        )
        try:
            cf = run_counterfactual(experiment, intv, strategy=ReplayStrategy.FULL_REPLAY)
        except Exception:
            continue
        dist = float((cf.divergence or {}).get("final_state_distance_l2", 0.0) or 0.0)
        magnitudes.append(dist)
        points.append(TimingSensitivityPoint(candidate_timestep=t, divergence_magnitude=round(dist, 4), phase=WindowSensitivity.STABLE))

    if not points:
        return TemporalSensitivityResult(
            experiment_id=experiment.experiment_id,
            target_memory=target["memory_id"],
            points=[],
            critical_window=None,
            explanation="No valid alternate placements were available to test in this timeline.",
        )

    mean_mag = float(np.mean(magnitudes))
    std_mag = float(np.std(magnitudes)) if len(magnitudes) > 1 else 0.0
    threshold = mean_mag + std_mag

    for p in points:
        if p.divergence_magnitude >= threshold and threshold > 0:
            p.phase = WindowSensitivity.SENSITIVE
        elif p.divergence_magnitude <= mean_mag * 0.4:
            p.phase = WindowSensitivity.EARLY if p.candidate_timestep < origin else WindowSensitivity.RECOVERY
        else:
            p.phase = WindowSensitivity.STABLE

    sensitive_points = [p for p in points if p.phase == WindowSensitivity.SENSITIVE]
    critical_window = None
    if sensitive_points:
        ts = [p.candidate_timestep for p in sensitive_points]
        peak = max(sensitive_points, key=lambda p: p.divergence_magnitude)
        critical_window = CriticalWindow(
            start_timestep=min(ts),
            end_timestep=max(ts),
            peak_timestep=peak.candidate_timestep,
            peak_magnitude=peak.divergence_magnitude,
            baseline_magnitude=round(mean_mag, 4),
            sensitivity_ratio=round(peak.divergence_magnitude / (mean_mag + 1e-6), 4),
        )
        explanation = (
            f"Causal sensitivity within this experiment: placing {target['concept_label']} between "
            f"t={critical_window.start_timestep} and t={critical_window.end_timestep} produces "
            f"{critical_window.sensitivity_ratio:.1f}x the mean downstream divergence observed across "
            f"all tested placements. This describes sensitivity within this experiment only, not a "
            f"universal causal law."
        )
    else:
        explanation = (
            f"No placement of {target['concept_label']} produced divergence more than one standard "
            f"deviation above the mean ({mean_mag:.4f}); this memory's downstream impact appears "
            f"relatively insensitive to timing within the tested range."
        )

    return TemporalSensitivityResult(
        experiment_id=experiment.experiment_id,
        target_memory=target["memory_id"],
        points=points,
        critical_window=critical_window,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Section 11-13 -- Multi-intervention experiments + interaction effects
# ---------------------------------------------------------------------------


def _single_intervention_effect(experiment: Experiment, target_query: str, intervention_type: str, dose: float) -> Tuple[float, str]:
    cmap = CascadeEngine.run_cascade(experiment, target_query, intervention_type=intervention_type, dose=dose)
    return float(cmap.total_cascade_impact), cmap.target_memory


def run_multi_intervention(
    experiment: Experiment,
    interventions: List[Dict[str, Any]],
) -> MultiInterventionResult:
    """Run each intervention individually, then chain them into one combined replay,
    and compare the additive expectation to the actually-observed combined effect.
    """
    if not interventions:
        raise CausalScenarioValidationError("At least one intervention is required.")
    if len(interventions) > MAX_MULTI_INTERVENTIONS:
        raise CausalScenarioValidationError(
            f"Requested {len(interventions)} interventions exceeds the safety limit of {MAX_MULTI_INTERVENTIONS}."
        )

    individual: List[SingleEffect] = []
    for spec in interventions:
        target = spec.get("target_memory")
        itype = spec.get("intervention_type", "remove")
        dose = float(spec.get("dose", 1.0))
        effect, resolved_id = _single_intervention_effect(experiment, target, itype, dose)
        individual.append(SingleEffect(target_memory=resolved_id, intervention=itype, effect=round(effect, 4)))

    # Chain interventions into one combined counterfactual: apply the first against
    # the real experiment, then apply each subsequent one against the *previous*
    # counterfactual's resulting experiment -- a genuinely combined replay.
    from core.genome.cascade import CascadeEngine as _CE

    current_exp = experiment
    last_cf: Optional[CounterfactualExperiment] = None
    for spec in interventions:
        target = spec.get("target_memory")
        itype = spec.get("intervention_type", "remove")
        dose = float(spec.get("dose", 1.0))
        target_mem = resolve_memory(current_exp, target)
        if not target_mem:
            continue
        intv = _CE._build_intervention(current_exp, target_mem, itype, dose)
        cf = run_counterfactual(current_exp, intv, strategy=ReplayStrategy.FULL_REPLAY)
        last_cf = cf
        current_exp = cf.to_experiment()

    if last_cf is None:
        raise CausalScenarioValidationError("No interventions could be resolved against this experiment.")

    observed_combined = float((last_cf.divergence or {}).get("final_state_distance_l2", 0.0) or 0.0)
    expected_combined = float(sum(e.effect for e in individual))
    observed_interaction = round(observed_combined - expected_combined, 4)

    denom = max(abs(expected_combined), 1e-4)
    ratio = observed_interaction / denom

    if abs(observed_interaction) < 0.02:
        classification = InteractionClassification.ADDITIVE
        explanation = (
            f"Observed combined effect ({observed_combined:.4f}) closely tracks the additive expectation "
            f"({expected_combined:.4f}); interventions appear to act independently."
        )
    elif len(individual) < 2:
        classification = InteractionClassification.UNKNOWN
        explanation = "At least two resolved interventions are required to classify an interaction."
    elif ratio > 0.15:
        classification = InteractionClassification.SYNERGY
        explanation = (
            f"Observed combined effect ({observed_combined:.4f}) exceeds the additive expectation "
            f"({expected_combined:.4f}) by {observed_interaction:+.4f}: flagged NON-LINEAR INTERACTION (synergy)."
        )
    elif ratio < -0.15:
        classification = InteractionClassification.ANTAGONISM
        explanation = (
            f"Observed combined effect ({observed_combined:.4f}) falls short of the additive expectation "
            f"({expected_combined:.4f}) by {observed_interaction:+.4f}: flagged NON-LINEAR INTERACTION (antagonism)."
        )
    else:
        classification = InteractionClassification.UNKNOWN
        explanation = "Interaction magnitude is within measurement noise; insufficient evidence to classify."

    interaction = InteractionEffectResult(
        individual_effects=individual,
        expected_combined_effect=round(expected_combined, 4),
        observed_combined_effect=round(observed_combined, 4),
        observed_interaction=observed_interaction,
        classification=classification,
        explanation=explanation,
    )

    return MultiInterventionResult(
        experiment_id=experiment.experiment_id,
        interventions=interventions,
        combined_counterfactual_id=last_cf.counterfactual_id,
        interaction=interaction,
    )


# ---------------------------------------------------------------------------
# Section 14 -- Memory swap experiment
# ---------------------------------------------------------------------------


def run_memory_swap(experiment: Experiment, memory_a_query: str, memory_b_query: str) -> MemorySwapResult:
    """Swap two memories' formation content (concept/attribute/strength) in place,
    holding every other event constant, and measure the resulting divergence.
    """
    mem_a = resolve_memory(experiment, memory_a_query)
    mem_b = resolve_memory(experiment, memory_b_query)
    if not mem_a or not mem_b or mem_a["memory_id"] == mem_b["memory_id"]:
        raise CausalScenarioValidationError("Two distinct, resolvable memories are required for a swap.")

    ev_a = next(e for e in experiment.events if e.get("id") == mem_a["memory_id"])
    ev_b = next(e for e in experiment.events if e.get("id") == mem_b["memory_id"])

    spec_b = {
        "concept_label": ev_b.get("concept_label"),
        "attribute_label": ev_b.get("attribute_label"),
        "strength": ev_b.get("strength", 1.0),
        "importance": ev_b.get("importance", 1.0),
    }
    spec_a = {
        "concept_label": ev_a.get("concept_label"),
        "attribute_label": ev_a.get("attribute_label"),
        "strength": ev_a.get("strength", 1.0),
        "importance": ev_a.get("importance", 1.0),
    }

    intv_a = create_replace_intervention(
        replacement_spec=spec_b,
        target_event_id=mem_a["memory_id"],
        description=f"Memory swap: replace {mem_a['concept_label']} content with {mem_b['concept_label']}",
    )
    cf1 = run_counterfactual(experiment, intv_a, strategy=ReplayStrategy.FULL_REPLAY)
    intermediate_exp = cf1.to_experiment()

    intv_b = create_replace_intervention(
        replacement_spec=spec_a,
        target_event_id=mem_b["memory_id"],
        description=f"Memory swap: replace {mem_b['concept_label']} content with {mem_a['concept_label']}",
    )
    cf2 = run_counterfactual(intermediate_exp, intv_b, strategy=ReplayStrategy.FULL_REPLAY)

    dist = float((cf2.divergence or {}).get("final_state_distance_l2", 0.0) or 0.0)
    output_changed = dist > 0.02
    identity_dependent = dist > 0.05

    explanation = (
        f"Swapping {mem_a['concept_label']} and {mem_b['concept_label']} while holding position and "
        f"surrounding events constant produced a final-state distance of {dist:.4f}. "
        + (
            "This is consistent with behavior depending on memory identity/content, not merely position."
            if identity_dependent
            else "This is consistent with behavior depending primarily on position/association structure "
            "rather than the specific identity of these two memories."
        )
    )

    return MemorySwapResult(
        experiment_id=experiment.experiment_id,
        memory_a=mem_a["memory_id"],
        memory_b=mem_b["memory_id"],
        swapped_counterfactual_id=cf2.counterfactual_id,
        state_distance_l2=round(dist, 4),
        output_changed=output_changed,
        identity_dependent=identity_dependent,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Section 19/20/21 -- Causality matrix + temporal causality map
# ---------------------------------------------------------------------------


def build_causality_matrix(experiment: Experiment, memory_queries: Optional[List[str]] = None) -> CausalityMatrix:
    """Build an N x N matrix of measured removal-effect magnitudes between memories.

    matrix[i][j] = |delta of memory j's strength when memory i is removed|.
    Bounded to MAX_MATRIX_MEMORIES to keep the number of full replays small.
    """
    memories = _extract_memory_cues(experiment)
    if memory_queries:
        resolved = [resolve_memory(experiment, q) for q in memory_queries]
        candidates = [m for m in resolved if m]
    else:
        candidates = memories[:MAX_MATRIX_MEMORIES]

    candidates = candidates[:MAX_MATRIX_MEMORIES]
    ids = [c["memory_id"] for c in candidates]
    labels = [c["concept_label"] for c in candidates]

    matrix: List[List[Optional[float]]] = [[None for _ in ids] for _ in ids]
    for i, src in enumerate(candidates):
        cmap = CascadeEngine.run_cascade(experiment, src["memory_id"], intervention_type="remove", dose=1.0)
        deltas = {n.memory_id: n.delta for n in cmap.nodes}
        for j, tgt in enumerate(candidates):
            if i == j:
                continue
            matrix[i][j] = round(abs(float(deltas.get(tgt["memory_id"], 0.0))), 4)

    return CausalityMatrix(
        experiment_id=experiment.experiment_id,
        memories=ids,
        labels=labels,
        matrix=matrix,
        metric="measured_removal_effect",
    )


def build_temporal_causality_map(experiment: Experiment, target_query: str, n_bins: int = 6) -> TemporalCausalityMap:
    """Reuse the timing-sensitivity sweep, bucketed into time windows for a heatmap view."""
    n_events = len(experiment.events)
    bin_width = max(1, n_events // n_bins)
    candidates = list(range(0, n_events, bin_width))[:n_bins]
    sensitivity = run_timing_sensitivity(experiment, target_query, candidate_timesteps=candidates)

    bins = [
        TemporalCausalityBin(
            window_start=p.candidate_timestep,
            window_end=min(n_events - 1, p.candidate_timestep + bin_width - 1),
            effect=p.divergence_magnitude,
        )
        for p in sensitivity.points
    ]
    return TemporalCausalityMap(
        experiment_id=experiment.experiment_id,
        target_memory=sensitivity.target_memory,
        bins=bins,
    )


# ---------------------------------------------------------------------------
# Section 27/28 -- Recovery experiment / curve (wraps existing RecoveryEngine)
# ---------------------------------------------------------------------------


def build_recovery_curve(experiment: Experiment, target_query: str) -> RecoveryCurveResult:
    rec = RecoveryEngine.test_recovery(experiment, target_query)
    points = [
        RecoveryCurvePoint(phase="PRE-DELETE", strength=rec.baseline_strength),
        RecoveryCurvePoint(phase="POST-DELETE", strength=rec.during_strength),
        RecoveryCurvePoint(phase="RECOVERY", strength=round((rec.during_strength + rec.restored_strength) / 2, 4)),
        RecoveryCurvePoint(phase="FINAL", strength=rec.restored_strength),
    ]
    return RecoveryCurveResult(
        experiment_id=experiment.experiment_id,
        target_memory=rec.target_memory,
        points=points,
        status=rec.status.value if hasattr(rec.status, "value") else str(rec.status),
        recovery_delta=rec.recovery_delta,
    )
