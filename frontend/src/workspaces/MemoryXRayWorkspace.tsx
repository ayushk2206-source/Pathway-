import React from 'react'
import type {
  ActivationProfile,
  AnomalyRecord,
  DiagnosticsProfile,
  EventInspector,
  Experiment,
  MemoryMap2D,
  SparsityAnalysis,
} from '../types'

interface MemoryXRayWorkspaceProps {
  experiment: Experiment | null
  currentStep: number
  onStepChange: (step: number) => void
  activationProfile: ActivationProfile | null
  sparsityAnalysis: SparsityAnalysis | null
  diagnostics: DiagnosticsProfile | null
  anomalies: AnomalyRecord[]
  eventInspector: EventInspector | null
  memoryMap: MemoryMap2D | null
  selectedMemoryId: string | null
  onSelectMemory: (id: string) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

export const MemoryXRayWorkspace: React.FC<MemoryXRayWorkspaceProps> = ({
  experiment,
  currentStep,
  onStepChange,
  activationProfile,
  sparsityAnalysis,
  diagnostics,
  anomalies,
  eventInspector,
  memoryMap,
  selectedMemoryId,
  onSelectMemory,
  onViewEvidence,
}) => {
  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>MEMORY X-RAY · OFFLINE</h3>
        <p>No active memory state detected. Please load or run an experiment to inspect state vectors.</p>
      </div>
    )
  }

  const currentSnapshot = experiment.snapshots[currentStep] || experiment.snapshots[0]
  const stateVec = currentSnapshot?.state_vector || []
  const events = experiment.events || []

  return (
    <div className="xray-workspace-layout">
      {/* Top Banner */}
      <div className="xray-header-strip">
        <div>
          <h2 className="xray-title">MEMORY X-RAY</h2>
          <div className="xray-subtitle">Inspect what changed beneath the surface.</div>
        </div>
        <div className="xray-top-metrics">
          {diagnostics && (
            <>
              <div className="metric-pill">
                <span className="k">HEALTH:</span>
                <span className={`v ${diagnostics.health_score > 70 ? 'emerald' : 'amber'}`}>
                  {diagnostics.health_score.toFixed(1)} / 100
                </span>
              </div>
              <div className="metric-pill">
                <span className="k">HEADROOM:</span>
                <span className="v cyan">{(diagnostics.capacity_headroom * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-pill">
                <span className="k">INTERFERENCE RISK:</span>
                <span className={`v ${diagnostics.interference_risk > 0.5 ? 'crimson' : 'emerald'}`}>
                  {(diagnostics.interference_risk * 100).toFixed(1)}%
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 4-Pane Grid Layout */}
      <div className="xray-grid">
        {/* Pane 1: Left - Memory Map Points & Clusters */}
        <div className="xray-pane left-pane">
          <div className="pane-header">
            <span>☵</span>
            <span>TOPOLOGICAL REPRESENTATION MAP</span>
          </div>
          <div className="pane-body">
            <div className="points-summary">
              <span>PROJECTION: PCA (2D)</span>
              <span className="cyan">
                VAR: {((memoryMap?.variance_explained?.[0] || 0) * 100).toFixed(1)}% PC1
              </span>
            </div>
            <div className="xray-cues-list">
              {memoryMap?.points.map((pt) => {
                const isSelected = selectedMemoryId === pt.memory_id
                return (
                  <div
                    key={pt.memory_id}
                    className={`cue-row ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectMemory(pt.memory_id)}
                  >
                    <div className="cue-main">
                      <span className="cue-dot" style={{ background: isSelected ? '#00f0ff' : '#64748b' }} />
                      <span className="cue-label">{pt.label}</span>
                      <span className="cue-id">({pt.memory_id})</span>
                    </div>
                    <div className="cue-strength">
                      <div
                        className="strength-bar-fill"
                        style={{ width: `${Math.max(0, Math.min(100, pt.strength * 100))}%` }}
                      />
                      <span className="strength-val">{pt.strength.toFixed(2)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
            {memoryMap?.disclaimer && (
              <div className="epistemic-disclaimer">{memoryMap.disclaimer}</div>
            )}
          </div>
        </div>

        {/* Pane 2: Center - State Vector Microscope & Activation */}
        <div className="xray-pane center-pane">
          <div className="pane-header">
            <span>⚡</span>
            <span>HIGH-DIMENSIONAL VECTOR SUBSTRATE (d = {stateVec.length})</span>
          </div>
          <div className="pane-body">
            {/* Real State Vector Bar Grid */}
            <div className="vector-unit-grid">
              {stateVec.slice(0, 128).map((val, idx) => {
                const absVal = Math.abs(val)
                const isPositive = val >= 0
                const opacity = Math.min(1, absVal * 3)
                const color = isPositive ? `rgba(0, 240, 255, ${opacity})` : `rgba(239, 68, 68, ${opacity})`

                return (
                  <div
                    key={idx}
                    className="unit-cell"
                    style={{ background: color }}
                    title={`Unit ${idx}: ${val.toFixed(5)}`}
                  />
                )
              })}
            </div>

            {/* Quantitative Quantiles & Entropy */}
            {activationProfile && (
              <div className="activation-summary-card">
                <div className="stat-col">
                  <span className="stat-lbl">MEAN ACTIVATION:</span>
                  <span className="stat-val">{activationProfile.mean.toFixed(4)}</span>
                </div>
                <div className="stat-col">
                  <span className="stat-lbl">NORMALIZED ENTROPY:</span>
                  <span className="stat-val cyan">{activationProfile.entropy.toFixed(3)}</span>
                </div>
                <div className="stat-col">
                  <span className="stat-lbl">SPARSITY:</span>
                  <span className="stat-val emerald">{activationProfile.sparsity.toFixed(3)}</span>
                </div>
                <div className="stat-col">
                  <span className="stat-lbl">L2 NORM:</span>
                  <span className="stat-val">{activationProfile.l2_norm.toFixed(4)}</span>
                </div>
              </div>
            )}

            {/* Sparsity Trend Preview */}
            {sparsityAnalysis && (
              <div className="sparsity-strip">
                <div className="sparsity-meta">
                  <span>DIMENSIONAL SPARSITY OVER TIME:</span>
                  <span className="emerald">DEAD UNITS: {sparsityAnalysis.dead_units_count}</span>
                </div>
                <div className="sparsity-bars">
                  {sparsityAnalysis.timeline_sparsity.map((sp, i) => (
                    <div
                      key={i}
                      className="sparsity-bar-col"
                      style={{ height: `${Math.max(4, sp * 60)}px` }}
                      title={`Step ${i}: ${(sp * 100).toFixed(1)}% active`}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Pane 3: Right - State Difference Microscope & Anomalies */}
        <div className="xray-pane right-pane">
          <div className="pane-header">
            <span>🔬</span>
            <span>BEFORE / AFTER EVENT MICROSCOPE</span>
          </div>
          <div className="pane-body">
            {eventInspector ? (
              <div className="microscope-details">
                <div className="microscope-event-title">
                  EVENT {eventInspector.event_index + 1}: {eventInspector.concept_label} = {eventInspector.attribute_label}
                </div>

                <div className="before-after-viz">
                  <div className="state-bar-row">
                    <span className="lbl">BEFORE:</span>
                    <div className="state-bar">
                      <div
                        className="bar-fill"
                        style={{ width: `${Math.min(100, eventInspector.before_norm * 18)}%` }}
                      />
                    </div>
                    <span className="val">{eventInspector.before_norm.toFixed(3)}</span>
                  </div>
                  <div className="state-bar-row">
                    <span className="lbl">AFTER:</span>
                    <div className="state-bar">
                      <div
                        className="bar-fill"
                        style={{ width: `${Math.min(100, eventInspector.after_norm * 18)}%` }}
                      />
                    </div>
                    <span className="val">{eventInspector.after_norm.toFixed(3)}</span>
                  </div>
                </div>

                <div className="microscope-delta-stats">
                  <div className="delta-pill">
                    <span className="k">Δ NORM:</span>
                    <span className="v cyan">+{eventInspector.delta_norm.toFixed(4)}</span>
                  </div>
                  <div className="delta-pill">
                    <span className="k">COS SHIFT:</span>
                    <span className="v amber">+{eventInspector.cosine_shift.toFixed(4)}</span>
                  </div>
                </div>

                {/* Top Shifted Units */}
                <div className="top-units-section">
                  <div className="section-subtitle">TOP SHIFTED DIMENSIONS (Δu):</div>
                  <div className="unit-shifts-list">
                    {eventInspector.top_shifted_dimensions.slice(0, 6).map((u) => (
                      <div key={u.unit} className="unit-shift-row">
                        <span className="u-idx">Unit #{u.unit}</span>
                        <span className={`u-delta ${u.delta >= 0 ? 'emerald' : 'crimson'}`}>
                          {u.delta >= 0 ? '+' : ''}{u.delta.toFixed(4)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  type="button"
                  className="secondary small-btn"
                  style={{ marginTop: '0.75rem', width: '100%' }}
                  onClick={() =>
                    onViewEvidence(`Event ${eventInspector.event_index + 1} State Diff Evidence`, {
                      concept: eventInspector.concept_label,
                      attribute: eventInspector.attribute_label,
                      delta_norm: eventInspector.delta_norm,
                      cosine_shift: eventInspector.cosine_shift,
                      top_shifted_dimensions: eventInspector.top_shifted_dimensions,
                      before_norm: eventInspector.before_norm,
                      after_norm: eventInspector.after_norm,
                    })
                  }
                >
                  VIEW STATE DIFF EVIDENCE
                </button>
              </div>
            ) : (
              <div className="diff-placeholder">Select a timeline event below to inspect before/after impact.</div>
            )}

            {/* Anomaly Radar */}
            <div className="anomalies-section">
              <div className="section-subtitle">STATISTICAL ANOMALIES ({anomalies.length}):</div>
              {anomalies.length ? (
                <div className="anomalies-list">
                  {anomalies.map((anom, i) => (
                    <div key={i} className="anomaly-card">
                      <div className="anomaly-type crimson">{anom.anomaly_type}</div>
                      <div className="anomaly-desc">{anom.description}</div>
                      <div className="anomaly-meta">
                        <span>STEP {anom.step}</span>
                        <span>DEV: +{anom.deviation.toFixed(2)}σ</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-anomalies">● NO STATISTICAL INSTABILITIES DETECTED</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Timeline Step Bar */}
      <div className="xray-bottom-strip">
        <span className="strip-title">TIMELINE CHECKPOINTS:</span>
        <div className="checkpoints-row">
          {events.map((ev, i) => (
            <button
              key={i}
              className={`checkpoint-btn ${currentStep === i + 1 ? 'active primary' : ''}`}
              onClick={() => onStepChange(i + 1)}
            >
              E{String(i + 1).padStart(2, '0')} ({ev.concept_label})
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
