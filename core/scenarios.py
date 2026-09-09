"""Reusable experiment scenarios + batch generators (Phase 02, sections 9–13, 20).

Scenarios are packaged, documented experiments. They all run through the
*same* deterministic engine as everything else — nothing here is special
or hardcoded. ``run_scenario(name, overrides)`` returns the full
``Experiment`` record (kind="experiment") or a structured report from a
batch of real runs (kind="report").

Batch generators (all values from real computation):

- ``retention_curve``      write A → N unrelated events → query A, for N in lags
- ``capacity_sweep``       identical task at d ∈ dimensions
- ``order_comparison``     identical memories in different orders
- ``strength_sweep``       identical task at different memory strengths
- ``interference_matrix``  similarity × update_strength grid
- ``collision_report``     two memories sharing a (controlled-similarity) concept
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .analysis import compare_states
from .experiment import ExperimentConfig
from .mechanisms.base import MechanismParams
from .memory import interference_model
from .runner import run_experiment
from .task import EventSpec, QuerySpec, TaskConfig
from .vectors import cosine

TEXT_SOURCE = "text"


def _events(pairs: List[tuple[str, str]], strength: float = 1.0) -> List[EventSpec]:
    return [
        EventSpec(concept, value, strength=strength)
        for concept, value in pairs
    ]


def _end_queries(concepts: List[str], kind: str = "latest") -> List[QuerySpec]:
    return [QuerySpec(c, timestep=-1, kind=kind) for c in concepts]


def _cfg(
    seed: int,
    mechanism: str,
    params: MechanismParams,
    events: List[EventSpec],
    queries: List[QuerySpec],
    *,
    object_similarity: float = 0.0,
    symbol_similarity: float = 0.0,
    input_noise: float = 0.0,
    probe_original: bool = True,
) -> ExperimentConfig:
    return ExperimentConfig(
        seed=seed,
        mechanism=mechanism,
        params=params,
        task=TaskConfig(
            seed=seed,
            d=params.state_dim,
            n_objects=len({e.object_label for e in events}),
            n_symbols=len({e.symbol_label for e in events}),
            n_conflicts=0,
            object_similarity=object_similarity,
            symbol_similarity=symbol_similarity,
            cycles=1,
            order="structured",
            probe_original=probe_original,
            input_noise=input_noise,
            vector_source=TEXT_SOURCE,
            events=events,
            queries=queries,
        ),
    )


# ---------------------------------------------------------------------------
# scenario registry (section 20)
# ---------------------------------------------------------------------------
@dataclass
class Scenario:
    name: str
    description: str
    learning_objective: str
    defaults: Dict[str, Any]
    kind: str = "experiment"  # "experiment" | "report"
    build: Optional[Callable[[Dict[str, Any]], Any]] = None

    def run(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        opts = dict(self.defaults)
        opts.update(overrides or {})
        assert self.build is not None
        result = self.build(opts)
        return {
            "scenario": self.name,
            "description": self.description,
            "learning_objective": self.learning_objective,
            "experiment": result.pop("experiment", None),
            "report": result.pop("report", None),
            **result,
        }


def _facts(n: int, prefix: str = "fact") -> List[tuple[str, str]]:
    return [(f"{prefix}_{i}", f"value_{i}") for i in range(n)]


def _build_simple(opts) -> Dict[str, Any]:
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events([(opts["concept"], opts["value"])]),
        _end_queries([opts["concept"]]),
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_conflicting(opts) -> Dict[str, Any]:
    c = opts["concept"]
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events([(c, opts["value_a"]), (c, opts["value_b"])]),
        [QuerySpec(c, timestep=-1, kind="latest"), QuerySpec(c, timestep=-1, kind="original")],
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_long_horizon(opts) -> Dict[str, Any]:
    facts = _facts(opts["n_facts"])
    target = facts[opts["query_index"]][0]
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events(facts),
        _end_queries([target]),
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_repeated(opts) -> Dict[str, Any]:
    c, v = opts["concept"], opts["value"]
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events([(c, v)] * int(opts["repetitions"])),
        _end_queries([c]),
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_noisy(opts) -> Dict[str, Any]:
    facts = _facts(opts["n_facts"])
    target = facts[0][0]
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events(facts),
        _end_queries([target]),
        input_noise=float(opts["noise"]),
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_forgetting(opts) -> Dict[str, Any]:
    c, v = opts["concept"], opts["value"]
    fillers = [(f"filler_{i}", f"val_{i}") for i in range(int(opts["lag"]))]
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events([(c, v)] + fillers),
        _end_queries([c]),
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_interleaved(opts) -> Dict[str, Any]:
    n = int(opts["n_each"])
    stream_a = _facts(n, "alpha")
    stream_b = _facts(n, "beta")
    events = []
    for i in range(n):
        events.append(stream_a[i])
        events.append(stream_b[i])
    target = stream_a[opts["query_index"]][0]
    cfg = _cfg(
        opts["seed"], opts["mechanism"], opts["params"],
        _events(events),
        _end_queries([target]),
    )
    return {"experiment": run_experiment(cfg).to_dict()}


def _build_collision(opts) -> Dict[str, Any]:
    report = collision_report(
        seed=opts["seed"],
        mechanism=opts["mechanism"],
        params=opts["params"],
        concept=opts["concept"],
        value_a=opts["value_a"],
        value_b=opts["value_b"],
        similarity=float(opts["collision_intensity"]),
        strength_a=float(opts.get("strength_a", 1.0)),
        strength_b=float(opts.get("strength_b", 1.0)),
    )
    return {"experiment": report.pop("experiment"), "report": report}


def _build_order(opts) -> Dict[str, Any]:
    return {"report": order_comparison(
        seed=opts["seed"], mechanism=opts["mechanism"], params=opts["params"],
        orders=opts["orders"],
    )}


def _build_capacity(opts) -> Dict[str, Any]:
    return {"report": capacity_sweep(
        seed=opts["seed"], mechanism=opts["mechanism"], params=opts["params"],
        dimensions=opts["dimensions"],
    )}


def _default_params(mechanism: str = "baseline") -> MechanismParams:
    return MechanismParams(
        state_dim=128,
        update_strength=1.0,
        memory_strength=1.0,
        decay=0.2 if mechanism == "leaky" else 0.0,
        interference_strength=0.5,
        sparsity=0.1,
    )


def _scenarios() -> Dict[str, Scenario]:
    return {
        "simple_memory": Scenario(
            name="simple_memory",
            description="Write one memory, query it immediately.",
            learning_objective="Baseline: a single fact is stored and retrieved exactly.",
            defaults={"seed": 1, "mechanism": "baseline", "params": _default_params(),
                      "concept": "gizmo", "value": "red"},
            build=_build_simple,
        ),
        "conflicting_memory": Scenario(
            name="conflicting_memory",
            description="Same concept written twice with different values.",
            learning_objective="How does the mechanism resolve (or fail to resolve) conflicting information? Compare latest vs original probes.",
            defaults={"seed": 2, "mechanism": "leaky", "params": _default_params("leaky"),
                      "concept": "vault_a", "value_a": "BLUE", "value_b": "GREEN"},
            build=_build_conflicting,
        ),
        "long_horizon_recall": Scenario(
            name="long_horizon_recall",
            description="Write N facts, query the first one at the end.",
            learning_objective="Does early information survive a long sequence inside a compact state?",
            defaults={"seed": 3, "mechanism": "leaky", "params": _default_params("leaky"),
                      "n_facts": 8, "query_index": 0},
            build=_build_long_horizon,
        ),
        "memory_collision": Scenario(
            name="memory_collision",
            description="Two memories share a (controlled-similarity) concept.",
            learning_objective="Collision: what happens when representations overlap?",
            defaults={"seed": 4, "mechanism": "interference",
                      "params": _default_params("interference"),
                      "concept": "enclosure_7", "value_a": "TIGER", "value_b": "LION",
                      "collision_intensity": 0.8},
            kind="report",
            build=_build_collision,
        ),
        "forgetting": Scenario(
            name="forgetting",
            description="Write a memory, interleave N unrelated events, query it.",
            learning_objective="Temporal decay: how does retention depend on intervening history?",
            defaults={"seed": 5, "mechanism": "leaky", "params": _default_params("leaky"),
                      "concept": "target", "value": "RED", "lag": 10},
            build=_build_forgetting,
        ),
        "order_sensitivity": Scenario(
            name="order_sensitivity",
            description="Identical memories in different arrival orders.",
            learning_objective="Input order: does history order change the final state and recall?",
            defaults={"seed": 6, "mechanism": "leaky", "params": _default_params("leaky"),
                      "orders": [
                          ["alpha_0", "beta_0", "gamma_0", "delta_0"],
                          ["delta_0", "gamma_0", "beta_0", "alpha_0"],
                          ["alpha_0", "gamma_0", "beta_0", "delta_0"],
                      ]},
            kind="report",
            build=_build_order,
        ),
        "capacity_stress": Scenario(
            name="capacity_stress",
            description="Identical task at state dimensions 8…128.",
            learning_objective="Capacity: how does state size change retention and interference?",
            defaults={"seed": 7, "mechanism": "baseline", "params": _default_params(),
                      "dimensions": [8, 16, 32, 64, 128]},
            kind="report",
            build=_build_capacity,
        ),
        "repeated_memory": Scenario(
            name="repeated_memory",
            description="The same memory written k times.",
            learning_objective="Reinforcement: does repetition strengthen retention?",
            defaults={"seed": 8, "mechanism": "interference",
                      "params": _default_params("interference"),
                      "concept": "mantra", "value": "hymn", "repetitions": 3},
            build=_build_repeated,
        ),
        "noisy_memory": Scenario(
            name="noisy_memory",
            description="Events written with input noise.",
            learning_objective="Robustness: how does noise degrade storage and recall?",
            defaults={"seed": 9, "mechanism": "baseline", "params": _default_params(),
                      "n_facts": 6, "noise": 0.6},
            build=_build_noisy,
        ),
        "interleaved_memories": Scenario(
            name="interleaved_memories",
            description="Two interleaved fact streams; query inside stream A.",
            learning_objective="Cross-stream interference: does stream B corrupt stream A?",
            defaults={"seed": 10, "mechanism": "competitive",
                      "params": _default_params("competitive"),
                      "n_each": 3, "query_index": 0},
            build=_build_interleaved,
        ),
    }


SCENARIOS: Dict[str, Scenario] = _scenarios()


def run_scenario(
    name: str, overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run a named scenario (deterministic). Raises ``KeyError`` if unknown."""
    if name not in SCENARIOS:
        raise KeyError(
            f"unknown scenario {name!r}; available: {sorted(SCENARIOS)}"
        )
    return SCENARIOS[name].run(overrides)


