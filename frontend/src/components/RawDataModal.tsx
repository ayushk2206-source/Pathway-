import React from 'react'

interface RawDataModalProps {
  isOpen: boolean
  title: string
  data: Record<string, unknown> | null
  onClose: () => void
  onExportJson?: () => void
}

export const RawDataModal: React.FC<RawDataModalProps> = ({
  isOpen,
  title,
  data,
  onClose,
  onExportJson,
}) => {
  if (!isOpen || !data) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, color: '#38bdf8', fontSize: '1.1rem' }}>{title}</h3>
          <button className="scanner-btn" onClick={onClose}>✕ Close</button>
        </div>

        <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>
          Research Mode: Direct inspection of underlying numerical arrays, coordinate partitions, and linear algebraic measurements.
        </p>

        <div className="raw-json-viewer">
          {JSON.stringify(data, null, 2)}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          {onExportJson && (
            <button className="scanner-btn primary" onClick={onExportJson}>
              💾 Download JSON
            </button>
          )}
          <button className="scanner-btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
