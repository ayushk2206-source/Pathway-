import React, { useState } from 'react'
import type { MemoryExplanation, MemoryStrengthProfile, MemoryTrace } from '../types'

interface MemoryInspectorDrawerProps {
  memoryId: string | null
  strengthProfile: MemoryStrengthProfile | null
  trace: MemoryTrace | null
  explanation: MemoryExplanation | null
  clusterId?: number
  onClose: () => void
  onTraceMemory: (id: string) => void
  onXRayMemory: (id: string) => void
  onSurgeryMemory: (id: string) => void
  onCounterfactual: (id: string) => void
  onInvestigateMemory?: (id: string) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

// Inline SVG sparkline for persistence over time
const PersistenceSparkline: React.FC<{
  history?: number[]
  strength: number
  color: string
}> = ({ history, strength, color }) => {
  const points = history?.length
    ? history
    : Array.from({ length: 12 }, (_, i) => {
        // Synthetic profile from final strength
        const t = i / 11
        return Math.min(1, strength * (0.3 + 0.7 * Math.pow(t, 0.5)) + (Math.random() - 0.5) * 0.05)
      })

  const maxVal = Math.max(...points, 0.01)
  const w = 100
  const h = 32

  const svgPoints = points
    .map((v, i) => {
      const x = (i / (points.length - 1)) * w
      const y = h - (v / maxVal) * h * 0.85
      return `${x},${y}`
    })
    .join(' ')

  const fillPoints = `0,${h} ${svgPoints} ${w},${h}`

  return (
    <div className="sparkline-wrapper">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        {/* Fill area */}
        <polygon
          points={fillPoints}
          fill={color.replace(')', ', 0.08)').replace('rgb(', 'rgba(')}
          style={{ fillOpacity: 1 }}
        />
        {/* Line */}
        <polyline
          points={svgPoints}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {/* Current position dot */}
        {(() => {
          const lastX = w
          const lastV = points[points.length - 1]
          const lastY = h - (lastV / maxVal) * h * 0.85
          return (
            <circle
              cx={lastX}
              cy={lastY}
              r="2.5"
              fill={color}
              fillOpacity="0.9"
            />
          )
        })()}
      </svg>
    </div>
  )
}

export const MemoryInspectorDrawer: React.FC<MemoryInspectorDrawerProps> = ({
  memoryId,
  strengthProfile,
  trace,
  explanation,
  clusterId = 0,
  onClose,
  onTraceMemory,
  onXRayMemory,
  onSurgeryMemory,
  onCounterfactual,
  onInvestigateMemory,
  onViewEvidence,
}) => {
  const [interventionStrength, setInterventionStrength] = useState<number | null>(null)

  if (!memoryId) return null

  const strength = strengthProfile?.final_strength ?? 0
  const reinforcements = strengthProfile?.reinforcement_count ?? 0
  const pattern = strengthProfile?.pattern ?? 'NO_DECAY'
  const concept = strengthProfile?.concept_label || memoryId
  const peakStrength = strengthProfile?.peak_strength ?? strength

  const effectiveStrength = interventionStrength !== null ? interventionStrength : strength
  const strengthClass = effectiveStrength > 0.6 ? 'emerald' : effectiveStrength > 0.3 ? 'amber' : 'crimson'
  const strengthColor =
    effectiveStrength > 0.6 ? 'var(--emerald)' : effectiveStrength > 0.3 ? 'var(--amber)' : 'var(--crimson)'

  // Causal descendants from trace
  const causalDescendants: string[] = trace?.influenced_memories
    ? Object.keys(trace.influenced_memories).slice(0, 5)
    : []

  return (
    <aside className="inspector-drawer">
      {/* ── Excavation Header ────────────────────────────────────── */}
      <div className="drawer-header">
        <div className="drawer-header-top">
          <div className="drawer-title-group">
            <span className="drawer-eyebrow">Excavation</span>
            <span className="drawer-memory-id">{memoryId}</span>
            {concept !== memoryId && (
              <span className="drawer-concept">{concept}</span>
            )}
          </div>
          <button
            className="drawer-close"
            onClick={onClose}
            title="Close (Esc)"
            aria-label="Close inspector"
          >
            ×
          </button>
        </div>

        {/* Strength bar */}
        <div className="drawer-strength-bar">
          <span className="strength-label">strength</span>
          <div className="strength-track">
            <div
              className={`strength-fill ${strengthClass}`}
              style={{ width: `${Math.min(100, effectiveStrength * 100).toFixed(1)}%` }}
            />
          </div>
          <span className="strength-val" style={{ color: strengthColor }}>
            {effectiveStrength.toFixed(3)}
          </span>
        </div>
      </div>

      <div className="drawer-body">
        {/* ── Persistence Section ─────────────────────────────────── */}
        <div className="drawer-section">
          <div className="drawer-section-title">Persistence</div>
          <PersistenceSparkline
            history={strengthProfile?.history}
            strength={strength}
            color={strengthColor}
          />
          <div className="drawer-metrics" style={{ marginTop: 10 }}>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Peak</span>
              <span className={`drawer-metric-val ${peakStrength > 0.6 ? 'emerald' : 'amber'}`}>
                {peakStrength.toFixed(3)}
              </span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Reinforcements</span>
              <span className="drawer-metric-val accent">{reinforcements}</span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Decay Pattern</span>
              <span className="drawer-metric-val" style={{ fontSize: 11 }}>{pattern}</span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Cluster</span>
              <span className="drawer-metric-val">{clusterId}</span>
            </div>
          </div>
        </div>

        {/* ── Causal Influence Chain ──────────────────────────────── */}
        {(causalDescendants.length > 0 || trace?.primary_competitor) && (
          <div className="drawer-section">
            <div className="drawer-section-title">Influence</div>
            <div className="influence-chain">
              {/* Origin node */}
              <div className="influence-node origin">
                <div className="influence-node-dot" />
                <span className="influence-node-label">{memoryId}</span>
                <span className="influence-arrow">↓</span>
              </div>
              {/* Descendants */}
              {causalDescendants.map((descId) => (
                <div key={descId} className="influence-node">
                  <div className="influence-node-dot" />
                  <span className="influence-node-label">{descId}</span>
                  {trace?.influenced_memories?.[descId] !== undefined && (
                    <span className="influence-node-delta">
                      Δ {trace.influenced_memories[descId].toFixed(3)}
                    </span>
                  )}
                </div>
              ))}
              {/* Primary competitor */}
              {trace?.primary_competitor && (
                <div className="influence-node" style={{ marginTop: 6 }}>
                  <div
                    className="influence-node-dot"
                    style={{ background: 'var(--crimson)' }}
                  />
                  <span className="influence-node-label" style={{ color: 'var(--crimson)' }}>
                    {trace.primary_competitor}
                  </span>
                  <span
                    className="influence-node-delta"
                    style={{ marginLeft: 'auto', color: 'var(--crimson)' }}
                  >
                    competitor
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Forensic Explanation ────────────────────────────────── */}
        {explanation && (
          <div className="drawer-section">
            <div className="drawer-section-title">Forensic Analysis</div>
            <p className="explanation-block">{explanation.summary}</p>
            {explanation.evidence && explanation.evidence.length > 0 && (
              <div className="evidence-list">
                {explanation.evidence.map((ev, i) => (
                  <div key={i} className="evidence-item">
                    <span className="evidence-marker">—</span>
                    <span>{ev}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Intervention Controls ───────────────────────────────── */}
        <div className="intervention-panel">
          <div className="intervention-header">
            <span className="intervention-title">Intervene</span>
            {interventionStrength !== null && (
              <span style={{ fontSize: 10, color: 'var(--amber)' }}>
                Modified: {interventionStrength.toFixed(2)}
              </span>
            )}
          </div>
          <div className="intervention-strength">
            <div className="strength-slider-row">
              <span style={{ fontSize: 10, color: 'var(--text-muted)', minWidth: 14 }}>0</span>
              <input
                type="range"
                className="strength-slider"
                min={0}
                max={1}
                step={0.01}
                value={effectiveStrength}
                onChange={(e) => setInterventionStrength(Number(e.target.value))}
                aria-label="Memory strength"
              />
              <span style={{ fontSize: 10, color: 'var(--text-muted)', minWidth: 14 }}>1</span>
            </div>
          </div>
          <div className="intervention-actions">
            <button
              className="intervention-btn btn-emerald"
              onClick={() => onSurgeryMemory(memoryId)}
              title="Strengthen this memory"
            >
              Strengthen
            </button>
            <button
              className="intervention-btn btn-amber"
              onClick={() => onSurgeryMemory(memoryId)}
              title="Weaken this memory"
            >
              Weaken
            </button>
            <button
              className="intervention-btn btn-crimson"
              onClick={() => onSurgeryMemory(memoryId)}
              title="Ablate (remove) this memory"
            >
              Ablate
            </button>
            <button
              className="intervention-btn"
              onClick={() => setInterventionStrength(null)}
              title="Restore to original"
            >
              Restore
            </button>
          </div>
        </div>
      </div>

      {/* ── Navigation Actions ───────────────────────────────────── */}
      <div className="drawer-actions">
        <button
          className="drawer-action-btn btn-primary"
          onClick={() => onTraceMemory(memoryId)}
          title="Full lifecycle trace"
        >
          <span className="drawer-action-icon">◎</span>
          Trace Lifecycle
        </button>
        <button
          className="drawer-action-btn"
          onClick={() => onXRayMemory(memoryId)}
          title="Weight matrix X-Ray"
        >
          <span className="drawer-action-icon">⌬</span>
          X-Ray Substrate
        </button>
        <button
          className="drawer-action-btn btn-violet"
          onClick={() => onCounterfactual(memoryId)}
          title="Run counterfactual"
        >
          <span className="drawer-action-icon">⋈</span>
          Counterfactual
        </button>
        {onInvestigateMemory && (
          <button
            className="drawer-action-btn"
            onClick={() => onInvestigateMemory(memoryId)}
            title="Detective investigation"
          >
            <span className="drawer-action-icon">◈</span>
            Investigate
          </button>
        )}
        <button
          className="drawer-action-btn btn-ghost"
          onClick={() =>
            onViewEvidence(`Memory ${memoryId} · Evidence`, {
              memory_id: memoryId,
              concept_label: concept,
              final_strength: strength,
              pattern,
              reinforcements,
              evidence: explanation?.evidence,
            })
          }
          title="View raw evidence"
        >
          <span className="drawer-action-icon">⊞</span>
          View Evidence
        </button>
      </div>
    </aside>
  )
}
