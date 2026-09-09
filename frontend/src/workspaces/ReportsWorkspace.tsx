import React, { useState } from 'react'
import type { Experiment, XRayReport } from '../types'
import { getXRayReport } from '../api'

interface ReportsWorkspaceProps {
  experiment: Experiment | null
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

export const ReportsWorkspace: React.FC<ReportsWorkspaceProps> = ({
  experiment,
  onViewEvidence,
}) => {
  const [report, setReport] = useState<XRayReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>RESEARCH REPORTS · OFFLINE</h3>
        <p>Run or load an experiment to generate evidence-linked archaeological research reports.</p>
      </div>
    )
  }

  const handleGenerate = async () => {
    setIsLoading(true)
    try {
      const rep = await getXRayReport(experiment.experiment_id)
      setReport(rep)
    } catch (e) {
      alert(`Report generation failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleExportMarkdown = () => {
    if (!report) return
    const mdContent = `# Forensic Memory X-Ray Report: ${experiment.experiment_id}
Generated: ${new Date().toISOString()}
Mechanism: ${experiment.mechanism} (d=${experiment.task.d})

## Executive Summary
${report.summary}

## Key Archaeological Findings
${report.findings.map((f) => `- ${f}`).join('\n')}

## Statistical Anomalies (${report.anomalies.length})
${report.anomalies.map((a) => `- [${a.anomaly_type}] Step ${a.step}: ${a.description} (deviation: +${a.deviation.toFixed(2)}σ)`).join('\n')}

## Epistemic Boundaries & Scientific Invariants
1. PCA projections are dimensional reduction approximations only.
2. Readout metrics derive strictly from exact circular correlation unbinding.
3. No biological/neurological equivalence claims are made.
`
    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `xray_report_${experiment.experiment_id}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="reports-workspace-layout">
      {/* Header */}
      <div className="workspace-header-strip">
        <div>
          <h2 className="workspace-title">FORENSIC RESEARCH REPORT GENERATOR</h2>
          <div className="workspace-subtitle">
            Compile structured, deterministic evidence linking state update equations, observed memory lifecycles, and epistemic boundaries.
          </div>
        </div>

        <div className="report-action-buttons">
          <button className="primary" onClick={handleGenerate} disabled={isLoading}>
            {isLoading ? 'COMPILING EVIDENCE...' : '⚡ GENERATE X-RAY REPORT'}
          </button>
          {report && (
            <>
              <button
                className="secondary"
                onClick={() =>
                  onViewEvidence(`Report Evidence: ${report.experiment_id}`, {
                    experiment_id: report.experiment_id,
                    summary: report.summary,
                    findings: report.findings,
                    anomalies: report.anomalies,
                    recommendations: report.recommendations,
                    generated_at: report.generated_at,
                  })
                }
              >
                VIEW RAW EVIDENCE
              </button>
              <button onClick={handleExportMarkdown}>
                💾 EXPORT MARKDOWN
              </button>
            </>
          )}
        </div>
      </div>

      <div className="report-content-body">
        {report ? (
          <div className="report-document-card">
            <div className="doc-meta-strip">
              <span>REPORT FOR: <code>{report.experiment_id}</code></span>
              <span>MECHANISM: <strong className="cyan">{experiment.mechanism.toUpperCase()}</strong></span>
              <span>GENERATED: {new Date(report.generated_at).toLocaleString()}</span>
            </div>

            <div className="doc-section">
              <h3 className="section-heading">1. EXECUTIVE SUMMARY</h3>
              <p className="summary-paragraph">{report.summary}</p>
            </div>

            <div className="doc-section">
              <h3 className="section-heading">2. OBSERVED DYNAMICS & MEMORY EVOLUTION</h3>
              <div className="findings-list">
                {report.findings.map((f, idx) => (
                  <div key={idx} className="finding-row">
                    <span className="bullet cyan">◈</span>
                    <span>{f}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="doc-section">
              <h3 className="section-heading">3. STATISTICAL ANOMALIES</h3>
              {report.anomalies.length ? (
                <div className="anomalies-grid">
                  {report.anomalies.map((a, i) => (
                    <div key={i} className="report-anomaly-card">
                      <div className="type crimson">{a.anomaly_type}</div>
                      <div className="desc">{a.description}</div>
                      <div className="step-tag">TIMESTEP {a.step} · DEVIATION +{a.deviation.toFixed(2)}σ</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="clean-p">No statistically significant dimensional collapses or sudden jumps were detected.</p>
              )}
            </div>

            <div className="doc-section">
              <h3 className="section-heading">4. RECOMMENDATIONS & NEXT EXPERIMENTS</h3>
              <div className="recommendations-list">
                {report.recommendations.map((r, i) => (
                  <div key={i} className="rec-row">
                    <span className="bullet emerald">✔</span>
                    <span>{r}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="doc-section">
              <h3 className="section-heading">5. EPISTEMIC BOUNDARIES & LIMITATIONS</h3>
              <div className="limitations-box">
                <p>
                  <strong>Visualization Approximation:</strong> 2D PCA projections are dimensional approximations and must never be interpreted as exact Euclidean distances in the substrate.
                </p>
                <p>
                  <strong>No Biological Equivalence:</strong> All models are educational mathematical toy substrates using circular convolution binding; no human neurological equivalence is asserted.
                </p>
                <p>
                  <strong>Pure Grounding:</strong> All metrics, half-lives, and shifts are computed strictly with verifiable floating-point matrix arithmetic; zero generative text was hallucinated.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <div style={{ fontSize: '32px', marginBottom: '16px', color: 'var(--accent-cyan)' }}>📄</div>
            <h3>REPORT UNCOMPILED</h3>
            <p>
              Click <strong>GENERATE X-RAY REPORT</strong> to execute full evidence extraction across state transitions, interference degradation, and counterfactual trajectories.
            </p>
            <button className="primary" onClick={handleGenerate} disabled={isLoading}>
              GENERATE X-RAY REPORT
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
