"""Experiment and hypothesis lineage graph for Experiment Lab (Phase 03).

Tracks the full provenance and evolution of scientific inquiry:
Experiment -> Hypothesis -> Experiment -> Contradiction -> New Hypothesis.
Supports graph serialization, parent-child versioning, and visual graph layout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class EdgeType(str, Enum):
    TESTS = "tests"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    FOLLOWS_FROM = "follows_from"
    REPRODUCES = "reproduces"
    REFINES = "refines"
    ASKED = "asked"
    CHALLENGES = "challenges"
    DERIVED_FROM = "derived_from"
    FOLLOWS = "follows"
    REQUIRES = "requires"


class NodeType(str, Enum):
    EXPERIMENT = "experiment"
    HYPOTHESIS = "hypothesis"
    FINDING = "finding"
    QUESTION = "question"
    COUNTERFACTUAL = "counterfactual"
    OBSERVATION = "observation"
    AGENT_ANALYSIS = "agent_analysis"
    DISAGREEMENT = "disagreement"
    CONCLUSION = "conclusion"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GraphNode":
        return cls(
            node_id=d["node_id"],
            node_type=NodeType(d["node_type"]),
            label=d["label"],
            metadata=d.get("metadata", {}),
            created_at=d.get("created_at", _now_iso()),
        )


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GraphEdge":
        return cls(
            source_id=d["source_id"],
            target_id=d["target_id"],
            edge_type=EdgeType(d["edge_type"]),
            metadata=d.get("metadata", {}),
            created_at=d.get("created_at", _now_iso()),
        )


class ExperimentGraph:
    """Directed graph tracking research experiments, hypotheses, and findings."""

    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_node(self, node: GraphNode) -> GraphNode:
        self.nodes[node.node_id] = node
        return node

    def add_experiment_node(
        self, experiment_id: str, title: str, metadata: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        node = GraphNode(
            node_id=experiment_id,
            node_type=NodeType.EXPERIMENT,
            label=title,
            metadata=metadata or {},
        )
        return self.add_node(node)

    def add_hypothesis_node(
        self, hypothesis_id: str, statement: str, metadata: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        node = GraphNode(
            node_id=hypothesis_id,
            node_type=NodeType.HYPOTHESIS,
            label=statement,
            metadata=metadata or {},
        )
        return self.add_node(node)

    def add_finding_node(
        self, finding_id: str, finding_text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        node = GraphNode(
            node_id=finding_id,
            node_type=NodeType.FINDING,
            label=finding_text,
            metadata=metadata or {},
        )
        return self.add_node(node)

    def add_edge(
        self,
        source_id: Union[str, GraphEdge],
        target_id: Optional[str] = None,
        edge_type: Optional[EdgeType] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphEdge:
        if isinstance(source_id, GraphEdge):
            edge = source_id
        else:
            edge = GraphEdge(
                source_id=source_id,
                target_id=target_id or "",
                edge_type=edge_type or EdgeType.TESTS,
                metadata=metadata or {},
            )
        self.edges.append(edge)
        return edge

    def get_ancestors(self, node_id: str) -> List[str]:
        """Traverse upstream parents."""
        visited: Set[str] = set()
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            for edge in self.edges:
                if edge.target_id == curr and edge.source_id not in visited:
                    visited.add(edge.source_id)
                    queue.append(edge.source_id)
        return list(visited)

    def get_descendants(self, node_id: str) -> List[str]:
        """Traverse downstream children."""
        visited: Set[str] = set()
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            for edge in self.edges:
                if edge.source_id == curr and edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append(edge.target_id)
        return list(visited)

    def get_connected_nodes(self, node_id: str) -> List[str]:
        """Traverse weakly connected component (undirected)."""
        visited: Set[str] = {node_id}
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            for edge in self.edges:
                neighbor = None
                if edge.source_id == curr:
                    neighbor = edge.target_id
                elif edge.target_id == curr:
                    neighbor = edge.source_id
                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return list(visited)

    def get_lineage(self, node_id: str) -> Dict[str, Any]:
        """Get the full sub-graph connected to node_id."""
        ancestors = set(self.get_ancestors(node_id))
        descendants = set(self.get_descendants(node_id))
        connected = set(self.get_connected_nodes(node_id))
        relevant_ids = ancestors | descendants | connected | {node_id}

        sub_nodes = [n.to_dict() for nid, n in self.nodes.items() if nid in relevant_ids]
        sub_edges = [
            e.to_dict()
            for e in self.edges
            if e.source_id in relevant_ids and e.target_id in relevant_ids
        ]

        return {
            "root_node_id": node_id,
            "nodes": sub_nodes,
            "edges": sub_edges,
            "ancestor_count": len(ancestors),
            "descendant_count": len(descendants),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExperimentGraph":
        graph = cls()
        for nd in d.get("nodes", []):
            node = GraphNode.from_dict(nd)
            graph.nodes[node.node_id] = node
        for ed in d.get("edges", []):
            edge = GraphEdge.from_dict(ed)
            graph.edges.append(edge)
        return graph
