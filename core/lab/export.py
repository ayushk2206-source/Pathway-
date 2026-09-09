"""Dataset export utilities for Experiment Lab (Phase 03).

Exports experiment runs, sweeps, and multi-trial results into clean JSON and CSV formats
with complete provenance (experiment_id, trial_id, seed, mechanism, parameters, metrics).
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Union

from .models import LabExperiment, SweepResult


def export_experiment_json(experiment: Union[LabExperiment, Dict[str, Any]]) -> str:
    """Export the complete experimental record as indented JSON."""
    d = experiment.to_dict() if hasattr(experiment, "to_dict") else dict(experiment)
    return json.dumps(d, indent=2)


def export_experiment_csv(experiment: Union[LabExperiment, Dict[str, Any]]) -> str:
    """Export all trials and condition observations as a flattened, standard CSV string."""
    exp = experiment.to_dict() if hasattr(experiment, "to_dict") else dict(experiment)
    rows: List[Dict[str, Any]] = []

    exp_id = exp.get("experiment_id", "")
    mech = exp.get("mechanism", "")
    base_seed = exp.get("seed", 42)

    results = exp.get("results")
    if isinstance(results, dict) and "conditions" in results:
        # SweepResult export
        for cond in results.get("conditions", []):
            cond_label = cond.get("condition_label", "")
            params = cond.get("parameter_values", {})
            trials = cond.get("trials", [])

            if trials:
                for tr in trials:
                    row: Dict[str, Any] = {
                        "experiment_id": exp_id,
                        "condition": cond_label,
                        "trial_index": tr.get("trial_index", 0),
                        "seed": tr.get("seed", base_seed),
                        "mechanism": mech,
                        "underlying_experiment_id": tr.get("underlying_experiment_id", ""),
                    }
                    # Add parameters
                    for pk, pv in params.items():
                        row[f"param_{pk}"] = pv
                    # Add metrics
                    for mk, mv in tr.get("metrics", {}).items():
                        row[f"metric_{mk}"] = mv
                    rows.append(row)
            else:
                row = {
                    "experiment_id": exp_id,
                    "condition": cond_label,
                    "trial_index": 0,
                    "seed": base_seed,
                    "mechanism": mech,
                }
                for pk, pv in params.items():
                    row[f"param_{pk}"] = pv
                for mk, mv in cond.get("aggregated_metrics", {}).items():
                    row[f"metric_{mk}"] = mv.get("mean") if isinstance(mv, dict) else mv
                rows.append(row)
    else:
        # Single condition or comparison export
        row = {
            "experiment_id": exp_id,
            "title": exp.get("title", ""),
            "mechanism": mech,
            "seed": base_seed,
            "trials": exp.get("trials", 1),
            "status": exp.get("status", ""),
        }
        for mk, mv in exp.get("metrics", {}).items():
            if isinstance(mv, (int, float)):
                row[f"metric_{mk}"] = mv
        rows.append(row)

    if not rows:
        return "experiment_id,status\n"

    output = io.StringIO()
    # Gather all unique column headers maintaining logical order
    headers: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in headers:
                headers.append(k)

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

    return output.getvalue()
