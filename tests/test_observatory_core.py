"""Unit tests for Phase 19 Adaptive Memory Observatory Core Engine."""

import pytest
from core.observatory import (
    AdaptiveObservatoryEngine,
    StreamEvent,
    ObservatorySession,
    ChangeDetection,
    StabilityPlasticityMetrics,
    EnvironmentShiftReport,
)


def test_stream_execution_and_snapshots():
    """Verify that a multi-step stream evolves the network and records full snapshots."""
    events = [
        StreamEvent(timestep=1, environment_id="ENV_A", event_type="WRITE", label="Write A", concept="solaris", value="golden_star", strength=1.0),
        StreamEvent(timestep=2, environment_id="ENV_A", event_type="WRITE", label="Write B", concept="luna", value="silver_orb", strength=1.0),
        StreamEvent(timestep=3, environment_id="ENV_A", event_type="DECAY", label="Decay 2 steps", n_steps=2),
    ]

    session = AdaptiveObservatoryEngine.run_stream(
        events=events,
        dimension=16,
        decay=0.04,
        update_strength=1.0,
        seed=42,
    )

    assert len(session.snapshots) == 4  # T0 init + 3 events
    assert session.snapshots[0].timestep == 0
    assert session.snapshots[1].timestep == 1
    assert session.snapshots[1].matrix_norm > 0.0
    assert len(session.snapshots[1].synaptic_weather) == 16 * 16

    # Verify probes
    snap3 = session.snapshots[3]
    solaris_probe = next((p for p in snap3.probes if p.concept == "solaris"), None)
    assert solaris_probe is not None
    assert solaris_probe.fidelity > 0.85
    assert solaris_probe.is_correct is True


def test_synaptic_weather_classification():
    """Verify synaptic weather encodes genuine state changes and activity."""
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    snap1 = session.snapshots[1]
    weather = snap1.synaptic_weather

    classifications = {w.classification for w in weather}
    assert "RECENTLY_STRENGTHENED" in classifications or "CURRENTLY_ACTIVE" in classifications
    assert "INACTIVE_ZERO" in classifications or "UNCHANGED" in classifications

    # Check that synapse ID format matches syn_kJ_vI
    for w in weather[:5]:
        assert w.synapse_id.startswith("syn_k")
        assert "_v" in w.synapse_id


def test_change_detection():
    """Verify change detector computes exact differences between adjacent timesteps."""
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    snap_t1 = session.snapshots[1]
    snap_t2 = session.snapshots[2]

    diff = AdaptiveObservatoryEngine.detect_changes(snap_t1, snap_t2, threshold=0.01)
    assert diff.timestep_before == 1
    assert diff.timestep_after == 2
    assert diff.frobenius_delta > 0.0
    assert len(diff.strengthened_synapses) > 0
    assert "From T1 to T2" in diff.summary


def test_stability_plasticity_metrics():
    """Verify stability vs plasticity metrics calculation."""
    session, _ = AdaptiveObservatoryEngine.run_env_shift_protocol()
    snap_t1 = session.snapshots[1]
    snap_t2 = session.snapshots[2]

    metrics = AdaptiveObservatoryEngine.compute_stability_plasticity(snap_t1, snap_t2)
    assert 0.0 <= metrics.stability_ratio <= 1.0
    assert metrics.plasticity_extent >= 0.0
    assert metrics.total_active > 0
    assert metrics.mean_abs_weight_change >= 0.0
    assert "Stability Ratio" in metrics.formula_note


def test_environment_shift_protocol():
    """Verify the controlled A -> B -> A environment shift experiment."""
    session, report = AdaptiveObservatoryEngine.run_env_shift_protocol(
        dimension=16,
        decay=0.04,
        update_strength=1.0,
        seed=42,
    )

    assert session.total_timesteps == 11
    assert report.environment_a == "ENV_A"
    assert report.environment_b == "ENV_B"
    assert report.retention_ratio_during_shift < 1.0  # Interference from B
    assert report.recovery_magnitude >= 0.0  # Recovers when re-written
    assert "solaris" in report.before_shift_recalls
    assert "terra" in report.during_shift_recalls
