import React, { useCallback, useEffect, useState } from 'react'
import type {
  StudioABComparison,
  StudioExperimentConfig,
  StudioExperimentNote,
  StudioExperimentResult,
  StudioExperimentTemplate,
  StudioGuidedJourney,
  StudioHistoryItem,
  StudioHypothesis,
  StudioSweepResult,
} from '../types'
import {
  branchStudioExperiment,
  compareStudioAB,
  exportStudioExperiment,
  getStudioExperiment,
  getStudioGuidedJourney,
  getStudioTemplates,
  listStudioHistory,
  runStudioExperiment,
  runStudioSweep,
  saveStudioNotes,
} from '../api'
import { ExperimentBuilderControls } from '../components/ExperimentBuilderControls'
import { MemoryExperimentGraph } from '../components/MemoryExperimentGraph'
import { ComputationPipelineVisualizer } from '../components/ComputationPipelineVisualizer'
import { PredictionChallengeModal } from '../components/PredictionChallengeModal'
import { ExperimentResultView } from '../components/ExperimentResultView'
import { ABComparisonView } from '../components/ABComparisonView'
import { ParameterSweepChart } from '../components/ParameterSweepChart'
import { GuidedJourneyModal } from '../components/GuidedJourneyModal'
import { ExperimentNotesWidget } from '../components/ExperimentNotesWidget'
import '../studio.css'

interface ExperimentStudioWorkspaceProps {
  onNavigateToWorkspace?: (workspaceId: string) => void
}

const DEFAULT_CONFIG: StudioExperimentConfig = {
  name: 'Interference Impact on Working Memory',
  experiment_type: 'INTERFERENCE',
  seed: 42,
  d: 16,
  decay: 0.05,
  update_strength: 1.0,
  mechanism: 'hebbian',
  concept_a: 'cat',
  value_a: 'whiskers',
  importance_a: 1.0,
  strength_a: 1.0,
  interfering_concept: 'tiger',
  interfering_value: 'stripes',
  interfering_strength: 0.8,
  intervening_steps: 1,
  surgery_target_row: 0,
  surgery_target_col: 0,
  surgery_action: 'zero',
  cf_param_name: 'decay',
  cf_param_value: 0.3,
  decay_cycles: 5,
  comparison_concept: 'dog',
  comparison_value: 'bark',
  controlled_variables: ['seed', 'd', 'mechanism', 'concept_a', 'value_a'],
}

