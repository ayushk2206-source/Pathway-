import React from 'react'

export type FlowStage = 'IDLE' | 'ACTIVITY' | 'SYNAPTIC_WRITE' | 'TEMPORARY_STATE' | 'RECALL'

interface SynapticFlowVisualizerProps {
  currentStage?: FlowStage
  activeMemoryConcept?: string
  activeMemoryValue?: string
  fidelity?: number
  matrixNorm?: number
}

const STAGES: Array<{ id: FlowStage; name: string; sub: string; num: string }> = [
  { id: 'ACTIVITY', name: '1. Activity', sub: 'Input Vector v ⊗ k', num: '01' },
  { id: 'SYNAPTIC_WRITE', name: '2. Synaptic Write', sub: 'W(t+1) = (1-λ)W + ηΔW', num: '02' },
  { id: 'TEMPORARY_STATE', name: '3. Temporary State', sub: 'Matrix Energy ||W||_F', num: '03' },
  { id: 'RECALL', name: '4. Recall', sub: 'Readout v̂ = W @ k', num: '04' },
]

export const SynapticFlowVisualizer: React.FC<SynapticFlowVisualizerProps> = ({
  currentStage = 'TEMPORARY_STATE',
  activeMemoryConcept,
  activeMemoryValue,
  fidelity,
  matrixNorm,
}) => {
  return (
    <div className="synaptic-flow-banner" role="region" aria-label="Synaptic Plasticity Flow Pipeline">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.08em' }}>
          SYNAPTIC FLOW
        </span>
        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
          [MATHEMATICAL STATE PIPELINE]
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {STAGES.map((stage, idx) => {
          const isActive = currentStage === stage.id
          const isPassed =
            currentStage === 'RECALL' ||
            (currentStage === 'TEMPORARY_STATE' && idx <= 2) ||
            (currentStage === 'SYNAPTIC_WRITE' && idx <= 1)

          return (
            <React.Fragment key={stage.id}>
              <div className={`flow-step ${isActive ? 'active' : ''}`}>
                <div
                  className="flow-step-icon"
                  style={{
                    backgroundColor: isActive ? '#0284c7' : isPassed ? 'rgba(56, 189, 248, 0.15)' : undefined,
                    color: isActive ? '#ffffff' : isPassed ? '#38bdf8' : undefined,
                    borderColor: isActive ? '#38bdf8' : isPassed ? 'rgba(56, 189, 248, 0.4)' : undefined,
                  }}
                >
                  {stage.num}
                </div>
                <div className="flow-step-info">
                  <span
                    className="flow-step-name"
                    style={{ color: isActive ? '#38bdf8' : isPassed ? '#f1f5f9' : '#64748b' }}
                  >
                    {stage.name}
                  </span>
                  <span className="flow-step-sub">{stage.sub}</span>
                </div>
              </div>

              {idx < STAGES.length - 1 && <span className="flow-arrow">&rarr;</span>}
            </React.Fragment>
          )
        })}
      </div>

      {(activeMemoryConcept || fidelity !== undefined || matrixNorm !== undefined) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', fontSize: '0.75rem', color: '#cbd5e1' }}>
          {activeMemoryConcept && (
            <span style={{ background: 'rgba(0,0,0,0.3)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
              Binding: <strong>{activeMemoryConcept}</strong> &rarr; <em>{activeMemoryValue || '?'}</em>
            </span>
          )}
          {matrixNorm !== undefined && (
            <span style={{ color: '#94a3b8' }}>
              ||W||: <strong>{matrixNorm.toFixed(2)}</strong>
            </span>
          )}
          {fidelity !== undefined && (
            <span style={{ color: fidelity >= 0.8 ? '#34d399' : '#fbbf24' }}>
              F: <strong>{(fidelity * 100).toFixed(0)}%</strong>
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default SynapticFlowVisualizer
