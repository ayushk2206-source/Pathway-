import React, { useMemo } from 'react'
import type { ExperimentEvent, Snapshot } from '../types'

interface TimelineControllerProps {
  events: ExperimentEvent[]
  snapshots: Snapshot[]
  currentStep: number
  onStepChange: (step: number) => void
  onJumpToEvent: (eventIdx: number) => void
  isPlaying: boolean
  onTogglePlay: () => void
  onStepForward: () => void
  onStepBackward: () => void
}

export const TimelineController: React.FC<TimelineControllerProps> = ({
  events,
  snapshots,
  currentStep,
  onStepChange,
  onJumpToEvent,
  isPlaying,
  onTogglePlay,
  onStepForward,
  onStepBackward,
}) => {
  const totalSteps = snapshots.length || events.length || 1
  const currentSnapshot = snapshots[currentStep] || null
  const currentEvent = events[Math.max(0, currentStep - 1)] || null

  const activeUnits = currentSnapshot?.num_active ?? currentSnapshot?.active_dimensions?.length ?? 0
  const sparsity = currentSnapshot?.sparsity ?? 0
  const norm = currentSnapshot?.norm ?? 0

  // Detect conflict events
  const conflictSet = useMemo(() => {
    const seen = new Map<string, number>()
    const conflicts = new Set<number>()
    events.forEach((ev, idx) => {
      const key = ev.concept_label
      if (seen.has(key)) conflicts.add(idx)
      else seen.set(key, idx)
    })
    return conflicts
  }, [events])

  const progressPct = totalSteps > 1
    ? `${((currentStep / (totalSteps - 1)) * 100).toFixed(2)}%`
    : '0%'

  return (
    <div className="timeline-controller">
      {/* ── Controls Row ────────────────────────────────────────── */}
      <div className="timeline-controls-row">
        <div className="timeline-playback">
          <button
            className={`tl-btn ${isPlaying ? 'active' : ''}`}
            onClick={onTogglePlay}
            title="Play / Pause (Space)"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>
          <button className="tl-btn" onClick={onStepBackward} title="Previous step (←)" aria-label="Previous step">
            ◀
          </button>
          <button className="tl-btn" onClick={onStepForward} title="Next step (→)" aria-label="Next step">
            ▶
          </button>
        </div>

        <div className="tl-divider" />

        <span className="tl-step-info">
          <span className="tl-step-current">{currentStep}</span>
          {' '}/ {totalSteps - 1}
        </span>

        {currentEvent && (
          <>
            <div className="tl-divider" />
            <span className="tl-event-pill">
              <strong>{currentEvent.concept_label}</strong>
              {' → '}
              {currentEvent.attribute_label}
            </span>
          </>
        )}

        {/* Right: key metrics */}
        <div style={{ marginLeft: 'auto' }} className="timeline-telemetry">
          {activeUnits > 0 && (
            <div className="tl-stat">
              <span className="tl-stat-label">Active</span>
              <span className="tl-stat-val">{activeUnits}</span>
            </div>
          )}
          {sparsity > 0 && (
            <div className="tl-stat">
              <span className="tl-stat-label">Sparsity</span>
              <span className="tl-stat-val">{sparsity.toFixed(3)}</span>
            </div>
          )}
          {norm > 0 && (
            <div className="tl-stat">
              <span className="tl-stat-label">Norm</span>
              <span className="tl-stat-val">{norm.toFixed(3)}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Scrub Track ──────────────────────────────────────────── */}
      <div className="timeline-track-area">
        {/* Background line */}
        <div className="timeline-track-bg" />
        {/* Progress fill */}
        <div
          className="timeline-track-progress"
          style={{ width: progressPct }}
        />

        {/* Event nodes */}
        <div className="timeline-nodes">
          {events.map((ev, idx) => {
            const stepNum = idx + 1
            const isCurrent = currentStep === stepNum
            const isPast = currentStep > stepNum
            const isConflict = conflictSet.has(idx)

            return (
              <div
                key={ev.id || idx}
                className={`tl-node ${isCurrent ? 'active' : ''} ${isPast ? 'past' : ''} ${isConflict ? 'conflict' : ''}`}
                onClick={() => {
                  onStepChange(stepNum)
                  onJumpToEvent(idx)
                }}
                title={`${isConflict ? '⚠ Conflict · ' : ''}${ev.concept_label} → ${ev.attribute_label}`}
              >
                <div className="tl-node-dot" />
                <span className="tl-node-label">
                  {isConflict ? '△' : `E${String(idx + 1).padStart(2, '0')}`}
                </span>
              </div>
            )
          })}
        </div>

        {/* Invisible range slider for dragging */}
        <input
          type="range"
          className="timeline-slider"
          min={0}
          max={Math.max(1, totalSteps - 1)}
          value={currentStep}
          onChange={(e) => onStepChange(Number(e.target.value))}
          aria-label="Timeline position"
        />
      </div>
    </div>
  )
}
