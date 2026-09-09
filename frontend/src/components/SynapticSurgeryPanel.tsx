import React, { useState } from 'react'
import type { SurgerySession, SynapseXRayDetail } from '../types'

interface SynapticSurgeryPanelProps {
  session: SurgerySession | null
  isLocked: boolean
  selectedSynapseIds: string[]
  onClearSelectedSynapses: () => void
  onSelectHighRelevanceSynapses?: () => void
  onLockBaseline: () => void
  onWeaken: (factor: number) => void
  onStrengthen: (factor: number) => void
  onSilence: () => void
  onRestore: () => void
  onReset: () => void
  synapseDetail: SynapseXRayDetail | null
  isBusy: boolean
}

export const SynapticSurgeryPanel: React.FC<SynapticSurgeryPanelProps> = ({
  session,
  isLocked,
  selectedSynapseIds,
  onClearSelectedSynapses,
  onSelectHighRelevanceSynapses,
  onLockBaseline,
  onWeaken,
  onStrengthen,
  onSilence,
  onRestore,
  onReset,
  synapseDetail,
  isBusy,
}) => {
  const [weakenFactor, setWeakenFactor] = useState<number>(0.5)
  const [strengthenFactor, setStrengthenFactor] = useState<number>(2.0)

  const hasSelection = selectedSynapseIds.length > 0

  return (
    <div className="surgery-control-panel">
      {/* Header & Lock Status */}
      <div className="surgery-panel-header">
        <div className="surgery-panel-title-group">
          <span className="surgery-panel-icon">⚕</span>
          <div>
            <h3 className="surgery-panel-title">SYNAPTIC SURGERY WORKBENCH</h3>
            <span className="surgery-panel-sub">Isolated Experimental Branch</span>
          </div>
        </div>

        <div className="surgery-branch-badge">
          {isLocked ? (
            <span className="badge-locked" title="Experimental branch is isolated from live brain">
              ● BRANCH ACTIVE
            </span>
          ) : (
            <span className="badge-unlocked" title="Baseline snapshot not yet created">
              ○ UNLOCKED
            </span>
          )}
        </div>
      </div>

      {/* Lock / Reset Toolbar */}
      <div className="surgery-toolbar">
        {!isLocked ? (
          <button
            className="btn-lock-baseline"
            onClick={onLockBaseline}
            disabled={isBusy}
            title="Freeze live brain as baseline snapshot and create experimental copy"
          >
            🔒 LOCK BASELINE SNAPSHOT
          </button>
        ) : (
          <div className="surgery-locked-controls">
            <button
              className="btn-reset-branch"
              onClick={onReset}
              disabled={isBusy}
              title="Discard all experimental modifications and revert to baseline"
            >
              ↺ Reset Branch to Baseline
            </button>
            <button
              className="btn-re-lock"
              onClick={onLockBaseline}
              disabled={isBusy}
              title="Capture a new baseline snapshot from the current live brain"
            >
              Re-Lock Current Brain
            </button>
          </div>
        )}
      </div>

      {/* Session telemetry if locked */}
      {isLocked && session && (
        <div className="surgery-telemetry-strip">
          <div className="telem-item">
            <span className="telem-label">OPERATIONS</span>
            <span className="telem-val cyan">{session.operations.length}</span>
          </div>
          <div className="telem-item">
            <span className="telem-label">SURGERY NORM</span>
            <span className="telem-val amber">{session.surgery_matrix_norm.toFixed(4)}</span>
          </div>
          <div className="telem-item">
            <span className="telem-label">BASELINE NORM</span>
            <span className="telem-val slate">{session.baseline_matrix_norm.toFixed(4)}</span>
          </div>
          <div className="telem-item">
            <span className="telem-label">MEMORIES</span>
            <span className="telem-val emerald">{session.library_size}</span>
          </div>
        </div>
      )}

      {/* Synapse Selection Bar */}
      <div className="surgery-selection-section">
        <div className="selection-header">
          <span className="selection-label">
            TARGET SYNAPSES ({selectedSynapseIds.length} SELECTED)
          </span>
          <div className="selection-actions">
            {onSelectHighRelevanceSynapses && (
              <button
                type="button"
                className="btn-text-action"
                onClick={onSelectHighRelevanceSynapses}
                title="Select all synapses flagged as high relevance in current Memory X-Ray"
              >
                + Select High Relevance
              </button>
            )}
            {hasSelection && (
              <button
                type="button"
                className="btn-text-action"
                onClick={onClearSelectedSynapses}
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {hasSelection ? (
          <div className="selected-synapses-pill-list">
            {selectedSynapseIds.slice(0, 12).map((id) => (
              <span key={id} className="synapse-pill">
                {id}
              </span>
            ))}
            {selectedSynapseIds.length > 12 && (
              <span className="synapse-pill-more">
                +{selectedSynapseIds.length - 12} more
              </span>
            )}
          </div>
        ) : (
          <div className="empty-selection-note">
            Click on synapses in the network canvas or select memories in Memory X-Ray below to target synapses.
          </div>
        )}
      </div>

      {/* Single Synapse Inspector if 1 selected */}
      {selectedSynapseIds.length === 1 && synapseDetail && (
        <div className="synapse-single-inspector">
          <div className="syn-inspector-header">
            <span className="syn-id-badge">{synapseDetail.synapse_id}</span>
            <span className="syn-path-label">
              {synapseDetail.source} → {synapseDetail.target}
            </span>
          </div>
          <div className="syn-metrics-grid">
            <div className="syn-metric">
              <span className="lbl">BASELINE WEIGHT</span>
              <span className="val">{synapseDetail.baseline_weight.toFixed(5)}</span>
            </div>
            <div className="syn-metric">
              <span className="lbl">SURGERY WEIGHT</span>
              <span className="val cyan">{synapseDetail.surgery_weight.toFixed(5)}</span>
            </div>
            <div className="syn-metric">
              <span className="lbl">DELTA (Δ)</span>
              <span
                className={`val ${
                  synapseDetail.weight_delta > 0.0001
                    ? 'emerald'
                    : synapseDetail.weight_delta < -0.0001
                    ? 'rose'
                    : 'slate'
                }`}
              >
                {synapseDetail.weight_delta >= 0 ? '+' : ''}
                {synapseDetail.weight_delta.toFixed(5)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Surgery Action Buttons */}
      <div className="surgery-operations-grid">
        {/* Weaken */}
        <div className="operation-card">
          <div className="op-card-top">
            <span className="op-title">WEAKEN</span>
            <span className="op-param">{weakenFactor.toFixed(2)}x</span>
          </div>
          <input
            type="range"
            min="0.05"
            max="0.95"
            step="0.05"
            value={weakenFactor}
            onChange={(e) => setWeakenFactor(Number(e.target.value))}
            disabled={!isLocked || !hasSelection || isBusy}
            className="surgery-slider"
          />
          <button
            className="btn-op btn-weaken"
            onClick={() => onWeaken(weakenFactor)}
            disabled={!isLocked || !hasSelection || isBusy}
            title="Scale down selected synapse weights in surgery branch"
          >
            📉 Apply Weaken
          </button>
        </div>

        {/* Strengthen */}
        <div className="operation-card">
          <div className="op-card-top">
            <span className="op-title">STRENGTHEN</span>
            <span className="op-param">{strengthenFactor.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min="1.1"
            max="4.0"
            step="0.1"
            value={strengthenFactor}
            onChange={(e) => setStrengthenFactor(Number(e.target.value))}
            disabled={!isLocked || !hasSelection || isBusy}
            className="surgery-slider"
          />
          <button
            className="btn-op btn-strengthen"
            onClick={() => onStrengthen(strengthenFactor)}
            disabled={!isLocked || !hasSelection || isBusy}
            title="Scale up selected synapse weights in surgery branch"
          >
            📈 Apply Strengthen
          </button>
        </div>

        {/* Silence (Controlled Ablation) */}
        <div className="operation-card ablation-card">
          <div className="op-card-top">
            <span className="op-title rose">SILENCE (ABLATION)</span>
            <span className="op-param rose">W = 0</span>
          </div>
          <p className="ablation-explainer">
            CONTROLLED ABLATION EXPERIMENT: Sets selected synapse weights to 0 in experimental branch.
          </p>
          <button
            className="btn-op btn-silence"
            onClick={onSilence}
            disabled={!isLocked || !hasSelection || isBusy}
            title="Ablate selected synapses (set weight to 0)"
          >
            ✂ Silence Synapses
          </button>
        </div>

        {/* Restore */}
        <div className="operation-card">
          <div className="op-card-top">
            <span className="op-title">RESTORE</span>
            <span className="op-param cyan">Revert</span>
          </div>
          <p className="ablation-explainer">
            Reverts selected synapses from frozen baseline snapshot.
          </p>
          <button
            className="btn-op btn-restore"
            onClick={onRestore}
            disabled={!isLocked || !hasSelection || isBusy}
            title="Restore selected synapses to baseline"
          >
            ↺ Restore Selected
          </button>
        </div>
      </div>

      {/* Educational Caution Banner */}
      <div className="surgery-transparency-banner">
        <span className="banner-icon">ℹ</span>
        <div className="banner-text">
          <strong>CONTROLLED ABLATION EXPERIMENT:</strong> All modifications occur on an isolated experimental branch.
          The baseline brain is preserved. Altering or removing connections measures changes in recall fidelity;
          this observational shift is associated with the intervention and does not assert biological causation.
        </div>
      </div>
    </div>
  )
}
