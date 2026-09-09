import React, { useState, useCallback, useEffect } from 'react'
import type { Experiment } from '../types'
import type {
  MemoryGenome,
  CascadeMap,
  DoseResponseEvaluation,
  FragilityReport,
  DependencyMatrix,
  CriticalMemoryRank,
  CentralityRecord,
} from '../types'
import {
  getMemoryGenome,
  runCascade,
  getCriticalMemories,
  getCentrality,
  getFragility,
  runDoseResponse,
  getDependencyMatrix,
} from '../api'
import { SynapticFingerprintStudioWorkspace } from './SynapticFingerprintStudioWorkspace'

interface Props {
  experiment: Experiment | null
  selectedMemoryId: string | null
  onSelectMemory: (id: string) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

type GenomeTab = 'dna' | 'cascade' | 'dose' | 'fragility' | 'matrix'

const DNA_SECTIONS = [
  { key: 'origin_bias', label: 'ORIGIN', color: 'var(--accent-cyan)' },
  { key: 'reinforcement_level', label: 'REINFORCE', color: 'var(--accent-emerald)' },
  { key: 'association_density', label: 'ASSOC', color: 'var(--accent-violet)' },
  { key: 'competition_pressure', label: 'COMPETE', color: 'var(--warning-amber)' },
  { key: 'retrieval_resilience', label: 'RETRIEVE', color: 'var(--accent-cyan)' },
  { key: 'historical_drift', label: 'DRIFT', color: 'var(--text-muted)' },
  { key: 'downstream_criticality', label: 'CRITICAL', color: 'var(--accent-emerald)' },
  { key: 'fragility_index', label: 'FRAGILITY', color: 'var(--danger-red)' },
]

const INTERVENTIONS = [
  { value: 'remove', label: 'REMOVE (ablate)' },
  { value: 'weaken', label: 'WEAKEN (dose=0.25)' },
  { value: 'strengthen', label: 'STRENGTHEN (boost)' },
  { value: 'suppress_reinforcement', label: 'SUPPRESS REINFORCE' },
]

export const GenomeWorkspace: React.FC<Props> = ({
  experiment,
  selectedMemoryId,
  onSelectMemory,
  onViewEvidence,
}) => {
  const [workspaceMode, setWorkspaceMode] = useState<'fingerprint' | 'cascade'>('fingerprint')
  const [activeTab, setActiveTab] = useState<GenomeTab>('dna')
  const [genome, setGenome] = useState<MemoryGenome | null>(null)
  const [cascade, setCascade] = useState<CascadeMap | null>(null)
  const [doseResponse, setDoseResponse] = useState<DoseResponseEvaluation | null>(null)
  const [fragility, setFragility] = useState<FragilityReport | null>(null)
  const [matrix, setMatrix] = useState<DependencyMatrix | null>(null)
  const [criticalMemories, setCriticalMemories] = useState<CriticalMemoryRank[]>([])
  const [centrality, setCentrality] = useState<CentralityRecord[]>([])
  const [isBusy, setIsBusy] = useState(false)
  const [selectedIntervention, setSelectedIntervention] = useState('remove')
  const [selectedDnaSection, setSelectedDnaSection] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const expId = experiment?.experiment_id
  const memId = selectedMemoryId || experiment?.events?.[0]?.id || ''

  // Load genome when experiment or memory changes
  useEffect(() => {
    if (!expId || !memId) return
    setGenome(null)
    setErrorMsg(null)
    getMemoryGenome(expId, memId)
      .then((r) => setGenome(r.genome))
      .catch((e) => setErrorMsg(String(e)))
  }, [expId, memId])

  // Load critical memories and centrality on experiment change
  useEffect(() => {
    if (!expId) return
    getCriticalMemories(expId)
      .then((r) => setCriticalMemories(r.critical_memories))
      .catch(() => {})
    getCentrality(expId)
      .then((r) => setCentrality(r.centrality))
      .catch(() => {})
  }, [expId])

  const handleRunCascade = useCallback(async () => {
    if (!expId || !memId) return
    setIsBusy(true)
    setErrorMsg(null)
    try {
      const r = await runCascade({
        experiment_id: expId,
        target_memory: memId,
        intervention: selectedIntervention,
        dose: selectedIntervention === 'weaken' ? 0.25 : 1.0,
      })
      setCascade(r.cascade)
      setActiveTab('cascade')
    } catch (e) {
      setErrorMsg(String(e))
    } finally {
      setIsBusy(false)
    }
  }, [expId, memId, selectedIntervention])

  const handleRunDoseResponse = useCallback(async () => {
    if (!expId || !memId) return
    setIsBusy(true)
    setErrorMsg(null)
    try {
      const r = await runDoseResponse({ experiment_id: expId, target_memory: memId })
      setDoseResponse(r.dose_response)
      setActiveTab('dose')
    } catch (e) {
      setErrorMsg(String(e))
    } finally {
      setIsBusy(false)
    }
  }, [expId, memId])

  const handleLoadFragility = useCallback(async () => {
    if (!expId || !memId) return
    setIsBusy(true)
    setErrorMsg(null)
    try {
      const r = await getFragility(expId, memId)
      setFragility(r.fragility)
      setActiveTab('fragility')
    } catch (e) {
      setErrorMsg(String(e))
    } finally {
      setIsBusy(false)
    }
  }, [expId, memId])

  const handleLoadMatrix = useCallback(async () => {
    if (!expId) return
    setIsBusy(true)
    setErrorMsg(null)
    try {
      const r = await getDependencyMatrix(expId, 'association')
      setMatrix(r.dependency_matrix)
      setActiveTab('matrix')
    } catch (e) {
      setErrorMsg(String(e))
    } finally {
      setIsBusy(false)
    }
  }, [expId])

  const dna = genome?.dna_strip

  const renderCascadeContent = () => {
    if (!experiment) {
      return (
        <div className="workspace-empty-state">
          <div className="empty-state-icon">🧬</div>
          <h2>Memory Genome & Cascade Engine</h2>
          <p>Run a memory experiment to inspect the structured genome of each memory — including origin, formation lineage, competitive associations, stability trajectory, and downstream cascade influence.</p>
        </div>
      )
    }

    return (
      <div className="genome-workspace">
        {/* Header */}
        <div className="workspace-header">
          <div className="workspace-title">
            <span className="workspace-icon">🧬</span>
            <span>MEMORY GENOME & CASCADE ENGINE</span>
            <span className="workspace-badge">PHASE 08</span>
          </div>
        <div className="workspace-meta">
          <span className="meta-chip">EXP: {expId?.slice(0, 12)}…</span>
          {memId && <span className="meta-chip active">MEM: {memId.slice(0, 16)}…</span>}
        </div>
      </div>

      {errorMsg && (
        <div className="genome-error-banner">
          ⚠ {errorMsg}
        </div>
      )}

      {/* Memory Selector */}
      <div className="genome-selector-row">
        <div className="genome-selector-label">TARGET MEMORY:</div>
        <div className="genome-selector-chips">
          {((experiment?.events) || []).slice(0, 12).map((ev) => (
            <button
              key={ev.id}
              className={`memory-chip ${memId === ev.id ? 'active' : ''}`}
              onClick={() => onSelectMemory(ev.id)}
              title={ev.concept_label}
            >
              {ev.concept_label || ev.id.slice(0, 10)}
            </button>
          ))}
        </div>
      </div>

      {/* DNA Strip */}
      {dna && (
        <div className="dna-strip">
          {DNA_SECTIONS.map((sec) => {
            const score = (dna as unknown as Record<string, number>)[sec.key] ?? 0
            return (
              <div
                key={sec.key}
                className={`dna-tile ${selectedDnaSection === sec.key ? 'selected' : ''}`}
                onClick={() => setSelectedDnaSection(selectedDnaSection === sec.key ? null : sec.key)}
                title={`${sec.label}: ${(score * 100).toFixed(0)}%`}
              >
                <div className="dna-tile-bar" style={{ height: `${Math.max(4, score * 100)}%`, background: sec.color }} />
                <div className="dna-tile-score" style={{ color: sec.color }}>{(score * 100).toFixed(0)}</div>
                <div className="dna-tile-label">{sec.label}</div>
              </div>
            )
          })}
          {selectedDnaSection && dna && (
            <div className="dna-section-detail">
              <span className="detail-key">{selectedDnaSection.toUpperCase()}:</span>
              <span className="detail-val">{((dna as unknown as Record<string, number>)[selectedDnaSection] * 100).toFixed(1)}%</span>
              <button className="btn-ghost btn-xs" onClick={() => onViewEvidence(`DNA: ${selectedDnaSection}`, dna as unknown as Record<string, unknown>)}>
                EVIDENCE
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab Bar */}
      <div className="genome-tab-bar">
        {([
          ['dna', '🧬 GENOME CORE'],
          ['cascade', '🌊 CASCADE SIM'],
          ['dose', '📈 DOSE-RESPONSE'],
          ['fragility', '🔬 FRAGILITY'],
          ['matrix', '🗃 DEPENDENCY MATRIX'],
        ] as [GenomeTab, string][]).map(([id, label]) => (
          <button
            key={id}
            className={`genome-tab ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      <div className="genome-panel">
        {/* === DNA CORE TAB === */}
        {activeTab === 'dna' && (
          <div className="genome-core-grid">
            {/* Genome Summary */}
            <div className="genome-summary-card">
              <div className="gc-section-title">MEMORY ORIGIN</div>
              {genome ? (
                <>
                  <div className="gc-row">
                    <span className="gc-key">Concept Label</span>
                    <span className="gc-val cyan">{genome.concept_label || '—'}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Origin Step</span>
                    <span className="gc-val">{genome.origin_step ?? '—'}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Current Strength</span>
                    <span className="gc-val emerald">{genome.current_strength?.toFixed(4) ?? '—'}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Stability</span>
                    <span className="gc-val">{genome.stability !== undefined ? `${(genome.stability * 100).toFixed(1)}%` : '—'}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Sensitivity</span>
                    <span className="gc-val amber">{genome.sensitivity?.toFixed(4) ?? '—'}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Associations</span>
                    <span className="gc-val">{genome.associations?.length ?? 0}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Competitors</span>
                    <span className="gc-val red">{genome.competitors?.length ?? 0}</span>
                  </div>
                  <div className="gc-row">
                    <span className="gc-key">Reinforcements</span>
                    <span className="gc-val">{genome.reinforcement_history?.length ?? 0}</span>
                  </div>
                </>
              ) : (
                <div className="gc-loading">Loading genome…</div>
              )}
            </div>

            {/* Associations */}
            <div className="genome-assoc-card">
              <div className="gc-section-title">ASSOCIATIONS</div>
              {genome?.associations?.length ? (
                <div className="assoc-list">
                  {genome.associations.slice(0, 8).map((a, i) => (
                    <div key={i} className="assoc-row">
                      <span className="assoc-mem" onClick={() => onSelectMemory(a.target_memory)} style={{ cursor: 'pointer', color: 'var(--accent-cyan)' }}>
                        {a.concept_label || a.target_memory.slice(0, 14)}
                      </span>
                      <div className="assoc-bar-bg">
                        <div className="assoc-bar-fill" style={{ width: `${(a.similarity * 100).toFixed(0)}%` }} />
                      </div>
                      <span className="assoc-score">{a.similarity.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="gc-empty">No strong associations detected.</div>
              )}
            </div>

            {/* Critical Memories */}
            <div className="genome-critical-card">
              <div className="gc-section-title">CRITICAL MEMORY RANKING</div>
              {criticalMemories.length ? (
                <div className="critical-list">
                  {criticalMemories.slice(0, 6).map((cm, i) => (
                    <div key={i} className={`critical-row`}
                      onClick={() => onSelectMemory(cm.memory_id)}
                    >
                      <span className={`tier-badge tier-${cm.classification?.toLowerCase() || 'low'}`}>{cm.classification}</span>
                      <span className="critical-label">{cm.concept_label || cm.memory_id.slice(0, 14)}</span>
                      <span className="critical-score">{cm.system_disruption?.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="gc-empty">
                  <button className="btn-primary btn-sm" onClick={() => {
                    if (expId) getCriticalMemories(expId).then(r => setCriticalMemories(r.critical_memories)).catch(() => {})
                  }}>
                    COMPUTE RANKINGS
                  </button>
                </div>
              )}
            </div>

            {/* Centrality */}
            <div className="genome-centrality-card">
              <div className="gc-section-title">CENTRALITY METRICS</div>
              {centrality.length ? (
                <div className="centrality-list">
                  {centrality.slice(0, 6).map((c, i) => (
                    <div key={i} className="centrality-row" onClick={() => onSelectMemory(c.memory_id)}>
                      <span className="cent-label">{c.concept_label || c.memory_id.slice(0, 14)}</span>
                      <div className="cent-bars">
                        <span className="cent-key">cent</span>
                        <div className="cent-bar-bg"><div className="cent-bar-fill" style={{ width: `${Math.min(100, c.centrality_score * 100)}%` }} /></div>
                        <span className="cent-key">eig</span>
                        <div className="cent-bar-bg"><div className="cent-bar-fill emerald" style={{ width: `${Math.min(100, c.eigenvector * 100)}%` }} /></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="gc-empty">Centrality data loading…</div>
              )}
            </div>
          </div>
        )}

        {/* === CASCADE TAB === */}
        {activeTab === 'cascade' && (
          <div className="cascade-panel">
            {/* Controls */}
            <div className="cascade-controls">
              <div className="ctrl-group">
                <label className="ctrl-label">INTERVENTION TYPE</label>
                <select
                  className="ctrl-select"
                  value={selectedIntervention}
                  onChange={(e) => setSelectedIntervention(e.target.value)}
                >
                  {INTERVENTIONS.map((i) => (
                    <option key={i.value} value={i.value}>{i.label}</option>
                  ))}
                </select>
              </div>
              <button
                className="btn-primary"
                onClick={handleRunCascade}
                disabled={isBusy || !memId}
              >
                {isBusy ? 'SIMULATING…' : '▶ RUN CASCADE SIMULATION'}
              </button>
              <button className="btn-secondary" onClick={handleRunDoseResponse} disabled={isBusy || !memId}>
                📈 DOSE-RESPONSE
              </button>
            </div>

            {cascade ? (
              <>
                {/* Cascade Summary */}
                <div className="cascade-summary">
                  <div className="cs-metric">
                    <span className="cs-key">TARGET</span>
                    <span className="cs-val cyan">{cascade.target_memory?.slice(0, 20)}</span>
                  </div>
                  <div className="cs-metric">
                    <span className="cs-key">DEPTH</span>
                    <span className="cs-val">{cascade.cascade_depth}</span>
                  </div>
                  <div className="cs-metric">
                    <span className="cs-key">MAGNITUDE</span>
                    <span className="cs-val amber">{cascade.cascade_magnitude?.toFixed(4)}</span>
                  </div>
                  <div className="cs-metric">
                    <span className="cs-key">FIRST DIVERGE</span>
                    <span className="cs-val red">t={cascade.first_divergence_step}</span>
                  </div>
                </div>

                {/* Cascade Ripple Graph */}
                <div className="cascade-ripple-grid">
                  {Object.entries(cascade.nodes || {}).slice(0, 24).map(([nid, node]) => (
                    <div
                      key={nid}
                      className={`ripple-node effect-${node.effect_type?.toLowerCase() || 'unchanged'}`}
                      onClick={() => onViewEvidence(`Cascade Node: ${nid}`, node as unknown as Record<string, unknown>)}
                    >
                      <div className="rn-label">{node.concept_label || nid.slice(0, 10)}</div>
                      <div className="rn-effect">{node.effect_type}</div>
                      <div className="rn-delta">{node.strength_delta?.toFixed(3) ?? '0.000'}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">🌊</div>
                <p>Select an intervention and click <strong>RUN CASCADE SIMULATION</strong> to visualize how intervening on this memory propagates through the system.</p>
              </div>
            )}
          </div>
        )}

        {/* === DOSE-RESPONSE TAB === */}
        {activeTab === 'dose' && (
          <div className="dose-panel">
            <div className="dose-controls">
              <button className="btn-primary" onClick={handleRunDoseResponse} disabled={isBusy || !memId}>
                {isBusy ? 'COMPUTING…' : '📈 RUN DOSE-RESPONSE EXPERIMENT'}
              </button>
            </div>

            {doseResponse ? (
              <>
                <div className="dose-header">
                  <span className="dose-pattern">{doseResponse.pattern?.toUpperCase()}</span>
                  {doseResponse.inflection_detected && (
                    <span className="dose-inflection">⚡ INFLECTION DETECTED at dose={doseResponse.threshold_dose?.toFixed(2)}</span>
                  )}
                </div>
                <div className="dose-chart">
                  {doseResponse.points?.map((pt, i) => (
                    <div key={i} className="dose-bar-col">
                      <div className="dose-divergence-bar" style={{ height: `${Math.min(100, pt.system_divergence * 200)}%` }} />
                      <div className="dose-label">{(pt.dose * 100).toFixed(0)}%</div>
                      <div className="dose-val">{pt.remaining_strength.toFixed(3)}</div>
                    </div>
                  ))}
                </div>
                <div className="dose-explanation">{doseResponse.explanation}</div>
              </>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">📈</div>
                <p>The Dose-Response experiment tests 5 intervention doses (0–100%) on this memory and measures system-wide divergence at each dose level, detecting thresholds and saturation effects.</p>
              </div>
            )}
          </div>
        )}

        {/* === FRAGILITY TAB === */}
        {activeTab === 'fragility' && (
          <div className="fragility-panel">
            <div className="fragility-controls">
              <button className="btn-primary" onClick={handleLoadFragility} disabled={isBusy || !memId}>
                {isBusy ? 'ANALYZING…' : '🔬 RUN FRAGILITY ANALYSIS'}
              </button>
            </div>

            {fragility ? (
              <>
                <div className="fragility-header">
                  <span className={`fragility-badge frag-${fragility.classification?.toLowerCase().replace(/_/g, '-') || 'inconclusive'}`}>
                    {fragility.classification?.replace(/_/g, ' ')}
                  </span>
                  <span className="fragility-spof">
                    {fragility.single_point_of_failure ? '⛔ SINGLE POINT OF FAILURE' : '✓ NOT SINGLE POINT OF FAILURE'}
                  </span>
                </div>
                <div className="fragility-metrics">
                  <div className="fm-row">
                    <span className="fm-key">Downstream Loss if Removed</span>
                    <span className="fm-val red">{(fragility.downstream_loss_if_removed * 100).toFixed(1)}%</span>
                  </div>
                  <div className="fm-row">
                    <span className="fm-key">System Coherence Drop</span>
                    <span className="fm-val amber">{(fragility.system_coherence_drop * 100).toFixed(1)}%</span>
                  </div>
                  <div className="fm-row">
                    <span className="fm-key">Compensation Available</span>
                    <span className={`fm-val ${fragility.compensation_available ? 'emerald' : 'red'}`}>
                      {fragility.compensation_available ? 'YES' : 'NO'}
                    </span>
                  </div>
                </div>
                <div className="fragility-explanation">{fragility.explanation}</div>
              </>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">🔬</div>
                <p>The Fragility Analysis measures how catastrophic it would be to remove or severely weaken this specific memory. It determines if this memory is a single point of failure with no redundant backup paths.</p>
              </div>
            )}
          </div>
        )}

        {/* === MATRIX TAB === */}
        {activeTab === 'matrix' && (
          <div className="matrix-panel">
            <div className="matrix-controls">
              <button className="btn-primary" onClick={handleLoadMatrix} disabled={isBusy}>
                {isBusy ? 'COMPUTING…' : '🗃 LOAD DEPENDENCY MATRIX'}
              </button>
            </div>

            {matrix ? (
              <div className="dependency-matrix-wrapper">
                <div className="matrix-header-row">
                  <div className="matrix-corner" />
                  {matrix.labels.map((lbl, j) => (
                    <div key={j} className="matrix-col-header">{lbl.slice(0, 8)}</div>
                  ))}
                </div>
                {matrix.matrix.map((row, i) => (
                  <div key={i} className="matrix-row">
                    <div className="matrix-row-header">{matrix.labels[i]?.slice(0, 8)}</div>
                    {row.map((val, j) => (
                      <div
                        key={j}
                        className="matrix-cell"
                        style={{
                          background: i === j ? 'var(--bg-surface)' : `rgba(99,102,241,${Math.min(1, Math.abs(val))})`,
                          color: Math.abs(val) > 0.5 ? '#fff' : 'var(--text-muted)',
                        }}
                        title={`${matrix.labels[i]} → ${matrix.labels[j]}: ${val.toFixed(3)}`}
                        onClick={() => onViewEvidence(`Dependency ${matrix.labels[i]} → ${matrix.labels[j]}`, { value: val, metric: matrix.metric })}
                      >
                        {val.toFixed(2)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">🗃</div>
                <p>The Dependency Matrix shows pairwise association and influence scores between all memories in the experiment as an N×N heatmap table.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
    )
  }

  return (
    <div className="genome-workspace-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div
        className="workspace-mode-selector"
        style={{
          display: 'flex',
          gap: '8px',
          padding: '8px 16px',
          backgroundColor: 'rgba(10, 15, 29, 0.95)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          alignItems: 'center',
          flexShrink: 0,
        }}
      >
        <button
          className={`btn-mode-toggle ${workspaceMode === 'fingerprint' ? 'active' : ''}`}
          onClick={() => setWorkspaceMode('fingerprint')}
          style={{
            padding: '6px 14px',
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.08em',
            borderRadius: '4px',
            border: workspaceMode === 'fingerprint' ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.12)',
            backgroundColor: workspaceMode === 'fingerprint' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            color: workspaceMode === 'fingerprint' ? '#38bdf8' : '#94a3b8',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>⚡</span> SYNAPTIC FINGERPRINT (PHASE 20)
        </button>
        <button
          className={`btn-mode-toggle ${workspaceMode === 'cascade' ? 'active' : ''}`}
          onClick={() => setWorkspaceMode('cascade')}
          style={{
            padding: '6px 14px',
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.08em',
            borderRadius: '4px',
            border: workspaceMode === 'cascade' ? '1px solid #a855f7' : '1px solid rgba(255, 255, 255, 0.12)',
            backgroundColor: workspaceMode === 'cascade' ? 'rgba(168, 85, 247, 0.15)' : 'transparent',
            color: workspaceMode === 'cascade' ? '#c084fc' : '#94a3b8',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>🧬</span> CASCADE GENETICS (PHASE 08)
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
          {workspaceMode === 'fingerprint' ? 'NEURAL FORENSIC SCANNER' : 'GENE CASCADE MAP'}
        </span>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
        {workspaceMode === 'fingerprint' ? (
          <SynapticFingerprintStudioWorkspace />
        ) : (
          renderCascadeContent()
        )}
      </div>
    </div>
  )
}

