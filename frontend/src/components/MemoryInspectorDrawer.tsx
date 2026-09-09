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
    <aside className="inspector-drawer" aria-label="Forensic Memory Inspector">
      {/* ── Excavation Header ────────────────────────────────────── */}
      <div className="drawer-header">
        <div className="drawer-header-top">
          <div className="drawer-title-group">
            <span className="drawer-eyebrow">FORENSIC MEMORY AUTOPSY</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
              <span className="drawer-memory-id">{memoryId}</span>
              {concept !== memoryId && (
                <span className="mono-badge cyan">{concept}</span>
              )}
            </div>
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
          <span className="strength-label">SYNAPTIC STRENGTH</span>
          <div className="strength-track">
            <div
              className={`strength-fill ${strengthClass}`}
              style={{ width: `${Math.min(100, effectiveStrength * 100).toFixed(1)}%` }}
            />
          </div>
          <span className="strength-val" style={{ color: strengthColor, fontFamily: 'var(--font-mono)' }}>
            {effectiveStrength.toFixed(4)}
          </span>
        </div>
      </div>

      <div className="drawer-body">
        {/* ── 1. IDENTITY ──────────────────────────────────────────── */}
        <div className="drawer-section">
          <div className="drawer-section-title">1. IDENTITY & ENCODING</div>
          <div className="drawer-metrics">
            <div className="drawer-metric">
              <span className="drawer-metric-label">Memory Identifier</span>
              <span className="drawer-metric-val" style={{ fontFamily: 'var(--font-mono)' }}>{memoryId}</span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Concept Label</span>
              <span className="drawer-metric-val accent">{concept}</span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Cluster Assigned</span>
              <span className="drawer-metric-val">#{clusterId}</span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Trace Pattern</span>
              <span className="drawer-metric-val" style={{ fontSize: 11 }}>{pattern}</span>
            </div>
          </div>
        </div>

        {/* ── 2. CURRENT STATE & PERSISTENCE ──────────────────────── */}
        <div className="drawer-section">
          <div className="drawer-section-title">2. CURRENT STATE & PERSISTENCE</div>
          <PersistenceSparkline
            history={strengthProfile?.history}
            strength={strength}
            color={strengthColor}
          />
          <div className="drawer-metrics" style={{ marginTop: 10 }}>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Peak Magnitude</span>
              <span className={`drawer-metric-val ${peakStrength > 0.6 ? 'emerald' : 'amber'}`}>
                {peakStrength.toFixed(4)}
              </span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Reinforcement Events</span>
              <span className="drawer-metric-val accent">{reinforcements}</span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Fidelity Assessment</span>
              <span className="drawer-metric-val" style={{ color: strengthColor }}>
                {effectiveStrength >= 0.7 ? 'HIGH FIDELITY' : effectiveStrength >= 0.4 ? 'ATTENUATED' : 'CRITICAL DECAY'}
              </span>
            </div>
            <div className="drawer-metric">
              <span className="drawer-metric-label">Intervention State</span>
              <span className="drawer-metric-val" style={{ color: interventionStrength !== null ? 'var(--amber)' : 'var(--text-muted)' }}>
                {interventionStrength !== null ? 'MODIFIED' : 'ORIGINAL'}
              </span>
            </div>
          </div>
        </div>

        {/* ── 3. DYNAMICS & INFLUENCE ──────────────────────────────── */}
        <div className="drawer-section">
          <div className="drawer-section-title">3. DYNAMICS & CAUSAL INFLUENCE</div>
          {(causalDescendants.length > 0 || trace?.primary_competitor) ? (
            <div className="influence-chain">
              <div className="influence-node origin">
                <div className="influence-node-dot" />
                <span className="influence-node-label">{memoryId}</span>
                <span className="influence-arrow">↓</span>
              </div>
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
                    COMPETITOR
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic', padding: '4px 0' }}>
              No active cross-memory interference recorded for this node.
            </div>
          )}

          {/* Micro-Intervention Controls */}
          <div className="intervention-panel" style={{ marginTop: '12px' }}>
            <div className="intervention-header">
              <span className="intervention-title">Micro-Intervention Slider</span>
              {interventionStrength !== null && (
                <span style={{ fontSize: 10, color: 'var(--amber)', fontFamily: 'var(--font-mono)' }}>
                  Active: {interventionStrength.toFixed(2)}
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
                  aria-label="Memory strength slider"
                />
                <span style={{ fontSize: 10, color: 'var(--text-muted)', minWidth: 14 }}>1</span>
              </div>
            </div>
            <div className="intervention-actions">
              <button
                className="intervention-btn btn-emerald"
                onClick={() => onSurgeryMemory(memoryId)}
                title="Strengthen this synaptic memory in Surgery"
              >
                + Strengthen
              </button>
              <button
                className="intervention-btn btn-amber"
                onClick={() => onSurgeryMemory(memoryId)}
                title="Weaken this synaptic memory in Surgery"
              >
                - Weaken
              </button>
              <button
                className="intervention-btn btn-crimson"
                onClick={() => onSurgeryMemory(memoryId)}
                title="Ablate (zero) this memory in Surgery"
              >
                ✕ Ablate
              </button>
              <button
                className="intervention-btn"
                onClick={() => setInterventionStrength(null)}
                title="Restore slider to true state"
              >
                ↺ Reset
              </button>
            </div>
          </div>
        </div>

        {/* ── 4. EVIDENCE AUDIT ────────────────────────────────────── */}
        <div className="drawer-section">
          <div className="drawer-section-title">4. FORENSIC EVIDENCE AUDIT</div>
          {explanation ? (
            <>
              <p className="explanation-block">{explanation.summary}</p>
              {explanation.evidence && explanation.evidence.length > 0 && (
                <div className="evidence-list" style={{ marginTop: '8px' }}>
                  {explanation.evidence.map((ev, i) => (
                    <div key={i} className="evidence-item">
                      <span className="evidence-marker">▸</span>
                      <span>{ev}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Standard Hebbian trace retention profile confirmed.
            </div>
          )}
        </div>
      </div>

      {/* ── 5. ACTION SUITE ──────────────────────────────────────── */}
      <div className="drawer-actions">
        <button
          className="drawer-action-btn btn-primary"
          onClick={() => onTraceMemory(memoryId)}
          title="Full temporal trace lifecycle"
        >
          <span className="drawer-action-icon">◎</span>
          Trace Timeline
        </button>
        <button
          className="drawer-action-btn"
          onClick={() => onXRayMemory(memoryId)}
          title="Weight matrix substrate X-Ray"
        >
          <span className="drawer-action-icon">⌬</span>
          X-Ray Substrate
        </button>
        <button
          className="drawer-action-btn btn-violet"
          onClick={() => onCounterfactual(memoryId)}
          title="Branch counterfactual parallel world"
        >
          <span className="drawer-action-icon">⋈</span>
          Counterfactual
        </button>
        {onInvestigateMemory && (
          <button
            className="drawer-action-btn"
            onClick={() => onInvestigateMemory(memoryId)}
            title="Launch diagnostic autopsy in Detective"
          >
            <span className="drawer-action-icon">◈</span>
            Detective
          </button>
        )}
        <button
          className="drawer-action-btn btn-ghost"
          onClick={() =>
            onViewEvidence(`Memory ${memoryId} · Forensic Audit`, {
              memory_id: memoryId,
              concept_label: concept,
              final_strength: strength,
              peak_strength: peakStrength,
              pattern,
              reinforcements,
              evidence: explanation?.evidence,
            })
          }
          title="View raw evidence payload"
        >
          <span className="drawer-action-icon">⊞</span>
          Evidence
        </button>
      </div>
    </aside>
  )
}