export const ExperimentStudioWorkspace: React.FC<ExperimentStudioWorkspaceProps> = () => {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'BUILDER' | 'AB' | 'SWEEP' | 'HISTORY'>('BUILDER')

  // Main Builder State
  const [config, setConfig] = useState<StudioExperimentConfig>(DEFAULT_CONFIG)
  const [oneVariableLock, setOneVariableLock] = useState<boolean>(false)
  const [hypothesisText, setHypothesisText] = useState<string>(
    'I predict intervening writes will degrade recall due to shared synaptic weights.'
  )
  const [predictedOutcome, setPredictedOutcome] = useState<string>('RETENTION_DROP')
  const [predictionChoice, setPredictionChoice] = useState<string | null>('B')
  const [isChallengeModalOpen, setIsChallengeModalOpen] = useState<boolean>(false)

  // Execution & Results
  const [isRunning, setIsRunning] = useState<boolean>(false)
  const [currentResult, setCurrentResult] = useState<StudioExperimentResult | null>(null)
  const [currentNotes, setCurrentNotes] = useState<StudioExperimentNote>({
    question: 'Can temporary synaptic changes preserve a memory despite intervening writes?',
    hypothesis: 'Stronger interference modifies shared weights, leading to degraded recall fidelity.',
    observation: 'Interfering write reduced cosine fidelity.',
    conclusion: 'In this Hebbian model, overlapping neural patterns cause synaptic cross-talk.',
  })

  // Templates & Guided Journey
  const [templates, setTemplates] = useState<StudioExperimentTemplate[]>([])
  const [guidedJourney, setGuidedJourney] = useState<StudioGuidedJourney | null>(null)
  const [isJourneyModalOpen, setIsJourneyModalOpen] = useState<boolean>(false)

  // A/B Comparison State
  const [abConfigA, setAbConfigA] = useState<StudioExperimentConfig>({
    ...DEFAULT_CONFIG,
    name: 'Condition A (Low Interference)',
    interfering_strength: 0.2,
  })
  const [abConfigB, setAbConfigB] = useState<StudioExperimentConfig>({
    ...DEFAULT_CONFIG,
    name: 'Condition B (High Interference)',
    interfering_strength: 1.4,
  })
  const [abComparison, setAbComparison] = useState<StudioABComparison | null>(null)
  const [isAbRunning, setIsAbRunning] = useState<boolean>(false)

  // Parameter Sweep State
  const [sweepParam, setSweepParam] = useState<string>('interfering_strength')
  const [sweepResult, setSweepResult] = useState<StudioSweepResult | null>(null)
  const [isSweepRunning, setIsSweepRunning] = useState<boolean>(false)

  // History State
  const [historyList, setHistoryList] = useState<StudioHistoryItem[]>([])

  // Initial Data Loader
  const loadInitialData = useCallback(async () => {
    try {
      const [tplRes, jrnRes, histRes] = await Promise.all([
        getStudioTemplates(),
        getStudioGuidedJourney(),
        listStudioHistory(),
      ])
      setTemplates(tplRes.templates)
      setGuidedJourney(jrnRes.journey)
      setHistoryList(histRes.history)

      if (histRes.history.length > 0) {
        const latestId = histRes.history[0].experiment_id
        const detailRes = await getStudioExperiment(latestId)
        setCurrentResult(detailRes.experiment)
        setCurrentNotes(detailRes.notes)
      }
    } catch (err) {
      console.error('Failed to load initial studio data:', err)
    }
  }, [])

  useEffect(() => {
    loadInitialData()
  }, [loadInitialData])

  // Execute Main Experiment
  const handleExecuteExperiment = async () => {
    setIsRunning(true)
    try {
      const hypo: StudioHypothesis = {
        hypothesis_text: hypothesisText,
        predicted_outcome: predictedOutcome,
        predicted_challenge_choice: predictionChoice,
      }

      const res = await runStudioExperiment({
        config,
        hypothesis: hypo,
        notes: currentNotes,
      })
      setCurrentResult(res.result)
      const hist = await listStudioHistory()
      setHistoryList(hist.history)
    } catch (err) {
      console.error('Experiment execution failed:', err)
    } finally {
      setIsRunning(false)
      setIsChallengeModalOpen(false)
    }
  }

  // Pre-Run Prediction Challenge Trigger
  const handleTriggerRun = () => {
    setIsChallengeModalOpen(true)
  }

  // Template Quick-Loader
  const handleApplyTemplate = (tpl: StudioExperimentTemplate) => {
    setConfig((prev) => ({
      ...prev,
      name: tpl.title,
      experiment_type: tpl.type,
      ...tpl.config,
    }))
    setHypothesisText(tpl.recommended_question)
  }

  // Apply step from guided journey
  const handleApplyJourneyStep = (stepIdx: number) => {
    if (stepIdx <= 3) {
      setConfig((p) => ({ ...p, experiment_type: 'ENCODING', concept_a: 'cat', value_a: 'whiskers' }))
    } else {
      setConfig((p) => ({ ...p, experiment_type: 'INTERFERENCE', concept_a: 'cat', value_a: 'whiskers', interfering_concept: 'tiger', interfering_value: 'stripes' }))
    }
  }

  // A/B Run
  const handleRunAB = async () => {
    setIsAbRunning(true)
    try {
      const res = await compareStudioAB({
        config_a: abConfigA,
        config_b: abConfigB,
      })
      setAbComparison(res.comparison)
    } catch (err) {
      console.error('A/B Comparison failed:', err)
    } finally {
      setIsAbRunning(false)
    }
  }

  // Sweep Run
  const handleRunSweep = async () => {
    setIsSweepRunning(true)
    try {
      const res = await runStudioSweep({
        base_config: config,
        param_name: sweepParam,
      })
      setSweepResult(res.sweep)
    } catch (err) {
      console.error('Sweep execution failed:', err)
    } finally {
      setIsSweepRunning(false)
    }
  }

  // Duplicate & Branch
  const handleDuplicateBranch = async () => {
    if (!currentResult) return
    try {
      const res = await branchStudioExperiment({
        experiment_id: currentResult.experiment_id,
        modified_param: 'decay',
        new_value: 0.25,
      })
      setCurrentResult(res.result)
      setConfig(res.result.config)
      const hist = await listStudioHistory()
      setHistoryList(hist.history)
    } catch (err) {
      console.error('Branching failed:', err)
    }
  }

  // Save Notes
  const handleSaveNotes = async (updated: StudioExperimentNote) => {
    if (!currentResult) return
    await saveStudioNotes({
      experiment_id: currentResult.experiment_id,
      ...updated,
    })
    setCurrentNotes(updated)
  }

  // Export JSON
  const handleExport = async () => {
    if (!currentResult) return
    const bundle = await exportStudioExperiment(currentResult.experiment_id)
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${currentResult.experiment_id}-reproducible-experiment.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="studio-workspace-container">
      {/* Control Room Header */}
      <div className="studio-header-strip">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.2))',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
          }}>
            🔬
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.04em' }}>
                EXPERIMENT STUDIO
              </h2>
              <span className="studio-badge-live">
                <span className="studio-live-dot" />
                DETERMINISTIC NUMPY ENGINE
              </span>
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '2px' }}>
              Build, predict, run, inspect, and compare your own synaptic plasticity experiments.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {guidedJourney && (
            <button
              onClick={() => setIsJourneyModalOpen(true)}
              style={{
                padding: '6px 12px',
                background: 'rgba(245, 158, 11, 0.15)',
                border: '1px solid #f59e0b',
                borderRadius: '6px',
                color: '#fbbf24',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span>🧭</span> GUIDED JOURNEY
            </button>
          )}

          <button
            onClick={handleTriggerRun}
            disabled={isRunning}
            style={{
              padding: '7px 18px',
              background: isRunning ? 'rgba(56, 189, 248, 0.3)' : 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              border: 'none',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem',
              fontWeight: 800,
              cursor: isRunning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 0 16px rgba(14, 165, 233, 0.4)',
            }}
          >
            <span>▶</span> {isRunning ? 'RUNNING...' : 'RUN EXPERIMENT'}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="studio-nav-tabs">
        <button
          className={`studio-tab-btn ${activeTab === 'BUILDER' ? 'active' : ''}`}
          onClick={() => setActiveTab('BUILDER')}
        >
          <span>🔬</span> EXPERIMENT BUILDER & RESULTS
        </button>
        <button
          className={`studio-tab-btn ${activeTab === 'AB' ? 'active' : ''}`}
          onClick={() => setActiveTab('AB')}
        >
          <span>⚖</span> A/B COMPARISON MODE
        </button>
        <button
          className={`studio-tab-btn ${activeTab === 'SWEEP' ? 'active' : ''}`}
          onClick={() => setActiveTab('SWEEP')}
        >
          <span>📈</span> PARAMETER SWEEP
        </button>
        <button
          className={`studio-tab-btn ${activeTab === 'HISTORY' ? 'active' : ''}`}
          onClick={() => setActiveTab('HISTORY')}
        >
          <span>📜</span> EXPERIMENT ARCHIVE ({historyList.length})
        </button>
      </div>

      {/* Tab 1: Builder & Results */}
      {activeTab === 'BUILDER' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Starter Templates Strip */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto', paddingBottom: '4px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', whiteSpace: 'nowrap' }}>
              TEMPLATES:
            </span>
            {templates.map((tpl) => (
              <button
                key={tpl.id}
                onClick={() => handleApplyTemplate(tpl)}
                style={{
                  padding: '4px 10px',
                  background: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '6px',
                  color: '#cbd5e1',
                  fontSize: '0.74rem',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                }}
              >
                {tpl.title}
              </button>
            ))}
          </div>

          {/* Master Canvas Grid */}
          <div className="studio-canvas-layout">
            {/* Left Column: Parameter Rails */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <ExperimentBuilderControls
                config={config}
                onChangeConfig={setConfig}
                oneVariableLock={oneVariableLock}
                onToggleOneVariableLock={() => setOneVariableLock((p) => !p)}
                disabled={isRunning}
              />

              {/* Hypothesis Box */}
              <div style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
              }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#fbbf24', letterSpacing: '0.04em' }}>
                  🎯 PRE-EXPERIMENT HYPOTHESIS
                </span>
                <textarea
                  rows={3}
                  value={hypothesisText}
                  onChange={(e) => setHypothesisText(e.target.value)}
                  placeholder="State your prediction prior to execution..."
                  style={{
                    width: '100%',
                    background: '#090d16',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#f8fafc',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    fontSize: '0.78rem',
                    boxSizing: 'border-box',
                    resize: 'vertical',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Expected Outcome:</span>
                  <select
                    value={predictedOutcome}
                    onChange={(e) => setPredictedOutcome(e.target.value)}
                    style={{ background: '#0f172a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#38bdf8', padding: '3px 6px', borderRadius: '4px', fontSize: '0.72rem' }}
                  >
                    <option value="RETENTION_DROP">RETENTION_DROP</option>
                    <option value="STABILITY_PRESERVED">STABILITY_PRESERVED</option>
                    <option value="RECALL_IMPROVED">RECALL_IMPROVED</option>
                    <option value="CROSSTALK_INCREASE">CROSSTALK_INCREASE</option>
                    <option value="UNSURE">UNSURE</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Right Column: Graph, Pipeline & Quantitative Results */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Causality Graph */}
              <MemoryExperimentGraph
                activeStage={currentResult?.experiment_graph_active_stage || 'STATE_UPDATE'}
              />

              {/* Execution Pipeline */}
              {currentResult && (
                <ComputationPipelineVisualizer
                  steps={currentResult.pipeline_steps}
                  isRunning={isRunning}
                />
              )}

              {/* Measured Results */}
              {currentResult ? (
                <ExperimentResultView
                  result={currentResult}
                  onDuplicateBranch={handleDuplicateBranch}
                  onExport={handleExport}
                />
              ) : (
                <div style={{
                  padding: '3rem',
                  textAlign: 'center',
                  background: 'rgba(15, 23, 42, 0.4)',
                  border: '1px dashed rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#64748b',
                }}>
                  Configure your variables on the left and click <strong>RUN EXPERIMENT</strong> to observe empirical outcomes.
                </div>
              )}

              {/* Notes Widget */}
              {currentResult && (
                <ExperimentNotesWidget
                  experimentId={currentResult.experiment_id}
                  notes={currentNotes}
                  onSaveNotes={handleSaveNotes}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: A/B Comparison Mode */}
      {activeTab === 'AB' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: '#f8fafc' }}>
                CONTROLLED A/B EXPERIMENTAL COMPARISON
              </h3>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                Run Baseline (A) and Treatment (B) concurrently to isolate the causal effect of independent variables.
              </div>
            </div>
            <button
              onClick={handleRunAB}
              disabled={isAbRunning}
              style={{
                padding: '6px 16px',
                background: 'linear-gradient(135deg, #38bdf8, #2563eb)',
                border: 'none',
                borderRadius: '6px',
                color: '#f8fafc',
                fontWeight: 700,
                fontSize: '0.8rem',
                cursor: isAbRunning ? 'not-allowed' : 'pointer',
              }}
            >
              {isAbRunning ? 'EVALUATING...' : '▶ RUN A/B EXPERIMENT'}
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#94a3b8' }}>Configuration A (Baseline)</h4>
              <ExperimentBuilderControls
                config={abConfigA}
                onChangeConfig={setAbConfigA}
                oneVariableLock={false}
                onToggleOneVariableLock={() => {}}
              />
            </div>
            <div>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#38bdf8' }}>Configuration B (Treatment)</h4>
              <ExperimentBuilderControls
                config={abConfigB}
                onChangeConfig={setAbConfigB}
                oneVariableLock={false}
                onToggleOneVariableLock={() => {}}
              />
            </div>
          </div>

          {abComparison && <ABComparisonView comparison={abComparison} />}
        </div>
      )}

      {/* Tab 3: Parameter Sweep */}
      {activeTab === 'SWEEP' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '8px',
            padding: '1rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>
                  Sweep Target Parameter:
                </span>
                <select
                  value={sweepParam}
                  onChange={(e) => setSweepParam(e.target.value)}
                  style={{
                    marginLeft: '0.5rem',
                    background: '#090d16',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#38bdf8',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                  }}
                >
                  <option value="interfering_strength">interfering_strength (0.0 → 1.5)</option>
                  <option value="decay">decay λ (0.0 → 0.75)</option>
                  <option value="update_strength">update_strength η (0.2 → 2.0)</option>
                  <option value="decay_cycles">decay_cycles (0 → 12)</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleRunSweep}
              disabled={isSweepRunning}
              style={{
                padding: '6px 16px',
                background: '#38bdf8',
                border: 'none',
                borderRadius: '6px',
                color: '#030712',
                fontWeight: 800,
                fontSize: '0.8rem',
                cursor: isSweepRunning ? 'not-allowed' : 'pointer',
              }}
            >
              {isSweepRunning ? 'SWEEPING...' : '▶ EXECUTE 1D SWEEP'}
            </button>
          </div>

          {sweepResult && <ParameterSweepChart sweep={sweepResult} />}
        </div>
      )}

      {/* Tab 4: History */}
      {activeTab === 'HISTORY' && (
        <div style={{
          background: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '1.25rem',
        }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.95rem', fontWeight: 800, color: '#f8fafc' }}>
            STORED EXPERIMENTS ({historyList.length})
          </h3>

          <table className="studio-metrics-table">
            <thead>
              <tr>
                <th>EXPERIMENT ID</th>
                <th>NAME</th>
                <th>TYPE</th>
                <th>CUE</th>
                <th>FIDELITY</th>
                <th>Δ FIDELITY</th>
                <th>HYPOTHESIS</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {historyList.map((item) => (
                <tr key={item.experiment_id}>
                  <td style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{item.experiment_id}</td>
                  <td style={{ fontWeight: 600 }}>{item.name}</td>
                  <td>{item.experiment_type}</td>
                  <td>{item.concept_a}</td>
                  <td>{item.fidelity.toFixed(4)}</td>
                  <td>
                    <span className={`studio-delta-badge ${item.delta_fidelity < -0.02 ? 'negative' : 'neutral'}`}>
                      {item.delta_fidelity > 0 ? '+' : ''}{item.delta_fidelity.toFixed(3)}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.72rem', color: item.hypothesis_status === 'SUPPORTED' ? '#34d399' : '#fbbf24' }}>
                      {item.hypothesis_status || 'N/A'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={async () => {
                        const detail = await getStudioExperiment(item.experiment_id)
                        setCurrentResult(detail.experiment)
                        setConfig(detail.experiment.config)
                        setCurrentNotes(detail.notes)
                        setActiveTab('BUILDER')
                      }}
                      style={{
                        padding: '3px 8px',
                        background: 'rgba(56, 189, 248, 0.15)',
                        border: '1px solid #38bdf8',
                        borderRadius: '4px',
                        color: '#38bdf8',
                        fontSize: '0.7rem',
                        cursor: 'pointer',
                      }}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pre-Run Prediction Challenge Modal */}
      <PredictionChallengeModal
        isOpen={isChallengeModalOpen}
        questionText={hypothesisText}
        selectedChoice={predictionChoice}
        onSelectChoice={setPredictionChoice}
        onConfirmRun={handleExecuteExperiment}
        onClose={() => setIsChallengeModalOpen(false)}
      />

      {/* Guided Journey Modal */}
      {guidedJourney && (
        <GuidedJourneyModal
          isOpen={isJourneyModalOpen}
          journey={guidedJourney}
          onClose={() => setIsJourneyModalOpen(false)}
          onApplyStepConfig={handleApplyJourneyStep}
        />
      )}
    </div>
  )
}
