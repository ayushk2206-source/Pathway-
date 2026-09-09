import React from 'react'
import type { StudioExperimentResult } from '../types'

interface ExperimentResultViewProps {
  result: StudioExperimentResult
  onDuplicateBranch: () => void
  onExport: () => void
}

export const ExperimentResultView: React.FC<ExperimentResultViewProps> = ({
  result,
  onDuplicateBranch,
  onExport,
}) => {
  const b = result.baseline_metrics
  const e = result.experiment_metrics
  const d = result.delta_metrics

  const formatDelta = (val: number) => {
    const sign = val > 0 ? '+' : ''
    return `${sign}${val.toFixed(3)}`
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header with Prediction Verification */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1rem',
        background: 'rgba(15, 23, 42, 0.8)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#f8fafc' }}>
            {result.config.name}
          </span>
          <span style={{
            fontSize: '0.68rem',
            fontWeight: 800,
            padding: '2px 6px',
            borderRadius: '4px',
            background: 'rgba(56, 189, 248, 0.15)',
            color: '#38bdf8',
            border: '1px solid rgba(56, 189, 248, 0.3)',
          }}>
            {result.config.experiment_type}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={onDuplicateBranch}
            style={{
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: 700,
              background: 'rgba(129, 140, 248, 0.15)',
              border: '1px solid #818cf8',
              borderRadius: '5px',
              color: '#a5b4fc',
              cursor: 'pointer',
            }}
          >
            🌿 DUPLICATE & BRANCH
          </button>
          <button
            onClick={onExport}
            style={{
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: 700,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '5px',
              color: '#f8fafc',
              cursor: 'pointer',
            }}
          >
            ⤓ EXPORT JSON
          </button>
        </div>
      </div>

      {/* Hypothesis & Prediction Outcome Banner */}
      <div style={{
        padding: '0.75rem 1rem',
        borderRadius: '8px',
        background: result.hypothesis.support_status === 'SUPPORTED' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
        border: `1px solid ${result.hypothesis.support_status === 'SUPPORTED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.35rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>
            Hypothesis Evaluation
          </span>
          <span style={{
            fontSize: '0.68rem',
            fontWeight: 800,
            padding: '2px 8px',
            borderRadius: '4px',
            background: result.hypothesis.support_status === 'SUPPORTED' ? '#10b981' : '#f59e0b',
            color: '#030712',
          }}>
            {result.hypothesis.support_status}
          </span>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#f8fafc' }}>
          <strong>Predicted:</strong> {result.hypothesis.predicted_outcome} · <strong>Observed:</strong> {result.hypothesis.actual_outcome}
        </div>
        <div style={{ fontSize: '0.74rem', color: '#cbd5e1' }}>
          <em>"{result.hypothesis.hypothesis_text}"</em>
        </div>
      </div>

      {/* Baseline vs Experiment Quantitative Matrix */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.7)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
        padding: '1rem',
      }}>
        <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.8rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.05em' }}>
          MEASURED RESULTS: BASELINE VS EXPERIMENT
        </h4>

        <table className="studio-metrics-table">
          <thead>
            <tr>
              <th>METRIC</th>
              <th>BASELINE</th>
              <th>EXPERIMENT</th>
              <th>Δ DIFFERENCE</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Recall Fidelity (cos(v, v̂))</td>
              <td>{b.fidelity.toFixed(4)}</td>
              <td>{e.fidelity.toFixed(4)}</td>
              <td>
                <span className={`studio-delta-badge ${d.fidelity_delta < -0.02 ? 'negative' : d.fidelity_delta > 0.02 ? 'positive' : 'neutral'}`}>
                  {formatDelta(d.fidelity_delta)}
                </span>
              </td>
            </tr>
            <tr>
              <td>Crosstalk Noise ||v̂ - v||</td>
              <td>{b.crosstalk.toFixed(4)}</td>
              <td>{e.crosstalk.toFixed(4)}</td>
              <td>
                <span className={`studio-delta-badge ${d.crosstalk_delta > 0.05 ? 'negative' : 'neutral'}`}>
                  {formatDelta(d.crosstalk_delta)}
                </span>
              </td>
            </tr>
            <tr>
              <td>Matrix Frobenius Norm ||W||_F</td>
              <td>{b.matrix_norm.toFixed(4)}</td>
              <td>{e.matrix_norm.toFixed(4)}</td>
              <td>
                <span className="studio-delta-badge neutral">
                  {formatDelta(d.matrix_norm_delta)}
                </span>
              </td>
            </tr>
            <tr>
              <td>Active Synapses (|W_rc| &gt; 0.01)</td>
              <td>{b.active_synapses}</td>
              <td>{e.active_synapses}</td>
              <td>
                <span className="studio-delta-badge neutral">
                  {formatDelta(d.active_synapses_delta)}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Top Synaptic Changes */}
      {result.top_synaptic_changes.length > 0 && (
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '1rem',
        }}>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.05em' }}>
            TOP MODIFIED SYNAPTIC CONNECTIONS (ΔW)
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.5rem' }}>
            {result.top_synaptic_changes.slice(0, 6).map((syn, idx) => (
              <div key={idx} style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                padding: '0.5rem',
                fontSize: '0.72rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#38bdf8', fontWeight: 700, fontFamily: 'monospace' }}>
                  <span>W[{syn.row}, {syn.col}]</span>
                  <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>[{syn.tag}]</span>
                </div>
                <div style={{ color: '#cbd5e1', marginTop: '2px' }}>
                  {syn.weight_before.toFixed(3)} → <strong>{syn.weight_after.toFixed(3)}</strong>
                </div>
                <div style={{ color: syn.delta < 0 ? '#fb7185' : '#34d399', fontWeight: 700 }}>
                  Δ {syn.delta > 0 ? '+' : ''}{syn.delta.toFixed(3)} ({syn.pct_change.toFixed(1)}%)
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Factual Observation & Scientific Interpretation */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div className="studio-claim-box observation">
          <div style={{ fontWeight: 800, fontSize: '0.7rem', color: '#38bdf8', letterSpacing: '0.06em', marginBottom: '4px' }}>
            [OBSERVED COMPUTATION]
          </div>
          {result.observation_statements.map((obs, i) => (
            <p key={i} style={{ margin: '0 0 4px 0' }}>• {obs}</p>
          ))}
        </div>

        <div className="studio-claim-box interpretation">
          <div style={{ fontWeight: 800, fontSize: '0.7rem', color: '#a5b4fc', letterSpacing: '0.06em', marginBottom: '4px' }}>
            [SCIENTIFIC INTERPRETATION]
          </div>
          {result.interpretation_statements.map((interp, i) => (
            <p key={i} style={{ margin: '0 0 4px 0' }}>• {interp}</p>
          ))}
        </div>
      </div>
    </div>
  )
}
