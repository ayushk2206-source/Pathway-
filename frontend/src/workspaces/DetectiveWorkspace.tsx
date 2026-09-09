import React, { useState, useEffect } from 'react'
import type {
  Experiment,
  Investigation,
  CandidateHypothesis,
  MemoryAutopsy,
  SensitivityRecord,
  MinimumIntervention,
  RobustnessEvaluation,
  DiscoveryObservation,
  NotebookEntry,
  InvestigationScorecard,
} from '../types'
import {
  parseDetectiveQuestion,
  runInvestigation,
  executeDetectiveTest,
  fetchAutopsy,
  fetchSensitivity,
  fetchDiscoveryFeed,
  listInvestigations,
  reproduceInvestigation,
  fetchScorecard,
  fetchNotebook,
  saveNotebookEntry,
  deleteNotebookEntry,
} from '../api'

interface DetectiveWorkspaceProps {
  experiment: Experiment | null
  currentStep: number
  onStepChange?: (step: number) => void
  selectedMemoryId?: string | null
  onSelectMemory?: (id: string) => void
  onViewEvidence?: (title: string, details: Record<string, unknown>) => void
}

export const DetectiveWorkspace: React.FC<DetectiveWorkspaceProps> = ({
  experiment,
  selectedMemoryId,
  onSelectMemory,
  onViewEvidence,
}) => {
  const [question, setQuestion] = useState('Why did Memory obj_A weaken at step 2?')
  const [targetMemory, setTargetMemory] = useState(selectedMemoryId || 'obj_A')
  const [parsedIntent, setParsedIntent] = useState<string | null>('INTERFERENCE')
  const [investigation, setInvestigation] = useState<Investigation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [activeTab, setActiveTab] = useState<'evidence' | 'hypotheses' | 'counterfactual' | 'autopsy' | 'discovery' | 'notebook'>('hypotheses')
  const [selectedHypothesis, setSelectedHypothesis] = useState<CandidateHypothesis | null>(null)

  // Sub-data states
  const [autopsy, setAutopsy] = useState<MemoryAutopsy | null>(null)
  const [sensitivity, setSensitivity] = useState<SensitivityRecord | null>(null)
  const [minIntervention, setMinIntervention] = useState<MinimumIntervention | null>(null)
  const [robustness, setRobustness] = useState<RobustnessEvaluation | null>(null)
  const [discoveries, setDiscoveries] = useState<DiscoveryObservation[]>([])
  const [notebookEntries, setNotebookEntries] = useState<NotebookEntry[]>([])
  const [savedInvestigations, setSavedInvestigations] = useState<Investigation[]>([])

  // Note-taking inputs
  const [noteTitle, setNoteTitle] = useState('')
  const [noteContent, setNoteContent] = useState('')
  const [noteTags, setNoteTags] = useState('crosstalk, proof')

  // Scorecard / Diff modals
  const [showScorecardModal, setShowScorecardModal] = useState(false)
  const [scorecard, setScorecard] = useState<InvestigationScorecard | null>(null)
  const [reproducing, setReproducing] = useState(false)

  // Sync target memory if parent changes selection
  useEffect(() => {
    if (selectedMemoryId) {
      setTargetMemory(selectedMemoryId)
    }
  }, [selectedMemoryId])

  // Fetch initial feed & notebook entries when experiment changes
  useEffect(() => {
    if (experiment) {
      loadDiscoveryFeed()
      loadNotebook()
      loadSavedInvestigations()
    }
  }, [experiment?.experiment_id])

  const loadDiscoveryFeed = async () => {
    if (!experiment) return
    try {
      const res = await fetchDiscoveryFeed(experiment.experiment_id)
      setDiscoveries(res.discoveries || [])
    } catch {
      // Non-critical background scan
    }
  }

  const loadNotebook = async () => {
    if (!experiment) return
    try {
      const res = await fetchNotebook(experiment.experiment_id)
      setNotebookEntries(res.entries || [])
    } catch {
      // Non-critical
    }
  }

  const loadSavedInvestigations = async () => {
    if (!experiment) return
    try {
      const res = await listInvestigations(experiment.experiment_id)
      setSavedInvestigations(res.investigations || [])
    } catch {
      // Non-critical
    }
  }

  const updateTargetMemory = (id: string) => {
    setTargetMemory(id)
    onSelectMemory?.(id)
  }

  const handleOpenScorecard = async () => {
    if (!investigation) return
    try {
      const sc = await fetchScorecard(investigation.investigation_id)
      setScorecard(sc)
    } catch {
      // Retain existing scorecard
    }
    setShowScorecardModal(true)
  }

  const handleQuestionChange = async (q: string) => {
    setQuestion(q)
    try {
      const parsed = await parseDetectiveQuestion(q)
      setParsedIntent(parsed.intent)
      if (parsed.target_memory) {
        updateTargetMemory(parsed.target_memory)
      }
    } catch {
      // Continue without breaking UI
    }
  }

  const handleRunInvestigation = async () => {
    if (!experiment) return
    setLoading(true)
    setError(null)
    try {
      const inv = await runInvestigation({
        experiment_id: experiment.experiment_id,
        question,
        target_memory: targetMemory || undefined,
        execute_tests: true,
      })
      setInvestigation(inv)
      if (inv.candidate_hypotheses?.length) {
        setSelectedHypothesis(inv.candidate_hypotheses[0])
      }
      if (inv.scorecard) {
        setScorecard(inv.scorecard)
      }
      await loadSavedInvestigations()
      // Also automatically trigger autopsy & sensitivity in the background
      handleLoadAutopsy()
      handleLoadSensitivity()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleLoadAutopsy = async () => {
    if (!experiment) return
    try {
      const res = await fetchAutopsy(experiment.experiment_id, targetMemory)
      setAutopsy(res.autopsy)
    } catch {
      // Non-critical
    }
  }

  const handleLoadSensitivity = async () => {
    if (!experiment) return
    try {
      const res = await fetchSensitivity(experiment.experiment_id, targetMemory)
      setSensitivity(res.sensitivity)
      setMinIntervention(res.minimum_intervention)
      setRobustness(res.robustness)
    } catch {
      // Non-critical
    }
  }

  const handleExecuteSingleTest = async (hyp: CandidateHypothesis) => {
    if (!experiment || !investigation) return
    setLoading(true)
    try {
      const res = await executeDetectiveTest({
        experiment_id: experiment.experiment_id,
        hypothesis_id: hyp.hypothesis_id,
        test_design: {
          hypothesis_id: hyp.hypothesis_id,
          description: hyp.required_test,
          intervention_type: 'remove_event',
          target_timestep: 1,
          target_event_id: 'e0001',
          target_memory: targetMemory,
        },
      })
      // Update hypothesis in list
      const updated = investigation.candidate_hypotheses.map((h) =>
        h.hypothesis_id === hyp.hypothesis_id ? res.updated_hypothesis : h
      )
      setInvestigation({
        ...investigation,
        candidate_hypotheses: updated,
        results: [...investigation.results, res.test_result],
      })
      setSelectedHypothesis(res.updated_hypothesis)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleReproduce = async () => {
    if (!investigation) return
    setReproducing(true)
    try {
      const repro = await reproduceInvestigation(investigation.investigation_id)
      setInvestigation(repro)
      await loadSavedInvestigations()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setReproducing(false)
    }
  }

  const handleSaveNote = async () => {
    if (!experiment || !noteContent.trim()) return
    try {
      const tags = noteTags.split(',').map((t) => t.trim()).filter(Boolean)
      const note = await saveNotebookEntry({
        experiment_id: experiment.experiment_id,
        title: noteTitle.trim() || `Forensic Note on ${targetMemory}`,
        content: noteContent.trim(),
        linked_investigation_id: investigation?.investigation_id,
        tags,
      })
      setNotebookEntries([note, ...notebookEntries])
      setNoteTitle('')
      setNoteContent('')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const handleDeleteNote = async (entryId: string) => {
    if (!experiment) return
    try {
      await deleteNotebookEntry(experiment.experiment_id, entryId)
      setNotebookEntries(notebookEntries.filter((e) => e.entry_id !== entryId))
    } catch {
      // Non-critical
    }
  }

  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>MEMORY DETECTIVE · OFFLINE</h3>
        <p>No active experiment substrate detected. Please load or run an experiment to begin forensic hypothesis testing.</p>
      </div>
    )
  }

  const questionsSuggestions = [
    'Why did Memory obj_A weaken at step 2?',
    'Why did Memory obj_B survive despite conflict?',
    'Which event caused the greatest state transition?',
    'Why did the counterfactual branch diverge here?',
    'Did passive decay cause the loss of Memory obj_C?',
  ]

  const activeResult = investigation?.results.find(
    (r) => r.hypothesis_id === selectedHypothesis?.hypothesis_id
  ) || investigation?.results[0]

  return (
    <div className="detective-workspace">
      {/* Top Banner: Question Formulation */}
      <section className="detective-header-card">
        <div className="detective-title-row">
          <div className="title-block">
            <span className="badge-agent-primary">FORENSIC REASONING INSTRUMENT</span>
            <h2>Memory Detective &amp; Hypothesis Engine</h2>
            <p className="subtitle">
              Strictly grounded empirical investigation: Question &rarr; Observable Evidence &rarr; Competing Hypotheses &rarr; Counterfactual Proof
            </p>
          </div>
          <div className="telemetry-pill-group">
            <span className="telemetry-pill">
              INTENT: <strong className="cyan">{parsedIntent || 'INTERFERENCE'}</strong>
            </span>
            <span className="telemetry-pill">
              TARGET: <strong className="amber">{targetMemory}</strong>
            </span>
            <span className="telemetry-pill">
              EPISTEMIC RULE: <strong className="emerald">NEVER INVENT AN EXPLANATION</strong>
            </span>
          </div>
        </div>

        {/* Interactive Query Input */}
        <div className="detective-query-bar">
          <div className="input-prefix">QUESTION:</div>
          <input
            type="text"
            className="detective-input"
            value={question}
            onChange={(e) => handleQuestionChange(e.target.value)}
            placeholder="Ask why a memory formed, survived, or degraded..."
          />
          <div className="target-input-box">
            <span className="target-label">TARGET MEMORY:</span>
            <input
              type="text"
              className="target-input"
              value={targetMemory}
              onChange={(e) => updateTargetMemory(e.target.value)}
              placeholder="e.g. obj_A"
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleRunInvestigation}
            disabled={loading}
          >
            {loading ? 'INVESTIGATING...' : 'INVESTIGATE'}
          </button>
        </div>

        {/* Question Suggestions Chips */}
        <div className="chip-row">
          <span className="chip-label">COMMON INQUIRIES:</span>
          {questionsSuggestions.map((q, idx) => (
            <button
              key={idx}
              className="suggestion-chip"
              onClick={() => handleQuestionChange(q)}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Saved Past Investigations Chips */}
        {savedInvestigations.length > 0 && (
          <div className="chip-row" style={{ marginTop: '6px' }}>
            <span className="chip-label">PAST CASES ({savedInvestigations.length}):</span>
            {savedInvestigations.slice(0, 5).map((inv) => (
              <button
                key={inv.investigation_id}
                className="suggestion-chip"
                style={{ borderColor: 'var(--accent-cyan)' }}
                onClick={() => {
                  setInvestigation(inv)
                  setQuestion(inv.question)
                  if (inv.target_memory) updateTargetMemory(inv.target_memory)
                  if (inv.scorecard) setScorecard(inv.scorecard)
                }}
                title={inv.question}
              >
                CASE #{inv.investigation_id.slice(-6)}: {inv.intent}
              </button>
            ))}
          </div>
        )}
      </section>

      {error && (
        <div className="alert-box alert-error">
          <span>Error during forensic test: {error}</span>
          <button className="btn-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Main Tabs Navigation */}
      <div className="detective-tabs">
        <button
          className={`tab-btn ${activeTab === 'hypotheses' ? 'active' : ''}`}
          onClick={() => setActiveTab('hypotheses')}
        >
          1. COMPETING HYPOTHESES ({investigation?.candidate_hypotheses.length || 0})
        </button>
        <button
          className={`tab-btn ${activeTab === 'evidence' ? 'active' : ''}`}
          onClick={() => setActiveTab('evidence')}
        >
          2. OBSERVABLE EVIDENCE ({investigation?.observations.length || 0})
        </button>
        <button
          className={`tab-btn ${activeTab === 'counterfactual' ? 'active' : ''}`}
          onClick={() => setActiveTab('counterfactual')}
        >
          3. COUNTERFACTUAL PROOF &amp; SENSITIVITY
        </button>
        <button
          className={`tab-btn ${activeTab === 'autopsy' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('autopsy')
            if (!autopsy) handleLoadAutopsy()
          }}
        >
          4. MEMORY AUTOPSY (7 QUESTIONS)
        </button>
        <button
          className={`tab-btn ${activeTab === 'discovery' ? 'active' : ''}`}
          onClick={() => setActiveTab('discovery')}
        >
          5. DISCOVERY FEED ({discoveries.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'notebook' ? 'active' : ''}`}
          onClick={() => setActiveTab('notebook')}
        >
          6. RESEARCH NOTEBOOK ({notebookEntries.length})
        </button>

        {investigation?.scorecard && (
          <button
            className="tab-btn highlight"
            onClick={handleOpenScorecard}
            style={{ marginLeft: 'auto' }}
          >
            ★ FORENSIC SCORECARD
          </button>
        )}
      </div>

      {/* Tab 1: Competing Hypotheses */}
      {activeTab === 'hypotheses' && (
        <div className="tab-pane">
          {!investigation ? (
            <div className="empty-panel">
              <h4>NO ACTIVE INVESTIGATION</h4>
              <p>Type a question and click <strong>INVESTIGATE</strong> to construct competing hypotheses from measured state vectors.</p>
            </div>
          ) : (
            <div className="hypotheses-grid">
              {investigation.candidate_hypotheses.map((hyp) => {
                const isSelected = selectedHypothesis?.hypothesis_id === hyp.hypothesis_id
                const isSupported =
                  hyp.status === 'COUNTERFACTUALLY_SUPPORTED' ||
                  hyp.classification === 'SUPPORTED'
                const isCorrelated = hyp.status === 'CORRELATED'
                const isRefuted =
                  hyp.status === 'UNSUPPORTED' ||
                  hyp.status === 'CONTRADICTED' ||
                  hyp.classification === 'REFUTED'

                return (
                  <div
                    key={hyp.hypothesis_id}
                    className={`hypothesis-card ${isSelected ? 'selected' : ''} ${
                      isSupported ? 'card-supported' : isRefuted ? 'card-refuted' : ''
                    }`}
                    onClick={() => setSelectedHypothesis(hyp)}
                  >
                    <div className="card-header">
                      <span className="hyp-id-badge">{hyp.hypothesis_id}</span>
                      {hyp.is_primary && <span className="primary-pill">PRIMARY EXPLANATION</span>}
                      <span
                        className={`status-badge ${
                          isSupported
                            ? 'emerald-glow'
                            : isCorrelated
                            ? 'amber-glow'
                            : isRefuted
                            ? 'rose-glow'
                            : 'cyan-glow'
                        }`}
                      >
                        {hyp.status}
                      </span>
                    </div>

                    <h4 className="hyp-statement">{hyp.statement}</h4>

                    <div className="hyp-mechanism">
                      MECHANISM: <code>{hyp.mechanism}</code>
                    </div>

                    <div className="evidence-section">
                      <div className="evidence-col">
                        <span className="col-title green">SUPPORTING EVIDENCE:</span>
                        {hyp.supporting_evidence.length === 0 ? (
                          <span className="muted-text">None observed</span>
                        ) : (
                          <ul>
                            {hyp.supporting_evidence.map((ev, i) => (
                              <li key={i}>{ev}</li>
                            ))}
                          </ul>
                        )}
                      </div>

                      {hyp.contradicting_evidence.length > 0 && (
                        <div className="evidence-col">
                          <span className="col-title red">CONTRADICTING EVIDENCE:</span>
                          <ul>
                            {hyp.contradicting_evidence.map((ev, i) => (
                              <li key={i}>{ev}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="test-box">
                      <span className="test-label">COUNTERFACTUAL TEST:</span>
                      <p>{hyp.required_test}</p>
                    </div>

                    <div className="card-footer">
                      <div className="metric-score">
                        CONFIDENCE: <strong>{(hyp.data_quality * 100).toFixed(0)}%</strong>
                      </div>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleExecuteSingleTest(hyp)
                        }}
                      >
                        RUN TEST
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Observable Evidence */}
      {activeTab === 'evidence' && (
        <div className="tab-pane">
          <div className="card full-width">
            <h3>Hard Empirical Evidence (Zero Hallucinations)</h3>
            <p className="subtitle">
              Derived directly from mathematical state vectors and circular convolution readouts:
            </p>

            {(!investigation || investigation.observations.length === 0) ? (
              <p className="muted-text">No observations extracted yet. Run an investigation to inspect metrics.</p>
            ) : (
              <table className="evidence-table">
                <thead>
                  <tr>
                    <th>METRIC</th>
                    <th>TARGET</th>
                    <th>BASELINE</th>
                    <th>OBSERVED</th>
                    <th>DELTA</th>
                    <th>CUE OVERLAP</th>
                    <th>COINCIDING EVENTS</th>
                    <th>SUMMARY</th>
                    <th>PROVENANCE</th>
                  </tr>
                </thead>
                <tbody>
                  {investigation.observations.map((obs) => {
                    const deltaPositive = obs.delta > 0
                    return (
                      <tr key={obs.observation_id}>
                        <td><code>{obs.metric_name}</code></td>
                        <td><strong>{obs.target_memory || 'Substrate'}</strong></td>
                        <td>{obs.initial_value.toFixed(4)}</td>
                        <td>{obs.final_value.toFixed(4)}</td>
                        <td className={deltaPositive ? 'green' : 'red'}>
                          {obs.delta > 0 ? `+${obs.delta.toFixed(4)}` : obs.delta.toFixed(4)}
                        </td>
                        <td>
                          {obs.cue_similarity !== null && obs.cue_similarity !== undefined
                            ? obs.cue_similarity.toFixed(4)
                            : 'N/A'}
                        </td>
                        <td>
                          {obs.relevant_events.length > 0 ? (
                            obs.relevant_events.map((ev, i) => (
                              <span key={i} className="mini-tag">{ev}</span>
                            ))
                          ) : (
                            <span className="muted-text">—</span>
                          )}
                        </td>
                        <td>{obs.summary}</td>
                        <td>
                          {onViewEvidence && (
                            <button
                              className="btn btn-secondary btn-xs"
                              onClick={() =>
                                onViewEvidence(`Forensic Observation: ${obs.metric_name}`, {
                                  observation_id: obs.observation_id,
                                  target_memory: obs.target_memory,
                                  target_event: obs.target_event,
                                  metric_name: obs.metric_name,
                                  baseline: obs.initial_value,
                                  observed: obs.final_value,
                                  delta: obs.delta,
                                  cue_similarity: obs.cue_similarity,
                                  relevant_events: obs.relevant_events,
                                  competing_memories: obs.competing_memories,
                                  summary: obs.summary,
                                })
                              }
                            >
                              VIEW
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Counterfactual Proof & Sensitivity */}
      {activeTab === 'counterfactual' && (
        <div className="tab-pane">
          <div className="two-column-layout">
            {/* Left: Control vs Intervention Trajectories */}
            <div className="card">
              <h3>Control vs Intervention Trajectories</h3>
              <p className="subtitle">Verifiable proof of causal impact through event ablation replay:</p>

              {!activeResult ? (
                <div className="empty-panel">
                  <p className="muted-text">Run a test on a candidate hypothesis to view the trajectory divergence.</p>
                </div>
              ) : (
                <div className="trajectory-proof-box">
                  <div className="verdict-banner">
                    <span className="verdict-tag">CAUSAL STATUS:</span>
                    <strong className={
                      activeResult.causal_support === 'COUNTERFACTUALLY_SUPPORTED' ? 'green' : 'red'
                    }>
                      {activeResult.causal_support}
                    </strong>
                    <span className="delta-pill">
                      RECOVERY DELTA: <strong>{activeResult.recovery_delta > 0 ? `+${activeResult.recovery_delta.toFixed(4)}` : activeResult.recovery_delta.toFixed(4)}</strong>
                    </span>
                  </div>

                  <div className="trajectory-comparison-table">
                    <div className="table-header-row">
                      <span>STEP</span>
                      <span>CONTROL (BASE)</span>
                      <span>INTERVENTION (BRANCH)</span>
                      <span>DELTA</span>
                    </div>
                    {activeResult.control_trajectory.map((ctrlVal, idx) => {
                      const intvVal = activeResult.intervention_trajectory[idx] ?? ctrlVal
                      const d = intvVal - ctrlVal
                      const diverged = Math.abs(d) > 0.02
                      return (
                        <div key={idx} className={`table-row ${diverged ? 'diverged-row' : ''}`}>
                          <span>Step {idx}</span>
                          <span>{ctrlVal.toFixed(3)}</span>
                          <span className={diverged ? 'cyan' : ''}>{intvVal.toFixed(3)}</span>
                          <span className={d > 0.01 ? 'green' : d < -0.01 ? 'red' : 'muted-text'}>
                            {d > 0 ? `+${d.toFixed(3)}` : d.toFixed(3)}
                          </span>
                        </div>
                      )
                    })}
                  </div>

                  <div className="evidence-narrative-box">
                    <strong>FORENSIC EVIDENCE SUMMARY:</strong>
                    <p>{activeResult.evidence_summary}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Minimum Intervention & Sensitivity Ladder */}
            <div className="card">
              <div className="card-header-flex">
                <h3>Sensitivity &amp; Minimum Intervention</h3>
                <button className="btn btn-secondary btn-sm" onClick={handleLoadSensitivity}>
                  RE-EVALUATE
                </button>
              </div>
              <p className="subtitle">Smallest modification that produces an observable outcome change:</p>

              {minIntervention ? (
                <div className="min-intervention-display">
                  <div className="highlight-metric-card">
                    <span className="label">SMALLEST INTERVENTION TYPE:</span>
                    <strong className="cyan">{minIntervention.smallest_intervention_type}</strong>
                    <span className="sub">Threshold: {minIntervention.parameter_threshold} &bull; Effect: {minIntervention.effect_size.toFixed(4)}</span>
                    <p className="outcome-text">{minIntervention.target_outcome}</p>
                  </div>

                  {sensitivity && (
                    <div className="sensitivity-metrics-row">
                      <div className="sub-metric">
                        <span>EFFECT SIZE</span>
                        <strong>{sensitivity.effect_size.toFixed(4)}</strong>
                      </div>
                      <div className="sub-metric">
                        <span>ISOLATED CAUSE</span>
                        <strong className={sensitivity.isolated_cause ? 'green' : 'amber'}>
                          {sensitivity.isolated_cause ? 'YES (TRUE)' : 'NO (CROSS-TALK)'}
                        </strong>
                      </div>
                      <div className="sub-metric">
                        <span>DOWNSTREAM AFFECTED</span>
                        <strong>{sensitivity.downstream_affected_count} memories</strong>
                      </div>
                    </div>
                  )}

                  {robustness && (
                    <div className="robustness-box">
                      <span className="label">MULTI-VARIATION ROBUSTNESS:</span>
                      <strong className={robustness.classification === 'stable' ? 'green' : 'amber'}>
                        {robustness.classification.toUpperCase()}
                      </strong>
                      <span className="sub">
                        Persistence: {(robustness.persistence_rate * 100).toFixed(0)}% &bull; Variance: {robustness.variance.toFixed(5)}
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="empty-panel">
                  <p className="muted-text">Click Re-Evaluate to test perturbation ladders.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Memory Autopsy */}
      {activeTab === 'autopsy' && (
        <div className="tab-pane">
          <div className="card full-width">
            <div className="card-header-flex">
              <div>
                <h3>Memory Autopsy: Complete Lifecycle &amp; Failure Analysis</h3>
                <p className="subtitle">
                  Answering the 7 core questions: Formation, Reinforcement, Competition, Inflection, Failure, Survival, and Epistemic Proof.
                </p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={handleLoadAutopsy}>
                REFRESH AUTOPSY
              </button>
            </div>

            {!autopsy ? (
              <div className="empty-panel">
                <p className="muted-text">Loading autopsy metrics for Memory {targetMemory}...</p>
              </div>
            ) : (
              <div className="autopsy-grid">
                {/* Q1: Formation */}
                <div className="autopsy-card">
                  <h4>1. FORMATION &amp; BIRTH</h4>
                  <div className="autopsy-item">
                    <span>Appearance Step:</span>
                    <strong>Step {autopsy.formation?.appearance_step ?? 0}</strong>
                  </div>
                  <div className="autopsy-item">
                    <span>Initial Event:</span>
                    <code>{autopsy.formation?.event_id ?? 'e0000'}</code>
                  </div>
                  <div className="autopsy-item">
                    <span>Initial Strength:</span>
                    <strong>{(autopsy.formation?.initial_strength ?? 0).toFixed(4)}</strong>
                  </div>
                  <div className="autopsy-item">
                    <span>Substrate Norm:</span>
                    <strong>{(autopsy.formation?.initial_state_norm ?? 0).toFixed(3)}</strong>
                  </div>
                </div>

                {/* Q2: Reinforcement */}
                <div className="autopsy-card">
                  <h4>2. REINFORCEMENT HISTORY</h4>
                  <div className="autopsy-item">
                    <span>Refresh Operations:</span>
                    <strong>{autopsy.reinforcement?.count ?? 0}</strong>
                  </div>
                  <div className="autopsy-item">
                    <span>Average Boost:</span>
                    <strong>+{(autopsy.reinforcement?.average_boost ?? 0).toFixed(4)}</strong>
                  </div>
                  <div className="autopsy-item">
                    <span>Reinforcing Events:</span>
                    <span>{autopsy.reinforcement?.events?.join(', ') || 'None'}</span>
                  </div>
                </div>

                {/* Q3: Competition */}
                <div className="autopsy-card">
                  <h4>3. VECTOR COMPETITION</h4>
                  <div className="autopsy-item">
                    <span>Active Competitors:</span>
                    <strong>{autopsy.competition?.competing_count ?? 0}</strong>
                  </div>
                  {autopsy.competition?.primary_competitor && (
                    <div className="autopsy-item">
                      <span>Primary Competitor:</span>
                      <strong className="amber">
                        {autopsy.competition.primary_competitor.label} (Sim: {autopsy.competition.primary_competitor.similarity.toFixed(3)})
                      </strong>
                    </div>
                  )}
                  <div className="competitor-mini-list">
                    {autopsy.competition?.all_competitors?.map((c, i) => (
                      <span key={i} className="mini-tag">
                        {c.label}: {c.similarity.toFixed(2)}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Q4: Weakening Inflection Point */}
                <div className="autopsy-card">
                  <h4>4. WEAKENING INFLECTION</h4>
                  {autopsy.weakening_inflection ? (
                    <>
                      <div className="autopsy-item">
                        <span>Inflection Step:</span>
                        <strong className="red">Step {autopsy.weakening_inflection.step}</strong>
                      </div>
                      <div className="autopsy-item">
                        <span>Single Step Drop:</span>
                        <strong className="red">-{autopsy.weakening_inflection.drop.toFixed(4)}</strong>
                      </div>
                      <div className="autopsy-item">
                        <span>Coinciding Write:</span>
                        <code>{autopsy.weakening_inflection.culprit_event}</code>
                      </div>
                    </>
                  ) : (
                    <p className="muted-text">No sudden inflection drop detected; memory remained stable.</p>
                  )}
                </div>

                {/* Q5: Survival or Failure */}
                <div className="autopsy-card">
                  <h4>5. STATUS &amp; ROOT CAUSES</h4>
                  {autopsy.failure_profile?.is_failed ? (
                    <div className="failure-summary">
                      <span className="badge-red">FAILED MEMORY</span>
                      <p>Final strength dropped below readout threshold.</p>
                      <ul>
                        {autopsy.failure_profile.failure_causes.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <div className="survival-summary">
                      <span className="badge-green">SURVIVING MEMORY</span>
                      <p>
                        Retention ratio:{' '}
                        <strong>
                          {((autopsy.survival_profile?.retention_ratio ?? 1) * 100).toFixed(1)}%
                        </strong>
                      </p>
                      <ul>
                        {autopsy.survival_profile?.survival_reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Q6 & Q7: Counterfactual & Evidence */}
                <div className="autopsy-card">
                  <h4>6 &amp; 7. COUNTERFACTUAL IMPACT &amp; PROOF</h4>
                  <div className="supporting-evidence-list">
                    {autopsy.supporting_evidence.map((ev, i) => (
                      <div key={i} className="evidence-bullet">
                        &bull; {ev}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Discovery Feed */}
      {activeTab === 'discovery' && (
        <div className="tab-pane">
          <div className="card full-width">
            <div className="card-header-flex">
              <div>
                <h3>Unprompted Discovery Feed</h3>
                <p className="subtitle">
                  Autonomous anomaly scanner detecting unexpected memory phenomena, resistance, and noise saturation:
                </p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={loadDiscoveryFeed}>
                SCAN EXPERIMENT
              </button>
            </div>

            {discoveries.length === 0 ? (
              <div className="empty-panel">
                <p className="muted-text">No anomalous dynamics detected. Click Scan to re-evaluate.</p>
              </div>
            ) : (
              <div className="discovery-feed-grid">
                {discoveries.map((disc) => (
                  <div key={disc.discovery_id} className="discovery-card">
                    <div className="card-header">
                      <span className="category-pill">{disc.category.toUpperCase()}</span>
                      <span className="novelty-tag">{disc.novelty}</span>
                    </div>
                    <h4>{disc.title}</h4>
                    <p>{disc.description}</p>
                    <div className="discovery-seed">
                      <span>SUGGESTED INVESTIGATION:</span>
                      <button
                        className="seed-question-btn"
                        onClick={() => {
                          handleQuestionChange(disc.seed_question)
                          setActiveTab('hypotheses')
                        }}
                      >
                        &ldquo;{disc.seed_question}&rdquo; &rarr;
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 6: Research Notebook */}
      {activeTab === 'notebook' && (
        <div className="tab-pane">
          <div className="two-column-layout">
            {/* Left: Notes Editor */}
            <div className="card">
              <h3>Research Notebook Note</h3>
              <p className="subtitle">Record formal observations, hypothesis revisions, and proof notes:</p>

              <div className="form-group">
                <label>NOTE TITLE</label>
                <input
                  type="text"
                  className="detective-input"
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  placeholder="e.g. Cross-talk ablation verification on obj_A"
                />
              </div>

              <div className="form-group">
                <label>OBSERVATIONS &amp; CONCLUSION</label>
                <textarea
                  className="detective-textarea"
                  rows={5}
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Log empirical notes, step details, and conclusions..."
                />
              </div>

              <div className="form-group">
                <label>TAGS (COMMA SEPARATED)</label>
                <input
                  type="text"
                  className="detective-input"
                  value={noteTags}
                  onChange={(e) => setNoteTags(e.target.value)}
                  placeholder="e.g. interference, cross-talk, verified"
                />
              </div>

              <button className="btn btn-primary" onClick={handleSaveNote}>
                COMMIT NOTE TO LOG
              </button>
            </div>

            {/* Right: Saved Notes Feed */}
            <div className="card">
              <h3>Investigation Log History</h3>
              <p className="subtitle">Saved notes linked to this experiment:</p>

              {notebookEntries.length === 0 ? (
                <div className="empty-panel">
                  <p className="muted-text">No notes logged yet. Use the editor to commit research notes.</p>
                </div>
              ) : (
                <div className="notes-list">
                  {notebookEntries.map((note) => (
                    <div key={note.entry_id} className="note-card">
                      <div className="card-header">
                        <strong>{note.title}</strong>
                        <button
                          className="btn-delete-note"
                          onClick={() => handleDeleteNote(note.entry_id)}
                        >
                          ×
                        </button>
                      </div>
                      <p className="note-text">{note.content || note.notes}</p>
                      <div className="note-footer">
                        <span className="author">by {note.author}</span>
                        <div className="tag-row">
                          {note.tags?.map((t, i) => (
                            <span key={i} className="mini-tag">{t}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Forensic Scorecard Modal */}
      {showScorecardModal && scorecard && (
        <div className="modal-backdrop" onClick={() => setShowScorecardModal(false)}>
          <div className="modal-content scorecard-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>INVESTIGATION FORENSIC SCORECARD</h2>
              <button className="btn-close" onClick={() => setShowScorecardModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="scorecard-hero">
                <span className="hero-label">INVESTIGATION QUESTION:</span>
                <h3>{scorecard.question}</h3>
                <div className="scorecard-verdict-row">
                  <span>FORENSIC VERDICT:</span>
                  <strong className={
                    scorecard.verdict.includes('SUPPORTED') ? 'green-pill' : 'red-pill'
                  }>
                    {scorecard.verdict}
                  </strong>
                </div>
              </div>

              <div className="scorecard-section">
                <h4>PRIMARY COMPUTATIONAL EXPLANATION</h4>
                <p className="scorecard-stmt">{scorecard.primary_hypothesis}</p>
              </div>

              <div className="scorecard-section">
                <h4>COUNTERFACTUAL EVIDENCE LOG</h4>
                <ul>
                  {scorecard.counterfactual_evidence.map((ev, i) => (
                    <li key={i}>{ev}</li>
                  ))}
                </ul>
              </div>

              <div className="scorecard-section">
                <h4>COMPETING ALTERNATIVES CONSIDERED</h4>
                <ul>
                  {scorecard.alternative_explanations.map((alt, i) => (
                    <li key={i}>{alt}</li>
                  ))}
                </ul>
              </div>

              <div className="scorecard-section">
                <h4>EPISTEMIC LIMITATIONS</h4>
                <ul>
                  {scorecard.epistemic_limitations.map((lim, i) => (
                    <li key={i} className="muted-text">{lim}</li>
                  ))}
                </ul>
              </div>

              <div className="scorecard-conclusion">
                <strong>CONCLUSION:</strong> {scorecard.conclusion}
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={handleReproduce}
                disabled={reproducing}
              >
                {reproducing ? 'REPRODUCING...' : 'REPRODUCE INVESTIGATION'}
              </button>
              <button className="btn btn-primary" onClick={() => setShowScorecardModal(false)}>
                CLOSE SCORECARD
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
