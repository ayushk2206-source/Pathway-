import React, { useState } from 'react'
import type { SurgeryRecallComparison } from '../types'

interface SurgeryResultPanelProps {
  comparison: SurgeryRecallComparison | null
  isLocked: boolean
  isBusy: boolean
  onRunRecall: (concept: string, expectedValue?: string) => void
  availableConcepts?: string[]
}

export const SurgeryResultPanel: React.FC<SurgeryResultPanelProps> = ({
  comparison,
  isLocked,
  isBusy,
  onRunRecall,
  availableConcepts = [],
}) => {
  const [queryConcept, setQueryConcept] = useState<string>(
    comparison?.query_concept || (availableConcepts[0] ?? '')
  )
  const [expectedValue, setExpectedValue] = useState<string>(
    comparison?.expected_value || ''
  )

  const handleRecallSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryConcept.trim()) return
    onRunRecall(queryConcept.trim(), expectedValue.trim() || undefined)
  }

  return (
    <div className="surgery-result-panel">
      {/* Panel Title */}
      <div className="result-panel-header">
        <div className="result-header-title">
          <span className="result-icon">⚖</span>
          <div>
            <h4 className="title-text">EXPERIMENTAL RECALL COMPARISON</h4>
            <span className="sub-text">Baseline Snapshot vs Experimental Branch</span>
          </div>
        </div>

        {comparison && (
          <span className="experiment-badge" title="Type of experiment performed">
            {comparison.experiment_label}
          </span>
        )}
      </div>

      {/* Query Trigger Form */}
      <form onSubmit={handleRecallSubmit} className="recall-test-form">
        <div className="recall-form-fields">
          <div className="recall-input-group">
            <label>QUERY CONCEPT:</label>
            {availableConcepts.length > 0 ? (
              <div className="concept-input-with-datalist">
                <input
                  type="text"
                  value={queryConcept}
                  onChange={(e) => setQueryConcept(e.target.value)}
                  placeholder="e.g. color"
                  list="available-concepts-list"
                  disabled={!isLocked || isBusy}
                  className="concept-text-input"
                />
                <datalist id="available-concepts-list">
                  {availableConcepts.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
              </div>
            ) : (
              <input
                type="text"
                value={queryConcept}
                onChange={(e) => setQueryConcept(e.target.value)}
                placeholder="e.g. color"
                disabled={!isLocked || isBusy}
                className="concept-text-input"
              />
            )}
          </div>

          <div className="recall-input-group">
            <label>EXPECTED VALUE (OPTIONAL):</label>
            <input
              type="text"
              value={expectedValue}
              onChange={(e) => setExpectedValue(e.target.value)}
              placeholder="e.g. blue"
              disabled={!isLocked || isBusy}
              className="concept-text-input"
            />
          </div>

          <button
            type="submit"
            className="btn-run-recall"
            disabled={!isLocked || !queryConcept.trim() || isBusy}
            title="Execute associative recall on both baseline and experimental branches simultaneously"
          >
            {isBusy ? 'Evaluating...' : '🔬 Compare Recall'}
          </button>
        </div>
      </form>

      {/* Comparison Results Card */}
      {comparison ? (
        <div className="comparison-card">
          {/* Agreement Status Banner */}
          <div
            className={`comparison-status-bar ${
              comparison.change.agreement ? 'status-agree' : 'status-diverged'
            }`}
          >
            <span className="status-indicator-dot">●</span>
            <span className="status-label">
              {comparison.change.agreement
                ? 'OUTPUT PRESERVED: Both branches recalled the same value'
                : 'OUTPUT DIVERGED: Intervention caused recall shift'}
            </span>
            <span className="ops-count-tag">
              {comparison.operations_applied} operation(s) applied
            </span>
          </div>

          {/* Three-Column Comparison Grid */}
          <div className="comparison-three-columns">
            {/* Column 1: Baseline */}
            <div className="col-card baseline-col">
              <div className="col-header">
                <span className="col-title">FROZEN BASELINE</span>
                <span className="col-tag">Original</span>
              </div>
              <div className="col-metrics">
                <div className="metric-row">
                  <span className="m-label">PREDICTED:</span>
                  <span className="m-val highlight">
                    {comparison.baseline.predicted || '—'}
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">CONFIDENCE:</span>
                  <span className="m-val">
                    {(comparison.baseline.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">READOUT NORM:</span>
                  <span className="m-val mono">
                    {comparison.baseline.readout_norm.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>

            {/* Column 2: Surgery */}
            <div className="col-card surgery-col">
              <div className="col-header">
                <span className="col-title">SURGERY BRANCH</span>
                <span className="col-tag cyan">Modified</span>
              </div>
              <div className="col-metrics">
                <div className="metric-row">
                  <span className="m-label">PREDICTED:</span>
                  <span
                    className={`m-val highlight ${
                      comparison.surgery.predicted === comparison.baseline.predicted
                        ? 'cyan'
                        : 'rose'
                    }`}
                  >
                    {comparison.surgery.predicted || '—'}
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">CONFIDENCE:</span>
                  <span className="m-val">
                    {(comparison.surgery.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">READOUT NORM:</span>
                  <span className="m-val mono">
                    {comparison.surgery.readout_norm.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>

            {/* Column 3: Change */}
            <div className="col-card change-col">
              <div className="col-header">
                <span className="col-title">NET CHANGE (Δ)</span>
                <span className="col-tag amber">Observed</span>
              </div>
              <div className="col-metrics">
                <div className="metric-row">
                  <span className="m-label">AGREEMENT:</span>
                  <span
                    className={`m-val ${
                      comparison.change.agreement ? 'emerald' : 'rose'
                    }`}
                  >
                    {comparison.change.agreement ? 'MATCH' : 'DIVERGED'}
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">Δ CONFIDENCE:</span>
                  <span
                    className={`m-val mono ${
                      comparison.change.delta_confidence > 0.001
                        ? 'emerald'
                        : comparison.change.delta_confidence < -0.001
                        ? 'rose'
                        : 'slate'
                    }`}
                  >
                    {comparison.change.delta_confidence >= 0 ? '+' : ''}
                    {(comparison.change.delta_confidence * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">Δ READOUT NORM:</span>
                  <span
                    className={`m-val mono ${
                      comparison.change.delta_readout_norm > 0.001
                        ? 'emerald'
                        : comparison.change.delta_readout_norm < -0.001
                        ? 'rose'
                        : 'slate'
                    }`}
                  >
                    {comparison.change.delta_readout_norm >= 0 ? '+' : ''}
                    {comparison.change.delta_readout_norm.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Scientific Caution Note */}
          <div className="comparison-caution-note">
            <span className="caution-icon">⚠️</span>
            <span className="caution-text">{comparison.caution_note}</span>
          </div>
        </div>
      ) : (
        <div className="empty-comparison-placeholder">
          {isLocked ? (
            <span>
              Baseline locked. Run a recall query above to compare performance between the frozen baseline and the experimental surgery branch.
            </span>
          ) : (
            <span>Lock baseline first to enable side-by-side recall comparison.</span>
          )}
        </div>
      )}
    </div>
  )
}
