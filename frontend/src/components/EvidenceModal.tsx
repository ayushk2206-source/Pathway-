import React from 'react'

interface EvidenceModalProps {
  isOpen: boolean
  title: string
  details: Record<string, unknown> | null
  onClose: () => void
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  isOpen,
  title,
  details,
  onClose,
}) => {
  if (!isOpen || !details) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-box"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Evidence"
      >
        {/* Header */}
        <div className="evidence-modal-header">
          <span className="evidence-modal-title">{title}</span>
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
        <div className="evidence-modal-body">
          <div className="evidence-section-label">Computational Provenance</div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.65 }}>
            All metrics computed from vector arithmetic on state vector snapshots S_t ∈ ℝ<sup>d</sup>
            via circular convolution unbinding. No generative fabrication.
          </p>

          {/* Key-value list */}
          <div className="evidence-kv-list">
            {Object.entries(details).map(([k, v]) => (
              <div key={k} className="evidence-kv-row">
                <span className="evidence-kv-key">{k}</span>
                <span className="evidence-kv-val">
                  {v === null || v === undefined
                    ? <span style={{ color: 'var(--text-faint)', fontStyle: 'italic' }}>null</span>
                    : typeof v === 'object'
                    ? (
                      <code
                        style={{
                          fontSize: 11,
                          fontFamily: 'var(--font-mono)',
                          background: 'var(--bg-canvas)',
                          border: '1px solid var(--border-subtle)',
                          padding: '2px 6px',
                          borderRadius: 2,
                          display: 'block',
                          marginTop: 2,
                          whiteSpace: 'pre-wrap',
                          maxHeight: 120,
                          overflowY: 'auto',
                        }}
                      >
                        {JSON.stringify(v, null, 2)}
                      </code>
                    )
                    : <span>{String(v)}</span>
                  }
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px 20px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 8,
          background: 'var(--bg-void)',
        }}>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
