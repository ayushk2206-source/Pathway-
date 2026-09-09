"""Counterfactual replay engine (Phase 04).

Replays historical memory trajectories under interventions without mutating original records.
Supports full deterministic replay as well as checkpoint-based partial replay.
"""

from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.events import Event
from core.experiment import Experiment, ExperimentConfig, make_experiment
from core.mechanisms import create_mechanism
from core.metrics import compute_metrics
from core.recall import QueryResult, execute_query
from core.runner import _query_summary, run_experiment
from core.task import EventSpec, QuerySpec, TaskConfig, generate_task

from .interventions import CounterfactualValidationError, Intervention, validate_intervention
from .types import InterventionType, ReplayStrategy


def _explicit_task_config_from_experiment(experiment: Experiment) -> TaskConfig:
    """Extract an explicit TaskConfig with editable EventSpec and QuerySpec objects."""
    task_dict = experiment.task
    config_task = experiment.config.get("task", {})
    return TaskConfig(
        seed=config_task.get("seed"),
        d=config_task.get("d", task_dict.get("d")),
        n_objects=config_task.get("n_objects", len(task_dict.get("objects", {}))),
        n_symbols=config_task.get("n_symbols", len(task_dict.get("symbols", {}))),
        n_conflicts=config_task.get("n_conflicts", 0),
        object_similarity=float(config_task.get("object_similarity", 0.0)),
        symbol_similarity=float(config_task.get("symbol_similarity", 0.0)),
        cycles=int(config_task.get("cycles", 1)),
        order=str(config_task.get("order", "interleaved")),
        probe_original=bool(config_task.get("probe_original", True)),
        input_noise=float(config_task.get("input_noise", 0.0)),
        vector_source=str(config_task.get("vector_source", "random")),
        events=[
            EventSpec(
                object_label=ev["concept_label"],
                symbol_label=ev["attribute_label"],
                importance=float(ev.get("importance", 1.0)),
                strength=float(ev.get("strength", 1.0)),
                noise=ev.get("noise"),
                metadata=dict(ev.get("metadata", {})),
            )
            for ev in task_dict.get("events", [])
        ],
        queries=[
            QuerySpec(
                object_label=q["object_label"],
                timestep=int(q["timestep"]),
                kind=q.get("kind", "latest"),
                expected_symbol_label=None,  # recomputed from counterfactual history
            )
            for q in task_dict.get("queries", [])
        ],
    )


def _resolve_target_timestep(experiment: Experiment, intervention: Intervention) -> int:
    """Find target index from target_timestep or target_event_id."""
    if intervention.target_timestep is not None:
        return int(intervention.target_timestep)
    if intervention.target_event_id:
        for idx, ev in enumerate(experiment.events):
            if ev.get("id") == intervention.target_event_id:
                return idx
        raise CounterfactualValidationError(f"Target event ID '{intervention.target_event_id}' not found in history.")
    return 0


