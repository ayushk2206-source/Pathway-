import React, { useEffect, useState } from 'react'
import type {
  Experiment,
  StateDiffResult,
  SynapticNetworkState,
} from '../types'
import {
  decaySynapticBrain,
  getSynapticFromExperiment,
  getSynapticSnapshot,
  getSynapticState,
  recallSynapticMemory,
  resetSynapticBrain,
  runSynapticProtocol,
  runSynapticScenario,
  writeSynapticMemory,
} from '../api'
import { SynapticNetworkCanvas } from '../components/SynapticNetworkCanvas'
import { SynapticInspectorDrawer } from '../components/SynapticInspectorDrawer'
import { SynapticTimeScrubber } from '../components/SynapticTimeScrubber'
import { SynapticDiffInspector } from '../components/SynapticDiffInspector'

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

  // Time Machine States
  const [activeStep, setActiveStep] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1)
  const [isFrozen, setIsFrozen] = useState<boolean>(false)
  const [showDiffModal, setShowDiffModal] = useState<boolean>(false)
  const [diffHighlightMode, setDiffHighlightMode] = useState<boolean>(true)
  const [activeDiffResult, setActiveDiffResult] = useState<StateDiffResult | null>(null)
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null)

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

  // Load initial state and check URL query param
  useEffect(() => {
    setIsBusy(true)
    const params = new URLSearchParams(window.location.search)
    const initialT = params.get('t') ? parseInt(params.get('t')!, 10) : null

    getSynapticState(dimension, decay)
      .then(async (st) => {
        setNetworkState(st)
        if (initialT !== null && initialT >= 0 && initialT < st.history_timeline.length) {
          setActiveStep(initialT)
          const snap = await getSynapticSnapshot(initialT)
          setNetworkState(snap)
        } else {
          setActiveStep(st.timestep)
        }
      })
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
      setActiveStep(currentStep)
    } catch (e) {
      alert(`Failed to load from experiment: ${String(e)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const syncStateAndStep = (st: SynapticNetworkState) => {
    setNetworkState(st)
    setActiveStep(st.timestep)
    const url = new URL(window.location.href)
    url.searchParams.set('t', String(st.timestep))
    window.history.replaceState({}, '', url.toString())
  }

  // Time Machine Scrubbing
  const handleScrub = async (step: number) => {
    setActiveStep(step)
    setIsBusy(true)
    try {
      if (experiment) {
        const st = await getSynapticFromExperiment(experiment.experiment_id, step, dimension)
        setNetworkState(st)
      } else {
        const st = await getSynapticSnapshot(step)
        setNetworkState(st)
      }
      const url = new URL(window.location.href)
      url.searchParams.set('t', String(step))
      window.history.replaceState({}, '', url.toString())
    } catch (e) {
      console.error(`Scrub to step ${step} failed:`, e)
    } finally {
      setIsBusy(false)
    }
  }

  // Auto playback loop
  useEffect(() => {
    if (!isPlaying) return
    const totalSteps = networkState?.history_timeline.length ?? 0
    if (totalSteps <= 1) {
      setIsPlaying(false)
      return
    }

    const intervalMs = Math.max(250, Math.round(1200 / playbackSpeed))
    const timer = setInterval(() => {
      setActiveStep((prev) => {
        const next = prev + 1
        if (next >= totalSteps) {
          setIsPlaying(false)
          return prev
        }
        handleScrub(next)
        return next
      })
    }, intervalMs)

    return () => clearInterval(timer)
  }, [isPlaying, playbackSpeed, networkState?.history_timeline.length])

  const handleTogglePlay = () => {
    const total = networkState?.history_timeline.length ?? 0
    if (total <= 1) return
    if (activeStep >= total - 1) {
      handleScrub(0)
    }
    setIsPlaying(!isPlaying)
  }

  const handleStepForward = () => {
    const total = networkState?.history_timeline.length ?? 0
    if (activeStep < total - 1) {
      handleScrub(activeStep + 1)
    }
  }

  const handleStepBackward = () => {
    if (activeStep > 0) {
      handleScrub(activeStep - 1)
    }
  }

  const handleToggleFreeze = () => {
    if (isPlaying) setIsPlaying(false)
    setIsFrozen(!isFrozen)
  }

  const handleRunGuidedProtocol = async () => {
    setIsBusy(true)
    try {
      const res = await runSynapticProtocol({ dimension, decay })
      setNetworkState(res.current_state)
      setActiveStep(0)
      await handleScrub(0)
      setIsPlaying(true)
    } catch (e) {
      alert(`Guided protocol failed: ${String(e)}`)
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
      syncStateAndStep(updated)
      setRecallConcept(writeConcept.trim())
      setRecallExpected(writeValue.trim())
      setSelectedConcept(writeConcept.trim())
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
      syncStateAndStep(updated)
      setSelectedConcept(recallConcept.trim())
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
      syncStateAndStep(updated)
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
      syncStateAndStep(updated)
      setSelectedNeuronId(null)
      setSelectedSynapseId(null)
      setSelectedConcept(null)
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
      syncStateAndStep(updated)
      setSelectedNeuronId(null)
      setSelectedSynapseId(null)
      setSelectedConcept(null)
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

          {/* Freeze Alert Banner */}
          {isFrozen && (
            <div className="freeze-banner-alert">
              <div className="freeze-banner-content">
                <span className="freeze-icon">❄</span>
                <span className="freeze-text">
                  <strong>CHRONOMETER FROZEN AT TIMESTEP T{activeStep}.</strong> State is locked for microscopic inspection.
                </span>
              </div>
              <button
                type="button"
                className="btn-unfreeze"
                onClick={handleToggleFreeze}
              >
                ▶ Resume Live Stream
              </button>
            </div>
          )}

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
                diffResult={activeDiffResult}
                diffHighlightMode={diffHighlightMode && showDiffModal}
                memoryTrailActiveSynapses={
                  selectedConcept && networkState.last_pathway?.active_synapse_ids
                    ? networkState.last_pathway.active_synapse_ids
                    : []
                }
              />
            )}
          </div>

          {/* Bottom Time Machine Timeline Scrubber */}
          {networkState && (
            <SynapticTimeScrubber
              timeline={networkState.history_timeline}
              currentStep={activeStep}
              totalSteps={networkState.history_timeline.length}
              isPlaying={isPlaying}
              playbackSpeed={playbackSpeed}
              isFrozen={isFrozen}
              diffMode={showDiffModal}
              onScrub={handleScrub}
              onTogglePlay={handleTogglePlay}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSetSpeed={(s) => setPlaybackSpeed(s)}
              onToggleFreeze={handleToggleFreeze}
              onToggleDiff={() => setShowDiffModal(!showDiffModal)}
              onRunProtocol={handleRunGuidedProtocol}
            />
          )}
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

          {/* Synapse / Neuron / Memory Inspector Drawer */}
          {(selectedNeuron || selectedSynapse || selectedConcept) && (
            <SynapticInspectorDrawer
              neuron={selectedNeuron}
              synapse={selectedSynapse}
              selectedConcept={selectedConcept}
              onClose={() => {
                setSelectedNeuronId(null)
                setSelectedSynapseId(null)
                setSelectedConcept(null)
              }}
              onSelectConcept={(c) => setSelectedConcept(c)}
            />
          )}
        </aside>
      </div>

      {/* ── Before / After Forensic Diff Modal ──────────────────────── */}
      {showDiffModal && networkState && (
        <div className="diff-modal-backdrop" onClick={() => setShowDiffModal(false)}>
          <div className="diff-modal-content" onClick={(e) => e.stopPropagation()}>
            <SynapticDiffInspector
              timeline={networkState.history_timeline}
              currentStep={activeStep}
              experimentId={experiment?.experiment_id}
              diffHighlight={diffHighlightMode}
              onToggleDiffHighlight={(val) => setDiffHighlightMode(val)}
              onSelectSynapse={(id) => {
                setSelectedSynapseId(id)
                setSelectedNeuronId(null)
              }}
              onClose={() => setShowDiffModal(false)}
              onDiffComputed={(diff) => setActiveDiffResult(diff)}
            />
          </div>
        </div>
      )}

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
