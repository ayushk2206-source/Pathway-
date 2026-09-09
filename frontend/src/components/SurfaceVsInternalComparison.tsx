import React from 'react'
import type { FingerprintComparison } from '../types'

interface SurfaceVsInternalComparisonProps {
  comparisons: FingerprintComparison[]
  selectedComparison: FingerprintComparison | null
  onSelectComparison: (comp: FingerprintComparison) => void
}

export const SurfaceVsInternalComparison: React.FC<SurfaceVsInternalComparisonProps> = ({
  comparisons,
  selectedComparison,
  onSelectComparison,
}) => {
  return (
    <div className="forensic-card">
      <div className="forensic-card-header">
        <h3 className="forensic-card-title">
          <span>Surface vs Internal Representation Similarity</span>
        </h3>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Input Cue Cosine vs Synaptic Outer Product Cosine
        </span>
      </div>

      <div className="surface-internal-container">
        {comparisons.map((comp) => {
          const isSelected =
            selectedComparison?.concept_a === comp.concept_a &&
            selectedComparison?.concept_b === comp.concept_b

          const isHighDiscrepancy = comp.similarity_discrepancy > 0.35

          return (
            <div
              key={`${comp.concept_a}-${comp.concept_b}`}
              className="sim-comparison-row"
              style={{
                borderColor: isSelected ? '#38bdf8' : undefined,
                background: isSelected ? 'rgba(56, 189, 248, 0.1)' : undefined,
                cursor: 'pointer',
              }}
              onClick={() => onSelectComparison(comp)}
            >
              <div className="sim-pair-title">
                <span>{comp.concept_a}</span>
                <span style={{ color: '#64748b' }}>vs</span>
                <span>{comp.concept_b}</span>
              </div>

              <div className="sim-values-group">
                <span className="sim-val-pill surface" title="Cosine of input cue vectors">
                  Surface: {comp.surface_similarity.toFixed(3)}
                </span>
                <span className="sim-val-pill internal" title="Cosine of flattened synaptic updates">
                  Internal: {comp.internal_similarity.toFixed(3)}
                </span>
                {isHighDiscrepancy && (
                  <span className="sim-divergence-badge" title="Significant difference between surface and internal similarity">
                    Δ Divergence: {comp.similarity_discrepancy.toFixed(3)}
                  </span>
                )}
              </div>
            </div>
          )
        })}

        {selectedComparison && (
          <div style={{
            padding: '0.8rem',
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '8px',
            fontSize: '0.8rem',
            color: '#e2e8f0',
            lineHeight: '1.4',
          }}>
            <strong>Empirical Finding:</strong> {selectedComparison.explanation}
          </div>
        )}
      </div>
    </div>
  )
}
