/**
 * CausalWorkspace.tsx — Phase 10: Causal Memory Lab
 *
 * Five integrated sub-panels:
 *   1. Scenario Builder       – design & validate causal interventions
 *   2. Counterfactual Replay  – split-screen divergence player
 *   3. Causal Graph           – interactive cascade + edge viewer
 *   4. Ledger & Claims        – versioned causal claims + conflicts
 *   5. Reports                – generate & browse causal investigation reports
 */

import React, { useCallback, useEffect, useRef, useState } from 'react'
import type { Experiment } from '../types'
import {
  causalCreateScenario,
  causalEstimateCost,
  causalGetCascadeTrace,
  causalGetCausalGraph,
  causalGetConflicts,
  causalGetCriticalWindows,
  causalGetFirstDivergence,
  causalGetLedger,
  causalGetMatrix,
  causalGetQueue,
  causalGetRecoveryCurve,
  causalGetReplay,
  causalGetReport,
  causalListReports,
  causalListScenarios,
  causalRegisterClaim,
  causalRunCounterfactual,
  causalRunMultiIntervention,
  causalRunRecovery,
  causalRunSwap,
  causalTestEdge,
  causalCreateReport,
} from '../api'

// ─── Local types ─────────────────────────────────────────────────────────────

interface CausalScenario {
  scenario_id: string
  experiment_id: string
  target_memory: string
  intervention: string
  timing?: number | null
  strength?: number | null
  label: string
  created_at: string
}

interface CausalCounterfactual {
  counterfactual_id: string
  parent_experiment_id: string
  divergence?: Record<string, unknown>
}

interface FirstDivergence {
  first_divergence_step: number | null
  cause_candidate: string | null
  magnitude: number
}

interface ReplayFrame {
  step: number
  original_event: string | null
  counterfactual_event: string | null
  divergence_magnitude: number
  is_first_divergence: boolean
}

interface CascadeNode {
  memory_id: string
  concept_label: string
  depth: number
  delta: number
  effect_type: string
}

interface CausalClaim {
  claim_id: string
  source_memory: string
  target_memory: string
  statement: string
  status: string
  version: number
  confidence?: number
  effect_consistency?: string
}

interface CausalLedger {
  claims: CausalClaim[]
  total_claims: number
  last_updated: string
}

interface CausalReport {
  report_id: string
  experiment_id: string
  question: string
  conclusion: string
  confidence_level: string
  created_at: string
}

// ─── Sub-panel types ──────────────────────────────────────────────────────────

type Panel = 'scenario' | 'replay' | 'graph' | 'ledger' | 'reports'

const PANELS: { id: Panel; label: string; icon: string }[] = [
  { id: 'scenario', label: 'Scenario Builder', icon: '⚙' },
  { id: 'replay', label: 'Counterfactual Replay', icon: '⏵' },
  { id: 'graph', label: 'Causal Graph', icon: '⬡' },
  { id: 'ledger', label: 'Ledger & Claims', icon: '📋' },
  { id: 'reports', label: 'Reports', icon: '📑' },
]

const INTERVENTIONS = ['REMOVE', 'STRENGTHEN', 'WEAKEN', 'SUPPRESS', 'AMPLIFY', 'FREEZE', 'RESTORE']

const STATUS_COLOR: Record<string, string> = {
  SUPPORTED_WITHIN_EXPERIMENT: '#00f0ff',
  CAUSAL: '#00ff7f',
  CONTESTED: '#ffd700',
  REFUTED: '#ff4c6a',
  PENDING: '#aaa',
}

// ─── Component ────────────────────────────────────────────────────────────────

interface CausalWorkspaceProps {
  experiment: Experiment | null
  onViewEvidence?: (title: string, details: Record<string, unknown>) => void
}

