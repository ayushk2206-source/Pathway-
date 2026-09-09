"""Tests for Experiment Lineage, Diffing, Export, and Queue (Phase 03)."""

import pytest

from core.lab.diff import diff_lab_experiments
from core.lab.export import export_experiment_csv, export_experiment_json
from core.lab.lineage import EdgeType, ExperimentGraph, NodeType
from core.lab.models import ConditionResult, ExperimentStatus, LabExperiment, SweepResult
from core.lab.queue import ExperimentQueue


def test_lineage_graph_traversal():
    graph = ExperimentGraph()

    e1 = graph.add_experiment_node("exp-01", "Baseline Study")
    h1 = graph.add_hypothesis_node("hyp-01", "Similarity drives decay")
    e2 = graph.add_experiment_node("exp-02", "Replication Study")

    graph.add_edge("exp-01", "hyp-01", EdgeType.SUPPORTS)
    graph.add_edge("exp-02", "hyp-01", EdgeType.TESTS)

    # Lineage lookup
    lin = graph.get_lineage("hyp-01")
    assert lin["ancestor_count"] == 2
    assert any(n["node_id"] == "exp-01" for n in lin["nodes"])
    assert any(n["node_id"] == "exp-02" for n in lin["nodes"])

    # Serialization roundtrip
    d = graph.to_dict()
    g_rebuilt = ExperimentGraph.from_dict(d)
    assert len(g_rebuilt.nodes) == 3
    assert len(g_rebuilt.edges) == 2


def test_diff_lab_experiments():
    exp1 = LabExperiment(
        experiment_id="exp-1",
        title="Exp 1",
        research_question="Q1",
        baseline_configuration={"decay": 0.1, "state_dim": 64},
        metrics={"recall_accuracy": 0.9, "memory_retention": 0.8},
    )
    exp2 = LabExperiment(
        experiment_id="exp-2",
        title="Exp 2",
        research_question="Q2",
        baseline_configuration={"decay": 0.5, "state_dim": 64},
        metrics={"recall_accuracy": 0.7, "memory_retention": 0.4},
    )

    diff = diff_lab_experiments(exp1, exp2)

    assert diff["is_identical"] is False
    assert "decay" in diff["parameter_changes"]
    assert diff["parameter_changes"]["decay"]["old"] == 0.1
    assert diff["parameter_changes"]["decay"]["new"] == 0.5

    assert "recall_accuracy" in diff["metric_changes"]
    assert diff["metric_changes"]["recall_accuracy"]["delta"] == pytest.approx(-0.2)


def test_export_dataset_json_and_csv():
    cond1 = ConditionResult("decay=0.1", {"decay": 0.1}, aggregated_metrics={"memory_retention": {"mean": 0.85}})
    cond2 = ConditionResult("decay=0.5", {"decay": 0.5}, aggregated_metrics={"memory_retention": {"mean": 0.45}})

    exp = LabExperiment(
        experiment_id="exp-sweep-export",
        title="Export Test",
        research_question="Q",
        mechanism="leaky",
        results=SweepResult("decay", [0.1, 0.5], [cond1, cond2]),
    )

    json_str = export_experiment_json(exp)
    assert "exp-sweep-export" in json_str
    assert "decay=0.1" in json_str

    csv_str = export_experiment_csv(exp)
    lines = csv_str.strip().splitlines()
    assert len(lines) >= 3  # Header + 2 rows
    assert "experiment_id" in lines[0]
    assert "param_decay" in lines[0]
    assert "0.1" in lines[1]
    assert "0.5" in lines[2]


def test_experiment_queue_lifecycle():
    queue = ExperimentQueue()
    exp = LabExperiment(
        experiment_id="q-exp-1",
        title="Queue Test",
        research_question="Will queue execute?",
    )

    item = queue.enqueue(exp)
    assert item.status == ExperimentStatus.QUEUED
    assert queue.pending_count() == 1

    # Execute
    def dummy_runner(e: LabExperiment) -> LabExperiment:
        e.conclusion = "Executed via queue."
        return e

    completed_item = queue.run_next(dummy_runner)
    assert completed_item is not None
    assert completed_item.status == ExperimentStatus.COMPLETED
    assert completed_item.experiment.status == ExperimentStatus.COMPLETED
    assert queue.pending_count() == 0
