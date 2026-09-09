import React from 'react'
import type { RecallMatrixRow, ThreeConditionResult } from './types'

interface CollisionRecallMatrixProps {
  threeConditionResult: ThreeConditionResult | null
  activeConditionName: string
  onSelectCondition: (conditionName: string) => void
  onRunThreeConditions: () => void
  loading: boolean
}

export const CollisionRecallMatrix: React.FC<CollisionRecallMatrixProps> = ({
  threeConditionResult,
  activeConditionName,
  onSelectCondition,
  onRunThreeConditions,
  loading,
}) => {
  if (!threeConditionResult) {
    return (
      <div style={{ textAlign: 'center', padding: '30px 10px' }}>
        <p style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '14px' }}>
          Evaluate Low, Moderate, and High overlap conditions simultaneously to analyze the interference gradient.
        </p>
        <button
          className="collision-btn collision-btn-warning"
          onClick={onRunThreeConditions}
          disabled={loading}
        >
          {loading ? 'Evaluating Suite...' : '⚡ Generate 3-Condition Recall Matrix'}
        </button>
      </div>
    )
  }

  const rows = threeConditionResult.recall_matrix || []

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '11px', color: '#94a3b8' }}>
          Real linear readouts comparing memory fidelity under graded synaptic overlap
        </span>
        <button
          className="collision-btn collision-btn-outline"
          style={{ padding: '4px 10px', fontSize: '11px' }}
          onClick={onRunThreeConditions}
          disabled={loading}
        >
          {loading ? 'Re-evaluating...' : '↻ Re-run Suite'}
        </button>
      </div>

      <table className="recall-table">
        <thead>
          <tr>
            <th>Condition</th>
            <th>Rep. Overlap (cos)</th>
            <th>Syn. Overlap (Jaccard)</th>
            <th>Recall A Fidelity</th>
            <th>Recall B Fidelity</th>
            <th>Interference</th>
            <th>Shared Synapses</th>
            <th>Dominance</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row: RecallMatrixRow) => {
            const isActive = activeConditionName.toUpperCase() === row.condition.toUpperCase()
            let badgeClass = 'badge-mod'
            if (row.condition.includes('LOW')) badgeClass = 'badge-low'
            else if (row.condition.includes('HIGH')) badgeClass = 'badge-high'

            return (
              <tr
                key={row.condition}
                className={isActive ? 'active-condition' : ''}
                onClick={() => onSelectCondition(row.condition)}
                style={{ cursor: 'pointer' }}
              >
                <td>
                  <span className={badgeClass}>{row.condition}</span>
                </td>
                <td style={{ fontFamily: 'monospace' }}>{row.representational_overlap.toFixed(3)}</td>
                <td style={{ fontFamily: 'monospace' }}>{(row.synaptic_overlap_fraction * 100).toFixed(1)}%</td>
                <td style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 600 }}>
                  {row.recall_a.toFixed(3)}
                </td>
                <td style={{ fontFamily: 'monospace', color: '#c084fc', fontWeight: 600 }}>
                  {row.recall_b.toFixed(3)}
                </td>
                <td style={{ fontFamily: 'monospace', color: row.interference > 0.3 ? '#ef4444' : '#fbbf24' }}>
                  {row.interference.toFixed(3)}
                </td>
                <td style={{ textAlign: 'center', fontWeight: 600 }}>{row.shared_synapses}</td>
                <td style={{ fontSize: '11px', color: '#94a3b8' }}>{row.dominant}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
