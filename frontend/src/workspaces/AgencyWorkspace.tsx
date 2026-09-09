import React, { useState, useCallback, useEffect } from 'react'
import type { ResearchInvestigation, AgentOutputRecord, AgentCatalogEntry, WarRoomState } from '../types'
import {
  listAgents,
  runAgencyInvestigation,
  listAgencyInvestigations,
  getAgencyInvestigation,
  getWarRoom,
  exportAntigravitySkills,
} from '../api'

type AgencyTab = 'launcher' | 'war_room' | 'investigations' | 'agents' | 'graph'

const VERDICT_COLOR: Record<string, string> = {
  supported: 'var(--accent-emerald)',
  weakened: 'var(--warning-amber)',
  questionable: 'var(--warning-amber)',
  insufficient_evidence: 'var(--text-muted)',
  unknown: 'var(--text-muted)',
}

const STATUS_COLOR: Record<string, string> = {
  planning: 'var(--accent-cyan)',
  running: 'var(--accent-violet)',
  analyzing: 'var(--accent-violet)',
  challenging: 'var(--warning-amber)',
  requires_experiment: 'var(--warning-amber)',
  synthesizing: 'var(--accent-emerald)',
  completed: 'var(--accent-emerald)',
  inconclusive: 'var(--text-muted)',
  failed: 'var(--danger-red)',
  partially_complete: 'var(--warning-amber)',
}

const PRESET_QUESTIONS = [
  'Does increasing memory similarity increase interference?',
  'Does higher decay rate cause faster memory forgetting?',
  'Does update_strength increase memory retention?',
  'What is the relationship between memory conflicts and retrieval accuracy?',
]

const STATION_ICONS: Record<string, string> = {
  director: '🎯',
  experiment_lab: '⚗',
  memory_engine: '💾',
  analyst: '📊',
  red_team: '⛔',
  debate: '⚖',
  synthesis: '📝',
}

