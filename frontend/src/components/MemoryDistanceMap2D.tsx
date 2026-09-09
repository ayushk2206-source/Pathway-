import React, { useState } from 'react'
import type { MemoryDistanceMap, MemoryDistancePoint } from '../types'

interface MemoryDistanceMap2DProps {
  distanceMap: MemoryDistanceMap | null
  selectedConcept?: string
  onSelectConcept?: (concept: string) => void
}

export const MemoryDistanceMap2D: React.FC<MemoryDistanceMap2DProps> = ({
  distanceMap,
  selectedConcept,
  onSelectConcept,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<MemoryDistancePoint | null>(null)

  if (!distanceMap || distanceMap.points.length === 0) {
    return (
      <div className="forensic-card" style={{ color: '#64748b', fontSize: '0.85rem' }}>
        No distance map points computed.
      </div>
    )
  }

  const width = 500
  const height = 240
  const padding = 35

  const xs = distanceMap.points.map((p) => p.x)
  const ys = distanceMap.points.map((p) => p.y)

  const minX = Math.min(...xs, -0.5)
  const maxX = Math.max(...xs, 0.5)
  const minY = Math.min(...ys, -0.5)
  const maxY = Math.max(...ys, 0.5)

  const rangeX = maxX - minX || 1.0
  const rangeY = maxY - minY || 1.0

  const getSvgX = (x: number) => padding + ((x - minX) / rangeX) * (width - 2 * padding)
  const getSvgY = (y: number) => height - padding - ((y - minY) / rangeY) * (height - 2 * padding)

  return (
    <div className="forensic-card">
      <div className="forensic-card-header">
        <h3 className="forensic-card-title">
          <span>Memory Distance Map (2D PCA SVD Projection)</span>
        </h3>
        {distanceMap.variance_explained !== null && (
          <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontFamily: 'monospace' }}>
            Variance Explained: {(distanceMap.variance_explained * 100).toFixed(1)}%
          </span>
        )}
      </div>

      <div className="distance-map-svg-container">
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '100%' }}>
          {/* Subtle grid lines */}
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="rgba(71, 85, 105, 0.3)" strokeDasharray="3 3" />
          <line x1={width / 2} y1={padding} x2={width / 2} y2={height - padding} stroke="rgba(71, 85, 105, 0.3)" strokeDasharray="3 3" />

          {/* Points */}
          {distanceMap.points.map((pt) => {
            const cx = getSvgX(pt.x)
            const cy = getSvgY(pt.y)
            const isSelected = selectedConcept === pt.concept

            return (
              <circle
                key={pt.memory_id}
                className="distance-point-circle"
                cx={cx}
                cy={cy}
                r={isSelected ? 7 : pt.is_outlier ? 6 : 5}
                fill={pt.is_outlier ? '#ef4444' : isSelected ? '#38bdf8' : '#10b981'}
                stroke="#0f172a"
                strokeWidth={1.5}
                onMouseEnter={() => setHoveredPoint(pt)}
                onMouseLeave={() => setHoveredPoint(null)}
                onClick={() => onSelectConcept?.(pt.concept)}
              />
            )
          })}
        </svg>

        {hoveredPoint && (
          <div style={{
            position: 'absolute',
            bottom: '10px',
            right: '10px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: `1px solid ${hoveredPoint.is_outlier ? '#ef4444' : '#38bdf8'}`,
            borderRadius: '6px',
            padding: '0.5rem 0.75rem',
            fontSize: '0.75rem',
            color: '#f8fafc',
            pointerEvents: 'none',
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
          }}>
            <div><strong>{hoveredPoint.concept}</strong></div>
            <div>Active Units: {hoveredPoint.active_units} | Recall: {(hoveredPoint.recall_fidelity * 100).toFixed(0)}%</div>
            {hoveredPoint.is_outlier && (
              <div style={{ color: '#f87171', marginTop: '3px', fontWeight: 600 }}>
                Representational Outlier: {hoveredPoint.outlier_reasons.join(', ')}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
