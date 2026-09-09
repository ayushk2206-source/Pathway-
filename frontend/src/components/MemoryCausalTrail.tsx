import React from 'react'

interface MemoryCausalTrailProps {
  onNavigate: (workspaceId: string) => void
}

export const MemoryCausalTrail: React.FC<MemoryCausalTrailProps> = ({ onNavigate }) => {
  const steps = [
    { label: 'INPUT', icon: '⤓', ws: 'lab', sub: 'Cue Vector' },
    { label: 'ACTIVITY', icon: '⚡', ws: 'observatory', sub: 'Firing Patterns' },
    { label: 'SYNAPTIC UPDATE', icon: '☊', ws: 'synaptic', sub: 'ΔW Outer Product' },
    { label: 'STATE', icon: '⌇', ws: 'genome', sub: 'Memory Fingerprint' },
    { label: 'RECALL', icon: '⌬', ws: 'xray', sub: 'v̂ Probing' },
  ]

  return (
    <div className="causal-trail-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0' }}>
          <span>⤳</span> MEMORY CAUSAL TRAIL
        </h4>
        <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
          Click an element to inspect the computational step
        </span>
      </div>

      <div className="causal-trail-sequence">
        {steps.map((s, idx) => (
          <React.Fragment key={s.label}>
            <button
              className="causal-node"
              onClick={() => onNavigate(s.ws)}
              title={`Jump to ${s.ws} workspace for ${s.label}`}
            >
              <span>{s.icon}</span>
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 700 }}>{s.label}</div>
                <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{s.sub}</div>
              </div>
            </button>
            {idx < steps.length - 1 && <span className="causal-arrow">→</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
