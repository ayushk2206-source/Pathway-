import React from 'react'
import type { StudioABComparison } from '../types'

interface ABComparisonViewProps {
  comparison: StudioABComparison
}

export const ABComparisonView: React.FC<ABComparisonViewProps> = ({ comparison }) => {
  const { exp_a, exp_b, diff_summary, differing_parameters } = comparison

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Parameter Difference Callout */}
      <div style={{
        background: 'rgba(56, 189, 248, 0.08)',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        borderRadius: '8px',
        padding: '0.75rem 1.25rem',
      }}>
        <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          Controlled Independent Variables
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '0.4rem' }}>
          {Object.entries(differing_parameters).map(([param, [valA, valB]]) => (
            <div key={param} style={{
              background: 'rgba(15, 23, 42, 0.8)',
              padding: '4px 10px',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              fontSize: '0.75rem',
            }}>
              <strong style={{ color: '#f8fafc' }}>{param}:</strong>{' '}
              <span style={{ color: '#94a3b8' }}>A({String(valA)})</span> →{' '}
              <span style={{ color: '#38bdf8', fontWeight: 700 }}>B({String(valB)})</span>
            </div>
          ))}
          {Object.keys(differing_parameters).length === 0 && (
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>No parameter differences detected between runs.</span>
          )}
        </div>
      </div>

      {/* Side-by-Side Cards */}
      <div className="studio-ab-grid">
        {/* Column A */}
        <div className="studio-ab-column">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#94a3b8' }}>
              CONFIGURATION A (BASELINE)
            </span>
            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>{exp_a.experiment_id}</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
            Concept: <strong>{exp_a.config.concept_a}</strong> · Type: <strong>{exp_a.config.experiment_type}</strong>
          </div>
          <table className="studio-metrics-table">
            <tbody>
              <tr>
                <td>Recall Fidelity</td>
                <td style={{ fontWeight: 700, color: '#38bdf8' }}>{exp_a.experiment_metrics.fidelity.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Crosstalk Noise</td>
                <td>{exp_a.experiment_metrics.crosstalk.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Matrix Norm ||W||_F</td>
                <td>{exp_a.experiment_metrics.matrix_norm.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Active Synapses</td>
                <td>{exp_a.experiment_metrics.active_synapses}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Column B */}
        <div className="studio-ab-column" style={{ borderColor: 'rgba(56, 189, 248, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#38bdf8' }}>
              CONFIGURATION B (TREATMENT)
            </span>
            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>{exp_b.experiment_id}</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
            Concept: <strong>{exp_b.config.concept_a}</strong> · Type: <strong>{exp_b.config.experiment_type}</strong>
          </div>
          <table className="studio-metrics-table">
            <tbody>
              <tr>
                <td>Recall Fidelity</td>
                <td style={{ fontWeight: 700, color: '#38bdf8' }}>{exp_b.experiment_metrics.fidelity.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Crosstalk Noise</td>
                <td>{exp_b.experiment_metrics.crosstalk.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Matrix Norm ||W||_F</td>
                <td>{exp_b.experiment_metrics.matrix_norm.toFixed(4)}</td>
              </tr>
              <tr>
                <td>Active Synapses</td>
                <td>{exp_b.experiment_metrics.active_synapses}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Difference Summary Table */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.75)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
        padding: '1rem',
      }}>
        <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.8rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.05em' }}>
          Δ DIFFERENCE SUMMARY (B - A)
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '6px' }}>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Fidelity Shift</div>
            <div style={{
              fontSize: '1.1rem',
              fontWeight: 800,
              color: diff_summary.fidelity_diff < 0 ? '#fb7185' : diff_summary.fidelity_diff > 0 ? '#34d399' : '#f8fafc',
              marginTop: '4px',
            }}>
              {diff_summary.fidelity_diff > 0 ? '+' : ''}{diff_summary.fidelity_diff.toFixed(4)}
            </div>
          </div>
          <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '6px' }}>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Crosstalk Shift</div>
            <div style={{
              fontSize: '1.1rem',
              fontWeight: 800,
              color: diff_summary.crosstalk_diff > 0 ? '#fb7185' : '#34d399',
              marginTop: '4px',
            }}>
              {diff_summary.crosstalk_diff > 0 ? '+' : ''}{diff_summary.crosstalk_diff.toFixed(4)}
            </div>
          </div>
          <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '6px' }}>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Matrix Norm Shift</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {diff_summary.matrix_norm_diff > 0 ? '+' : ''}{diff_summary.matrix_norm_diff.toFixed(4)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
