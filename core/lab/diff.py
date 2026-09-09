"""Experiment difference and comparison tool for Experiment Lab (Phase 03).

Provides structured comparison between two lab experiments or runs, identifying
changed parameters, conditions, metric shifts, and sequence alterations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np

from .models import LabExperiment


def diff_lab_experiments(
    exp_a: Union[LabExperiment, Dict[str, Any]],
    exp_b: Union[LabExperiment, Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate structured differences between two lab experiments."""
    da = exp_a.to_dict() if hasattr(exp_a, "to_dict") else dict(exp_a)
    db = exp_b.to_dict() if hasattr(exp_b, "to_dict") else dict(exp_b)

    # 1. Parameter / Configuration differences
    param_diffs: Dict[str, Dict[str, Any]] = {}
    base_a = da.get("baseline_configuration", {}) or {}
    base_b = db.get("baseline_configuration", {}) or {}
    all_keys = sorted(set(base_a.keys()) | set(base_b.keys()))

    for k in all_keys:
        va, vb = base_a.get(k), base_b.get(k)
        if va != vb:
            param_diffs[k] = {"old": va, "new": vb}

    # Meta differences
    meta_diffs: Dict[str, Dict[str, Any]] = {}
    for meta_k in ["mechanism", "seed", "trials", "version", "status"]:
        ma, mb = da.get(meta_k), db.get(meta_k)
        if ma != mb:
            meta_diffs[meta_k] = {"old": ma, "new": mb}

    # 2. Metric differences
    metric_diffs: Dict[str, Dict[str, Any]] = {}
    ma = da.get("metrics", {}) or {}
    mb = db.get("metrics", {}) or {}
    for m_k in sorted(set(ma.keys()) | set(mb.keys())):
        v_a = ma.get(m_k)
        v_b = mb.get(m_k)
        if isinstance(v_a, (int, float)) and isinstance(v_b, (int, float)):
            delta = float(v_b - v_a)
            metric_diffs[m_k] = {
                "old": round(float(v_a), 6),
                "new": round(float(v_b), 6),
                "delta": round(delta, 6),
                "pct_change": round((delta / abs(v_a) * 100.0), 2) if abs(v_a) > 1e-6 else None,
            }

    is_identical = (
        len(param_diffs) == 0
        and len(meta_diffs) == 0
        and len(metric_diffs) == 0
        and da.get("independent_variables") == db.get("independent_variables")
    )

    return {
        "experiment_a_id": da.get("experiment_id"),
        "experiment_b_id": db.get("experiment_id"),
        "is_identical": is_identical,
        "parameter_changes": param_diffs,
        "meta_changes": meta_diffs,
        "metric_changes": metric_diffs,
        "independent_variables_a": da.get("independent_variables", []),
        "independent_variables_b": db.get("independent_variables", []),
    }
