import pytest
from core import Experiment, ExperimentConfig, run_experiment
from core.genome.centrality import CentralityAnalyzer, DependencyMatrixBuilder
from core.genome.experiments import (
    DoseResponseEngine,
    MutationEngine,
    PathDependenceEngine,
    RecoveryEngine,
)
from core.genome.fragility import (
    CriticalMemoryDetector,
    FragilityAnalyzer,
    RedundancyAnalyzer,
)
from core.genome.reports import (
    AutomaticResearchQuestionGenerator,
    ReportGenerator,
)
from core.genome.sandbox import SandboxManager
from core.genome.types import DoseResponsePattern, FragilityClassification, RecoveryStatus


@pytest.fixture
def canonical_experiment() -> Experiment:
    config = ExperimentConfig.from_api({
        "seed": 42,
        "mechanism": "interference",
        "task_name": "associative_recall",
        "d": 128,
        "num_events": 10,
    })
    return run_experiment(config)


def test_dose_response_experiment(canonical_experiment: Experiment):
    """Test 5-point dose response sweep (100% -> 0%)."""
    eval_res = DoseResponseEngine.run_dose_response(canonical_experiment, "obj_A")
    assert len(eval_res.points) == 5
    assert eval_res.points[0].dose == 1.0
    assert eval_res.points[-1].dose == 0.0
    assert eval_res.pattern in list(DoseResponsePattern)
    assert isinstance(eval_res.explanation, str)


def test_recovery_experiment(canonical_experiment: Experiment):
    """Test before-during-after intervention recovery testing."""
    rec = RecoveryEngine.test_recovery(canonical_experiment, "obj_A")
    assert rec.status in list(RecoveryStatus)
    assert rec.during_strength <= rec.baseline_strength + 0.05
    assert rec.restored_strength > rec.during_strength
    assert rec.recovery_delta >= 0.0


def test_path_dependence_experiment(canonical_experiment: Experiment):
    """Test operation sequence permutation and order sensitivity."""
    path_eval = PathDependenceEngine.test_path_dependence(canonical_experiment)
    assert len(path_eval.sequence_a) >= 2
    assert len(path_eval.sequence_b) >= 2
    assert path_eval.final_distance_l2 >= 0.0


def test_critical_memory_detector(canonical_experiment: Experiment):
    """Test finding and ranking critical memories."""
    ranks = CriticalMemoryDetector.find_critical_memories(canonical_experiment)
    assert len(ranks) >= 2
    assert all(r.impact_level in ("HIGH", "MEDIUM", "LOW") for r in ranks)
    assert ranks[0].total_cascade_impact >= ranks[-1].total_cascade_impact


def test_fragility_analyzer(canonical_experiment: Experiment):
    """Test single point of failure fragility analysis."""
    report = FragilityAnalyzer.analyze_fragility(canonical_experiment, "obj_A")
    assert report.classification in list(FragilityClassification)
    assert report.impact_ratio >= 0.0
    assert len(report.evidence) >= 3


def test_redundancy_analyzer(canonical_experiment: Experiment):
    """Test discovering redundancy compensation paths."""
    rec = RedundancyAnalyzer.analyze_redundancy(canonical_experiment, "obj_A")
    assert rec.target_memory == "e0000"
    assert isinstance(rec.has_viable_backup, bool)


def test_centrality_analyzer(canonical_experiment: Experiment):
    """Test memory graph centrality metrics."""
    records = CentralityAnalyzer.analyze_centrality(canonical_experiment)
    assert len(records) >= 2
    assert all(r.degree >= 0 for r in records)
    assert all(0.0 <= r.eigenvector_centrality <= 1.0 for r in records)


def test_dependency_matrix_builder(canonical_experiment: Experiment):
    """Test building N x N pairwise memory dependency matrices."""
    matrix_assoc = DependencyMatrixBuilder.build_matrix(canonical_experiment, "association")
    n = len(matrix_assoc.memories)
    assert len(matrix_assoc.matrix) == n
    assert len(matrix_assoc.matrix[0]) == n
    assert matrix_assoc.matrix[0][0] == 1.0

    matrix_inf = DependencyMatrixBuilder.build_matrix(canonical_experiment, "influence")
    assert len(matrix_inf.matrix) == n


def test_sandbox_and_branch_comparison(canonical_experiment: Experiment):
    """Test creating sandbox branches and comparing them side-by-side."""
    br = SandboxManager.create_branch(
        experiment=canonical_experiment,
        parent_id="base",
        intervention={"target_memory": "obj_A", "intervention_type": "remove"},
    )
    assert br.branch_id.startswith("br_")
    assert br.experiment_id == canonical_experiment.experiment_id

    branches = SandboxManager.list_branches(canonical_experiment.experiment_id)
    assert len(branches) >= 1

    comp = SandboxManager.compare_branches(
        experiment=canonical_experiment,
        intervention_a={"target_memory": "obj_A", "intervention_type": "remove"},
        intervention_b={"target_memory": "obj_B", "intervention_type": "remove"},
    )
    assert "branch_a" in comp
    assert "branch_b" in comp
    assert "common_effects" in comp


def test_reports_and_automatic_questions(canonical_experiment: Experiment):
    """Test generating structured Genome/Cascade reports and automatic questions."""
    g_rep = ReportGenerator.generate_genome_report(canonical_experiment, "obj_A")
    assert g_rep.memory_id == "e0000"
    assert "summary" in g_rep.to_dict()

    c_rep = ReportGenerator.generate_cascade_report(canonical_experiment, "obj_A", "remove")
    assert c_rep.target_memory == "e0000"
    assert c_rep.cascade_depth >= 0

    questions = AutomaticResearchQuestionGenerator.generate_questions(canonical_experiment, "obj_A")
    assert len(questions) >= 1
    assert any("?" in q for q in questions)
