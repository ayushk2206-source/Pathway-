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
  onNavigate?: (area: 'observatory' | 'substrate' | 'evaluation' | 'research') => void
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
  onNavigate,
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
          <span className="brand-tagline">scientific instrument</span>
        </div>

        <div className="topbar-status">
          <span className={`status-led ${isBusy ? 'busy' : 'live'}`} />
          <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.04em' }}>
            {isBusy ? 'COMPUTING' : 'READY'}
          </span>
        </div>
      </div>

      {/* ── Research Context (center) ── */}
      <div className="topbar-center">
        {currentExperiment ? (
          <div className="topbar-context" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="mono-badge cyan">
              EXP: {currentExperiment.experiment_id.slice(0, 8)}
            </span>
            {mechanism && (
              <span className="mono-badge violet">
                {mechanism}
              </span>
            )}
            {dim && (
              <span className="mono-badge">
                {dim}D
              </span>
            )}
            {numEvents > 0 && (
              <span className="mono-badge">
                {numEvents} EVT
              </span>
            )}
          </div>
        ) : (
          <span className="topbar-context" style={{ fontStyle: 'italic', opacity: 0.5 }}>
            No experiment loaded
          </span>
        )}
      </div>

      {/* ── Actions (right) ── */}
      <div className="topbar-right">
        {onNavigate && (
          <nav className="primary-areas" aria-label="Primary areas">
            <button className="primary-area active" onClick={() => onNavigate('observatory')}>Observatory</button>
            <button className="primary-area" onClick={() => onNavigate('substrate')}>Substrate</button>
            <button className="primary-area" onClick={() => onNavigate('evaluation')}>Evaluation</button>
            <button className="primary-area" onClick={() => onNavigate('research')}>Research</button>
          </nav>
        )}

        {/* Global Memory Selector & Follow Badge */}
        {selectedMemoryId && (
          <div className="topbar-memory-pill">
            <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
              INSPECT:
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)', fontWeight: 700, fontSize: '11px' }}>
              {selectedMemoryId}
            </span>
            {onToggleFollowMemory && (
              <button
                className={`topbar-follow-toggle ${isFollowingMemory ? 'active' : ''}`}
                onClick={onToggleFollowMemory}
                title="Toggle 'Follow This Memory' mode across all tools"
              >
                <span>{isFollowingMemory ? '★' : '☆'}</span>
                <span>{isFollowingMemory ? 'FOLLOW' : 'UNLOCKED'}</span>
              </button>
            )}
          </div>
        )}

        {/* Experiment selector — compact */}
        {experiments.length > 0 && (
          <div className="exp-selector">
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

        {onOpenJudgeMode && (
          <button
            className="topbar-btn"
            onClick={onOpenJudgeMode}
            title="Launch 2-minute Judge Mode evaluation tour (J)"
            style={{
              background: 'rgba(245, 158, 11, 0.15)',
              borderColor: 'rgba(245, 158, 11, 0.4)',
              color: '#fbbf24',
              fontWeight: 700,
            }}
          >
            ★ JUDGE MODE
          </button>
        )}

        <button
          className="topbar-btn btn-primary"
          onClick={onLaunchDemo}
          disabled={isBusy}
          title="Launch canonical demo experiment"
        >
          ▶ Run Experiment
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
          aria-label="Command palette"
        >
          <span className="kbd">⌘K</span>
        </button>

        <button
          className="topbar-btn btn-ghost"
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
