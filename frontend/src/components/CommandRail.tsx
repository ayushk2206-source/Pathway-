import React from 'react'

export type WorkspaceId =
  | 'ecosystem'
  | 'synaptic'
  | 'surgery'
  | 'collision'
  | 'detective'
  | 'research'
  | 'observatory'
  | 'lab'
  | 'xray'
  | 'timeline'
  | 'map'
  | 'counterfactual'
  | 'experiments'
  | 'reports'
  | 'genome'
  | 'agency'
  | 'causal'
  | 'studio'
  | 'evidence'
  | 'judge'

interface CommandRailProps {
  activeWorkspace: WorkspaceId
  onSelectWorkspace: (id: WorkspaceId) => void
  engineDim?: number
  apiStatus?: string
  isExpanded?: boolean
  onToggleExpand?: () => void
}

interface NavCategory {
  category: string
  items: { id: WorkspaceId; label: string; icon: string; shortcut?: string }[]
}

const NAV_GROUPS: NavCategory[] = [
  {
    category: 'EVALUATION',
    items: [
      { id: 'judge',        label: 'Judge Mode (2-Min)', icon: '★', shortcut: 'J' },
    ],
  },
  {
    category: 'EXPLORE',
    items: [
      { id: 'ecosystem',    label: 'Ecosystem Hub',  icon: '🌐', shortcut: 'E' },
      { id: 'observatory',  label: 'Observe',        icon: '○', shortcut: '1' },
      { id: 'map',          label: 'Memory Map',     icon: '⊕', shortcut: 'M' },
    ],
  },
  {
    category: 'EXPERIMENT',
    items: [
      { id: 'studio',       label: 'Experiment Studio', icon: '🔬', shortcut: 'P' },
      { id: 'collision',    label: 'Collision Lab',     icon: '⚡', shortcut: 'K' },
      { id: 'lab',          label: 'Memory Lab',        icon: '◈', shortcut: '2' },
      { id: 'experiments',  label: 'Archive',           icon: '⊞', shortcut: '7' },
    ],
  },
  {
    category: 'INSPECT',
    items: [
      { id: 'synaptic',     label: 'Synaptic Brain', icon: '☊', shortcut: 'S' },
      { id: 'surgery',      label: 'Surgery & X-Ray', icon: '⚕', shortcut: 'W' },
      { id: 'xray',         label: 'X-Ray',          icon: '⌬', shortcut: 'X' },
      { id: 'detective',    label: 'Detective',      icon: '◎', shortcut: 'D' },
    ],
  },
  {
    category: 'INTERVENE',
    items: [
      { id: 'counterfactual', label: 'Counterfactual', icon: '⋈', shortcut: 'C' },
      { id: 'causal',       label: 'Causal Lab',     icon: '⊸', shortcut: 'L' },
    ],
  },
  {
    category: 'COMPARE',
    items: [
      { id: 'evidence',     label: 'Scientific Evidence', icon: '📜', shortcut: 'V' },
      { id: 'genome',       label: 'Genome',         icon: '⌇', shortcut: 'G' },
      { id: 'research',     label: 'Research Lab',   icon: '🧪', shortcut: 'R' },
      { id: 'reports',      label: 'Reports',        icon: '⊟', shortcut: '8' },
    ],
  },
  {
    category: 'HISTORY',
    items: [
      { id: 'timeline',     label: 'Timeline',       icon: '⌘', shortcut: '4' },
      { id: 'agency',       label: 'Agency',         icon: '⟁', shortcut: 'A' },
    ],
  },
]


export const CommandRail: React.FC<CommandRailProps> = ({
  activeWorkspace,
  onSelectWorkspace,
  engineDim = 128,
  apiStatus = 'ONLINE',
  isExpanded = false,
  onToggleExpand,
}) => {
  const isOnline = apiStatus.includes('200') || apiStatus.toLowerCase().includes('online')

  return (
    <aside
      className={`command-rail ${isExpanded ? 'expanded' : 'collapsed'}`}
      aria-label="Workspaces Navigation"
    >
      <div className="rail-header">
        {isExpanded && <span className="rail-header-title">Workspaces</span>}
        {onToggleExpand && (
          <button
            className="rail-toggle-btn"
            onClick={onToggleExpand}
            title={isExpanded ? "Collapse sidebar ([)" : "Expand sidebar ([)"}
            aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
          >
            {isExpanded ? '◀' : '▶'}
          </button>
        )}
      </div>

      <nav className="rail-nav-group">
        {NAV_GROUPS.map((group) => (
          <div key={group.category} className="rail-category-section">
            <div className="rail-section-label">
              {group.category}
            </div>
            {group.items.map((item) => {
              const isActive = activeWorkspace === item.id
              return (
                <button
                  key={item.id}
                  className={`rail-item ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectWorkspace(item.id)}
                  title={`${item.label}${item.shortcut ? ` (${item.shortcut})` : ''}`}
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
          </div>
        ))}
      </nav>

      <div className="rail-footer">
        <div className="rail-footer-row">
          <span className="status-led live" style={{ background: isOnline ? 'var(--emerald)' : 'var(--crimson)' }} />
          <span className="rail-footer-val">
            {isOnline ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
        <div className="rail-footer-row">
          <span className="rail-icon" style={{ fontSize: 9 }}>◈</span>
          <span className="rail-footer-val">d={engineDim}</span>
        </div>
      </div>
    </aside>
  )
}
