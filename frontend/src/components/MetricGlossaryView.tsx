import React from 'react'
import type { MetricDefinition } from '../types'
import { SciBadge } from './ScientificBadges'

interface MetricGlossaryViewProps {
  metrics: MetricDefinition[]
}

export const MetricGlossaryView: React.FC<MetricGlossaryViewProps> = ({ metrics }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.2rem', color: '#f8fafc' }}>
            Mathematical Metric Definitions & Glossary
          </h2>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Formal equations, measurement units, computational interpretations, and real mathematical limitations.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <SciBadge type="live" label="DETERMINISTIC" />
          <SciBadge type="simplified" label="LINEAR METRICS" />
        </div>
      </div>

      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div key={metric.metric_id} className="metric-card">
            <div className="metric-card-top">
              <span className="metric-name">{metric.name}</span>
              <span className="metric-symbol">{metric.symbol}</span>
            </div>

            <div className="metric-formula-box">
              <code>{metric.formula}</code>
            </div>

            <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
              <strong>Unit:</strong> {metric.unit}
            </div>

            <div className="metric-body">
              <strong style={{ color: '#94a3b8', display: 'block', fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                DEFINITION:
              </strong>
              {metric.definition}
            </div>

            <div className="metric-body" style={{ background: 'rgba(56, 189, 248, 0.05)', padding: '0.5rem', borderRadius: '6px' }}>
              <strong style={{ color: '#38bdf8', display: 'block', fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                INTERPRETATION:
              </strong>
              {metric.interpretation}
            </div>

            <div className="metric-limitation">
              <strong style={{ color: '#ef4444', display: 'block', fontSize: '0.76rem', marginBottom: '0.15rem' }}>
                MATHEMATICAL LIMITATION:
              </strong>
              {metric.limitation}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MetricGlossaryView
