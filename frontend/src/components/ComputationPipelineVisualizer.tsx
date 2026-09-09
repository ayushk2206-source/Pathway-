import React from 'react'
import type { StudioComputationStep } from '../types'

interface ComputationPipelineVisualizerProps {
  steps: StudioComputationStep[]
  isRunning?: boolean
}

export const ComputationPipelineVisualizer: React.FC<ComputationPipelineVisualizerProps> = ({
  steps,
  isRunning = false,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          Physical Execution Pipeline
        </span>
        {isRunning && (
          <span style={{ fontSize: '0.7rem', color: '#38bdf8', fontWeight: 700 }}>
            ⚡ COMPUTING...
          </span>
        )}
      </div>

      <div className="studio-pipeline-strip">
        {steps.map((step) => (
          <div key={step.order_index} className="studio-pipeline-step active">
            <span className="studio-step-tag">
              #{step.order_index} {step.step_name}
            </span>
            <span className="studio-step-detail">{step.detail}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
