import React, { useState } from 'react'

interface UniverseWorldData {
  title: string
  subtitle: string
  fidelity: number
  crosstalk: number
  matrixNorm: number
  activeSynapses: number
  weightsSample: number[]
}

interface SplitUniverseViewProps {
  worldA: UniverseWorldData
  worldB: UniverseWorldData
  onSelectWorld?: (world: 'A' | 'B') => void
}

export const SplitUniverseView: React.FC<SplitUniverseViewProps> = ({
  worldA,
  worldB,
  onSelectWorld,
}) => {
  const [viewMode, setViewMode] = useState<'SPLIT' | 'MERGE_DIFF'>('SPLIT')

  const fidelityDelta = worldB.fidelity - worldA.fidelity
  const crosstalkDelta = worldB.crosstalk - worldA.crosstalk
  const normDelta = worldB.matrixNorm - worldA.matrixNorm

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#f8fafc', letterSpacing: '-0.02em' }}>
            A/B SPLIT UNIVERSE & COUNTERFACTUAL BRANCHING
          </h2>
          <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
            Comparing parallel synaptic configurations under controlled intervention.
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`tag-btn ${viewMode === 'SPLIT' ? 'active' : ''}`}
            onClick={() => setViewMode('SPLIT')}
          >
            SIDE-BY-SIDE WORLDS
          </button>
          <button
            className={`tag-btn ${viewMode === 'MERGE_DIFF' ? 'active' : ''}`}
            onClick={() => setViewMode('MERGE_DIFF')}
          >
            MERGE DIFFERENCE (&Delta;W)
          </button>
        </div>
      </div>

      {viewMode === 'SPLIT' ? (
        <div className="split-universe-container">
          {/* World A */}
          <div
            className="universe-panel world-a"
            onClick={() => onSelectWorld && onSelectWorld('A')}
            style={{ cursor: onSelectWorld ? 'pointer' : 'default' }}
          >
            <div className="universe-header">
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.1em' }}>
                  PARALLEL WORLD A
                </span>
                <h3 style={{ margin: '0.2rem 0', fontSize: '1.1rem', color: '#f8fafc' }}>
                  {worldA.title}
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{worldA.subtitle}</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.5rem' }}>
              <div className="memory-metric-cell">
                <span className="metric-cell-label">RECALL FIDELITY</span>
                <span className="metric-cell-val" style={{ color: '#38bdf8' }}>
                  {(worldA.fidelity * 100).toFixed(1)}%
                </span>
              </div>
              <div className="memory-metric-cell">
                <span className="metric-cell-label">CROSSTALK</span>
                <span className="metric-cell-val">{worldA.crosstalk.toFixed(3)}</span>
              </div>
              <div className="memory-metric-cell">
                <span className="metric-cell-label">||W|| NORM</span>
                <span className="metric-cell-val">{worldA.matrixNorm.toFixed(2)}</span>
              </div>
            </div>

            {/* Weights mini-strip */}
            <div style={{ display: 'flex', gap: '4px', height: '24px', alignItems: 'flex-end', marginTop: '0.5rem' }}>
              {worldA.weightsSample.map((w, idx) => (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    height: `${Math.max(4, Math.abs(w) * 24)}px`,
                    background: w >= 0 ? '#38bdf8' : '#f43f5e',
                    borderRadius: '2px',
                  }}
                />
              ))}
            </div>
          </div>

          {/* World B */}
          <div
            className="universe-panel world-b"
            onClick={() => onSelectWorld && onSelectWorld('B')}
            style={{ cursor: onSelectWorld ? 'pointer' : 'default' }}
          >
            <div className="universe-header">
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c084fc', letterSpacing: '0.1em' }}>
                  PARALLEL WORLD B
                </span>
                <h3 style={{ margin: '0.2rem 0', fontSize: '1.1rem', color: '#f8fafc' }}>
                  {worldB.title}
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{worldB.subtitle}</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.5rem' }}>
              <div className="memory-metric-cell">
                <span className="metric-cell-label">RECALL FIDELITY</span>
                <span className="metric-cell-val" style={{ color: '#c084fc' }}>
                  {(worldB.fidelity * 100).toFixed(1)}%
                </span>
              </div>
              <div className="memory-metric-cell">
                <span className="metric-cell-label">CROSSTALK</span>
                <span className="metric-cell-val">{worldB.crosstalk.toFixed(3)}</span>
              </div>
              <div className="memory-metric-cell">
                <span className="metric-cell-label">||W|| NORM</span>
                <span className="metric-cell-val">{worldB.matrixNorm.toFixed(2)}</span>
              </div>
            </div>

            {/* Weights mini-strip */}
            <div style={{ display: 'flex', gap: '4px', height: '24px', alignItems: 'flex-end', marginTop: '0.5rem' }}>
              {worldB.weightsSample.map((w, idx) => (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    height: `${Math.max(4, Math.abs(w) * 24)}px`,
                    background: w >= 0 ? '#c084fc' : '#f43f5e',
                    borderRadius: '2px',
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ background: 'rgba(10, 20, 38, 0.9)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '14px', padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', color: '#f8fafc' }}>
            SYNAPTIC DIFFERENCE ANALYSIS: WORLD B &minus; WORLD A
          </h3>
          <p style={{ margin: '0 0 1rem 0', color: '#94a3b8', fontSize: '0.85rem' }}>
            Quantifying the exact divergence resulting from the counterfactual parameter modification.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="memory-metric-cell" style={{ padding: '0.75rem' }}>
              <span className="metric-cell-label">&Delta; RECALL FIDELITY</span>
              <span
                style={{
                  fontSize: '1.3rem',
                  fontWeight: 800,
                  color: fidelityDelta >= 0 ? '#34d399' : '#f87171',
                }}
              >
                {fidelityDelta >= 0 ? '+' : ''}{(fidelityDelta * 100).toFixed(1)}%
              </span>
            </div>

            <div className="memory-metric-cell" style={{ padding: '0.75rem' }}>
              <span className="metric-cell-label">&Delta; CROSSTALK RESIDUAL</span>
              <span
                style={{
                  fontSize: '1.3rem',
                  fontWeight: 800,
                  color: crosstalkDelta <= 0 ? '#34d399' : '#f87171',
                }}
              >
                {crosstalkDelta >= 0 ? '+' : ''}{crosstalkDelta.toFixed(3)}
              </span>
            </div>

            <div className="memory-metric-cell" style={{ padding: '0.75rem' }}>
              <span className="metric-cell-label">&Delta; MATRIX NORM</span>
              <span style={{ fontSize: '1.3rem', fontWeight: 800, color: '#e2e8f0' }}>
                {normDelta >= 0 ? '+' : ''}{normDelta.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SplitUniverseView
