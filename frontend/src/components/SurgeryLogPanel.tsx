import React from 'react'
import type { SurgeryOperation } from '../types'

interface SurgeryLogPanelProps {
  operations: SurgeryOperation[]
  onSelectOperationSynapses?: (synapseIds: string[]) => void
}

export const SurgeryLogPanel: React.FC<SurgeryLogPanelProps> = ({
  operations,
  onSelectOperationSynapses,
}) => {
  return (
    <div className="surgery-log-panel">
      <div className="log-panel-header">
        <div className="log-header-left">
          <span className="log-icon">📋</span>
          <h4 className="log-title">EXPERIMENTAL SURGERY LOG</h4>
          <span className="log-count">({operations.length} recorded operations)</span>
        </div>
        <span className="log-disclaimer-tag">
          Auditable intervention history — experimental branch only
        </span>
      </div>

      {operations.length === 0 ? (
        <div className="log-empty-state">
          No surgery operations recorded yet in this session.
          Use the workbench above to weaken, strengthen, silence, or restore synapses.
        </div>
      ) : (
        <div className="log-entries-list">
          {operations.map((op, idx) => {
            const isAblation = op.operation === 'silence'
            const isRestore = op.operation === 'restore' || op.operation === 'restore_all'
            const isWeaken = op.operation === 'weaken'

            return (
              <div
                key={op.op_id || idx}
                className={`log-entry-card ${isAblation ? 'entry-ablation' : ''}`}
                onClick={() => {
                  if (onSelectOperationSynapses && op.synapse_ids[0] !== '*') {
                    onSelectOperationSynapses(op.synapse_ids)
                  }
                }}
                title={
                  op.synapse_ids[0] !== '*'
                    ? `Click to select ${op.synapse_ids.length} synapse(s) affected by this operation`
                    : undefined
                }
              >
                <div className="entry-left-badge">
                  <span className="entry-index">#{idx + 1}</span>
                  <span
                    className={`entry-type-tag ${
                      isAblation
                        ? 'tag-rose'
                        : isRestore
                        ? 'tag-cyan'
                        : isWeaken
                        ? 'tag-amber'
                        : 'tag-emerald'
                    }`}
                  >
                    {op.operation.toUpperCase()}
                  </span>
                </div>

                <div className="entry-body">
                  <div className="entry-title-row">
                    <span className="entry-desc">{op.description}</span>
                    <span className="entry-time">Step {op.timestamp_step}</span>
                  </div>

                  <div className="entry-synapses-summary">
                    <span className="syn-count-badge">
                      {op.synapse_ids[0] === '*'
                        ? 'All synapses restored'
                        : `${op.synapse_ids.length} synapse(s): `}
                    </span>
                    {op.synapse_ids[0] !== '*' && (
                      <span className="syn-ids-inline">
                        {op.synapse_ids.slice(0, 8).join(', ')}
                        {op.synapse_ids.length > 8 && ` +${op.synapse_ids.length - 8} more`}
                      </span>
                    )}
                  </div>
                </div>

                {op.factor !== null && op.factor !== undefined && (
                  <div className="entry-factor-tag">
                    {op.factor === 0 ? 'W=0' : `${op.factor.toFixed(2)}x`}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
