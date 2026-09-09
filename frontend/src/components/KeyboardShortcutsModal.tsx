import React from 'react'

interface KeyboardShortcutsModalProps {
  isOpen: boolean
  onClose: () => void
}

const SHORTCUT_GROUPS = [
  {
    title: 'Timeline & Playback',
    items: [
      { key: 'Space', desc: 'Play / Pause scrub playback' },
      { key: '←', desc: 'Step backward one event' },
      { key: '→', desc: 'Step forward one event' },
      { key: 'R', desc: 'Replay stored experiment sequence' },
    ],
  },
  {
    title: 'Workspace Navigation',
    items: [
      { key: '1', desc: 'Observatory · Memory Field' },
      { key: '2', desc: 'Memory Lab · Configure experiment' },
      { key: 'X', desc: 'X-Ray · Substrate analysis' },
      { key: 'D', desc: 'Detective · Hypothesis engine' },
      { key: 'G', desc: 'Genome · Lifecycle curves' },
      { key: 'A', desc: 'Agency · Autonomous research' },
      { key: 'L', desc: 'Causal Lab · Counterfactuals' },
      { key: 'M', desc: 'Memory Map · 2D projection' },
      { key: 'C', desc: 'Counterfactual · Split world' },
    ],
  },
  {
    title: 'Interface',
    items: [
      { key: '⌘ / Ctrl + K', desc: 'Open command palette' },
      { key: 'Esc', desc: 'Close inspector or modal' },
      { key: '?', desc: 'Toggle this reference dialog' },
    ],
  },
]

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-box"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 480 }}
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard shortcuts"
      >
        {/* Header */}
        <div className="shortcuts-modal-header">
          <span className="shortcuts-modal-title">Keyboard shortcuts</span>
          <button
            className="btn-ghost"
            onClick={onClose}
            aria-label="Close"
            style={{ padding: '4px 8px', fontSize: 16 }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '16px 20px', overflowY: 'auto' }}>
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.title}>
              <div className="shortcut-group-title">{group.title}</div>
              {group.items.map((s) => (
                <div key={s.key} className="shortcut-row">
                  <span className="shortcut-desc">{s.desc}</span>
                  <div className="shortcut-keys">
                    {s.key.split(' + ').map((part) => (
                      <span key={part} className="shortcut-key">{part}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{
          padding: '10px 20px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end',
          background: 'var(--bg-void)',
        }}>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
