import React, { useState } from 'react'
import type { SynapticNetworkState } from '../types'
import { SynapticNetworkCanvas } from './SynapticNetworkCanvas'

interface SynchronizedNetworkComparisonProps {
  stepIdx: number
  divergenceStep: number | null
  originalNetwork: SynapticNetworkState | null
  counterfactualNetwork: SynapticNetworkState | null
  matrixFrobeniusDelta: number
  changedSynapsesCount: number
  selectedSynapseId: string | null
  onSelectSynapse: (synapseId: string | null) => void
}

export const SynchronizedNetworkComparison: React.FC<SynchronizedNetworkComparisonProps> = ({
  stepIdx,
  divergenceStep,
  originalNetwork,
  counterfactualNetwork,
  matrixFrobeniusDelta,
  changedSynapsesCount,
  selectedSynapseId,
  onSelectSynapse,
}) => {
  const [layoutMode, setLayoutMode] = useState<'bipartite' | 'matrix'>('bipartite')

  if (!originalNetwork || !counterfactualNetwork) {
    return (
      <div className="sync-network-empty">
        <span>Awaiting synchronized network states for Timestep T{stepIdx}...</span>
      </div>
    )
  }

  const isDiverged = divergenceStep !== null && stepIdx >= divergenceStep

  return (
    <div className="synchronized-network-comparison-card">
      <div className="sync-header">
        <div className="sync-title-group">
          <span className="sync-glyph">⚡</span>
          <span className="sync-title">SYNCHRONIZED NETWORK COMPARISON (TIMESTEP T={stepIdx})</span>
          <span className={`sync-status-badge ${isDiverged ? 'diverged' : 'identical'}`}>
            {isDiverged ? `DIVERGED (${changedSynapsesCount} SYNAPSES ALTERED)` : 'IDENTICAL WIRING'}
          </span>
        </div>
        <div className="sync-controls">
          <div className="metric-chip">
            <span className="lbl">‖ΔW‖_F:</span>
            <span className="val">{matrixFrobeniusDelta.toFixed(4)}</span>
          </div>
          <div className="layout-toggle">
            <button
              className={`toggle-btn ${layoutMode === 'bipartite' ? 'active' : ''}`}
              onClick={() => setLayoutMode('bipartite')}
            >
              BIPARTITE
            </button>
            <button
              className={`toggle-btn ${layoutMode === 'matrix' ? 'active' : ''}`}
              onClick={() => setLayoutMode('matrix')}
            >
              MATRIX
            </button>
          </div>
        </div>
      </div>

      <div className="sync-canvases-grid">
        {/* Left: Original Reality */}
        <div className="network-column original-col">
          <div className="col-tag orig-tag">
            <span>ORIGINAL TRAJECTORY</span>
            <span className="sub-metric">Norm: {originalNetwork.matrix_norm.toFixed(3)}</span>
          </div>
          <div className="canvas-wrapper">
            <SynapticNetworkCanvas
              dimension={originalNetwork.dimension}
              neurons={originalNetwork.neurons}
              synapses={originalNetwork.synapses}
              lastPathway={originalNetwork.last_pathway}
              selectedNeuronId={null}
              selectedSynapseId={selectedSynapseId}
              onSelectNeuron={() => {}}
              onSelectSynapse={onSelectSynapse}
              layoutMode={layoutMode}
              showLabels={true}
              showAllSynapses={false}
            />
          </div>
        </div>

        {/* Right: Counterfactual Branch */}
        <div className="network-column counterfactual-col">
          <div className="col-tag cf-tag">
            <span>WHAT IF? (COUNTERFACTUAL)</span>
            <span className="sub-metric">Norm: {counterfactualNetwork.matrix_norm.toFixed(3)}</span>
          </div>
          <div className="canvas-wrapper">
            <SynapticNetworkCanvas
              dimension={counterfactualNetwork.dimension}
              neurons={counterfactualNetwork.neurons}
              synapses={counterfactualNetwork.synapses}
              lastPathway={counterfactualNetwork.last_pathway}
              selectedNeuronId={null}
              selectedSynapseId={selectedSynapseId}
              onSelectNeuron={() => {}}
              onSelectSynapse={onSelectSynapse}
              layoutMode={layoutMode}
              showLabels={true}
              showAllSynapses={false}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