# ---------------------------------------------------------------------------
# batch generators
# ---------------------------------------------------------------------------
def _text_cfg(
    seed: int,
    mechanism: str,
    params: MechanismParams,
    events: List[EventSpec],
    queries: List[QuerySpec],
    **task_kw: Any,
) -> ExperimentConfig:
    return _cfg(
        seed, mechanism, params, events, queries, **task_kw
    )


def retention_curve(
    seed: int = 11,
    mechanism: str = "leaky",
    params: Optional[MechanismParams] = None,
    lags: Optional[List[int]] = None,
    concept: str = "target",
    value: str = "RED",
) -> Dict[str, Any]:
    """Write A → N unrelated events → query A, for each N in ``lags``.

    Filler texts are a stable prefix (``filler_0..N-1``), so the target
    memory's own representation is identical across lags — the curve
    isolates the *number of intervening events*.
    """
    params = params or _default_params(mechanism)
    lags = lags if lags is not None else [0, 5, 10, 20, 40, 80, 160]
    data = []
    for lag in lags:
        fillers = [(f"filler_{i}", f"val_{i}") for i in range(lag)]
        cfg = _text_cfg(
            seed, mechanism, params,
            _events([(concept, value)] + fillers),
            _end_queries([concept]),
        )
        exp = run_experiment(cfg)
        q = _final_latest_quality(exp)
        data.append(
            {
                "steps": int(lag),
                "retention": q["quality"],
                "accuracy": 1.0 if q["correctness"] else 0.0,
                "confidence": q["confidence"],
                "final_state_norm": float(exp.snapshots[-1]["norm"]),
            }
        )
    return {"data": data, "mechanism": mechanism, "concept": concept}


