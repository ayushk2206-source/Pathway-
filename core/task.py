"""Synthetic controlled-memory task generator (section 8).

The canonical task is a *paired-associate recall with conflicts*:

    "The symbol associated with object A is RED."    (event 1)
    "The symbol associated with object B is BLUE."   (event 2)
    "The symbol associated with object A is GREEN."  (event 5 — conflict)

and queries such as "What is the symbol associated with A?" asked at a
chosen point in the sequence. Objects (cues) and symbols (values) are
fixed-dimensional vectors; their mutual similarity is a task control, so a
learner can dial how confusable competing memories are.

Ground truth for a query is fully determined by the *history*:

- kind="latest"   → the symbol most recently bound to the object at/before
                     the query timestep (correct answer for a recency test)
- kind="original" → the symbol bound to the object *before its first
                     conflict* (correct answer for a retention/probe test)

The generator is deterministic: all randomness flows from a single seeded
``numpy.random.Generator``. The same ``TaskConfig`` + seed always yields
the same events, vectors, and queries.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .events import Event
from .vectors import correlated_flat_vectors, correlated_vectors

SYMBOL_POOL = ["RED", "BLUE", "GREEN", "YELLOW", "PURPLE", "ORANGE", "CYAN", "PINK"]


def _symbol_label(i: int) -> str:
    if i < len(SYMBOL_POOL):
        return f"sym_{SYMBOL_POOL[i]}"
    return f"sym_{i}"


def _object_label(i: int) -> str:
    return f"obj_{chr(ord('A') + i)}" if i < 26 else f"obj_{i}"


@dataclass
class EventSpec:
    """Explicit event requested by the experimenter (bypasses auto-gen)."""

    object_label: str
    symbol_label: str
    importance: float = 1.0
    strength: float = 1.0
    noise: Optional[float] = None  # None → use task-level input_noise
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuerySpec:
    """Explicit query requested by the experimenter.

    ``timestep`` = run the query after events[0..timestep] have been
    processed (use -1 for "after the final event").
    """

    object_label: str
    timestep: int = -1
    kind: str = "latest"  # "latest" | "original"
    expected_symbol_label: Optional[str] = None  # override ground truth


@dataclass
class TaskConfig:
    """Controls for the task generator (section 7 variables).

    ``events``/``queries``, when provided, bypass auto-generation (useful
    for hand-crafted experiments and counterfactuals in later phases).
    """

    seed: Optional[int] = None
    d: int = 128
    n_objects: int = 6
    n_symbols: int = 4
    n_conflicts: int = 2
    object_similarity: float = 0.0
    symbol_similarity: float = 0.0
    cycles: int = 1
    order: str = "interleaved"  # structured | interleaved | randomized
    probe_original: bool = True
    input_noise: float = 0.0
    # "random": vectors drawn from the seed RNG (Phase 01 behavior)
    # "text":   vectors encoded deterministically from the labels via
    #           core.encoder (Phase 02 memory engine)
    vector_source: str = "random"
    events: Optional[List[EventSpec]] = None
    queries: Optional[List[QuerySpec]] = None

    def __post_init__(self) -> None:
        # accept plain dicts for convenience (API layer, scenarios)
        if self.events is not None:
            self.events = [
                e if isinstance(e, EventSpec) else EventSpec(**dict(e))
                for e in self.events
            ]
        if self.queries is not None:
            converted = []
            for q in self.queries:
                if isinstance(q, QuerySpec):
                    converted.append(q)
                    continue
                q = dict(q)
                if "concept" in q and "object_label" not in q:
                    q["object_label"] = q.pop("concept")
                converted.append(QuerySpec(**q))
            self.queries = converted

    def validated(self) -> "TaskConfig":
        if self.d < 1:
            raise ValueError("d must be >= 1")
        if self.n_objects < 1:
            raise ValueError("n_objects must be >= 1")
        if self.n_symbols < 1:
            raise ValueError("n_symbols must be >= 1")
        if self.n_conflicts < 0 or self.n_conflicts > self.n_objects:
            raise ValueError("n_conflicts must be in [0, n_objects]")
        if self.n_symbols == 1 and self.n_conflicts > 0:
            raise ValueError("conflicts require at least 2 symbols")
        if self.cycles < 1:
            raise ValueError("cycles must be >= 1")
        if self.order not in ("structured", "interleaved", "randomized"):
            raise ValueError(f"unknown order {self.order!r}")
        if self.vector_source not in ("random", "text"):
            raise ValueError(f"unknown vector_source {self.vector_source!r}")
        for name in ("object_similarity", "symbol_similarity", "input_noise"):
            v = float(getattr(self, name))
            if name != "input_noise" and not (0.0 <= v <= 1.0):
                raise ValueError(f"{name} must be in [0, 1]")
            if name == "input_noise" and v < 0:
                raise ValueError("input_noise must be >= 0")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "d": int(self.d),
            "n_objects": int(self.n_objects),
            "n_symbols": int(self.n_symbols),
            "n_conflicts": int(self.n_conflicts),
            "object_similarity": float(self.object_similarity),
            "symbol_similarity": float(self.symbol_similarity),
            "cycles": int(self.cycles),
            "order": self.order,
            "probe_original": bool(self.probe_original),
            "input_noise": float(self.input_noise),
            "vector_source": self.vector_source,
            "events": (
                None
                if self.events is None
                else [
                    {
                        "object_label": e.object_label,
                        "symbol_label": e.symbol_label,
                        "importance": float(e.importance),
                        "strength": float(e.strength),
                        "noise": e.noise,
                        "metadata": dict(e.metadata),
                    }
                    for e in self.events
                ]
            ),
            "queries": (
                None
                if self.queries is None
                else [
                    {
                        "object_label": q.object_label,
                        "timestep": int(q.timestep),
                        "kind": q.kind,
                        "expected_symbol_label": q.expected_symbol_label,
                    }
                    for q in self.queries
                ]
            ),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskConfig":
        ev = d.get("events")
        qs = d.get("queries")
        return cls(
            seed=d.get("seed"),
            d=int(d.get("d", 128)),
            n_objects=int(d.get("n_objects", 6)),
            n_symbols=int(d.get("n_symbols", 4)),
            n_conflicts=int(d.get("n_conflicts", 2)),
            object_similarity=float(d.get("object_similarity", 0.0)),
            symbol_similarity=float(d.get("symbol_similarity", 0.0)),
            cycles=int(d.get("cycles", 1)),
            order=str(d.get("order", "interleaved")),
            probe_original=bool(d.get("probe_original", True)),
            input_noise=float(d.get("input_noise", 0.0)),
            vector_source=str(d.get("vector_source", "random")),
            events=(
                None
                if ev is None
                else [EventSpec(**{k: v for k, v in e.items()}) for e in ev]
            ),
            queries=(
                None
                if qs is None
                else [QuerySpec(**{k: v for k, v in q.items()}) for q in qs]
            ),
        )


@dataclass
class Query:
    """A recall probe: "what is the symbol of <object>?" at a timestep."""

    id: str
    timestep: int
    object_label: str
    kind: str  # "latest" | "original"
    expected_attribute_label: str
    key_vector: Optional[np.ndarray] = None
    expected_value_vector: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestep": int(self.timestep),
            "object_label": self.object_label,
            "kind": self.kind,
            "expected_attribute_label": self.expected_attribute_label,
            "key_vector": None if self.key_vector is None else self.key_vector.tolist(),
            "expected_value_vector": (
                None
                if self.expected_value_vector is None
                else self.expected_value_vector.tolist()
            ),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Query":
        kv = d.get("key_vector")
        ev = d.get("expected_value_vector")
        return cls(
            id=d["id"],
            timestep=int(d["timestep"]),
            object_label=d["object_label"],
            kind=d.get("kind", "latest"),
            expected_attribute_label=d["expected_attribute_label"],
            key_vector=None if kv is None else np.asarray(kv, dtype=np.float64),
            expected_value_vector=None if ev is None else np.asarray(ev, dtype=np.float64),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass
class Task:
    """A fully materialized task: vectors, events, queries, and history."""

    config: Dict[str, Any]
    seed: int
    d: int
    objects: Dict[str, np.ndarray]  # label -> key vector
    symbols: Dict[str, np.ndarray]  # label -> value vector
    events: List[Event]
    queries: List[Query]
    # history metadata (used by metrics + forensics)
    initial_assignment: Dict[str, str]  # object -> first symbol
    last_write: Dict[str, tuple[int, str]]  # object -> (timestep, symbol)
    conflicts: Dict[str, List[Dict[str, Any]]]  # object -> conflict records

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": self.config,
            "seed": int(self.seed),
            "d": int(self.d),
            "objects": {k: v.tolist() for k, v in self.objects.items()},
            "symbols": {k: v.tolist() for k, v in self.symbols.items()},
            "events": [e.to_dict() for e in self.events],
            "queries": [q.to_dict() for q in self.queries],
            "initial_assignment": dict(self.initial_assignment),
            "last_write": {k: list(v) for k, v in self.last_write.items()},
            "conflicts": {
                k: list(v) for k, v in self.conflicts.items()
            },
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Task":
        return cls(
            config=dict(d["config"]),
            seed=int(d["seed"]),
            d=int(d["d"]),
            objects={k: np.asarray(v, dtype=np.float64) for k, v in d["objects"].items()},
            symbols={k: np.asarray(v, dtype=np.float64) for k, v in d["symbols"].items()},
            events=[Event.from_dict(e) for e in d["events"]],
            queries=[Query.from_dict(q) for q in d["queries"]],
            initial_assignment=dict(d["initial_assignment"]),
            last_write={k: tuple(v) for k, v in d["last_write"].items()},
            conflicts={k: list(v) for k, v in d["conflicts"].items()},
        )


def generate_task(config: TaskConfig, fallback_seed: int = 0) -> Task:
    """Materialize a task from a config (deterministic given a seed)."""
    config = config.validated()
    seed = config.seed if config.seed is not None else fallback_seed
    rng = np.random.default_rng(seed)

    if config.events is not None:
        raw_objs = list(dict.fromkeys(e.object_label for e in config.events))
        std_objs = [_object_label(i) for i in range(config.n_objects)]
        object_labels = list(dict.fromkeys(std_objs + raw_objs))

        raw_syms = list(dict.fromkeys(e.symbol_label for e in config.events))
        std_syms = [_symbol_label(i) for i in range(config.n_symbols)]
        symbol_labels = list(dict.fromkeys(std_syms + raw_syms))
    else:
        object_labels = [_object_label(i) for i in range(config.n_objects)]
        symbol_labels = [_symbol_label(i) for i in range(config.n_symbols)]

    if config.vector_source == "text":
        # Phase 02: deterministic text encoder (see core/encoder.py)
        from .encoder import encode_texts

        objects, symbols = encode_texts(
            object_labels,
            symbol_labels,
            seed,
            config.d,
            concept_similarity=config.object_similarity,
            value_similarity=config.symbol_similarity,
        )
    else:
        # Keys (objects) are flat-spectrum vectors so binding is exactly
        # invertible; values (symbols) are unit Gaussian vectors.
        keys = correlated_flat_vectors(
            rng, len(object_labels), config.d, config.object_similarity
        )
        values = correlated_vectors(
            rng, len(symbol_labels), config.d, config.symbol_similarity
        )
        objects = {label: keys[i] for i, label in enumerate(object_labels)}
        symbols = {label: values[i] for i, label in enumerate(symbol_labels)}

    initial_assignment: Dict[str, str] = {}
    if config.events is None:
        # ---- auto-generate the event sequence ---------------------------
        base = [
            (obj, sym)
            for _ in range(config.cycles)
            for obj, sym in (
                (object_labels[i], symbol_labels[i % config.n_symbols])
                for i in range(config.n_objects)
            )
        ]
        initial_assignment = {obj: sym for obj, sym in base[: config.n_objects]}

        # conflict targets: the next symbol in the pool (guaranteed != initial
        # because n_symbols >= 2 when conflicts > 0)
        conflicts = [
            (object_labels[j], symbol_labels[(j + 1) % config.n_symbols])
            for j in range(config.n_conflicts)
        ]

        seq: List[tuple[str, str]] = list(base)
        t_total = len(base)
        c_total = len(conflicts)
        for k, (obj, sym) in enumerate(conflicts):
            spread = math.ceil((k + 1) * (t_total + 1) / (c_total + 1)) - 1
            # the conflict must come strictly after the object's own first
            # write, or it would create a spurious conflict record
            first_write = next(i for i, (o, _) in enumerate(seq) if o == obj)
            pos = max(spread, first_write + 1)
            pos = min(pos, len(seq))
            seq.insert(pos, (obj, sym))

        if config.order == "randomized":
            order = list(range(len(seq)))
            rng.shuffle(order)
            seq = [seq[i] for i in order]

        event_specs: List[EventSpec] = [
            EventSpec(obj, sym, noise=config.input_noise) for obj, sym in seq
        ]
    else:
        event_specs = list(config.events)
        for spec in event_specs:
            if spec.object_label not in objects:
                raise ValueError(f"event references unknown object {spec.object_label!r}")
            if spec.symbol_label not in symbols:
                raise ValueError(f"event references unknown symbol {spec.symbol_label!r}")

    # ---- materialize events ---------------------------------------------
    events: List[Event] = []
    last_write: Dict[str, tuple[int, str]] = {}
    conflict_records: Dict[str, List[Dict[str, Any]]] = {}
    for t, spec in enumerate(event_specs):
        obj, sym = spec.object_label, spec.symbol_label
        if config.events is not None:
            # explicit events: first symbol seen per object is the "initial"
            if obj not in initial_assignment:
                initial_assignment[obj] = sym
        noise = spec.noise if spec.noise is not None else config.input_noise
        events.append(
            Event(
                id=f"e{t:04d}",
                timestep=t,
                concept_label=obj,
                attribute_label=sym,
                key_vector=objects[obj],
                value_vector=symbols[sym],
                importance=float(spec.importance),
                strength=float(spec.strength),
                noise=float(noise),
                metadata=dict(spec.metadata),
            )
        )
        if obj in last_write and last_write[obj][1] != sym:
            conflict_records.setdefault(obj, []).append(
                {
                    "old_symbol": last_write[obj][1],
                    "new_symbol": sym,
                    "timestep": t,
                }
            )
        last_write[obj] = (t, sym)

    # ---- queries ---------------------------------------------------------
    if len(events) == 0 and config.queries is None:
        query_specs = []  # nothing written, nothing to ask
    elif config.queries is not None:
        query_specs = list(config.queries)
    else:
        query_specs = []
        end = len(events) - 1
        for obj in object_labels:
            query_specs.append(QuerySpec(object_label=obj, timestep=end, kind="latest"))
        for obj, recs in conflict_records.items():
            conflict_t = recs[-1]["timestep"]
            query_specs.append(
                QuerySpec(object_label=obj, timestep=conflict_t, kind="latest")
            )
            if config.probe_original:
                query_specs.append(
                    QuerySpec(object_label=obj, timestep=end, kind="original")
                )

    queries: List[Query] = []
    for i, spec in enumerate(query_specs):
        obj = spec.object_label
        if obj not in objects:
            raise ValueError(f"query references unknown object {obj!r}")
        t = spec.timestep
        if t < 0:
            t = len(events) - 1
        if t >= len(events):
            t = len(events) - 1  # clamp: querying beyond the end is the end

        if spec.expected_symbol_label is not None:
            expected = spec.expected_symbol_label
            kind = spec.kind
        elif spec.kind == "original":
            expected = initial_assignment.get(obj)
            kind = "original"
            if expected is None:
                raise ValueError(
                    f"original query for {obj!r} but that object was never written"
                )
        else:
            # latest write at or before timestep t
            kind = "latest"
            last_ts = -1
            for j in range(t + 1):
                if events[j].concept_label == obj:
                    last_ts = j
            if last_ts < 0:
                raise ValueError(f"no write for {obj!r} at or before timestep {t}")
            expected = events[last_ts].attribute_label
        if expected not in symbols:
            raise ValueError(f"expected symbol {expected!r} unknown")
        queries.append(
            Query(
                id=f"q{i:03d}",
                timestep=t,
                object_label=obj,
                kind=kind,
                expected_attribute_label=expected,
                key_vector=objects[obj],
                expected_value_vector=symbols[expected],
            )
        )

    return Task(
        config=config.to_dict(),
        seed=seed,
        d=config.d,
        objects=objects,
        symbols=symbols,
        events=events,
        queries=queries,
        initial_assignment=initial_assignment,
        last_write=last_write,
        conflicts=conflict_records,
    )