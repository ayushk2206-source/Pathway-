"""Investigation store, notebook persistence, reproducibility, and diffing (Phase 07)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from core.experiment import Experiment
from .models import (
    DiscoveryObservation,
    Investigation,
    NotebookEntry,
    TestResult,
)
from .testing import TestRunner
from .types import InvestigationStatus


class InvestigationStore:
    """In-memory persistence and management for investigations, notebooks, and discoveries."""

    def __init__(self) -> None:
        self._investigations: Dict[str, Investigation] = {}
        self._notebooks: Dict[str, List[NotebookEntry]] = {}  # exp_id -> list
        self._discoveries: List[DiscoveryObservation] = []

    def save_investigation(self, inv: Investigation) -> None:
        if not inv.created_at:
            inv.created_at = datetime.now(timezone.utc).isoformat()
        self._investigations[inv.investigation_id] = inv

    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        return self._investigations.get(investigation_id)

    def list_investigations(self, experiment_id: Optional[str] = None) -> List[Investigation]:
        invs = list(self._investigations.values())
        if experiment_id:
            invs = [i for i in invs if i.experiment_id == experiment_id]
        return sorted(invs, key=lambda x: x.created_at, reverse=True)

    def save_notebook_entry(self, entry: NotebookEntry) -> None:
        if not entry.timestamp:
            entry.timestamp = datetime.now(timezone.utc).isoformat()
        if entry.experiment_id not in self._notebooks:
            self._notebooks[entry.experiment_id] = []
        self._notebooks[entry.experiment_id].append(entry)

    def get_notebook_entries(self, experiment_id: str) -> List[NotebookEntry]:
        return self._notebooks.get(experiment_id, [])

    def add_discoveries(self, discoveries: List[DiscoveryObservation]) -> None:
        self._discoveries.extend(discoveries)

    def get_discovery_feed(self, limit: int = 50) -> List[DiscoveryObservation]:
        return self._discoveries[-limit:]

    def reproduce_investigation(
        self,
        investigation_id: str,
        experiment: Experiment,
    ) -> Investigation:
        """Deterministically reproduce an investigation and re-verify its counterfactual tests."""
        orig = self._investigations.get(investigation_id)
        if not orig:
            raise KeyError(f"Investigation {investigation_id} not found")

        reproduced = Investigation(
            investigation_id=f"repro-{uuid.uuid4().hex[:8]}",
            experiment_id=experiment.experiment_id,
            question=orig.question,
            intent=orig.intent,
            target_memory=orig.target_memory,
            target_event=orig.target_event,
            observations=orig.observations,
            candidate_hypotheses=orig.candidate_hypotheses,
            tests=orig.tests,
            status=InvestigationStatus.TESTING,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        results: List[TestResult] = []
        for test in reproduced.tests:
            # find corresponding hypothesis
            hyp = next(
                (h for h in reproduced.candidate_hypotheses if h.hypothesis_id == test.hypothesis_id),
                reproduced.candidate_hypotheses[0] if reproduced.candidate_hypotheses else None,
            )
            if hyp:
                res, chain = TestRunner.run_test(experiment, hyp, test)
                results.append(res)
                reproduced.evidence_chain.append(chain)

        reproduced.results = results
        reproduced.status = InvestigationStatus.CONFIRMED if results else InvestigationStatus.INCONCLUSIVE
        reproduced.scorecard = self.build_scorecard(reproduced)

        self.save_investigation(reproduced)
        return reproduced

    def diff_investigations(self, inv_a_id: str, inv_b_id: str) -> Dict[str, Any]:
        """Compare two investigations side-by-side."""
        inv_a = self.get_investigation(inv_a_id)
        inv_b = self.get_investigation(inv_b_id)
        if not inv_a or not inv_b:
            raise KeyError("One or both investigations not found")

        a_results = {r.test_id: r for r in inv_a.results}
        b_results = {r.test_id: r for r in inv_b.results}

        divergence_deltas = {}
        for tid, r_a in a_results.items():
            if tid in b_results:
                r_b = b_results[tid]
                divergence_deltas[tid] = {
                    "divergence_mag_diff": r_b.divergence_magnitude - r_a.divergence_magnitude,
                    "recovery_delta_diff": r_b.recovery_delta - r_a.recovery_delta,
                    "status_a": r_a.causal_support.value,
                    "status_b": r_b.causal_support.value,
                }

        return {
            "investigation_a": inv_a_id,
            "investigation_b": inv_b_id,
            "question_match": inv_a.question == inv_b.question,
            "status_a": inv_a.status.value,
            "status_b": inv_b.status.value,
            "divergence_comparison": divergence_deltas,
        }

    @classmethod
    def build_scorecard(cls, inv: Investigation) -> Dict[str, Any]:
        """Build an exportable scorecard summarizing the completed investigation."""
        def _get(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        supported_hyps = []
        for h in inv.candidate_hypotheses:
            st = str(_get(h, "status", ""))
            cl = str(_get(h, "classification", ""))
            if "COUNTERFACTUALLY_SUPPORTED" in st or "SUPPORTED" in cl:
                supported_hyps.append(h)

        primary_hyp = supported_hyps[0] if supported_hyps else (
            inv.candidate_hypotheses[0] if inv.candidate_hypotheses else None
        )

        p_stmt = _get(primary_hyp, "statement", "No hypothesis generated") if primary_hyp else "No hypothesis generated"
        p_status = _get(primary_hyp, "status", "INCONCLUSIVE") if primary_hyp else "INCONCLUSIVE"
        if hasattr(p_status, "value"):
            p_status = p_status.value
        p_status = str(p_status)

        p_ev_cnt = _get(primary_hyp, "supporting_evidence_count", 0) if primary_hyp else 0
        p_alts = _get(primary_hyp, "alternative_explanations", []) if primary_hyp else []

        evidence_list = [_get(r, "evidence_summary", "") for r in inv.results]

        inv_status = getattr(inv.status, "value", str(inv.status))

        return {
            "investigation_id": inv.investigation_id,
            "experiment_id": inv.experiment_id,
            "question": inv.question,
            "primary_hypothesis": p_stmt,
            "verdict": p_status,
            "counterfactual_evidence": evidence_list,
            "supporting_evidence_count": p_ev_cnt,
            "alternative_explanations": p_alts,
            "epistemic_limitations": [
                "Counterfactual conclusions hold within the deterministic discrete model substrate.",
                "Circular convolution approximations may differ in alternate dimensional scales.",
            ],
            "conclusion": f"Investigation {inv_status}: {p_stmt}.",
        }
