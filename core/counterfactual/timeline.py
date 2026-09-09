"""Timeline representation and branching tree models for Counterfactual Memory Archaeology (Phase 04)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from .types import BranchType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
class Timeline:
    """An immutable, ordered historical event-and-state trajectory."""

    timeline_id: str = field(default_factory=lambda: f"time-{uuid.uuid4().hex[:8]}")
    parent_timeline_id: Optional[str] = None
    experiment_id: str = ""
    branch_point: Optional[int] = None
    branch_metadata: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    snapshots: List[Dict[str, Any]] = field(default_factory=list)
    queries: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    is_original: bool = False

    @property
    def length(self) -> int:
        return len(self.events)

    def get_event(self, identifier: int | str) -> Optional[Dict[str, Any]]:
        if isinstance(identifier, int):
            if 0 <= identifier < len(self.events):
                return self.events[identifier]
            return None
        for ev in self.events:
            if ev.get("id") == identifier:
                return ev
        return None

    def get_snapshot_at(self, timestep: int) -> Optional[Dict[str, Any]]:
        for s in self.snapshots:
            if int(s.get("timestep", -1)) == timestep:
                return s
        return None

    def get_state_at(self, timestep: int) -> Optional[np.ndarray]:
        snap = self.get_snapshot_at(timestep)
        if snap and "state_vector" in snap and snap["state_vector"] is not None:
            return np.asarray(snap["state_vector"], dtype=np.float64)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "parent_timeline_id": self.parent_timeline_id,
            "experiment_id": self.experiment_id,
            "branch_point": self.branch_point,
            "branch_metadata": _sanitize(self.branch_metadata),
            "events": _sanitize(self.events),
            "snapshots": _sanitize(self.snapshots),
            "queries": _sanitize(self.queries),
            "metrics": _sanitize(self.metrics),
            "created_at": self.created_at,
            "is_original": self.is_original,
            "length": self.length,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Timeline":
        return cls(
            timeline_id=d.get("timeline_id", f"time-{uuid.uuid4().hex[:8]}"),
            parent_timeline_id=d.get("parent_timeline_id"),
            experiment_id=d.get("experiment_id", ""),
            branch_point=d.get("branch_point"),
            branch_metadata=dict(d.get("branch_metadata", {})),
            events=list(d.get("events", [])),
            snapshots=list(d.get("snapshots", [])),
            queries=list(d.get("queries", [])),
            metrics=dict(d.get("metrics", {})),
            created_at=d.get("created_at", _now_iso()),
            is_original=bool(d.get("is_original", False)),
        )


@dataclass
class TimelineNode:
    """A node in a branching timeline tree for visualization and provenance."""

    node_id: str
    parent_id: Optional[str]
    timeline_id: str
    history_id: str
    label: str
    branch_type: BranchType = BranchType.ROOT
    branch_point: Optional[int] = None
    intervention: Optional[Dict[str, Any]] = None
    state_summary: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    divergence_from_parent: Optional[float] = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "timeline_id": self.timeline_id,
            "history_id": self.history_id,
            "label": self.label,
            "branch_type": self.branch_type.value if isinstance(self.branch_type, BranchType) else str(self.branch_type),
            "branch_point": self.branch_point,
            "intervention": _sanitize(self.intervention),
            "state_summary": _sanitize(self.state_summary),
            "metrics": _sanitize(self.metrics),
            "divergence_from_parent": self.divergence_from_parent,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TimelineNode":
        btype = d.get("branch_type", BranchType.ROOT)
        if isinstance(btype, str):
            btype = BranchType(btype)
        return cls(
            node_id=d["node_id"],
            parent_id=d.get("parent_id"),
            timeline_id=d.get("timeline_id", ""),
            history_id=d.get("history_id", ""),
            label=d.get("label", ""),
            branch_type=btype,
            branch_point=d.get("branch_point"),
            intervention=d.get("intervention"),
            state_summary=dict(d.get("state_summary", {})),
            metrics=dict(d.get("metrics", {})),
            divergence_from_parent=d.get("divergence_from_parent"),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class CounterfactualTree:
    """A tree structure organizing all counterfactual branches rooted in an original timeline."""

    root_id: Optional[str] = None
    nodes: Dict[str, TimelineNode] = field(default_factory=dict)

    def add_node(self, node: TimelineNode) -> None:
        self.nodes[node.node_id] = node
        if self.root_id is None and node.parent_id is None:
            self.root_id = node.node_id

    def get_node(self, node_id: str) -> Optional[TimelineNode]:
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[TimelineNode]:
        return [n for n in self.nodes.values() if n.parent_id == node_id]

    def get_path_from_root(self, node_id: str) -> List[TimelineNode]:
        path: List[TimelineNode] = []
        curr = self.nodes.get(node_id)
        while curr:
            path.insert(0, curr)
            if not curr.parent_id:
                break
            curr = self.nodes.get(curr.parent_id)
        return path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_id": self.root_id,
            "total_nodes": len(self.nodes),
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CounterfactualTree":
        tree = cls(root_id=d.get("root_id"))
        for nd in d.get("nodes", []):
            node = TimelineNode.from_dict(nd)
            tree.nodes[node.node_id] = node
        return tree