export const AgencyWorkspace: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AgencyTab>('launcher')
  const [researchQuestion, setResearchQuestion] = useState(PRESET_QUESTIONS[0])
  const [maxRounds, setMaxRounds] = useState(2)
  const [isBusy, setIsBusy] = useState(false)
  const [activeInvestigation, setActiveInvestigation] = useState<ResearchInvestigation | null>(null)
  const [investigations, setInvestigations] = useState<ResearchInvestigation[]>([])
  const [agents, setAgents] = useState<AgentCatalogEntry[]>([])
  const [warRoom, setWarRoom] = useState<WarRoomState | null>(null)
  const [exportResult, setExportResult] = useState<{ total_exported: number } | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<AgentCatalogEntry | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [runLog, setRunLog] = useState<string[]>([])

  // Load investigations and agents on mount
  useEffect(() => {
    listAgencyInvestigations()
      .then((r) => setInvestigations(r.investigations || []))
      .catch(() => {})
    listAgents()
      .then((r) => setAgents(r.agents || []))
      .catch(() => {})
  }, [])

  const handleRunInvestigation = useCallback(async () => {
    if (!researchQuestion.trim()) return
    setIsBusy(true)
    setErrorMsg(null)
    setActiveInvestigation(null)
    setWarRoom(null)
    setRunLog([])
    const log: string[] = []
    const addLog = (msg: string) => {
      log.push(msg)
      setRunLog([...log])
    }

    addLog('📋 Initializing Research Director...')
    addLog(`🔬 Question: "${researchQuestion}"`)
    addLog('🧪 Dispatching specialist agent pipeline...')

    try {
      addLog('⚗  Designing controlled parameter sweep...')
      addLog('💾 Executing memory engine with real vector arithmetic...')
      addLog('📊 Running parallel analysis agents...')
      addLog('⛔  Red Team adversarial review in progress...')
      if (maxRounds >= 2) {
        addLog('⚖  Structured disagreement detected — running counterfactual surgery...')
      }
      addLog('📝 Synthesizing multi-agent research conclusions...')

      const inv = await runAgencyInvestigation(researchQuestion, maxRounds)
      setActiveInvestigation(inv)
      addLog(`✅ Investigation complete: ${inv.investigation_id}`)
      addLog(`   Status: ${inv.status.toUpperCase()}`)
      addLog(`   Verdict: ${(inv.synthesis as { verdict?: string })?.verdict?.toUpperCase() ?? 'N/A'}`)
      addLog(`   Rounds: ${inv.round_number}`)
      addLog(`   Evidence pieces: ${inv.experiments.length + inv.counterfactuals.length}`)

      // Load war room
      getWarRoom(inv.investigation_id)
        .then((r) => setWarRoom(r.war_room))
        .catch(() => {})

      // Refresh list
      listAgencyInvestigations()
        .then((r) => setInvestigations(r.investigations || []))
        .catch(() => {})

      setActiveTab('war_room')
    } catch (e) {
      setErrorMsg(String(e))
      addLog(`❌ Error: ${String(e)}`)
    } finally {
      setIsBusy(false)
    }
  }, [researchQuestion, maxRounds])

  const handleLoadInvestigation = useCallback(async (id: string) => {
    try {
      const inv = await getAgencyInvestigation(id)
      setActiveInvestigation(inv)
      getWarRoom(id).then((r) => setWarRoom(r.war_room)).catch(() => {})
      setActiveTab('war_room')
    } catch (e) {
      setErrorMsg(String(e))
    }
  }, [])

  const handleExportSkills = useCallback(async () => {
    setIsBusy(true)
    try {
      const r = await exportAntigravitySkills()
      setExportResult(r)
    } catch (e) {
      setErrorMsg(String(e))
    } finally {
      setIsBusy(false)
    }
  }, [])

  const synth = activeInvestigation?.synthesis as { verdict?: string; summary?: string; confidence?: number; supporting_evidence_count?: number } | undefined

  return (
    <div className="agency-workspace">
      {/* Header */}
      <div className="workspace-header">
        <div className="workspace-title">
          <span className="workspace-icon">🤖</span>
          <span>AUTONOMOUS DISCOVERY ENGINE</span>
          <span className="workspace-badge">PHASE 09</span>
        </div>
        <div className="workspace-meta">
          <span className="meta-chip">{investigations.length} investigations</span>
          <span className="meta-chip active">{agents.length} agents registered</span>
        </div>
      </div>

      {errorMsg && (
        <div className="genome-error-banner">⚠ {errorMsg}</div>
      )}

      {/* Tab Bar */}
      <div className="genome-tab-bar">
        {([
          ['launcher', '🚀 LAUNCHER'],
          ['war_room', '⚔ WAR ROOM'],
          ['investigations', '📁 INVESTIGATIONS'],
          ['agents', '🤖 AGENT CATALOG'],
          ['graph', '🕸 RESEARCH GRAPH'],
        ] as [AgencyTab, string][]).map(([id, label]) => (
          <button
            key={id}
            className={`genome-tab ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="genome-panel">
        {/* === LAUNCHER === */}
        {activeTab === 'launcher' && (
          <div className="agency-launcher">
            <div className="launcher-hero">
              <div className="launcher-hero-title">MULTI-AGENT RESEARCH PIPELINE</div>
              <div className="launcher-hero-subtitle">
                Enter a research question. The system formulates hypotheses, designs controlled experiments,
                executes them on the real memory engine, submits results to specialist analysts,
                runs a hostile Red Team review, resolves disagreements via counterfactual surgery,
                and produces a grounded synthesis — never manufacturing findings.
              </div>
            </div>

            {/* Pipeline visualization */}
            <div className="pipeline-viz">
              {[
                { step: '1', icon: '❓', label: 'QUESTION', desc: 'Research Director decomposes' },
                { step: '2', icon: '💡', label: 'HYPOTHESES', desc: 'Formulate & pre-specify' },
                { step: '3', icon: '⚗', label: 'EXPERIMENT', desc: 'Validated parameter sweep' },
                { step: '4', icon: '💾', label: 'MEMORY ENGINE', desc: 'Real vector arithmetic' },
                { step: '5', icon: '📊', label: 'ANALYSIS', desc: 'Parallel specialists' },
                { step: '6', icon: '⛔', label: 'RED TEAM', desc: 'Hostile review' },
                { step: '7', icon: '⚖', label: 'DEBATE', desc: 'Structured disagreement' },
                { step: '8', icon: '🔬', label: 'COUNTERFACT', desc: 'Causal surgery' },
                { step: '9', icon: '📝', label: 'SYNTHESIS', desc: 'Grounded conclusion' },
              ].map((s, i) => (
                <div key={i} className="pipe-step">
                  <div className="pipe-icon">{s.icon}</div>
                  <div className="pipe-label">{s.label}</div>
                  <div className="pipe-desc">{s.desc}</div>
                  {i < 8 && <div className="pipe-arrow">→</div>}
                </div>
              ))}
            </div>

            {/* Question input */}
            <div className="launcher-form">
              <div className="form-section">
                <label className="form-label">RESEARCH QUESTION</label>
                <textarea
                  className="question-input"
                  value={researchQuestion}
                  onChange={(e) => setResearchQuestion(e.target.value)}
                  rows={2}
                  placeholder="Enter a causal or correlational research question about the memory system..."
                />
                <div className="preset-chips">
                  {PRESET_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      className={`preset-chip ${researchQuestion === q ? 'active' : ''}`}
                      onClick={() => setResearchQuestion(q)}
                    >
                      {q.slice(0, 50)}…
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-row">
                <div className="form-section half">
                  <label className="form-label">MAX INVESTIGATION ROUNDS</label>
                  <div className="rounds-selector">
                    {[1, 2, 3].map((r) => (
                      <button
                        key={r}
                        className={`rounds-btn ${maxRounds === r ? 'active' : ''}`}
                        onClick={() => setMaxRounds(r)}
                      >
                        {r} round{r !== 1 ? 's' : ''}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="form-section half">
                  <label className="form-label">PIPELINE MODE</label>
                  <div className="mode-info">Full 9-stage multi-agent pipeline with real memory engine execution, Red Team challenge, and counterfactual resolution.</div>
                </div>
              </div>

              <button
                className="btn-primary btn-large"
                onClick={handleRunInvestigation}
                disabled={isBusy || !researchQuestion.trim()}
              >
                {isBusy ? '🔄 RUNNING INVESTIGATION…' : '🚀 LAUNCH INVESTIGATION'}
              </button>
            </div>

            {/* Run log */}
            {runLog.length > 0 && (
              <div className="run-log">
                <div className="run-log-title">PIPELINE LOG</div>
                {runLog.map((line, i) => (
                  <div key={i} className="run-log-line">{line}</div>
                ))}
              </div>
            )}

            {/* Quick result */}
            {activeInvestigation && synth && (
              <div className="launcher-result">
                <div className="result-verdict" style={{ color: VERDICT_COLOR[synth.verdict || 'unknown'] || 'inherit' }}>
                  {synth.verdict?.toUpperCase() || 'PENDING'}
                </div>
                <div className="result-summary">{synth.summary}</div>
                <div className="result-meta">
                  Confidence: {((synth.confidence ?? 0) * 100).toFixed(0)}% ·
                  Evidence: {synth.supporting_evidence_count ?? 0} pieces ·
                  Rounds: {activeInvestigation.round_number}
                </div>
                <button className="btn-secondary btn-sm" onClick={() => setActiveTab('war_room')}>
                  VIEW FULL WAR ROOM →
                </button>
              </div>
            )}
          </div>
        )}

        {/* === WAR ROOM === */}
        {activeTab === 'war_room' && (
          <div className="war-room-panel">
            {activeInvestigation ? (
              <>
                {/* Investigation Header */}
                <div className="inv-header">
                  <div className="inv-id">{activeInvestigation.investigation_id}</div>
                  <div
                    className="inv-status"
                    style={{ color: STATUS_COLOR[activeInvestigation.status] || 'inherit' }}
                  >
                    {activeInvestigation.status.toUpperCase().replace(/_/g, ' ')}
                  </div>
                  <div className="inv-round">Round {activeInvestigation.round_number}</div>
                </div>

                <div className="inv-question">
                  ❓ {activeInvestigation.research_question}
                </div>

                {/* War Room Stations */}
                {warRoom && (
                  <div className="stations-grid">
                    {Object.entries(warRoom.stations).map(([key, station]) => (
                      <div key={key} className={`station-card status-${station.current_status?.toLowerCase().replace(/ /g, '-')}`}>
                        <div className="station-icon">{STATION_ICONS[key] || '👤'}</div>
                        <div className="station-name">{station.name}</div>
                        <div className="station-role">{station.role}</div>
                        <div className="station-status">{station.current_status}</div>
                        {station.verdict && (
                          <div
                            className="station-verdict"
                            style={{ color: VERDICT_COLOR[station.verdict] || 'inherit' }}
                          >
                            {station.verdict.toUpperCase()}
                          </div>
                        )}
                        {station.confidence !== null && station.confidence !== undefined && (
                          <div className="station-confidence">
                            conf: {(station.confidence * 100).toFixed(0)}%
                          </div>
                        )}
                        {(station.objection_count || 0) > 0 && (
                          <div className="station-objections">
                            ⚠ {station.objection_count} objection{station.objection_count !== 1 ? 's' : ''}
                          </div>
                        )}
                        <div className="station-last-action">{station.last_action}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Consensus Meter */}
                {warRoom && (
                  <div className="consensus-bar-wrapper">
                    <div className="consensus-label">CONSENSUS METER</div>
                    <div className="consensus-bar-bg">
                      <div
                        className="consensus-bar-fill"
                        style={{
                          width: `${warRoom.consensus_meter * 100}%`,
                          background: warRoom.consensus_meter >= 0.8
                            ? 'var(--accent-emerald)'
                            : warRoom.consensus_meter >= 0.5
                            ? 'var(--warning-amber)'
                            : 'var(--danger-red)',
                        }}
                      />
                    </div>
                    <div className="consensus-score">
                      {(warRoom.consensus_meter * 100).toFixed(0)}% consensus
                    </div>
                  </div>
                )}

                {/* Agent Outputs */}
                <div className="agent-outputs-section">
                  <div className="section-title-row">AGENT OUTPUTS</div>
                  {activeInvestigation.agent_outputs.map((out: AgentOutputRecord, i: number) => (
                    <div key={i} className={`agent-output-card verdict-${out.verdict}`}>
                      <div className="ao-header">
                        <span className="ao-agent">{out.agent}</span>
                        <span className="ao-verdict" style={{ color: VERDICT_COLOR[out.verdict] || 'inherit' }}>
                          {out.verdict.toUpperCase()}
                        </span>
                        <span className="ao-confidence">{(out.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="ao-analysis">{out.analysis}</div>
                      {out.objections.length > 0 && (
                        <div className="ao-objections">
                          {out.objections.map((obj, j) => (
                            <div key={j} className="ao-objection">⚠ {obj}</div>
                          ))}
                        </div>
                      )}
                      {out.recommendation && (
                        <div className="ao-recommendation">💡 {out.recommendation}</div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Disagreements */}
                {activeInvestigation.disagreements.length > 0 && (
                  <div className="disagreements-section">
                    <div className="section-title-row">STRUCTURED DISAGREEMENTS</div>
                    {activeInvestigation.disagreements.map((d, i) => (
                      <div key={i} className={`disagreement-card ${d.resolved ? 'resolved' : 'unresolved'}`}>
                        <div className="d-agents">{d.agent_a} ↔ {d.agent_b}</div>
                        <div className="d-issue">{d.underlying_issue}</div>
                        <div className="d-status">
                          {d.resolved ? '✅ RESOLVED by counterfactual evidence' : '⏳ PENDING RESOLUTION'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Synthesis */}
                {synth && synth.verdict && (
                  <div className="synthesis-card">
                    <div className="synth-header">
                      <span className="synth-title">RESEARCH SYNTHESIS</span>
                      <span className="synth-verdict" style={{ color: VERDICT_COLOR[synth.verdict] || 'inherit' }}>
                        {synth.verdict?.toUpperCase()}
                      </span>
                    </div>
                    <div className="synth-summary">{synth.summary}</div>
                    <div className="synth-meta">
                      <span>Evidence: {synth.supporting_evidence_count} pieces</span>
                      <span>Confidence: {((synth.confidence ?? 0) * 100).toFixed(0)}%</span>
                    </div>
                    {activeInvestigation.next_actions.length > 0 && (
                      <div className="synth-next-actions">
                        <div className="next-label">NEXT EXPERIMENTS RECOMMENDED:</div>
                        {activeInvestigation.next_actions.map((a, i) => (
                          <div key={i} className="next-action">→ {a}</div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">⚔</div>
                <p>Run a research investigation to see the War Room — the real-time status board showing all active specialist agents, their outputs, consensus meter, and structured debate resolution.</p>
                <button className="btn-primary" onClick={() => setActiveTab('launcher')}>
                  LAUNCH AN INVESTIGATION →
                </button>
              </div>
            )}
          </div>
        )}

        {/* === INVESTIGATIONS === */}
        {activeTab === 'investigations' && (
          <div className="investigations-panel">
            <div className="investigations-header">
              <div className="section-title-row">INVESTIGATION ARCHIVE</div>
              <button className="btn-secondary btn-sm" onClick={() => setActiveTab('launcher')}>
                + NEW INVESTIGATION
              </button>
            </div>
            {investigations.length ? (
              <div className="investigations-list">
                {investigations.map((inv) => {
                  const s = inv.synthesis as { verdict?: string } | undefined
                  return (
                    <div key={inv.investigation_id} className="investigation-row"
                      onClick={() => handleLoadInvestigation(inv.investigation_id)}
                    >
                      <div className="ir-id">{inv.investigation_id.slice(0, 16)}…</div>
                      <div className="ir-question">{inv.research_question}</div>
                      <div className="ir-meta">
                        <span className="ir-status" style={{ color: STATUS_COLOR[inv.status] || 'inherit' }}>
                          {inv.status.toUpperCase().replace(/_/g, ' ')}
                        </span>
                        {s?.verdict && (
                          <span className="ir-verdict" style={{ color: VERDICT_COLOR[s.verdict] || 'inherit' }}>
                            {s.verdict.toUpperCase()}
                          </span>
                        )}
                        <span className="ir-rounds">R{inv.round_number}</span>
                        <span className="ir-exps">{inv.experiments.length} exp</span>
                        <span className="ir-cfs">{inv.counterfactuals.length} cf</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">📁</div>
                <p>No investigations yet. Launch your first research investigation to begin building an empirical research archive.</p>
              </div>
            )}
          </div>
        )}

        {/* === AGENT CATALOG === */}
        {activeTab === 'agents' && (
          <div className="agents-panel">
            <div className="agents-header">
              <div className="section-title-row">SPECIALIST AGENT CATALOG</div>
              <div className="agents-meta">
                {agents.length} agents · MIT Licensed · msitarzewski/agency-agents
              </div>
              <button className="btn-secondary btn-sm" onClick={handleExportSkills} disabled={isBusy}>
                {isBusy ? 'EXPORTING…' : '⬇ EXPORT AS ANTIGRAVITY SKILLS'}
              </button>
              {exportResult && (
                <span className="export-badge">✅ Exported {exportResult.total_exported} skills</span>
              )}
            </div>
            <div className="agents-grid">
              {agents.map((agent) => (
                <div
                  key={agent.slug}
                  className={`agent-card ${selectedAgent?.slug === agent.slug ? 'selected' : ''}`}
                  onClick={() => setSelectedAgent(selectedAgent?.slug === agent.slug ? null : agent)}
                >
                  <div className="ac-division">{agent.division.toUpperCase()}</div>
                  <div className="ac-name">{agent.name}</div>
                  <div className="ac-vibe">{agent.vibe}</div>
                  <div className="ac-attribution">{agent.attribution}</div>
                </div>
              ))}
            </div>
            {selectedAgent && (
              <div className="agent-detail-panel">
                <div className="detail-header">
                  <div className="detail-name">{selectedAgent.name}</div>
                  <div className="detail-slug">/{selectedAgent.slug}</div>
                  <button className="btn-ghost btn-xs" onClick={() => setSelectedAgent(null)}>✕</button>
                </div>
                <div className="detail-vibe">"{selectedAgent.vibe}"</div>
                <div className="detail-instructions">{selectedAgent.instructions.slice(0, 600)}…</div>
                <div className="detail-attribution">🔗 {selectedAgent.attribution}</div>
              </div>
            )}
          </div>
        )}

        {/* === RESEARCH GRAPH === */}
        {activeTab === 'graph' && (
          <div className="graph-panel">
            {activeInvestigation ? (
              <>
                <div className="graph-header">
                  <div className="section-title-row">PROVENANCE GRAPH</div>
                  <div className="graph-meta">
                    Question → Hypotheses → Experiments → Observations → Analysis → Counterfactuals → Conclusion
                  </div>
                </div>
                {/* Node Legend */}
                <div className="graph-legend">
                  {[
                    ['question', 'var(--accent-cyan)', '❓'],
                    ['hypothesis', 'var(--accent-violet)', '💡'],
                    ['experiment', 'var(--accent-emerald)', '⚗'],
                    ['observation', 'var(--warning-amber)', '👁'],
                    ['agent_analysis', 'var(--accent-cyan)', '📊'],
                    ['counterfactual', 'var(--danger-red)', '🔬'],
                    ['conclusion', 'var(--accent-emerald)', '📝'],
                  ].map(([type, color, icon]) => (
                    <div key={type} className="legend-item">
                      <span style={{ color }}>{icon as string}</span>
                      <span className="legend-label">{(type as string).replace(/_/g, ' ').toUpperCase()}</span>
                    </div>
                  ))}
                </div>

                {/* Simplified node list as graph proxy */}
                <div className="graph-nodes">
                  <div className="graph-node-row node-question">
                    <span className="gn-icon">❓</span>
                    <span className="gn-type">QUESTION</span>
                    <span className="gn-label">{activeInvestigation.research_question}</span>
                  </div>
                  {activeInvestigation.initial_hypotheses.map((h: Record<string, unknown>, i) => (
                    <div key={i} className="graph-node-row node-hypothesis">
                      <span className="gn-icon">💡</span>
                      <span className="gn-type">HYPOTHESIS</span>
                      <span className="gn-label">{String(h.statement || '')}</span>
                    </div>
                  ))}
                  {activeInvestigation.experiments.map((e: Record<string, unknown>, i) => (
                    <div key={i} className="graph-node-row node-experiment">
                      <span className="gn-icon">⚗</span>
                      <span className="gn-type">EXPERIMENT</span>
                      <span className="gn-label">{String(e.title || e.experiment_id || '')}</span>
                    </div>
                  ))}
                  {activeInvestigation.observations.map((o: Record<string, unknown>, i) => (
                    <div key={i} className="graph-node-row node-observation">
                      <span className="gn-icon">👁</span>
                      <span className="gn-type">OBSERVATION</span>
                      <span className="gn-label">{String(o.label || '')}</span>
                    </div>
                  ))}
                  {activeInvestigation.agent_outputs.map((a: AgentOutputRecord, i: number) => (
                    <div key={i} className="graph-node-row node-analysis">
                      <span className="gn-icon">📊</span>
                      <span className="gn-type">AGENT: {a.agent}</span>
                      <span
                        className="gn-verdict"
                        style={{ color: VERDICT_COLOR[a.verdict] || 'inherit' }}
                      >
                        {a.verdict.toUpperCase()}
                      </span>
                    </div>
                  ))}
                  {activeInvestigation.counterfactuals.map((c: Record<string, unknown>, i) => (
                    <div key={i} className="graph-node-row node-counterfactual">
                      <span className="gn-icon">🔬</span>
                      <span className="gn-type">COUNTERFACTUAL</span>
                      <span className="gn-label">{String(c.title || c.counterfactual_id || '')}</span>
                    </div>
                  ))}
                  {synth?.verdict && (
                    <div className="graph-node-row node-conclusion">
                      <span className="gn-icon">📝</span>
                      <span className="gn-type">CONCLUSION</span>
                      <span className="gn-verdict" style={{ color: VERDICT_COLOR[synth.verdict] || 'inherit' }}>
                        {synth.verdict.toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="cascade-placeholder">
                <div className="placeholder-icon">🕸</div>
                <p>Run a research investigation to populate the provenance graph — a complete traceable chain from research question through hypotheses, experiments, agent analyses, counterfactuals, and final conclusions.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
