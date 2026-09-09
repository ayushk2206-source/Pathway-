"""Experiment object and local persistence (section 10).

An ``Experiment`` is the complete record of one investigation: the config
that produced it, the full event history, a state snapshot after every
event, every query answer, and the computed metrics. It is fully
serializable as JSON (numpy values are converted to native Python types)
and can be saved/loaded from disk for now; shareable experiment IDs and
real persistence arrive in a later phase.

The ``experiment_id`` and ``created_at`` are the only non-computational
fields — everything else is a deterministic function of the config, which
is what makes ``/experiments/{id}/replay`` a true reconstruction.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .events import Event
from .mechanisms.base import MechanismParams
from .task import TaskConfig

SCHEMA_VERSION = 1

EXPERIMENT_DIR = Path(__file__).resolve().parent.parent / "experiments"


@dataclass
class ExperimentConfig:
    """Everything needed to reproduce an experiment, deterministically."""

    seed: int = 42
    mechanism: str = "baseline"
    params: MechanismParams = field(default_factory=MechanismParams)
    task: TaskConfig = field(default_factory=TaskConfig)
    update_steps_per_event: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": int(self.seed),
            "mechanism": self.mechanism,
            "params": self.params.to_dict(),
            "task": self.task.to_dict(),
            "update_steps_per_event": int(self.update_steps_per_event),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExperimentConfig":
        p = MechanismParams(**{k: v for k, v in d.get("params", {}).items()})
        t = TaskConfig.from_dict(d.get("task", {}))
        return cls(
            seed=int(d.get("seed", 42)),
            mechanism=str(d.get("mechanism", "baseline")),
            params=p,
            task=t,
            update_steps_per_event=int(d.get("update_steps_per_event", 1)),
        )

    @classmethod
    def from_api(cls, d: Dict[str, Any]) -> "ExperimentConfig":
        """Build from an API payload (merges with defaults per-field)."""
        seed = int(d.get("seed", 42))
        mechanism = str(d.get("mechanism", "baseline"))
        params = MechanismParams(**d.get("params", {}))
        task = TaskConfig(**d.get("task", {}))
        return cls(
            seed=seed,
            mechanism=mechanism,
            params=params,
            task=task,
            update_steps_per_event=int(d.get("update_steps_per_event", 1)),
        )


@dataclass
class Experiment:
    """The complete, serializable record of one run."""

    experiment_id: str
    seed: int
    mechanism: str
    parameters: Dict[str, Any]
    config: Dict[str, Any]
    task: Dict[str, Any]
    events: List[Dict[str, Any]]
    snapshots: List[Dict[str, Any]]
    queries: List[Dict[str, Any]]  # executed query results
    predictions: List[Dict[str, Any]]
    ground_truth: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    created_at: str
    version: int = SCHEMA_VERSION
    replay_of: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "seed": int(self.seed),
            "mechanism": self.mechanism,
            "parameters": self.parameters,
            "config": self.config,
            "task": self.task,
            "events": self.events,
            "snapshots": self.snapshots,
            "queries": self.queries,
            "predictions": self.predictions,
            "ground_truth": self.ground_truth,
            "metrics": self.metrics,
            "created_at": self.created_at,
            "version": int(self.version),
            "replay_of": self.replay_of,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Experiment":
        return cls(
            experiment_id=d["experiment_id"],
            seed=int(d["seed"]),
            mechanism=d["mechanism"],
            parameters=dict(d["parameters"]),
            config=dict(d["config"]),
            task=dict(d["task"]),
            events=list(d["events"]),
            snapshots=list(d["snapshots"]),
            queries=list(d["queries"]),
            predictions=list(d["predictions"]),
            ground_truth=list(d["ground_truth"]),
            metrics=dict(d["metrics"]),
            created_at=d["created_at"],
            version=int(d.get("version", SCHEMA_VERSION)),
            replay_of=d.get("replay_of"),
        )

    # -- convenience ------------------------------------------------------
    @property
    def num_events(self) -> int:
        return len(self.events)

    @property
    def num_snapshots(self) -> int:
        return len(self.snapshots)

    def snapshot_at(self, events_processed: int) -> Optional[Dict[str, Any]]:
        """Snapshot after ``events_processed`` events (0 = initial state)."""
        for s in self.snapshots:
            if int(s["timestep"]) == events_processed:
                return s
        return None

    def query_results_for(self, object_label: str) -> List[Dict[str, Any]]:
        return [q for q in self.queries if q.get("object_label") == object_label]


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_experiment(
    *,
    seed: int,
    mechanism: str,
    params: MechanismParams,
    task_dict: Dict[str, Any],
    config_dict: Dict[str, Any],
    events: List[Dict[str, Any]],
    snapshots: List[Dict[str, Any]],
    queries: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    replay_of: Optional[str] = None,
) -> Experiment:
    """Assemble an ``Experiment`` (used by the runner)."""
    return Experiment(
        experiment_id=_new_id(),
        seed=int(seed),
        mechanism=mechanism,
        parameters=params.to_dict(),
        config=config_dict,
        task=task_dict,
        events=events,
        snapshots=snapshots,
        queries=queries,
        predictions=predictions,
        ground_truth=ground_truth,
        metrics=metrics,
        created_at=_now_iso(),
        replay_of=replay_of,
    )


# ---------------------------------------------------------------------------
# JSON persistence (local, for now)
# ---------------------------------------------------------------------------
def _json_default(o: Any) -> Any:
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, float)):
        return float(o)
    if isinstance(o, (np.integer, int)):
        return int(o)
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    raise TypeError(f"not JSON serializable: {type(o)!r}")


def experiment_to_json(exp: Experiment, indent: int = 2) -> str:
    return json.dumps(exp.to_dict(), indent=indent, default=_json_default)


def save_experiment(exp: Experiment, path: Optional[Path] = None) -> Path:
    """Save an experiment as JSON locally; returns the file path."""
    path = Path(path) if path else EXPERIMENT_DIR / f"{exp.experiment_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(experiment_to_json(exp), encoding="utf-8")
    return path


def load_experiment(path: Path) -> Experiment:
    """Load an experiment from a JSON file on disk."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Experiment.from_dict(data)


def dict_to_json(data: Dict[str, Any], indent: int = 2) -> str:
    return json.dumps(data, indent=indent, default=_json_default)


def strip_non_deterministic(exp_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return the experiment dict with wall-clock/id fields removed.

    Used by the determinism tests: two runs with the same config must have
    identical stripped dicts. Removes ``created_at``/``experiment_id``/
    ``replay_of`` and every event ``timestamp`` (including inside the
    embedded task record).
    """
    out = {k: v for k, v in exp_dict.items() if k not in ("created_at", "experiment_id", "replay_of")}

    def _strip_events(events):
        for ev in events or []:
            ev.pop("timestamp", None)

    _strip_events(out.get("events"))
    task = out.get("task")
    if isinstance(task, dict):
        _strip_events(task.get("events"))
    return out