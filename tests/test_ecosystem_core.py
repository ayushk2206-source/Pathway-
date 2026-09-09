"""Tests for Phase 21 Core Memory Ecosystem Engine."""

import pytest
from core.ecosystem import MemoryEcosystemEngine, MemoryPassport, MemoryLifecycle


def test_ecosystem_initialization():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    assert engine.dimension == 16
    assert engine.active_memory_id == "M-001"
    assert engine.is_following is True

    passports = engine.list_passports()
    assert len(passports) >= 4
    assert any(p.memory_id == "M-001" for p in passports)
    assert any(p.concept == "Concept Alpha" for p in passports)


def test_get_memory_passport():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    passport = engine.get_memory_passport("M-001")

    assert isinstance(passport, MemoryPassport)
    assert passport.memory_id == "M-001"
    assert passport.concept == "Concept Alpha"
    assert passport.active_units > 0
    assert passport.synaptic_modifications > 0
    assert passport.recall_fidelity >= -1.0 and passport.recall_fidelity <= 1.0
    assert passport.fingerprint_norm > 0.0

    d = passport.to_dict()
    assert d["memory_id"] == "M-001"
    assert "active_units" in d
    assert "synaptic_modifications" in d


def test_set_active_memory_and_follow():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    p = engine.set_active_memory("M-002", follow=True)
    assert engine.active_memory_id == "M-002"
    assert engine.is_following is True
    assert p.memory_id == "M-002"
    assert p.is_following is True

    p_off = engine.set_active_memory("M-002", follow=False)
    assert engine.is_following is False
    assert p_off.is_following is False


def test_get_memory_lifecycle():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    lifecycle = engine.get_memory_lifecycle("M-001")

    assert isinstance(lifecycle, MemoryLifecycle)
    assert lifecycle.memory_id == "M-001"
    assert len(lifecycle.stages) == 8

    stage_ids = [s.stage_id for s in lifecycle.stages]
    assert stage_ids == [
        "ENCODE",
        "WRITE",
        "STABILIZE",
        "RECALL",
        "INTERFERE",
        "ADAPT",
        "INSPECT",
        "COUNTERFACTUAL",
    ]

    for s in lifecycle.stages:
        assert s.target_workspace in [
            "lab",
            "synaptic",
            "timeline",
            "xray",
            "collision",
            "observatory",
            "detective",
            "counterfactual",
        ]


def test_unified_timeline_events():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    events = engine.get_unified_timeline()
    assert len(events) >= 8

    evt_types = {e.event_type for e in events}
    assert "MEMORY_CREATED" in evt_types
    assert "SYNAPTIC_WRITE" in evt_types

    m1_events = engine.get_unified_timeline(memory_id="M-001")
    assert len(m1_events) >= 2
    assert all(e.memory_id == "M-001" for e in m1_events)


def test_build_relationship_map():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    relationships = engine.build_relationship_map()

    assert len(relationships) > 0
    for r in relationships:
        assert r.relationship_type in [
            "SHARED_STATE",
            "SYNAPTIC_OVERLAP",
            "DERIVED_FROM",
            "INTERFERENCE",
            "COUNTERFACTUAL_OF",
        ]
        assert r.weight >= 0.0
        assert "cue_cosine" in r.evidence or "intervened_synapse" in r.evidence


def test_synaptic_change_ledger():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    ledger = engine.get_change_ledger("M-001", transition_name="SYNAPTIC WRITE")

    assert ledger.transition_name == "SYNAPTIC WRITE"
    assert ledger.memory_id == "M-001"
    assert "active_connections" in ledger.before
    assert "active_connections" in ledger.after
    assert len(ledger.scientific_claims) >= 3

    claim_types = {c["type"] for c in ledger.scientific_claims}
    assert "OBSERVED" in claim_types
    assert "MEASURED" in claim_types


def test_checkpoints_and_comparison():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    cp = engine.create_checkpoint("M-001", "Post-Test Verification Checkpoint")

    assert cp.memory_id == "M-001"
    assert cp.label == "Post-Test Verification Checkpoint"
    assert "W_norm" in cp.weights_summary

    cps = engine.list_checkpoints("M-001")
    assert any(c.checkpoint_id == cp.checkpoint_id for c in cps)

    diff = engine.compare_states(
        {"W_norm": 1.0, "active_ratio": 0.5},
        {"W_norm": 1.3, "active_ratio": 0.65},
    )
    assert diff["frobenius_drift"] == 0.3
    assert diff["active_ratio_shift"] == 0.15


def test_learner_hypothesis_evaluation():
    engine = MemoryEcosystemEngine(dimension=16, seed=42)
    hyp = engine.record_hypothesis(
        memory_id="M-001",
        experiment_type="INTERFERENCE",
        prediction_text="Intervening updates will degrade recall due to shared weights.",
        predicted_outcome="RETENTION_DROP",
    )

    assert hyp.memory_id == "M-001"
    assert hyp.is_match is True
    assert hyp.observed_outcome == "RETENTION_DROP"
    assert "Hypothesis confirmed" in hyp.difference_explanation

    all_hyps = engine.get_hypotheses("M-001")
    assert len(all_hyps) >= 1
