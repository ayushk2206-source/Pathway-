import React from 'react'
import type { SynapticChangeLedger } from '../types'

interface SynapticChangeLedgerViewProps {
  ledger: SynapticChangeLedger | null
}

export const SynapticChangeLedgerView: React.FC<SynapticChangeLedgerViewProps> = ({ ledger }) => {
  if (!ledger) {
    return null
  }

  const renderTag = (type: string) => {
    switch (type) {
      case 'OBSERVED':
        return <span className="claim-tag observed">OBSERVED</span>
      case 'MEASURED':
        return <span className="claim-tag measured">MEASURED</span>
      case 'INFERRED':
        return <span className="claim-tag inferred">INFERRED</span>
      case 'TEACHING_SIMPLIFICATION':
        return <span className="claim-tag simplification">TEACHING SIMPLIFICATION</span>
      default:
        return <span className="claim-tag">{type}</span>
    }
  }

  return (
    <div className="ledger-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
          <span>⚖</span> SYNAPTIC CHANGE LEDGER — {ledger.transition_name}
        </h4>
        <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontFamily: 'monospace' }}>
          Memory: {ledger.memory_id} ({ledger.concept})
        </span>
      </div>

      <div className="ledger-comparison-grid">
        <div className="ledger-box">
          <span className="ledger-box-title">State Before Transition</span>
          {Object.entries(ledger.before).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: '#94a3b8' }}>{k.replace(/_/g, ' ')}:</span>
              <span style={{ fontFamily: 'monospace', color: '#f1f5f9', fontWeight: 600 }}>{String(v)}</span>
            </div>
          ))}
        </div>

        <div className="ledger-box">
          <span className="ledger-box-title" style={{ color: '#38bdf8' }}>State After Transition</span>
          {Object.entries(ledger.after).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: '#94a3b8' }}>{k.replace(/_/g, ' ')}:</span>
              <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 600 }}>{String(v)}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.25rem' }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Empirical Scientific Claims
        </span>
        {ledger.scientific_claims.map((claim, idx) => (
          <div key={idx} className="ledger-claim-item">
            {renderTag(claim.type)}
            <span>{claim.statement}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
