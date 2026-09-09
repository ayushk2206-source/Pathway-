"""Scientific report generator for Experiment Lab (Phase 03).

Generates a formal 10-section markdown research report summarizing an experiment's
question, hypothesis, setup, variables, controls, empirical results, observed patterns,
prediction alignment, limitations, and conclusions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from .hypotheses import Hypothesis, PredictionEvaluation
from .models import ComparisonResult, GridResult, LabExperiment, SweepResult


def _fmt_val(val: Any, prec: int = 4) -> str:
    if val is None or not isinstance(val, (int, float)):
        return "—"
    return f"{val:.{prec}f}"


def generate_scientific_report(
    experiment: Union[LabExperiment, Dict[str, Any]],
    hypothesis: Optional[Union[Hypothesis, Dict[str, Any]]] = None,
    evaluation: Optional[Union[PredictionEvaluation, Dict[str, Any]]] = None,
) -> str:
    """Generate a rigorous 10-section markdown scientific report from empirical data."""
    exp = experiment.to_dict() if hasattr(experiment, "to_dict") else dict(experiment)
    hyp = hypothesis.to_dict() if hasattr(hypothesis, "to_dict") and hypothesis else (dict(hypothesis) if hypothesis else {})
    eval_dict = evaluation.to_dict() if hasattr(evaluation, "to_dict") and evaluation else (dict(evaluation) if evaluation else {})

    title = exp.get("title", "Computational Memory Investigation")
    q = exp.get("research_question", "Unspecified research question")
    h_stmt = hyp.get("statement") or exp.get("hypothesis") or "No explicit hypothesis recorded."
    mech = exp.get("mechanism", "unspecified")
    trials = exp.get("trials", 1)
    seed = exp.get("seed", 42)

    indep = exp.get("independent_variables", [])
    dep = exp.get("dependent_variables", [])
    ctrls = exp.get("controlled_variables", {})

    lines: list[str] = [
        f"# Scientific Research Report: {title}",
        f"**Experiment ID**: `{exp.get('experiment_id')}` | **Version**: `v{exp.get('version', 1)}` | **Status**: `{exp.get('status', 'completed')}`",
        f"**Generated**: {exp.get('created_at', 'N/A')}",
        "",
        "---",
        "",
        "## 1. Research Question",
        f"> {q}",
        "",
        "## 2. Hypothesis & Predictions",
        f"- **Hypothesis Statement**: {h_stmt}",
    ]

    if hyp:
        lines.append(f"- **Predicted Direction**: `{hyp.get('predicted_direction', 'N/A')}`")
        if hyp.get("expected_relationship"):
            lines.append(f"- **Expected Relationship**: {hyp['expected_relationship']}")
        lines.append(f"- **Prior Confidence**: `{hyp.get('confidence_before', 0.5):.2f}` -> **Posterior Confidence**: `{hyp.get('confidence_after', 0.5):.2f}`")

    lines.extend([
        "",
        "## 3. Experimental Setup",
        f"- **Computational Substrate**: Holographic circular convolution binding with flat-spectrum keys.",
        f"- **Mechanism Architecture**: `{mech}`",
        f"- **Repeated Trials**: `{trials}` (deterministic derived seeds derived from master seed `{seed}`)",
        "",
        "## 4. Experimental Variables",
        f"- **Independent Variables**: {', '.join(f'`{v}`' for v in indep) if indep else 'None specified'}",
        f"- **Dependent Metrics Observed**: {', '.join(f'`{v}`' for v in dep) if dep else 'Standard metrics'}",
        "",
        "## 5. Controlled Variables",
    ])

    if ctrls:
        lines.append("| Variable | Controlled Value |")
        lines.append("|---|---|")
        for k, v in ctrls.items():
            lines.append(f"| `{k}` | `{v}` |")
    else:
        lines.append("*All secondary parameters held constant at baseline defaults.*")

    lines.extend([
        "",
        "## 6. Empirical Results",
    ])

    results = exp.get("results")
    if isinstance(results, dict) and "parameter" in results:
        # Sweep report table
        param = results["parameter"]
        conds = results.get("conditions", [])
        lines.append(f"**Parameter Sweep across `{param}`**:")
        lines.append("")
        lines.append(f"| `{param}` | Retention | Interference | Accuracy | Recovery |")
        lines.append("|---|---|---|---|---|")
        for c in conds:
            p_val = c.get("parameter_values", {}).get(param, "N/A")
            agg = c.get("aggregated_metrics", {})
            ret = agg.get("memory_retention", {}).get("mean")
            inter = agg.get("interference_score", {}).get("mean")
            acc = agg.get("recall_accuracy", {}).get("mean")
            rec = agg.get("recovery_score", {}).get("mean")
            lines.append(
                f"| `{p_val}` | {_fmt_val(ret)} | "
                f"{_fmt_val(inter)} | "
                f"{_fmt_val(acc)} | "
                f"{_fmt_val(rec)} |"
            )
    elif isinstance(results, dict) and "baseline_condition" in results:
        lines.append("**Controlled Baseline vs Treatment Comparison**:")
        deltas = results.get("metric_deltas", {})
        pcts = results.get("percentage_changes", {})
        lines.append("")
        lines.append("| Metric | Delta (Treatment - Baseline) | Relative Shift |")
        lines.append("|---|---|---|")
        for m_key, delta_val in deltas.items():
            pct_val = pcts.get(m_key)
            pct_str = f"{pct_val:+.2f}%" if pct_val is not None else "N/A"
            lines.append(f"| `{m_key}` | `{delta_val:+.4f}` | {pct_str} |")
    else:
        m_dict = exp.get("metrics", {})
        if m_dict:
            lines.append("| Metric | Observed Value |")
            lines.append("|---|---|")
            for k, v in m_dict.items():
                if isinstance(v, (int, float)):
                    lines.append(f"| `{k}` | `{v:.4f}` |")

    lines.extend([
        "",
        "## 7. Observed Relationships & Patterns",
    ])

    if isinstance(results, dict) and "relationship_analysis" in results:
        rel = results["relationship_analysis"]
        for m_key, analysis in rel.items():
            lines.append(f"- **`{m_key}`**: {analysis.get('scientific_summary', 'Analyzed')}")
        pats = results.get("detected_pattern", {})
        for m_key, pat in pats.items():
            lines.append(f"  - Pattern classification: `{pat.get('pattern')}` (confidence: {pat.get('confidence', 0.5):.2f}) — {pat.get('details', '')}")
    else:
        lines.append("Single condition or comparative test completed without sweep curve regression.")

    lines.extend([
        "",
        "## 8. Prediction vs Observation Analysis",
    ])

    if eval_dict:
        lines.append(f"- **Predicted**: `{eval_dict.get('prediction', {}).get('predicted_direction')}`")
        lines.append(f"- **Observed**: `{eval_dict.get('observed_direction')}`")
        lines.append(f"- **Outcome**: {'Confirmed by observation' if eval_dict.get('prediction_correct') else 'Discrepant with observation'}")
        lines.append(f"- **Analysis**: {eval_dict.get('verdict')}")
    else:
        lines.append("No explicit pre-trial formal prediction was registered for this run.")

    lines.extend([
        "",
        "## 9. Methodological Limitations",
        "- **Computational Model**: The observed phenomena are derived from mathematical simulations of superposition, decay, and state interference, and are not claimed as biological neuroscience proofs or production transformer architectures.",
        "- **Synthetic Representation**: Concepts and cues are synthetic vector representations; ground truth is dictated by the generated event stream history.",
        "- **Causal Scoping**: Numerical correlations and gradients reflect computational system mechanics under specified controls; caution should be exercised before generalizing beyond the parameter envelope.",
        "",
        "## 10. Conclusion & Recommended Next Experiments",
        f"- **Primary Observation**: {exp.get('conclusion') or 'The computational memory substrate exhibited behavior consistent with its mathematical update formulation.'}",
        "- **Recommended Investigation**: Follow up with discriminating experiments holding write gain constant or test under high cue interference regimes.",
        "",
        "---",
        "*Neural Archaeology Scientific Lab Console — Phase 03 Automated Research Report.*",
    ])

    return "\n".join(lines)
