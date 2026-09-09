import React from 'react'

interface ExplanationBuilderProps {
  chain: string[]
  onChangeChain: (newChain: string[]) => void
}

const AVAILABLE_CHAIN_BLOCKS = [
  { id: 'MEMORY_WRITE', label: '1. Memory Write', icon: '📝' },
  { id: 'SYNAPTIC_UPDATE', label: '2. Synaptic Co-Update', icon: '⚡' },
  { id: 'SHARED_COORDINATES', label: '3. Shared Coordinates', icon: '🔗' },
  { id: 'TEMPORAL_DECAY', label: '3b. Passive Decay', icon: '⏳' },
  { id: 'SYNAPSE_ABLATION', label: '3c. Synapse Ablation', icon: '✂️' },
  { id: 'CROSSTALK_NOISE', label: '4. Crosstalk Noise', icon: '💥' },
  { id: 'RECALL_DROP', label: '5. Readout Divergence', icon: '📉' },
  { id: 'COUNTERFACTUAL_PROTECTION', label: 'Alt. Causal Protection', icon: '🛡️' },
]

export const ExplanationBuilder: React.FC<ExplanationBuilderProps> = ({
  chain,
  onChangeChain,
}) => {
  const addBlock = (id: string) => {
    if (!chain.includes(id)) {
      onChangeChain([...chain, id])
    }
  }

  const removeBlock = (index: number) => {
    const updated = [...chain]
    updated.splice(index, 1)
    onChangeChain(updated)
  }

  const clearChain = () => {
    onChangeChain([])
  }

  const autoFillPreset = (presetType: 'collision' | 'ablation' | 'decay') => {
    if (presetType === 'collision') {
      onChangeChain(['MEMORY_WRITE', 'SYNAPTIC_UPDATE', 'SHARED_COORDINATES', 'CROSSTALK_NOISE', 'RECALL_DROP'])
    } else if (presetType === 'ablation') {
      onChangeChain(['MEMORY_WRITE', 'SYNAPTIC_UPDATE', 'SYNAPSE_ABLATION', 'RECALL_DROP'])
    } else {
      onChangeChain(['MEMORY_WRITE', 'SYNAPTIC_UPDATE', 'TEMPORAL_DECAY', 'RECALL_DROP'])
    }
  }

  return (
    <div className="explanation-builder-panel">
      <div className="panel-title-bar">
        <h3>
          <span>🧩</span> Causal Explanation Chain Builder
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => autoFillPreset('collision')}
            style={{
              background: 'rgba(51, 65, 85, 0.4)',
              border: '1px solid rgba(148, 163, 184, 0.2)',
              color: '#cbd5e1',
              borderRadius: '4px',
              padding: '0.2rem 0.5rem',
              fontSize: '0.72rem',
              cursor: 'pointer',
            }}
          >
            Preset: Collision
          </button>
          <button
            onClick={() => autoFillPreset('ablation')}
            style={{
              background: 'rgba(51, 65, 85, 0.4)',
              border: '1px solid rgba(148, 163, 184, 0.2)',
              color: '#cbd5e1',
              borderRadius: '4px',
              padding: '0.2rem 0.5rem',
              fontSize: '0.72rem',
              cursor: 'pointer',
            }}
          >
            Preset: Ablation
          </button>
          <button
            onClick={clearChain}
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              borderRadius: '4px',
              padding: '0.2rem 0.5rem',
              fontSize: '0.72rem',
              cursor: 'pointer',
            }}
          >
            Reset
          </button>
        </div>
      </div>

      <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
        Assemble the causal narrative explaining how synaptic mechanisms produced the observed outcome:
      </div>

      {/* Assembled Chain Flow */}
      <div className="chain-steps-flow">
        {chain.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: '0.85rem', fontStyle: 'italic', padding: '0.5rem 0' }}>
            No steps in causal chain yet. Click blocks below to assemble your mechanistic theory.
          </div>
        ) : (
          chain.map((blockId, idx) => {
            const blockDef = AVAILABLE_CHAIN_BLOCKS.find((b) => b.id === blockId)
            return (
              <React.Fragment key={`${blockId}-${idx}`}>
                <div className="chain-node">
                  <span>{blockDef?.icon || '🔹'}</span>
                  <span>{blockDef?.label || blockId}</span>
                  <button
                    onClick={() => removeBlock(idx)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#94a3b8',
                      cursor: 'pointer',
                      padding: '0 0.2rem',
                      fontWeight: 'bold',
                    }}
                  >
                    ×
                  </button>
                </div>
                {idx < chain.length - 1 && <span className="chain-arrow">➔</span>}
              </React.Fragment>
            )
          })
        )}
      </div>

      {/* Available Blocks Pool */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
        {AVAILABLE_CHAIN_BLOCKS.map((b) => {
          const isAdded = chain.includes(b.id)
          return (
            <button
              key={b.id}
              onClick={() => addBlock(b.id)}
              disabled={isAdded}
              style={{
                background: isAdded ? 'rgba(51, 65, 85, 0.2)' : 'rgba(30, 41, 59, 0.8)',
                border: '1px solid',
                borderColor: isAdded ? 'rgba(148, 163, 184, 0.1)' : 'rgba(56, 189, 248, 0.3)',
                color: isAdded ? '#64748b' : '#e2e8f0',
                borderRadius: '6px',
                padding: '0.35rem 0.65rem',
                fontSize: '0.78rem',
                cursor: isAdded ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <span>{b.icon}</span>
              <span>{b.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
