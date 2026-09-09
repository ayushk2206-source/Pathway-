import React from 'react'

export type WorkspaceId =
  | 'observatory'
  | 'lab'
  | 'xray'
  | 'detective'
  | 'timeline'
  | 'map'
  | 'counterfactual'
  | 'experiments'
  | 'reports'
  | 'genome'
  | 'agency'
  | 'causal'

interface CommandRailProps {
  activeWorkspace: WorkspaceId
  onSelectWorkspace: (id: WorkspaceId) => void
  engineDim?: number
  apiStatus?: string
}

const NAV_ITEMS: { id: WorkspaceId; label: string; icon: string; shortcut?: string }[] = [
  { id: 'observatory',    label: 'Observe',        icon: '○', shortcut: '1' },
  { id: 'lab',            label: 'Memory Lab',     icon: '◈', shortcut: '2' },
  { id: 'xray',           label: 'X-Ray',          icon: '⌬', shortcut: 'X' },
  { id: 'detective',      label: 'Detective',      icon: '◎', shortcut: 'D' },
  { id: 'genome',         label: 'Genome',         icon: '⌇', shortcut: 'G' },
  { id: 'agency',         label: 'Agency',         icon: '⟁', shortcut: 'A' },
  { id: 'causal',         label: 'Causal Lab',     icon: '⊸', shortcut: 'L' },
  { id: 'timeline',       label: 'Timeline',       icon: '⌘', shortcut: '4' },
  { id: 'map',            label: 'Memory Map',     icon: '⊕', shortcut: 'M' },
  { id: 'counterfactual', label: 'Counterfactual', icon: '⋈', shortcut: 'C' },
  { id: 'experiments',    label: 'Experiments',    icon: '⊞', shortcut: '7' },
  { id: 'reports',        label: 'Reports',        icon: '⊟', shortcut: '8' },
]

export const CommandRail: React.FC<CommandRailProps> = ({
  activeWorkspace,
  onSelectWorkspace,
  engineDim = 128,
  apiStatus = 'ONLINE',
}) => {
  const isOnline = apiStatus.includes('200') || apiStatus.toLowerCase().includes('online')

  return (
    <aside className="command-rail">
      <nav className="rail-nav-group">
        {NAV_ITEMS.map((item) => {
          const isActive = activeWorkspace === item.id
          return (
            <button
              key={item.id}
              className={`rail-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectWorkspace(item.id)}
              title={item.label}
              aria-label={`${item.label}${item.shortcut ? ` (${item.shortcut})` : ''}`}
            >
              <span className="rail-icon">{item.icon}</span>
              <span className="rail-label">{item.label}</span>
              {item.shortcut && (
                <span className="rail-shortcut">{item.shortcut}</span>
              )}
            </button>
          )
        })}
      </nav>

      <div className="rail-footer">
        <div className="rail-footer-row">
          <span className="rail-icon" style={{ fontSize: 8 }}>●</span>
          <span
            className="rail-footer-val"
            style={{ color: isOnline ? 'var(--emerald)' : 'var(--crimson)' }}
          >
            API {isOnline ? 'online' : 'offline'}
          </span>
        </div>
        <div className="rail-footer-row">
          <span className="rail-icon" style={{ fontSize: 8 }}>◈</span>
          <span className="rail-footer-val">Engine d={engineDim}</span>
        </div>
      </div>
    </aside>
  )
}
