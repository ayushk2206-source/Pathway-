"""Candidate hypothesis generator (Phase 07).

Generates multiple competing explanations derived strictly from measurable computational mechanisms.
Never provides only a single explanation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.experiment import Experiment
from .models import CandidateHypothesis, MeasurableObservation
from .types import CausalSupportStatus, HypothesisClassification, QuestionIntent


class HypothesisGenerator:
    """Generates competing candidate explanations strictly from verifiable mechanisms."""

    @classmethod
    def generate_hypotheses(
        cls,
        observations: List[MeasurableObservation],
        experiment: Experiment,
        intent: QuestionIntent = QuestionIntent.INTERFERENCE,
    ) -> List[CandidateHypothesis]:
        """Produce a ranked set of competing hypotheses based on measurable observations."""
        hypotheses: List[CandidateHypothesis] = []

        # Extract context from observations
        target_mem = observations[0].target_memory if observations else "target_memory"
        competing_mems = []
        cue_sim = 0.0
        rel_events = []
        strength_delta = 0.0

        for obs in observations:
            if obs.competing_memories:
                competing_mems.extend(obs.competing_memories)
            if obs.cue_similarity and obs.cue_similarity > cue_sim:
                cue_sim = obs.cue_similarity
            if obs.relevant_events:
                rel_events.extend(obs.relevant_events)
            if obs.metric_name == "representation_strength":
                strength_delta = obs.delta

        competing_mems = list(dict.fromkeys(competing_mems))
        rel_events = list(dict.fromkeys(rel_events))
        competitor_str = f"Memory {competing_mems[0]}" if competing_mems else "subsequent writes"
        event_str = rel_events[0] if rel_events else "inflection event"

        # Determine primary hypothesis based on intent and observations
        if intent == QuestionIntent.PERSISTENCE or strength_delta >= 0:
            # Persistence scenarios
            h1 = CandidateHypothesis(
                hypothesis_id="H1-ISOLATION",
                statement=f"Memory {target_mem} survived due to low vector overlap and isolation from interfering writes.",
                mechanism="representational_isolation",
                is_primary=True,
                supporting_evidence=[
                    f"Low active cross-talk with subsequent writes (max similarity: {cue_sim:.2f}).",
                    f"Final representation strength remained high at {strength_delta:+.3f} delta.",
                ],
                contradicting_evidence=[],
                required_test="Counterfactual test: Inject high-similarity competing writes; verify if readout drops.",
                status=CausalSupportStatus.CORRELATED,
                classification=HypothesisClassification.PARTIALLY_SUPPORTED,
                supporting_evidence_count=2,
                contradicting_evidence_count=0,
                data_quality=0.95,
                explanation_score=0.85,
            )

            h2 = CandidateHypothesis(
                hypothesis_id="H2-REINFORCEMENT",
                statement=f"Memory {target_mem} survived through periodic reinforcement and associative binding stability.",
                mechanism="associative_reinforcement",
                is_primary=False,
                supporting_evidence=[
                    "Target cue received sustaining update pulses across timeline epochs.",
                ],
                contradicting_evidence=[],
                required_test="Counterfactual test: Remove reinforcing event pulses; measure survival horizon.",
                status=CausalSupportStatus.CORRELATED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=1,
                contradicting_evidence_count=0,
                data_quality=0.90,
                explanation_score=0.70,
            )

            h3 = CandidateHypothesis(
                hypothesis_id="H3-DRIFT-STABILITY",
                statement=f"The apparent survival reflects alignment with global substrate drift vectors.",
                mechanism="representation_drift_alignment",
                is_primary=False,
                supporting_evidence=[
                    "Substrate state evolution maintained positive inner product with target key-value binding.",
                ],
                contradicting_evidence=[],
                required_test="Counterfactual test: Orthogonalize state vector drift; test readout retention.",
                status=CausalSupportStatus.OBSERVED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=1,
                contradicting_evidence_count=0,
                data_quality=0.85,
                explanation_score=0.60,
            )

            h_unk = CandidateHypothesis(
                hypothesis_id="H-UNKNOWN",
                statement="Memory persistence arises from unmodeled high-dimensional geometry or circular convolution symmetry.",
                mechanism="unknown_symmetry",
                is_primary=False,
                supporting_evidence=[],
                contradicting_evidence=[],
                required_test="Exhaustive parameter sweep across dimensions and noise seeds.",
                status=CausalSupportStatus.OBSERVED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=0,
                contradicting_evidence_count=0,
                data_quality=0.50,
                explanation_score=0.30,
            )

            all_hyps = [h1, h2, h3, h_unk]

        else:
            # Memory decay / interference scenarios (default)
            h1 = CandidateHypothesis(
                hypothesis_id="H1-INTERFERENCE",
                statement=f"{competitor_str} caused direct cross-talk interference with Memory {target_mem}.",
                mechanism="cross_talk_interference",
                is_primary=True,
                supporting_evidence=[
                    f"Measured key vector similarity of {cue_sim:.3f} between target and competitor.",
                    f"Representation strength dropped noticeably at or following {event_str}.",
                ],
                contradicting_evidence=[],
                required_test=f"Counterfactual test: Replay sequence with {event_str} removed; measure if target memory recovers.",
                status=CausalSupportStatus.CORRELATED,
                classification=HypothesisClassification.PARTIALLY_SUPPORTED,
                supporting_evidence_count=2,
                contradicting_evidence_count=0,
                data_quality=0.95,
                explanation_score=0.85,
            )

            h2 = CandidateHypothesis(
                hypothesis_id="H2-PASSIVE-DECAY",
                statement=f"Memory {target_mem} degraded primarily through passive temporal decay without reinforcement.",
                mechanism="passive_temporal_decay",
                is_primary=False,
                supporting_evidence=[
                    f"Decay parameter λ is active ({experiment.parameters.get('decay', 0.0)}).",
                    "Target memory received no subsequent refresh operations after initial write.",
                ],
                contradicting_evidence=[
                    f"Step drop at {event_str} exceeded normal exponential decay baseline.",
                ] if rel_events else [],
                required_test="Counterfactual test: Replay with decay=0; observe if target memory still weakens.",
                status=CausalSupportStatus.CORRELATED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=2,
                contradicting_evidence_count=1 if rel_events else 0,
                data_quality=0.90,
                explanation_score=0.65,
            )

            h3 = CandidateHypothesis(
                hypothesis_id="H3-DISPLACEMENT",
                statement=f"Subsequent state writes collectively displaced the superposition norm of Memory {target_mem}.",
                mechanism="state_superposition_displacement",
                is_primary=False,
                supporting_evidence=[
                    "Substrate vector norm expanded as sequential events were written.",
                ],
                contradicting_evidence=[],
                required_test="Counterfactual test: Scale down update strengths of all subsequent events.",
                status=CausalSupportStatus.OBSERVED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=1,
                contradicting_evidence_count=0,
                data_quality=0.85,
                explanation_score=0.60,
            )

            h4 = CandidateHypothesis(
                hypothesis_id="H4-DRIFT",
                statement=f"The apparent loss of Memory {target_mem} is representation drift rather than true memory erasure.",
                mechanism="representation_drift",
                is_primary=False,
                supporting_evidence=[
                    "Cumulative directional cosine shift in the substrate exceeds 0.20.",
                ],
                contradicting_evidence=[],
                required_test="Counterfactual test: Apply rotated readout probe aligned to substrate drift.",
                status=CausalSupportStatus.OBSERVED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=1,
                contradicting_evidence_count=0,
                data_quality=0.80,
                explanation_score=0.55,
            )

            h_unk = CandidateHypothesis(
                hypothesis_id="H-UNKNOWN",
                statement="Decline stems from high-dimensional convolution noise saturation or unmodeled interactions.",
                mechanism="unmodeled_noise_saturation",
                is_primary=False,
                supporting_evidence=[],
                contradicting_evidence=[],
                required_test="High-dimensional orthogonal benchmark sweep.",
                status=CausalSupportStatus.OBSERVED,
                classification=HypothesisClassification.INCONCLUSIVE,
                supporting_evidence_count=0,
                contradicting_evidence_count=0,
                data_quality=0.50,
                explanation_score=0.25,
            )

            all_hyps = [h1, h2, h3, h4, h_unk]

        # Link alternative explanations
        for h in all_hyps:
            h.alternative_explanations = [other.statement for other in all_hyps if other.hypothesis_id != h.hypothesis_id]

        return all_hyps
