import React from 'react'
import type { MemoryBranchNode } from '../types'

interface MemoryFamilyTreeProps {
  tree: MemoryBranchNode | null
  selectedNodeId?: string
  onSelectNode: (node: MemoryBranchNode) => void
}

export const MemoryFamilyTree: React.FC<MemoryFamilyTreeProps> = ({
  tree,
  selectedNodeId,
  onSelectNode,
}) => {
  if (!tree) {
    return (
      <div className="forensic-card" style={{ color: '#64748b', fontSize: '0.85rem' }}>
        No branch tree available.
      </div>
    )
  }

  // Recursive render of tree nodes
  const renderNode = (node: MemoryBranchNode, depth: number = 0) => {
    const isSelected = selectedNodeId === node.node_id

    let badgeColor = '#38bdf8'
    if (node.branch_type === 'COLLISION') badgeColor = '#f59e0b'
    if (node.branch_type === 'SURGERY') badgeColor = '#ec4899'
    if (node.branch_type === 'COUNTERFACTUAL') badgeColor = '#a855f7'

    return (
      <div key={node.node_id} style={{ marginLeft: `${depth * 20}px`, marginTop: '0.5rem' }}>
        <div
          onClick={() => onSelectNode(node)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.75rem',
            background: isSelected ? 'rgba(56, 189, 248, 0.2)' : 'rgba(30, 41, 59, 0.6)',
            border: `1px solid ${isSelected ? '#38bdf8' : 'rgba(71, 85, 105, 0.4)'}`,
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.8rem',
            transition: 'all 0.15s ease',
          }}
        >
          <span style={{ color: badgeColor, fontWeight: 700, fontSize: '0.7rem' }}>
            [{node.branch_type}]
          </span>
          <span style={{ color: '#f8fafc', fontWeight: 600 }}>{node.label}</span>
          {node.fingerprint && (
            <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'monospace' }}>
              Fidelity: {(node.fingerprint.recall_performance.fidelity * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {node.children && node.children.length > 0 && (
          <div style={{ borderLeft: '1px dashed rgba(71, 85, 105, 0.5)', marginLeft: '12px', paddingLeft: '4px' }}>
            {node.children.map((c) => renderNode(c, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="forensic-card">
      <div className="forensic-card-header">
        <h3 className="forensic-card-title">
          <span>Memory Family Tree (Branch Navigation)</span>
        </h3>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Original ➔ Collision ➔ Surgery ➔ Counterfactual
        </span>
      </div>

      <div className="family-tree-container">{renderNode(tree)}</div>
    </div>
  )
}
