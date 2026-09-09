"""State progression replay controller for interactive memory timelines (Phase 05)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Union

from core import Experiment
from .checkpoints import get_state_checkpoint


class PlaybackStatus(str, Enum):
    IDLE = "IDLE"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class MemoryReplayController:
    """State-control machine for stepping forward, backward, and jumping across events."""

    def __init__(self, experiment: Experiment) -> None:
        self.experiment = experiment
        self.total_steps = len(experiment.snapshots)
        self.current_step = 0
        self.status = PlaybackStatus.IDLE

    def start(self) -> Dict[str, Any]:
        """Start replay progression from t=0."""
        self.current_step = 0
        self.status = PlaybackStatus.PLAYING
        return self.get_current_state()

    def pause(self) -> Dict[str, Any]:
        """Pause playback at current timestep."""
        self.status = PlaybackStatus.PAUSED
        return self.get_current_state()

    def resume(self) -> Dict[str, Any]:
        """Resume playback from current timestep."""
        if self.current_step >= self.total_steps - 1:
            self.status = PlaybackStatus.COMPLETED
        else:
            self.status = PlaybackStatus.PLAYING
        return self.get_current_state()

    def step_forward(self) -> Dict[str, Any]:
        """Advance replay by one event/step."""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
        if self.current_step >= self.total_steps - 1:
            self.status = PlaybackStatus.COMPLETED
        return self.get_current_state()

    def step_backward(self) -> Dict[str, Any]:
        """Rewind replay by one event/step."""
        if self.current_step > 0:
            self.current_step -= 1
        self.status = PlaybackStatus.PAUSED
        return self.get_current_state()

    def jump_to_event(self, event_identifier: Union[int, str]) -> Dict[str, Any]:
        """Jump directly to a specific timestep index or event_id."""
        if isinstance(event_identifier, int):
            target = max(0, min(self.total_steps - 1, event_identifier))
        else:
            # Find step matching event_id
            target = next(
                (
                    i
                    for i, snap in enumerate(self.experiment.snapshots)
                    if snap.get("event_id") == event_identifier
                ),
                self.current_step,
            )

        self.current_step = target
        self.status = PlaybackStatus.PAUSED if self.current_step < self.total_steps - 1 else PlaybackStatus.COMPLETED
        return self.get_current_state()

    def get_current_state(self) -> Dict[str, Any]:
        """Retrieve current playback checkpoint and player state."""
        checkpoint = get_state_checkpoint(self.experiment, self.current_step)
        return {
            "playback_status": self.status.value,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "has_next": self.current_step < self.total_steps - 1,
            "has_prev": self.current_step > 0,
            "checkpoint": checkpoint,
        }
