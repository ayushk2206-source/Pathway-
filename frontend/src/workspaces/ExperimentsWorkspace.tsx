import React, { useState } from 'react'
import type { Experiment, ExperimentSummary } from '../types'

interface ExperimentsWorkspaceProps {
  currentExperiment: Experiment | null
  experiments: ExperimentSummary[]
  onSelectExperiment: (id: string) => void
  onLaunchDemo: () => void
}

export const ExperimentsWorkspace: React.FC<ExperimentsWorkspaceProps> = ({
  currentExperiment,
  experiments,
  onSelectExperiment,
  onLaunchDemo,
}) => {
  const [compareIdA, setCompareIdA] = useState<string>(currentExperiment?.experiment_id || '')
  const [compareIdB, setCompareIdB] = useState<string>(experiments[0]?.experiment_id || '')

  const expA = experiments.find((e) => e.experiment_id === compareIdA) || (currentExperiment ? {
    experiment_id: currentExperiment.experiment_id,
    mechanism: currentExperiment.mechanism,
    created_at: currentExperiment.created_at,
    num_events: currentExperiment.events.length,
    parameters: currentExperiment.parameters,
    metrics: currentExperiment.metrics,
    version: currentExperiment.version,
  } : null)

  const expB = experiments.find((e) => e.experiment_id === compareIdB)

  return (
    <div className="experiments-workspace-layout">
      {/* Header */}
      <div className="workspace-header-strip">
        <div>
          <h2 className="workspace-title">EXPERIMENT ARCHIVE & COMPARATIVE MATRIX</h2>
          <div className="workspace-subtitle">
            Inspect stored computational trajectories and evaluate side-by-side performance across different mechanisms.
          </div>
        </div>
        <button className="primary" onClick={onLaunchDemo}>
          ▶ LAUNCH DEMO EXPERIMENT
        </button>
      </div>

      <div className="experiments-grid">
        {/* Archive Table */}
        <div className="experiments-table-pane">
          <div className="panel-header">
            <span>▤</span>
            <span>STORED EXPERIMENTS ({experiments.length + (currentExperiment ? 1 : 0)})</span>
          </div>

          <div className="archive-table-wrapper">
            <table className="scientific-archive-table">
              <thead>
                <tr>
                  <th>EXPERIMENT ID</th>
                  <th>MECHANISM</th>
                  <th>EVENTS</th>
                  <th>STATE DIM (d)</th>
                  <th>TIMESTAMP</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {currentExperiment && (
                  <tr className="current-row">
                    <td>
                      <span className="dot emerald" />
                      <strong>{currentExperiment.experiment_id.slice(0, 12)}</strong>
                      <span className="active-tag">CURRENT</span>
                    </td>
                    <td className="cyan">{currentExperiment.mechanism.toUpperCase()}</td>
                    <td>{currentExperiment.events.length}</td>
                    <td>d={currentExperiment.task.d}</td>
                    <td className="mono-date">{new Date(currentExperiment.created_at).toLocaleTimeString()}</td>
                    <td>
                      <button className="primary" disabled>
                        LOADED
                      </button>
                    </td>
                  </tr>
                )}
                {experiments
                  .filter((e) => e.experiment_id !== currentExperiment?.experiment_id)
                  .map((e) => (
                    <tr key={e.experiment_id}>
                      <td>
                        <span className="dot" />
                        <code>{e.experiment_id.slice(0, 12)}</code>
                      </td>
                      <td className="cyan">{e.mechanism.toUpperCase()}</td>
                      <td>{e.num_events}</td>
                      <td>d={e.parameters.state_dim}</td>
                      <td className="mono-date">{new Date(e.created_at).toLocaleTimeString()}</td>
                      <td>
                        <button onClick={() => onSelectExperiment(e.experiment_id)}>
                          LOAD
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Side-by-Side Comparison Matrix */}
        <div className="comparison-matrix-pane">
          <div className="panel-header">
            <span>⚖</span>
            <span>SIDE-BY-SIDE COMPARISON</span>
          </div>

          <div className="comparison-body">
            <div className="compare-selectors">
              <div className="selector-col">
                <label>EXPERIMENT A</label>
                <select value={compareIdA} onChange={(e) => setCompareIdA(e.target.value)}>
                  {currentExperiment && (
                    <option value={currentExperiment.experiment_id}>
                      Current ({currentExperiment.experiment_id.slice(0, 8)})
                    </option>
                  )}
                  {experiments.map((e) => (
                    <option key={e.experiment_id} value={e.experiment_id}>
                      {e.experiment_id.slice(0, 8)} · {e.mechanism}
                    </option>
                  ))}
                </select>
              </div>

              <span className="vs-badge">VS</span>

              <div className="selector-col">
                <label>EXPERIMENT B</label>
                <select value={compareIdB} onChange={(e) => setCompareIdB(e.target.value)}>
                  {experiments.map((e) => (
                    <option key={e.experiment_id} value={e.experiment_id}>
                      {e.experiment_id.slice(0, 8)} · {e.mechanism}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {expA && expB ? (
              <div className="comparison-table-wrapper">
                <table className="compare-metrics-table">
                  <thead>
                    <tr>
                      <th>METRIC / ATTRIBUTE</th>
                      <th>{expA.experiment_id.slice(0, 8)}</th>
                      <th>{expB.experiment_id.slice(0, 8)}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>MECHANISM</td>
                      <td className="cyan">{expA.mechanism.toUpperCase()}</td>
                      <td className="cyan">{expB.mechanism.toUpperCase()}</td>
                    </tr>
                    <tr>
                      <td>STATE DIMENSION</td>
                      <td>d = {expA.parameters.state_dim}</td>
                      <td>d = {expB.parameters.state_dim}</td>
                    </tr>
                    <tr>
                      <td>UPDATE STRENGTH (α)</td>
                      <td>{expA.parameters.update_strength}</td>
                      <td>{expB.parameters.update_strength}</td>
                    </tr>
                    <tr>
                      <td>DECAY RATE (λ)</td>
                      <td>{expA.parameters.decay}</td>
                      <td>{expB.parameters.decay}</td>
                    </tr>
                    <tr>
                      <td>TOTAL EVENTS</td>
                      <td>{expA.num_events}</td>
                      <td>{expB.num_events}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="diff-placeholder">
                Select two experiments from the dropdowns above to compare metrics side-by-side.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
