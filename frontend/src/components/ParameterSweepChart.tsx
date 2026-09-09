import React from 'react'
import type { StudioSweepResult } from '../types'

interface ParameterSweepChartProps {
  sweep: StudioSweepResult
}

export const ParameterSweepChart: React.FC<ParameterSweepChartProps> = ({ sweep }) => {
  const { points, param_name, correlation, trend_interpretation } = sweep

  if (points.length === 0) return null

  // SVG dimensions
  const width = 560
  const height = 240
  const padLeft = 50
  const padRight = 30
  const padTop = 30
  const padBottom = 40

  const xMin = points[0].param_value
  const xMax = points[points.length - 1].param_value
  const xSpan = xMax - xMin || 1.0

  const yMin = 0.0
  const yMax = 1.0

  const getX = (val: number) => padLeft + ((val - xMin) / xSpan) * (width - padLeft - padRight)
  const getY = (val: number) => height - padBottom - ((val - yMin) / (yMax - yMin)) * (height - padTop - padBottom)

  const linePath = points
    .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${getX(p.param_value)} ${getY(p.fidelity)}`)
    .join(' ')

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.75)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '8px',
      padding: '1.25rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 800, color: '#f8fafc' }}>
            PARAMETER SWEEP: {param_name.toUpperCase()} VS RECALL FIDELITY
          </h4>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '2px' }}>
            Empirical non-linear response curve across {points.length} measured points
          </div>
        </div>
        <div style={{
          fontSize: '0.72rem',
          fontWeight: 700,
          padding: '3px 8px',
          borderRadius: '4px',
          background: 'rgba(56, 189, 248, 0.15)',
          color: '#38bdf8',
          border: '1px solid rgba(56, 189, 248, 0.3)',
        }}>
          Pearson r = {correlation.toFixed(2)}
        </div>
      </div>

      {/* SVG Chart */}
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} style={{ background: '#090d16', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.04)' }}>
          {/* Horizontal grid lines */}
          {[0.0, 0.25, 0.5, 0.75, 1.0].map((yVal) => (
            <g key={yVal}>
              <line
                x1={padLeft}
                y1={getY(yVal)}
                x2={width - padRight}
                y2={getY(yVal)}
                stroke="rgba(255, 255, 255, 0.07)"
                strokeDasharray="3 3"
              />
              <text x={padLeft - 8} y={getY(yVal) + 4} fill="#64748b" fontSize="9" textAnchor="end">
                {yVal.toFixed(2)}
              </text>
            </g>
          ))}

          {/* Connective Line */}
          <path d={linePath} fill="none" stroke="#38bdf8" strokeWidth="2.5" />

          {/* Data Points */}
          {points.map((p) => {
            const cx = getX(p.param_value)
            const cy = getY(p.fidelity)
            return (
              <g key={p.param_value}>
                <circle cx={cx} cy={cy} r="5" fill="#38bdf8" stroke="#090d16" strokeWidth="2" />
                <text x={cx} y={height - padBottom + 16} fill="#94a3b8" fontSize="9" textAnchor="middle">
                  {p.param_value.toFixed(2)}
                </text>
              </g>
            )
          })}

          {/* Axis Labels */}
          <text x={width / 2} y={height - 6} fill="#94a3b8" fontSize="10" textAnchor="middle" fontWeight="700">
            {param_name}
          </text>
          <text x={12} y={height / 2} fill="#94a3b8" fontSize="10" textAnchor="middle" transform={`rotate(-90 12 ${height / 2})`} fontWeight="700">
            Fidelity
          </text>
        </svg>
      </div>

      <div style={{
        fontSize: '0.74rem',
        color: '#cbd5e1',
        background: 'rgba(30, 41, 59, 0.5)',
        padding: '0.6rem 0.8rem',
        borderRadius: '6px',
        borderLeft: '3px solid #38bdf8',
      }}>
        <strong>Observation:</strong> {trend_interpretation}
      </div>
    </div>
  )
}
