import React from 'react'
import type { Experiment, HeatmapsData, MemoryTrace } from '../types'

interface TimelineWorkspaceProps {
  experiment: Experiment | null
  currentStep: number
  onStepChange: (step: number) => void
  selectedMemoryId: string | null
  trace: MemoryTrace | null
  heatmaps: HeatmapsData | null
  onSelectMemory: (id: string) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

export const TimelineWorkspace: React.FC<TimelineWorkspaceProps> = ({
  experiment,
  currentStep,
  onStepChange,
  selectedMemoryId,
  trace,
  heatmaps,
  onSelectMemory,
  onViewEvidence,
}) => {
  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>TIMELINE FORENSICS · OFFLINE</h3>
        <p>No active memory history. Run or load an experiment to inspect chronological traces.</p>
      </div>
    )
  }

  return (
    <div className="timeline-workspace-layout">
      {/* Top Banner */}
      <div className="workspace-header-strip">
        <div>
          <h2 className="workspace-title">MEMORY TIMELINE & LIFECYCLE FORENSICS</h2>
          <div className="workspace-subtitle">
            Reconstruct how memories originate, decay, compete, and stabilize across sequential write operations.
          </div>
        </div>
      </div>

      <div className="timeline-grid-layout">
        {/* Left Column: Vertical Forensic Memory Trace */}
        <div className="timeline-col left-col">
          <div className="panel-header">
            <span>↓</span>
            <span>FORENSIC MEMORY TRACE {selectedMemoryId ? `(${selectedMemoryId})` : ''}</span>
          </div>

          <div className="timeline-col-body">
            {trace && trace.stages.length ? (
              <div className="vertical-trace-tree">
                <div className="trace-summary-badge">
                  <span className="concept-name">{trace.concept_label}</span>
                  <span className="current-stage-pill cyan">STAGE: {trace.current_stage}</span>
                </div>
                <button
                  type="button"
                  className="secondary small-btn"
                  style={{ marginBottom: '0.75rem', width: '100%' }}
                  onClick={() =>
                    onViewEvidence(`Forensic Memory Trace: ${trace.concept_label}`, {
                      concept: trace.concept_label,
                      current_stage: trace.current_stage,
                      total_stages: trace.stages.length,
                      stages: trace.stages,
                      total_events_in_experiment: experiment.events.length,
                    })
                  }
                >
                  VIEW LIFECYCLE EVIDENCE
                </button>

                <div className="trace-stages-list">
                  {trace.stages.map((st, i) => (
                    <div key={i} className="trace-stage-card">
                      <div className="stage-connector">
                        <span className="stage-dot" />
                        {i < trace.stages.length - 1 && <span className="stage-line" />}
                      </div>
                      <div className="stage-content">
                        <div className="stage-head">
                          <span className="stage-name">{st.stage}</span>
                          <span className="stage-step">STEP {st.step}</span>
                        </div>
                        <div className="stage-metrics">
                          <span>STRENGTH: <strong className="emerald">{st.strength.toFixed(3)}</strong></span>
                          <span>EVENT: <code>{st.event_id}</code></span>
                        </div>
                        <div className="stage-evidence">{st.evidence}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="trace-empty">
                <p>Select a memory to construct its vertical lifecycle trace.</p>
                <div className="cues-quick-picker">
                  {heatmaps?.memories.map((m) => (
                    <button
                      key={m}
                      className={selectedMemoryId === m ? 'primary' : ''}
                      onClick={() => onSelectMemory(m)}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Time x Memory Strength Matrix Heatmap */}
        <div className="timeline-col right-col">
          <div className="panel-header">
            <span>▦</span>
            <span>TIME × MEMORY STRENGTH HEATMAP</span>
          </div>

          <div className="timeline-col-body">
            {heatmaps && heatmaps.memory_matrix.length ? (
              <div className="heatmap-container">
                <div className="heatmap-meta">
                  <span>ROWS: MEMORY ITEMS ({heatmaps.memories.length})</span>
                  <span>COLUMNS: TIMESTEPS ({heatmaps.time_steps.length})</span>
                </div>

                <div className="heatmap-scrollable-table">
                  <table className="scientific-heatmap-table">
                    <thead>
                      <tr>
                        <th className="sticky-col">MEMORY</th>
                        {heatmaps.time_steps.map((t) => (
                          <th
                            key={t}
                            className={currentStep === t ? 'highlight-header' : ''}
                            onClick={() => onStepChange(t)}
                          >
                            T{t}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {heatmaps.memories.map((mId, rowIdx) => {
                        const isSelected = selectedMemoryId === mId
                        return (
                          <tr
                            key={mId}
                            className={isSelected ? 'selected-row' : ''}
                            onClick={() => onSelectMemory(mId)}
                          >
                            <td className="sticky-col memory-label-cell">
                              <span className="dot" />
                              <span>{mId}</span>
                            </td>
                            {heatmaps.memory_matrix[rowIdx].map((val, stepIdx) => {
                              const strength = Math.max(0, Math.min(1, val))
                              const isStepActive = currentStep === heatmaps.time_steps[stepIdx]
                              const bg =
                                strength > 0.6
                                  ? `rgba(0, 240, 255, ${0.2 + strength * 0.7})`
                                  : strength > 0.2
                                  ? `rgba(16, 185, 129, ${0.15 + strength * 0.5})`
                                  : `rgba(239, 68, 68, ${0.1 + (1 - strength) * 0.3})`

                              return (
                                <td
                                  key={stepIdx}
                                  className={`heatmap-cell ${isStepActive ? 'step-active' : ''}`}
                                  style={{ background: bg }}
                                  title={`${mId} at Step ${heatmaps.time_steps[stepIdx]}: Strength = ${val.toFixed(4)}`}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onStepChange(heatmaps.time_steps[stepIdx])
                                    onSelectMemory(mId)
                                  }}
                                >
                                  {val.toFixed(2)}
                                </td>
                              )
                            })}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                <div className="heatmap-legend">
                  <div className="legend-item"><span className="swatch" style={{ background: 'rgba(0, 240, 255, 0.8)' }} /> High Readout (&gt;0.6)</div>
                  <div className="legend-item"><span className="swatch" style={{ background: 'rgba(16, 185, 129, 0.5)' }} /> Moderate Readout (0.2–0.6)</div>
                  <div className="legend-item"><span className="swatch" style={{ background: 'rgba(239, 68, 68, 0.4)' }} /> Degraded / Decayed (&lt;0.2)</div>
                </div>
              </div>
            ) : (
              <div className="diff-placeholder">Loading sequential heatmap matrices...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
