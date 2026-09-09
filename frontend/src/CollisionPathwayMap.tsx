import React from 'react'
import type { CollisionResult, SynapticPathwayClassification } from './types'

interface CollisionPathwayMapProps {
  result: CollisionResult | null
  selectedSynapse: SynapticPathwayClassification | null
  onSelectSynapse: (syn: SynapticPathwayClassification) => void
  currentWeights?: number[][] | null
}

export const CollisionPathwayMap: React.FC<CollisionPathwayMapProps> = ({
  result,
  selectedSynapse,
  onSelectSynapse,
  currentWeights,
}) => {
  if (!result) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        No collision simulation run yet. Click "Run Collision" to generate the synaptic pathway map.
      </div>
    )
  }

  const dimension = result.config.dimension || 16
  const collisionMap = result.collision_map || []

  // Create a 2D lookup map for quick access
  const cellMap = new Map<string, SynapticPathwayClassification>()
  collisionMap.forEach((item) => {
    cellMap.set(`${item.target_idx}_${item.source_idx}`, item)
  })

  return (
    <div className="matrix-container">
      <div
        className="matrix-grid"
        style={{
          gridTemplateColumns: `repeat(${dimension}, 22px)`,
          gridTemplateRows: `repeat(${dimension}, 22px)`,
        }}
      >
        {Array.from({ length: dimension }).map((_, targetIdx) =>
          Array.from({ length: dimension }).map((_, sourceIdx) => {
            const item = cellMap.get(`${targetIdx}_${sourceIdx}`)
            const isSelected = selectedSynapse?.synapse_id === item?.synapse_id
            const classification = item?.classification || 'UNCHANGED'

            let cellClass = 'cell-unchanged'
            if (classification === 'SHARED') cellClass = 'cell-shared'
            else if (classification === 'A_ONLY') cellClass = 'cell-a-only'
            else if (classification === 'B_ONLY') cellClass = 'cell-b-only'

            // Check if we are viewing a specific historical timestep weights
            const activeWeight = currentWeights
              ? currentWeights[targetIdx]?.[sourceIdx] ?? item?.final_weight ?? 0
              : item?.final_weight ?? 0

            return (
              <div
                key={`${targetIdx}_${sourceIdx}`}
                className={`synapse-cell ${cellClass} ${isSelected ? 'selected' : ''}`}
                onClick={() => item && onSelectSynapse(item)}
                title={`${item?.synapse_id || `syn_k${sourceIdx}_v${targetIdx}`}: ${classification} (W=${activeWeight.toFixed(3)})`}
              >
                {classification === 'SHARED' ? '★' : ''}
              </div>
            )
          })
        )}
      </div>

      <div className="pathway-legend">
        <div className="legend-item">
          <span className="color-dot-a"></span>
          <span>A-Only Pathway ({result.a_only_synapses?.length || 0})</span>
        </div>
        <div className="legend-item">
          <span className="color-dot-b"></span>
          <span>B-Only Pathway ({result.b_only_synapses?.length || 0})</span>
        </div>
        <div className="legend-item">
          <span className="color-dot-shared"></span>
          <span>Shared Colliding Synapses ({result.shared_synapses?.length || 0})</span>
        </div>
        <div className="legend-item">
          <span style={{ width: 8, height: 8, background: '#1e293b', border: '1px solid #334155' }}></span>
          <span>Unmodified Base</span>
        </div>
      </div>
    </div>
  )
}
