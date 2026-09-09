"""Deterministic question classification layer (Phase 07)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .types import QuestionIntent


INTENT_PATTERNS: List[tuple[QuestionIntent, List[re.Pattern]]] = [
    (
        QuestionIntent.INTERFERENCE,
        [
            re.compile(r"\b(interfere|interference|conflict|compete|competition|cross-talk|crosstalk|overwrite)\b", re.IGNORECASE),
            re.compile(r"\bwhy did (these|two) memories\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.MEMORY_DECAY,
        [
            re.compile(r"\b(weaken|weakened|decay|decayed|fading|fade|loss|forgotten|drop|dropped|degrade)\b", re.IGNORECASE),
            re.compile(r"\bwhy did (this|the) memory weaken\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.PERSISTENCE,
        [
            re.compile(r"\b(survive|survived|persist|persistence|persistent|stable|retention|remain|alive)\b", re.IGNORECASE),
            re.compile(r"\bwhy did (this|the) memory survive\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.MEMORY_REINFORCEMENT,
        [
            re.compile(r"\b(reinforce|reinforcement|reinforced|strengthen|strengthened|boost|repeat|repetition)\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.COUNTERFACTUAL,
        [
            re.compile(r"\b(counterfactual|diverge|diverged|divergence|branch|what if|intervention|surgery)\b", re.IGNORECASE),
            re.compile(r"\bwhy did the counterfactual diverge\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.EVENT_IMPACT,
        [
            re.compile(r"\b(which event|event mattered|matter most|event impact|caused by event)\b", re.IGNORECASE),
            re.compile(r"\bwhat caused this\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.STATE_SHIFT,
        [
            re.compile(r"\b(state transition|state shift|drift|vector shift|representation drift|norm jump)\b", re.IGNORECASE),
            re.compile(r"\bwhat caused this state transition\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.RETRIEVAL,
        [
            re.compile(r"\b(retrieval|recall|query|probe|unbinding|readout|accuracy|confidence)\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.SPARSITY,
        [
            re.compile(r"\b(sparsity|sparse|active dimension|dead unit|k-wta|dimension collapse)\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.ASSOCIATION,
        [
            re.compile(r"\b(association|associate|cluster|similarity|overlap|neighbor)\b", re.IGNORECASE),
        ],
    ),
    (
        QuestionIntent.ANOMALY,
        [
            re.compile(r"\b(anomaly|abnormal|instability|jump|sudden drop|spike)\b", re.IGNORECASE),
        ],
    ),
]


REQUIRED_DATA_BY_INTENT: Dict[QuestionIntent, List[str]] = {
    QuestionIntent.INTERFERENCE: [
        "memory_strength_trajectory",
        "competition_graph",
        "interference_records",
        "cue_similarities",
    ],
    QuestionIntent.MEMORY_DECAY: [
        "memory_strength_trajectory",
        "reinforcement_history",
        "decay_parameter",
        "timeline_events",
    ],
    QuestionIntent.PERSISTENCE: [
        "memory_strength_trajectory",
        "isolation_index",
        "reinforcement_count",
        "cue_similarities",
    ],
    QuestionIntent.MEMORY_REINFORCEMENT: [
        "reinforcement_events",
        "strength_delta_per_write",
        "saturation_threshold",
    ],
    QuestionIntent.COUNTERFACTUAL: [
        "branch_point",
        "divergence_profile",
        "state_distance_l2",
        "affected_memories",
    ],
    QuestionIntent.EVENT_IMPACT: [
        "state_delta_norm",
        "cosine_shift",
        "memory_impact_list",
        "timeline_events",
    ],
    QuestionIntent.STATE_SHIFT: [
        "state_trajectory",
        "step_distances",
        "top_shifted_dimensions",
    ],
    QuestionIntent.RETRIEVAL: [
        "query_history",
        "confusion_matrix",
        "readout_similarities",
    ],
    QuestionIntent.SPARSITY: [
        "timeline_sparsity",
        "dead_units",
        "activation_quantiles",
    ],
    QuestionIntent.ASSOCIATION: [
        "memory_map_points",
        "clusters",
        "key_vector_correlations",
    ],
    QuestionIntent.ANOMALY: [
        "anomaly_records",
        "z_score_deviations",
        "metric_timelines",
    ],
}


AVAILABLE_TESTS_BY_INTENT: Dict[QuestionIntent, List[str]] = {
    QuestionIntent.INTERFERENCE: [
        "remove_competing_event",
        "isolate_cue_vector",
        "delay_competing_write",
        "scale_interference_strength",
    ],
    QuestionIntent.MEMORY_DECAY: [
        "reinforce_at_interval",
        "zero_decay_parameter",
        "advance_readout_probe",
    ],
    QuestionIntent.PERSISTENCE: [
        "inject_competing_noise",
        "remove_reinforcements",
        "increase_temporal_horizon",
    ],
    QuestionIntent.MEMORY_REINFORCEMENT: [
        "remove_reinforcement_event",
        "double_write_strength",
    ],
    QuestionIntent.COUNTERFACTUAL: [
        "reproduce_branch",
        "minimum_intervention_search",
        "sensitivity_sweep",
    ],
    QuestionIntent.EVENT_IMPACT: [
        "remove_target_event",
        "modify_event_strength",
        "shift_event_timing",
    ],
    QuestionIntent.STATE_SHIFT: [
        "freeze_state_at_step",
        "remove_transition_trigger",
    ],
    QuestionIntent.RETRIEVAL: [
        "probe_at_every_step",
        "re-orthogonalize_cues",
    ],
    QuestionIntent.SPARSITY: [
        "toggle_kwta_threshold",
        "prune_inactive_units",
    ],
    QuestionIntent.ASSOCIATION: [
        "orthogonalize_associated_pair",
        "cluster_ablation",
    ],
    QuestionIntent.ANOMALY: [
        "smooth_input_noise",
        "remove_anomaly_event",
    ],
}


class DeterministicQuestionParser:
    """Classifies researcher questions deterministically into concrete computational intents."""

    @classmethod
    def parse(
        cls,
        question: str,
        known_memories: Optional[List[str]] = None,
        known_events: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        cleaned = question.strip()

        # 1. Match Intent
        detected_intent = QuestionIntent.INTERFERENCE  # default fallback
        for intent, patterns in INTENT_PATTERNS:
            if any(pat.search(cleaned) for pat in patterns):
                detected_intent = intent
                break

        # 2. Extract Target Memory
        target_memory = None
        if known_memories:
            for m in known_memories:
                if re.search(rf"\b{re.escape(m)}\b", cleaned, re.IGNORECASE):
                    target_memory = m
                    break

        if not target_memory:
            # Look for common label patterns e.g. "Memory A", "obj_A", "mem_0"
            m_match = re.search(r"\b(Memory\s+([A-Z0-9_]+)|obj_[A-Z0-9_]+|mem_[0-9]+)\b", cleaned, re.IGNORECASE)
            if m_match:
                target_memory = m_match.group(2) if m_match.group(2) else m_match.group(1)

        # 3. Extract Target Event
        target_event = None
        if known_events:
            for ev in known_events:
                if re.search(rf"\b{re.escape(ev)}\b", cleaned, re.IGNORECASE):
                    target_event = ev
                    break

        if not target_event:
            ev_match = re.search(r"\b(E[0-9]+|event\s*([0-9]+)|step\s*([0-9]+))\b", cleaned, re.IGNORECASE)
            if ev_match:
                target_event = ev_match.group(0)

        required_data = REQUIRED_DATA_BY_INTENT.get(detected_intent, [])
        available_tests = AVAILABLE_TESTS_BY_INTENT.get(detected_intent, [])

        return {
            "intent": detected_intent.value,
            "target_memory": target_memory,
            "target_event": target_event,
            "required_data": required_data,
            "available_tests": available_tests,
            "is_deterministic": True,
            "original_question": cleaned,
        }
