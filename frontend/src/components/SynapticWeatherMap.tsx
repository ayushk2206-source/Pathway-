import React, { useState } from 'react'
import type { SynapticWeatherPoint } from '../types'

interface SynapticWeatherMapProps {
  weatherMap: SynapticWeatherPoint[]
  dimension: number
  onSelectSynapse?: (row: number, col: number, weight: number) => void
}

export const SynapticWeatherMap: React.FC<SynapticWeatherMapProps> = ({
  weatherMap,
  dimension,
  onSelectSynapse,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<SynapticWeatherPoint | null>(null)

  // Quick lookup dictionary for points
  const pointsMap = new Map<string, SynapticWeatherPoint>()
  for (const pt of weatherMap) {
    pointsMap.set(`${pt.row},${pt.col}`, pt)
  }

  // Count by category
  const counts = {
    UNCHANGED: 0,
    RECENTLY_STRENGTHENED: 0,
    RECENTLY_WEAKENED: 0,
    CURRENTLY_ACTIVE: 0,
    INACTIVE_ZERO: 0,
  }
  for (const pt of weatherMap) {
    if (counts[pt.category] !== undefined) {
      counts[pt.category]++
    }
  }

  const cells: React.ReactNode[] = []
  for (let r = 0; r < dimension; r++) {
    for (let c = 0; c < dimension; c++) {
      const key = `${r},${c}`
      const pt = pointsMap.get(key) || {
        row: r,
        col: c,
        weight: 0,
        prev_weight: 0,
        delta: 0,
        transmission_energy: 0,
        category: 'INACTIVE_ZERO' as const,
      }

      cells.push(
        <div
          key={key}
          className={`weather-cell cell-${pt.category}`}
          onMouseEnter={() => setHoveredPoint(pt)}
          onMouseLeave={() => setHoveredPoint(null)}
          onClick={() => onSelectSynapse?.(r, c, pt.weight)}
          title={`W[${r},${c}] = ${pt.weight.toFixed(4)}`}
        />,
      )
    }
  }

  return (
    <div className="weather-map-container">
      <div
        className="weather-matrix-grid"
        style={{
          gridTemplateColumns: `repeat(${dimension}, 18px)`,
          position: 'relative',
        }}
      >
        {cells}

        {hoveredPoint && (
          <div className="weather-tooltip">
            <div>
              <strong>Synapse ({hoveredPoint.row}, {hoveredPoint.col})</strong>
            </div>
            <div>Category: <span>{hoveredPoint.category.replace('_', ' ')}</span></div>
            <div>Weight: <span>{hoveredPoint.weight.toFixed(4)}</span> (prev: {hoveredPoint.prev_weight.toFixed(4)})</div>
            <div>Delta: <span style={{ color: hoveredPoint.delta > 0 ? '#34d399' : hoveredPoint.delta < 0 ? '#fbbf24' : '#94a3b8' }}>
              {hoveredPoint.delta > 0 ? `+${hoveredPoint.delta.toFixed(4)}` : hoveredPoint.delta.toFixed(4)}
            </span></div>
            <div>Transmission Energy: <span>{hoveredPoint.transmission_energy.toFixed(4)}</span></div>
            <div style={{ fontSize: '0.65rem', color: '#818cf8', marginTop: '2px' }}>
              Click to perform Synaptic Surgery
            </div>
          </div>
        )}
      </div>

      <div className="weather-legend">
        <div className="legend-item">
          <span className="legend-swatch swatch-unchanged" />
          <span>Unchanged ({counts.UNCHANGED})</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch swatch-strengthened" />
          <span>Strengthened ({counts.RECENTLY_STRENGTHENED})</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch swatch-weakened" />
          <span>Weakened ({counts.RECENTLY_WEAKENED})</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch swatch-active" />
          <span>Active ({counts.CURRENTLY_ACTIVE})</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch swatch-inactive" />
          <span>Zero/Inactive ({counts.INACTIVE_ZERO})</span>
        </div>
      </div>
    </div>
  )
}
