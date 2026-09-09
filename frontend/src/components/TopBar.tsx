import React from 'react'
import type { Experiment, ExperimentSummary } from '../types'

interface TopBarProps {
  currentExperiment: Experiment | null
  experiments: ExperimentSummary[]
  onSelectExperiment: (id: string) => void
  onLaunchDemo: () => void
  onReplay: () => void
  onOpenCommandPalette: () => void
  onOpenShortcuts: () => void
  isBusy: boolean
}

export const TopBar: React.FC<TopBarProps> = ({
  currentExperiment,
  experiments,
  onSelectExperiment,
  onLaunchDemo,
  onReplay,
  onOpenCommandPalette,
  isBusy,
}) => {
  const mechanism = currentExperiment?.mechanism?.toUpperCase() || null
  const dim = currentExperiment?.task?.d || null
  const numEvents = currentExperiment?.events?.length || 0

  return (
    <header className="topbar">
      {/* ── Brand ── */}
      <div className="topbar-left">
        <div className="brand">
          <span className="brand-wordmark">Neural Archaeology</span>
          <span className="brand-tagline">research instrument</span>
        </div>

        <div className="topbar-status">
          <span className={`status-dot ${isBusy ? 'busy' : 'live'}`} />
          <span style={{ fontSize: 10, fontWeight: 500 }}>
            {isBusy ? 'Computing' : 'Live'}
          </span>
        </div>
      </div>

      {/* ── Research Context (center) ── */}
      <div className="topbar-center">
        {currentExperiment ? (
          <span className="topbar-context">
            <span className="topbar-context-name">
              {currentExperiment.experiment_id.slice(0, 8)}
            </span>
            <span className="topbar-context-sep">·</span>
            {mechanism && <span>{mechanism}</span>}
            {dim && (
              <>
                <span className="topbar-context-sep">·</span>
                <span>{dim}D substrate</span>
              </>
            )}
            {numEvents > 0 && (
              <>
                <span className="topbar-context-sep">·</span>
                <span>{numEvents} events</span>
              </>
            )}
          </span>
        ) : (
          <span className="topbar-context" style={{ fontStyle: 'italic', opacity: 0.5 }}>
            No experiment loaded
          </span>
        )}
      </div>

      {/* ── Actions (right) ── */}
      <div className="topbar-right">
        {/* Experiment selector — compact */}
        {experiments.length > 0 && (
          <div className="exp-selector">
            <select
              className="exp-select"
              value={currentExperiment?.experiment_id || ''}
              onChange={(e) => e.target.value && onSelectExperiment(e.target.value)}
              disabled={isBusy}
              title="Switch experiment"
            >
              {currentExperiment ? (
                <option value={currentExperiment.experiment_id}>
                  {currentExperiment.experiment_id.slice(0, 10)}
                </option>
              ) : (
                <option value="">No experiment</option>
              )}
              {experiments
                .filter((e) => e.experiment_id !== currentExperiment?.experiment_id)
                .map((e) => (
                  <option key={e.experiment_id} value={e.experiment_id}>
                    {e.experiment_id.slice(0, 10)} · {e.mechanism}
                  </option>
                ))}
            </select>
          </div>
        )}

        <button
          className="topbar-btn btn-primary"
          onClick={onLaunchDemo}
          disabled={isBusy}
          title="Launch canonical demo experiment"
        >
          ▶ Demo
        </button>

        <button
          className="topbar-btn"
          onClick={onReplay}
          disabled={isBusy || !currentExperiment}
          title="Re-execute state sequence"
        >
          ↺ Replay
        </button>

        <button
          className="topbar-btn btn-ghost"
          onClick={onOpenCommandPalette}
          title="Command palette (Ctrl/Cmd + K)"
        >
          <span className="kbd">⌘K</span>
        </button>
      </div>
    </header>
  )
}
