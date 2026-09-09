import React, { useState } from 'react'
import type { SynapticFingerprint } from '../types'

interface SynapticFingerprintHeroProps {
  fingerprint: SynapticFingerprint | null
  onSelectSynapse?: (row: number, col: number, delta: number) => void
  isScanning?: boolean
}

export const SynapticFingerprintHero: React.FC<SynapticFingerprintHeroProps> = ({
  fingerprint,
  onSelectSynapse,
  isScanning = false,
}) => {
  const [hoveredSynapse, setHoveredSynapse] = useState<{
    row: number
    col: number
    delta: number
  } | null>(null)

  if (!fingerprint) {
    return (
      <div className="forensic-card" style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
        Select or compute a memory fingerprint to initialize forensic scan.
      </div>
    )
  }

  const dim = fingerprint.dimension || 16
  const modMap = new Map<string, number>()
  for (const [r, c, delta] of fingerprint.modified_synapses) {
    modMap.set(`${r},${c}`, delta)
  }

  const maxDelta = fingerprint.synaptic_strength_stats.max || 1.0
  const minDelta = fingerprint.synaptic_strength_stats.min || -1.0
  const range = Math.max(Math.abs(maxDelta), Math.abs(minDelta), 0.01)

  // Build grid pixels
  const pixels: React.ReactNode[] = []
  for (let r = 0; r < dim; r++) {
    for (let c = 0; c < dim; c++) {
      const key = `${r},${c}`
      const delta = modMap.get(key) || 0.0
      const absVal = Math.abs(delta)
      const intensity = Math.min(1.0, absVal / range)

      let bgColor = 'rgba(15, 23, 42, 0.9)'
      let borderColor = 'rgba(51, 65, 85, 0.4)'

      if (absVal > 0.001) {
        if (delta > 0) {
          // Potentiated (Emerald / Cyan)
          bgColor = `rgba(16, 185, 129, ${0.2 + intensity * 0.75})`
          borderColor = `rgba(56, 189, 248, ${0.4 + intensity * 0.6})`
        } else {
          // Depressed (Amber / Red)
          bgColor = `rgba(245, 158, 11, ${0.2 + intensity * 0.75})`
          borderColor = `rgba(239, 68, 68, ${0.4 + intensity * 0.6})`
        }
      }

      pixels.push(
        <div
          key={key}
          className="density-pixel"
          style={{
            background: bgColor,
            border: `1px solid ${borderColor}`,
          }}
          onMouseEnter={() => setHoveredSynapse({ row: r, col: c, delta })}
          onMouseLeave={() => setHoveredSynapse(null)}
          onClick={() => onSelectSynapse?.(r, c, delta)}
          title={`Synapse (${r}, ${c}): ΔW = ${delta.toFixed(4)}`}
        />,
      )
    }
  }

  return (
    <div className="forensic-card">
      <div className="forensic-card-header">
        <h3 className="forensic-card-title">
          <span>Synaptic Fingerprint: {fingerprint.concept}</span>
        </h3>

        <div className="dna-scan-indicator">
          <span className="scan-pulse" />
          <span>{isScanning ? 'SCANNING SUBSTRATE...' : 'FINGERPRINT VERIFIED'}</span>
        </div>
      </div>

      {/* 4 Stat Boxes */}
      <div className="fingerprint-metrics-row">
        <div className="fingerprint-stat-box">
          <div className="stat-label">Active Units</div>
          <div className="stat-number cyan">{fingerprint.active_unit_count}</div>
        </div>
        <div className="fingerprint-stat-box">
          <div className="stat-label">Modified Synapses</div>
          <div className="stat-number emerald">{fingerprint.modified_synapse_count}</div>
        </div>
        <div className="fingerprint-stat-box">
          <div className="stat-label">Unit Sparsity</div>
          <div className="stat-number purple">
            {(fingerprint.sparsity * 100).toFixed(0)}%
          </div>
        </div>
        <div className="fingerprint-stat-box">
          <div className="stat-label">Recall Fidelity</div>
          <div className="stat-number amber">
            {(fingerprint.recall_performance.fidelity * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Matrix Density Strip */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8' }}>
          <span>Synaptic Outer-Product Allocations (16 × 16)</span>
          {hoveredSynapse && (
            <span style={{ color: '#38bdf8', fontFamily: 'Courier New, monospace' }}>
              Synapse ({hoveredSynapse.row}, {hoveredSynapse.col}): ΔW = {hoveredSynapse.delta.toFixed(4)} (Click to operate)
            </span>
          )}
        </div>

        <div className="density-strip-matrix">{pixels}</div>
      </div>

      {/* Synaptic Strength Distribution Summary */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '0.5rem',
        background: 'rgba(30, 41, 59, 0.4)',
        padding: '0.6rem 0.8rem',
        borderRadius: '8px',
        fontSize: '0.75rem',
        color: '#cbd5e1',
        fontFamily: 'Courier New, monospace',
      }}>
        <div>Mean ΔW: <strong style={{ color: '#f8fafc' }}>{fingerprint.synaptic_strength_stats.mean.toFixed(4)}</strong></div>
        <div>Std Dev: <strong style={{ color: '#f8fafc' }}>{fingerprint.synaptic_strength_stats.std.toFixed(4)}</strong></div>
        <div>Frobenius ||ΔW||: <strong style={{ color: '#38bdf8' }}>{fingerprint.synaptic_strength_stats.frobenius_contribution.toFixed(4)}</strong></div>
        <div>Crosstalk Noise: <strong style={{ color: '#fbbf24' }}>{fingerprint.recall_performance.crosstalk_noise.toFixed(4)}</strong></div>
      </div>
    </div>
  )
}
