"""Local experiment store for Phase 01/02 and Phase 03 Experiment Lab.

Experiments are persisted as JSON files in ``experiments/`` and mirrored in
memory. Preserves complete compatibility with Phase 01/02 while extending
storage for LabExperiment, Hypothesis, and ExperimentGraph.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from core import Experiment
from core.experiment import EXPERIMENT_DIR
from core.lab import ExperimentGraph, Hypothesis, LabExperiment
from core.counterfactual import (
    BranchType,
    CounterfactualExperiment,
    CounterfactualTree,
    TimelineNode,
)
from agency.orchestration.investigation import Investigation
from core.causal import (
    CausalClaim,
    CausalLedger,
    CausalQueueManager,
    CausalReport,
    CausalScenario,
    ContradictionEngine,
)


class ExperimentStore:
    def __init__(self, directory: Optional[Path] = None) -> None:
        self.directory = Path(directory) if directory else EXPERIMENT_DIR
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lab_dir = self.directory / "lab"
        self.lab_dir.mkdir(parents=True, exist_ok=True)
        self.hyp_dir = self.directory / "hypotheses"
        self.hyp_dir.mkdir(parents=True, exist_ok=True)
        self.cf_dir = self.directory / "counterfactuals"
        self.cf_dir.mkdir(parents=True, exist_ok=True)
        self.inv_dir = self.directory / "investigations"
        self.inv_dir.mkdir(parents=True, exist_ok=True)
        self.causal_dir = self.directory / "causal"
        self.causal_dir.mkdir(parents=True, exist_ok=True)
        self.causal_reports_dir = self.causal_dir / "reports"
        self.causal_reports_dir.mkdir(parents=True, exist_ok=True)

        self._experiments: Dict[str, Experiment] = {}
        self._lab_experiments: Dict[str, LabExperiment] = {}
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._counterfactuals: Dict[str, CounterfactualExperiment] = {}
        self._trees: Dict[str, CounterfactualTree] = {}
        self._investigations: Dict[str, Investigation] = {}
        self._graph: ExperimentGraph = ExperimentGraph()
        self._causal_ledger: CausalLedger = CausalLedger()
        self._contradiction_engine: ContradictionEngine = ContradictionEngine()
        self._causal_queue_manager: CausalQueueManager = CausalQueueManager()
        self._causal_reports: Dict[str, CausalReport] = {}
        self._causal_scenarios: Dict[str, CausalScenario] = {}

        self._load_disk()

    def _load_disk(self) -> None:
        # 1. Base experiments
        for f in sorted(self.directory.glob("*.json")):
            if f.is_file() and not f.name.startswith("graph"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if "snapshots" in data:
                        self._experiments[data["experiment_id"]] = Experiment.from_dict(data)
                except Exception:
                    continue

        # 2. Lab experiments
        for f in sorted(self.lab_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._lab_experiments[data["experiment_id"]] = LabExperiment.from_dict(data)
            except Exception:
                continue

        # 3. Hypotheses
        for f in sorted(self.hyp_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._hypotheses[data["hypothesis_id"]] = Hypothesis.from_dict(data)
            except Exception:
                continue

        # 4. Counterfactuals
        for f in sorted(self.cf_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                cf_obj = CounterfactualExperiment.from_dict(data)
                self._counterfactuals[cf_obj.counterfactual_id] = cf_obj
                self._index_counterfactual_tree(cf_obj)
            except Exception:
                continue

        # 5. Investigations
        for f in sorted(self.inv_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._investigations[data["investigation_id"]] = Investigation.from_dict(data)
            except Exception:
                continue

        # 6. Graph
        graph_path = self.directory / "lineage_graph.json"
        if graph_path.exists():
            try:
                data = json.loads(graph_path.read_text(encoding="utf-8"))
                self._graph = ExperimentGraph.from_dict(data)
            except Exception:
                pass

        # 7. Causal Ledger
        ledger_path = self.causal_dir / "ledger.json"
        if ledger_path.exists():
            try:
                data = json.loads(ledger_path.read_text(encoding="utf-8"))
                self._causal_ledger = CausalLedger.from_dict(data)
            except Exception:
                pass

        # 8. Causal Reports
        for f in sorted(self.causal_reports_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                rep = CausalReport(
                    report_id=data.get("report_id", ""),
                    experiment_id=data.get("experiment_id", ""),
                    question=data.get("question", ""),
                    scenario=data.get("scenario", {}),
                    baseline=data.get("baseline", {}),
                    intervention=data.get("intervention", {}),
                    temporal_window=data.get("temporal_window"),
                    first_divergence=data.get("first_divergence"),
                    cascade=data.get("cascade", {}),
                    effect=data.get("effect", {}),
                    alternative_paths=data.get("alternative_paths", []),
                    replication=data.get("replication", {}),
                    limitations=data.get("limitations", []),
                    conclusion=data.get("conclusion", ""),
                    created_at=data.get("created_at", ""),
                )
                self._causal_reports[rep.report_id] = rep
            except Exception:
                continue

    # --- Phase 01 / 02 Experiment methods ---
    def save(self, experiment: Experiment) -> Experiment:
        path = self.directory / f"{experiment.experiment_id}.json"
        path.write_text(json.dumps(experiment.to_dict(), indent=2), encoding="utf-8")
        self._experiments[experiment.experiment_id] = experiment
        return experiment

    def get(self, experiment_id: str) -> Optional[Experiment]:
        return self._experiments.get(experiment_id)

    def list_ids(self) -> List[str]:
        return sorted(self._experiments.keys())

    # --- Phase 03 LabExperiment methods ---
    def save_lab_experiment(self, experiment: LabExperiment) -> LabExperiment:
        path = self.lab_dir / f"{experiment.experiment_id}.json"
        path.write_text(json.dumps(experiment.to_dict(), indent=2), encoding="utf-8")
        self._lab_experiments[experiment.experiment_id] = experiment

        # Automatically record into lineage graph
        self._graph.add_experiment_node(
            experiment_id=experiment.experiment_id,
            title=experiment.title,
            metadata={
                "research_question": experiment.research_question,
                "mechanism": experiment.mechanism,
                "status": experiment.status.value,
                "version": experiment.version,
            },
        )
        self.save_graph()
        return experiment

    def get_lab_experiment(self, experiment_id: str) -> Optional[LabExperiment]:
        return self._lab_experiments.get(experiment_id)

    def list_lab_experiments(self) -> List[LabExperiment]:
        return list(self._lab_experiments.values())

    def list_lab_experiment_ids(self) -> List[str]:
        return sorted(self._lab_experiments.keys())

    # --- Phase 03 Hypothesis methods ---
    def save_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        path = self.hyp_dir / f"{hypothesis.hypothesis_id}.json"
        path.write_text(json.dumps(hypothesis.to_dict(), indent=2), encoding="utf-8")
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis

        # Automatically record into lineage graph
        self._graph.add_hypothesis_node(
            hypothesis_id=hypothesis.hypothesis_id,
            statement=hypothesis.statement,
            metadata={
                "status": hypothesis.status.value,
                "confidence": hypothesis.confidence_after,
            },
        )
        self.save_graph()
        return hypothesis

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        return self._hypotheses.get(hypothesis_id)

    def list_hypotheses(self) -> List[Hypothesis]:
        return list(self._hypotheses.values())

    # --- Lineage Graph methods ---
    def get_graph(self) -> ExperimentGraph:
        return self._graph

    def save_graph(self) -> None:
        path = self.directory / "lineage_graph.json"
        try:
            path.write_text(json.dumps(self._graph.to_dict(), indent=2), encoding="utf-8")
        except Exception:
            pass

    # --- Phase 04 Counterfactual methods ---
    def _index_counterfactual_tree(self, cf: CounterfactualExperiment) -> None:
        root_id = cf.parent_experiment_id or cf.counterfactual_id
        tree = self._trees.get(root_id)
        if not tree:
            tree = CounterfactualTree(root_id=root_id)
            root_node = TimelineNode(
                node_id=root_id,
                parent_id=None,
                timeline_id=root_id,
                history_id=root_id,
                label=f"Root History ({root_id})",
                branch_type=BranchType.ROOT,
            )
            tree.add_node(root_node)
            self._trees[root_id] = tree

        b_type = BranchType.ABLATION if cf.intervention_type == "remove_event" else BranchType.SURGERY
        branch_node = TimelineNode(
            node_id=cf.counterfactual_id,
            parent_id=cf.parent_experiment_id,
            timeline_id=cf.counterfactual_id,
            history_id=cf.parent_history_id or cf.parent_experiment_id,
            label=cf.title,
            branch_type=b_type,
            branch_point=cf.provenance.get("branch_point"),
            intervention=cf.intervention,
            metrics=cf.counterfactual_result.get("metrics", {}),
            divergence_from_parent=cf.comparison.get("state_distance_l2"),
            created_at=cf.created_at,
        )
        tree.add_node(branch_node)

    def save_counterfactual(self, cf: CounterfactualExperiment) -> CounterfactualExperiment:
        path = self.cf_dir / f"{cf.counterfactual_id}.json"
        path.write_text(json.dumps(cf.to_dict(), indent=2), encoding="utf-8")
        self._counterfactuals[cf.counterfactual_id] = cf
        self._index_counterfactual_tree(cf)

        # Record in lineage graph
        try:
            self._graph.add_experiment_node(
                experiment_id=cf.counterfactual_id,
                title=cf.title,
                metadata={
                    "type": "counterfactual",
                    "intervention_type": cf.intervention_type,
                    "parent": cf.parent_experiment_id,
                },
            )
            from core.lab import EdgeType
            self._graph.add_edge(
                source_id=cf.parent_experiment_id,
                target_id=cf.counterfactual_id,
                edge_type=EdgeType.FOLLOWS_FROM,
                metadata={"intervention": cf.intervention_type},
            )
            self.save_graph()
        except Exception:
            pass

        return cf

    def get_counterfactual(self, cf_id: str) -> Optional[CounterfactualExperiment]:
        return self._counterfactuals.get(cf_id)

    def list_counterfactuals(self, parent_id: Optional[str] = None) -> List[CounterfactualExperiment]:
        if parent_id:
            return [cf for cf in self._counterfactuals.values() if cf.parent_experiment_id == parent_id]
        return list(self._counterfactuals.values())

    def get_counterfactual_tree(self, history_id: str) -> CounterfactualTree:
        if history_id in self._trees:
            return self._trees[history_id]
        # Return empty or single-node tree
        tree = CounterfactualTree(root_id=history_id)
        tree.add_node(
            TimelineNode(
                node_id=history_id,
                parent_id=None,
                timeline_id=history_id,
                history_id=history_id,
                label=f"Root History ({history_id})",
                branch_type=BranchType.ROOT,
            )
        )
        return tree

    # --- Phase 05 Investigation methods ---
    def save_investigation(self, inv: Investigation) -> Investigation:
        path = self.inv_dir / f"{inv.investigation_id}.json"
        path.write_text(json.dumps(inv.to_dict(), indent=2), encoding="utf-8")
        self._investigations[inv.investigation_id] = inv
        return inv

    def get_investigation(self, inv_id: str) -> Optional[Investigation]:
        return self._investigations.get(inv_id)

    def list_investigations(self) -> List[Investigation]:
        return list(self._investigations.values())

    # --- Phase 10 Causal Memory Lab methods ---
    def get_causal_ledger(self) -> CausalLedger:
        return self._causal_ledger

    def save_causal_ledger(self) -> None:
        path = self.causal_dir / "ledger.json"
        path.write_text(json.dumps(self._causal_ledger.to_dict(), indent=2), encoding="utf-8")

    def get_contradiction_engine(self) -> ContradictionEngine:
        return self._contradiction_engine

    def get_causal_queue_manager(self) -> CausalQueueManager:
        return self._causal_queue_manager

    def save_causal_scenario(self, scenario: CausalScenario) -> CausalScenario:
        self._causal_scenarios[scenario.scenario_id] = scenario
        return scenario

    def get_causal_scenario(self, scenario_id: str) -> Optional[CausalScenario]:
        return self._causal_scenarios.get(scenario_id)

    def list_causal_scenarios(self, experiment_id: Optional[str] = None) -> List[CausalScenario]:
        if experiment_id:
            return [s for s in self._causal_scenarios.values() if s.experiment_id == experiment_id]
        return list(self._causal_scenarios.values())

    def save_causal_report(self, report: CausalReport) -> CausalReport:
        path = self.causal_reports_dir / f"{report.report_id}.json"
        path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        self._causal_reports[report.report_id] = report
        return report

    def get_causal_report(self, report_id: str) -> Optional[CausalReport]:
        return self._causal_reports.get(report_id)

    def list_causal_reports(self, experiment_id: Optional[str] = None) -> List[CausalReport]:
        if experiment_id:
            return [r for r in self._causal_reports.values() if r.experiment_id == experiment_id]
        return list(self._causal_reports.values())