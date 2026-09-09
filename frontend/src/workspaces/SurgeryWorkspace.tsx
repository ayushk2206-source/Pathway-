import React, { useEffect, useMemo, useState } from 'react'
import type {
  Experiment,
  MemoryXRay,
  SurgeryRecallComparison,
  SurgerySession,
  SynapseXRayDetail,
  SynapticNetworkState,
} from '../types'
import {
  getMemoryXRay,
  getSurgeryState,
  getSynapseXRay,
  getSynapticState,
  lockSurgeryBaseline,
  resetSurgery,
  restoreSynapses,
  runSurgeryRecall,
  silenceSynapses,
  strengthenSynapses,
  weakenSynapses,
} from '../api'
import { SynapticNetworkCanvas } from '../components/SynapticNetworkCanvas'
import { SynapticSurgeryPanel } from '../components/SynapticSurgeryPanel'
import { SurgeryResultPanel } from '../components/SurgeryResultPanel'
import { SurgeryLogPanel } from '../components/SurgeryLogPanel'
import '../surgery.css'

interface SurgeryWorkspaceProps {
  experiment?: Experiment | null
  onViewEvidence?: (title: string, details: Record<string, unknown>) => void
}

export const SurgeryWorkspace: React.FC<SurgeryWorkspaceProps> = () => {
  // Dimension & engine params
  const [dimension] = useState<number>(16)
  const [decay] = useState<number>(0.05)
  const [seed] = useState<number>(42)

  // Network state for canvas rendering
  const [networkState, setNetworkState] = useState<SynapticNetworkState | null>(null)
  const [isBusy, setIsBusy] = useState<boolean>(false)
  const [canvasLayout, setCanvasLayout] = useState<'bipartite' | 'matrix'>('bipartite')

  // Surgery Session State
  const [session, setSession] = useState<SurgerySession | null>(null)
  const [isLocked, setIsLocked] = useState<boolean>(false)

  // Selection state
  const [selectedSynapseIds, setSelectedSynapseIds] = useState<string[]>([])
  const [activeSynapseDetail, setActiveSynapseDetail] = useState<SynapseXRayDetail | null>(null)

  // Memory X-Ray state
  const [xrayConcept, setXrayConcept] = useState<string>('color')
  const [xrayExpected, setXrayExpected] = useState<string>('blue')
  const [xrayBranch, setXrayBranch] = useState<'live' | 'baseline' | 'surgery'>('live')
  const [memoryXRay, setMemoryXRay] = useState<MemoryXRay | null>(null)
  const [xrayFilterTier, setXrayFilterTier] = useState<string>('all')

  // Recall comparison state
  const [recallComparison, setRecallComparison] = useState<SurgeryRecallComparison | null>(null)

  // Methodology modal
  const [showMethodology, setShowMethodology] = useState<boolean>(false)

  // Load initial network state and surgery state
  useEffect(() => {
    refreshAll()
  }, [])

  const refreshAll = async () => {
    setIsBusy(true)
    try {
      const [net, surg] = await Promise.all([
        getSynapticState(dimension, decay, seed),
        getSurgeryState(),
      ])
      setNetworkState(net)
      setIsLocked(surg.locked)
      setSession(surg.session)
      if (surg.session?.last_comparison) {
        setRecallComparison(surg.session.last_comparison)
      }
      // Populate default concept if write history exists
      if (net.history_timeline && net.history_timeline.length > 0) {
        const writeEv = net.history_timeline.find(
          (e) => e.event_type === 'WRITE' && e.details && typeof e.details.concept === 'string'
        )
        if (writeEv && writeEv.details) {
          setXrayConcept(writeEv.details.concept as string)
          if (typeof writeEv.details.value === 'string') {
            setXrayExpected(writeEv.details.value as string)
          }
        }
      }
    } catch (err) {
      console.error('Failed to load surgery workspace data:', err)
    } finally {
      setIsBusy(false)
    }
  }

  // Update synapse detail when a single synapse is selected
  useEffect(() => {
    if (selectedSynapseIds.length === 1 && isLocked) {
      getSynapseXRay(selectedSynapseIds[0])
        .then((detail) => setActiveSynapseDetail(detail))
        .catch(() => setActiveSynapseDetail(null))
    } else {
      setActiveSynapseDetail(null)
    }
  }, [selectedSynapseIds, isLocked])

  // Map of synapse relevance for canvas coloring
  const xrayRelevanceMap = useMemo(() => {
    const map = new Map<string, { tier: string; score: number }>()
    if (memoryXRay?.synapses) {
      memoryXRay.synapses.forEach((s) => {
        map.set(s.synapse_id, { tier: s.relevance_tier, score: s.relevance_score })
      })
    }
    return map
  }, [memoryXRay])

  // Filtered synapses list for table
  const filteredXRaySynapses = useMemo(() => {
    if (!memoryXRay) return []
    if (xrayFilterTier === 'all') return memoryXRay.synapses
    return memoryXRay.synapses.filter((s) => s.relevance_tier === xrayFilterTier)
  }, [memoryXRay, xrayFilterTier])

  // Lock baseline
  const handleLockBaseline = async () => {
    setIsBusy(true)
    try {
      const res = await lockSurgeryBaseline({ dimension, seed, decay })
      setSession(res.session)
      setIsLocked(true)
      setXrayBranch('surgery')
    } catch (err) {
      console.error('Lock baseline error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  // Surgery operations
  const handleWeaken = async (factor: number) => {
    if (!selectedSynapseIds.length) return
    setIsBusy(true)
    try {
      const res = await weakenSynapses(selectedSynapseIds, factor)
      setSession(res.session)
      await updateSynapsesAfterSurgery()
    } catch (err) {
      console.error('Weaken error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  const handleStrengthen = async (factor: number) => {
    if (!selectedSynapseIds.length) return
    setIsBusy(true)
    try {
      const res = await strengthenSynapses(selectedSynapseIds, factor)
      setSession(res.session)
      await updateSynapsesAfterSurgery()
    } catch (err) {
      console.error('Strengthen error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  const handleSilence = async () => {
    if (!selectedSynapseIds.length) return
    setIsBusy(true)
    try {
      const res = await silenceSynapses(selectedSynapseIds)
      setSession(res.session)
      await updateSynapsesAfterSurgery()
    } catch (err) {
      console.error('Silence error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  const handleRestore = async () => {
    if (!selectedSynapseIds.length) return
    setIsBusy(true)
    try {
      const res = await restoreSynapses(selectedSynapseIds)
      setSession(res.session)
      await updateSynapsesAfterSurgery()
    } catch (err) {
      console.error('Restore error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  const handleReset = async () => {
    setIsBusy(true)
    try {
      const res = await resetSurgery()
      setSession(res.session)
      setRecallComparison(null)
      setSelectedSynapseIds([])
      await updateSynapsesAfterSurgery()
    } catch (err) {
      console.error('Reset error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  // Update canvas synapses and active detail after surgery ops
  const updateSynapsesAfterSurgery = async () => {
    if (selectedSynapseIds.length === 1 && isLocked) {
      try {
        const d = await getSynapseXRay(selectedSynapseIds[0])
        setActiveSynapseDetail(d)
      } catch {}
    }
    // Re-run Memory X-Ray if concept was already inspected
    if (memoryXRay) {
      handleRunMemoryXRay(xrayConcept, xrayExpected)
    }
  }

  // Memory X-Ray execution
  const handleRunMemoryXRay = async (concept: string, expected?: string) => {
    if (!concept.trim()) return
    setIsBusy(true)
    try {
      const xray = await getMemoryXRay({
        query_concept: concept.trim(),
        expected_value: expected?.trim() || undefined,
        dimension,
        seed,
        decay,
        branch: isLocked ? xrayBranch : 'live',
      })
      setMemoryXRay(xray)
    } catch (err) {
      console.error('Memory X-Ray error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  // Run Recall comparison
  const handleRunRecallComparison = async (concept: string, expected?: string) => {
    if (!concept.trim()) return
    setIsBusy(true)
    try {
      const res = await runSurgeryRecall({
        query_concept: concept.trim(),
        expected_value: expected?.trim() || undefined,
      })
      setRecallComparison(res.comparison)
      setSession(res.session)
    } catch (err) {
      console.error('Surgery recall error:', err)
    } finally {
      setIsBusy(false)
    }
  }

  // Select all high relevance synapses from current X-Ray
  const handleSelectHighRelevance = () => {
    if (!memoryXRay) return
    const highIds = memoryXRay.synapses
      .filter((s) => s.relevance_tier === 'high')
      .map((s) => s.synapse_id)
    setSelectedSynapseIds(highIds)
  }

  // Toggle synapse selection
  const handleToggleSynapse = (synId: string) => {
    setSelectedSynapseIds((prev) =>
      prev.includes(synId) ? prev.filter((id) => id !== synId) : [...prev, synId]
    )
  }

  // Available concepts from write history
  const availableConcepts = useMemo(() => {
    const concepts: string[] = []
    if (networkState?.history_timeline) {
      for (const ev of networkState.history_timeline) {
        if (ev.details && typeof ev.details.concept === 'string') {
          if (!concepts.includes(ev.details.concept)) {
            concepts.push(ev.details.concept)
          }
        }
      }
    }
    return concepts
  }, [networkState])

  return (
    <div className="surgery-workspace">
      {/* ── Top Header ─────────────────────────────────────────────── */}
      <header className="surgery-header">
        <div className="header-left-title">
          <div className="title-row">
            <span className="surgery-header-glyph">⚕</span>
            <h1 className="surgery-header-h1">SYNAPTIC SURGERY & MEMORY X-RAY</h1>
            <span className="surgery-phase-tag">PHASE 15</span>
          </div>
          <p className="surgery-header-sub">
            Forensic causality & controlled ablation laboratory on associative matrix substrate
          </p>
        </div>

        {/* Telemetry pill row */}
        <div className="surgery-header-telemetry">
          <div className="telemetry-pill">
            <span className="pill-label">BRANCH</span>
            <span className={`pill-val ${isLocked ? 'cyan' : 'emerald'}`}>
              {isLocked ? 'EXPERIMENTAL BRANCH' : 'LIVE BRAIN'}
            </span>
          </div>
          <div className="telemetry-pill">
            <span className="pill-label">DIMENSION</span>
            <span className="pill-val mono">d={dimension}</span>
          </div>
          <div className="telemetry-pill">
            <span className="pill-label">SELECTED</span>
            <span className="pill-val mono amber">{selectedSynapseIds.length} syn</span>
          </div>
          <div className="telemetry-pill">
            <span className="pill-label">STATUS</span>
            <span className={`pill-val ${isLocked ? 'amber' : 'slate'}`}>
              {isLocked ? 'BASELINE LOCKED' : 'UNLOCKED'}
            </span>
          </div>
        </div>

        <div className="surgery-header-actions">
          <button
            className="btn-scientific-info"
            onClick={() => setShowMethodology(true)}
            title="Scientific Methodology & Theoretical Derivation"
          >
            ⓘ Methodology
          </button>
          <button
            className="btn-refresh-state"
            onClick={refreshAll}
            disabled={isBusy}
            title="Reload current brain state"
          >
            ↻ Sync State
          </button>
        </div>
      </header>

      {/* ── Main Dual-Section Scientific Layout ────────────────────── */}
      <div className="surgery-main-grid">
        {/* ── Left Column: Network Canvas & Memory X-Ray ───────────── */}
        <div className="surgery-left-col">
          {/* Canvas Section */}
          <div className="canvas-wrapper-card">
            <div className="canvas-header-bar">
              <div className="canvas-title-group">
                <span className="canvas-title">SYNAPTIC TRANSMISSION MAPPING</span>
                {memoryXRay && (
                  <span className="xray-active-label">
                    X-Ray Active: <strong>{memoryXRay.query_concept}</strong>
                  </span>
                )}
              </div>

              <div className="canvas-controls">
                <button
                  type="button"
                  className={`btn-mode-toggle ${canvasLayout === 'bipartite' ? 'active' : ''}`}
                  onClick={() => setCanvasLayout('bipartite')}
                >
                  Bipartite Network
                </button>
                <button
                  type="button"
                  className={`btn-mode-toggle ${canvasLayout === 'matrix' ? 'active' : ''}`}
                  onClick={() => setCanvasLayout('matrix')}
                >
                  Crossbar Matrix
                </button>
              </div>
            </div>

            {/* Network Canvas */}
            {networkState && (
              <SynapticNetworkCanvas
                dimension={dimension}
                neurons={networkState.neurons}
                synapses={networkState.synapses}
                lastPathway={networkState.last_pathway}
                selectedNeuronId={null}
                selectedSynapseId={selectedSynapseIds[0] || null}
                onSelectNeuron={() => {}}
                onSelectSynapse={(synId) => {
                  if (synId) handleToggleSynapse(synId)
                }}
                layoutMode={canvasLayout}
                xrayRelevanceMap={xrayRelevanceMap}
              />
            )}

            {/* Canvas Legend */}
            <div className="canvas-footer-legend">
              <span className="legend-item">
                <span className="dot dot-high" /> High Relevance (&ge;50%)
              </span>
              <span className="legend-item">
                <span className="dot dot-mod" /> Moderate (&ge;20%)
              </span>
              <span className="legend-item">
                <span className="dot dot-weak" /> Weak (&ge;5%)
              </span>
              <span className="legend-item">
                <span className="dot dot-unrel" /> Unrelated (&lt;5%)
              </span>
            </div>
          </div>

          {/* Memory X-Ray Panel */}
          <div className="xray-panel-card">
            <div className="xray-panel-header">
              <div className="xray-header-left">
                <span className="xray-icon">⌬</span>
                <div>
                  <h3 className="xray-title">MEMORY X-RAY</h3>
                  <span className="xray-sub">
                    Identify synaptic connections computationally responsible for recall
                  </span>
                </div>
              </div>

              {isLocked && (
                <div className="branch-selector">
                  <span className="branch-label">EVALUATE BRANCH:</span>
                  <button
                    type="button"
                    className={`btn-branch ${xrayBranch === 'live' ? 'active' : ''}`}
                    onClick={() => setXrayBranch('live')}
                  >
                    Live
                  </button>
                  <button
                    type="button"
                    className={`btn-branch ${xrayBranch === 'baseline' ? 'active' : ''}`}
                    onClick={() => setXrayBranch('baseline')}
                  >
                    Baseline
                  </button>
                  <button
                    type="button"
                    className={`btn-branch ${xrayBranch === 'surgery' ? 'active' : ''}`}
                    onClick={() => setXrayBranch('surgery')}
                  >
                    Surgery
                  </button>
                </div>
              )}
            </div>

            {/* X-Ray Trigger Form */}
            <div className="xray-form-strip">
              <div className="xray-field">
                <label>MEMORY CONCEPT:</label>
                <input
                  type="text"
                  value={xrayConcept}
                  onChange={(e) => setXrayConcept(e.target.value)}
                  placeholder="e.g. color"
                  list="xray-concepts-list"
                  disabled={isBusy}
                  className="xray-input"
                />
                <datalist id="xray-concepts-list">
                  {availableConcepts.map((c: string) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
              </div>

              <div className="xray-field">
                <label>EXPECTED VALUE:</label>
                <input
                  type="text"
                  value={xrayExpected}
                  onChange={(e) => setXrayExpected(e.target.value)}
                  placeholder="e.g. blue"
                  disabled={isBusy}
                  className="xray-input"
                />
              </div>

              <button
                type="button"
                className="btn-run-xray"
                onClick={() => handleRunMemoryXRay(xrayConcept, xrayExpected)}
                disabled={!xrayConcept.trim() || isBusy}
                title="Execute Memory X-Ray to isolate relevant synapses"
              >
                {isBusy ? 'Analyzing...' : '⚡ Run Memory X-Ray'}
              </button>
            </div>

            {/* X-Ray Results */}
            {memoryXRay && (
              <div className="xray-results-container">
                {/* Summary Metrics Banner */}
                <div className="xray-summary-strip">
                  <div className="summary-stat">
                    <span className="lbl">TOTAL ANALYZED</span>
                    <span className="val mono">{memoryXRay.summary.total_synapses_analyzed}</span>
                  </div>
                  <div className="summary-stat">
                    <span className="lbl">HIGH RELEVANCE</span>
                    <span className="val mono amber">{memoryXRay.summary.highly_relevant}</span>
                  </div>
                  <div className="summary-stat">
                    <span className="lbl">MODERATE</span>
                    <span className="val mono cyan">{memoryXRay.summary.moderately_relevant}</span>
                  </div>
                  <div className="summary-stat">
                    <span className="lbl">WEAK</span>
                    <span className="val mono slate">{memoryXRay.summary.weakly_relevant}</span>
                  </div>
                  <div className="summary-stat">
                    <span className="lbl">CONFIDENCE</span>
                    <span className="val mono emerald">
                      {(memoryXRay.readout.top_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Filter and Selection Header */}
                <div className="synapse-table-toolbar">
                  <div className="filter-group">
                    <span className="filter-label">TIER FILTER:</span>
                    {['all', 'high', 'moderate', 'weak'].map((tier) => (
                      <button
                        key={tier}
                        type="button"
                        className={`filter-chip ${xrayFilterTier === tier ? 'active' : ''}`}
                        onClick={() => setXrayFilterTier(tier)}
                      >
                        {tier.toUpperCase()}
                      </button>
                    ))}
                  </div>

                  <div className="action-group">
                    <button
                      type="button"
                      className="btn-select-high"
                      onClick={handleSelectHighRelevance}
                    >
                      + Target High Relevance ({memoryXRay.summary.highly_relevant})
                    </button>
                  </div>
                </div>

                {/* Synapse Breakdown Table */}
                <div className="xray-synapses-table-scroll">
                  <table className="synapse-xray-table">
                    <thead>
                      <tr>
                        <th style={{ width: 36 }}>SEL</th>
                        <th>SYNAPSE (ID)</th>
                        <th>PATHWAY</th>
                        <th>RELEVANCE |W·k|</th>
                        <th>TIER</th>
                        <th>WEIGHT</th>
                        <th>CONTRIB (W·k)</th>
                        <th>ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredXRaySynapses.slice(0, 50).map((syn) => {
                        const isSelected = selectedSynapseIds.includes(syn.synapse_id)
                        return (
                          <tr
                            key={syn.synapse_id}
                            className={`${isSelected ? 'row-selected' : ''}`}
                            onClick={() => handleToggleSynapse(syn.synapse_id)}
                          >
                            <td onClick={(e) => e.stopPropagation()}>
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => handleToggleSynapse(syn.synapse_id)}
                              />
                            </td>
                            <td className="mono syn-id-cell">{syn.synapse_id}</td>
                            <td className="syn-path-cell">
                              {syn.source} &rarr; {syn.target}
                            </td>
                            <td className="mono relevance-cell">
                              {syn.relevance_score.toFixed(4)}
                            </td>
                            <td>
                              <span className={`tier-badge tier-${syn.relevance_tier}`}>
                                {syn.relevance_tier.toUpperCase()}
                              </span>
                            </td>
                            <td
                              className={`mono ${
                                syn.polarity === 'excitatory'
                                  ? 'cyan'
                                  : syn.polarity === 'inhibitory'
                                  ? 'rose'
                                  : 'slate'
                              }`}
                            >
                              {syn.current_weight.toFixed(4)}
                            </td>
                            <td className="mono">
                              {syn.contribution_to_readout >= 0 ? '+' : ''}
                              {syn.contribution_to_readout.toFixed(4)}
                            </td>
                            <td>
                              <button
                                type="button"
                                className={`btn-target-syn ${isSelected ? 'active' : ''}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleToggleSynapse(syn.synapse_id)
                                }}
                              >
                                {isSelected ? 'Targeted' : 'Target'}
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  {filteredXRaySynapses.length > 50 && (
                    <div className="table-overflow-note">
                      Showing top 50 of {filteredXRaySynapses.length} synapses sorted by relevance.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Right Column: Surgery Workbench & Recall Comparison ──── */}
        <div className="surgery-right-col">
          {/* Synaptic Surgery Panel */}
          <SynapticSurgeryPanel
            session={session}
            isLocked={isLocked}
            selectedSynapseIds={selectedSynapseIds}
            onClearSelectedSynapses={() => setSelectedSynapseIds([])}
            onSelectHighRelevanceSynapses={handleSelectHighRelevance}
            onLockBaseline={handleLockBaseline}
            onWeaken={handleWeaken}
            onStrengthen={handleStrengthen}
            onSilence={handleSilence}
            onRestore={handleRestore}
            onReset={handleReset}
            synapseDetail={activeSynapseDetail}
            isBusy={isBusy}
          />

          {/* Surgery Result Panel */}
          <SurgeryResultPanel
            comparison={recallComparison}
            isLocked={isLocked}
            isBusy={isBusy}
            onRunRecall={handleRunRecallComparison}
            availableConcepts={availableConcepts}
          />
        </div>
      </div>

      {/* ── Bottom Section: Surgery Log ────────────────────────────── */}
      <div className="surgery-bottom-log-section">
        <SurgeryLogPanel
          operations={session?.operations || []}
          onSelectOperationSynapses={(synIds) => setSelectedSynapseIds(synIds)}
        />
      </div>

      {/* ── Methodology Modal ──────────────────────────────────────── */}
      {showMethodology && (
        <div className="methodology-modal-backdrop" onClick={() => setShowMethodology(false)}>
          <div
            className="methodology-modal-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>SCIENTIFIC METHODOLOGY & DERIVATION</h3>
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setShowMethodology(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <h4>1. Associative Linear Readout</h4>
              <p>
                In the Synaptic Brain model, associative memory recall is computed as the linear matrix-vector product:
              </p>
              <pre className="math-block">v̂ = W @ k_query</pre>
              <p>
                Expanding this inner product for each output unit <em>i</em>:
              </p>
              <pre className="math-block">v̂[i] = &Sigma;_j (W[i, j] &middot; k_query[j])</pre>

              <h4>2. Memory X-Ray Relevance Metric</h4>
              <p>
                To quantify the computational contribution of each individual synapse <em>(i &rarr; j)</em> to the readout of a memory concept, we calculate its effective transmission magnitude:
              </p>
              <pre className="math-block">relevance_score(i, j) = |W[i, j] &middot; k_query[j]|</pre>
              <p>
                Synapses are classified into relevance tiers based on their transmission relative to the peak contribution:
              </p>
              <ul>
                <li><strong>High Relevance:</strong> &ge; 50% of maximum transmission</li>
                <li><strong>Moderate Relevance:</strong> &ge; 20% of maximum transmission</li>
                <li><strong>Weak Relevance:</strong> &ge; 5% of maximum transmission</li>
                <li><strong>Unrelated:</strong> &lt; 5% of maximum transmission</li>
              </ul>

              <h4>3. Synaptic Surgery & Controlled Ablation</h4>
              <p>
                When you click <strong>LOCK BASELINE</strong>, the system freezes the current synaptic matrix as a reference snapshot and spawns an isolated experimental copy.
                All surgery operations (weaken, strengthen, silence, restore) are applied <em>strictly to the experimental copy</em>.
              </p>
              <p>
                Silencing a synapse sets its weight to zero (controlled ablation).
                Running recall re-evaluates both matrices on identical query vectors to isolate the exact empirical effect of the intervention.
              </p>

              <h4>4. Scientific Causation Transparency</h4>
              <div className="transparency-note-box">
                <strong>EDUCATIONAL COMPUTATIONAL MODEL:</strong>
                Removing or altering a connection and observing a drop in recall indicates that the connection contributes to the current readout.
                However, this intervention shows an association in an educational model and should not be confused with biological causation or commercial LLM internals.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
