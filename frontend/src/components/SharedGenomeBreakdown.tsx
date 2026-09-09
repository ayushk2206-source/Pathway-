import React, { useState } from 'react'
import type { FingerprintComparison } from '../types'

interface SharedGenomeBreakdownProps {
  comparison: FingerprintComparison | null
  onTriggerSurgery?: (row: number, col: number) => void
}

export const SharedGenomeBreakdown: React.FC<SharedGenomeBreakdownProps> = ({
  comparison,
  onTriggerSurgery,
}) => {
  const [activeTab, setActiveTab] = useState<'shared' | 'a_only' | 'b_only'>('shared')

  if (!comparison) {
    return (
      <div className="forensic-card" style={{ color: '#64748b', fontSize: '0.85rem' }}>
        Select a pair of memories to inspect shared synaptic genome.
      </div>
    )
  }

  const jaccardPct = Math.round(comparison.synaptic_overlap_jaccard * 100)

  return (
    <div className="forensic-card">
      <div className="forensic-card-header">
        <h3 className="forensic-card-title">
          <span>Shared Synaptic Genome (Phase 17 Partition)</span>
        </h3>
        <span style={{ fontSize: '0.78rem', color: '#38bdf8', fontWeight: 600 }}>
          Jaccard Overlap: {jaccardPct}% ({comparison.shared_synapses.length} Shared Synapses)
        </span>
      </div>

      <div style={{ display: 'flex', gap: '0.4rem', borderBottom: '1px solid rgba(71, 85, 105, 0.4)', paddingBottom: '0.5rem' }}>
        <button
          className={`concept-chip ${activeTab === 'shared' ? 'active' : ''}`}
          onClick={() => setActiveTab('shared')}
        >
          Shared ({comparison.shared_synapses.length})
        </button>
        <button
          className={`concept-chip ${activeTab === 'a_only' ? 'active' : ''}`}
          onClick={() => setActiveTab('a_only')}
        >
          {comparison.concept_a} Only ({comparison.a_only_synapses.length})
        </button>
        <button
          className={`concept-chip ${activeTab === 'b_only' ? 'active' : ''}`}
          onClick={() => setActiveTab('b_only')}
        >
          {comparison.concept_b} Only ({comparison.b_only_synapses.length})
        </button>
      </div>

      <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
        <table className="shared-genome-table">
          <thead>
            {activeTab === 'shared' ? (
              <tr>
                <th>Synapse</th>
                <th>ΔW ({comparison.concept_a})</th>
                <th>ΔW ({comparison.concept_b})</th>
                <th>Intervention</th>
              </tr>
            ) : (
              <tr>
                <th>Synapse</th>
                <th>ΔW</th>
                <th>Status</th>
              </tr>
            )}
          </thead>
          <tbody>
            {activeTab === 'shared' &&
              comparison.shared_synapses.map(([r, c, wa, wb]) => (
                <tr key={`${r}-${c}`}>
                  <td>({r}, {c})</td>
                  <td style={{ color: wa > 0 ? '#34d399' : '#fbbf24' }}>{wa > 0 ? `+${wa.toFixed(4)}` : wa.toFixed(4)}</td>
                  <td style={{ color: wb > 0 ? '#34d399' : '#fbbf24' }}>{wb > 0 ? `+${wb.toFixed(4)}` : wb.toFixed(4)}</td>
                  <td>
                    <button
                      className="scanner-btn"
                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                      onClick={() => onTriggerSurgery?.(r, c)}
                      title="Operate on this shared synapse via Synaptic Surgery"
                    >
                      ⚕ Surgery
                    </button>
                  </td>
                </tr>
              ))}

            {activeTab === 'a_only' &&
              comparison.a_only_synapses.map(([r, c, w]) => (
                <tr key={`${r}-${c}`}>
                  <td>({r}, {c})</td>
                  <td style={{ color: w > 0 ? '#34d399' : '#fbbf24' }}>{w > 0 ? `+${w.toFixed(4)}` : w.toFixed(4)}</td>
                  <td style={{ color: '#94a3b8' }}>Unique to A</td>
                </tr>
              ))}

            {activeTab === 'b_only' &&
              comparison.b_only_synapses.map(([r, c, w]) => (
                <tr key={`${r}-${c}`}>
                  <td>({r}, {c})</td>
                  <td style={{ color: w > 0 ? '#34d399' : '#fbbf24' }}>{w > 0 ? `+${w.toFixed(4)}` : w.toFixed(4)}</td>
                  <td style={{ color: '#94a3b8' }}>Unique to B</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
