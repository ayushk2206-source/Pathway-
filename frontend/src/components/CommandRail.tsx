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
    category: 'OBSERVATORY',
    items: [
      { id: 'ecosystem',    label: 'Living Ecosystem', icon: '🌐', shortcut: 'E' },
      { id: 'observatory',  label: 'Memory Field',     icon: '◉', shortcut: '1' },
      { id: 'map',          label: 'Topology Map',     icon: '⊕', shortcut: 'M' },
    ],
  },
  {
    category: 'SUBSTRATE',
    items: [
      { id: 'synaptic',     label: 'Synaptic Brain',   icon: '☊', shortcut: 'S' },
      { id: 'surgery',      label: 'Surgery & X-Ray',  icon: '⚕', shortcut: 'W' },
      { id: 'xray',         label: 'Forensic X-Ray',   icon: '⌬', shortcut: 'X' },
      { id: 'detective',    label: 'Investigation',    icon: '◎', shortcut: 'D' },
    ],
  },
  {
    category: 'INTERVENTION',
    items: [
      { id: 'counterfactual', label: 'Counterfactuals', icon: '⋈', shortcut: 'C' },
      { id: 'causal',       label: 'Causal Inference',  icon: '⊸', shortcut: 'L' },
      { id: 'collision',    label: 'Collision Lab',     icon: '⚡', shortcut: 'K' },
    ],
  },
  {
    category: 'RESEARCH',
    items: [
      { id: 'studio',       label: 'Experiment Studio', icon: '🔬', shortcut: 'P' },
      { id: 'evidence',     label: 'Evidence & Proofs', icon: '📜', shortcut: 'V' },
      { id: 'genome',       label: 'Memory Genome',     icon: '🧬', shortcut: 'G' },
      { id: 'timeline',     label: 'Lifecycle Timeline', icon: '⌘', shortcut: '4' },
      { id: 'experiments',  label: 'Experiment Archive', icon: '⊞', shortcut: '7' },
      { id: 'reports',      label: 'Research Reports',  icon: '⊟', shortcut: '8' },
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
      aria-label="Scientific Workspaces Navigation"
    >
      <div className="rail-header">
        {isExpanded && <span className="rail-header-title">INSTRUMENT MODES</span>}
        {onToggleExpand && (
          <button
            className="rail-toggle-btn"
            onClick={onToggleExpand}
            title={isExpanded ? "Collapse Rail ([)" : "Expand Rail ([)"}
            aria-label={isExpanded ? "Collapse Rail" : "Expand Rail"}
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
                  {isActive && <span className="rail-active-dot" />}
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
          <span className="rail-icon" style={{ fontSize: '9px', color: 'var(--accent)' }}>◈</span>
          <span className="rail-footer-val">d={engineDim}</span>
        </div>
      </div>
    </aside>
  )
}
