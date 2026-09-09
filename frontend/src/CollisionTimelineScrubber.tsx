import React from 'react'
import type { CollisionTimelineStep } from './types'

interface CollisionTimelineScrubberProps {
  timeline: CollisionTimelineStep[]
  activeStepIndex: number
  onSelectStep: (stepIndex: number) => void
}

export const CollisionTimelineScrubber: React.FC<CollisionTimelineScrubberProps> = ({
  timeline,
  activeStepIndex,
  onSelectStep,
}) => {
  if (!timeline || timeline.length === 0) return null

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '11px', color: '#94a3b8' }}>
          COLLISION TIMELINE MACHINE (Step-by-step matrix evolution)
        </span>
        <span style={{ fontSize: '10px', color: '#64748b' }}>
          Step {activeStepIndex + 1} of {timeline.length}
        </span>
      </div>

      <div className="collision-timeline">
        {timeline.map((stepItem, idx) => {
          const isActive = idx === activeStepIndex
          let badgeColor = '#38bdf8'
          if (stepItem.event_type.includes('COLLISION') || stepItem.event_type === 'WRITE_2') {
            badgeColor = '#fbbf24'
          } else if (stepItem.event_type.startsWith('RECALL')) {
            badgeColor = '#c084fc'
          } else if (stepItem.event_type === 'DECAY_DELAY') {
            badgeColor = '#94a3b8'
          }

          return (
            <div
              key={idx}
              className={`timeline-node ${isActive ? 'active' : ''}`}
              onClick={() => onSelectStep(idx)}
            >
              <span className="timeline-step-badge" style={{ color: badgeColor }}>
                T{stepItem.step} • {stepItem.event_type}
              </span>
              <span className="timeline-step-name" title={stepItem.label}>
                {stepItem.label}
              </span>
              <span className="timeline-step-meta">
                {stepItem.fidelity !== undefined
                  ? `Fidelity: ${stepItem.fidelity.toFixed(2)}`
                  : `‖W‖: ${stepItem.matrix_norm.toFixed(2)}`}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
