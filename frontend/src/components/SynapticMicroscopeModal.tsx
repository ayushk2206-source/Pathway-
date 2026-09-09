import React, { useState } from 'react'
import type { MemoryObjectData } from './LivingMemoryObject'

interface SynapticMicroscopeModalProps {
  memory: MemoryObjectData | null
  onClose: () => void
  onAblateSynapse?: (synapseIndex: number) => void
}

export const SynapticMicroscopeModal: React.FC<SynapticMicroscopeModalProps> = ({
  memory,
  onClose,
  onAblateSynapse,
}) => {
  const [zoomLevel, setZoomLevel] = useState<'MACRO' | 'SYNAPSE_GRID' | 'ATOMIC_CAUSAL'>('SYNAPSE_GRID')
  const [selectedWeightIdx, setSelectedWeightIdx] = useState<number | null>(null)

  if (!memory) return null

  // Generate synthetic slice of weights corresponding to the memory dimension
  const dim = 16
  const weights = memory.activationWave.length >= dim
    ? memory.activationWave.slice(0, dim)
    : [...memory.activationWave, ...Array(dim - memory.activationWave.length).fill(0.1)]

  return (
    <div className="microscope-modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="microscope-modal-frame" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="microscope-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.2rem', color: '#38bdf8' }}>⌬</span>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem', color: '#f8fafc', letterSpacing: '-0.02em' }}>
                SYNAPTIC MICROSCOPE: {memory.concept.toUpperCase()}
              </h2>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                ID: {memory.memoryId} &bull; Target: {memory.value}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* Zoom level toggles */}
            <button
              className={`tag-btn ${zoomLevel === 'MACRO' ? 'active' : ''}`}
              onClick={() => setZoomLevel('MACRO')}
            >
              1X MACRO
            </button>
            <button
              className={`tag-btn ${zoomLevel === 'SYNAPSE_GRID' ? 'active' : ''}`}
              onClick={() => setZoomLevel('SYNAPSE_GRID')}
            >
              10X SYNAPSE SLICE
            </button>
            <button
              className={`tag-btn ${zoomLevel === 'ATOMIC_CAUSAL' ? 'active' : ''}`}
              onClick={() => setZoomLevel('ATOMIC_CAUSAL')}
            >
              100X ATOMIC CAUSAL
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                fontSize: '1.3rem',
                cursor: 'pointer',
                marginLeft: '0.5rem',
              }}
              aria-label="Close microscope"
            >
              &times;
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="microscope-body">
          {zoomLevel === 'MACRO' && (
            <div className="microscope-reticle">
              <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.5rem' }}>
                MACROSCOPIC RETRIEVAL PROFILE
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#38bdf8' }}>
                {(memory.recallFidelity * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                Cosine Recall Fidelity &bull; Crosstalk Residual: {memory.crosstalkResidual.toFixed(3)}
              </div>
            </div>
          )}

          {zoomLevel === 'SYNAPSE_GRID' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>
                  SYNAPTIC CONNECTION WEIGHT SLICE ($W_{'{i, :}'}$)
                </span>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                  Click synapse cell to inspect atomic causal contribution
                </span>
              </div>

              {/* 4x4 Grid of connection intensities */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.65rem' }}>
                {weights.map((w, idx) => {
                  const isSelected = selectedWeightIdx === idx
                  const absVal = Math.abs(w)
                  const bg = absVal > 0.6
                    ? 'rgba(56, 189, 248, 0.35)'
                    : absVal > 0.3
                    ? 'rgba(16, 185, 129, 0.25)'
                    : 'rgba(148, 163, 184, 0.1)'

                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedWeightIdx(idx)}
                      style={{
                        background: bg,
                        border: isSelected ? '2px solid #38bdf8' : '1px solid rgba(56, 189, 248, 0.25)',
                        borderRadius: '8px',
                        padding: '0.75rem',
                        cursor: 'pointer',
                        textAlign: 'center',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ fontSize: '0.68rem', color: '#64748b', fontFamily: 'var(--font-data)' }}>
                        SYN_{idx}
                      </div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', marginTop: '0.15rem' }}>
                        {w.toFixed(3)}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {zoomLevel === 'ATOMIC_CAUSAL' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ background: 'rgba(239, 68, 68, 0.08)', borderLeft: '3px solid #ef4444', padding: '0.75rem 1rem', borderRadius: '0 8px 8px 0' }}>
                <strong style={{ color: '#f87171', display: 'block', fontSize: '0.85rem' }}>
                  CAUSAL INTERVENTION LABORATORY
                </strong>
                <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                  Targeting individual synaptic connections to measure causal impact on associative reconstruction.
                </span>
              </div>

              {selectedWeightIdx !== null ? (
                <div style={{ background: 'rgba(15, 28, 53, 0.6)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    Active Synapse: SYN_{selectedWeightIdx}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                    Current Efficacy Weight: {weights[selectedWeightIdx]?.toFixed(4)}
                  </div>

                  <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem' }}>
                    <button
                      className="tag-btn active"
                      style={{ background: '#ef4444', borderColor: '#f87171', color: '#ffffff' }}
                      onClick={() => onAblateSynapse && onAblateSynapse(selectedWeightIdx)}
                    >
                      CLAMP TO ZERO (SURGICAL ABLATION)
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                  Select a synapse cell in 10X view to inspect and ablate it here.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SynapticMicroscopeModal
