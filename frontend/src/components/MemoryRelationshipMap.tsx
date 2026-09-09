import React from 'react'
import type { MemoryRelationship } from '../types'

interface MemoryRelationshipMapProps {
  relationships: MemoryRelationship[]
  onSelectMemory?: (id: string) => void
}

export const MemoryRelationshipMap: React.FC<MemoryRelationshipMapProps> = ({
  relationships,
  onSelectMemory,
}) => {
  if (!relationships || relationships.length === 0) {
    return (
      <div className="ledger-card" style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
        No measurable synaptic relationships recorded yet.
      </div>
    )
  }

  return (
    <div className="ledger-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
          <span>🌐</span> EVIDENCE-BASED RELATIONSHIP GRAPH
        </h4>
        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
          Measurable linear algebra correlations only
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        {relationships.map((rel, idx) => (
          <div key={idx} className="rel-item">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                onClick={() => onSelectMemory && onSelectMemory(rel.source_id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#38bdf8',
                  fontWeight: 700,
                  cursor: 'pointer',
                  padding: 0,
                  fontSize: '0.85rem',
                }}
              >
                {rel.source_concept} ({rel.source_id})
              </button>
              <span style={{ color: '#64748b' }}>⇄</span>
              <button
                onClick={() => onSelectMemory && onSelectMemory(rel.target_id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#e2e8f0',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                  fontSize: '0.85rem',
                }}
              >
                {rel.target_concept} ({rel.target_id})
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span className={`rel-tag ${rel.relationship_type}`}>
                {rel.relationship_type.replace(/_/g, ' ')}
              </span>
              <span style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: '#94a3b8' }}>
                weight={rel.weight.toFixed(2)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
