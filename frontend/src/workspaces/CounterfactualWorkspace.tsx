import React, { useState } from 'react'
import type {
  CounterfactualExperiment,
  Experiment,
  SurgeryDiff,
} from '../types'
import { compareSurgery, runAblation, runSurgery } from '../api'

interface CounterfactualWorkspaceProps {
  experiment: Experiment | null
  counterfactuals: CounterfactualExperiment[]
  onCounterfactualCreated: (cf: CounterfactualExperiment) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

export const CounterfactualWorkspace: React.FC<CounterfactualWorkspaceProps> = ({
  experiment,
  counterfactuals,
  onCounterfactualCreated,
  onViewEvidence,
}) => {
  const [selectedTargetStep, setSelectedTargetStep] = useState<number>(1)
  const [interventionType, setInterventionType] = useState<'WEAKEN' | 'REMOVE' | 'REINFORCE'>('WEAKEN')
  const [newStrength, setNewStrength] = useState<number>(0.1)
  const [isExecuting, setIsExecuting] = useState(false)
  const [activeDiff, setActiveDiff] = useState<SurgeryDiff | null>(null)
  const [selectedCf, setSelectedCf] = useState<CounterfactualExperiment | null>(null)

  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>COUNTERFACTUAL ARCHAEOLOGY · OFFLINE</h3>
        <p>Run or load an experiment to perform surgical interventions and fork counterfactual timelines.</p>
      </div>
    )
  }

  const events = experiment.events || []
  const targetEvent = events[selectedTargetStep - 1] || events[0]

  const handleRunSurgery = async () => {
    if (!experiment || isExecuting) return
    setIsExecuting(true)
    try {
      let cf: CounterfactualExperiment
      if (interventionType === 'REMOVE') {
        cf = await runAblation({
          experiment_id: experiment.experiment_id,
          target_timestep: selectedTargetStep,
          title: `Ablation of Event ${selectedTargetStep} (${targetEvent?.concept_label})`,
        })
      } else {
        const strVal = interventionType === 'REINFORCE' ? 1.5 : newStrength
        cf = await runSurgery({
          experiment_id: experiment.experiment_id,
          target_timestep: selectedTargetStep,
          new_strength: strVal,
          title: `Surgery: ${interventionType} on Event ${selectedTargetStep} (${targetEvent?.concept_label})`,
        })
      }

      onCounterfactualCreated(cf)
      setSelectedCf(cf)

      // Fetch topological surgery diff
      if (cf.counterfactual_result?.experiment_id) {
        const diff = await compareSurgery(experiment.experiment_id, cf.counterfactual_result.experiment_id)
        setActiveDiff(diff)
      }
    } catch (e) {
      alert(`Surgery execution failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="counterfactual-workspace-layout">
      {/* Header Strip */}
      <div className="workspace-header-strip">
        <div>
          <h2 className="workspace-title">COUNTERFACTUAL ARCHAEOLOGY & MEMORY SURGERY</h2>
          <div className="workspace-subtitle">
            Remove, weaken, or scale a stored memory event. Then observe causal divergence and downstream topological shifts.
          </div>
        </div>
      </div>

      <div className="cf-content-grid">
        {/* Left Column: Surgery Controls & What If Scenarios */}
        <div className="cf-col left-col">
          <div className="panel-header">
            <span>✂</span>
            <span>SURGICAL INTERVENTION CONTROLLER</span>
          </div>

          <div className="cf-panel-body">
            {/* Target Selection */}
            <div className="form-field">
              <label>TARGET EVENT TO SURGICALLY MODIFY</label>
              <select
                value={selectedTargetStep}
                onChange={(e) => setSelectedTargetStep(Number(e.target.value))}
              >
                {events.map((ev, idx) => (
                  <option key={idx} value={idx + 1}>
                    Event {idx + 1}: {ev.concept_label} = {ev.attribute_label} (Step {idx + 1})
                  </option>
                ))}
              </select>
            </div>

            {/* Intervention Type Selector */}
            <div className="intervention-selector">
              <label>INTERVENTION TYPE</label>
              <div className="type-buttons">
                <button
                  type="button"
                  className={interventionType === 'WEAKEN' ? 'active primary' : ''}
                  onClick={() => setInterventionType('WEAKEN')}
                >
                  WEAKEN
                </button>
                <button
                  type="button"
                  className={interventionType === 'REMOVE' ? 'active accent-crimson' : ''}
                  onClick={() => setInterventionType('REMOVE')}
                >
                  REMOVE (ABLATE)
                </button>
                <button
                  type="button"
                  className={interventionType === 'REINFORCE' ? 'active accent-emerald' : ''}
                  onClick={() => setInterventionType('REINFORCE')}
                >
                  REINFORCE
                </button>
              </div>
            </div>

            {/* Slider if WEAKEN */}
            {interventionType === 'WEAKEN' && (
              <div className="form-field">
                <label>NEW STRENGTH (α): {newStrength.toFixed(2)}</label>
                <input
                  type="range"
                  min="0.0"
                  max="0.5"
                  step="0.05"
                  value={newStrength}
                  onChange={(e) => setNewStrength(Number(e.target.value))}
                />
              </div>
            )}

            {/* "What If?" Quick Scenarios */}
            <div className="what-if-box">
              <div className="box-title">"WHAT IF?" PRESET PROBES:</div>
              <div className="what-if-buttons">
                <button
                  type="button"
                  onClick={() => {
                    setInterventionType('REMOVE')
                    setSelectedTargetStep(1)
                  }}
                >
                  "What if Event 1 was never written?"
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInterventionType('WEAKEN')
                    setNewStrength(0.1)
                    setSelectedTargetStep(1)
                  }}
                >
                  "What if Event 1 strength was reduced by 90%?"
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInterventionType('REINFORCE')
                    setSelectedTargetStep(events.length > 2 ? 2 : 1)
                  }}
                >
                  "What if this concept was reinforced?"
                </button>
              </div>
            </div>

            <button
              className="primary run-surgery-btn"
              onClick={handleRunSurgery}
              disabled={isExecuting}
            >
              {isExecuting ? 'COMPUTING COUNTERFACTUAL...' : '⚡ EXECUTE COUNTERFACTUAL SURGERY'}
            </button>
          </div>
        </div>

        {/* Right Column: Split View & Divergence Metrics */}
        <div className="cf-col right-col">
          <div className="panel-header">
            <span>⌥</span>
            <span>TIMELINE DIVERGENCE & TOPOLOGICAL SHIFT</span>
          </div>

          <div className="cf-panel-body">
            {selectedCf ? (
              <div className="divergence-results-card">
                <div className="divergence-head">
                  <span className="cf-title">{selectedCf.title}</span>
                  <span className="divergence-tag crimson">
                    {selectedCf.comparison?.divergence_classification || 'DIVERGED'}
                  </span>
                  <button
                    style={{ marginLeft: 'auto', padding: '2px 8px', fontSize: '10px' }}
                    onClick={() =>
                      onViewEvidence(
                        `Divergence Evidence: ${selectedCf.title}`,
                        selectedCf.comparison as unknown as Record<string, unknown>
                      )
                    }
                  >
                    VIEW EVIDENCE
                  </button>
                </div>

                {/* Split Visual Tree */}
                <div className="timeline-split-diagram">
                  <div className="branch-line original-branch">
                    <span className="branch-name">ORIGINAL TIMELINE</span>
                    <span className="branch-metric">
                      Final Norm: {selectedCf.original_result.final_state_norm.toFixed(4)}
                    </span>
                  </div>
                  <div className="branch-split-point">
                    <span className="split-glyph">⑂</span>
                    <span className="split-label">
                      FIRST DIVERGENCE AT STEP {selectedCf.comparison?.first_divergence_step ?? selectedTargetStep}
                    </span>
                  </div>
                  <div className="branch-line counterfactual-branch">
                    <span className="branch-name">COUNTERFACTUAL BRANCH</span>
                    <span className="branch-metric">
                      Final Norm: {selectedCf.counterfactual_result.final_state_norm.toFixed(4)}
                    </span>
                  </div>
                </div>

                {/* Quantitative Divergence Metrics */}
                <div className="divergence-stats-grid">
                  <div className="stat-box">
                    <span className="stat-k">STATE DISTANCE (L2):</span>
                    <span className="stat-v cyan">
                      {selectedCf.comparison?.state_distance_l2.toFixed(4) || '—'}
                    </span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-k">COSINE SIMILARITY:</span>
                    <span className="stat-v amber">
                      {selectedCf.comparison?.cosine_similarity.toFixed(4) || '—'}
                    </span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-k">RELATIVE L2 DIFF:</span>
                    <span className="stat-v crimson">
                      {selectedCf.comparison?.relative_l2.toFixed(4) || '—'}
                    </span>
                  </div>
                </div>

                {/* Topological Shifts */}
                {activeDiff && (
                  <div className="topological-shifts-box">
                    <div className="box-title">REPRESENTATION SPACE SHIFTS ({activeDiff.point_shifts.length}):</div>
                    <div className="shifts-table-wrapper">
                      <table className="shifts-table">
                        <thead>
                          <tr>
                            <th>MEMORY</th>
                            <th>SHIFT MAGNITUDE (2D)</th>
                            <th>Δ STRENGTH</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activeDiff.point_shifts.map((s) => (
                            <tr key={s.memory_id}>
                              <td>{s.label} ({s.memory_id})</td>
                              <td className="cyan">{s.shift_magnitude.toFixed(4)}</td>
                              <td className={s.strength_delta >= 0 ? 'emerald' : 'crimson'}>
                                {s.strength_delta >= 0 ? '+' : ''}{s.strength_delta.toFixed(4)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="diff-placeholder">
                Configure a surgical intervention on the left and click Execute to observe causal branching.
              </div>
            )}

            {/* List of Previous Counterfactuals */}
            {counterfactuals.length > 0 && (
              <div className="previous-counterfactuals-section">
                <div className="section-title">BRANCH HISTORY ({counterfactuals.length}):</div>
                <div className="cf-history-list">
                  {counterfactuals.map((cf) => (
                    <div
                      key={cf.counterfactual_id}
                      className={`cf-history-item ${selectedCf?.counterfactual_id === cf.counterfactual_id ? 'active' : ''}`}
                      onClick={() => setSelectedCf(cf)}
                    >
                      <span className="history-title">{cf.title}</span>
                      <span className="history-step cyan">Step {cf.comparison?.first_divergence_step ?? '—'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
