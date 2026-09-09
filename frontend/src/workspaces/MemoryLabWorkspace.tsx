import React, { useState } from 'react'
import type { MechanismInfo, RunRequest } from '../types'

interface MemoryLabWorkspaceProps {
  mechanisms: Record<string, MechanismInfo>
  onRunExperiment: (req: RunRequest) => Promise<void>
  isBusy: boolean
}

const MECHANISM_DESCRIPTIONS: Record<string, string> = {
  baseline: 'Naive linear superposition with circular convolution binding. Exact single-pair recall, honest superposition interference.',
  leaky: 'Leaky recurrent update with exponential fading factor (λ). Simulates biological memory decay and finite temporal horizons.',
  competitive: 'Non-linear k-WTA sparsification preserving top-k active dimensions. Suppresses cross-talk background noise.',
  hebbian: 'Associative outer-product matrix representation. Captures multi-dimensional relational key-value correlations.',
  interference: 'Active error-driven erasure that suppresses competing previous bindings before writing new associations.',
}

export const MemoryLabWorkspace: React.FC<MemoryLabWorkspaceProps> = ({
  mechanisms,
  onRunExperiment,
  isBusy,
}) => {
  const [seed, setSeed] = useState(777)
  const [mechanism, setMechanism] = useState('interference')
  const [stateDim, setStateDim] = useState(128)
  const [decay, setDecay] = useState(0.2)
  const [interferenceStrength, setInterferenceStrength] = useState(0.6)
  const [sparsity, setSparsity] = useState(0.15)
  const [updateStrength, setUpdateStrength] = useState(0.9)
  const [nObjects, setNObjects] = useState(6)
  const [nSymbols, setNSymbols] = useState(4)
  const [nConflicts, setNConflicts] = useState(3)
  const [objectSim, setObjectSim] = useState(0.4)
  const [cycles, setCycles] = useState(2)
  const [order, setOrder] = useState<'structured' | 'interleaved' | 'randomized'>('interleaved')

  const [executingStage, setExecutingStage] = useState<string | null>(null)

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isBusy) return

    setExecutingStage('INITIALIZING SUBSTRATE')
    setTimeout(() => setExecutingStage('ENCODING HIGH-DIMENSIONAL CUES'), 250)
    setTimeout(() => setExecutingStage('UPDATING VECTOR SUPERPOSITION'), 500)
    setTimeout(() => setExecutingStage('ANALYZING TOPOLOGICAL MANIFOLD'), 750)

    const req: RunRequest = {
      seed,
      mechanism,
      params: {
        state_dim: stateDim,
        update_strength: updateStrength,
        memory_strength: 1.0,
        decay,
        interference_strength: interferenceStrength,
        sparsity,
        normalize_state: false,
        input_noise: 0.0,
      },
      task: {
        d: stateDim,
        n_objects: nObjects,
        n_symbols: nSymbols,
        n_conflicts: nConflicts,
        object_similarity: objectSim,
        symbol_similarity: 0.0,
        cycles,
        order,
        probe_original: true,
        input_noise: 0.0,
      },
      update_steps_per_event: 1,
    }

    try {
      await onRunExperiment(req)
      setExecutingStage('COMPLETE')
      setTimeout(() => setExecutingStage(null), 1000)
    } catch {
      setExecutingStage(null)
    }
  }

  return (
    <div className="memory-lab-layout">
      <div className="lab-header">
        <h2 className="lab-title">MEMORY LAB · EXPERIMENT CONFIGURATION</h2>
        <p className="lab-desc">
          Design computational memory substrates, calibrate state update dynamics, and generate controlled interference scenarios.
        </p>
      </div>

      <form className="lab-form" onSubmit={handleRun}>
        <div className="lab-grid">
          {/* Column 1: Mechanism Architecture */}
          <div className="lab-panel">
            <div className="panel-title">1. MECHANISM ARCHITECTURE</div>
            
            <div className="form-field">
              <label>UPDATE MECHANISM</label>
              <select value={mechanism} onChange={(e) => setMechanism(e.target.value)}>
                {Object.entries(mechanisms).map(([key, info]) => (
                  <option key={key} value={key}>
                    {info.name}
                  </option>
                ))}
              </select>
              <div className="field-hint">{MECHANISM_DESCRIPTIONS[mechanism]}</div>
            </div>

            <div className="form-field">
              <label>STATE DIMENSIONALITY (d)</label>
              <select value={stateDim} onChange={(e) => setStateDim(Number(e.target.value))}>
                <option value={32}>d = 32 (Low capacity / Heavy cross-talk)</option>
                <option value={64}>d = 64 (Moderate capacity)</option>
                <option value={128}>d = 128 (Recommended standard)</option>
                <option value={256}>d = 256 (High capacity / Sparse overlap)</option>
              </select>
            </div>

            <div className="form-field">
              <label>DETERMINISTIC SEED</label>
              <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
            </div>
          </div>

          {/* Column 2: Memory & Substrate Dynamics */}
          <div className="lab-panel">
            <div className="panel-title">2. SUBSTRATE DYNAMICS</div>

            <div className="form-field">
              <label>UPDATE STRENGTH (α): {updateStrength.toFixed(2)}</label>
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.05"
                value={updateStrength}
                onChange={(e) => setUpdateStrength(Number(e.target.value))}
              />
            </div>

            <div className="form-field">
              <label>DECAY RATE (λ): {decay.toFixed(2)}</label>
              <input
                type="range"
                min="0.0"
                max="0.9"
                step="0.05"
                value={decay}
                onChange={(e) => setDecay(Number(e.target.value))}
              />
            </div>

            <div className="form-field">
              <label>INTERFERENCE ERASURE (γ): {interferenceStrength.toFixed(2)}</label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={interferenceStrength}
                onChange={(e) => setInterferenceStrength(Number(e.target.value))}
              />
            </div>

            <div className="form-field">
              <label>SPARSITY THRESHOLD (k-WTA): {sparsity.toFixed(2)}</label>
              <input
                type="range"
                min="0.01"
                max="0.5"
                step="0.01"
                value={sparsity}
                onChange={(e) => setSparsity(Number(e.target.value))}
              />
            </div>
          </div>

          {/* Column 3: Task & Sequence Parameters */}
          <div className="lab-panel">
            <div className="panel-title">3. TASK & INTERFERENCE PROTOCOL</div>

            <div className="form-row">
              <div className="form-field half">
                <label>OBJECT CUES</label>
                <input
                  type="number"
                  min="2"
                  max="16"
                  value={nObjects}
                  onChange={(e) => setNObjects(Number(e.target.value))}
                />
              </div>
              <div className="form-field half">
                <label>SYMBOL VALUES</label>
                <input
                  type="number"
                  min="2"
                  max="16"
                  value={nSymbols}
                  onChange={(e) => setNSymbols(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="form-field">
              <label>CONFLICTING WRITES: {nConflicts}</label>
              <input
                type="range"
                min="0"
                max={Math.min(8, nObjects)}
                value={nConflicts}
                onChange={(e) => setNConflicts(Number(e.target.value))}
              />
            </div>

            <div className="form-field">
              <label>CUE VECTOR SIMILARITY: {objectSim.toFixed(2)}</label>
              <input
                type="range"
                min="0.0"
                max="0.8"
                step="0.05"
                value={objectSim}
                onChange={(e) => setObjectSim(Number(e.target.value))}
              />
            </div>

            <div className="form-field">
              <label>TASK CYCLES: {cycles}</label>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={cycles}
                onChange={(e) => setCycles(Number(e.target.value))}
              />
            </div>

            <div className="form-field">
              <label>SEQUENCE ORDER</label>
              <select
                value={order}
                onChange={(e) => setOrder(e.target.value as 'structured' | 'interleaved' | 'randomized')}
              >
                <option value="interleaved">Interleaved (Continuous Interference)</option>
                <option value="structured">Structured (Clustered Epochs)</option>
                <option value="randomized">Randomized Sequence</option>
              </select>
            </div>
          </div>
        </div>

        {/* Execution Strip */}
        <div className="lab-footer">
          {executingStage ? (
            <div className="execution-stepper">
              <span className="status-dot live" />
              <span className="stepper-stage">{executingStage}</span>
            </div>
          ) : (
            <div className="execution-info">
              Ready to compute state trajectory. Exact floating-point math across {stateDim} dimensions.
            </div>
          )}

          <button type="submit" className="primary large-btn" disabled={isBusy}>
            <span>⚡</span> RUN EXPERIMENT
          </button>
        </div>
      </form>
    </div>
  )
}