export const CausalWorkspace: React.FC<CausalWorkspaceProps> = ({
  experiment,
  onViewEvidence,
}) => {
  const [panel, setPanel] = useState<Panel>('scenario')

  // ── Scenario Builder state ─────────────────────────────────────────────────
  const [targetMemory, setTargetMemory] = useState('')
  const [intervention, setIntervention] = useState('REMOVE')
  const [timing, setTiming] = useState<string>('')
  const [strength, setStrength] = useState<string>('')
  const [scenarioLabel, setScenarioLabel] = useState('')
  const [scenarios, setScenarios] = useState<CausalScenario[]>([])
  const [scenarioBusy, setScenarioBusy] = useState(false)
  const [scenarioMsg, setScenarioMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [costEstimate, setCostEstimate] = useState<Record<string, unknown> | null>(null)
  const [criticalWindows, setCriticalWindows] = useState<Record<string, unknown> | null>(null)
  const [swapMemA, setSwapMemA] = useState('')
  const [swapMemB, setSwapMemB] = useState('')
  const [swapResult, setSwapResult] = useState<Record<string, unknown> | null>(null)
  const [multiTargets, setMultiTargets] = useState('')
  const [multiResult, setMultiResult] = useState<Record<string, unknown> | null>(null)

  // ── Counterfactual Replay state ────────────────────────────────────────────
  const [cfId, setCfId] = useState('')
  const [replayFrames, setReplayFrames] = useState<ReplayFrame[]>([])
  const [firstDiv, setFirstDiv] = useState<FirstDivergence | null>(null)
  const [replayStep, setReplayStep] = useState(0)
  const [replayPlaying, setReplayPlaying] = useState(false)
  const [replayBusy, setReplayBusy] = useState(false)
  const playRef = useRef(false)

  // ── Causal Graph state ─────────────────────────────────────────────────────
  const [graphMemory, setGraphMemory] = useState('')
  const [graphIntv, setGraphIntv] = useState('remove')
  const [cascadeNodes, setCascadeNodes] = useState<CascadeNode[]>([])
  const [cascadeEdges, setCascadeEdges] = useState<{ source: string; target: string; strength: number }[]>([])
  const [graphBusy, setGraphBusy] = useState(false)
  const [matrixData, setMatrixData] = useState<Record<string, unknown> | null>(null)
  const [edgeSrc, setEdgeSrc] = useState('')
  const [edgeTgt, setEdgeTgt] = useState('')
  const [edgeResult, setEdgeResult] = useState<Record<string, unknown> | null>(null)
  const [recoveryCurve, setRecoveryCurve] = useState<Record<string, unknown> | null>(null)
  const [temporalMap, setTemporalMap] = useState<Record<string, unknown> | null>(null)

  // ── Ledger & Claims state ──────────────────────────────────────────────────
  const [ledger, setLedger] = useState<CausalLedger | null>(null)
  const [conflicts, setConflicts] = useState<Record<string, unknown>[]>([])
  const [claimSrc, setClaimSrc] = useState('')
  const [claimTgt, setClaimTgt] = useState('')
  const [claimStmt, setClaimStmt] = useState('')
  const [claimStatus, setClaimStatus] = useState('SUPPORTED_WITHIN_EXPERIMENT')
  const [ledgerBusy, setLedgerBusy] = useState(false)
  const [claimMsg, setClaimMsg] = useState<{ ok: boolean; text: string } | null>(null)

  // ── Reports state ──────────────────────────────────────────────────────────
  const [reports, setReports] = useState<CausalReport[]>([])
  const [selectedReport, setSelectedReport] = useState<Record<string, unknown> | null>(null)
  const [reportQ, setReportQ] = useState('')
  const [reportConc, setReportConc] = useState('')
  const [reportBusy, setReportBusy] = useState(false)
  const [reportMsg, setReportMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const expId = experiment?.experiment_id ?? ''

  // ── Load scenarios on mount / experiment change ────────────────────────────
  useEffect(() => {
    if (!expId) return
    causalListScenarios(expId).then(setScenarios).catch(() => {})
    causalListReports(expId).then(setReports).catch(() => {})
    causalGetLedger().then(setLedger).catch(() => {})
  }, [expId])

  // ── Playback loop ──────────────────────────────────────────────────────────
  useEffect(() => {
    playRef.current = replayPlaying
    if (!replayPlaying) return
    const iv = setInterval(() => {
      setReplayStep((s) => {
        if (s >= replayFrames.length - 1) {
          setReplayPlaying(false)
          return s
        }
        return s + 1
      })
    }, 500)
    return () => clearInterval(iv)
  }, [replayPlaying, replayFrames.length])

  // ── Scenario Builder actions ───────────────────────────────────────────────
  const handleEstimateCost = async () => {
    if (!expId) return
    setScenarioBusy(true)
    try {
      const r = await causalEstimateCost({ experiment_id: expId, runs_required: 3 })
      setCostEstimate(r)
    } finally {
      setScenarioBusy(false)
    }
  }

  const handleCreateScenario = async () => {
    if (!expId || !targetMemory) {
      setScenarioMsg({ ok: false, text: 'Select a target memory first.' })
      return
    }
    setScenarioBusy(true)
    setScenarioMsg(null)
    try {
      await causalCreateScenario({
        experiment_id: expId,
        target_memory: targetMemory,
        intervention,
        timing: timing ? Number(timing) : undefined,
        strength: strength ? Number(strength) : undefined,
        label: scenarioLabel || `${intervention} ${targetMemory}`,
      })
      const list = await causalListScenarios(expId)
      setScenarios(list)
      setScenarioMsg({ ok: true, text: 'Scenario saved ✓' })
    } catch (e) {
      setScenarioMsg({ ok: false, text: String(e) })
    } finally {
      setScenarioBusy(false)
    }
  }

  const handleRunCounterfactual = async () => {
    if (!expId || !targetMemory) {
      setScenarioMsg({ ok: false, text: 'Set a target memory.' })
      return
    }
    setScenarioBusy(true)
    setScenarioMsg(null)
    try {
      const r = await causalRunCounterfactual({
        experiment_id: expId,
        target_memory: targetMemory,
        intervention,
        timing: timing ? Number(timing) : undefined,
        strength: strength ? Number(strength) : undefined,
        label: scenarioLabel || `${intervention} ${targetMemory}`,
      })
      setCfId(r.counterfactual?.counterfactual_id ?? '')
      setScenarioMsg({ ok: true, text: `Counterfactual ready — divergence @ step ${r.first_divergence?.first_divergence_step ?? '?'}` })
      setPanel('replay')
    } catch (e) {
      setScenarioMsg({ ok: false, text: String(e) })
    } finally {
      setScenarioBusy(false)
    }
  }

  const handleCriticalWindows = async () => {
    if (!expId || !targetMemory) return
    setScenarioBusy(true)
    try {
      const r = await causalGetCriticalWindows(expId, targetMemory)
      setCriticalWindows(r)
    } catch (e) {
      setCriticalWindows({ error: String(e) })
    } finally {
      setScenarioBusy(false)
    }
  }

  const handleSwap = async () => {
    if (!expId || !swapMemA || !swapMemB) return
    setScenarioBusy(true)
    try {
      const r = await causalRunSwap({ experiment_id: expId, memory_a: swapMemA, memory_b: swapMemB })
      setSwapResult(r)
    } catch (e) {
      setSwapResult({ error: String(e) })
    } finally {
      setScenarioBusy(false)
    }
  }

  const handleMultiIntervention = async () => {
    if (!expId || !multiTargets) return
    setScenarioBusy(true)
    try {
      const specs = multiTargets.split(',').map((m) => ({
        memory_id: m.trim(),
        intervention: intervention,
        dose: strength ? Number(strength) : 1.0,
      }))
      const r = await causalRunMultiIntervention({ experiment_id: expId, interventions: specs })
      setMultiResult(r)
    } catch (e) {
      setMultiResult({ error: String(e) })
    } finally {
      setScenarioBusy(false)
    }
  }

  // ── Replay actions ─────────────────────────────────────────────────────────
  const handleLoadReplay = useCallback(async () => {
    if (!expId || !cfId) return
    setReplayBusy(true)
    try {
      const [replayData, divData] = await Promise.all([
        causalGetReplay(expId, cfId),
        causalGetFirstDivergence(cfId),
      ])
      setReplayFrames(replayData.frames ?? [])
      setFirstDiv(divData)
      setReplayStep(0)
    } catch (e) {
      setReplayFrames([])
    } finally {
      setReplayBusy(false)
    }
  }, [expId, cfId])

  // ── Graph actions ──────────────────────────────────────────────────────────
  const handleLoadCascade = async () => {
    if (!expId || !graphMemory) return
    setGraphBusy(true)
    try {
      const r = await causalGetCascadeTrace(expId, graphMemory, graphIntv)
      setCascadeNodes(r.nodes ?? [])
      setCascadeEdges(r.edges ?? [])
    } catch {
      setCascadeNodes([])
    } finally {
      setGraphBusy(false)
    }
  }

  const handleLoadMatrix = async () => {
    if (!expId) return
    setGraphBusy(true)
    try {
      const r = await causalGetMatrix(expId)
      setMatrixData(r)
    } finally {
      setGraphBusy(false)
    }
  }

  const handleTestEdge = async () => {
    if (!expId || !edgeSrc || !edgeTgt) return
    setGraphBusy(true)
    try {
      const r = await causalTestEdge({ experiment_id: expId, source_memory: edgeSrc, target_memory: edgeTgt })
      setEdgeResult(r)
    } catch (e) {
      setEdgeResult({ error: String(e) })
    } finally {
      setGraphBusy(false)
    }
  }

  const handleRecoveryCurve = async () => {
    if (!expId || !graphMemory) return
    setGraphBusy(true)
    try {
      const r = await causalGetRecoveryCurve(expId, graphMemory)
      setRecoveryCurve(r)
    } catch (e) {
      setRecoveryCurve({ error: String(e) })
    } finally {
      setGraphBusy(false)
    }
  }

  // ── Ledger actions ─────────────────────────────────────────────────────────
  const handleLoadLedger = async () => {
    setLedgerBusy(true)
    try {
      const [l, c] = await Promise.all([causalGetLedger(), causalGetConflicts()])
      setLedger(l)
      setConflicts(c)
    } finally {
      setLedgerBusy(false)
    }
  }

  const handleRegisterClaim = async () => {
    if (!expId || !claimSrc || !claimTgt || !claimStmt) {
      setClaimMsg({ ok: false, text: 'Fill in all claim fields.' })
      return
    }
    setLedgerBusy(true)
    setClaimMsg(null)
    try {
      await causalRegisterClaim({
        source_memory: claimSrc,
        target_memory: claimTgt,
        statement: claimStmt,
        status: claimStatus,
        evidence_experiment_ids: [expId],
      })
      const l = await causalGetLedger()
      setLedger(l)
      setClaimMsg({ ok: true, text: 'Claim registered ✓' })
    } catch (e) {
      setClaimMsg({ ok: false, text: String(e) })
    } finally {
      setLedgerBusy(false)
    }
  }

  // ── Report actions ─────────────────────────────────────────────────────────
  const handleGenerateReport = async () => {
    if (!expId || !reportQ) {
      setReportMsg({ ok: false, text: 'Provide a research question.' })
      return
    }
    setReportBusy(true)
    setReportMsg(null)
    try {
      await causalCreateReport({
        experiment_id: expId,
        question: reportQ,
        conclusion: reportConc || 'Pending analysis.',
        scenario: `Experiment ${expId}`,
      })
      const list = await causalListReports(expId)
      setReports(list)
      setReportMsg({ ok: true, text: 'Report created ✓' })
    } catch (e) {
      setReportMsg({ ok: false, text: String(e) })
    } finally {
      setReportBusy(false)
    }
  }

  const handleViewReport = async (reportId: string) => {
    try {
      const r = await causalGetReport(reportId)
      setSelectedReport(r)
    } catch {}
  }

  // ─── Helpers ───────────────────────────────────────────────────────────────
  const memories = experiment?.events.map((e) => e.id ?? e.concept_label ?? '').filter(Boolean) ?? []
  const uniqueMemories = [...new Set(memories)]

  const currentFrame = replayFrames[replayStep] ?? null

  const maxDivergence = replayFrames.reduce((m, f) => Math.max(m, f.divergence_magnitude), 0.001)

  if (!experiment) {
    return (
      <div className="causal-empty">
        <div className="causal-empty-icon">⚗</div>
        <div className="causal-empty-title">Causal Memory Lab</div>
        <div className="causal-empty-sub">Run or load an experiment to begin causal analysis.</div>
      </div>
    )
  }

  return (
    <div className="causal-workspace">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="causal-header">
        <div className="causal-header-left">
          <span className="causal-icon">⚗</span>
          <span className="causal-title">CAUSAL MEMORY LAB</span>
          <span className="causal-subtitle">Phase 10 · Counterfactual Engine</span>
        </div>
        <div className="causal-header-right">
          <span className="causal-exp-pill">{expId.slice(0, 12)}…</span>
          <span className="causal-mem-count">{uniqueMemories.length} memories</span>
        </div>
      </div>

      {/* ── Panel tabs ─────────────────────────────────────────────────────── */}
      <div className="causal-tabs">
        {PANELS.map((p) => (
          <button
            key={p.id}
            className={`causal-tab ${panel === p.id ? 'active' : ''}`}
            onClick={() => setPanel(p.id)}
          >
            <span className="causal-tab-icon">{p.icon}</span>
            <span>{p.label}</span>
          </button>
        ))}
      </div>

      {/* ── Panel: Scenario Builder ─────────────────────────────────────────── */}
      {panel === 'scenario' && (
        <div className="causal-panel">
          <div className="causal-panel-cols">
            {/* Left: Intervention Designer */}
            <div className="causal-col">
              <div className="causal-section-header">⚙ INTERVENTION DESIGNER</div>

              <div className="causal-field-group">
                <label className="causal-label">TARGET MEMORY</label>
                {uniqueMemories.length > 0 ? (
                  <select
                    className="causal-select"
                    value={targetMemory}
                    onChange={(e) => setTargetMemory(e.target.value)}
                  >
                    <option value="">— select memory —</option>
                    {uniqueMemories.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="causal-input"
                    placeholder="memory_id"
                    value={targetMemory}
                    onChange={(e) => setTargetMemory(e.target.value)}
                  />
                )}
              </div>

              <div className="causal-field-group">
                <label className="causal-label">INTERVENTION TYPE</label>
                <div className="causal-chip-row">
                  {INTERVENTIONS.map((iv) => (
                    <button
                      key={iv}
                      className={`causal-chip ${intervention === iv ? 'active' : ''}`}
                      onClick={() => setIntervention(iv)}
                    >
                      {iv}
                    </button>
                  ))}
                </div>
              </div>

              <div className="causal-field-row">
                <div className="causal-field-group half">
                  <label className="causal-label">TIMING (step)</label>
                  <input
                    type="number"
                    className="causal-input"
                    placeholder="auto"
                    value={timing}
                    onChange={(e) => setTiming(e.target.value)}
                  />
                </div>
                <div className="causal-field-group half">
                  <label className="causal-label">STRENGTH (0–2)</label>
                  <input
                    type="number"
                    className="causal-input"
                    placeholder="1.0"
                    step="0.1"
                    value={strength}
                    onChange={(e) => setStrength(e.target.value)}
                  />
                </div>
              </div>

              <div className="causal-field-group">
                <label className="causal-label">SCENARIO LABEL</label>
                <input
                  className="causal-input"
                  placeholder={`${intervention} ${targetMemory || 'memory'}`}
                  value={scenarioLabel}
                  onChange={(e) => setScenarioLabel(e.target.value)}
                />
              </div>

              <div className="causal-action-row">
                <button
                  className="causal-btn secondary"
                  onClick={handleEstimateCost}
                  disabled={scenarioBusy}
                >
                  ∑ Estimate Cost
                </button>
                <button
                  className="causal-btn secondary"
                  onClick={handleCreateScenario}
                  disabled={scenarioBusy}
                >
                  💾 Save Scenario
                </button>
                <button
                  className="causal-btn primary"
                  onClick={handleRunCounterfactual}
                  disabled={scenarioBusy || !targetMemory}
                >
                  ▶ Run Counterfactual
                </button>
              </div>

              {scenarioMsg && (
                <div className={`causal-msg ${scenarioMsg.ok ? 'ok' : 'err'}`}>
                  {scenarioMsg.text}
                </div>
              )}

              {costEstimate && (
                <div className="causal-card small">
                  <div className="causal-card-title">COST ESTIMATE</div>
                  <div className="causal-kv-grid">
                    {Object.entries(costEstimate).map(([k, v]) => (
                      <React.Fragment key={k}>
                        <span className="kv-key">{k}</span>
                        <span className="kv-val">{String(v)}</span>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {/* Critical Windows */}
              <div className="causal-section-header" style={{ marginTop: 20 }}>⏱ CRITICAL WINDOWS</div>
              <div className="causal-action-row">
                <button
                  className="causal-btn secondary"
                  onClick={handleCriticalWindows}
                  disabled={scenarioBusy || !targetMemory}
                >
                  Detect Windows
                </button>
              </div>
              {criticalWindows && (
                <div className="causal-card small">
                  <pre className="causal-pre">{JSON.stringify(criticalWindows, null, 2)}</pre>
                </div>
              )}
            </div>

            {/* Right: Saved scenarios + advanced ops */}
            <div className="causal-col">
              <div className="causal-section-header">📂 SAVED SCENARIOS ({scenarios.length})</div>
              <div className="causal-list">
                {scenarios.length === 0 && (
                  <div className="causal-empty-list">No scenarios yet. Design one on the left.</div>
                )}
                {scenarios.map((sc) => (
                  <div key={sc.scenario_id} className="causal-list-item">
                    <div className="cli-top">
                      <span className="cli-label">{sc.label}</span>
                      <span className={`cli-badge ${sc.intervention.toLowerCase()}`}>{sc.intervention}</span>
                    </div>
                    <div className="cli-meta">
                      <span>target: {sc.target_memory}</span>
                      {sc.timing != null && <span>t={sc.timing}</span>}
                      {sc.strength != null && <span>s={sc.strength}</span>}
                    </div>
                  </div>
                ))}
              </div>

              {/* Memory Swap */}
              <div className="causal-section-header" style={{ marginTop: 20 }}>🔀 MEMORY SWAP</div>
              <div className="causal-field-row">
                <input
                  className="causal-input half"
                  placeholder="Memory A"
                  value={swapMemA}
                  onChange={(e) => setSwapMemA(e.target.value)}
                />
                <input
                  className="causal-input half"
                  placeholder="Memory B"
                  value={swapMemB}
                  onChange={(e) => setSwapMemB(e.target.value)}
                />
              </div>
              <button
                className="causal-btn secondary"
                onClick={handleSwap}
                disabled={scenarioBusy || !swapMemA || !swapMemB}
              >
                Run Swap
              </button>
              {swapResult && (
                <div className="causal-card small">
                  <pre className="causal-pre">{JSON.stringify(swapResult, null, 2)}</pre>
                </div>
              )}

              {/* Multi-Intervention */}
              <div className="causal-section-header" style={{ marginTop: 20 }}>⬡ MULTI-INTERVENTION</div>
              <div className="causal-field-group">
                <label className="causal-label">TARGETS (comma-separated)</label>
                <input
                  className="causal-input"
                  placeholder="mem_a, mem_b, mem_c"
                  value={multiTargets}
                  onChange={(e) => setMultiTargets(e.target.value)}
                />
              </div>
              <button
                className="causal-btn secondary"
                onClick={handleMultiIntervention}
                disabled={scenarioBusy || !multiTargets}
              >
                Run Multi-Intervention
              </button>
              {multiResult && (
                <div className="causal-card small">
                  <div className="causal-card-title">INTERACTION RESULT</div>
                  <pre className="causal-pre">{JSON.stringify(multiResult, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Panel: Counterfactual Replay ───────────────────────────────────── */}
      {panel === 'replay' && (
        <div className="causal-panel">
          <div className="causal-section-header">⏵ SPLIT-SCREEN COUNTERFACTUAL REPLAY</div>
          <div className="causal-field-row" style={{ marginBottom: 12 }}>
            <input
              className="causal-input"
              placeholder="counterfactual_id"
              value={cfId}
              onChange={(e) => setCfId(e.target.value)}
              style={{ flex: 1 }}
            />
            <button
              className="causal-btn primary"
              onClick={handleLoadReplay}
              disabled={replayBusy || !cfId}
            >
              {replayBusy ? 'Loading…' : '↯ Load Replay'}
            </button>
          </div>

          {replayFrames.length === 0 && (
            <div className="causal-empty-list">
              Run a counterfactual in the Scenario Builder, then load it here.
            </div>
          )}

          {replayFrames.length > 0 && (
            <>
              {/* First divergence banner */}
              {firstDiv && (
                <div className="causal-div-banner">
                  <span className="div-icon">⚠</span>
                  <span>First divergence at step <strong>{firstDiv.first_divergence_step ?? '?'}</strong></span>
                  {firstDiv.cause_candidate && (
                    <span> — candidate cause: <strong>{firstDiv.cause_candidate}</strong></span>
                  )}
                  <span className="div-mag">Δ={firstDiv.magnitude?.toFixed(4) ?? '?'}</span>
                </div>
              )}

              {/* Divergence timeline bar */}
              <div className="replay-timeline">
                {replayFrames.map((f, i) => {
                  const pct = (f.divergence_magnitude / maxDivergence) * 100
                  return (
                    <div
                      key={i}
                      className={`replay-tick ${i === replayStep ? 'current' : ''} ${f.is_first_divergence ? 'div-point' : ''}`}
                      style={{ '--pct': `${pct}%` } as React.CSSProperties}
                      onClick={() => setReplayStep(i)}
                      title={`Step ${f.step}: Δ=${f.divergence_magnitude.toFixed(4)}`}
                    />
                  )
                })}
              </div>

              {/* Controls */}
              <div className="replay-controls">
                <button className="replay-btn" onClick={() => setReplayStep((s) => Math.max(0, s - 1))}>◀</button>
                <button
                  className={`replay-btn play ${replayPlaying ? 'active' : ''}`}
                  onClick={() => setReplayPlaying((p) => !p)}
                >
                  {replayPlaying ? '⏸' : '▶'}
                </button>
                <button
                  className="replay-btn"
                  onClick={() => setReplayStep((s) => Math.min(replayFrames.length - 1, s + 1))}
                >
                  ▶
                </button>
                <span className="replay-counter">Step {replayStep + 1} / {replayFrames.length}</span>
              </div>

              {/* Split screen */}
              {currentFrame && (
                <div className="replay-split">
                  <div className={`replay-world original ${currentFrame.is_first_divergence ? 'diverged' : ''}`}>
                    <div className="replay-world-label">⦿ ORIGINAL WORLD</div>
                    <div className="replay-world-step">Step {currentFrame.step}</div>
                    <div className="replay-world-event">
                      {currentFrame.original_event ?? <span className="muted">—</span>}
                    </div>
                    <div className="replay-world-delta">Δ = {currentFrame.divergence_magnitude.toFixed(4)}</div>
                  </div>
                  <div className="replay-divider">
                    <div className="replay-div-line" />
                    <div className="replay-div-label">vs</div>
                    <div className="replay-div-line" />
                  </div>
                  <div className={`replay-world counterfactual ${currentFrame.is_first_divergence ? 'diverged' : ''}`}>
                    <div className="replay-world-label">◎ COUNTERFACTUAL WORLD</div>
                    <div className="replay-world-step">Step {currentFrame.step}</div>
                    <div className="replay-world-event">
                      {currentFrame.counterfactual_event ?? <span className="muted">—</span>}
                    </div>
                    {currentFrame.is_first_divergence && (
                      <div className="replay-first-div-badge">⚠ FIRST DIVERGENCE</div>
                    )}
                  </div>
                </div>
              )}

              {/* Frame table */}
              <div className="replay-frame-table">
                <table className="causal-table">
                  <thead>
                    <tr>
                      <th>Step</th>
                      <th>Original Event</th>
                      <th>CF Event</th>
                      <th>Δ Magnitude</th>
                      <th>Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {replayFrames.map((f, i) => (
                      <tr
                        key={i}
                        className={`${i === replayStep ? 'selected-row' : ''} ${f.is_first_divergence ? 'diverge-row' : ''}`}
                        onClick={() => setReplayStep(i)}
                      >
                        <td className="mono">{f.step}</td>
                        <td>{f.original_event ?? '—'}</td>
                        <td>{f.counterfactual_event ?? '—'}</td>
                        <td className="mono">{f.divergence_magnitude.toFixed(4)}</td>
                        <td>{f.is_first_divergence ? <span className="badge-warn">⚠ DIVERGE</span> : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Panel: Causal Graph ────────────────────────────────────────────── */}
      {panel === 'graph' && (
        <div className="causal-panel">
          <div className="causal-panel-cols">
            <div className="causal-col">
              <div className="causal-section-header">⬡ CASCADE TRACE</div>
              <div className="causal-field-group">
                <label className="causal-label">TARGET MEMORY</label>
                <input
                  className="causal-input"
                  placeholder="memory_id"
                  value={graphMemory}
                  onChange={(e) => setGraphMemory(e.target.value)}
                />
              </div>
              <div className="causal-field-group">
                <label className="causal-label">INTERVENTION</label>
                <select
                  className="causal-select"
                  value={graphIntv}
                  onChange={(e) => setGraphIntv(e.target.value)}
                >
                  {INTERVENTIONS.map((i) => (
                    <option key={i} value={i.toLowerCase()}>{i}</option>
                  ))}
                </select>
              </div>
              <div className="causal-action-row">
                <button
                  className="causal-btn primary"
                  onClick={handleLoadCascade}
                  disabled={graphBusy || !graphMemory}
                >
                  {graphBusy ? '…' : '▶ Trace Cascade'}
                </button>
                <button
                  className="causal-btn secondary"
                  onClick={handleRecoveryCurve}
                  disabled={graphBusy || !graphMemory}
                >
                  ↺ Recovery Curve
                </button>
                <button
                  className="causal-btn secondary"
                  onClick={handleLoadMatrix}
                  disabled={graphBusy}
                >
                  ⊞ Causality Matrix
                </button>
              </div>

              {/* Cascade nodes */}
              {cascadeNodes.length > 0 && (
                <div className="causal-cascade-vis">
                  {cascadeNodes.map((n) => (
                    <div
                      key={n.memory_id}
                      className="cascade-node"
                      style={{ '--depth': n.depth } as React.CSSProperties}
                    >
                      <div className="cn-header">
                        <span className="cn-id">{n.memory_id.slice(0, 10)}</span>
                        <span className={`cn-effect ${n.effect_type}`}>{n.effect_type}</span>
                        <span className="cn-delta">Δ={n.delta.toFixed(3)}</span>
                      </div>
                      <div className="cn-label">{n.concept_label}</div>
                      <div className="cn-depth-bar">
                        {'▪'.repeat(n.depth + 1)}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Edges */}
              {cascadeEdges.length > 0 && (
                <div className="causal-card small" style={{ marginTop: 12 }}>
                  <div className="causal-card-title">CAUSAL EDGES ({cascadeEdges.length})</div>
                  {cascadeEdges.slice(0, 10).map((e, i) => (
                    <div key={i} className="edge-row">
                      <span className="edge-src">{e.source.slice(0, 8)}</span>
                      <span className="edge-arrow">→</span>
                      <span className="edge-tgt">{e.target.slice(0, 8)}</span>
                      <span className="edge-str">{e.strength.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Recovery curve */}
              {recoveryCurve && (
                <div className="causal-card small" style={{ marginTop: 12 }}>
                  <div className="causal-card-title">↺ RECOVERY CURVE</div>
                  <pre className="causal-pre">{JSON.stringify(recoveryCurve, null, 2)}</pre>
                </div>
              )}
            </div>

            <div className="causal-col">
              {/* Edge Tester */}
              <div className="causal-section-header">🔬 EDGE TESTER</div>
              <div className="causal-field-row">
                <input
                  className="causal-input half"
                  placeholder="Source memory"
                  value={edgeSrc}
                  onChange={(e) => setEdgeSrc(e.target.value)}
                />
                <span style={{ color: 'var(--accent-cyan)', padding: '0 8px' }}>→</span>
                <input
                  className="causal-input half"
                  placeholder="Target memory"
                  value={edgeTgt}
                  onChange={(e) => setEdgeTgt(e.target.value)}
                />
              </div>
              <button
                className="causal-btn primary"
                onClick={handleTestEdge}
                disabled={graphBusy || !edgeSrc || !edgeTgt}
              >
                Test Edge
              </button>
              {edgeResult && (
                <div className="causal-card small">
                  <div className="causal-card-title">EDGE EVIDENCE</div>
                  <div className="causal-kv-grid">
                    {Object.entries(edgeResult).map(([k, v]) => (
                      <React.Fragment key={k}>
                        <span className="kv-key">{k}</span>
                        <span className="kv-val">{String(v)}</span>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {/* Causality Matrix */}
              {matrixData && (
                <div className="causal-card small" style={{ marginTop: 16 }}>
                  <div className="causal-card-title">⊞ CAUSALITY MATRIX</div>
                  {Array.isArray((matrixData as Record<string, unknown>).matrix) ? (
                    <div className="causal-matrix">
                      {((matrixData as Record<string, unknown>).memory_ids as string[])?.map((rowId: string, ri: number) => (
                        <div key={ri} className="matrix-row">
                          <span className="matrix-label">{rowId.slice(0, 6)}</span>
                          {(((matrixData as Record<string, unknown>).matrix as number[][])[ri] ?? []).map((v: number, ci: number) => (
                            <div
                              key={ci}
                              className="matrix-cell"
                              style={{ '--intensity': Math.abs(v) } as React.CSSProperties}
                              title={`${rowId}→${((matrixData as Record<string, unknown>).memory_ids as string[])[ci]}: ${v.toFixed(3)}`}
                            />
                          ))}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <pre className="causal-pre">{JSON.stringify(matrixData, null, 2)}</pre>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Panel: Ledger & Claims ─────────────────────────────────────────── */}
      {panel === 'ledger' && (
        <div className="causal-panel">
          <div className="causal-panel-cols">
            <div className="causal-col">
              <div className="causal-section-header">📋 CAUSALITY LEDGER</div>
              <div className="causal-action-row">
                <button
                  className="causal-btn secondary"
                  onClick={handleLoadLedger}
                  disabled={ledgerBusy}
                >
                  ↺ Refresh Ledger
                </button>
              </div>

              {ledger && (
                <div className="causal-ledger-stats">
                  <div className="ledger-stat">
                    <span className="ls-val">{ledger.total_claims}</span>
                    <span className="ls-key">TOTAL CLAIMS</span>
                  </div>
                  <div className="ledger-stat">
                    <span className="ls-val err">{conflicts.length}</span>
                    <span className="ls-key">CONFLICTS</span>
                  </div>
                  <div className="ledger-stat">
                    <span className="ls-val muted">{ledger.last_updated?.slice(0, 10) ?? '—'}</span>
                    <span className="ls-key">LAST UPDATED</span>
                  </div>
                </div>
              )}

              <div className="causal-list" style={{ maxHeight: 340 }}>
                {(!ledger || ledger.claims.length === 0) && (
                  <div className="causal-empty-list">No claims in ledger yet.</div>
                )}
                {ledger?.claims.map((c) => (
                  <div key={c.claim_id} className="causal-claim-card">
                    <div className="cc-header">
                      <span
                        className="cc-status-dot"
                        style={{ background: STATUS_COLOR[c.status] ?? '#888' }}
                      />
                      <span className="cc-status">{c.status}</span>
                      <span className="cc-version">v{c.version}</span>
                    </div>
                    <div className="cc-stmt">{c.statement}</div>
                    <div className="cc-route">
                      <span className="cc-mem">{c.source_memory.slice(0, 10)}</span>
                      <span className="cc-arrow">→</span>
                      <span className="cc-mem">{c.target_memory.slice(0, 10)}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Conflicts */}
              {conflicts.length > 0 && (
                <>
                  <div className="causal-section-header warn" style={{ marginTop: 16 }}>
                    ⚠ CONTRADICTIONS ({conflicts.length})
                  </div>
                  {conflicts.map((c, i) => (
                    <div key={i} className="conflict-card">
                      <pre className="causal-pre">{JSON.stringify(c, null, 2)}</pre>
                    </div>
                  ))}
                </>
              )}
            </div>

            <div className="causal-col">
              {/* Register new claim */}
              <div className="causal-section-header">✎ REGISTER CAUSAL CLAIM</div>
              <div className="causal-field-group">
                <label className="causal-label">SOURCE MEMORY</label>
                <input
                  className="causal-input"
                  value={claimSrc}
                  onChange={(e) => setClaimSrc(e.target.value)}
                  placeholder="source_memory_id"
                />
              </div>
              <div className="causal-field-group">
                <label className="causal-label">TARGET MEMORY</label>
                <input
                  className="causal-input"
                  value={claimTgt}
                  onChange={(e) => setClaimTgt(e.target.value)}
                  placeholder="target_memory_id"
                />
              </div>
              <div className="causal-field-group">
                <label className="causal-label">CLAIM STATEMENT</label>
                <textarea
                  className="causal-textarea"
                  rows={3}
                  value={claimStmt}
                  onChange={(e) => setClaimStmt(e.target.value)}
                  placeholder="e.g. Removing memory A causes a 40% reduction in memory B activation…"
                />
              </div>
              <div className="causal-field-group">
                <label className="causal-label">STATUS</label>
                <select
                  className="causal-select"
                  value={claimStatus}
                  onChange={(e) => setClaimStatus(e.target.value)}
                >
                  <option value="SUPPORTED_WITHIN_EXPERIMENT">SUPPORTED WITHIN EXPERIMENT</option>
                  <option value="CAUSAL">CAUSAL</option>
                  <option value="CONTESTED">CONTESTED</option>
                  <option value="REFUTED">REFUTED</option>
                  <option value="PENDING">PENDING</option>
                </select>
              </div>
              <button
                className="causal-btn primary"
                onClick={handleRegisterClaim}
                disabled={ledgerBusy}
              >
                Register Claim
              </button>
              {claimMsg && (
                <div className={`causal-msg ${claimMsg.ok ? 'ok' : 'err'}`}>{claimMsg.text}</div>
              )}

              {/* Epistemological reminder */}
              <div className="causal-epistem-box">
                <div className="epistem-title">⚠ CAUTIOUS EPISTEMOLOGY</div>
                <ul className="epistem-list">
                  <li>Correlation ≠ causation. Test edges before claiming causality.</li>
                  <li>Claims are only as strong as the number of replications.</li>
                  <li>Contested claims must not be promoted without replication.</li>
                  <li>Register conflicts; do not delete contradictory evidence.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Panel: Reports ─────────────────────────────────────────────────── */}
      {panel === 'reports' && (
        <div className="causal-panel">
          <div className="causal-panel-cols">
            <div className="causal-col">
              <div className="causal-section-header">📑 CAUSAL INVESTIGATION REPORTS</div>
              <div className="causal-list" style={{ maxHeight: 380 }}>
                {reports.length === 0 && (
                  <div className="causal-empty-list">No reports yet. Generate one on the right.</div>
                )}
                {reports.map((r) => (
                  <div
                    key={r.report_id}
                    className="causal-list-item clickable"
                    onClick={() => handleViewReport(r.report_id)}
                  >
                    <div className="cli-top">
                      <span className="cli-label">{r.question.slice(0, 60)}</span>
                      <span className={`cli-badge conf-${r.confidence_level?.toLowerCase()}`}>
                        {r.confidence_level}
                      </span>
                    </div>
                    <div className="cli-meta">
                      <span>{r.created_at?.slice(0, 10)}</span>
                      <span>{r.experiment_id.slice(0, 12)}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Report detail viewer */}
              {selectedReport && (
                <div className="causal-report-viewer">
                  <div className="causal-card-title">📑 REPORT DETAIL</div>
                  <div className="report-section">
                    <span className="report-key">QUESTION</span>
                    <span className="report-val">{String((selectedReport as Record<string,unknown>).question ?? '')}</span>
                  </div>
                  <div className="report-section">
                    <span className="report-key">CONCLUSION</span>
                    <span className="report-val">{String((selectedReport as Record<string,unknown>).conclusion ?? '')}</span>
                  </div>
                  <div className="report-section">
                    <span className="report-key">CONFIDENCE</span>
                    <span className={`report-confidence ${String((selectedReport as Record<string,unknown>).confidence_level ?? '').toLowerCase()}`}>
                      {String((selectedReport as Record<string,unknown>).confidence_level ?? '')}
                    </span>
                  </div>
                  {(selectedReport as Record<string,unknown>).limitations && (
                    <div className="report-section">
                      <span className="report-key">LIMITATIONS</span>
                      <span className="report-val warn">{String((selectedReport as Record<string,unknown>).limitations)}</span>
                    </div>
                  )}
                  <button
                    className="causal-btn secondary small"
                    onClick={() => onViewEvidence?.('Causal Report', selectedReport as Record<string, unknown>)}
                  >
                    View Full Evidence
                  </button>
                </div>
              )}
            </div>

            <div className="causal-col">
              <div className="causal-section-header">✎ GENERATE REPORT</div>
              <div className="causal-field-group">
                <label className="causal-label">RESEARCH QUESTION</label>
                <textarea
                  className="causal-textarea"
                  rows={3}
                  value={reportQ}
                  onChange={(e) => setReportQ(e.target.value)}
                  placeholder="What would have happened if memory X had never existed?"
                />
              </div>
              <div className="causal-field-group">
                <label className="causal-label">PRELIMINARY CONCLUSION</label>
                <textarea
                  className="causal-textarea"
                  rows={3}
                  value={reportConc}
                  onChange={(e) => setReportConc(e.target.value)}
                  placeholder="Removing memory X caused a 35% reduction in recall accuracy…"
                />
              </div>
              <button
                className="causal-btn primary"
                onClick={handleGenerateReport}
                disabled={reportBusy || !reportQ}
              >
                Generate Report
              </button>
              {reportMsg && (
                <div className={`causal-msg ${reportMsg.ok ? 'ok' : 'err'}`}>{reportMsg.text}</div>
              )}

              {/* Report guidance */}
              <div className="causal-epistem-box" style={{ marginTop: 20 }}>
                <div className="epistem-title">📐 REPORT STANDARDS</div>
                <ul className="epistem-list">
                  <li>State the exact intervention and timing used.</li>
                  <li>Report first divergence step and magnitude.</li>
                  <li>List all alternative causal paths considered.</li>
                  <li>Acknowledge limitations of single-experiment evidence.</li>
                  <li>Use confidence levels: HIGH / MODERATE / LOW / SPECULATIVE.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
