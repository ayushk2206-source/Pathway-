import React, { useState } from 'react'
import type { FingerprintEvolution } from '../types'

interface GenomeEvolutionViewProps {
  evolution: FingerprintEvolution | null
}

export const GenomeEvolutionView: React.FC<GenomeEvolutionViewProps> = ({ evolution }) => {
  const [activeStepIdx, setActiveStepIdx] = useState<number>(0)

  if (!evolution || evolution.timesteps.length === 0) {
    return (
      <div className="forensic-card" style={{ color: '#64748b', fontSize: '0.85rem' }}>
        No temporal evolution recorded for this concept yet.
      </div>
    )
  }

  const currentFp = evolution.fingerprints[activeStepIdx] || evolution.fingerprints[0]

  return (
    <div className="forensic-card">
      <div className="forensic-card-header">
        <h3 className="forensic-card-title">
          <span>Genome Evolution Across Time (Phase 19 Stream)</span>
        </h3>
        <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
          Concept: <strong style={{ color: '#38bdf8' }}>{evolution.concept}</strong>
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
          Timesteps:
        </span>
        {evolution.timesteps.map((t, idx) => (
          <button
            key={t}
            className={`concept-chip ${activeStepIdx === idx ? 'active' : ''}`}
            onClick={() => setActiveStepIdx(idx)}
          >
            T{t}
          </button>
        ))}
      </div>

      {currentFp && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '0.5rem',
          background: 'rgba(30, 41, 59, 0.4)',
          padding: '0.75rem',
          borderRadius: '8px',
          fontSize: '0.8rem',
        }}>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>ACTIVE UNITS</div>
            <div style={{ color: '#38bdf8', fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace' }}>
              {currentFp.active_unit_count}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>MODIFIED SYNAPSES</div>
            <div style={{ color: '#34d399', fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace' }}>
              {currentFp.modified_synapse_count}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>FROBENIUS ||ΔW||</div>
            <div style={{ color: '#c084fc', fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace' }}>
              {currentFp.synaptic_strength_stats.frobenius_contribution.toFixed(3)}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>RECALL FIDELITY</div>
            <div style={{ color: '#fbbf24', fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace' }}>
              {(currentFp.recall_performance.fidelity * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
