import React, { useEffect, useState } from 'react'
import type { MemoryHistory, SynapseHistory, SynapticConnection, SynapticNeuron } from '../types'
import { getMemoryHistory, getSynapseHistory } from '../api'

interface SynapticInspectorDrawerProps {
  neuron: SynapticNeuron | null
  synapse: SynapticConnection | null
  selectedConcept?: string | null
  onClose: () => void
  onSelectConcept?: (concept: string) => void
}

export const SynapticInspectorDrawer: React.FC<SynapticInspectorDrawerProps> = ({
  neuron,
  synapse,
  selectedConcept,
  onClose,
  onSelectConcept,
}) => {
  const [synapseHistory, setSynapseHistory] = useState<SynapseHistory | null>(null)
  const [memoryHistory, setMemoryHistory] = useState<MemoryHistory | null>(null)
  const [isLoadingSynapse, setIsLoadingSynapse] = useState<boolean>(false)
  const [isLoadingMemory, setIsLoadingMemory] = useState<boolean>(false)

  // Fetch synapse history when selected synapse changes
  useEffect(() => {
    if (!synapse) {
      setSynapseHistory(null)
      return
    }
    setIsLoadingSynapse(true)
    getSynapseHistory(synapse.id)
      .then((res) => setSynapseHistory(res))
      .catch(() => setSynapseHistory(null))
      .finally(() => setIsLoadingSynapse(false))
  }, [synapse?.id])

  // Fetch memory history if a concept is selected or when a neuron has dominant concepts
  const activeConcept = selectedConcept || neuron?.dominant_concepts?.[0] || null
  useEffect(() => {
    if (!activeConcept) {
      setMemoryHistory(null)
      return
    }
    setIsLoadingMemory(true)
    getMemoryHistory(activeConcept)
      .then((res) => setMemoryHistory(res))
      .catch(() => setMemoryHistory(null))
      .finally(() => setIsLoadingMemory(false))
  }, [activeConcept])

  if (!neuron && !synapse && !selectedConcept) return null

  // Helper to render SVG line graph for synapse weight over time
  const renderSynapseSparkline = () => {
    if (!synapseHistory || synapseHistory.history.length === 0) return null
    const points = synapseHistory.history
    const w = 270
    const h = 75
    const pad = 12

    const weights = points.map((p) => p.weight)
    const minW = Math.min(0, ...weights)
    const maxW = Math.max(0.01, ...weights)
    const range = Math.max(1e-4, maxW - minW)

    const zeroY = h - pad - ((0 - minW) / range) * (h - 2 * pad)

    const polyPoints = points
      .map((p, idx) => {
        const x = pad + (idx / Math.max(1, points.length - 1)) * (w - 2 * pad)
        const y = h - pad - ((p.weight - minW) / range) * (h - 2 * pad)
        return `${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ')

    return (
      <div className="synapse-sparkline-container">
        <div className="sparkline-header">
          <span className="sparkline-title">TEMPORAL WEIGHT TRAJECTORY W(t)</span>
          <span className="sparkline-range">
            [{minW.toFixed(3)}, {maxW.toFixed(3)}]
          </span>
        </div>
        <svg viewBox={`0 0 ${w} ${h}`} className="synapse-sparkline-svg">
          {/* Zero baseline */}
          <line x1={pad} y1={zeroY} x2={w - pad} y2={zeroY} stroke="rgba(255,255,255,0.15)" strokeDasharray="3 3" />

          {/* Sparkline curve */}
          <polyline fill="none" stroke="#38bdf8" strokeWidth="2" points={polyPoints} />

          {/* Dots on steps */}
          {points.map((p, idx) => {
            const x = pad + (idx / Math.max(1, points.length - 1)) * (w - 2 * pad)
            const y = h - pad - ((p.weight - minW) / range) * (h - 2 * pad)
            return (
              <circle
                key={idx}
                cx={x}
                cy={y}
                r="3"
                fill={p.weight > 0 ? '#38bdf8' : p.weight < 0 ? '#f43f5e' : '#64748b'}
              >
                <title>{`T${p.step} (${p.label}): W=${p.weight.toFixed(4)}`}</title>
              </circle>
            )
          })}
        </svg>

        <div className="sparkline-metrics-grid">
          <div className="sp-metric">
            <span className="sp-k">Initial:</span>
            <span className="sp-v">{synapseHistory.initial_weight.toFixed(3)}</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Peak |W|:</span>
            <span className="sp-v">{synapseHistory.max_weight.toFixed(3)}</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Current:</span>
            <span className="sp-v">{synapseHistory.current_weight.toFixed(3)}</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">ΔW Total:</span>
            <span className={`sp-v ${synapseHistory.total_change >= 0 ? 'cyan' : 'crimson'}`}>
              {synapseHistory.total_change >= 0 ? '+' : ''}
              {synapseHistory.total_change.toFixed(3)}
            </span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Updates:</span>
            <span className="sp-v">{synapseHistory.update_count}</span>
          </div>
        </div>
      </div>
    )
  }

  // Helper to render Memory Trail curve
  const renderMemoryTrail = () => {
    if (!memoryHistory || memoryHistory.trail.length === 0) return null
    const trail = memoryHistory.trail
    const w = 270
    const h = 75
    const pad = 12

    const maxFid = Math.max(0.1, ...trail.map((t) => t.fidelity))

    const polyPoints = trail
      .map((t, idx) => {
        const x = pad + (idx / Math.max(1, trail.length - 1)) * (w - 2 * pad)
        const y = h - pad - (t.fidelity / maxFid) * (h - 2 * pad)
        return `${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ')

    return (
      <div className="synapse-sparkline-container memory-trail-box">
        <div className="sparkline-header">
          <span className="sparkline-title">RETENTION & RECALL TRAIL</span>
          <span className="sparkline-range">Max: {maxFid.toFixed(3)}</span>
        </div>
        <svg viewBox={`0 0 ${w} ${h}`} className="synapse-sparkline-svg">
          <polyline fill="none" stroke="#a855f7" strokeWidth="2" points={polyPoints} />
          {trail.map((t, idx) => {
            const x = pad + (idx / Math.max(1, trail.length - 1)) * (w - 2 * pad)
            const y = h - pad - (t.fidelity / maxFid) * (h - 2 * pad)
            return (
              <circle key={idx} cx={x} cy={y} r="3" fill="#c084fc">
                <title>{`T${t.step}: fidelity=${t.fidelity.toFixed(3)}, strength=${t.strength.toFixed(3)}`}</title>
              </circle>
            )
          })}
        </svg>

        <div className="sparkline-metrics-grid">
          <div className="sp-metric">
            <span className="sp-k">Concept:</span>
            <span className="sp-v accent">{memoryHistory.concept}</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Target:</span>
            <span className="sp-v">{memoryHistory.value}</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Written:</span>
            <span className="sp-v">T{memoryHistory.written_step}</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Retention:</span>
            <span className="sp-v cyan">{(memoryHistory.retention_rate * 100).toFixed(1)}%</span>
          </div>
          <div className="sp-metric">
            <span className="sp-k">Fidelity:</span>
            <span className="sp-v">{memoryHistory.recall_fidelity.toFixed(3)}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <aside className="synaptic-inspector-drawer">
      <div className="syn-drawer-header">
        <div className="syn-drawer-title-group">
          <span className="syn-drawer-eyebrow">
            {synapse ? 'SYNAPSE FORENSIC INSPECTION' : neuron ? 'NEURON FORENSIC INSPECTION' : 'MEMORY TRAIL'}
          </span>
          <span className="syn-drawer-id">{synapse ? synapse.id : neuron ? neuron.label : activeConcept}</span>
        </div>
        <button className="drawer-close" onClick={onClose} title="Close Inspector" aria-label="Close">
          ×
        </button>
      </div>

      <div className="syn-drawer-body">
        {synapse && (
          <div className="syn-drawer-section">
            <div className="syn-section-title">Connectivity & Plasticity</div>

            <div className="syn-spec-row">
              <span className="spec-label">Pre-synaptic Node (Input):</span>
              <span className="spec-val accent">
                {synapse.source} (K-{synapse.source_idx})
              </span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Post-synaptic Node (Output):</span>
              <span className="spec-val accent">
                {synapse.target} (V-{synapse.target_idx})
              </span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">
                Current Weight W<sub>ij</sub>:
              </span>
              <span
                className={`spec-val font-bold ${
                  synapse.weight > 0 ? 'cyan' : synapse.weight < 0 ? 'crimson' : 'muted'
                }`}
              >
                {synapse.weight > 0 ? '+' : ''}
                {synapse.weight.toFixed(5)}
              </span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Weight Before Event:</span>
              <span className="spec-val">{synapse.weight_before.toFixed(5)}</span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Weight Change ΔW:</span>
              <span
                className={`spec-val ${
                  synapse.delta_weight > 0 ? 'emerald' : synapse.delta_weight < 0 ? 'amber' : 'muted'
                }`}
              >
                {synapse.delta_weight > 0 ? '+' : ''}
                {synapse.delta_weight.toFixed(5)}
              </span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Strength Tier:</span>
              <span className={`badge ${synapse.tier}`}>{synapse.tier.toUpperCase()}</span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Polarity:</span>
              <span className={`badge ${synapse.polarity}`}>{synapse.polarity.toUpperCase()}</span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Last Updated:</span>
              <span className="spec-val">Timestep T{synapse.last_update_timestep}</span>
            </div>

            {/* Historical Weight Evolution Sparkline */}
            {isLoadingSynapse ? (
              <div className="sparkline-loading">Loading historical synapse trace...</div>
            ) : (
              renderSynapseSparkline()
            )}
          </div>
        )}

        {neuron && !synapse && (
          <div className="syn-drawer-section">
            <div className="syn-section-title">Neuron Unit Telemetry</div>

            <div className="syn-spec-row">
              <span className="spec-label">Neuron ID:</span>
              <span className="spec-val accent">{neuron.id}</span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Neuron Role:</span>
              <span className="spec-val">
                {neuron.neuron_type === 'input_key' ? 'Pre-synaptic Key Unit' : 'Post-synaptic Value Unit'}
              </span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">
                Current Activation a<sub>i</sub>:
              </span>
              <span
                className={`spec-val font-bold ${
                  neuron.activation > 0 ? 'cyan' : neuron.activation < 0 ? 'crimson' : 'muted'
                }`}
              >
                {neuron.activation > 0 ? '+' : ''}
                {neuron.activation.toFixed(4)}
              </span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Inflow Synaptic Weight:</span>
              <span className="spec-val">{neuron.inflow_weight.toFixed(4)}</span>
            </div>

            <div className="syn-spec-row">
              <span className="spec-label">Outflow Synaptic Weight:</span>
              <span className="spec-val">{neuron.outflow_weight.toFixed(4)}</span>
            </div>

            {neuron.dominant_concepts.length > 0 && (
              <div className="syn-spec-row">
                <span className="spec-label">Associated Concepts:</span>
                <span className="spec-val accent">
                  {neuron.dominant_concepts.map((c) => (
                    <button
                      key={c}
                      type="button"
                      className="concept-chip-btn"
                      onClick={() => onSelectConcept?.(c)}
                      title={`Inspect memory trail for '${c}'`}
                    >
                      {c}
                    </button>
                  ))}
                </span>
              </div>
            )}

            {/* Memory Trail if concept associated */}
            {isLoadingMemory ? (
              <div className="sparkline-loading">Loading memory history trail...</div>
            ) : (
              renderMemoryTrail()
            )}
          </div>
        )}

        {/* Dedicated Memory Trail if opened from concept list */}
        {!neuron && !synapse && activeConcept && (
          <div className="syn-drawer-section">
            <div className="syn-section-title">Memory Trail: {activeConcept.toUpperCase()}</div>
            {isLoadingMemory ? (
              <div className="sparkline-loading">Tracing memory evolution through time...</div>
            ) : (
              renderMemoryTrail()
            )}
          </div>
        )}
      </div>
    </aside>
  )
}
