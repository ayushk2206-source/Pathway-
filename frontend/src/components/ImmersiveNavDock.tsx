import React, { useEffect } from 'react'
import type { WorkspaceId } from './CommandRail'

interface ImmersiveNavDockProps {
  activeWorkspace: WorkspaceId
  onSelectWorkspace: (id: WorkspaceId) => void
  onOpenPortal?: () => void
  onOpenJudgeMode?: () => void
}

interface NavDestination {
  id: WorkspaceId
  label: string
  icon: string
  shortcut: string
}

const PRIMARY_DESTINATIONS: NavDestination[] = [
  { id: 'synaptic', label: 'MEMORY', icon: '☊', shortcut: '1' },
  { id: 'observatory', label: 'OBSERVATORY', icon: '○', shortcut: '2' },
  { id: 'studio', label: 'EXPERIMENTS', icon: '🔬', shortcut: '3' },
  { id: 'surgery', label: 'SURGERY', icon: '⚕', shortcut: '4' },
  { id: 'collision', label: 'COLLISIONS', icon: '⚡', shortcut: '5' },
  { id: 'counterfactual', label: 'COUNTERFACTUALS', icon: '⋈', shortcut: '6' },
  { id: 'genome', label: 'GENOME', icon: '⌇', shortcut: '7' },
  { id: 'evidence', label: 'RESEARCH', icon: '📜', shortcut: '8' },
]

export const ImmersiveNavDock: React.FC<ImmersiveNavDockProps> = ({
  activeWorkspace,
  onSelectWorkspace,
  onOpenPortal,
  onOpenJudgeMode,
}) => {
  // Global keyboard listener for hotkeys 1-8 and J for Judge Mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea') return

      if (e.key === 'j' || e.key === 'J') {
        if (onOpenJudgeMode) onOpenJudgeMode()
        return
      }

      const found = PRIMARY_DESTINATIONS.find((d) => d.shortcut === e.key)
      if (found) {
        onSelectWorkspace(found.id)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onSelectWorkspace, onOpenJudgeMode])

  return (
    <nav className="immersive-nav-dock" aria-label="Scientific Instrument Primary Navigation">
      {onOpenJudgeMode && (
        <>
          <button
            className="dock-item-btn"
            onClick={onOpenJudgeMode}
            title="Launch 2-Minute Judge Mode Evaluation Tour (J)"
            style={{
              color: '#fbbf24',
              background: 'rgba(245, 158, 11, 0.15)',
              borderColor: 'rgba(245, 158, 11, 0.4)',
              fontWeight: 700,
            }}
          >
            <span>★</span>
            <span>JUDGE TOUR</span>
            <span className="dock-item-shortcut" style={{ color: '#fbbf24' }}>J</span>
          </button>
          <div className="dock-separator" />
        </>
      )}

      {onOpenPortal && (
        <>
          <button
            className="dock-item-btn"
            onClick={onOpenPortal}
            title="Return to Neural Portal / Universe Screen"
            style={{ color: '#38bdf8' }}
          >
            <span>🌌</span>
            <span>UNIVERSE</span>
          </button>
          <div className="dock-separator" />
        </>
      )}

      {PRIMARY_DESTINATIONS.map((dest) => {
        const isActive =
          activeWorkspace === dest.id ||
          (dest.id === 'synaptic' && activeWorkspace === 'map')

        return (
          <button
            key={dest.id}
            className={`dock-item-btn ${isActive ? 'active' : ''}`}
            onClick={() => onSelectWorkspace(dest.id)}
            aria-current={isActive ? 'page' : undefined}
          >
            <span style={{ fontSize: '1rem' }}>{dest.icon}</span>
            <span>{dest.label}</span>
            <span className="dock-item-shortcut">{dest.shortcut}</span>
          </button>
        )
      })}
    </nav>
  )
}

export default ImmersiveNavDock
