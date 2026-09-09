import React, { useState } from 'react'
import type { CounterfactualExperiment } from '../types'

interface CounterfactualHypothesisCardProps {
  counterfactual: CounterfactualExperiment | null
  currentHypothesis: string
  onChangeHypothesis: (val: string) => void
  onRunIntervention: () => void
  isExecuting: boolean
  variableControlledDescription: string
  onReRun: () => void
  onExport: () => void
  onSelectGuidedSynapse?: (synapseId: string) => void
  topCandidateSynapses?: string[]
}

export const CounterfactualHypothesisCard: React.FC<CounterfactualHypothesisCardProps> = ({
  counterfactual,
  currentHypothesis,
  onChangeHypothesis,
  onRunIntervention,
  isExecuting,
  variableControlledDescription,
  onReRun,
  onExport,
  onSelectGuidedSynapse,
  topCandidateSynapses = [],
}) => {
  const [discoverMode, setDiscoverMode] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopyCompact = () => {
    if (!counterfactual) return
    onExport?.()
    const origAcc = counterfactual.original_result.metrics?.recall_accuracy ?? 'N/A'
    const cfAcc = counterfactual.counterfactual_result.metrics?.recall_accuracy ?? 'N/A'
    const text = `COUNTERFACTUAL ${counterfactual.counterfactual_id}
Baseline: ${counterfactual.parent_experiment_id}
Divergence: T${counterfactual.provenance?.branch_point ?? 0}
Intervention: ${counterfactual.intervention_type} (${variableControlledDescription})
Hypothesis: ${counterfactual.description || 'N/A'}
Result: Recall Accuracy changed from ${origAcc} → ${cfAcc}
Scientific Note: Controlled computational intervention in educational associative memory model.`

    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }


  const origMetrics = counterfactual?.original_result?.metrics || {}
  const cfMetrics = counterfactual?.counterfactual_result?.metrics || {}

  const origRecall = typeof origMetrics.recall_accuracy === 'number' ? (origMetrics.recall_accuracy * 100).toFixed(1) : '—'
  const cfRecall = typeof cfMetrics.recall_accuracy === 'number' ? (cfMetrics.recall_accuracy * 100).toFixed(1) : '—'
  const origStrength = typeof origMetrics.mean_retrieval_strength === 'number' ? origMetrics.mean_retrieval_strength.toFixed(3) : '—'
  const cfStrength = typeof cfMetrics.mean_retrieval_strength === 'number' ? cfMetrics.mean_retrieval_strength.toFixed(3) : '—'

  return (
    <div className="hypothesis-workflow-card">
      <div className="hypothesis-header">
        <div className="step-chain">
          <span className="chain-node active">1. HYPOTHESIS</span>
          <span className="chain-sep">→</span>
          <span className={`chain-node ${isExecuting ? 'active' : ''}`}>2. EXPERIMENT</span>
          <span className="chain-sep">→</span>
          <span className={`chain-node ${counterfactual ? 'active' : ''}`}>3. OBSERVATION</span>
          <span className="chain-sep">→</span>
          <span className={`chain-node ${counterfactual ? 'active' : ''}`}>4. RESULT</span>
        </div>

        <div className="mode-toggle">
          <button
            type="button"
            className={`discover-toggle-btn ${discoverMode ? 'active' : ''}`}
            onClick={() => setDiscoverMode(!discoverMode)}
          >
            {discoverMode ? '🔍 DISCOVER MODE: ACTIVE' : 'DISCOVER MODE'}
          </button>
        </div>
      </div>

      {/* Discover Mode Prompt */}
      {discoverMode && (
        <div className="discover-mode-banner">
          <div className="discover-title">INVESTIGATE: WHICH CONNECTION DRIVES THIS MEMORY?</div>
          <p className="discover-sub">
            Formulate an empirical prediction: test which synapse's strengthening is causally necessary for retrieval.
          </p>
          {topCandidateSynapses.length > 0 && onSelectGuidedSynapse && (
            <div className="guided-candidate-chips">
              <span className="guide-lbl">Candidate Connections:</span>
              {topCandidateSynapses.slice(0, 5).map((s) => (
                <button
                  key={s}
                  type="button"
                  className="syn-chip-btn"
                  onClick={() => onSelectGuidedSynapse(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Hypothesis Input Box */}
      <div className="hypothesis-input-group">
        <div className="lbl-row">
          <label className="hyp-lbl">YOUR EMPIRICAL HYPOTHESIS (FORMULATE BEFORE EXECUTING):</label>
          <span className="controlled-chip">VARIABLE CONTROLLED</span>
        </div>
        <textarea
          value={currentHypothesis}
          onChange={(e) => onChangeHypothesis(e.target.value)}
          placeholder='e.g. "If syn_k1_v2 strengthening is prevented, recall of the target cue will fail because the linear readout projection is suppressed."'
          className="hypothesis-textarea"
          rows={2}
        />
        <div className="controlled-var-banner">
          <span className="cv-icon">⚖</span>
          <span className="cv-text">
            <strong>SINGLE-VARIABLE CONTROL:</strong> {variableControlledDescription} All other parameters, symbols, and timings remain identical.
          </span>
        </div>
      </div>

      {/* Action Trigger */}
      <div className="hypothesis-actions">
        <button
          className="execute-branch-btn primary"
          onClick={onRunIntervention}
          disabled={isExecuting}
        >
          {isExecuting ? 'COMPUTING REAL COUNTERFACTUAL...' : '⚡ EXECUTE COUNTERFACTUAL BRANCH'}
        </button>

        {counterfactual && (
          <div className="post-run-actions">
            <button className="rerun-btn" onClick={onReRun} title="Reproduce deterministic counterfactual">
              ↻ RE-RUN
            </button>
            <button className="export-btn" onClick={handleCopyCompact}>
              {copied ? '✓ COPIED!' : '📋 EXPORT COMPACT'}
            </button>
          </div>
        )}
      </div>

      {/* Results and Conclusion if Counterfactual Exists */}
      {counterfactual && (
        <div className="counterfactual-outcome-box">
          <div className="outcome-header">
            <span className="outcome-title">MEASURED COMPUTATIONAL DELTA</span>
            <span className="branch-badge">{counterfactual.counterfactual_id}</span>
          </div>

          <div className="outcome-metrics-grid">
            <div className="outcome-metric-card">
              <span className="m-name">RECALL ACCURACY</span>
              <div className="m-vals">
                <span className="orig-val">{origRecall}%</span>
                <span className="arrow">→</span>
                <span className="cf-val">{cfRecall}%</span>
              </div>
              <span className="delta-tag">
                Δ = {(Number(cfRecall) - Number(origRecall)).toFixed(1)}%
              </span>
            </div>

            <div className="outcome-metric-card">
              <span className="m-name">RETRIEVAL STRENGTH</span>
              <div className="m-vals">
                <span className="orig-val">{origStrength}</span>
                <span className="arrow">→</span>
                <span className="cf-val">{cfStrength}</span>
              </div>
              <span className="delta-tag">
                Δ = {(Number(cfStrength) - Number(origStrength)).toFixed(3)}
              </span>
            </div>

            <div className="outcome-metric-card">
              <span className="m-name">STATE L2 DIVERGENCE</span>
              <div className="m-vals">
                <span className="cf-val cyan">
                  {counterfactual.comparison?.state_distance_l2?.toFixed(4) || '—'}
                </span>
              </div>
              <span className="delta-tag">
                {counterfactual.comparison?.divergence_classification || 'DIVERGED'}
              </span>
            </div>
          </div>

          {/* Scientific Honesty Notice */}
          <div className="scientific-honesty-notice">
            <span className="notice-icon">🔬</span>
            <span className="notice-text">
              <strong>SCIENTIFIC COMPUTATIONAL NOTE:</strong> Controlled computational intervention changed the measured outcome. This demonstrates causal sensitivity in this educational computational model.
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
