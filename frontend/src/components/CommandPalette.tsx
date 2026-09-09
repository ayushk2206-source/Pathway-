import React, { useEffect, useState } from 'react'
import type { WorkspaceId } from './CommandRail'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onNavigate: (workspace: WorkspaceId) => void
  onLaunchDemo: () => void
  onReplay: () => void
  onSelectMemory: (id: string) => void
  availableMemories: string[]
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onLaunchDemo,
  onReplay,
  onSelectMemory,
  availableMemories,
}) => {
  const [query, setQuery] = useState('')

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
      setQuery('')
    }
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const actions = [
    { title: 'Launch demo experiment', desc: '128D canonical demonstration', shortcut: 'D', category: 'action', run: () => onLaunchDemo() },
    { title: 'Replay timeline', desc: 'Re-execute current experiment sequence', shortcut: 'R', category: 'action', run: () => onReplay() },
    { title: 'Synaptic Brain', desc: 'Live Hebbian synaptic matrix and time machine', shortcut: 'S', category: 'workspace', run: () => onNavigate('synaptic') },
    { title: 'Surgery & X-Ray', desc: 'Causal synaptic surgery and memory X-ray', shortcut: 'W', category: 'workspace', run: () => onNavigate('surgery') },
    { title: 'Collision Lab', desc: 'Memory collision and synaptic interference lab', shortcut: 'K', category: 'workspace', run: () => onNavigate('collision') },
    { title: 'Observe · Memory Field', desc: 'Living memory visualization', shortcut: '1', category: 'workspace', run: () => onNavigate('observatory') },
    { title: 'Memory Lab', desc: 'Configure and run experiments', shortcut: '2', category: 'workspace', run: () => onNavigate('lab') },
    { title: 'X-Ray · Substrate Analysis', desc: 'Weight matrix heatmaps and activation', shortcut: 'X', category: 'workspace', run: () => onNavigate('xray') },
    { title: 'Memory Detective', desc: 'Hypothesis engine and mystery cases', shortcut: 'D', category: 'workspace', run: () => onNavigate('detective') },
    { title: 'Research Lab', desc: 'Custom experiments and comparative diffs', shortcut: 'R', category: 'workspace', run: () => onNavigate('research') },
    { title: 'Memory Genome', desc: 'Lifecycle genetics and decay curves', shortcut: 'G', category: 'workspace', run: () => onNavigate('genome') },
    { title: 'Research Agency', desc: 'Autonomous multi-agent investigation', shortcut: 'A', category: 'workspace', run: () => onNavigate('agency') },
    { title: 'Causal Memory Lab', desc: 'Counterfactual interventions and cascades', shortcut: 'L', category: 'workspace', run: () => onNavigate('causal') },
    { title: 'Timeline Engine', desc: 'Step-by-step scrub and playback', shortcut: '4', category: 'workspace', run: () => onNavigate('timeline') },
    { title: 'Memory Map', desc: '2D/3D semantic projection', shortcut: 'M', category: 'workspace', run: () => onNavigate('map') },
    { title: 'Counterfactual World', desc: 'Side-by-side divergence comparison', shortcut: 'C', category: 'workspace', run: () => onNavigate('counterfactual') },
    { title: 'Experiments', desc: 'Benchmark archive and compare', shortcut: '7', category: 'workspace', run: () => onNavigate('experiments') },
    { title: 'Reports', desc: 'Scientific investigation reports', shortcut: '8', category: 'workspace', run: () => onNavigate('reports') },
    ...availableMemories.map((m) => ({
      title: `Excavate: ${m}`,
      desc: 'Open forensic inspector',
      shortcut: '',
      category: 'memory',
      run: () => onSelectMemory(m),
    })),
  ]

  const filtered = actions.filter(
    (a) =>
      !query ||
      a.title.toLowerCase().includes(query.toLowerCase()) ||
      a.desc.toLowerCase().includes(query.toLowerCase()) ||
      a.category.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="command-palette-box"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
      >
        <div className="palette-input-wrapper">
          <span className="palette-search-icon">⌕</span>
          <input
            type="text"
            className="palette-search-input"
            placeholder="Search commands, workspaces, memories…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            aria-label="Search commands"
          />
          <span className="palette-esc">ESC</span>
        </div>

        <div className="palette-results-list" role="listbox">
          {filtered.length ? (
            filtered.map((item, idx) => (
              <div
                key={idx}
                className="palette-item"
                role="option"
                onClick={() => {
                  item.run()
                  onClose()
                }}
              >
                <div className="palette-item-body">
                  <div className="palette-item-title">{item.title}</div>
                  <div className="palette-item-desc">{item.desc}</div>
                </div>
                {item.shortcut && (
                  <span className="palette-item-shortcut">{item.shortcut}</span>
                )}
              </div>
            ))
          ) : (
            <div className="palette-empty">No matching commands found.</div>
          )}
        </div>
      </div>
    </div>
  )
}