def capacity_sweep(
    seed: int = 12,
    mechanism: str = "baseline",
    params: Optional[MechanismParams] = None,
    dimensions: Optional[List[int]] = None,
    n_facts: int = 6,
) -> Dict[str, Any]:
    """Identical task (same texts, same seed) at several state dimensions."""
    params = params or _default_params(mechanism)
    dimensions = dimensions or [8, 16, 32, 64, 128]
    facts = _facts(n_facts)
    data = []
    for d in dimensions:
        p = MechanismParams(**{**params.to_dict(), "state_dim": d})
        cfg = _text_cfg(
            seed, mechanism, p,
            _events(facts),
            _end_queries([f"fact_{i}" for i in range(n_facts)]),
        )
        exp = run_experiment(cfg)
        m = exp.metrics
        data.append(
            {
                "d": int(d),
                "recall_accuracy": m["recall_accuracy"],
                "recall_quality": m["recall_quality"],
                "memory_retention": m["memory_retention"],
                "interference_score": m["interference_score"],
                "state_drift": m["state_drift"],
                "update_magnitude": m["update_magnitude"],
                "final_state_norm": float(exp.snapshots[-1]["norm"]),
            }
        )
    return {"data": data, "mechanism": mechanism, "n_facts": n_facts}


def order_comparison(
    seed: int = 13,
    mechanism: str = "leaky",
    params: Optional[MechanismParams] = None,
    orders: Optional[List[List[str]]] = None,
) -> Dict[str, Any]:
    """Identical memories (one value per concept) in different arrival orders."""
    params = params or _default_params(mechanism)
    default_orders = [
        ["alpha_0", "beta_0", "gamma_0", "delta_0"],
        ["delta_0", "gamma_0", "beta_0", "alpha_0"],
        ["alpha_0", "gamma_0", "beta_0", "delta_0"],
    ]
    orders = orders or default_orders
    all_concepts = list(dict.fromkeys(c for o in orders for c in o))
    values = {c: f"value_{i}" for i, c in enumerate(all_concepts)}

    runs = []
    for i, order in enumerate(orders):
        cfg = _text_cfg(
            seed, mechanism, params,
            _events([(c, values[c]) for c in order]),
            _end_queries(all_concepts),
        )
        exp = run_experiment(cfg)
        runs.append(
            {
                "label": f"order_{i}",
                "order": order,
                "metrics": exp.metrics,
                "final_state_norm": float(exp.snapshots[-1]["norm"]),
                "final_state_vector": exp.snapshots[-1]["state_vector"],
            }
        )

    differences = []
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            diff = compare_states(
                runs[i]["final_state_vector"], runs[j]["final_state_vector"]
            )
            differences.append(
                {
                    "a": runs[i]["label"],
                    "b": runs[j]["label"],
                    "l2_distance": diff["l2_distance"],
                    "cosine_similarity": diff["cosine_similarity"],
                    "normalized_difference": diff["normalized_difference"],
                    "num_changed": diff["num_changed"],
                }
            )
    for r in runs:
        r.pop("final_state_vector", None)
    return {"orders": runs, "pairwise_differences": differences, "mechanism": mechanism}


