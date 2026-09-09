import React, { useEffect, useMemo, useState } from 'react'
import type {
  CounterfactualExperiment,
  Experiment,
  ExperimentBranchSummary,
  SynapticCompareResponse,
} from '../types'
import {
  compareSynapticCounterfactual,
  getExperimentBranches,
  runSynapticCounterfactual,
} from '../api'
import { BranchingTimelineVisualizer } from '../components/BranchingTimelineVisualizer'
import { SynchronizedNetworkComparison } from '../components/SynchronizedNetworkComparison'
import { SynapticDeltaTable } from '../components/SynapticDeltaTable'
import { CounterfactualHypothesisCard } from '../components/CounterfactualHypothesisCard'
import '../counterfactual.css'

interface CounterfactualWorkspaceProps {
  experiment: Experiment | null
  counterfactuals: CounterfactualExperiment[]
  onCounterfactualCreated: (cf: CounterfactualExperiment) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

export const CounterfactualWorkspace: React.FC<CounterfactualWorkspaceProps> = ({
  experiment,
  counterfactuals: _initialCounterfactuals,
  onCounterfactualCreated,
  onViewEvidence,
}) => {
  // Intervention Configuration State
  const [interventionMode, setInterventionMode] = useState<
    'PREVENT_STRENGTHEN' | 'SILENCE' | 'SCALE' | 'DECAY' | 'PLASTICITY'
  >('PREVENT_STRENGTHEN')
  const [selectedSynapseId, setSelectedSynapseId] = useState<string | null>('syn_k0_v1')
  const [divergenceTimestep, setDivergenceTimestep] = useState<number>(1)
  const [scaleFactor, setScaleFactor] = useState<number>(0.25)
  const [newDecay, setNewDecay] = useState<number>(0.4)
  const [newPlasticity, setNewPlasticity] = useState<number>(0.3)
  const [hypothesis, setHypothesis] = useState<string>('')
  const [isExecuting, setIsExecuting] = useState<boolean>(false)

  // Active Branch & Synchronized Inspection State
  const [activeCounterfactual, setActiveCounterfactual] = useState<CounterfactualExperiment | null>(null)
  const [activeBranchId, setActiveBranchId] = useState<string | null>(null)
  const [inspectedTimestep, setInspectedTimestep] = useState<number>(1)
  const [syncCompareData, setSyncCompareData] = useState<SynapticCompareResponse | null>(null)
  const [branches, setBranches] = useState<ExperimentBranchSummary[]>([])
  const [isLoadingCompare, setIsLoadingCompare] = useState<boolean>(false)

  const events = experiment?.events || []
  const totalTimesteps = Math.max(events.length, (experiment?.snapshots?.length ?? 1) - 1, 1)

  // Candidate synapses extracted from experiment
  const candidateSynapses = useMemo(() => {
    const list: string[] = []
    const d = 16
    for (let i = 0; i < Math.min(d, 6); i++) {
      for (let j = 0; j < Math.min(d, 6); j++) {
        list.push(`syn_k${j}_v${i}`)
      }
    }
    return list
  }, [])

  // Load existing branches for this experiment
  useEffect(() => {
    if (!experiment) return
    let isMounted = true
    getExperimentBranches(experiment.experiment_id)
      .then((res) => {
        if (isMounted) setBranches(res.branches || [])
      })
      .catch(() => {})
    return () => {
      isMounted = false
    }
  }, [experiment])

  // Single variable controlled description
  const variableControlledDescription = useMemo(() => {
    switch (interventionMode) {
      case 'PREVENT_STRENGTHEN':
        return `Prevent synaptic strengthening on connection ${selectedSynapseId} at T>=${divergenceTimestep}.`
      case 'SILENCE':
        return `Zero out (silence) connection ${selectedSynapseId} at T>=${divergenceTimestep}.`
      case 'SCALE':
        return `Scale synaptic weight of ${selectedSynapseId} by ${scaleFactor}x at T=${divergenceTimestep}.`
      case 'DECAY':
        return `Change global decay rate λ to ${newDecay} (baseline: ${experiment?.parameters?.decay ?? 0.05}).`
      case 'PLASTICITY':
        return `Change write gain η to ${newPlasticity} (baseline: ${experiment?.parameters?.update_strength ?? 1.0}).`
    }
  }, [interventionMode, selectedSynapseId, divergenceTimestep, scaleFactor, newDecay, newPlasticity, experiment])

  // Execute real counterfactual branch
  const handleExecuteCounterfactual = async () => {
    if (!experiment || isExecuting) return
    setIsExecuting(true)

    let itype: 'synapse_prevent_strengthen' | 'synapse_silence' | 'synapse_scale' | 'change_decay' | 'change_plasticity' = 'synapse_prevent_strengthen'
    if (interventionMode === 'SILENCE') itype = 'synapse_silence'
    else if (interventionMode === 'SCALE') itype = 'synapse_scale'
    else if (interventionMode === 'DECAY') itype = 'change_decay'
    else if (interventionMode === 'PLASTICITY') itype = 'change_plasticity'

    try {
      const res = await runSynapticCounterfactual({
        experiment_id: experiment.experiment_id,
        intervention_type: itype,
        synapse_id: (itype.startsWith('synapse')) ? (selectedSynapseId || 'syn_k0_v1') : undefined,
        target_timestep: divergenceTimestep,
        factor: scaleFactor,
        new_decay: newDecay,
        new_update_strength: newPlasticity,
        hypothesis: hypothesis || variableControlledDescription,
        title: `What-If: ${variableControlledDescription}`,
      })

      const cf = res.counterfactual
      setActiveCounterfactual(cf)
      setActiveBranchId(cf.counterfactual_id)
      onCounterfactualCreated(cf)

      // Refresh branches list
      const branchList = await getExperimentBranches(experiment.experiment_id)
      setBranches(branchList.branches || [])

      // Synchronize comparison at divergence step
      setInspectedTimestep(res.branch_point || divergenceTimestep)
      await fetchSynchronizedComparison(cf.counterfactual_id, res.branch_point || divergenceTimestep)
    } catch (err) {
      alert(`Counterfactual execution failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIsExecuting(false)
    }
  }

  // Fetch synchronized network states and deltas at step
  const fetchSynchronizedComparison = async (cfId: string, step: number) => {
    if (!experiment) return
    setIsLoadingCompare(true)
    try {
      const data = await compareSynapticCounterfactual(
        experiment.experiment_id,
        cfId,
        step,
        16
      )
      setSyncCompareData(data)
    } catch (e) {
      console.error('Failed to compare synaptic counterfactual states:', e)
    } finally {
      setIsLoadingCompare(false)
    }
  }

  // When scrubbing timesteps
  const handleSelectStep = (step: number) => {
    setInspectedTimestep(step)
    if (activeCounterfactual) {
      fetchSynchronizedComparison(activeCounterfactual.counterfactual_id, step)
    }
  }

  // Switch between existing branches
  const handleSelectBranch = (b: ExperimentBranchSummary) => {
    setActiveBranchId(b.branch_id)
    setInspectedTimestep(b.divergence_step)
    fetchSynchronizedComparison(b.branch_id, b.divergence_step)
  }

  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>WHAT IF? · COUNTERFACTUAL ENGINE OFFLINE</h3>
        <p>Run or load an experiment first to branch alternative computational timelines.</p>
      </div>
    )
  }

  return (
    <div className="counterfactual-workspace-layout">
      {/* Header Bar */}
      <div className="workspace-header-strip">
        <div>
          <h2 className="workspace-title">WHAT IF? · COUNTERFACTUAL COMPUTATION ENGINE</h2>
          <div className="workspace-subtitle">
            Controlled computational interventions. Alter one synaptic or mechanism variable, run the exact memory task, and measure real divergence.
          </div>
        </div>
        <div className="experiment-badge">
          <span className="lbl">BASELINE:</span>
          <strong>{experiment.experiment_id}</strong>
          <span className="mechanism-tag">({experiment.mechanism})</span>
        </div>
      </div>

      <div className="cf-content-grid">
        {/* Left Column: Single-Variable Controller & Hypothesis */}
        <div className="cf-col left-col">
          <div className="panel-header">
            <span>⑂</span>
            <span>SINGLE-VARIABLE INTERVENTION CONTROLLER</span>
          </div>

          <div className="cf-panel-body">
            {/* Signature Experiment Presets */}
            <div className="form-field">
              <label>WHAT-IF INVESTIGATION MODE</label>
              <div className="btn-group-vertical" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button
                  type="button"
                  className={`interv-btn ${interventionMode === 'PREVENT_STRENGTHEN' ? 'active emerald' : ''}`}
                  onClick={() => setInterventionMode('PREVENT_STRENGTHEN')}
                >
                  ⭐ "What if this synapse NEVER strengthened?"
                </button>
                <button
                  type="button"
                  className={`interv-btn ${interventionMode === 'SILENCE' ? 'active crimson' : ''}`}
                  onClick={() => setInterventionMode('SILENCE')}
                >
                  ⚡ "What if this connection was SILENCED?"
                </button>
                <button
                  type="button"
                  className={`interv-btn ${interventionMode === 'SCALE' ? 'active amber' : ''}`}
                  onClick={() => setInterventionMode('SCALE')}
                >
                  ⚖ "What if this connection was WEAKENED?"
                </button>
                <button
                  type="button"
                  className={`interv-btn ${interventionMode === 'DECAY' ? 'active cyan' : ''}`}
                  onClick={() => setInterventionMode('DECAY')}
                >
                  ⏳ "What if synaptic decay happened FASTER?"
                </button>
                <button
                  type="button"
                  className={`interv-btn ${interventionMode === 'PLASTICITY' ? 'active purple' : ''}`}
                  onClick={() => setInterventionMode('PLASTICITY')}
                >
                  🧠 "What if plasticity was WEAKER?"
                </button>
              </div>
            </div>

            {/* Target Synapse Selection if synaptic mode */}
            {['PREVENT_STRENGTHEN', 'SILENCE', 'SCALE'].includes(interventionMode) && (
              <div className="form-field">
                <label>TARGET SYNAPSE CONNECTION</label>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <input
                    type="text"
                    value={selectedSynapseId || ''}
                    onChange={(e) => setSelectedSynapseId(e.target.value)}
                    placeholder="e.g. syn_k0_v1"
                    className="delta-search-input"
                    style={{ flex: 1 }}
                  />
                  <select
                    value={selectedSynapseId || candidateSynapses[0] || 'syn_k0_v1'}
                    onChange={(e) => setSelectedSynapseId(e.target.value)}
                    style={{ background: '#0f172a', color: '#fff', border: '1px solid #334155', borderRadius: '4px' }}
                  >
                    {candidateSynapses.slice(0, 16).map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Divergence Timestep */}
            <div className="form-field">
              <label>DIVERGENCE TIMESTEP (FORK POINT): T{divergenceTimestep}</label>
              <input
                type="range"
                min="0"
                max={Math.max(totalTimesteps - 1, 0)}
                value={divergenceTimestep}
                onChange={(e) => setDivergenceTimestep(Number(e.target.value))}
                className="timeline-slider"
              />
              <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                Event at T{divergenceTimestep}: {events[divergenceTimestep]?.concept_label || 'Initial state'}
              </span>
            </div>

            {/* Variable parameter controls */}
            {interventionMode === 'SCALE' && (
              <div className="form-field">
                <label>SCALE FACTOR: {scaleFactor.toFixed(2)}x</label>
                <input
                  type="range"
                  min="0.0"
                  max="2.0"
                  step="0.05"
                  value={scaleFactor}
                  onChange={(e) => setScaleFactor(Number(e.target.value))}
                  className="timeline-slider"
                />
              </div>
            )}

            {interventionMode === 'DECAY' && (
              <div className="form-field">
                <label>NEW DECAY RATE (λ): {newDecay.toFixed(2)}</label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={newDecay}
                  onChange={(e) => setNewDecay(Number(e.target.value))}
                  className="timeline-slider"
                />
              </div>
            )}

            {interventionMode === 'PLASTICITY' && (
              <div className="form-field">
                <label>NEW PLASTICITY (η): {newPlasticity.toFixed(2)}</label>
                <input
                  type="range"
                  min="0.0"
                  max="2.0"
                  step="0.05"
                  value={newPlasticity}
                  onChange={(e) => setNewPlasticity(Number(e.target.value))}
                  className="timeline-slider"
                />
              </div>
            )}

            {/* Scientific Hypothesis Card */}
            <CounterfactualHypothesisCard
              counterfactual={activeCounterfactual}
              currentHypothesis={hypothesis}
              onChangeHypothesis={setHypothesis}
              onRunIntervention={handleExecuteCounterfactual}
              isExecuting={isExecuting}
              variableControlledDescription={variableControlledDescription}
              onReRun={handleExecuteCounterfactual}
              onExport={() => {}}
              onSelectGuidedSynapse={(s) => setSelectedSynapseId(s)}
              topCandidateSynapses={candidateSynapses}
            />

            {/* Multiple Branches Tree Section */}
            {branches.length > 0 && (
              <div className="branch-tree-card">
                <div className="branch-tree-title">
                  COUNTERFACTUAL EXPERIMENTAL TREE ({branches.length} BRANCHES)
                </div>
                <div className="branch-tree-list">
                  {branches.map((b) => (
                    <div
                      key={b.branch_id}
                      className={`branch-item ${activeBranchId === b.branch_id ? 'active' : ''}`}
                      onClick={() => handleSelectBranch(b)}
                    >
                      <div>
                        <div className="b-title">{b.title}</div>
                        <div className="b-meta">
                          Fork: T{b.divergence_step} · {b.intervention_type}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: b.accuracy_delta >= 0 ? '#34d399' : '#f87171' }}>
                          Δ Acc: {b.accuracy_delta >= 0 ? '+' : ''}{(b.accuracy_delta * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Branching Visualizer, Synchronized Dual Canvases & Synaptic Deltas */}
        <div className="cf-col right-col">
          <div className="panel-header">
            <span>⚖</span>
            <span>COMPARATIVE CAUSAL OBSERVATION & SYNAPTIC DELTA</span>
          </div>

          <div className="cf-panel-body">
            {/* Branching Timeline Visualizer */}
            <BranchingTimelineVisualizer
              totalSteps={totalTimesteps}
              divergenceStep={activeCounterfactual?.provenance?.branch_point !== undefined ? Number(activeCounterfactual.provenance.branch_point) : divergenceTimestep}
              currentStep={inspectedTimestep}
              onSelectStep={handleSelectStep}
              events={events}
              targetSynapse={selectedSynapseId || undefined}
              modifiedVariable={variableControlledDescription}
              originalMetric={typeof experiment.metrics?.recall_accuracy === 'number' ? experiment.metrics.recall_accuracy : undefined}
              counterfactualMetric={typeof activeCounterfactual?.counterfactual_result?.metrics?.recall_accuracy === 'number' ? Number(activeCounterfactual.counterfactual_result.metrics.recall_accuracy) : undefined}
            />

            {/* Synchronized Network Comparison */}
            {isLoadingCompare ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
                Synchronizing networks at T{inspectedTimestep}...
              </div>
            ) : syncCompareData ? (
              <SynchronizedNetworkComparison
                stepIdx={inspectedTimestep}
                divergenceStep={syncCompareData.divergence_step}
                originalNetwork={syncCompareData.original_network}
                counterfactualNetwork={syncCompareData.counterfactual_network}
                matrixFrobeniusDelta={syncCompareData.matrix_frobenius_delta}
                changedSynapsesCount={syncCompareData.changed_synapses_count}
                selectedSynapseId={selectedSynapseId}
                onSelectSynapse={setSelectedSynapseId}
              />
            ) : (
              <div className="sync-network-empty" style={{ padding: '30px', textAlign: 'center', background: '#090d16', border: '1px solid #1e293b', borderRadius: '8px' }}>
                <span style={{ color: '#94a3b8' }}>
                  Select an intervention on the left and click <strong>EXECUTE COUNTERFACTUAL BRANCH</strong> to view side-by-side synchronized network states.
                </span>
              </div>
            )}

            {/* Synaptic Delta Table */}
            {syncCompareData && (
              <SynapticDeltaTable
                deltas={syncCompareData.synaptic_deltas}
                selectedSynapseId={selectedSynapseId}
                onSelectSynapse={setSelectedSynapseId}
              />
            )}

            {/* Query Outcome Comparison Table */}
            {syncCompareData && syncCompareData.query_comparison.length > 0 && (
              <div className="synaptic-delta-card">
                <div className="delta-table-header">
                  <span className="delta-title">QUERY RECALL DELTA AT THIS TIMESTEP</span>
                  <button
                    className="inspect-btn"
                    onClick={() =>
                      onViewEvidence('Query Outcomes Evidence', {
                        queries: syncCompareData.query_comparison,
                        deltas: syncCompareData.outcome_deltas,
                      })
                    }
                  >
                    VIEW EVIDENCE
                  </button>
                </div>
                <table className="delta-table">
                  <thead>
                    <tr>
                      <th>CUE (OBJECT)</th>
                      <th>TRUTH</th>
                      <th>ORIGINAL PREDICTION</th>
                      <th>WHAT IF? PREDICTION</th>
                      <th>Δ CONFIDENCE</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {syncCompareData.query_comparison.map((q) => (
                      <tr key={q.query_id}>
                        <td><strong>{q.object_label}</strong></td>
                        <td>{q.truth_label || '—'}</td>
                        <td>{q.original_prediction} ({(q.original_confidence * 100).toFixed(1)}%)</td>
                        <td style={{ color: q.outcome_diverged ? '#f87171' : '#34d399' }}>
                          {q.counterfactual_prediction} ({(q.counterfactual_confidence * 100).toFixed(1)}%)
                        </td>
                        <td className={`num-cell ${q.confidence_delta < 0 ? 'negative' : 'positive'}`}>
                          {q.confidence_delta >= 0 ? '+' : ''}{(q.confidence_delta * 100).toFixed(1)}%
                        </td>
                        <td>
                          {q.outcome_diverged ? (
                            <span style={{ color: '#f87171', fontWeight: 'bold' }}>DIVERGED</span>
                          ) : (
                            <span style={{ color: '#34d399' }}>STABLE</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
