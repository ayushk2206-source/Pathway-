import React, { useState, useEffect, useCallback } from 'react'
import {
  getEcosystemOverview,
  getMemoryEcosystemDetails,
  selectActiveMemory,
  getUnifiedTimeline,
  getMemoryRelationships,
  submitLearnerHypothesis,
  listLearnerHypotheses,
  createMemoryCheckpoint,
  compareMemoryStates,
  replayMemoryHistory,
} from '../api'
import type {
  MemoryPassport,
  MemoryLifecycle,
  MemoryBranch,
  MemoryCheckpoint,
  SynapticChangeLedger,
  UnifiedTimelineEvent,
  MemoryRelationship,
  LearnerHypothesis,
  LifecycleStage,
} from '../types'
import { MemoryPassportCard } from '../components/MemoryPassportCard'
import { MemoryLifecyclePipeline } from '../components/MemoryLifecyclePipeline'
import { MemoryCausalTrail } from '../components/MemoryCausalTrail'
import { SynapticChangeLedgerView } from '../components/SynapticChangeLedgerView'
import { MemoryRelationshipMap } from '../components/MemoryRelationshipMap'
import { LearnerHypothesisWidget } from '../components/LearnerHypothesisWidget'
import { StateComparatorView } from '../components/StateComparatorView'
import '../ecosystem.css'

interface MemoryEcosystemWorkspaceProps {
  onNavigateToWorkspace: (workspaceId: string) => void
  onSelectGlobalMemory: (memoryId: string) => void
}

