import React, { useState } from 'react'
import type { ObservatorySnapshot } from '../types'

interface AdaptationGraphProps {
  snapshots: ObservatorySnapshot[]
  currentStep: number
  onSelectStep?: (step: number) => void
}

export const AdaptationGraph: React.FC<AdaptationGraphProps> = ({
  snapshots,
  currentStep,
  onSelectStep,
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'norm' | 'fidelity' | 'active'>('fidelity')

  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="chart-svg-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No telemetry data yet. Run stream to observe graph.</span>
      </div>
    )
  }

  const width = 640
  const height = 180
  const padding = { top: 20, right: 30, bottom: 30, left: 45 }

  // Extract points based on selected metric
  const points = snapshots.map((s) => {
    let val = 0
    if (selectedMetric === 'norm') {
      val = s.matrix_norm
    } else if (selectedMetric === 'active') {
      val = s.active_synapse_count
    } else {
      // average probe fidelity
      val = s.probes && s.probes.length > 0
        ? s.probes.reduce((sum, p) => sum + p.fidelity, 0) / s.probes.length
        : 0
    }
    return { step: s.step, value: val }
  })

  const minVal = Math.min(...points.map((p) => p.value), 0)
  const maxVal = Math.max(...points.map((p) => p.value), selectedMetric === 'fidelity' ? 1.0 : 1.0)
  const valRange = maxVal - minVal || 1

  const maxStep = snapshots.length > 1 ? snapshots.length - 1 : 1

  const getX = (step: number) =>
    padding.left + ((step) / maxStep) * (width - padding.left - padding.right)

  const getY = (val: number) =>
    height - padding.bottom - ((val - minVal) / valRange) * (height - padding.top - padding.bottom)

  // Construct SVG path
  const pathD = points
    .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${getX(pt.step).toFixed(1)} ${getY(pt.value).toFixed(1)}`)
    .join(' ')

  const currentX = getX(currentStep)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
          Real Telemetry Series across <strong style={{ color: '#f8fafc' }}>{snapshots.length} Timesteps</strong>
        </div>

        <div style={{ display: 'flex', gap: '0.35rem' }}>
          <button
            className={`preset-chip ${selectedMetric === 'fidelity' ? 'active' : ''}`}
            onClick={() => setSelectedMetric('fidelity')}
          >
            Probe Fidelity
          </button>
          <button
            className={`preset-chip ${selectedMetric === 'norm' ? 'active' : ''}`}
            onClick={() => setSelectedMetric('norm')}
          >
            Frobenius Norm
          </button>
          <button
            className={`preset-chip ${selectedMetric === 'active' ? 'active' : ''}`}
            onClick={() => setSelectedMetric('active')}
          >
            Active Synapses
          </button>
        </div>
      </div>

      <div className="chart-svg-container">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: '100%' }}
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={width - padding.right}
            y2={padding.top}
            stroke="rgba(71, 85, 105, 0.3)"
            strokeDasharray="4 4"
          />
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="rgba(71, 85, 105, 0.4)"
          />

          {/* Current step line */}
          <line
            x1={currentX}
            y1={padding.top}
            x2={currentX}
            y2={height - padding.bottom}
            stroke="#818cf8"
            strokeWidth="2"
            strokeDasharray="2 2"
          />

          {/* Telemetry Path */}
          <path
            d={pathD}
            fill="none"
            stroke={selectedMetric === 'fidelity' ? '#10b981' : selectedMetric === 'norm' ? '#38bdf8' : '#ec4899'}
            strokeWidth="2.5"
          />

          {/* Point markers */}
          {points.map((pt) => {
            const cx = getX(pt.step)
            const cy = getY(pt.value)
            const isSelected = pt.step === currentStep

            return (
              <circle
                key={pt.step}
                cx={cx}
                cy={cy}
                r={isSelected ? 5 : 3}
                fill={isSelected ? '#ffffff' : selectedMetric === 'fidelity' ? '#10b981' : '#38bdf8'}
                stroke="#0f172a"
                strokeWidth="1.5"
                style={{ cursor: 'pointer' }}
                onClick={() => onSelectStep?.(pt.step)}
              >
                <title>T{pt.step}: {pt.value.toFixed(4)}</title>
              </circle>
            )
          })}

          {/* Axes labels */}
          <text
            x={padding.left - 8}
            y={getY(maxVal) + 4}
            fill="#94a3b8"
            fontSize="10"
            textAnchor="end"
            fontFamily="monospace"
          >
            {selectedMetric === 'fidelity' ? `${(maxVal * 100).toFixed(0)}%` : maxVal.toFixed(2)}
          </text>
          <text
            x={padding.left - 8}
            y={getY(minVal)}
            fill="#94a3b8"
            fontSize="10"
            textAnchor="end"
            fontFamily="monospace"
          >
            {selectedMetric === 'fidelity' ? `${(minVal * 100).toFixed(0)}%` : minVal.toFixed(2)}
          </text>

          <text
            x={padding.left}
            y={height - 8}
            fill="#94a3b8"
            fontSize="10"
            fontFamily="monospace"
          >
            T0
          </text>
          <text
            x={width - padding.right}
            y={height - 8}
            fill="#94a3b8"
            fontSize="10"
            textAnchor="end"
            fontFamily="monospace"
          >
            T{maxStep}
          </text>
        </svg>
      </div>
    </div>
  )
}
