import React, { useState } from 'react'
import type { MemoryCheckpoint } from '../types'

interface StateComparatorViewProps {
  checkpoints: MemoryCheckpoint[]
  onCompare: (stateA: Record<string, unknown>, stateB: Record<string, unknown>) => Promise<{
    frobenius_drift: number
    active_ratio_shift: number
    shared_stability: number
    scientific_interpretation: string
  }>
}

export const StateComparatorView: React.FC<StateComparatorViewProps> = ({
  checkpoints,
  onCompare,
}) => {
  const [idxA, setIdxA] = useState<number>(0)
  const [idxB, setIdxB] = useState<number>(Math.min(1, checkpoints.length - 1))
  const [diffResult, setDiffResult] = useState<{
    frobenius_drift: number
    active_ratio_shift: number
    shared_stability: number
    scientific_interpretation: string
  } | null>(null)
  const [isComparing, setIsComparing] = useState<boolean>(false)

  const handleRunComparison = async () => {
    if (checkpoints.length < 2) return
    setIsComparing(true)
    try {
      const res = await onCompare(
        checkpoints[idxA].weights_summary as unknown as Record<string, unknown>,
        checkpoints[idxB].weights_summary as unknown as Record<string, unknown>
      )
      setDiffResult(res)
    } finally {
      setIsComparing(false)
    }
  }

  if (checkpoints.length < 2) {
    return (
      <div className="ledger-card" style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
        Create at least 2 checkpoints to compare model states.
      </div>
    )
  }

  return (
    <div className="ledger-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
          <span>⚖</span> STATE COMPARATOR — WHAT CHANGED?
        </h4>
        <button
          onClick={handleRunComparison}
          disabled={isComparing}
          style={{
            padding: '5px 12px',
            background: 'rgba(56, 189, 248, 0.2)',
            border: '1px solid #38bdf8',
            color: '#38bdf8',
            borderRadius: '4px',
            fontWeight: 700,
            fontSize: '0.75rem',
            cursor: 'pointer',
          }}
        >
          {isComparing ? 'Comparing...' : 'Compare Selected States'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <div>
          <label style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
            State A (Baseline):
          </label>
          <select
            value={idxA}
            onChange={(e) => setIdxA(parseInt(e.target.value, 10))}
            style={{
              width: '100%',
              padding: '6px',
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f8fafc',
              borderRadius: '4px',
              fontSize: '0.8rem',
              marginTop: '4px',
            }}
          >
            {checkpoints.map((cp, idx) => (
              <option key={cp.checkpoint_id} value={idx}>
                {cp.label} ({cp.created_at})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
            State B (Comparison):
          </label>
          <select
            value={idxB}
            onChange={(e) => setIdxB(parseInt(e.target.value, 10))}
            style={{
              width: '100%',
              padding: '6px',
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#38bdf8',
              borderRadius: '4px',
              fontSize: '0.8rem',
              marginTop: '4px',
            }}
          >
            {checkpoints.map((cp, idx) => (
              <option key={cp.checkpoint_id} value={idx}>
                {cp.label} ({cp.created_at})
              </option>
            ))}
          </select>
        </div>
      </div>

      {diffResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(30, 41, 59, 0.5)', padding: '0.8rem', borderRadius: '6px', marginTop: '0.25rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            <div>
              <span style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase' }}>Frobenius Drift</span>
              <div style={{ fontFamily: 'monospace', fontWeight: 700, color: '#f59e0b', fontSize: '0.95rem' }}>
                {diffResult.frobenius_drift.toFixed(4)}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase' }}>Active Ratio Shift</span>
              <div style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8', fontSize: '0.95rem' }}>
                {diffResult.active_ratio_shift.toFixed(4)}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase' }}>Shared Stability</span>
              <div style={{ fontFamily: 'monospace', fontWeight: 700, color: '#10b981', fontSize: '0.95rem' }}>
                {(diffResult.shared_stability * 100).toFixed(1)}%
              </div>
            </div>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#cbd5e1', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '0.4rem' }}>
            <span className="claim-tag inferred" style={{ marginRight: '0.5rem' }}>INFERRED</span>
            {diffResult.scientific_interpretation}
          </div>
        </div>
      )}
    </div>
  )
}
