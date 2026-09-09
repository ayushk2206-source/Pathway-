"""Unit tests for Synaptic Surgery and Memory X-Ray engine (Phase 15)."""

import numpy as np
import pytest

from core.surgery import (
    SurgerySession,
    compute_memory_xray,
    get_synapse_xray_in_session,
    lock_baseline,
    reset_session,
    restore_synapses,
    run_recall_comparison,
    silence_synapses,
    strengthen_synapses,
    weaken_synapses,
)
from core.synaptic import SynapticBrain


def test_lock_baseline_creates_isolated_branch():
    brain = SynapticBrain(seed=42, d=8, decay=0.05)
    brain.write("color", "blue")
    brain.write("city", "tokyo")

    orig_w = brain.W.copy()
    session = lock_baseline(brain)

    assert session.d == 8
    assert session.seed == 42
    assert np.allclose(session.baseline_W, orig_w)
    assert np.allclose(session.surgery_W, orig_w)
    assert len(session.library) == 2
    assert session.surgery_op_count == 0

    # Modify surgery branch - brain must NOT change
    session.surgery_W[0, 0] = 999.0
    assert brain.W[0, 0] != 999.0
    assert session.baseline_W[0, 0] != 999.0


def test_weaken_synapses():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("apple", "fruit")
    session = lock_baseline(brain)

    syn_id = "syn_k0_v0"
    init_w = float(session.baseline_W[0, 0])

    op = weaken_synapses(session, [syn_id], factor=0.5)

    assert op.operation == "weaken"
    assert op.factor == pytest.approx(0.5)
    assert session.surgery_W[0, 0] == pytest.approx(init_w * 0.5)
    assert session.baseline_W[0, 0] == pytest.approx(init_w)  # Baseline untouched
    assert len(session.operations) == 1
    assert session.surgery_op_count == 1


def test_strengthen_synapses():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("apple", "fruit")
    session = lock_baseline(brain)

    syn_id = "syn_k1_v2"
    init_w = float(session.baseline_W[2, 1])

    op = strengthen_synapses(session, [syn_id], factor=2.5)

    assert op.operation == "strengthen"
    assert op.factor == pytest.approx(2.5)
    assert session.surgery_W[2, 1] == pytest.approx(init_w * 2.5)
    assert session.baseline_W[2, 1] == pytest.approx(init_w)


def test_silence_synapses_controlled_ablation():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("cat", "animal")
    session = lock_baseline(brain)

    syn_ids = ["syn_k0_v0", "syn_k1_v1"]
    op = silence_synapses(session, syn_ids)

    assert op.operation == "silence"
    assert session.surgery_W[0, 0] == 0.0
    assert session.surgery_W[1, 1] == 0.0
    assert "CONTROLLED ABLATION EXPERIMENT" in op.description
    assert len(session.operations) == 1


def test_restore_synapses():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("dog", "pet")
    session = lock_baseline(brain)

    syn_id = "syn_k2_v3"
    init_w = float(session.baseline_W[3, 2])

    silence_synapses(session, [syn_id])
    assert session.surgery_W[3, 2] == 0.0

    op_restore = restore_synapses(session, [syn_id])
    assert op_restore.operation == "restore"
    assert session.surgery_W[3, 2] == pytest.approx(init_w)


def test_reset_session():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("river", "water")
    session = lock_baseline(brain)

    silence_synapses(session, ["syn_k0_v0", "syn_k1_v1", "syn_k2_v2"])
    strengthen_synapses(session, ["syn_k3_v3"], factor=3.0)
    assert not np.allclose(session.surgery_W, session.baseline_W)

    reset_session(session)
    assert np.allclose(session.surgery_W, session.baseline_W)


def test_run_recall_comparison():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("sun", "star")
    brain.write("earth", "planet")
    session = lock_baseline(brain)

    # Initial comparison before any surgery
    comp1 = run_recall_comparison(session, "sun", expected_value="star")
    assert comp1.baseline_predicted == comp1.surgery_predicted
    assert comp1.delta_confidence == pytest.approx(0.0)
    assert comp1.delta_fidelity == pytest.approx(0.0)
    assert comp1.agreement is True

    # Silence critical synapses for "sun"
    xray = compute_memory_xray(
        brain.W, brain.W_prev, brain.last_delta, brain.last_update_steps,
        brain.library, brain.seed, brain.d, "sun", expected_value="star"
    )
    top_syns = [s.synapse_id for s in xray.synapses[:5]]
    silence_synapses(session, top_syns)

    comp2 = run_recall_comparison(session, "sun", expected_value="star")
    assert comp2.operations_applied >= 1
    assert comp2.experiment_label == "CONTROLLED ABLATION EXPERIMENT"
    assert comp2.surgery_confidence != comp2.baseline_confidence
    assert "Correlation does not establish causation" in comp2.caution_note


def test_compute_memory_xray_mathematical_integrity():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("key_concept", "target_value")

    xray = compute_memory_xray(
        brain.W, brain.W_prev, brain.last_delta, brain.last_update_steps,
        brain.library, brain.seed, brain.d, "key_concept", expected_value="target_value"
    )

    assert xray.query_concept == "key_concept"
    assert xray.expected_value == "target_value"
    assert xray.dimension == 8
    assert xray.total_synapses_analyzed > 0
    assert len(xray.synapses) == xray.total_synapses_analyzed

    # Check that synapses are sorted by descending relevance_score
    relevance_scores = [s.relevance_score for s in xray.synapses]
    assert relevance_scores == sorted(relevance_scores, reverse=True)

    # Check tier classification logic
    assert xray.highly_relevant >= 1
    assert (
        xray.highly_relevant + xray.moderately_relevant +
        xray.weakly_relevant + xray.unrelated
    ) == xray.total_synapses_analyzed

    # Check documentation and transparency
    assert "relevance_score(i,j) = |W[i,j] * k_query[j]|" in xray.metric_description or "linear readout equation" in xray.metric_description
    assert "Educational computational model" in xray.disclaimer


def test_get_synapse_xray_in_session():
    brain = SynapticBrain(seed=42, d=8, decay=0.0)
    brain.write("alpha", "beta")
    session = lock_baseline(brain)

    syn_id = "syn_k1_v2"
    weaken_synapses(session, [syn_id], factor=0.4)

    details = get_synapse_xray_in_session(session, syn_id)
    assert details["synapse_id"] == syn_id
    assert details["is_modified"] is True
    assert details["weight_delta"] < 0
    assert len(details["operations_applied"]) == 1