def prepare_counterfactual_task(
    original_experiment: Experiment,
    intervention: Intervention,
) -> Tuple[TaskConfig, int]:
    """Transform the task configuration by applying an intervention to the event stream.

    Returns the new TaskConfig and the branch_point (earliest altered timestep).
    """
    history_len = len(original_experiment.events)
    validate_intervention(intervention, history_len)

    task_cfg = _explicit_task_config_from_experiment(original_experiment)
    itype = intervention.intervention_type
    p = intervention.parameters

    branch_point = 0
    events = list(task_cfg.events)

    if itype == InterventionType.REMOVE_EVENT:
        t_idx = _resolve_target_timestep(original_experiment, intervention)
        branch_point = t_idx
        events = [e for i, e in enumerate(events) if i != t_idx]
        new_end = len(events) - 1
        surviving = {e.object_label for e in events}

        def remap_t(t: int) -> int:
            if t < t_idx:
                return t
            return max(0, min(t - 1, new_end))

        task_cfg.queries = [
            QuerySpec(
                object_label=q.object_label,
                timestep=remap_t(q.timestep),
                kind=q.kind,
                expected_symbol_label=None,
            )
            for q in task_cfg.queries
            if q.object_label in surviving
        ]

    elif itype == InterventionType.DUPLICATE_EVENT:
        t_idx = _resolve_target_timestep(original_experiment, intervention)
        branch_point = t_idx + 1
        dup = copy.deepcopy(events[t_idx])
        events.insert(t_idx + 1, dup)

        def remap_dup(t: int) -> int:
            return t + 1 if t >= t_idx + 1 else t

        for q in task_cfg.queries:
            q.timestep = remap_dup(q.timestep)

    elif itype == InterventionType.REPLACE_EVENT:
        t_idx = _resolve_target_timestep(original_experiment, intervention)
        branch_point = t_idx
        spec = p["replacement_spec"]
        events[t_idx] = EventSpec(
            object_label=spec["concept_label"],
            symbol_label=spec["attribute_label"],
            importance=float(spec.get("importance", 1.0)),
            strength=float(spec.get("strength", 1.0)),
            noise=spec.get("noise"),
            metadata=dict(spec.get("metadata", {})),
        )

    elif itype == InterventionType.MODIFY_EVENT:
        t_idx = _resolve_target_timestep(original_experiment, intervention)
        branch_point = t_idx
        mods = p.get("modifications", {})
        ev = events[t_idx]
        if "concept_label" in mods:
            ev.object_label = str(mods["concept_label"])
        if "attribute_label" in mods:
            ev.symbol_label = str(mods["attribute_label"])
        if "strength" in mods:
            ev.strength = float(mods["strength"])
        if "importance" in mods:
            ev.importance = float(mods["importance"])
        if "noise" in mods:
            ev.noise = float(mods["noise"]) if mods["noise"] is not None else None

    elif itype == InterventionType.MOVE_EVENT:
        t_from = _resolve_target_timestep(original_experiment, intervention)
        t_to = int(p["destination_timestep"])
        branch_point = min(t_from, t_to)
        ev = events.pop(t_from)
        events.insert(t_to, ev)

    elif itype == InterventionType.CHANGE_STRENGTH:
        t_idx = _resolve_target_timestep(original_experiment, intervention)
        branch_point = t_idx
        ev = events[t_idx]
        if "new_strength" in p and p["new_strength"] is not None:
            ev.strength = float(p["new_strength"])
        elif "factor" in p and p["factor"] is not None:
            ev.strength = float(ev.strength * float(p["factor"]))

    elif itype == InterventionType.CHANGE_SIMILARITY:
        t_idx = _resolve_target_timestep(original_experiment, intervention)
        branch_point = t_idx
        d_sim = float(p.get("delta_similarity", 0.0))
        task_cfg.object_similarity = float(np.clip(task_cfg.object_similarity + d_sim, 0.0, 1.0))

    elif itype == InterventionType.INJECT_MEMORY:
        spec = p["event_spec"]
        inj_time = intervention.target_timestep if intervention.target_timestep is not None else int(p.get("timestep", len(events)))
        branch_point = inj_time
        new_ev = EventSpec(
            object_label=spec["concept_label"],
            symbol_label=spec["attribute_label"],
            importance=float(spec.get("importance", 1.0)),
            strength=float(spec.get("strength", 1.0)),
            noise=spec.get("noise"),
            metadata=dict(spec.get("metadata", {})),
        )
        events.insert(inj_time, new_ev)
        for q in task_cfg.queries:
            if q.timestep >= inj_time:
                q.timestep += 1

    elif itype == InterventionType.TEMPORAL_DELETE:
        t_start = int(p.get("start_timestep", 0))
        t_end = int(p.get("end_timestep", len(events) - 1))
        branch_point = t_start
        events = [e for i, e in enumerate(events) if not (t_start <= i <= t_end)]
        new_end = len(events) - 1
        surviving = {e.object_label for e in events}
        count_removed = t_end - t_start + 1

        def remap_range(t: int) -> int:
            if t < t_start:
                return t
            return max(0, min(t - count_removed, new_end))

        task_cfg.queries = [
            QuerySpec(
                object_label=q.object_label,
                timestep=remap_range(q.timestep),
                kind=q.kind,
                expected_symbol_label=None,
            )
            for q in task_cfg.queries
            if q.object_label in surviving
        ]

    elif itype == InterventionType.TEMPORAL_SCALE:
        t_start = int(p.get("start_timestep", 0))
        t_end = int(p.get("end_timestep", len(events) - 1))
        factor = float(p.get("factor", 1.0))
        branch_point = t_start
        for i in range(t_start, min(t_end + 1, len(events))):
            events[i].strength = float(events[i].strength * factor)

    elif itype in {
        InterventionType.RESET_MEMORY,
        InterventionType.FREEZE_MEMORY,
        InterventionType.TEMPORAL_FREEZE,
        InterventionType.SYNAPSE_PREVENT_STRENGTHEN,
        InterventionType.SYNAPSE_SILENCE,
        InterventionType.SYNAPSE_SCALE,
        InterventionType.CHANGE_DECAY,
        InterventionType.CHANGE_PLASTICITY,
    }:
        # These dynamic interventions are applied during the execution replay loop
        if itype == InterventionType.RESET_MEMORY:
            branch_point = _resolve_target_timestep(original_experiment, intervention)
        elif itype in {InterventionType.FREEZE_MEMORY, InterventionType.TEMPORAL_FREEZE}:
            branch_point = int(p.get("start_timestep", 0))
        else:
            branch_point = intervention.target_timestep if intervention.target_timestep is not None else int(p.get("target_timestep", 0))

    task_cfg.events = events
    return task_cfg, branch_point


