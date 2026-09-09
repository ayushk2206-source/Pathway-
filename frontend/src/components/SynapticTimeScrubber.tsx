import React, { useEffect, useRef } from 'react'
import type { SynapticTimelineEvent } from '../types'

interface SynapticTimeScrubberProps {
  timeline: SynapticTimelineEvent[]
  currentStep: number
  totalSteps: number
  isPlaying: boolean
  playbackSpeed: number
  isFrozen: boolean
  diffMode: boolean
  onScrub: (step: number) => void
  onTogglePlay: () => void
  onStepForward: () => void
  onStepBackward: () => void
  onSetSpeed: (speed: number) => void
  onToggleFreeze: () => void
  onToggleDiff: () => void
  onRunProtocol: () => void
}

export const SynapticTimeScrubber: React.FC<SynapticTimeScrubberProps> = ({
  timeline,
  currentStep,
  totalSteps,
  isPlaying,
  playbackSpeed,
  isFrozen,
  diffMode,
  onScrub,
  onTogglePlay,
  onStepForward,
  onStepBackward,
  onSetSpeed,
  onToggleFreeze,
  onToggleDiff,
  onRunProtocol,
}) => {
  const ribbonRef = useRef<HTMLDivElement>(null)

  // Auto-scroll the timeline ribbon to keep current step visible
  useEffect(() => {
    if (ribbonRef.current) {
      const activeEl = ribbonRef.current.querySelector(`[data-step="${currentStep}"]`)
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      }
    }
  }, [currentStep])

  const maxStep = Math.max(0, totalSteps - 1)
  const currentEvent = timeline[currentStep] || timeline[0]

  const getEventBadgeClass = (type: string = '') => {
    switch (type.toUpperCase()) {
      case 'WRITE':
        return 'event-chip-write'
      case 'RECALL':
        return 'event-chip-recall'
      case 'DECAY':
        return 'event-chip-decay'
      default:
        return 'event-chip-init'
    }
  }

  return (
    <div className={`synaptic-time-scrubber ${isFrozen ? 'frozen-state' : ''}`}>
      {/* Top Chronometer Status Bar */}
      <div className="scrubber-status-bar">
        <div className="scrubber-status-left">
          <span className="scrubber-step-badge">
            <span className="step-label">TIMESTEP</span>
            <span className="step-val">
              T{currentStep} / T{maxStep}
            </span>
          </span>

          {currentEvent && (
            <div className="scrubber-event-summary">
              <span className={`event-type-tag ${getEventBadgeClass(currentEvent.event_type)}`}>
                {currentEvent.event_type || 'INIT'}
              </span>
              <span className="event-label-text">{currentEvent.label || 'Resting State'}</span>
            </div>
          )}

          {isFrozen && (
            <span className="freeze-indicator-tag" title="State is locked for microscopic inspection">
              ❄ FROZEN AT T{currentStep}
            </span>
          )}
        </div>

        <div className="scrubber-status-right">
          <div className="metric-chip">
            <span className="metric-k">||W||:</span>
            <span className="metric-v">{(currentEvent?.matrix_norm ?? 0).toFixed(3)}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-k">ACTIVE SYNS:</span>
            <span className="metric-v">{currentEvent?.active_synapses ?? 0}</span>
          </div>

          <button
            type="button"
            className={`btn-scrubber-action ${isFrozen ? 'btn-frozen-active' : ''}`}
            onClick={onToggleFreeze}
            title={isFrozen ? 'Unfreeze time machine' : 'Freeze state for forensic inspection'}
          >
            {isFrozen ? '▶ UNFREEZE' : '❄ FREEZE'}
          </button>

          <button
            type="button"
            className={`btn-scrubber-action ${diffMode ? 'btn-diff-active' : ''}`}
            onClick={onToggleDiff}
            title="Forensic Before / After State Delta Comparison"
          >
            ⚖ COMPARE
          </button>

          <button
            type="button"
            className="btn-scrubber-action btn-protocol"
            onClick={onRunProtocol}
            title="Execute Guided Protocol: Write -> Strengthen -> Hold -> Decay -> Recall"
          >
            🧪 GUIDED DEMO
          </button>
        </div>
      </div>

      {/* Main Scrubber Control Row */}
      <div className="scrubber-slider-row">
        {/* Transport Buttons */}
        <div className="transport-controls">
          <button
            type="button"
            className="transport-btn"
            onClick={() => onScrub(0)}
            disabled={currentStep === 0}
            title="First Timestep (T0)"
          >
            ⏮
          </button>
          <button
            type="button"
            className="transport-btn"
            onClick={onStepBackward}
            disabled={currentStep === 0}
            title="Step Backward (Previous State)"
          >
            ◀
          </button>
          <button
            type="button"
            className={`transport-btn play-btn ${isPlaying ? 'playing' : ''}`}
            onClick={onTogglePlay}
            title={isPlaying ? 'Pause Playback' : 'Play Timeline Evolution'}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>
          <button
            type="button"
            className="transport-btn"
            onClick={onStepForward}
            disabled={currentStep >= maxStep}
            title="Step Forward (Next State)"
          >
            ▶
          </button>
          <button
            type="button"
            className="transport-btn"
            onClick={() => onScrub(maxStep)}
            disabled={currentStep >= maxStep}
            title="Latest Timestep"
          >
            ⏭
          </button>

          {/* Speed Selector */}
          <div className="playback-speed-selector">
            {[0.5, 1, 2, 4].map((s) => (
              <button
                key={s}
                type="button"
                className={`speed-pill ${playbackSpeed === s ? 'active' : ''}`}
                onClick={() => onSetSpeed(s)}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Range Slider */}
        <div className="scrubber-range-container">
          <input
            type="range"
            min={0}
            max={maxStep}
            value={currentStep}
            onChange={(e) => onScrub(parseInt(e.target.value, 10))}
            className="scrubber-range-input"
            aria-label="Time machine scrubber"
          />
          <div className="scrubber-ticks">
            {timeline.map((ev, idx) => (
              <span
                key={idx}
                className={`scrubber-tick ${idx === currentStep ? 'active' : ''}`}
                style={{ left: maxStep > 0 ? `${(idx / maxStep) * 100}%` : '0%' }}
                onClick={() => onScrub(idx)}
                title={`T${idx}: ${ev.label}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Horizontal Event Chips Ribbon */}
      <div className="scrubber-ribbon" ref={ribbonRef}>
        {timeline.map((ev, idx) => {
          const isSelected = idx === currentStep
          return (
            <button
              key={idx}
              type="button"
              data-step={idx}
              className={`timeline-ribbon-chip ${isSelected ? 'active' : ''} ${getEventBadgeClass(ev.event_type)}`}
              onClick={() => onScrub(idx)}
            >
              <div className="ribbon-chip-top">
                <span className="ribbon-chip-step">T{idx}</span>
                <span className="ribbon-chip-type">{ev.event_type}</span>
              </div>
              <div className="ribbon-chip-label" title={ev.label}>
                {ev.label}
              </div>
              <div className="ribbon-chip-sub">
                <span>||W||: {(ev.matrix_norm ?? 0).toFixed(2)}</span>
                <span>syns: {ev.active_synapses ?? 0}</span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