def strength_sweep(
    seed: int = 14,
    mechanism: str = "baseline",
    params: Optional[MechanismParams] = None,
    strengths: Optional[List[float]] = None,
    n_facts: int = 4,
) -> Dict[str, Any]:
    """Identical task at different memory strengths (0.1 … 1.0)."""
    params = params or _default_params(mechanism)
    strengths = strengths if strengths is not None else [0.1, 0.25, 0.5, 0.75, 1.0]
    facts = _facts(n_facts)
    data = []
    for s in strengths:
        cfg = _text_cfg(
            seed, mechanism, params,
            _events(facts, strength=s),
            _end_queries([f"fact_{i}" for i in range(n_facts)]),
        )
        exp = run_experiment(cfg)
        m = exp.metrics
        data.append(
            {
                "strength": float(s),
                "recall_accuracy": m["recall_accuracy"],
                "recall_quality": m["recall_quality"],
                "memory_retention": m["memory_retention"],
                "update_magnitude": m["update_magnitude"],
                "final_state_norm": float(exp.snapshots[-1]["norm"]),
            }
        )
    return {"data": data, "mechanism": mechanism, "n_facts": n_facts}


def interference_matrix(
    seed: int = 15,
    mechanism: str = "baseline",
    params: Optional[MechanismParams] = None,
    similarities: Optional[List[float]] = None,
    update_strengths: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Grid of similarity × update_strength, every cell a real run.

    Cell experiment: memory A (``alpha_0 = value_a``) is written at
    strength 1.0, then memory B (``beta_0 = value_b``) is written at
    strength ``update_strength`` (η — the *interfering* write's strength);
    then we recall ``alpha_0``. Reported ``similarity`` is the *measured*
    key similarity, ``interference`` is the measured leakage of beta's
    value into alpha's readout, ``retention`` is alpha's recall quality.

    Note: η is the interfering memory's write strength, not the mechanism's
    global learning rate — otherwise η would cancel out of every cosine
    (a scale-invariant readout) and the grid would be degenerate.
    """
    params = params or _default_params(mechanism)
    similarities = similarities if similarities is not None else [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    update_strengths = (
        update_strengths if update_strengths is not None else [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    )
    cells = []
    for rho in similarities:
        for eta in update_strengths:
            cfg = _text_cfg(
                seed, mechanism, params,
                [
                    EventSpec("alpha_0", "value_a", strength=1.0),
                    EventSpec("beta_0", "value_b", strength=float(eta)),
                ],
                _end_queries(["alpha_0"]),
                object_similarity=rho,
            )
            exp = run_experiment(cfg)
            task = exp.task
            ka = np.asarray(task["objects"]["alpha_0"], dtype=np.float64)
            kb = np.asarray(task["objects"]["beta_0"], dtype=np.float64)
            measured_sim = float(cosine(ka, kb))
            q = _final_latest_quality(exp)
            readout = np.asarray(q["predicted_vector"], dtype=np.float64)
            vb = np.asarray(task["symbols"]["value_b"], dtype=np.float64)
            leak = float(max(0.0, cosine(readout, vb)))
            cells.append(
                {
                    "similarity": measured_sim,
                    "update_strength": float(eta),
                    "interference": leak,
                    "retention": q["quality"],
                    "recall_accuracy": 1.0 if q["correctness"] else 0.0,
                    "confidence": q["confidence"],
                }
            )
    return {
        "data": cells,
        "mechanism": mechanism,
        "grid": {"similarities": similarities, "update_strengths": update_strengths},
        "units": {
            "similarity": "measured cosine of the two concept key vectors",
            "update_strength": "write strength of the INTERFERING memory B (A is written at 1.0)",
            "interference": "cosine of alpha's readout with beta's value (leakage)",
            "retention": "cosine of alpha's readout with alpha's true value",
            "recall_accuracy": "alpha's latest query correct?",
        },
    }


def collision_report(
    seed: int = 16,
    mechanism: str = "interference",
    params: Optional[MechanismParams] = None,
    concept: str = "enclosure_7",
    value_a: str = "TIGER",
    value_b: str = "LION",
    similarity: float = 0.8,
    strength_a: float = 1.0,
    strength_b: float = 1.0,
) -> Dict[str, Any]:
    """Two memories colliding on a (controlled-similarity) concept.

    Memory A: "<concept> = <value_a>". Memory B: "<concept> = <value_b>".
    ``similarity`` controls how similar B's key is to A's key (1.0 →
    identical concept, a hard collision on the same key). Returns the full
    report: representation similarity, state before/after each write,
    recall, original/new retention, and the measured + modeled
    interference.
    """
    params = params or _default_params(mechanism)
    hard_collision = similarity >= 1.0 - 1e-9
    concept_b = concept if hard_collision else f"{concept}__b"
    cfg = _text_cfg(
        seed, mechanism, params,
        [
            EventSpec(concept, value_a, strength=strength_a),
            EventSpec(concept_b, value_b, strength=strength_b),
        ],
        _end_queries([concept]),
        object_similarity=similarity if not hard_collision else 0.0,
    )
    exp = run_experiment(cfg)
    task = exp.task

    ka = np.asarray(task["objects"][concept], dtype=np.float64)
    kb = np.asarray(task["objects"].get(concept_b, ka), dtype=np.float64)
    key_sim = float(cosine(ka, kb))
    va = np.asarray(task["symbols"][value_a], dtype=np.float64)
    vb = np.asarray(task["symbols"][value_b], dtype=np.float64)
    value_sim = float(cosine(va, vb))

    q = _final_latest_quality(exp)
    readout = np.asarray(q["predicted_vector"], dtype=np.float64)
    original_retention = float(cosine(readout, va))
    new_retention = float(cosine(readout, vb))
    interference_measured = float(max(0.0, cosine(readout, vb)))
    interference_modeled = float(
        interference_model(
            ka, kb, params.update_strength, competition_factor=1.0
        )
    )

    return {
        "memory_a": {"concept": concept, "value": value_a, "strength": strength_a},
        "memory_b": {"concept": concept_b, "value": value_b, "strength": strength_b},
        "representation_similarity": {
            "key_similarity": key_sim,
            "value_similarity": value_sim,
            "hard_collision_same_key": hard_collision,
        },
        "collision_intensity": {
            "requested": float(similarity),
            "measured_key_similarity": key_sim,
        },
        "state_before": {"norm": float(exp.snapshots[0]["norm"]),
                         "top_dimensions": exp.snapshots[0]["active_dimensions"][:10]},
        "state_after_a": {"norm": float(exp.snapshots[1]["norm"]),
                          "num_active": int(exp.snapshots[1]["num_active"])},
        "state_after_b": {"norm": float(exp.snapshots[2]["norm"]),
                          "num_active": int(exp.snapshots[2]["num_active"])},
        "recall": {
            "query": concept,
            "predicted_value": q["predicted_label"],
            "confidence": q["confidence"],
            "ground_truth": q["truth_label"],
            "correct": q["correctness"],
            "quality": q["quality"],
            "candidates": q["top_matches"][:3],
        },
        "retention": {
            "original_memory": original_retention,
            "new_memory": new_retention,
        },
        "interference_score": {
            "measured": interference_measured,
            "modeled": interference_modeled,
            "model_formula": "similarity × update_strength × competition_factor (educational model)",
        },
        "experiment": exp.to_dict(),
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _final_latest_quality(exp) -> Dict[str, Any]:
    max_ts = max((q["timestep"] for q in exp.queries), default=-1)
    best = None
    for q in exp.queries:
        if q["kind"] == "latest" and q["timestep"] == max_ts:
            best = q
            break
    assert best is not None, "expected at least one final latest query"
    return best