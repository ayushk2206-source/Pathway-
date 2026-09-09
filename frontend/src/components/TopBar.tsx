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
  onOpenJudgeMode?: () => void
  isBusy: boolean
  selectedMemoryId?: string | null
  isFollowingMemory?: boolean
  onToggleFollowMemory?: () => void
}

export const TopBar: React.FC<TopBarProps> = ({
  currentExperiment,
  experiments,
  onSelectExperiment,
  onLaunchDemo,
  onReplay,
  onOpenCommandPalette,
  onOpenShortcuts,
  onOpenJudgeMode,
  isBusy,
  selectedMemoryId,
  isFollowingMemory = true,
  onToggleFollowMemory,
}) => {
  const mechanism = currentExperiment?.mechanism?.toUpperCase() || null
  const dim = currentExperiment?.task?.d || null
  const numEvents = currentExperiment?.events?.length || 0

  return (
    <header className="topbar">
      {/* ── Brand ── */}
      <div className="topbar-left">
        <div className="brand">
          <div className="brand-icon-box">
            <span className="brand-glyph">◈</span>
          </div>
          <div className="brand-text-block">
            <span className="brand-wordmark">NEURAL ARCHAEOLOGY</span>
            <span className="brand-tagline">RESEARCH INSTRUMENT</span>
          </div>
        </div>

        <div className="topbar-status-pill">
          <span className={`status-led ${isBusy ? 'busy' : 'live'}`} />
          <span className="status-text">{isBusy ? 'COMPUTING' : 'SUBSTRATE READY'}</span>
        </div>
      </div>

      {/* ── Research Context (center) ── */}
      <div className="topbar-center">
        {currentExperiment ? (
          <div className="topbar-context-strip">
            <span className="context-pill exp-pill">
              <span className="pill-k">EXP</span>
              <span className="pill-v">{currentExperiment.experiment_id.slice(0, 8)}</span>
            </span>
            {mechanism && (
              <span className="context-pill mech-pill">
                <span className="pill-k">MECH</span>
                <span className="pill-v">{mechanism}</span>
              </span>
            )}
            {dim && (
              <span className="context-pill dim-pill">
                <span className="pill-k">DIM</span>
                <span className="pill-v">{dim}D</span>
              </span>
            )}
            {numEvents > 0 && (
              <span className="context-pill evt-pill">
                <span className="pill-k">EVT</span>
                <span className="pill-v">{numEvents}</span>
              </span>
            )}
          </div>
        ) : (
          <span className="topbar-empty-context">
            NO ACTIVE EXPERIMENT LOADED
          </span>
        )}
      </div>

      {/* ── Actions (right) ── */}
      <div className="topbar-right">
        {/* Global Memory Selector & Follow Badge */}
        {selectedMemoryId && (
          <div className="topbar-memory-pill">
            <span className="memory-pill-label">INSPECT</span>
            <span className="memory-pill-val">{selectedMemoryId.slice(0, 14)}</span>
            {onToggleFollowMemory && (
              <button
                className={`topbar-follow-toggle ${isFollowingMemory ? 'active' : ''}`}
                onClick={onToggleFollowMemory}
                title="Toggle 'Follow This Memory' mode across all tools"
              >
                <span>{isFollowingMemory ? '★' : '☆'}</span>
                <span>{isFollowingMemory ? 'FOLLOW' : 'LOCK'}</span>
              </button>
            )}
          </div>
        )}

        {/* Experiment selector dropdown */}
        {experiments.length > 0 && (
          <div className="exp-selector-box">
            <select
              className="exp-select"
              value={currentExperiment?.experiment_id || ''}
              onChange={(e) => e.target.value && onSelectExperiment(e.target.value)}
              disabled={isBusy}
              title="Switch experiment"
              aria-label="Switch experiment"
            >
              {currentExperiment ? (
                <option value={currentExperiment.experiment_id}>
                  {currentExperiment.experiment_id.slice(0, 10)}
                </option>
              ) : (
                <option value="">Select Experiment</option>
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

        {/* Judge Mode Tour Trigger */}
        {onOpenJudgeMode && (
          <button
            className="topbar-judge-pill-btn"
            onClick={onOpenJudgeMode}
            title="Launch 2-minute Judge Mode evaluation tour (J)"
          >
            ★ JUDGE MODE
          </button>
        )}

        {/* Action Controls */}
        <button
          className="topbar-pill-btn btn-primary"
          onClick={onLaunchDemo}
          disabled={isBusy}
          title="Launch canonical demo experiment"
        >
          ▶ Demo
        </button>

        <button
          className="topbar-pill-btn btn-secondary"
          onClick={onReplay}
          disabled={isBusy || !currentExperiment}
          title="Re-execute state sequence"
        >
          ↺ Replay
        </button>

        <button
          className="topbar-icon-pill"
          onClick={onOpenCommandPalette}
          title="Command palette (Ctrl/Cmd + K)"
          aria-label="Command palette"
        >
          <span className="kbd">⌘K</span>
        </button>

        <button
          className="topbar-icon-pill"
          onClick={onOpenShortcuts}
          title="Keyboard shortcuts (?)"
          aria-label="Keyboard shortcuts"
        >
          <span className="kbd">?</span>
        </button>
      </div>
    </header>
  )
}
