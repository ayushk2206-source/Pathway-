import React, { useState } from 'react'
import type {
  ClusterResult,
  Experiment,
  InterferenceRecord,
  MemoryMap2D,
  MemoryRelationshipGraph,
} from '../types'

interface MemoryMapWorkspaceProps {
  experiment: Experiment | null
  memoryMap: MemoryMap2D | null
  graph: MemoryRelationshipGraph | null
  clusters: ClusterResult[]
  interferenceRecords: InterferenceRecord[]
  selectedMemoryId: string | null
  onSelectMemory: (id: string) => void
  onViewEvidence: (title: string, details: Record<string, unknown>) => void
}

export const MemoryMapWorkspace: React.FC<MemoryMapWorkspaceProps> = ({
  experiment,
  memoryMap,
  graph,
  clusters,
  interferenceRecords,
  selectedMemoryId,
  onSelectMemory,
  onViewEvidence,
}) => {
  // Layer toggles
  const [showAssociations, setShowAssociations] = useState(true)
  const [showCompetition, setShowCompetition] = useState(true)
  const [showClusters, setShowClusters] = useState(true)
  const [showStrength, setShowStrength] = useState(true)

  // Zoom & Pan offset
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })

  // Competition Comparison selector
  const [compMemoryA, setCompMemoryA] = useState<string>(memoryMap?.points[0]?.memory_id || '')
  const [compMemoryB, setCompMemoryB] = useState<string>(memoryMap?.points[1]?.memory_id || '')

  if (!experiment) {
    return (
      <div className="empty-state">
        <h3>MEMORY MAP · OFFLINE</h3>
        <p>Run or load an experiment to render high-dimensional topological projections and competition graphs.</p>
      </div>
    )
  }

  const points = memoryMap?.points || []
  const activeCompetition = interferenceRecords.find(
    (r) =>
      (r.target_memory_id === compMemoryA && r.competing_memory_id === compMemoryB) ||
      (r.target_memory_id === compMemoryB && r.competing_memory_id === compMemoryA)
  )

  const selectedPt = points.find((p) => p.memory_id === selectedMemoryId) || points[0]

  return (
    <div className="memory-map-workspace-layout">
      {/* Top Controls & Toggles Strip */}
      <div className="map-toolbar-strip">
        <div className="toolbar-title-group">
          <h2 className="workspace-title">2D TOPOLOGICAL MEMORY MAP</h2>
          <span className="epistemic-tag">PCA PROJECTION APPROXIMATION</span>
        </div>

        <div className="toggles-group">
          <button
            className={`toggle-btn ${showAssociations ? 'active primary' : ''}`}
            onClick={() => setShowAssociations(!showAssociations)}
          >
            {showAssociations ? '☑' : '☐'} ASSOCIATIONS
          </button>
          <button
            className={`toggle-btn ${showCompetition ? 'active accent-crimson' : ''}`}
            onClick={() => setShowCompetition(!showCompetition)}
          >
            {showCompetition ? '☑' : '☐'} COMPETITION
          </button>
          <button
            className={`toggle-btn ${showClusters ? 'active' : ''}`}
            onClick={() => setShowClusters(!showClusters)}
          >
            {showClusters ? '☑' : '☐'} CLUSTERS
          </button>
          <button
            className={`toggle-btn ${showStrength ? 'active' : ''}`}
            onClick={() => setShowStrength(!showStrength)}
          >
            {showStrength ? '☑' : '☐'} STRENGTH
          </button>
        </div>

        <div className="zoom-group">
          <button onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}>+</button>
          <span className="zoom-val">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))}>-</button>
          <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }) }}>RESET</button>
        </div>
      </div>

      <div className="map-content-grid">
        {/* Main 2D Projection & Relational Network SVG Surface */}
        <div className="map-main-pane">
          <div className="svg-canvas-wrapper">
            <svg
              className="topological-svg"
              viewBox="-2.5 -2.5 5 5"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: 'center center',
              }}
            >
              {/* Reference Coordinate Axes */}
              <line x1="-2.5" y1="0" x2="2.5" y2="0" stroke="#172235" strokeWidth="0.015" />
              <line x1="0" y1="-2.5" x2="0" y2="2.5" stroke="#172235" strokeWidth="0.015" />

              {/* Concentric Guide Rings */}
              <circle cx="0" cy="0" r="1.0" fill="none" stroke="#101826" strokeWidth="0.01" />
              <circle cx="0" cy="0" r="2.0" fill="none" stroke="#0d1421" strokeWidth="0.01" />

              {/* Edges from Graph */}
              {graph &&
                graph.edges.map((e, idx) => {
                  const src = points.find((p) => p.memory_id === e.source)
                  const tgt = points.find((p) => p.memory_id === e.target)
                  if (!src || !tgt) return null

                  const isComp = e.relationship === 'COMPETITION'
                  const isAssoc = e.relationship === 'ASSOCIATION' || e.relationship === 'REINFORCEMENT'

                  if (isComp && !showCompetition) return null
                  if (isAssoc && !showAssociations) return null

                  return (
                    <line
                      key={idx}
                      x1={src.x}
                      y1={src.y}
                      x2={tgt.x}
                      y2={tgt.y}
                      stroke={isComp ? '#ef4444' : '#00f0ff'}
                      strokeWidth={Math.max(0.015, e.weight * 0.05)}
                      strokeDasharray={isComp ? '0.04, 0.04' : undefined}
                      opacity={0.6}
                    />
                  )
                })}

              {/* Memory Nodes */}
              {points.map((pt) => {
                const isSelected = selectedMemoryId === pt.memory_id
                const r = showStrength ? 0.06 + Math.max(0, pt.strength) * 0.12 : 0.08

                return (
                  <g
                    key={pt.memory_id}
                    onClick={() => onSelectMemory(pt.memory_id)}
                    style={{ cursor: 'pointer' }}
                  >
                    {isSelected && (
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r={r + 0.06}
                        fill="none"
                        stroke="#00f0ff"
                        strokeWidth="0.02"
                      />
                    )}
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r={r}
                      fill={isSelected ? '#ffffff' : showClusters ? ['#00f0ff', '#10b981', '#f59e0b', '#a855f7'][pt.cluster % 4] : '#00f0ff'}
                      stroke="#070b12"
                      strokeWidth="0.015"
                    />
                    <text
                      x={pt.x}
                      y={pt.y + r + 0.08}
                      fill={isSelected ? '#00f0ff' : '#cbd5e1'}
                      fontSize="0.09"
                      fontFamily="var(--font-mono)"
                      textAnchor="middle"
                    >
                      {pt.label}
                    </text>
                  </g>
                )
              })}
            </svg>
          </div>
        </div>

        {/* Right Side Panels: Clusters, Neighborhood, and Competition Comparison */}
        <div className="map-sidebar-pane">
          {/* Cluster Explorer */}
          <div className="sidebar-card">
            <div className="card-header">
              <span>◈</span>
              <span>CLUSTER EXPLORER ({clusters.length})</span>
            </div>
            <div className="clusters-list">
              {clusters.map((c) => (
                <div key={c.cluster_id} className="cluster-item">
                  <div className="cluster-head">
                    <span className="cluster-badge">CLUSTER {String(c.cluster_id).padStart(2, '0')}</span>
                    <span className="member-count">{c.members.length} MEMORIES</span>
                  </div>
                  <div className="cluster-metrics">
                    <span>COHESION: {c.cohesion.toFixed(2)}</span>
                    <span>SEPARATION: {c.separation.toFixed(2)}</span>
                  </div>
                  <div className="cluster-members">
                    {c.members.map((m) => (
                      <span
                        key={m}
                        className={`cluster-pill ${selectedMemoryId === m ? 'selected' : ''}`}
                        onClick={() => onSelectMemory(m)}
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Memory Neighborhood ("Semantic Galaxy") */}
          <div className="sidebar-card">
            <div className="card-header">
              <span>◎</span>
              <span>MEMORY NEIGHBORHOOD</span>
            </div>
            {selectedPt ? (
              <div className="neighborhood-box">
                <div className="center-node">
                  <span className="center-label">TARGET: {selectedPt.label}</span>
                  <span className="center-id">({selectedPt.memory_id})</span>
                </div>
                <div className="neighbors-list">
                  {points
                    .filter((p) => p.memory_id !== selectedPt.memory_id)
                    .map((other) => {
                      const dist = Math.hypot(other.x - selectedPt.x, other.y - selectedPt.y)
                      const similarity = Math.max(0, 1 - dist / 3)
                      return (
                        <div
                          key={other.memory_id}
                          className="neighbor-row"
                          onClick={() => onSelectMemory(other.memory_id)}
                        >
                          <span className="neighbor-name">{other.label}</span>
                          <span className="neighbor-sim cyan">SIM: {similarity.toFixed(3)}</span>
                        </div>
                      )
                    })}
                </div>
              </div>
            ) : null}
          </div>

          {/* Memory Competition View (A vs B) */}
          <div className="sidebar-card">
            <div className="card-header">
              <span>⚔</span>
              <span>MEMORY COMPETITION VIEW</span>
            </div>
            <div className="competition-pickers">
              <select value={compMemoryA} onChange={(e) => setCompMemoryA(e.target.value)}>
                {points.map((p) => (
                  <option key={p.memory_id} value={p.memory_id}>
                    {p.label} ({p.memory_id})
                  </option>
                ))}
              </select>
              <span className="vs-tag">VS</span>
              <select value={compMemoryB} onChange={(e) => setCompMemoryB(e.target.value)}>
                {points.map((p) => (
                  <option key={p.memory_id} value={p.memory_id}>
                    {p.label} ({p.memory_id})
                  </option>
                ))}
              </select>
            </div>

            {activeCompetition ? (
              <div className="competition-details">
                <div className="comp-row">
                  <span>CUE SIMILARITY:</span>
                  <span className="amber">{(activeCompetition.similarity * 100).toFixed(1)}%</span>
                </div>
                <div className="comp-row">
                  <span>CROSS-TALK DEGRADATION:</span>
                  <span className="crimson">-{activeCompetition.degradation.toFixed(4)}</span>
                </div>
                <div className="comp-row">
                  <span>CONFLICTING EVENT:</span>
                  <code>{activeCompetition.event_id}</code>
                </div>
                <button
                  type="button"
                  className="secondary small-btn"
                  style={{ marginTop: '0.5rem', width: '100%' }}
                  onClick={() =>
                    onViewEvidence('Memory Competition & Cross-Talk Evidence', {
                      memory_a: compMemoryA,
                      memory_b: compMemoryB,
                      active_competition: activeCompetition,
                      variance_explained: memoryMap?.variance_explained,
                    })
                  }
                >
                  VIEW COMPETITION EVIDENCE
                </button>
              </div>
            ) : (
              <div className="diff-placeholder">
                No active conflicting writes detected between these two memory cues.
                <button
                  type="button"
                  className="secondary small-btn"
                  style={{ marginTop: '0.5rem', width: '100%' }}
                  onClick={() =>
                    onViewEvidence('Memory Map & Manifold Topology', {
                      projection_method: memoryMap?.projection_method,
                      variance_explained: memoryMap?.variance_explained,
                      total_points: points.length,
                    })
                  }
                >
                  VIEW MANIFOLD PROVENANCE
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
