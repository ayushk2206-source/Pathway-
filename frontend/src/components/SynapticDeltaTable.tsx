import React, { useState } from 'react'
import type { SynapticDeltaItem } from '../types'

interface SynapticDeltaTableProps {
  deltas: SynapticDeltaItem[]
  selectedSynapseId: string | null
  onSelectSynapse: (synapseId: string | null) => void
}

export const SynapticDeltaTable: React.FC<SynapticDeltaTableProps> = ({
  deltas,
  selectedSynapseId,
  onSelectSynapse,
}) => {
  const [filter, setFilter] = useState<'ALL' | 'STRENGTHENED' | 'WEAKENED'>('ALL')
  const [searchTerm, setSearchTerm] = useState('')

  const filtered = deltas.filter((d) => {
    if (filter === 'STRENGTHENED' && d.delta <= 0) return false
    if (filter === 'WEAKENED' && d.delta >= 0) return false
    if (searchTerm && !d.synapse_id.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  return (
    <div className="synaptic-delta-card">
      <div className="delta-table-header">
        <div className="title-group">
          <span className="delta-glyph">Δ</span>
          <span className="delta-title">SYNAPTIC DELTA (ACTUAL COMPUTATIONAL DATA)</span>
          <span className="count-badge">{deltas.length} Synapses Altered</span>
        </div>
        <div className="delta-filters">
          <input
            type="text"
            placeholder="Filter synapse..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="delta-search-input"
          />
          <div className="btn-group">
            <button
              className={`filter-btn ${filter === 'ALL' ? 'active' : ''}`}
              onClick={() => setFilter('ALL')}
            >
              ALL
            </button>
            <button
              className={`filter-btn ${filter === 'WEAKENED' ? 'active crimson' : ''}`}
              onClick={() => setFilter('WEAKENED')}
            >
              WEAKENED (Δ &lt; 0)
            </button>
            <button
              className={`filter-btn ${filter === 'STRENGTHENED' ? 'active emerald' : ''}`}
              onClick={() => setFilter('STRENGTHENED')}
            >
              STRENGTHENED (Δ &gt; 0)
            </button>
          </div>
        </div>
      </div>

      {deltas.length === 0 ? (
        <div className="delta-empty-notice">
          No synaptic differences at this timestep (original and counterfactual networks are currently identical).
        </div>
      ) : (
        <div className="delta-table-wrapper">
          <table className="delta-table">
            <thead>
              <tr>
                <th>SYNAPSE</th>
                <th>PRE (KEY)</th>
                <th>POST (VALUE)</th>
                <th>ORIGINAL</th>
                <th>WHAT IF?</th>
                <th>Δ (DIFFERENCE)</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 30).map((item) => {
                const isSelected = selectedSynapseId === item.synapse_id
                const isNegative = item.delta < 0
                return (
                  <tr
                    key={item.synapse_id}
                    className={`delta-row ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectSynapse(item.synapse_id)}
                  >
                    <td className="syn-id-cell">
                      <span className="syn-dot" style={{ backgroundColor: isNegative ? '#ef4444' : '#10b981' }} />
                      <strong>{item.synapse_id}</strong>
                    </td>
                    <td>{item.source}</td>
                    <td>{item.target}</td>
                    <td className="num-cell">{item.original_weight.toFixed(4)}</td>
                    <td className="num-cell">{item.counterfactual_weight.toFixed(4)}</td>
                    <td className={`num-cell delta-cell ${isNegative ? 'negative' : 'positive'}`}>
                      {item.delta > 0 ? `+${item.delta.toFixed(4)}` : item.delta.toFixed(4)}
                    </td>
                    <td>
                      <button
                        className="inspect-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          onSelectSynapse(item.synapse_id)
                        }}
                      >
                        {isSelected ? 'INSPECTING' : 'SELECT'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {filtered.length > 30 && (
            <div className="delta-table-footer">
              Showing top 30 of {filtered.length} altered connections (sorted by absolute Δ).
            </div>
          )}
        </div>
      )}
    </div>
  )
}
