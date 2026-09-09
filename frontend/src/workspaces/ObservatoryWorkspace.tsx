import React from 'react'
import type {
  EventInspector,
  Experiment,
  MemoryMapPoint,
  MemoryRelationshipGraph,
} from '../types'
import { MemoryFieldCanvas } from '../components/MemoryFieldCanvas'
import { TimelineController } from '../components/TimelineController'

interface ObservatoryWorkspaceProps {
  experiment: Experiment | null
  currentStep: number
  onStepChange: (step: number) => void
  onJumpToEvent: (eventIdx: number) => void
  isPlaying: boolean
  onTogglePlay: () => void
  onStepForward: () => void
  onStepBackward: () => void
  mapPoints: MemoryMapPoint[]
  graph: MemoryRelationshipGraph | null
  selectedMemoryId: string | null
  onSelectMemory: (id: string) => void
  lastModifiedMemoryId: string | null
  eventInspector: EventInspector | null
  onLaunchDemo: () => void
  onOpenCreateExperiment: () => void
}

export const ObservatoryWorkspace: React.FC<ObservatoryWorkspaceProps> = ({
  experiment,
  currentStep,
  onStepChange,
  onJumpToEvent,
  isPlaying,
  onTogglePlay,
  onStepForward,
  onStepBackward,
  mapPoints,
  graph,
  selectedMemoryId,
  onSelectMemory,
  lastModifiedMemoryId,
  eventInspector,
  onLaunchDemo,
  onOpenCreateExperiment,
}) => {
  // ── Entry State ───────────────────────────────────────────────────
  if (!experiment) {
    return (
      <div className="empty-state">
        <svg className="empty-state-icon" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="1.5" opacity="0.3" />
          <circle cx="24" cy="24" r="10" stroke="currentColor" strokeWidth="1" opacity="0.5" />
          <circle cx="24" cy="24" r="3" fill="currentColor" opacity="0.6" />
          <line x1="24" y1="2" x2="24" y2="8" stroke="currentColor" strokeWidth="1" opacity="0.3" />
          <line x1="24" y1="40" x2="24" y2="46" stroke="currentColor" strokeWidth="1" opacity="0.3" />
          <line x1="2" y1="24" x2="8" y2="24" stroke="currentColor" strokeWidth="1" opacity="0.3" />
          <line x1="40" y1="24" x2="46" y2="24" stroke="currentColor" strokeWidth="1" opacity="0.3" />
        </svg>
        <h3>Neural Archaeology</h3>
        <p>
          Observe how computational memory forms, adapts, competes,
          and persists on a fixed-dimensional vector substrate.
          The memory field is currently void.
        </p>
        <div className="empty-state-actions">
          <button className="btn-primary" onClick={onLaunchDemo}>
            ▶ Launch Demo
          </button>
          <button onClick={onOpenCreateExperiment}>
            Configure Experiment
          </button>
        </div>
      </div>
    )
  }

  const currentSnapshot = experiment.snapshots[currentStep] || null
  const events = experiment.events || []
  const density = graph?.density ?? 0
  const activeCues = mapPoints.length || currentSnapshot?.num_active || 0

  return (
    <div className="observatory-layout">
      {/* ── Main Canvas Pane ─────────────────────────────────────── */}
      <div className="observatory-canvas-pane">
        {/* Toolbar */}
        <div className="observatory-toolbar">
          <div className="toolbar-left">
            <span className="toolbar-title">Memory Field</span>
            {activeCues > 0 && (
              <span className="metric-badge accent">{activeCues} active</span>
            )}
            {density > 0 && (
              <span className="metric-badge">
                {(density * 100).toFixed(1)}% dense
              </span>
            )}
          </div>
          <div className="toolbar-right">
            <span className="toolbar-hint">Hover to isolate · Click to excavate</span>
          </div>
        </div>

        {/* Living Canvas */}
        <div className="observatory-canvas-wrapper">
          <MemoryFieldCanvas
            snapshot={currentSnapshot}
            mapPoints={mapPoints}
            graph={graph}
            selectedMemoryId={selectedMemoryId}
            onSelectMemory={onSelectMemory}
            activeTimestep={currentStep}
            lastModifiedMemoryId={lastModifiedMemoryId}
          />
        </div>

        {/* Timeline strip */}
        <div className="observatory-timeline-wrapper">
          <TimelineController
            events={events}
            snapshots={experiment.snapshots}
            currentStep={currentStep}
            onStepChange={onStepChange}
            onJumpToEvent={onJumpToEvent}
            isPlaying={isPlaying}
            onTogglePlay={onTogglePlay}
            onStepForward={onStepForward}
            onStepBackward={onStepBackward}
          />
        </div>
      </div>

      {/* ── Right Sidebar ─────────────────────────────────────────── */}
      <aside className="observatory-sidebar">
        {/* State Difference */}
        <div className="obs-sidebar-section">
          <div className="obs-section-header">
            <span className="obs-section-title">State Δ</span>
            {eventInspector && (
              <span className="obs-section-count">
                Event {eventInspector.event_index + 1}
              </span>
            )}
          </div>
          {eventInspector ? (
            <div className="state-diff-card">
              <div>
                <div className="diff-event-label">
                  {eventInspector.concept_label}
                  <span style={{ color: 'var(--text-faint)', margin: '0 6px' }}>→</span>
                  {eventInspector.attribute_label}
                </div>
              </div>
              <div className="diff-metrics-row">
                <div className="diff-metric">
                  <span className="diff-metric-label">Δ Norm</span>
                  <span className="diff-metric-val">{eventInspector.delta_norm.toFixed(4)}</span>
                </div>
                <div className="diff-metric">
                  <span className="diff-metric-label">Cosine Δ</span>
                  <span
                    className="diff-metric-val"
                    style={{ color: 'var(--amber)' }}
                  >
                    {eventInspector.cosine_shift.toFixed(4)}
                  </span>
                </div>
              </div>
              {(eventInspector.strengthened_memories.length > 0 ||
                eventInspector.weakened_memories.length > 0) && (
                <div className="diff-tags">
                  {eventInspector.strengthened_memories.map((m) => (
                    <span key={m} className="diff-tag reinforced">{m}</span>
                  ))}
                  {eventInspector.weakened_memories.map((m) => (
                    <span key={m} className="diff-tag weakened">{m}</span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="diff-placeholder">
              Scrub the timeline or click an event to inspect state changes.
            </div>
          )}
        </div>

        {/* Event Stream */}
        <div className="obs-sidebar-section" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div className="obs-section-header">
            <span className="obs-section-title">Event stream</span>
            <span className="obs-section-count">{events.length}</span>
          </div>
          <div className="event-stream-list">
            {events.map((ev, idx) => {
              const stepNum = idx + 1
              const isActive = currentStep === stepNum
              const isConflict =
                idx > 0 &&
                events.slice(0, idx).some((e) => e.concept_label === ev.concept_label)

              return (
                <div
                  key={ev.id || idx}
                  className={`event-stream-item ${isActive ? 'active' : ''} ${isConflict ? 'conflict' : ''}`}
                  onClick={() => {
                    onStepChange(stepNum)
                    onJumpToEvent(idx)
                  }}
                >
                  <span className="event-idx">E{String(idx + 1).padStart(2, '0')}</span>
                  <div className="event-body">
                    <span className="event-type">
                      {isConflict ? '△ Competing write' : 'Memory encoded'}
                    </span>
                    <span className="event-binding">
                      <strong>{ev.concept_label}</strong> → {ev.attribute_label}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </aside>
    </div>
  )
}