export const MemoryEcosystemWorkspace: React.FC<MemoryEcosystemWorkspaceProps> = ({
  onNavigateToWorkspace,
  onSelectGlobalMemory,
}) => {
  // Master Ecosystem State
  const [activeMemoryId, setActiveMemoryId] = useState<string>('M-001')
  const [isFollowing, setIsFollowing] = useState<boolean>(true)
  const [passports, setPassports] = useState<MemoryPassport[]>([])
  const [currentPassport, setCurrentPassport] = useState<MemoryPassport | null>(null)
  const [lifecycle, setLifecycle] = useState<MemoryLifecycle | null>(null)
  const [branches, setBranches] = useState<MemoryBranch | null>(null)
  const [checkpoints, setCheckpoints] = useState<MemoryCheckpoint[]>([])
  const [ledger, setLedger] = useState<SynapticChangeLedger | null>(null)
  const [timelineEvents, setTimelineEvents] = useState<UnifiedTimelineEvent[]>([])
  const [relationships, setRelationships] = useState<MemoryRelationship[]>([])
  const [hypotheses, setHypotheses] = useState<LearnerHypothesis[]>([])

  // Checkpoint modal & Replay state
  const [newCheckpointLabel, setNewCheckpointLabel] = useState<string>('')
  const [isCreatingCheckpoint, setIsCreatingCheckpoint] = useState<boolean>(false)
  const [replayModalOpen, setReplayModalOpen] = useState<boolean>(false)
  const [replayData, setReplayData] = useState<{
    memory_id: string
    concept: string
    total_steps: number
    playback_steps: {
      step_index: number
      event_type: string
      title: string
      description: string
      producing_experiment: string
      session_time: string
      metrics: Record<string, unknown>
      is_simplification: boolean
      label: string
    }[]
    disclaimer: string
  } | null>(null)

  // Load Ecosystem Overview
  const loadOverview = useCallback(async () => {
    try {
      const overview = await getEcosystemOverview()
      setActiveMemoryId(overview.active_memory_id)
      setIsFollowing(overview.is_following)
      setPassports(overview.passports)
      setCurrentPassport(overview.active_passport)

      // Fetch memory specific details
      const details = await getMemoryEcosystemDetails(overview.active_memory_id)
      setLifecycle(details.lifecycle)
      setBranches(details.branch_tree)
      setCheckpoints(details.checkpoints)
      setLedger(details.ledger)

      // Fetch timeline and relations
      const [tl, rels, hyps] = await Promise.all([
        getUnifiedTimeline(overview.active_memory_id),
        getMemoryRelationships(),
        listLearnerHypotheses(overview.active_memory_id),
      ])
      setTimelineEvents(tl.events)
      setRelationships(rels.relationships)
      setHypotheses(hyps.hypotheses)
    } catch (e) {
      console.error('Failed to load ecosystem overview:', e)
    }
  }, [])

  useEffect(() => {
    loadOverview()
  }, [loadOverview])

  // Change active memory
  const handleSelectMemory = async (memId: string) => {
    try {
      const res = await selectActiveMemory(memId, isFollowing)
      setActiveMemoryId(res.active_memory_id)
      setCurrentPassport(res.passport)
      onSelectGlobalMemory(memId)

      const [details, tl, hyps] = await Promise.all([
        getMemoryEcosystemDetails(memId),
        getUnifiedTimeline(memId),
        listLearnerHypotheses(memId),
      ])
      setLifecycle(details.lifecycle)
      setBranches(details.branch_tree)
      setCheckpoints(details.checkpoints)
      setLedger(details.ledger)
      setTimelineEvents(tl.events)
      setHypotheses(hyps.hypotheses)
    } catch (e) {
      console.error('Failed to select memory:', e)
    }
  }

  // Toggle follow mode
  const handleToggleFollow = async () => {
    const next = !isFollowing
    setIsFollowing(next)
    await selectActiveMemory(activeMemoryId, next)
  }

  // Create Checkpoint
  const handleCreateCheckpoint = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCheckpointLabel.trim()) return
    setIsCreatingCheckpoint(true)
    try {
      const res = await createMemoryCheckpoint({
        memory_id: activeMemoryId,
        label: newCheckpointLabel.trim(),
      })
      setCheckpoints((prev) => [...prev, res.checkpoint])
      setNewCheckpointLabel('')
      const tl = await getUnifiedTimeline(activeMemoryId)
      setTimelineEvents(tl.events)
    } finally {
      setIsCreatingCheckpoint(false)
    }
  }

  // Record Hypothesis
  const handleSaveHypothesis = async (expType: string, predictionText: string, predictedOutcome: string) => {
    const res = await submitLearnerHypothesis({
      memory_id: activeMemoryId,
      experiment_type: expType,
      prediction_text: predictionText,
      predicted_outcome: predictedOutcome,
    })
    setHypotheses((prev) => [res.hypothesis, ...prev])
  }

  // Trigger Replay
  const handleTriggerReplay = async () => {
    try {
      const data = await replayMemoryHistory(activeMemoryId)
      setReplayData(data)
      setReplayModalOpen(true)
    } catch (e) {
      console.error('Failed to reconstruct replay:', e)
    }
  }

  return (
    <div className="ecosystem-container">
      {/* Central Ecosystem Header */}
      <div className="ecosystem-header">
        <div className="ecosystem-header-title">
          <span style={{ fontSize: '1.4rem' }}>🌐</span>
          <div>
            <h2>
              <span>MEMORY ECOSYSTEM</span>
              <span className="ecosystem-badge">PHASE 21 UNIFIED WORLD</span>
            </h2>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
              One living memory · Full lifecycle from input to synaptic write, recall, and counterfactual
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(30, 41, 59, 0.7)', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
              Memory Selector:
            </span>
            <select
              value={activeMemoryId}
              onChange={(e) => handleSelectMemory(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#38bdf8',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              {passports.map((p) => (
                <option key={p.memory_id} value={p.memory_id} style={{ background: '#0f172a', color: '#f8fafc' }}>
                  {p.memory_id} · {p.concept}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleTriggerReplay}
            style={{
              padding: '6px 12px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid #38bdf8',
              borderRadius: '6px',
              color: '#38bdf8',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <span>▶</span> REPLAY {activeMemoryId}
          </button>
        </div>
      </div>

      {/* Hero Memory Passport */}
      <MemoryPassportCard
        passport={currentPassport}
        onToggleFollow={handleToggleFollow}
      />

      {/* Memory Lifecycle Pipeline */}
      <MemoryLifecyclePipeline
        lifecycle={lifecycle}
        onSelectStage={(stage: LifecycleStage) => {
          onNavigateToWorkspace(stage.target_workspace)
        }}
      />

      {/* Memory Branch Hierarchy Banner */}
      {branches && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 14px',
          background: 'rgba(15, 23, 42, 0.65)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          borderRadius: '8px',
          fontSize: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ color: '#38bdf8', fontWeight: 700, letterSpacing: '0.05em' }}>🌿 COMPUTATIONAL BRANCH:</span>
            <span style={{ color: '#f8fafc', fontWeight: 600, fontFamily: 'monospace' }}>{branches.label}</span>
            <span style={{
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '0.68rem',
              fontWeight: 700,
              background: branches.branch_type === 'ORIGINAL' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              color: branches.branch_type === 'ORIGINAL' ? '#38bdf8' : '#fbbf24',
              border: `1px solid ${branches.branch_type === 'ORIGINAL' ? '#38bdf8' : '#fbbf24'}`,
            }}>
              {branches.branch_type}
            </span>
          </div>
          <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>
            {branches.children && branches.children.length > 0 ? (
              <span>Sub-branches: <strong style={{ color: '#f8fafc' }}>{branches.children.map(c => c.label).join(', ')}</strong></span>
            ) : (
              <span>Root computational trajectory</span>
            )}
          </div>
        </div>
      )}

      {/* Memory Causal Trail */}
      <MemoryCausalTrail onNavigate={onNavigateToWorkspace} />

      {/* Split Grid Layout */}
      <div className="ecosystem-grid-split">
        {/* Left Column: Ledger, Relationships, Checkpoints */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Synaptic Change Ledger */}
          <SynapticChangeLedgerView ledger={ledger} />

          {/* Evidence-based Relationship Graph */}
          <MemoryRelationshipMap
            relationships={relationships}
            onSelectMemory={handleSelectMemory}
          />

          {/* Checkpoint System & State Comparator */}
          <div className="ledger-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                <span>📌</span> EXPERIMENTAL CHECKPOINTS & STATE PRESERVATION
              </h4>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                {checkpoints.length} saved
              </span>
            </div>

            <form onSubmit={handleCreateCheckpoint} style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                value={newCheckpointLabel}
                onChange={(e) => setNewCheckpointLabel(e.target.value)}
                placeholder="Name checkpoint (e.g. POST-COLLISION-STABLE)..."
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  background: '#0f172a',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#f8fafc',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                }}
              />
              <button
                type="submit"
                disabled={isCreatingCheckpoint || !newCheckpointLabel.trim()}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid #10b981',
                  color: '#10b981',
                  borderRadius: '4px',
                  fontWeight: 700,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                }}
              >
                + Checkpoint
              </button>
            </form>

            <StateComparatorView
              checkpoints={checkpoints}
              onCompare={async (stateA, stateB) => {
                const res = await compareMemoryStates({ state_a: stateA, state_b: stateB })
                return res.comparison
              }}
            />
          </div>
        </div>

        {/* Right Column: Unified Timeline & Learner Hypothesis */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Learner Hypothesis Engine */}
          <LearnerHypothesisWidget
            memoryId={activeMemoryId}
            onSaveHypothesis={handleSaveHypothesis}
            recentHypotheses={hypotheses}
          />

          {/* Unified Timeline & Computational History */}
          <div className="ledger-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                <span>⌘</span> COMPUTATIONAL HISTORY ({timelineEvents.length} EVENTS)
              </h4>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Session-relative sequence
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', maxHeight: '440px', overflowY: 'auto', paddingRight: '4px' }}>
              {timelineEvents.map((evt) => (
                <div
                  key={evt.event_id}
                  style={{
                    background: 'rgba(30, 41, 59, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '6px',
                    padding: '0.6rem 0.8rem',
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 700, fontSize: '0.75rem' }}>
                        {evt.session_time}
                      </span>
                      <span style={{ fontWeight: 700, color: '#f1f5f9' }}>{evt.title}</span>
                    </div>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '1px 6px',
                        borderRadius: '3px',
                        background: 'rgba(56, 189, 248, 0.15)',
                        color: '#38bdf8',
                      }}
                    >
                      {evt.producing_experiment}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                    {evt.description}
                  </div>

                  {evt.delta_metrics && Object.keys(evt.delta_metrics).length > 0 && (
                    <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.35rem', fontFamily: 'monospace', fontSize: '0.68rem', color: '#10b981' }}>
                      {Object.entries(evt.delta_metrics).map(([k, v]) => (
                        <span key={k}>Δ{k}: {String(v)}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Step-by-Step Replay Reconstruction Modal */}
      {replayModalOpen && replayData && (
        <div className="modal-overlay" style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(6px)',
        }}>
          <div className="modal-content-card" style={{
            background: '#0f172a',
            border: '1px solid #38bdf8',
            borderRadius: '10px',
            padding: '1.5rem',
            maxWidth: '620px',
            width: '90%',
            maxHeight: '80vh',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>▶</span> REPLAYING MEMORY: {replayData.concept} ({replayData.memory_id})
              </h3>
              <button
                onClick={() => setReplayModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ fontSize: '0.78rem', color: '#cbd5e1', background: 'rgba(56, 189, 248, 0.1)', padding: '0.5rem 0.75rem', borderRadius: '4px', borderLeft: '3px solid #38bdf8' }}>
              {replayData.disclaimer}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {replayData.playback_steps.map((step) => (
                <div
                  key={step.step_index}
                  style={{
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '6px',
                    padding: '0.6rem 0.8rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 700, fontSize: '0.75rem' }}>
                      STEP {step.step_index + 1} · {step.session_time}
                    </span>
                    <span className="claim-tag observed">{step.label}</span>
                  </div>
                  <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                    {step.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                    {step.description}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button
                onClick={() => setReplayModalOpen(false)}
                style={{
                  padding: '6px 16px',
                  background: 'rgba(56, 189, 248, 0.2)',
                  border: '1px solid #38bdf8',
                  color: '#38bdf8',
                  borderRadius: '4px',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Close Replay
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
