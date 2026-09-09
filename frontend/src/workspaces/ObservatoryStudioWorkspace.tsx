import React, { useState, useEffect, useRef } from 'react'
import {
  getObservatoryPresets,
  listObservatorySessions,
  getObservatorySession,
  runObservatoryStream,
  diffObservatoryStates,
  getStabilityPlasticity,
  branchObservatoryIntervention,
  branchObservatoryCounterfactual,
  compareObservatorySessions,
  submitObservatoryPrediction,
  exportObservatoryDetectiveCase,
  exportObservatorySessionJson,
} from '../api'
import type {
  ObservatorySession,
  ChangeDetection,
  StabilityPlasticityMetrics,
  EnvironmentShiftReport,
  ObservatoryPreset,
  ObservatoryComparison,
} from '../types'
import { SynapticWeatherMap } from '../components/SynapticWeatherMap'
import { MemoryStateTrail } from '../components/MemoryStateTrail'
import { ChangeDetectorPanel } from '../components/ChangeDetectorPanel'
import { StabilityPlasticityView } from '../components/StabilityPlasticityView'
import { AdaptationGraph } from '../components/AdaptationGraph'
import '../observatory.css'

export const ObservatoryStudioWorkspace: React.FC = () => {
  // Session & Presets state
  const [presets, setPresets] = useState<ObservatoryPreset[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState<string>('env_shift_aba')
  const [sessionsList, setSessionsList] = useState<Array<{ session_id: string; name: string }>>([])
  const [activeSession, setActiveSession] = useState<ObservatorySession | null>(null)
  const [envReport, setEnvReport] = useState<EnvironmentShiftReport | null>(null)

  // Sliders
  const [learningRate, setLearningRate] = useState<number>(0.25)
  const [decayRate, setDecayRate] = useState<number>(0.02)
  const [dimension] = useState<number>(16)

  // Playback & Scrubber
  const [currentStep, setCurrentStep] = useState<number>(0)
  const [compareStep, setCompareStep] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const playTimerRef = useRef<number | null>(null)

  // Analysis State
  const [diff, setDiff] = useState<ChangeDetection | null>(null)
  const [stabilityMetrics, setStabilityMetrics] = useState<StabilityPlasticityMetrics | null>(null)
  const [loadingDiff, setLoadingDiff] = useState<boolean>(false)
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(false)

  // Prediction State
  const [predictionCategory, setPredictionCategory] = useState<string>('')
  const [hypothesisText, setHypothesisText] = useState<string>('')
  const [predictionSubmitted, setPredictionSubmitted] = useState<boolean>(false)
  const [predictionFeedback, setPredictionFeedback] = useState<string | null>(null)

  // Modals & Branching
  const [surgeryModalOpen, setSurgeryModalOpen] = useState<boolean>(false)
  const [selectedSynapse, setSelectedSynapse] = useState<{ row: number; col: number; weight: number } | null>(null)
  const [newSynapseWeight, setNewSynapseWeight] = useState<number>(0.0)

  const [counterfactualModalOpen, setCounterfactualModalOpen] = useState<boolean>(false)
  const [cfLearningRate, setCfLearningRate] = useState<number>(0.1)
  const [cfDecayRate, setCfDecayRate] = useState<number>(0.05)

  const [comparisonResult, setComparisonResult] = useState<ObservatoryComparison | null>(null)
  const [compareModalOpen, setCompareModalOpen] = useState<boolean>(false)
  const [selectedCompareSessionId, setSelectedCompareSessionId] = useState<string>('')

  const [statusMessage, setStatusMessage] = useState<string>('')

  // Load Presets & Initial Sessions on mount
  useEffect(() => {
    loadPresets()
    loadSessions()
  }, [])

  const loadPresets = async () => {
    try {
      const res = await getObservatoryPresets()
      setPresets(res.presets)
      if (res.presets.length > 0) {
        setSelectedPresetId(res.presets[0].id)
      }
    } catch (err) {
      console.error('Failed to load observatory presets:', err)
    }
  }

  const loadSessions = async () => {
    try {
      const res = await listObservatorySessions()
      setSessionsList(res.sessions)
      if (res.sessions.length > 0 && !activeSession) {
        const full = await getObservatorySession(res.sessions[0].session_id)
        setActiveSession(full.session)
        setEnvReport(full.env_report || null)
        setCurrentStep(full.session.snapshots.length > 0 ? full.session.snapshots.length - 1 : 0)
        setCompareStep(0)
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  // Handle Play / Pause Animation
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = window.setInterval(() => {
        setCurrentStep((prev) => {
          if (!activeSession || prev >= activeSession.snapshots.length - 1) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, 700)
    } else {
      if (playTimerRef.current) window.clearInterval(playTimerRef.current)
    }
    return () => {
      if (playTimerRef.current) window.clearInterval(playTimerRef.current)
    }
  }, [isPlaying, activeSession])

  // Update Diff when steps change
  useEffect(() => {
    if (activeSession && activeSession.snapshots.length > 0) {
      fetchDiff(currentStep, compareStep)
      fetchStability(compareStep, currentStep)
    }
  }, [currentStep, compareStep, activeSession])

  const fetchDiff = async (to: number, from: number) => {
    if (!activeSession) return
    setLoadingDiff(true)
    try {
      const res = await diffObservatoryStates({
        session_id: activeSession.session_id,
        step_from: from,
        step_to: to,
        threshold: 0.005,
      })
      setDiff(res.diff)
    } catch (err) {
      console.error('Failed to compute diff:', err)
    } finally {
      setLoadingDiff(false)
    }
  }

  const fetchStability = async (stepA: number, stepB: number) => {
    if (!activeSession) return
    setLoadingMetrics(true)
    try {
      const res = await getStabilityPlasticity(activeSession.session_id, stepA, stepB)
      setStabilityMetrics(res.metrics)
    } catch (err) {
      console.error('Failed to get stability metrics:', err)
    } finally {
      setLoadingMetrics(false)
    }
  }

  // Execute Stream for Selected Preset
  const handleExecuteStream = async () => {
    setStatusMessage('Simulating adaptive continuous memory stream...')
    setIsPlaying(false)
    try {
      let events: Array<{
        event_id: string
        step: number
        event_type: string
        key_label: string
        environment_id: string
        learning_rate: number
        decay_rate: number
        cue_pattern: number[]
        target_pattern: number[]
      }> = []

      const d = dimension
      const patA = Array(d).fill(0).map((_, i) => (i < d / 2 ? 1 : 0))
      const patB = Array(d).fill(0).map((_, i) => (i >= d / 4 && i < (3 * d) / 4 ? 1 : 0))
      const patC = Array(d).fill(0).map((_, i) => (i % 2 === 0 ? 1 : 0))

      if (selectedPresetId === 'env_shift_aba') {
        events = [
          { event_id: 'ev_0', step: 0, event_type: 'BASELINE', key_label: 'Init', environment_id: 'ENV_A', learning_rate: 0, decay_rate: 0, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_1', step: 1, event_type: 'WRITE_A', key_label: 'Concept A', environment_id: 'ENV_A', learning_rate: learningRate, decay_rate: decayRate, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_2', step: 2, event_type: 'WRITE_A_REINFORCE', key_label: 'Concept A', environment_id: 'ENV_A', learning_rate: learningRate, decay_rate: decayRate, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_3', step: 3, event_type: 'ENV_TRANSITION', key_label: 'Context Shift', environment_id: 'ENV_B', learning_rate: 0, decay_rate: decayRate, cue_pattern: patB, target_pattern: patB },
          { event_id: 'ev_4', step: 4, event_type: 'WRITE_B', key_label: 'Concept B', environment_id: 'ENV_B', learning_rate: learningRate, decay_rate: decayRate, cue_pattern: patB, target_pattern: patB },
          { event_id: 'ev_5', step: 5, event_type: 'WRITE_B_OVERWRITE', key_label: 'Concept B', environment_id: 'ENV_B', learning_rate: learningRate, decay_rate: decayRate, cue_pattern: patB, target_pattern: patB },
          { event_id: 'ev_6', step: 6, event_type: 'RETURN_TO_A', key_label: 'Return Context', environment_id: 'ENV_A', learning_rate: 0, decay_rate: decayRate, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_7', step: 7, event_type: 'WRITE_A_RECALL', key_label: 'Concept A', environment_id: 'ENV_A', learning_rate: learningRate, decay_rate: decayRate, cue_pattern: patA, target_pattern: patA },
        ]
      } else if (selectedPresetId === 'catastrophic_collision') {
        events = [
          { event_id: 'ev_0', step: 0, event_type: 'BASELINE', key_label: 'Init', environment_id: 'ENV_MAIN', learning_rate: 0, decay_rate: 0, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_1', step: 1, event_type: 'STRONG_WRITE_A', key_label: 'Concept A', environment_id: 'ENV_MAIN', learning_rate: 0.5, decay_rate: decayRate, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_2', step: 2, event_type: 'OVERLAPPING_WRITE_B', key_label: 'Concept B (Overlapping)', environment_id: 'ENV_MAIN', learning_rate: 0.5, decay_rate: decayRate, cue_pattern: patB, target_pattern: patB },
          { event_id: 'ev_3', step: 3, event_type: 'INTERFERENCE_WRITE_C', key_label: 'Concept C (Orthogonal)', environment_id: 'ENV_MAIN', learning_rate: 0.4, decay_rate: decayRate, cue_pattern: patC, target_pattern: patC },
        ]
      } else {
        // Passive decay
        events = [
          { event_id: 'ev_0', step: 0, event_type: 'BASELINE', key_label: 'Init', environment_id: 'ENV_LAB', learning_rate: 0, decay_rate: 0, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_1', step: 1, event_type: 'WRITE_A', key_label: 'Concept A', environment_id: 'ENV_LAB', learning_rate: 0.4, decay_rate: 0, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_2', step: 2, event_type: 'DECAY_1', key_label: 'Passive Decay T1', environment_id: 'ENV_LAB', learning_rate: 0, decay_rate: 0.08, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_3', step: 3, event_type: 'DECAY_2', key_label: 'Passive Decay T2', environment_id: 'ENV_LAB', learning_rate: 0, decay_rate: 0.08, cue_pattern: patA, target_pattern: patA },
          { event_id: 'ev_4', step: 4, event_type: 'RE_CONSOLIDATION', key_label: 'Re-activation', environment_id: 'ENV_LAB', learning_rate: 0.35, decay_rate: 0.01, cue_pattern: patA, target_pattern: patA },
        ]
      }

      const probes = [
        { concept: 'Concept A', cue_pattern: patA, target_pattern: patA },
        { concept: 'Concept B', cue_pattern: patB, target_pattern: patB },
        { concept: 'Concept C', cue_pattern: patC, target_pattern: patC },
      ]

      const res = await runObservatoryStream({
        name: `Stream - ${selectedPresetId} (η=${learningRate}, λ=${decayRate})`,
        description: `Simulated continuous stream for preset ${selectedPresetId}`,
        dimension,
        default_learning_rate: learningRate,
        default_decay_rate: decayRate,
        events,
        probes,
      })

      setActiveSession(res.session)
      setEnvReport(res.env_report || null)
      setCurrentStep(res.session.snapshots.length - 1)
      setCompareStep(0)
      loadSessions()
      setStatusMessage(`Stream completed successfully (${res.session.snapshots.length} timesteps recorded).`)

      // Check prediction if submitted
      if (predictionSubmitted && res.env_report) {
        validatePrediction(res.env_report)
      }
    } catch (err) {
      console.error('Failed to run observatory stream:', err)
      setStatusMessage('Error executing stream.')
    }
  }

  // Handle Prediction Submit
  const handlePredictionSubmit = async () => {
    if (!activeSession || !predictionCategory) return
    try {
      const res = await submitObservatoryPrediction({
        session_id: activeSession.session_id,
        target_env: 'ENV_B',
        predicted_category: predictionCategory,
        hypothesis: hypothesisText || 'Learner predicted adaptation outcome',
        confidence: 0.85,
      })
      setPredictionSubmitted(true)
      setPredictionFeedback(res.prediction.validation_summary || 'Prediction recorded.')
      setStatusMessage('Prediction recorded. Run or step the stream to verify!')
    } catch (err) {
      console.error('Failed to submit prediction:', err)
    }
  }

  const validatePrediction = (report: EnvironmentShiftReport) => {
    const isInterference = report.interference_detected
    let correct = false
    if (isInterference && predictionCategory === 'INTERFERENCE') correct = true
    if (!isInterference && predictionCategory === 'PRESERVED') correct = true
    if (predictionCategory === 'RECOVERY' && report.retroactive_retention > 0.4) correct = true

    setPredictionFeedback(
      correct
        ? `Hypothesis Confirmed! Real data shows: ${report.summary}`
        : `Empirical divergence: Observed ${report.summary}`,
    )
  }

  // Handle Synaptic Surgery Branch
  const handlePerformSurgery = async () => {
    if (!activeSession || !selectedSynapse) return
    try {
      const res = await branchObservatoryIntervention({
        session_id: activeSession.session_id,
        branch_step: currentStep,
        target_synapse: [selectedSynapse.row, selectedSynapse.col],
        new_weight: newSynapseWeight,
        branch_name: `Surgery W[${selectedSynapse.row},${selectedSynapse.col}]=${newSynapseWeight.toFixed(2)} @ T${currentStep}`,
      })
      setSurgeryModalOpen(false)
      setActiveSession(res.branch_session)
      setCurrentStep(res.branch_session.snapshots.length - 1)
      setStatusMessage(`Branched timeline via Synaptic Surgery on (${selectedSynapse.row}, ${selectedSynapse.col}).`)
      loadSessions()
    } catch (err) {
      console.error('Failed to branch surgery:', err)
      setStatusMessage('Surgery failed.')
    }
  }

  // Handle Counterfactual Branch
  const handlePerformCounterfactual = async () => {
    if (!activeSession) return
    try {
      const res = await branchObservatoryCounterfactual({
        session_id: activeSession.session_id,
        branch_step: currentStep,
        altered_learning_rate: cfLearningRate,
        altered_decay_rate: cfDecayRate,
        branch_name: `What-If η=${cfLearningRate}, λ=${cfDecayRate} @ T${currentStep}`,
      })
      setCounterfactualModalOpen(false)
      setActiveSession(res.branch_session)
      setCurrentStep(res.branch_session.snapshots.length - 1)
      setStatusMessage(`Branched counterfactual timeline from T${currentStep}.`)
      loadSessions()
    } catch (err) {
      console.error('Failed to branch counterfactual:', err)
      setStatusMessage('Counterfactual branch failed.')
    }
  }

  // Handle Compare Sessions
  const handleCompareSessions = async () => {
    if (!activeSession || !selectedCompareSessionId) return
    try {
      const res = await compareObservatorySessions(activeSession.session_id, selectedCompareSessionId)
      setComparisonResult(res.comparison)
      setStatusMessage('Side-by-side session comparison calculated.')
    } catch (err) {
      console.error('Failed to compare sessions:', err)
    }
  }

  // Export to Detective
  const handleExportToDetective = async () => {
    if (!activeSession) return
    try {
      const res = await exportObservatoryDetectiveCase({
        session_id: activeSession.session_id,
        target_concept: 'Concept A',
        interference_step: currentStep,
      })
      setStatusMessage(`Exported anomaly to Memory Detective: "${res.title}"`)
    } catch (err) {
      console.error('Failed to export to detective:', err)
      setStatusMessage('Export to detective failed.')
    }
  }

  // Export JSON
  const handleExportJson = async () => {
    if (!activeSession) return
    try {
      const data = await exportObservatorySessionJson(activeSession.session_id)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `observatory_${activeSession.session_id}.json`
      a.click()
      URL.revokeObjectURL(url)
      setStatusMessage('Session telemetry exported as JSON.')
    } catch (err) {
      console.error('Failed to export JSON:', err)
    }
  }

  const currentSnapshot = activeSession && activeSession.snapshots[currentStep]
    ? activeSession.snapshots[currentStep]
    : null

  return (
    <div className="observatory-container">
      {/* Header */}
      <div className="observatory-header">
        <div className="observatory-title-group">
          <h1>
            <span>Adaptive Memory Observatory</span>
          </h1>
          <p className="observatory-subtitle">
            Phase 19: Continuous synaptic state evolution, dynamic weather maps, and live stability-plasticity analysis
          </p>
        </div>

        <div className="observatory-controls">
          <button className="observatory-btn primary" onClick={handleExecuteStream}>
            ⚡ Execute Stream
          </button>
          <button
            className="observatory-btn accent"
            onClick={() => setCounterfactualModalOpen(true)}
            disabled={!activeSession}
          >
            🔀 Branch What-If
          </button>
          <button
            className="observatory-btn warning"
            onClick={() => {
              if (sessionsList.length > 1) {
                const other = sessionsList.find((s) => s.session_id !== activeSession?.session_id)
                if (other) setSelectedCompareSessionId(other.session_id)
                setCompareModalOpen(true)
              } else {
                setStatusMessage('Need at least 2 sessions to run side-by-side comparison.')
              }
            }}
            disabled={!activeSession || sessionsList.length < 2}
          >
            ⚖ Compare Runs
          </button>
          <button
            className="observatory-btn"
            onClick={handleExportToDetective}
            disabled={!activeSession}
            title="Send real memory anomaly case to Phase 18 Detective"
          >
            🕵 Send to Detective
          </button>
          <button
            className="observatory-btn"
            onClick={handleExportJson}
            disabled={!activeSession}
            title="Download full session as JSON"
          >
            💾 Export JSON
          </button>
        </div>
      </div>

      {statusMessage && (
        <div style={{
          padding: '0.5rem 1rem',
          background: 'rgba(56, 189, 248, 0.15)',
          border: '1px solid #38bdf8',
          borderRadius: '8px',
          fontSize: '0.82rem',
          color: '#e0f2fe',
        }}>
          {statusMessage}
        </div>
      )}

      {/* Preset & Plasticity Ribbon */}
      <div className="observatory-ribbon">
        <div className="ribbon-presets">
          <span className="ribbon-label">Experimental Presets:</span>
          {presets.map((preset) => (
            <button
              key={preset.id}
              className={`preset-chip ${selectedPresetId === preset.id ? 'active' : ''}`}
              onClick={() => setSelectedPresetId(preset.id)}
            >
              {preset.name}
            </button>
          ))}
        </div>

        <div className="ribbon-params">
          <div className="param-group">
            <span>Learning Rate (η):</span>
            <input
              type="range"
              min="0.05"
              max="0.80"
              step="0.05"
              value={learningRate}
              onChange={(e) => setLearningRate(parseFloat(e.target.value))}
            />
            <span className="param-val">{learningRate.toFixed(2)}</span>
          </div>

          <div className="param-group">
            <span>Passive Decay (λ):</span>
            <input
              type="range"
              min="0.0"
              max="0.20"
              step="0.01"
              value={decayRate}
              onChange={(e) => setDecayRate(parseFloat(e.target.value))}
            />
            <span className="param-val">{decayRate.toFixed(2)}</span>
          </div>
        </div>

        {envReport && (
          <div style={{
            padding: '0.4rem 0.8rem',
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '6px',
            fontSize: '0.75rem',
            color: '#38bdf8',
            marginTop: '0.4rem',
            width: '100%',
          }}>
            <strong>Environment Shift Report ({envReport.env_a} ➔ {envReport.env_b}):</strong> {envReport.summary} (Drift: {envReport.drift_distance.toFixed(4)}, Retroactive Retention: {(envReport.retroactive_retention * 100).toFixed(1)}%)
          </div>
        )}
      </div>

      {/* Prediction Mode Banner */}
      <div className="prediction-banner">
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
            🔮 Active Prediction Mode: Predict Adaptation Outcome
          </div>
          <div style={{ fontSize: '0.78rem', color: '#c7d2fe', marginTop: '2px' }}>
            How will the memory network respond across the upcoming environment shift?
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="prediction-options">
            {[
              { id: 'PRESERVED', label: 'Preserved (Zero Loss)' },
              { id: 'RECOVERY', label: 'Retroactive Recovery' },
              { id: 'INTERFERENCE', label: 'Severe Interference' },
              { id: 'HYBRID', label: 'Hybrid Representation' },
            ].map((opt) => (
              <button
                key={opt.id}
                className={`prediction-option-btn ${predictionCategory === opt.id ? 'active' : ''}`}
                onClick={() => setPredictionCategory(opt.id)}
                style={{
                  background: predictionCategory === opt.id ? '#6366f1' : undefined,
                  borderColor: predictionCategory === opt.id ? '#a5b4fc' : undefined,
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <input
            type="text"
            placeholder="Hypothesis note..."
            value={hypothesisText}
            onChange={(e) => setHypothesisText(e.target.value)}
            style={{
              background: 'rgba(30, 41, 59, 0.8)',
              border: '1px solid rgba(129, 140, 248, 0.4)',
              borderRadius: '6px',
              color: '#f8fafc',
              padding: '0.35rem 0.6rem',
              fontSize: '0.78rem',
              width: '180px',
            }}
          />

          <button
            className="observatory-btn primary"
            onClick={handlePredictionSubmit}
            disabled={!predictionCategory || !activeSession}
          >
            Submit
          </button>
        </div>
      </div>

      {predictionFeedback && (
        <div style={{
          padding: '0.5rem 1rem',
          background: 'rgba(99, 102, 241, 0.15)',
          border: '1px solid #818cf8',
          borderRadius: '8px',
          fontSize: '0.82rem',
          color: '#e0e7ff',
        }}>
          <strong>Hypothesis Verification:</strong> {predictionFeedback}
        </div>
      )}

      {/* Memory State Trail (Timeline Scrubber) */}
      {activeSession && (
        <MemoryStateTrail
          snapshots={activeSession.snapshots}
          currentStep={currentStep}
          compareStep={compareStep}
          onSelectStep={setCurrentStep}
          onSelectCompareStep={setCompareStep}
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying(!isPlaying)}
          onStepForward={() => setCurrentStep((p) => Math.min(p + 1, activeSession.snapshots.length - 1))}
          onStepBackward={() => setCurrentStep((p) => Math.max(p - 1, 0))}
        />
      )}

      {/* Main Grid: Weather Map & What Changed */}
      <div className="observatory-grid">
        {/* Left: Synaptic Weather Map */}
        <div className="observatory-card">
          <div className="card-title-row">
            <h3 className="card-title">
              <span>Synaptic Weather Map (Step {currentStep})</span>
            </h3>
            {currentSnapshot && (
              <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                Event: <strong style={{ color: '#38bdf8' }}>{currentSnapshot.adaptation_event}</strong> | Norm: {currentSnapshot.matrix_norm.toFixed(3)}
              </span>
            )}
          </div>

          {currentSnapshot ? (
            <SynapticWeatherMap
              weatherMap={currentSnapshot.weather_map}
              dimension={dimension}
              onSelectSynapse={(row, col, weight) => {
                setSelectedSynapse({ row, col, weight })
                setNewSynapseWeight(weight)
                setSurgeryModalOpen(true)
              }}
            />
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
              Execute or load a session to inspect synaptic weather.
            </div>
          )}
        </div>

        {/* Right: What Changed? Panel */}
        <div className="observatory-card">
          <div className="card-title-row">
            <h3 className="card-title">
              <span>What Changed? (T{compareStep} ➔ T{currentStep})</span>
            </h3>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Differential State Analysis
            </span>
          </div>

          <ChangeDetectorPanel
            diff={diff}
            stepFrom={compareStep}
            stepTo={currentStep}
            isLoading={loadingDiff}
          />
        </div>
      </div>

      {/* Stability vs Plasticity Row */}
      <div className="observatory-card">
        <div className="card-title-row">
          <h3 className="card-title">
            <span>Stability vs Plasticity Dynamics (T{compareStep} ➔ T{currentStep})</span>
          </h3>
          <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
            Empirical Linear Algebraic Equilibrium
          </span>
        </div>

        <StabilityPlasticityView
          metrics={stabilityMetrics}
          isLoading={loadingMetrics}
        />
      </div>

      {/* Telemetry Adaptation Graph */}
      {activeSession && (
        <div className="observatory-card adaptation-chart-card">
          <div className="card-title-row">
            <h3 className="card-title">
              <span>Adaptation Telemetry Graph</span>
            </h3>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Continuous State Evolution Curve
            </span>
          </div>

          <AdaptationGraph
            snapshots={activeSession.snapshots}
            currentStep={currentStep}
            onSelectStep={setCurrentStep}
          />
        </div>
      )}

      {/* Synaptic Surgery Modal */}
      {surgeryModalOpen && selectedSynapse && (
        <div className="observatory-modal-overlay">
          <div className="observatory-modal-card">
            <div className="modal-header">
              <h3>Synaptic Surgery Intervention (Phase 15 Branch)</h3>
              <button className="modal-close-btn" onClick={() => setSurgeryModalOpen(false)}>✕</button>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
              Manually alter connection weight for synapse <strong>({selectedSynapse.row}, {selectedSynapse.col})</strong> at Step {currentStep}. This will branch continuous execution into an alternate timeline.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span>New Weight:</span>
              <input
                type="range"
                min="-1.5"
                max="1.5"
                step="0.05"
                value={newSynapseWeight}
                onChange={(e) => setNewSynapseWeight(parseFloat(e.target.value))}
                style={{ flex: 1, accentColor: '#6366f1' }}
              />
              <span style={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#38bdf8' }}>
                {newSynapseWeight.toFixed(2)}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="observatory-btn" onClick={() => setSurgeryModalOpen(false)}>Cancel</button>
              <button className="observatory-btn primary" onClick={handlePerformSurgery}>Execute Surgery Branch</button>
            </div>
          </div>
        </div>
      )}

      {/* Counterfactual Branch Modal */}
      {counterfactualModalOpen && (
        <div className="observatory-modal-overlay">
          <div className="observatory-modal-card">
            <div className="modal-header">
              <h3>Counterfactual Timeline Branch (Phase 16 Engine)</h3>
              <button className="modal-close-btn" onClick={() => setCounterfactualModalOpen(false)}>✕</button>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
              Branch the current session from Step {currentStep} under alternate plasticity parameters. The remainder of the stream will re-execute with these new conditions.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ width: '130px' }}>Altered Learning Rate:</span>
                <input
                  type="range"
                  min="0.05"
                  max="0.80"
                  step="0.05"
                  value={cfLearningRate}
                  onChange={(e) => setCfLearningRate(parseFloat(e.target.value))}
                  style={{ flex: 1, accentColor: '#6366f1' }}
                />
                <span style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{cfLearningRate.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ width: '130px' }}>Altered Decay Rate:</span>
                <input
                  type="range"
                  min="0.0"
                  max="0.20"
                  step="0.01"
                  value={cfDecayRate}
                  onChange={(e) => setCfDecayRate(parseFloat(e.target.value))}
                  style={{ flex: 1, accentColor: '#6366f1' }}
                />
                <span style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{cfDecayRate.toFixed(2)}</span>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="observatory-btn" onClick={() => setCounterfactualModalOpen(false)}>Cancel</button>
              <button className="observatory-btn primary" onClick={handlePerformCounterfactual}>Branch What-If Stream</button>
            </div>
          </div>
        </div>
      )}

      {/* Side-by-side Run Comparison Modal */}
      {compareModalOpen && (
        <div className="observatory-modal-overlay">
          <div className="observatory-modal-card" style={{ maxWidth: '720px' }}>
            <div className="modal-header">
              <h3>Side-by-Side Run Comparison</h3>
              <button className="modal-close-btn" onClick={() => setCompareModalOpen(false)}>✕</button>
            </div>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span>Compare Current Run With:</span>
              <select
                value={selectedCompareSessionId}
                onChange={(e) => setSelectedCompareSessionId(e.target.value)}
                style={{
                  background: 'rgba(30, 41, 59, 0.8)',
                  color: '#f8fafc',
                  padding: '0.4rem 0.6rem',
                  borderRadius: '6px',
                  border: '1px solid #6366f1',
                  flex: 1,
                }}
              >
                {sessionsList
                  .filter((s) => s.session_id !== activeSession?.session_id)
                  .map((s) => (
                    <option key={s.session_id} value={s.session_id}>
                      {s.name} ({s.session_id.substring(0, 8)})
                    </option>
                  ))}
              </select>
              <button className="observatory-btn primary" onClick={handleCompareSessions}>
                Calculate Divergence
              </button>
            </div>

            {comparisonResult && (
              <div style={{
                marginTop: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                background: 'rgba(15, 23, 42, 0.8)',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid rgba(71, 85, 105, 0.4)',
              }}>
                <div><strong>Final Frobenius Distance:</strong> <span style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{comparisonResult.final_frobenius_distance.toFixed(4)}</span></div>
                <div><strong>Stability Difference:</strong> <span style={{ color: '#34d399', fontFamily: 'monospace' }}>{(comparisonResult.stability_difference * 100).toFixed(1)}%</span></div>
                <div><strong>Plasticity Difference:</strong> <span style={{ color: '#ec4899', fontFamily: 'monospace' }}>{(comparisonResult.plasticity_difference * 100).toFixed(1)}%</span></div>
                <div style={{ fontStyle: 'italic', color: '#cbd5e1', fontSize: '0.85rem' }}>"{comparisonResult.narrative_conclusion}"</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
