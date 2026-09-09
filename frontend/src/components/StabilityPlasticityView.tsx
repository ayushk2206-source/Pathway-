import React from 'react'
import type { StabilityPlasticityMetrics } from '../types'

interface StabilityPlasticityViewProps {
  metrics: StabilityPlasticityMetrics | null
  isLoading?: boolean
}

export const StabilityPlasticityView: React.FC<StabilityPlasticityViewProps> = ({
  metrics,
  isLoading,
}) => {
  if (isLoading) {
    return <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Evaluating stability metrics...</div>
  }

  if (!metrics) {
    return (
      <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
        Run or scrub stream to calculate stability and plasticity metrics.
      </div>
    )
  }

  const stabilityPct = Math.round(metrics.stability_ratio * 100)
  const plasticityPct = Math.round(metrics.plasticity_extent * 100)

  return (
    <div className="dual-gauge-container">
      <div className="gauge-bars">
        <div className="gauge-row">
          <div className="gauge-label-row">
            <span>Stability Ratio (Preserved Synapses)</span>
            <strong style={{ color: '#38bdf8' }}>{stabilityPct}%</strong>
          </div>
          <div className="gauge-track">
            <div className="gauge-fill-stability" style={{ width: `${stabilityPct}%` }} />
          </div>
        </div>

        <div className="gauge-row">
          <div className="gauge-label-row">
            <span>Plasticity Extent (Reconfigured Synapses)</span>
            <strong style={{ color: '#ec4899' }}>{plasticityPct}%</strong>
          </div>
          <div className="gauge-track">
            <div className="gauge-fill-plasticity" style={{ width: `${plasticityPct}%` }} />
          </div>
        </div>
      </div>

      <div className="stability-metrics-grid">
        <div>Total Synapses: <strong style={{ color: '#f8fafc' }}>{metrics.total_synapses}</strong></div>
        <div>Unchanged: <strong style={{ color: '#38bdf8' }}>{metrics.unchanged_synapses}</strong></div>
        <div>Adapted: <strong style={{ color: '#ec4899' }}>{metrics.adapted_synapses}</strong></div>
        <div>Consolidated: <strong style={{ color: '#10b981' }}>{metrics.consolidated_count}</strong></div>
        <div>High Plasticity: <strong style={{ color: '#fbbf24' }}>{metrics.high_plasticity_count}</strong></div>
        <div>Avg Weight Shift: <strong style={{ color: '#c084fc' }}>{metrics.average_weight_shift.toFixed(4)}</strong></div>
      </div>
    </div>
  )
}
