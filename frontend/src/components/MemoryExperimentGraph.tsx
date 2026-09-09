import React from 'react'

interface MemoryExperimentGraphProps {
  activeStage?: string // "INPUT" | "MEMORY" | "SYNAPTIC_WRITE" | "STATE_UPDATE" | "RECALL" | "MEASUREMENT"
}

export const MemoryExperimentGraph: React.FC<MemoryExperimentGraphProps> = ({
  activeStage = 'STATE_UPDATE',
}) => {
  const isInputActive = activeStage === 'INPUT'
  const isMemoryActive = activeStage === 'ACTIVITY' || activeStage === 'SYNAPTIC_WRITE'
  const isStateActive = activeStage === 'STATE_UPDATE'
  const isRecallActive = activeStage === 'RECALL' || activeStage === 'MEASUREMENT'

  return (
    <div className="studio-causal-graph">
      {/* Node 1: Input */}
      <div className={`studio-graph-node ${isInputActive ? 'active' : ''}`}>
        <div className="studio-node-bubble">
          <span>⌨</span>
        </div>
        <span className="studio-node-label">1. INPUT CUE</span>
      </div>

      <div className={`studio-graph-connector ${isMemoryActive || isStateActive || isRecallActive ? 'active' : ''}`} />

      {/* Node 2: Memory Activity */}
      <div className={`studio-graph-node ${isMemoryActive ? 'active' : ''}`}>
        <div className="studio-node-bubble">
          <span>💡</span>
        </div>
        <span className="studio-node-label">2. ACTIVITY (v ⊗ k)</span>
      </div>

      <div className={`studio-graph-connector ${isStateActive || isRecallActive ? 'active' : ''}`} />

      {/* Node 3: Synaptic State */}
      <div className={`studio-graph-node ${isStateActive ? 'active' : ''}`}>
        <div className="studio-node-bubble">
          <span>⚡</span>
        </div>
        <span className="studio-node-label">3. SYNAPTIC MATRIX (W)</span>
      </div>

      <div className={`studio-graph-connector ${isRecallActive ? 'active' : ''}`} />

      {/* Node 4: Recall */}
      <div className={`studio-graph-node ${isRecallActive ? 'active' : ''}`}>
        <div className="studio-node-bubble">
          <span>🎯</span>
        </div>
        <span className="studio-node-label">4. RECALL READOUT (v̂)</span>
      </div>
    </div>
  )
}