def _parse_synapse_coords(params: Dict[str, Any]) -> Tuple[int, int]:
    """Parse synapse target coordinates (target_row, source_col) from intervention parameters."""
    if "target_idx" in params and "source_idx" in params:
        return int(params["target_idx"]), int(params["source_idx"])
    syn_id = str(params.get("synapse_id", ""))
    parts = syn_id.split("_")
    if len(parts) == 3 and parts[0] == "syn" and parts[1].startswith("k") and parts[2].startswith("v"):
        try:
            return int(parts[2][1:]), int(parts[1][1:])
        except ValueError:
            pass
    if "_" in syn_id:
        sub = syn_id.split("_")
        try:
            k_part = [s for s in sub if s.startswith("k")]
            v_part = [s for s in sub if s.startswith("v")]
            if k_part and v_part:
                return int(v_part[0][1:]), int(k_part[0][1:])
        except Exception:
            pass
    return (0, 0)


def replay_counterfactual_engine(
    original_experiment: Experiment,
    intervention: Intervention,
    strategy: ReplayStrategy = ReplayStrategy.FULL_REPLAY,
) -> Tuple[Experiment, int]:
    """Execute the counterfactual replay through the memory engine.

    Returns the new Experiment and branch_point.
    The original_experiment object is strictly preserved and never mutated.
    """
    task_cfg, branch_point = prepare_counterfactual_task(original_experiment, intervention)

    orig_cfg = ExperimentConfig.from_dict(original_experiment.config)
    cf_config = ExperimentConfig(
        seed=orig_cfg.seed,
        mechanism=orig_cfg.mechanism,
        params=copy.deepcopy(orig_cfg.params),
        task=task_cfg,
        update_steps_per_event=orig_cfg.update_steps_per_event,
    )

    itype = intervention.intervention_type
    p = intervention.parameters

    # Dynamic intervention flags for custom loop
    needs_custom_loop = itype in {
        InterventionType.RESET_MEMORY,
        InterventionType.FREEZE_MEMORY,
        InterventionType.TEMPORAL_FREEZE,
        InterventionType.SYNAPSE_PREVENT_STRENGTHEN,
        InterventionType.SYNAPSE_SILENCE,
        InterventionType.SYNAPSE_SCALE,
        InterventionType.CHANGE_DECAY,
        InterventionType.CHANGE_PLASTICITY,
    } or strategy == ReplayStrategy.CHECKPOINT

    if not needs_custom_loop:
        # Standard clean deterministic replay
        cf_exp = run_experiment(cf_config, replay_of=original_experiment.experiment_id)
        return cf_exp, branch_point

    # Custom loop handling dynamic state reset, freeze, synaptic surgery, or parameter shifts
    task = generate_task(cf_config.task, fallback_seed=cf_config.seed)
    mech = create_mechanism(cf_config.mechanism, cf_config.params, seed=cf_config.seed)

    # Initial adjustments if branch_point == 0
    if itype == InterventionType.CHANGE_DECAY and branch_point == 0:
        new_decay = float(p.get("new_decay", mech.params.decay))
        mech.params.decay = new_decay
        cf_config.params.decay = new_decay
    elif itype == InterventionType.CHANGE_PLASTICITY and branch_point == 0:
        new_str = float(p.get("new_update_strength", mech.params.update_strength))
        mech.params.update_strength = new_str
        cf_config.params.update_strength = new_str

    queries_by_time: Dict[int, List] = defaultdict(list)
    for q in task.queries:
        queries_by_time[int(q.timestep)].append(q)

    snapshots: List[Dict] = []
    initial = mech.get_state_snapshot()
    initial["timestep"] = 0
    initial["event_id"] = None
    initial["trace"] = {
        "mechanism": mech.name,
        "note": "initial state (zero) before any event",
    }
    snapshots.append(initial)

    reset_t = _resolve_target_timestep(original_experiment, intervention) if itype == InterventionType.RESET_MEMORY else -1
    freeze_start = int(p.get("start_timestep", -1)) if itype in {InterventionType.FREEZE_MEMORY, InterventionType.TEMPORAL_FREEZE} else -1
    freeze_end = int(p.get("end_timestep", -1)) if itype in {InterventionType.FREEZE_MEMORY, InterventionType.TEMPORAL_FREEZE} else -1

    target_row, source_col = _parse_synapse_coords(p) if itype in {
        InterventionType.SYNAPSE_PREVENT_STRENGTHEN,
        InterventionType.SYNAPSE_SILENCE,
        InterventionType.SYNAPSE_SCALE,
    } else (0, 0)
    pre_branch_weight: Optional[float] = None

    query_results: List[QueryResult] = []
    for t, event in enumerate(task.events):
        if t == reset_t:
            mech.initialize()

        # At divergence step, capture baseline weight before this event is written
        if t == branch_point:
            if itype == InterventionType.CHANGE_DECAY:
                mech.params.decay = float(p.get("new_decay", mech.params.decay))
            elif itype == InterventionType.CHANGE_PLASTICITY:
                mech.params.update_strength = float(p.get("new_update_strength", mech.params.update_strength))
            elif itype == InterventionType.SYNAPSE_PREVENT_STRENGTHEN:
                if mech.state_is_matrix:
                    if target_row < mech._state.shape[0] and source_col < mech._state.shape[1]:
                        pre_branch_weight = float(mech._state[target_row, source_col])
                    else:
                        pre_branch_weight = 0.0
                else:
                    dim = target_row % mech._state.shape[0]
                    pre_branch_weight = float(mech._state[dim])

        if freeze_start <= t <= freeze_end and freeze_start != -1:
            # Frozen: skip write, apply idle dynamics if decay exists
            trace = mech.step_no_input(cf_config.update_steps_per_event)
            trace["note"] = f"Counterfactual frozen memory state at t={t}"
        else:
            trace = mech.update(event)
            if cf_config.update_steps_per_event > 1:
                trace["extra_steps"] = mech.step_no_input(cf_config.update_steps_per_event - 1)

        # Apply post-write synaptic intervention starting at branch_point
        if t >= branch_point:
            if itype == InterventionType.SYNAPSE_PREVENT_STRENGTHEN and pre_branch_weight is not None:
                if mech.state_is_matrix:
                    if target_row < mech._state.shape[0] and source_col < mech._state.shape[1]:
                        curr = float(mech._state[target_row, source_col])
                        if pre_branch_weight >= 0:
                            mech._state[target_row, source_col] = min(curr, pre_branch_weight)
                        else:
                            mech._state[target_row, source_col] = max(curr, pre_branch_weight)
                else:
                    dim = target_row % mech._state.shape[0]
                    curr = float(mech._state[dim])
                    if pre_branch_weight >= 0:
                        mech._state[dim] = min(curr, pre_branch_weight)
                    else:
                        mech._state[dim] = max(curr, pre_branch_weight)

            elif itype == InterventionType.SYNAPSE_SILENCE:
                if mech.state_is_matrix:
                    if target_row < mech._state.shape[0] and source_col < mech._state.shape[1]:
                        mech._state[target_row, source_col] = 0.0
                else:
                    dim = target_row % mech._state.shape[0]
                    mech._state[dim] = 0.0

            elif itype == InterventionType.SYNAPSE_SCALE and t == branch_point:
                factor = float(p.get("factor", 0.5))
                if mech.state_is_matrix:
                    if target_row < mech._state.shape[0] and source_col < mech._state.shape[1]:
                        mech._state[target_row, source_col] *= factor
                else:
                    dim = target_row % mech._state.shape[0]
                    mech._state[dim] *= factor

        snap = mech.get_state_snapshot()
        snap["timestep"] = t + 1
        snap["event_id"] = event.id
        snap["trace"] = trace

        for q in queries_by_time.get(t, []):
            res = execute_query(mech, q, task.symbols)
            query_results.append(res)
            snap.setdefault("query_results", []).append(_query_summary(res))
        snapshots.append(snap)

    predictions = [_query_summary(r) for r in query_results]
    ground_truth = [
        {
            "query_id": r.query_id,
            "timestep": int(r.timestep),
            "object_label": r.object_label,
            "kind": r.kind,
            "truth_label": r.truth_label,
        }
        for r in query_results
    ]
    metrics = compute_metrics(snapshots, query_results, task)

    cf_exp = make_experiment(
        seed=cf_config.seed,
        mechanism=cf_config.mechanism,
        params=cf_config.params,
        task_dict=task.to_dict(),
        config_dict=cf_config.to_dict(),
        events=[e.to_dict() for e in task.events],
        snapshots=snapshots,
        queries=[r.to_dict() for r in query_results],
        predictions=predictions,
        ground_truth=ground_truth,
        metrics=metrics,
        replay_of=original_experiment.experiment_id,
    )
    return cf_exp, branch_point
