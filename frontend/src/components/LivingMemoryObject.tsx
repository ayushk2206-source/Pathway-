import React from 'react'

export interface MemoryObjectData {
  memoryId: string
  concept: string
  value: string
  encodedStep: number
  currentStep: number
  recallFidelity: number
  crosstalkResidual: number
  activeSynapsesCount: number
  activationWave: number[] // Normalized vector amplitudes (length 8-16)
}

interface LivingMemoryObjectProps {
  memory: MemoryObjectData
  isSelected?: boolean
  onSelect?: (memoryId: string) => void
  onOpenMicroscope?: (memory: MemoryObjectData) => void
}

export const LivingMemoryObject: React.FC<LivingMemoryObjectProps> = ({
  memory,
  isSelected = false,
  onSelect,
  onOpenMicroscope,
}) => {
  const age = Math.max(0, memory.currentStep - memory.encodedStep)
  const fidelityPct = Math.round(memory.recallFidelity * 100)

  return (
    <div
      className={`living-memory-object ${isSelected ? 'selected' : ''}`}
      style={{
        borderColor: isSelected ? '#38bdf8' : undefined,
        boxShadow: isSelected ? '0 0 20px rgba(56, 189, 248, 0.4)' : undefined,
      }}
      onClick={() => onSelect && onSelect(memory.memoryId)}
    >
      <div className="memory-object-header">
        <div>
          <div className="memory-concept-label">{memory.concept}</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.1rem' }}>
            ID: {memory.memoryId.slice(0, 8)}
          </div>
        </div>
        <div className="memory-value-pill">&rarr; {memory.value}</div>
      </div>

      {/* Activation Waveform (Fingerprint Signature) */}
      <div className="memory-spark-wave" title="Normalized Synaptic Activation Vector">
        {memory.activationWave.map((amp, idx) => {
          const h = Math.max(4, Math.round(amp * 28))
          const color = amp > 0.7 ? '#38bdf8' : amp > 0.4 ? '#34d399' : '#64748b'
          return (
            <div
              key={idx}
              className="memory-wave-bar"
              style={{
                height: `${h}px`,
                backgroundColor: color,
              }}
            />
          )
        })}
      </div>

      {/* Real Metric Readouts */}
      <div className="memory-metrics-strip">
        <div className="memory-metric-cell">
          <span className="metric-cell-label">RECALL</span>
          <span
            className="metric-cell-val"
            style={{
              color: fidelityPct >= 80 ? '#34d399' : fidelityPct >= 50 ? '#fbbf24' : '#f87171',
            }}
          >
            {fidelityPct}%
          </span>
        </div>

        <div className="memory-metric-cell">
          <span className="metric-cell-label">CROSSTALK</span>
          <span className="metric-cell-val">
            {memory.crosstalkResidual.toFixed(3)}
          </span>
        </div>

        <div className="memory-metric-cell">
          <span className="metric-cell-label">AGE</span>
          <span className="metric-cell-val">{age} steps</span>
        </div>
      </div>

      {onOpenMicroscope && (
        <button
          className="memory-microscope-btn"
          onClick={(e) => {
            e.stopPropagation()
            onOpenMicroscope(memory)
          }}
        >
          <span>⌬</span>
          <span>EXAMINE IN MICROSCOPE</span>
        </button>
      )}
    </div>
  )
}

export default LivingMemoryObject
