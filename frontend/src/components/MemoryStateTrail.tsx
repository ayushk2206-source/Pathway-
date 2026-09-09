import React from 'react'
import type { ObservatorySnapshot } from '../types'

interface MemoryStateTrailProps {
  snapshots: ObservatorySnapshot[]
  currentStep: number
  compareStep?: number
  onSelectStep: (step: number) => void
  onSelectCompareStep?: (step: number) => void
  isPlaying?: boolean
  onTogglePlay?: () => void
  onStepForward?: () => void
  onStepBackward?: () => void
}

export const MemoryStateTrail: React.FC<MemoryStateTrailProps> = ({
  snapshots,
  currentStep,
  compareStep,
  onSelectStep,
  onSelectCompareStep,
  isPlaying,
  onTogglePlay,
  onStepForward,
  onStepBackward,
}) => {
  const getBadgeClass = (event: string) => {
    if (event.includes('WRITE')) return 'badge-WRITE'
    if (event.includes('SHIFT')) return 'badge-SHIFT'
    if (event.includes('INTERFERENCE')) return 'badge-INTERFERENCE'
    if (event.includes('RECOVERY')) return 'badge-RECOVERY'
    if (event.includes('MODIFICATION')) return 'badge-MODIFICATION'
    if (event.includes('DECAY')) return 'badge-DECAY'
    return 'badge-BASELINE'
  }

  return (
    <div className="timeline-strip-container">
      <div className="timeline-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <strong style={{ color: '#f8fafc' }}>Memory State Trail (Timelines)</strong>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Current: Step {currentStep} {compareStep !== undefined ? `| Compared to: Step ${compareStep}` : ''}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <button
            className="observatory-btn"
            onClick={onStepBackward}
            disabled={currentStep <= 0}
            title="Step backward"
          >
            ◀
          </button>
          <button
            className="observatory-btn primary"
            onClick={onTogglePlay}
            title={isPlaying ? 'Pause stream' : 'Play stream'}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          <button
            className="observatory-btn"
            onClick={onStepForward}
            disabled={currentStep >= snapshots.length - 1}
            title="Step forward"
          >
            ▶
          </button>
        </div>
      </div>

      <div className="timeline-track">
        {snapshots.map((snap) => {
          const isActive = snap.step === currentStep
          const isCompared = snap.step === compareStep
          const avgFidelity = snap.probes && snap.probes.length > 0
            ? snap.probes.reduce((sum, p) => sum + p.fidelity, 0) / snap.probes.length
            : 0

          return (
            <div
              key={snap.step}
              className={`timeline-step-node ${isActive ? 'active' : ''} ${isCompared ? 'compared' : ''}`}
              onClick={(e) => {
                if (e.shiftKey && onSelectCompareStep) {
                  onSelectCompareStep(snap.step)
                } else {
                  onSelectStep(snap.step)
                }
              }}
              title={`Step ${snap.step}: ${snap.adaptation_description}\n(Shift-click to set as comparison step)`}
            >
              <div className="step-number">T{snap.step}</div>
              <span className={`step-badge ${getBadgeClass(snap.adaptation_event)}`}>
                {snap.adaptation_event.replace('MEMORY_', '').replace('PASSIVE_', '')}
              </span>

              <div className="step-fidelity-bar">
                <div
                  className="step-fidelity-fill"
                  style={{
                    width: `${Math.round(avgFidelity * 100)}%`,
                    backgroundColor: avgFidelity > 0.8 ? '#10b981' : avgFidelity > 0.5 ? '#f59e0b' : '#ef4444',
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
