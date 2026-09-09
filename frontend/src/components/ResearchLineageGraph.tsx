import React, { useState } from 'react'
import type { ResearchGraphData, ResearchGraphNode } from '../types'

interface ResearchLineageGraphProps {
  graphData: ResearchGraphData
  onSelectPaperId?: (paperId: string) => void
}

const TYPE_COLORS: Record<string, { stroke: string; fill: string; text: string }> = {
  CONCEPT: { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' },
  PAPER: { stroke: '#10b981', fill: 'rgba(16, 185, 129, 0.15)', text: '#34d399' },
  IMPLEMENTATION: { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.15)', text: '#7dd3fc' },
  OBSERVATION: { stroke: '#c084fc', fill: 'rgba(192, 132, 252, 0.15)', text: '#e9d5ff' },
  EXPERIMENT: { stroke: '#ec4899', fill: 'rgba(236, 72, 153, 0.15)', text: '#f472b6' },
}

export const ResearchLineageGraph: React.FC<ResearchLineageGraphProps> = ({
  graphData,
  onSelectPaperId,
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('concept_plasticity')

  // Group nodes into 4 horizontal visual columns
  const columnPositions = React.useMemo(() => {
    const colMap: Record<string, number> = {
      CONCEPT: 80,
      PAPER: 340,
      IMPLEMENTATION: 640,
      OBSERVATION: 940,
      EXPERIMENT: 640,
    }

    // Assign Y positions within each column
    const grouped: Record<string, ResearchGraphNode[]> = {
      CONCEPT: [],
      PAPER: [],
      IMPLEMENTATION: [],
      OBSERVATION: [],
    }

    graphData.nodes.forEach((n) => {
      const t = n.node_type === 'EXPERIMENT' ? 'IMPLEMENTATION' : n.node_type
      if (grouped[t]) {
        grouped[t].push(n)
      }
    })

    const coords = new Map<string, { x: number; y: number }>()

    Object.entries(grouped).forEach(([colType, nodes]) => {
      const spacingY = 90
      const totalH = (nodes.length - 1) * spacingY
      const offsetTop = Math.max(40, (400 - totalH) / 2)

      nodes.forEach((n, idx) => {
        coords.set(n.id, {
          x: colMap[colType] || 100,
          y: offsetTop + idx * spacingY,
        })
      })
    })

    return coords
  }, [graphData])

  const selectedNode = graphData.nodes.find((n) => n.id === selectedNodeId)

  return (
    <div className="graph-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.2rem', color: '#f8fafc' }}>
            Visual Research Lineage Graph
          </h2>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Concept &rarr; Published Literature &rarr; Computational Implementation &rarr; Empirical Observation
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.78rem' }}>
          <span style={{ color: '#fbbf24' }}>&bull; Concept</span>
          <span style={{ color: '#34d399' }}>&bull; Peer-Reviewed Paper</span>
          <span style={{ color: '#38bdf8' }}>&bull; Pathway Code</span>
          <span style={{ color: '#c084fc' }}>&bull; Empirical Observation</span>
        </div>
      </div>

      <div className="graph-svg-wrapper">
        <svg width="1120" height="460" viewBox="0 0 1120 460">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="6"
              refX="7"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#64748b" />
            </marker>
          </defs>

          {/* Render edges */}
          {graphData.edges.map((edge, idx) => {
            const src = columnPositions.get(edge.source)
            const tgt = columnPositions.get(edge.target)
            if (!src || !tgt) return null

            const isHighlighted =
              edge.source === selectedNodeId || edge.target === selectedNodeId

            const dx = (tgt.x - src.x) / 2
            const d = `M ${src.x + 80} ${src.y} C ${src.x + 80 + dx} ${src.y}, ${tgt.x - dx} ${tgt.y}, ${tgt.x - 10} ${tgt.y}`

            return (
              <path
                key={idx}
                d={d}
                fill="none"
                stroke={isHighlighted ? '#38bdf8' : 'rgba(100, 116, 139, 0.35)'}
                strokeWidth={isHighlighted ? 2.5 : 1.2}
                markerEnd="url(#arrowhead)"
              />
            )
          })}

          {/* Render nodes */}
          {graphData.nodes.map((node) => {
            const pos = columnPositions.get(node.id)
            if (!pos) return null

            const isSelected = node.id === selectedNodeId
            const color = TYPE_COLORS[node.node_type] || TYPE_COLORS.CONCEPT

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                style={{ cursor: 'pointer' }}
                onClick={() => setSelectedNodeId(node.id)}
              >
                {/* Node Pill */}
                <rect
                  x="-80"
                  y="-22"
                  width="160"
                  height="44"
                  rx="8"
                  fill={isSelected ? 'rgba(15, 23, 42, 0.95)' : color.fill}
                  stroke={isSelected ? '#ffffff' : color.stroke}
                  strokeWidth={isSelected ? 2.5 : 1.2}
                />
                <text
                  textAnchor="middle"
                  y="-4"
                  fill={color.text}
                  fontSize="11"
                  fontWeight="bold"
                >
                  {node.node_type}
                </text>
                <text
                  textAnchor="middle"
                  y="12"
                  fill="#f1f5f9"
                  fontSize="10"
                  fontWeight="500"
                >
                  {node.label.length > 20 ? `${node.label.slice(0, 19)}…` : node.label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="graph-details-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <div>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  color: TYPE_COLORS[selectedNode.node_type]?.text || '#38bdf8',
                  textTransform: 'uppercase',
                }}
              >
                Selected: {selectedNode.node_type}
              </span>
              <h3 style={{ margin: '0.15rem 0', fontSize: '1.05rem', color: '#f8fafc' }}>
                {selectedNode.label}
              </h3>
            </div>
            {selectedNode.node_type === 'PAPER' && onSelectPaperId && Boolean(selectedNode.details?.paper_id) && (
              <button
                className="tag-btn active"
                onClick={() => onSelectPaperId(String(selectedNode.details!.paper_id))}
              >
                Open Paper Card &rarr;
              </button>
            )}
          </div>

          <p style={{ margin: '0 0 0.5rem 0', color: '#cbd5e1', fontSize: '0.88rem', lineHeight: 1.45 }}>
            {selectedNode.summary}
          </p>

          {selectedNode.details && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: '0.78rem', color: '#94a3b8' }}>
              {Object.entries(selectedNode.details).map(([k, v]) => (
                <div key={k} style={{ background: 'rgba(0,0,0,0.25)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                  <strong>{k}:</strong> {String(v)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ResearchLineageGraph
