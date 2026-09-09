import React from 'react'
import type { SynapticConnection, SynapticNeuron } from '../types'

interface SynapticInspectorDrawerProps {
  neuron: SynapticNeuron | null
  synapse: SynapticConnection | null
  onClose: () => void
}

export const SynapticInspectorDrawer: React.FC<SynapticInspectorDrawerProps> = ({
  neuron,
  synapse,
  onClose,
}) => {
  if (!neuron && !synapse) return null

  return (
    <aside className="synaptic-inspector-drawer">
      <div className="syn-drawer-header">
        <div className="syn-drawer-title-group">
          <span className="syn-drawer-eyebrow">
            {synapse ? 'SYNAPSE INSPECTOR' : 'NEURON INSPECTOR'}
          </span>
          <span className="syn-drawer-id">
            {synapse ? synapse.id : neuron?.label}
          </span>
        </div>
        <button
          className="drawer-close"
          onClick={onClose}
          title="Close Inspector"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      <div className="syn-drawer-body">
        {synapse && (
          <div className="syn-drawer-section">
            <div className="syn-section-title">Synaptic Connectivity</div>

            <div className="syn-spec-row">
              <span className="spec-label">Pre-synaptic Node (Input):</span>
              <span className="spec-val accent">{synapse.source} (K-{synapse.source_idx})</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Post-synaptic Node (Output):</span>
              <span className="spec-val accent">{synapse.target} (V-{synapse.target_idx})</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Current Weight W<sub>ij</sub>:</span>
              <span className={`spec-val font-bold ${synapse.weight > 0 ? 'cyan' : synapse.weight < 0 ? 'crimson' : 'muted'}`}>
                {synapse.weight > 0 ? '+' : ''}{synapse.weight.toFixed(5)}
              </span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Weight Before Event:</span>
              <span className="spec-val">{synapse.weight_before.toFixed(5)}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Weight Change ΔW:</span>
              <span className={`spec-val ${synapse.delta_weight > 0 ? 'emerald' : synapse.delta_weight < 0 ? 'amber' : 'muted'}`}>
                {synapse.delta_weight > 0 ? '+' : ''}{synapse.delta_weight.toFixed(5)}
              </span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Strength Tier:</span>
              <span className={`badge ${synapse.tier}`}>{synapse.tier.toUpperCase()}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Polarity:</span>
              <span className={`badge ${synapse.polarity}`}>{synapse.polarity.toUpperCase()}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Plasticity Trace |ΔW|:</span>
              <span className="spec-val">{synapse.plasticity_trace.toFixed(5)}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Last Updated:</span>
              <span className="spec-val">Timestep T{synapse.last_update_timestep}</span>
            </div>

            <div className="synaptic-math-box">
              <div className="math-label">Hebbian Plasticity Rule:</div>
              <code>W<sub>ij</sub>(t+1) = (1 - λ) · W<sub>ij</sub>(t) + η · v<sub>i</sub> · k<sub>j</sub></code>
            </div>
          </div>
        )}

        {neuron && !synapse && (
          <div className="syn-drawer-section">
            <div className="syn-section-title">Neuron Unit Telemetry</div>

            <div className="spec-row">
              <span className="spec-label">Neuron ID:</span>
              <span className="spec-val accent">{neuron.id}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Neuron Role:</span>
              <span className="spec-val">{neuron.neuron_type === 'input_key' ? 'Pre-synaptic Key Unit' : 'Post-synaptic Value Unit'}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Current Activation a<sub>i</sub>:</span>
              <span className={`spec-val font-bold ${neuron.activation > 0 ? 'cyan' : neuron.activation < 0 ? 'crimson' : 'muted'}`}>
                {neuron.activation > 0 ? '+' : ''}{neuron.activation.toFixed(4)}
              </span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Inflow Synaptic Weight:</span>
              <span className="spec-val">{neuron.inflow_weight.toFixed(4)}</span>
            </div>

            <div className="spec-row">
              <span className="spec-label">Outflow Synaptic Weight:</span>
              <span className="spec-val">{neuron.outflow_weight.toFixed(4)}</span>
            </div>

            {neuron.dominant_concepts.length > 0 && (
              <div className="spec-row">
                <span className="spec-label">Associated Concepts:</span>
                <span className="spec-val accent">{neuron.dominant_concepts.join(', ')}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  )
}
