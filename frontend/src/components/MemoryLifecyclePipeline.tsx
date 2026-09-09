import React from 'react'
import type { MemoryLifecycle, LifecycleStage } from '../types'

interface MemoryLifecyclePipelineProps {
  lifecycle: MemoryLifecycle | null
  onSelectStage: (stage: LifecycleStage) => void
}

export const MemoryLifecyclePipeline: React.FC<MemoryLifecyclePipelineProps> = ({
  lifecycle,
  onSelectStage,
}) => {
  if (!lifecycle) {
    return null
  }

  return (
    <div className="lifecycle-pipeline-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>⤳</span>
          <span>MEMORY LIFECYCLE PIPELINE</span>
        </h3>
        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
          Click any stage to navigate to the underlying experiment
        </span>
      </div>

      <div className="pipeline-track">
        {lifecycle.stages.map((stage, idx) => {
          const isCurrent = stage.stage_id === lifecycle.current_stage_id
          const isCompleted = stage.status === 'COMPLETED'

          return (
            <div
              key={stage.stage_id}
              className={`pipeline-step ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`}
              onClick={() => onSelectStage(stage)}
              title={`${stage.name}: ${stage.description}`}
            >
              <div className="pipeline-step-header">
                <span className="pipeline-step-id">0{idx + 1} · {stage.stage_id}</span>
                <span
                  style={{
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    color: isCurrent ? '#38bdf8' : isCompleted ? '#10b981' : '#64748b',
                  }}
                >
                  {isCurrent ? 'CURRENT' : stage.status}
                </span>
              </div>

              <div className="pipeline-step-name">{stage.name}</div>

              <div style={{ fontSize: '0.68rem', color: '#94a3b8', lineHeight: 1.3 }}>
                {stage.description}
              </div>

              <div style={{ marginTop: 'auto', paddingTop: '0.4rem', borderTop: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#64748b' }}>
                <span>Workspace:</span>
                <strong style={{ color: '#38bdf8', textTransform: 'uppercase' }}>{stage.target_workspace}</strong>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
