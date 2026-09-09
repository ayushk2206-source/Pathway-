import React, { useState } from 'react'
import type { ForensicsEvidenceItem } from '../types'

interface EvidenceBoardProps {
  evidence: ForensicsEvidenceItem[]
  collectedIds: string[]
  onToggleCollect: (evidenceId: string) => void
}

export const EvidenceBoard: React.FC<EvidenceBoardProps> = ({
  evidence,
  collectedIds,
  onToggleCollect,
}) => {
  const [inspectedId, setInspectedId] = useState<string | null>(null)

  return (
    <div className="evidence-board-panel">
      <div className="panel-title-bar">
        <h3>
          <span>📌</span> Evidence Board ({collectedIds.length}/{evidence.length} Collected)
        </h3>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Pin critical clues to build your case verdict
        </span>
      </div>

      <div className="evidence-items-container">
        {evidence.map((item) => {
          const isCollected = collectedIds.includes(item.evidence_id)
          return (
            <div
              key={item.evidence_id}
              className={`evidence-card ${item.is_critical ? 'critical' : ''}`}
              style={{
                borderColor: isCollected ? '#38bdf8' : undefined,
                background: isCollected ? 'rgba(56, 189, 248, 0.08)' : undefined,
              }}
            >
              <div className="evidence-card-header">
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span className="evidence-id-badge">{item.evidence_id}</span>
                  <span className="evidence-category-badge">{item.category}</span>
                  {item.is_critical && (
                    <span
                      style={{
                        fontSize: '0.68rem',
                        background: 'rgba(245, 158, 11, 0.2)',
                        color: '#fbbf24',
                        padding: '0.1rem 0.35rem',
                        borderRadius: '3px',
                        fontWeight: 700,
                      }}
                    >
                      CRITICAL
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => setInspectedId(inspectedId === item.evidence_id ? null : item.evidence_id)}
                    style={{
                      background: 'none',
                      border: '1px solid rgba(148, 163, 184, 0.3)',
                      color: '#94a3b8',
                      borderRadius: '4px',
                      padding: '0.2rem 0.5rem',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                    }}
                  >
                    {inspectedId === item.evidence_id ? 'Hide Raw' : 'Inspect Raw'}
                  </button>
                  <button
                    onClick={() => onToggleCollect(item.evidence_id)}
                    style={{
                      background: isCollected ? '#0284c7' : 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid #38bdf8',
                      color: '#fff',
                      borderRadius: '4px',
                      padding: '0.2rem 0.6rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {isCollected ? '✓ Pinned' : '+ Pin to Verdict'}
                  </button>
                </div>
              </div>

              <div className="evidence-title">{item.title}</div>
              <div className="evidence-description">{item.description}</div>

              {inspectedId === item.evidence_id && (
                <div className="evidence-data-snippet">
                  <div style={{ color: '#94a3b8', marginBottom: '0.25rem' }}>
                    // Raw Computation Data (Timestep {item.timestep})
                  </div>
                  <pre style={{ margin: 0 }}>{JSON.stringify(item.data_point, null, 2)}</pre>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
