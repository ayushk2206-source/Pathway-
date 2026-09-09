"""Research War Room state and station data modeling (Phase 05).

Provides structured backend representations for interactive research station views:
Director's Desk, Experiment Station, Memory Engine Monitor, Analyst Desk,
Red Team Bunker, and Debate Podium.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WarRoomStation:
    """Represents a specialized research station in the War Room."""
    station_id: str
    station_name: str
    active_agent: str
    agent_avatar: str
    status: str  # "idle", "active", "warning", "complete"
    current_thought: str
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    active_alerts: List[str] = field(default_factory=list)
    recent_dialogue: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "active_agent": self.active_agent,
            "agent_avatar": self.agent_avatar,
            "status": self.status,
            "current_thought": self.current_thought,
            "metrics_summary": self.metrics_summary,
            "active_alerts": self.active_alerts,
            "recent_dialogue": self.recent_dialogue,
        }


@dataclass
class WarRoomState:
    """Complete snapshot of the Research War Room for real-time frontend visualization."""
    investigation_id: str
    research_question: str
    round_number: int
    investigation_status: str
    stations: Dict[str, WarRoomStation]
    live_event_log: List[Dict[str, Any]] = field(default_factory=list)
    consensus_meter: float = 0.5  # 0.0 (high conflict) to 1.0 (unanimous agreement)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "research_question": self.research_question,
            "round_number": self.round_number,
            "investigation_status": self.investigation_status,
            "stations": {k: v.to_dict() for k, v in self.stations.items()},
            "live_event_log": self.live_event_log,
            "consensus_meter": self.consensus_meter,
            "updated_at": self.updated_at,
        }


class WarRoomBuilder:
    """Builds and updates the War Room state from active investigation data."""

    @classmethod
    def build_state(
        cls,
        investigation_id: str,
        question: str,
        status: str,
        round_number: int,
        agent_outputs: List[Dict[str, Any]],
        experiments: List[Dict[str, Any]],
        disagreements: List[Dict[str, Any]],
    ) -> WarRoomState:
        # Station 1: Research Director
        director_thought = "Coordinating investigation pipeline..."
        if status == "completed":
            director_thought = "Research synthesis finalized."
        elif status == "challenging":
            director_thought = "Evaluating Red Team critique."

        director_station = WarRoomStation(
            station_id="director_desk",
            station_name="Director's Podium",
            active_agent="Research Director",
            agent_avatar="🎛️",
            status="active" if status != "completed" else "complete",
            current_thought=director_thought,
            metrics_summary={"round": round_number, "total_experiments": len(experiments)},
        )

        # Station 2: Experiment Lab
        latest_exp = experiments[-1] if experiments else {}
        exp_station = WarRoomStation(
            station_id="experiment_lab",
            station_name="Experiment Control Desk",
            active_agent="Statistician",
            agent_avatar="📊",
            status="active" if status in ("running", "requires_experiment") else "idle",
            current_thought=f"Operating experiment: {latest_exp.get('title', 'Awaiting run')}",
            metrics_summary={
                "experiment_id": latest_exp.get("experiment_id"),
                "mechanism": latest_exp.get("mechanism", "interference"),
            },
        )

        # Station 3: Memory Engine Monitor
        memory_station = WarRoomStation(
            station_id="memory_engine",
            station_name="Vector Memory Telemetry",
            active_agent="AI Engineer",
            agent_avatar="🤖",
            status="active",
            current_thought="Simulating circular convolution binding in R^d vector space.",
            metrics_summary={
                "state_dimension": 64,
                "binding_type": "circular_convolution",
                "lossy_compression": True,
            },
        )

        # Station 4: Analyst Desk
        analyst_out = next((o for o in agent_outputs if "analyst" in o.get("agent", "").lower()), None)
        analyst_station = WarRoomStation(
            station_id="analyst_desk",
            station_name="Quantitative Analysis Desk",
            active_agent="Data Analyst",
            agent_avatar="📈",
            status="active" if analyst_out else "idle",
            current_thought=analyst_out.get("analysis", "Awaiting experiment results.") if analyst_out else "Standing by.",
            metrics_summary={
                "confidence": analyst_out.get("confidence", 0.0) if analyst_out else 0.0,
                "verdict": analyst_out.get("verdict", "unknown") if analyst_out else "unknown",
            },
        )

        # Station 5: Red Team Bunker
        red_team_out = next((o for o in agent_outputs if "red team" in o.get("agent", "").lower()), None)
        objections = red_team_out.get("objections", []) if red_team_out else []
        red_team_station = WarRoomStation(
            station_id="red_team_bunker",
            station_name="Hostile Review Bunker",
            active_agent="Red Team",
            agent_avatar="🧐",
            status="warning" if objections else "idle",
            current_thought="Interrogating confounders and boundary vulnerabilities." if red_team_out else "Preparing challenge.",
            active_alerts=objections,
            metrics_summary={"objection_count": len(objections)},
        )

        # Station 6: Debate Podium
        podium_station = WarRoomStation(
            station_id="debate_podium",
            station_name="Research Debate Chamber",
            active_agent="Research Synthesist",
            agent_avatar="🔍",
            status="warning" if disagreements else "complete",
            current_thought="Facilitating specialist debate without flattening nuance.",
            metrics_summary={"active_disagreements": len(disagreements)},
        )

        consensus_val = 0.85 if not disagreements else 0.45

        stations = {
            "director": director_station,
            "experiment_lab": exp_station,
            "memory_engine": memory_station,
            "analyst": analyst_station,
            "red_team": red_team_station,
            "debate": podium_station,
        }

        return WarRoomState(
            investigation_id=investigation_id,
            research_question=question,
            round_number=round_number,
            investigation_status=status,
            stations=stations,
            consensus_meter=consensus_val,
        )
