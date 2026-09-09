import React from 'react'
import type { ChangeDetection } from '../types'

interface ChangeDetectorPanelProps {
  diff: ChangeDetection | null
  stepFrom: number
  stepTo: number
  isLoading?: boolean
}

export const ChangeDetectorPanel: React.FC<ChangeDetectorPanelProps> = ({
  diff,
  stepFrom,
  stepTo,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="diff-panel-container">
        <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Computing exact matrix differences...</p>
      </div>
    )
  }

  if (!diff) {
    return (
      <div className="diff-panel-container">
        <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
          Select two steps on the timeline to observe exact differential changes.
        </p>
      </div>
    )
  }

  return (
    <div className="diff-panel-container">
      <div style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>
        <strong>Comparing:</strong> Step {stepFrom} ➔ Step {stepTo}
      </div>

      <div className="diff-stat-cards">
        <div className="stat-card">
          <div className="stat-card-title">Strengthened</div>
          <div className="stat-card-value green">+{diff.strengthened_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-title">Weakened</div>
          <div className="stat-card-value amber">-{diff.weakened_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-title">Frobenius Δ</div>
          <div className="stat-card-value blue">{diff.frobenius_delta.toFixed(4)}</div>
        </div>
      </div>

      {diff.summary && (
        <div style={{
          padding: '0.6rem 0.8rem',
          borderRadius: '8px',
          background: 'rgba(30, 41, 59, 0.4)',
          border: '1px solid rgba(71, 85, 105, 0.3)',
          fontSize: '0.8rem',
          color: '#e2e8f0',
        }}>
          {diff.summary}
        </div>
      )}

      {diff.probe_fidelity_deltas && Object.keys(diff.probe_fidelity_deltas).length > 0 && (
        <div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem', fontWeight: 600 }}>
            PROBE FIDELITY DELTAS:
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {Object.entries(diff.probe_fidelity_deltas).map(([concept, delta]) => (
              <span
                key={concept}
                style={{
                  fontSize: '0.75rem',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  background: delta > 0 ? 'rgba(16, 185, 129, 0.15)' : delta < 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(51, 65, 85, 0.4)',
                  color: delta > 0 ? '#34d399' : delta < 0 ? '#f87171' : '#cbd5e1',
                  border: `1px solid ${delta > 0 ? 'rgba(16, 185, 129, 0.3)' : delta < 0 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(71, 85, 105, 0.3)'}`,
                  fontFamily: 'Courier New, monospace',
                }}
              >
                {concept}: {delta > 0 ? `+${(delta * 100).toFixed(1)}%` : `${(delta * 100).toFixed(1)}%`}
              </span>
            ))}
          </div>
        </div>
      )}

      {diff.top_modified_synapses && diff.top_modified_synapses.length > 0 && (
        <div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem', fontWeight: 600 }}>
            TOP MODIFIED SYNAPSES:
          </div>
          <div style={{ maxHeight: '130px', overflowY: 'auto' }}>
            <table className="diff-top-synapses-table">
              <thead>
                <tr>
                  <th>Synapse</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Delta</th>
                </tr>
              </thead>
              <tbody>
                {diff.top_modified_synapses.slice(0, 5).map((syn) => (
                  <tr key={`${syn.row}-${syn.col}`}>
                    <td>({syn.row}, {syn.col})</td>
                    <td>{syn.from_weight.toFixed(4)}</td>
                    <td>{syn.to_weight.toFixed(4)}</td>
                    <td style={{ color: syn.delta > 0 ? '#34d399' : '#fbbf24' }}>
                      {syn.delta > 0 ? `+${syn.delta.toFixed(4)}` : syn.delta.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
