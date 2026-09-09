"""Section 33/37/38/39/42 -- Causality Ledger, Claim Versioning, Contradiction Engine, and Causal Reports.

Provides scientific provenance tracking for causal claims:
- Claims are immutable records with explicit version histories (v1, v2, ...).
- ContradictionEngine automatically detects empirical divergences across experiments.
- CausalReportGenerator produces cautious, publication-grade investigation reports.
- CausalQueueManager enforces resource budgets with Pause/Stop/Clear queue controls.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from core import Experiment
from .models import (
    CausalClaim,
    CausalClaimVersion,
    CausalityConflict,
    CausalReport,
    CausalQueueItem,
    CausalScenario,
    CausalCostEstimate,
    _now_iso,
)
from .types import ClaimStatus, QueueStatus, MAX_QUEUE_SIZE


class CausalLedger:
    """Registry of verified or tested causal claims with immutable version history."""

    def __init__(self) -> None:
        self._claims: Dict[str, CausalClaim] = {}

    def register_claim(
        self,
        source_memory: str,
        target_memory: str,
        statement: str,
        status: ClaimStatus = ClaimStatus.SUPPORTED_WITHIN_EXPERIMENT,
        evidence_experiment_ids: Optional[List[str]] = None,
        interventions: int = 1,
        replications: int = 1,
        effect_consistency: str = "HIGH",
        claim_id: Optional[str] = None,
    ) -> CausalClaim:
        cid = claim_id or f"CLM-{len(self._claims) + 1:03d}"
        v1 = CausalClaimVersion(
            version=1,
            statement=statement,
            status=status,
            evidence_experiment_ids=list(evidence_experiment_ids or []),
            interventions=interventions,
            replications=replications,
            effect_consistency=effect_consistency,
            changed_because="Initial causal claim formulated from counterfactual evidence.",
        )
        claim = CausalClaim(
            claim_id=cid,
            source_memory=source_memory,
            target_memory=target_memory,
            versions=[v1],
        )
        self._claims[cid] = claim
        return claim

    def update_claim(
        self,
        claim_id: str,
        statement: str,
        status: ClaimStatus,
        evidence_experiment_ids: List[str],
        interventions: int,
        replications: int,
        effect_consistency: str,
        changed_because: str,
    ) -> CausalClaim:
        claim = self._claims.get(claim_id)
        if not claim:
            raise KeyError(f"Claim with id '{claim_id}' not found in ledger.")

        next_version_num = len(claim.versions) + 1
        new_v = CausalClaimVersion(
            version=next_version_num,
            statement=statement,
            status=status,
            evidence_experiment_ids=list(evidence_experiment_ids),
            interventions=interventions,
            replications=replications,
            effect_consistency=effect_consistency,
            changed_because=changed_because,
        )
        claim.versions.append(new_v)
        return claim

    def get_claim(self, claim_id: str) -> Optional[CausalClaim]:
        return self._claims.get(claim_id)

    def list_claims(self) -> List[CausalClaim]:
        return list(self._claims.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_claims": len(self._claims),
            "claims": [c.to_dict() for c in self._claims.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalLedger":
        ledger = cls()
        for item in data.get("claims", []):
            claim = CausalClaim.from_dict(item)
            ledger._claims[claim.claim_id] = claim
        return ledger


class ContradictionEngine:
    """Section 39 -- Detects empirical contradictions between experiments and suggests discriminating tests."""

    def __init__(self) -> None:
        self._conflicts: Dict[str, CausalityConflict] = {}

    def detect_conflicts(
        self,
        ledger: CausalLedger,
        observations: Optional[List[Dict[str, Any]]] = None,
    ) -> List[CausalityConflict]:
        """Scans recorded observations or claims for conflicting causal effects."""
        obs = observations or []
        # Group observations by (source_memory, target_memory)
        grouped: Dict[tuple, List[Dict[str, Any]]] = {}
        for o in obs:
            src = str(o.get("source_memory", "")).strip()
            tgt = str(o.get("target_memory", "")).strip()
            if src and tgt and src != tgt:
                key = (src, tgt)
                grouped.setdefault(key, []).append(o)

        detected: List[CausalityConflict] = []
        for (src, tgt), items in grouped.items():
            if len(items) >= 2:
                # Compare pairwise
                for i in range(len(items)):
                    for j in range(i + 1, len(items)):
                        a = items[i]
                        b = items[j]
                        eff_a = float(a.get("effect", 0.0))
                        eff_b = float(b.get("effect", 0.0))
                        exp_a = str(a.get("experiment_id", "exp_a"))
                        exp_b = str(b.get("experiment_id", "exp_b"))

                        # Conflict if one experiment shows significant effect and another shows near-zero or opposite
                        if abs(eff_a - eff_b) >= 0.15 and (abs(eff_a) > 0.10 or abs(eff_b) > 0.10):
                            conflict_key = f"{src}->{tgt}:{exp_a}:{exp_b}"
                            existing = next((c for c in self._conflicts.values() if f"{c.source_memory}->{c.target_memory}:{c.experiment_a}:{c.experiment_b}" == conflict_key), None)
                            if not existing:
                                conflict = CausalityConflict(
                                    source_memory=src,
                                    target_memory=tgt,
                                    experiment_a=exp_a,
                                    experiment_b=exp_b,
                                    effect_a=round(eff_a, 4),
                                    effect_b=round(eff_b, 4),
                                    comparison={
                                        "delta_difference": round(abs(eff_a - eff_b), 4),
                                        "timing_a": a.get("timing"),
                                        "timing_b": b.get("timing"),
                                        "dose_a": a.get("dose", 1.0),
                                        "dose_b": b.get("dose", 1.0),
                                        "notes": "Measurable divergence in observed intervention impact across distinct conditions.",
                                    },
                                    suggested_controlled_test=(
                                        f"Run controlled parameter sweep holding memory topology fixed: test {src} at "
                                        f"both t={a.get('timing', 'baseline')} and t={b.get('timing', 'alternate')} to isolate timing sensitivity."
                                    ),
                                )
                                self._conflicts[conflict.conflict_id] = conflict
                                detected.append(conflict)

        return list(self._conflicts.values())

    def add_conflict(self, conflict: CausalityConflict) -> CausalityConflict:
        self._conflicts[conflict.conflict_id] = conflict
        return conflict

    def list_conflicts(self) -> List[CausalityConflict]:
        return list(self._conflicts.values())


class CausalReportGenerator:
    """Section 33 -- Generates publication-grade, scientifically cautious causal investigation reports."""

    @classmethod
    def generate_report(
        cls,
        experiment_id: str,
        question: str,
        scenario: Dict[str, Any],
        baseline: Dict[str, Any],
        intervention: Dict[str, Any],
        temporal_window: Optional[Dict[str, Any]] = None,
        first_divergence: Optional[Dict[str, Any]] = None,
        cascade: Optional[Dict[str, Any]] = None,
        effect: Optional[Dict[str, Any]] = None,
        alternative_paths: Optional[List[Dict[str, Any]]] = None,
        replication: Optional[Dict[str, Any]] = None,
        limitations: Optional[List[str]] = None,
        conclusion: Optional[str] = None,
    ) -> CausalReport:
        default_limits = [
            "Causal inferences are strictly valid only within the tested substrate architecture and experimental parameters.",
            "Counterfactual replay holds historical non-intervened events fixed and does not simulate exogenous environmental dynamics.",
            "Correlation between memories does not establish direct causal dependence in the absence of targeted perturbation.",
        ]
        limits = list(limitations or default_limits)

        concl = conclusion or (
            f"The targeted intervention on memory {scenario.get('target_memory', 'TARGET')} produced measurable "
            f"downstream divergence starting at t={first_divergence.get('first_divergence_step') if first_divergence else 'UNKNOWN'}. "
            "Evidence supports state sensitivity within the tested simulation configuration."
        )

        return CausalReport(
            experiment_id=experiment_id,
            question=question,
            scenario=dict(scenario),
            baseline=dict(baseline),
            intervention=dict(intervention),
            temporal_window=dict(temporal_window) if temporal_window else None,
            first_divergence=dict(first_divergence) if first_divergence else None,
            cascade=dict(cascade or {}),
            effect=dict(effect or {}),
            alternative_paths=list(alternative_paths or []),
            replication=dict(replication or {"replications_count": 1, "consistency": "HIGH"}),
            limitations=limits,
            conclusion=concl,
        )


class CausalQueueManager:
    """Section 17 / 18 / 42 -- Queue manager for causal experiments with resource limits and pause/stop controls."""

    def __init__(self, max_size: int = MAX_QUEUE_SIZE) -> None:
        self.max_size = max_size
        self._queue: List[CausalQueueItem] = []
        self._is_paused: bool = False
        self._is_stopped: bool = False

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    def enqueue(self, scenario: CausalScenario, cost_estimate: CausalCostEstimate) -> CausalQueueItem:
        if len(self._queue) >= self.max_size:
            raise ValueError(f"Queue is full (limit {self.max_size}). Clear queue or wait for execution.")
        if self._is_stopped:
            raise RuntimeError("Queue is stopped. Reset or resume before enqueuing new jobs.")

        item = CausalQueueItem(
            scenario=scenario.to_dict(),
            estimated_cost=cost_estimate.to_dict(),
            status=QueueStatus.QUEUED,
        )
        self._queue.append(item)
        return item

    def list_items(self) -> List[CausalQueueItem]:
        return list(self._queue)

    def get_item(self, queue_id: str) -> Optional[CausalQueueItem]:
        return next((it for it in self._queue if it.queue_id == queue_id), None)

    def update_item_status(self, queue_id: str, status: QueueStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> Optional[CausalQueueItem]:
        item = self.get_item(queue_id)
        if item:
            item.status = status
            item.result = result
            item.error = error
            item.updated_at = _now_iso()
        return item

    def pause(self) -> None:
        self._is_paused = True

    def resume(self) -> None:
        self._is_paused = False
        self._is_stopped = False

    def stop(self) -> None:
        self._is_stopped = True
        for it in self._queue:
            if it.status in (QueueStatus.QUEUED, QueueStatus.RUNNING):
                it.status = QueueStatus.CANCELLED
                it.updated_at = _now_iso()

    def clear(self) -> None:
        self._queue.clear()
        self._is_paused = False
        self._is_stopped = False
