"""Export serialization for counterfactual experiments in JSON and CSV formats (Phase 04)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict

from .models import CounterfactualExperiment


def export_counterfactual_json(cf: CounterfactualExperiment, indent: int = 2) -> str:
    """Export complete counterfactual experiment including original and alternate results with full provenance."""
    d = cf.to_dict()
    return json.dumps(d, indent=indent)


def export_divergence_csv(cf: CounterfactualExperiment) -> str:
    """Export the step-by-step divergence trajectory as a clean CSV table."""
    timeline = cf.divergence.get("timeline", [])
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "step",
        "event_id",
        "state_distance_l2",
        "cosine_similarity",
        "relative_l2",
        "recall_accuracy_delta",
    ])

    for item in timeline:
        deltas = item.get("metric_delta", {})
        writer.writerow([
            item.get("step", 0),
            item.get("event_id", ""),
            f"{item.get('state_distance_l2', 0.0):.6f}",
            f"{item.get('cosine_similarity', 1.0):.6f}",
            f"{item.get('relative_l2', 0.0):.6f}",
            f"{deltas.get('recall_accuracy_delta', 0.0):.6f}" if "recall_accuracy_delta" in deltas else "",
        ])

    return output.getvalue()
