"""Local experiment execution queue for Experiment Lab (Phase 03).

Provides queue lifecycle handling (draft -> queued -> running -> completed / failed),
FIFO execution, cancellation, and execution status inspection.
"""

from __future__ import annotations

import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .models import ExperimentStatus, LabExperiment


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueueItem:
    item_id: str
    experiment: LabExperiment
    status: ExperimentStatus = ExperimentStatus.QUEUED
    enqueued_at: str = field(default_factory=_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "experiment_id": self.experiment.experiment_id,
            "title": self.experiment.title,
            "status": self.status.value,
            "enqueued_at": self.enqueued_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }


class ExperimentQueue:
    """Thread-safe local execution queue for lab experiments."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queue: deque[QueueItem] = deque()
        self._items: Dict[str, QueueItem] = {}
        self._active_item: Optional[QueueItem] = None

    def enqueue(self, experiment: LabExperiment) -> QueueItem:
        with self._lock:
            item_id = f"q-{uuid.uuid4().hex[:8]}"
            experiment.status = ExperimentStatus.QUEUED
            item = QueueItem(
                item_id=item_id,
                experiment=experiment,
                status=ExperimentStatus.QUEUED,
            )
            self._items[item_id] = item
            self._queue.append(item)
            return item

    def run_next(self, runner_fn: Callable[[LabExperiment], LabExperiment]) -> Optional[QueueItem]:
        """Execute the next experiment in the queue synchronously."""
        with self._lock:
            if not self._queue:
                return None
            item = self._queue.popleft()
            self._active_item = item
            item.status = ExperimentStatus.RUNNING
            item.started_at = _now_iso()
            item.experiment.status = ExperimentStatus.RUNNING

        try:
            executed_exp = runner_fn(item.experiment)
            with self._lock:
                item.experiment = executed_exp
                item.status = ExperimentStatus.COMPLETED
                item.completed_at = _now_iso()
                item.experiment.status = ExperimentStatus.COMPLETED
                self._active_item = None
                return item
        except Exception as exc:
            with self._lock:
                item.status = ExperimentStatus.FAILED
                item.completed_at = _now_iso()
                item.error_message = str(exc)
                item.experiment.status = ExperimentStatus.FAILED
                self._active_item = None
                return item

    def get_status(self, item_id: str) -> Optional[QueueItem]:
        with self._lock:
            return self._items.get(item_id)

    def cancel(self, item_id: str) -> bool:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return False
            if item.status == ExperimentStatus.QUEUED:
                self._queue.remove(item)
                item.status = ExperimentStatus.FAILED
                item.error_message = "Cancelled by user before execution."
                item.completed_at = _now_iso()
                return True
            return False

    def list_items(self) -> List[QueueItem]:
        with self._lock:
            return list(self._items.values())

    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)
