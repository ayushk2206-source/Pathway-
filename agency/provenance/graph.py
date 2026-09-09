"""Research graph construction for multi-agent investigation lineage (Phase 05)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.lab.lineage import EdgeType, ExperimentGraph, GraphEdge, GraphNode, NodeType


class ResearchGraphBuilder:
    """Extends the laboratory lineage graph with multi-agent research inquiry nodes and edges."""

    def __init__(self, base_graph: Optional[ExperimentGraph] = None) -> None:
        self.graph = base_graph or ExperimentGraph()

    def add_question(self, question_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> GraphNode:
        node = GraphNode(
            node_id=question_id,
            node_type=NodeType.QUESTION,
            label=text[:60] + ("..." if len(text) > 60 else ""),
            metadata=metadata or {"full_text": text},
        )
        return self.graph.add_node(node)

    def add_hypothesis(
        self,
        hypothesis_id: str,
        label: str,
        question_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = self.graph.add_hypothesis_node(hypothesis_id, label, metadata=metadata)
        if question_id:
            self.graph.add_edge(GraphEdge(
                source_id=question_id,
                target_id=hypothesis_id,
                edge_type=EdgeType.DERIVED_FROM,
            ))
        return node

    def add_experiment(
        self,
        experiment_id: str,
        label: str,
        hypothesis_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = self.graph.add_experiment_node(experiment_id, label, metadata=metadata)
        if hypothesis_id:
            self.graph.add_edge(GraphEdge(
                source_id=experiment_id,
                target_id=hypothesis_id,
                edge_type=EdgeType.TESTS,
            ))
        return node

    def add_observation(
        self,
        observation_id: str,
        label: str,
        experiment_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            node_id=observation_id,
            node_type=NodeType.OBSERVATION,
            label=label,
            metadata=metadata or {},
        )
        self.graph.add_node(node)
        self.graph.add_edge(GraphEdge(
            source_id=observation_id,
            target_id=experiment_id,
            edge_type=EdgeType.DERIVED_FROM,
        ))
        return node

    def add_agent_analysis(
        self,
        analysis_id: str,
        agent_name: str,
        target_id: str,
        verdict: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            node_id=analysis_id,
            node_type=NodeType.AGENT_ANALYSIS,
            label=f"{agent_name}: {verdict}",
            metadata=metadata or {"agent": agent_name, "verdict": verdict},
        )
        self.graph.add_node(node)
        edge_type = EdgeType.SUPPORTS if verdict.lower() == "supported" else EdgeType.CHALLENGES
        self.graph.add_edge(GraphEdge(
            source_id=analysis_id,
            target_id=target_id,
            edge_type=edge_type,
        ))
        return node

    def add_disagreement(
        self,
        disagreement_id: str,
        label: str,
        source_analysis_id: str,
        target_analysis_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            node_id=disagreement_id,
            node_type=NodeType.DISAGREEMENT,
            label=label,
            metadata=metadata or {},
        )
        self.graph.add_node(node)
        self.graph.add_edge(GraphEdge(
            source_id=disagreement_id,
            target_id=source_analysis_id,
            edge_type=EdgeType.CHALLENGES,
        ))
        self.graph.add_edge(GraphEdge(
            source_id=disagreement_id,
            target_id=target_analysis_id,
            edge_type=EdgeType.CHALLENGES,
        ))
        return node

    def add_counterfactual(
        self,
        counterfactual_id: str,
        label: str,
        parent_experiment_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            node_id=counterfactual_id,
            node_type=NodeType.COUNTERFACTUAL,
            label=label,
            metadata=metadata or {},
        )
        self.graph.add_node(node)
        self.graph.add_edge(GraphEdge(
            source_id=counterfactual_id,
            target_id=parent_experiment_id,
            edge_type=EdgeType.FOLLOWS,
        ))
        return node

    def add_conclusion(
        self,
        conclusion_id: str,
        label: str,
        supporting_node_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            node_id=conclusion_id,
            node_type=NodeType.CONCLUSION,
            label=label,
            metadata=metadata or {},
        )
        self.graph.add_node(node)
        for supp_id in supporting_node_ids:
            if supp_id in self.graph.nodes:
                self.graph.add_edge(GraphEdge(
                    source_id=conclusion_id,
                    target_id=supp_id,
                    edge_type=EdgeType.SUPPORTS,
                ))
        return node

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.graph.nodes.items()},
            "edges": [e.to_dict() for e in self.graph.edges],
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
        }
