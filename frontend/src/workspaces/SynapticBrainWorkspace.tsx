import React, { useEffect, useState } from 'react'
import type {
  Experiment,
  SynapticNetworkState,
} from '../types'
import {
  decaySynapticBrain,
  getSynapticFromExperiment,
  getSynapticState,
  recallSynapticMemory,
  resetSynapticBrain,
  runSynapticScenario,
  writeSynapticMemory,
} from '../api'
import { SynapticNetworkCanvas } from '../components/SynapticNetworkCanvas'
import { SynapticInspectorDrawer } from '../components/SynapticInspectorDrawer'

interface SynapticBrainWorkspaceProps {
  experiment: Experiment | null
  currentStep?: number
  onViewEvidence?: (title: string, details: Record<string, unknown>) => void
}

export const SynapticBrainWorkspace: React.FC<SynapticBrainWorkspaceProps> = ({
  experiment,
  currentStep = 0,
  onViewEvidence,
}) => {
  // Dimension & state
  const [dimension, setDimension] = useState<number>(16)
  const [decay, setDecay] = useState<number>(0.05)
  const updateStrength = 1.0
  const memoryStrength = 1.0
  const [networkState, setNetworkState] = useState<SynapticNetworkState | null>(null)
  const [isBusy, setIsBusy] = useState<boolean>(false)

  // Layout & Display toggles
  const [layoutMode, setLayoutMode] = useState<'bipartite' | 'radial' | 'matrix'>('bipartite')
  const [showLabels, setShowLabels] = useState<boolean>(true)
  const [showAllSynapses, setShowAllSynapses] = useState<boolean>(true)
  const [showMethodologyModal, setShowMethodologyModal] = useState<boolean>(false)

  // Selection
  const [selectedNeuronId, setSelectedNeuronId] = useState<string | null>(null)
  const [selectedSynapseId, setSelectedSynapseId] = useState<string | null>(null)

  // Forms: Write
  const [writeConcept, setWriteConcept] = useState<string>('color')
  const [writeValue, setWriteValue] = useState<string>('blue')
  const [writeImportance, setWriteImportance] = useState<number>(1.0)
  const [writeStrength, setWriteStrength] = useState<number>(1.0)

  // Forms: Recall
  const [recallConcept, setRecallConcept] = useState<string>('color')
  const [recallExpected, setRecallExpected] = useState<string>('blue')
  const [recallMeasure, setRecallMeasure] = useState<string>('cosine')

  // Load initial state
  useEffect(() => {
    setIsBusy(true)
    getSynapticState(dimension, decay)
      .then((st) => setNetworkState(st))
      .catch(() => {})
      .finally(() => setIsBusy(false))
  }, [dimension])

  // Sync with active experiment if requested
  const handleLoadFromActiveExperiment = async () => {
    if (!experiment) return
    setIsBusy(true)
    try {
      const st = await getSynapticFromExperiment(
        experiment.experiment_id,
        currentStep,
        dimension
      )
      setNetworkState(st)
    } catch (e) {
      alert(`Failed to load from experiment: ${String(e)}`)
    } finally {
      setIsBusy(false)
    }
  }

  // Action handlers
  const handleWriteMemory = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!writeConcept || !writeValue) return
    setIsBusy(true)
    try {
      const updated = await writeSynapticMemory({
        concept: writeConcept.trim(),
        value: writeValue.trim(),
        importance: writeImportance,
        strength: writeStrength,
        decay,
        update_strength: updateStrength,
        memory_strength: memoryStrength,
        dimension,
      })
      setNetworkState(updated)
      // Auto populate recall concept for convenience
      setRecallConcept(writeConcept.trim())
      setRecallExpected(writeValue.trim())
    } catch (err) {
      alert(`Write failed: ${String(err)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const handleRecallMemory = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!recallConcept) return
    setIsBusy(true)
    try {
      const updated = await recallSynapticMemory({
        query_concept: recallConcept.trim(),
        expected_value: recallExpected ? recallExpected.trim() : undefined,
        measure: recallMeasure,
        dimension,
      })
      setNetworkState(updated)
    } catch (err) {
      alert(`Recall failed: ${String(err)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const handleDecayStep = async (steps: number = 1) => {
    setIsBusy(true)
    try {
      const updated = await decaySynapticBrain(steps, decay)
      setNetworkState(updated)
    } catch (err) {
      alert(`Decay failed: ${String(err)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const handleReset = async () => {
    setIsBusy(true)
    try {
      const updated = await resetSynapticBrain(dimension, decay)
      setNetworkState(updated)
      setSelectedNeuronId(null)
      setSelectedSynapseId(null)
    } catch (err) {
      alert(`Reset failed: ${String(err)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const handleRunPreset = async (presetName: string) => {
    setIsBusy(true)
    try {
      const updated = await runSynapticScenario(presetName, dimension, decay)
      setNetworkState(updated)
      setSelectedNeuronId(null)
      setSelectedSynapseId(null)
    } catch (err) {
      alert(`Preset failed: ${String(err)}`)
    } finally {
      setIsBusy(false)
    }
  }

  // Selected entities for inspector
  const selectedNeuron = React.useMemo(() => {
    if (!selectedNeuronId || !networkState) return null
    return networkState.neurons.find((n) => n.id === selectedNeuronId) || null
  }, [selectedNeuronId, networkState])

  const selectedSynapse = React.useMemo(() => {
    if (!selectedSynapseId || !networkState) return null
    return networkState.synapses.find((s) => s.id === selectedSynapseId) || null
  }, [selectedSynapseId, networkState])

  const explanation = networkState?.last_explanation || null
  const recallResult = networkState?.last_recall || null

  return (
    <div className="synaptic-brain-workspace">
      {/* ── Top Instrumentation Header ───────────────────────────────── */}
      <header className="synaptic-header">
        <div className="synaptic-header-left">
          <div className="synaptic-title-badge">
            <span className="live-dot" />
            <span className="synaptic-title">LIVE SYNAPTIC BRAIN</span>
          </div>
          <span className="synaptic-subtitle">
            Synaptic Plasticity as Short-Term Memory
          </span>
        </div>

        <div className="synaptic-header-metrics">
          <div className="header-stat">
            <span className="stat-label">MATRIX DIM</span>
            <select
              className="stat-val accent"
              value={dimension}
              onChange={(e) => setDimension(Number(e.target.value))}
              style={{ background: 'transparent', border: 'none', color: '#818cf8', cursor: 'pointer', outline: 'none' }}
              disabled={isBusy}
            >
              <option value={8} style={{ background: '#0a0d14' }}>8×8 (64 syn)</option>
              <option value={16} style={{ background: '#0a0d14' }}>16×16 (256 syn)</option>
              <option value={32} style={{ background: '#0a0d14' }}>32×32 (1024 syn)</option>
            </select>
          </div>
          <div className="header-stat">
            <span className="stat-label">SYNAPSES</span>
            <span className="stat-val">{networkState?.active_synapses_count ?? 0} / {dimension * dimension}</span>
          </div>
          <div className="header-stat">
            <span className="stat-label">MATRIX NORM ||W||</span>
            <span className="stat-val cyan">{(networkState?.matrix_norm ?? 0).toFixed(3)}</span>
          </div>
          <div className="header-stat">
            <span className="stat-label">DECAY λ</span>
            <span className="stat-val amber">{(decay * 100).toFixed(1)}%</span>
          </div>
          <div className="header-stat">
            <span className="stat-label">TIMESTEP</span>
            <span className="stat-val emerald">T{networkState?.timestep ?? 0}</span>
          </div>
        </div>

        <div className="synaptic-header-actions">
          <button
            className="btn-scientific-info"
            onClick={() => setShowMethodologyModal(true)}
            title="Scientific Methodology & Model Context"
          >
            ⓘ Methodology
          </button>
          {experiment && (
            <button
              className="btn-secondary small"
              onClick={handleLoadFromActiveExperiment}
              title="Project active experiment step into synaptic network"
            >
              Sync Active Exp (Step {currentStep})
            </button>
          )}
        </div>
      </header>

      {/* ── Main Layout: Controls | Canvas | Telemetry ──────────────── */}
      <div className="synaptic-main-layout">
        {/* ── Left Scientific Controls ─────────────────────────────── */}
        <aside className="synaptic-controls-sidebar">
          {/* Hebbian Write Panel */}
          <div className="control-card">
            <div className="control-card-header">
              <span className="control-card-title">1. HEBBIAN SYNAPTIC WRITE</span>
              <span className="math-badge">W ← (1-λ)W + η(v⊗k)</span>
            </div>
            <form onSubmit={handleWriteMemory} className="synaptic-form">
              <div className="form-row">
                <div className="form-field">
                  <label>CONCEPT (KEY):</label>
                  <input
                    type="text"
                    value={writeConcept}
                    onChange={(e) => setWriteConcept(e.target.value)}
                    placeholder="e.g. color"
                    disabled={isBusy}
                  />
                </div>
                <div className="form-field">
                  <label>VALUE (PAYLOAD):</label>
                  <input
                    type="text"
                    value={writeValue}
                    onChange={(e) => setWriteValue(e.target.value)}
                    placeholder="e.g. blue"
                    disabled={isBusy}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-field">
                  <label>IMPORTANCE ({writeImportance}x):</label>
                  <input
                    type="range"
                    min="0.2"
                    max="2.0"
                    step="0.1"
                    value={writeImportance}
                    onChange={(e) => setWriteImportance(Number(e.target.value))}
                    disabled={isBusy}
                  />
                </div>
                <div className="form-field">
                  <label>WRITE STRENGTH ({writeStrength}x):</label>
                  <input
                    type="range"
                    min="0.2"
                    max="2.0"
                    step="0.1"
                    value={writeStrength}
                    onChange={(e) => setWriteStrength(Number(e.target.value))}
                    disabled={isBusy}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn-primary write-btn"
                disabled={isBusy || !writeConcept || !writeValue}
              >
                ⚡ Write Memory (Hebbian Update)
              </button>
            </form>
          </div>

          {/* Associative Recall Panel */}
          <div className="control-card">
            <div className="control-card-header">
              <span className="control-card-title">2. ASSOCIATIVE MEMORY RECALL</span>
              <span className="math-badge">v̂ = W @ k_query</span>
            </div>
            <form onSubmit={handleRecallMemory} className="synaptic-form">
              <div className="form-row">
                <div className="form-field">
                  <label>QUERY CONCEPT:</label>
                  <input
                    type="text"
                    value={recallConcept}
                    onChange={(e) => setRecallConcept(e.target.value)}
                    placeholder="e.g. color"
                    disabled={isBusy}
                  />
                </div>
                <div className="form-field">
                  <label>EXPECTED VALUE (OPTIONAL):</label>
                  <input
                    type="text"
                    value={recallExpected}
                    onChange={(e) => setRecallExpected(e.target.value)}
                    placeholder="e.g. blue"
                    disabled={isBusy}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-field">
                  <label>SIMILARITY MEASURE:</label>
                  <select
                    value={recallMeasure}
                    onChange={(e) => setRecallMeasure(e.target.value)}
                    disabled={isBusy}
                  >
                    <option value="cosine">Cosine (Directional)</option>
                    <option value="dot">Dot Product (Magnitude)</option>
                    <option value="euclidean">Euclidean Proximity</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="btn-secondary recall-btn"
                disabled={isBusy || !recallConcept}
              >
                ⌕ Recall / Probe Network
              </button>
            </form>
          </div>

          {/* Decay & Plasticity Dynamics */}
          <div className="control-card">
            <div className="control-card-header">
              <span className="control-card-title">3. DECAY & IDLE DYNAMICS</span>
              <span className="math-badge">W ← (1-λ)^n W</span>
            </div>
            <div className="decay-controls">
              <div className="form-field">
                <label>DECAY COEFFICIENT λ ({(decay * 100).toFixed(1)}% / step):</label>
                <input
                  type="range"
                  min="0.0"
                  max="0.4"
                  step="0.01"
                  value={decay}
                  onChange={(e) => setDecay(Number(e.target.value))}
                  disabled={isBusy}
                />
              </div>

              <div className="decay-btn-group">
                <button
                  type="button"
                  className="btn-decay"
                  onClick={() => handleDecayStep(1)}
                  disabled={isBusy}
                  title="Advance 1 step without input"
                >
                  ⏳ +1 Decay Step
                </button>
                <button
                  type="button"
                  className="btn-decay"
                  onClick={() => handleDecayStep(5)}
                  disabled={isBusy}
                  title="Advance 5 steps without input"
                >
                  ⏳ +5 Steps
                </button>
                <button
                  type="button"
                  className="btn-reset"
                  onClick={handleReset}
                  disabled={isBusy}
                  title="Reset all synaptic weights to zero"
                >
                  ↺ Reset
                </button>
              </div>
            </div>
          </div>

          {/* Scientific Scenarios */}
          <div className="control-card presets-card">
            <div className="control-card-header">
              <span className="control-card-title">EDUCATIONAL PRESETS</span>
            </div>
            <div className="preset-buttons">
              <button
                type="button"
                className="btn-preset"
                onClick={() => handleRunPreset('hebbian_formation')}
                disabled={isBusy}
              >
                ◈ 1. Hebbian Memory Formation
              </button>
              <button
                type="button"
                className="btn-preset"
                onClick={() => handleRunPreset('interference_demo')}
                disabled={isBusy}
              >
                ⊘ 2. Catastrophic Overwrite & Interference
              </button>
              <button
                type="button"
                className="btn-preset"
                onClick={() => handleRunPreset('decay_forgetting')}
                disabled={isBusy}
              >
                ⌛ 3. Working Memory Decay & Forgetting
              </button>
              <button
                type="button"
                className="btn-preset"
                onClick={() => handleRunPreset('pattern_completion')}
                disabled={isBusy}
              >
                ☊ 4. Associative Pattern Completion
              </button>
            </div>
          </div>
        </aside>

        {/* ── Center Central Canvas ─────────────────────────────────── */}
        <section className="synaptic-center-viewport">
          {/* Canvas Toolbar */}
          <div className="canvas-toolbar">
            <div className="toolbar-layout-toggles">
              <span className="toolbar-label">LAYOUT:</span>
              <button
                className={`btn-toggle ${layoutMode === 'bipartite' ? 'active' : ''}`}
                onClick={() => setLayoutMode('bipartite')}
              >
                Bipartite Crossbar
              </button>
              <button
                className={`btn-toggle ${layoutMode === 'radial' ? 'active' : ''}`}
                onClick={() => setLayoutMode('radial')}
              >
                Concentric Radial
              </button>
              <button
                className={`btn-toggle ${layoutMode === 'matrix' ? 'active' : ''}`}
                onClick={() => setLayoutMode('matrix')}
              >
                Matrix Heatmap
              </button>
            </div>

            <div className="toolbar-display-toggles">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                />
                Labels
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showAllSynapses}
                  onChange={(e) => setShowAllSynapses(e.target.checked)}
                />
                All Synapses
              </label>
            </div>
          </div>

          {/* Interactive Network Canvas */}
          <div className="canvas-wrapper">
            {networkState && (
              <SynapticNetworkCanvas
                dimension={dimension}
                neurons={networkState.neurons}
                synapses={networkState.synapses}
                lastPathway={networkState.last_pathway}
                selectedNeuronId={selectedNeuronId}
                selectedSynapseId={selectedSynapseId}
                onSelectNeuron={(id) => {
                  setSelectedNeuronId(id)
                  setSelectedSynapseId(null)
                }}
                onSelectSynapse={(id) => {
                  setSelectedSynapseId(id)
                  setSelectedNeuronId(null)
                }}
                layoutMode={layoutMode}
                showLabels={showLabels}
                showAllSynapses={showAllSynapses}
              />
            )}
          </div>

          {/* Bottom Event Timeline */}
          <div className="synaptic-timeline-bar">
            <div className="timeline-bar-header">
              <span className="timeline-title">EVENT TIMELINE</span>
              <span className="timeline-hint">Select event to inspect historical synaptic state</span>
            </div>
            <div className="timeline-events-track">
              {networkState?.history_timeline.map((item, idx) => (
                <div
                  key={idx}
                  className={`timeline-step-chip ${item.event_type.toLowerCase()}`}
                  title={`${item.event_type}: ${item.label}`}
                >
                  <span className="step-num">T{item.step}</span>
                  <span className="step-type">{item.event_type}</span>
                  <span className="step-label">{item.label}</span>
                  <span className="step-norm">||W||={item.matrix_norm.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Right Telemetry & Forensic Analysis ──────────────────── */}
        <aside className="synaptic-telemetry-sidebar">
          {/* Computational Explanation HUD */}
          {explanation && (
            <div className="telemetry-card">
              <div className="telemetry-card-header">
                <span className="telemetry-title">COMPUTATIONAL FORMATION HUD</span>
                <span className={`event-badge ${explanation.event_type.toLowerCase()}`}>
                  {explanation.event_type}
                </span>
              </div>
              <div className="event-name-banner">{explanation.event_label}</div>

              <div className="telemetry-metrics-grid">
                <div className="tele-metric">
                  <span className="tele-label">Active Units:</span>
                  <span className="tele-val accent">{explanation.active_units}</span>
                </div>
                <div className="tele-metric">
                  <span className="tele-label">Synaptic Updates:</span>
                  <span className="tele-val">{explanation.synaptic_updates}</span>
                </div>
                <div className="tele-metric">
                  <span className="tele-label">Mean ΔW:</span>
                  <span className="tele-val cyan">{explanation.mean_weight_change.toFixed(4)}</span>
                </div>
                <div className="tele-metric">
                  <span className="tele-label">State Δ%:</span>
                  <span className="tele-val emerald">{explanation.state_change_pct.toFixed(1)}%</span>
                </div>
                <div className="tele-metric">
                  <span className="tele-label">Norm Before:</span>
                  <span className="tele-val">{explanation.norm_before.toFixed(3)}</span>
                </div>
                <div className="tele-metric">
                  <span className="tele-label">Norm After:</span>
                  <span className="tele-val font-bold">{explanation.norm_after.toFixed(3)}</span>
                </div>
              </div>

              <p className="telemetry-scientific-note">
                {explanation.scientific_note}
              </p>

              {onViewEvidence && (
                <button
                  className="btn-evidence"
                  onClick={() =>
                    onViewEvidence('Synaptic Formation Telemetry', {
                      explanation,
                      networkState,
                    })
                  }
                >
                  View Computational Evidence
                </button>
              )}
            </div>
          )}

          {/* Recall Fidelity & Readout HUD */}
          {recallResult && (
            <div className="telemetry-card recall-fidelity-card">
              <div className="telemetry-card-header">
                <span className="telemetry-title">RECALL FIDELITY & READOUT</span>
                <span className={`fidelity-status-badge ${recallResult.is_correct === false ? 'fail' : 'pass'}`}>
                  {recallResult.is_correct === true
                    ? 'EXACT MATCH ✓'
                    : recallResult.is_correct === false
                    ? 'DEGRADED / MISMATCH'
                    : 'PROBE RESULT'}
                </span>
              </div>

              <div className="recall-prediction-box">
                <div className="pred-row">
                  <span className="pred-label">Query:</span>
                  <span className="pred-query accent">{recallResult.query_concept}</span>
                </div>
                <div className="pred-row">
                  <span className="pred-label">Predicted:</span>
                  <span className="pred-val font-bold">{recallResult.predicted_value || 'None'}</span>
                </div>
                <div className="pred-row">
                  <span className="pred-label">Confidence:</span>
                  <span className="pred-conf cyan">{(recallResult.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>

              {/* Candidate rankings */}
              <div className="candidate-rankings">
                <span className="candidate-header">LIBRARY CANDIDATES MATCHING:</span>
                {recallResult.candidate_matches.map((cand, idx) => (
                  <div key={idx} className="candidate-row">
                    <span className="cand-name">{cand.concept}={cand.value}</span>
                    <div className="cand-bar-track">
                      <div
                        className="cand-bar-fill"
                        style={{
                          width: `${Math.max(0, Math.min(100, cand.similarity * 100))}%`,
                        }}
                      />
                    </div>
                    <span className="cand-score">{(cand.similarity * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Synapse / Neuron Inspector Drawer */}
          {(selectedNeuron || selectedSynapse) && (
            <SynapticInspectorDrawer
              neuron={selectedNeuron}
              synapse={selectedSynapse}
              onClose={() => {
                setSelectedNeuronId(null)
                setSelectedSynapseId(null)
              }}
            />
          )}
        </aside>
      </div>

      {/* ── Scientific Methodology & Honesty Modal ──────────────────── */}
      {showMethodologyModal && (
        <div className="methodology-modal-backdrop" onClick={() => setShowMethodologyModal(false)}>
          <div className="methodology-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Scientific Model & Educational Context</h3>
              <button className="modal-close" onClick={() => setShowMethodologyModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="methodology-alert info">
                <strong>Educational Scientific Instrument:</strong> This interactive laboratory
                demonstrates how recent neural activity temporarily strengthens synaptic connections
                (synaptic plasticity), turning network wiring into a dynamic form of short-term/working memory.
              </div>

              <h4>1. Research Connection (BDH & Associative Memory)</h4>
              <p>
                Inspired by the conceptual neuron-synapse models (e.g. BDH neuron-synapse architecture
                and classical Anderson/Kohonen associative matrix memory), where local Hebbian writes allow
                recent token activity to configure temporary synaptic pathways that modulate subsequent computation.
              </p>

              <h4>2. Mathematical Formulations</h4>
              <ul>
                <li>
                  <strong>Hebbian Outer-Product Write:</strong>
                  <code>W(t+1) = (1 - λ) · W(t) + η · (v ⊗ k)</code>
                </li>
                <li>
                  <strong>Linear Associative Recall:</strong>
                  <code>v̂ = W @ k_query</code>
                </li>
                <li>
                  <strong>Exponential Synaptic Decay:</strong>
                  <code>W(t+n) = (1 - λ)^n · W(t)</code>
                </li>
                <li>
                  <strong>Cosine Readout Metric:</strong>
                  <code>cosine(v̂, v) = ⟨v̂, v⟩ / (||v̂|| · ||v||)</code>
                </li>
              </ul>

              <h4>3. Scientific Honesty Statement</h4>
              <p>
                This toy model is an educational computational substrate designed for transparent
                forensic inspection. It is NOT a claim of having invented a new production LLM architecture
                or a literal biological brain simulation.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
