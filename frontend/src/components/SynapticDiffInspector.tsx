import React, { useEffect, useState } from 'react'
import type { StateDiffResult, SynapticTimelineEvent } from '../types'
import { diffSynapticStates } from '../api'

interface SynapticDiffInspectorProps {
  timeline: SynapticTimelineEvent[]
  currentStep: number
  experimentId?: string
  diffHighlight: boolean
  onToggleDiffHighlight: (active: boolean) => void
  onSelectSynapse: (synapseId: string) => void
  onClose: () => void
  onDiffComputed?: (diff: StateDiffResult | null) => void
}

export const SynapticDiffInspector: React.FC<SynapticDiffInspectorProps> = ({
  timeline,
  currentStep,
  experimentId,
  diffHighlight,
  onToggleDiffHighlight,
  onSelectSynapse,
  onClose,
  onDiffComputed,
}) => {
  const [stepA, setStepA] = useState<number>(Math.max(0, currentStep - 1))
  const [stepB, setStepB] = useState<number>(currentStep)
  const [diffResult, setDiffResult] = useState<StateDiffResult | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDiff = async (a: number, b: number) => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await diffSynapticStates({
        step_a: a,
        step_b: b,
        experiment_id: experimentId,
      })
      setDiffResult(res)
      onDiffComputed?.(res)
    } catch (err) {
      setError(String(err))
      onDiffComputed?.(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchDiff(stepA, stepB)
  }, [stepA, stepB, experimentId])

  return (
    <div className="synaptic-diff-inspector">
      <div className="diff-header">
        <div className="diff-title-row">
          <span className="diff-title">FORENSIC STATE COMPARISON</span>
          <button type="button" className="diff-close-btn" onClick={onClose} title="Close Comparison">
            ✕
          </button>
        </div>
        <div className="diff-selectors">
          <div className="diff-selector-col">
            <label className="diff-label">BEFORE (TA):</label>
            <select
              value={stepA}
              onChange={(e) => setStepA(parseInt(e.target.value, 10))}
              className="diff-select"
            >
              {timeline.map((ev, idx) => (
                <option key={idx} value={idx}>
                  T{idx}: {ev.label}
                </option>
              ))}
            </select>
          </div>

          <span className="diff-arrow">⇄</span>

          <div className="diff-selector-col">
            <label className="diff-label">AFTER (TB):</label>
            <select
              value={stepB}
              onChange={(e) => setStepB(parseInt(e.target.value, 10))}
              className="diff-select"
            >
              {timeline.map((ev, idx) => (
                <option key={idx} value={idx}>
                  T{idx}: {ev.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Highlight Toggle */}
        <div className="diff-toggle-row">
          <label className="diff-checkbox-label">
            <input
              type="checkbox"
              checked={diffHighlight}
              onChange={(e) => onToggleDiffHighlight(e.target.checked)}
            />
            Highlight changes on synaptic network canvas
          </label>
        </div>
      </div>

      {/* Content Body */}
      {isLoading ? (
        <div className="diff-loading">Computing matrix delta ΔW = W(TB) - W(TA)...</div>
      ) : error ? (
        <div className="diff-error">Error: {error}</div>
      ) : diffResult ? (
        <div className="diff-body">
          {/* Summary Metrics */}
          <div className="diff-summary-grid">
            <div className="diff-stat-card strengthened">
              <span className="stat-badge-k">STRENGTHENED (LTP)</span>
              <span className="stat-badge-v">+{diffResult.strengthened_count}</span>
            </div>
            <div className="diff-stat-card weakened">
              <span className="stat-badge-k">WEAKENED (LTD)</span>
              <span className="stat-badge-v">−{diffResult.weakened_count}</span>
            </div>
            <div className="diff-stat-card unchanged">
              <span className="stat-badge-k">UNCHANGED</span>
              <span className="stat-badge-v">={diffResult.unchanged_count}</span>
            </div>
            <div className="diff-stat-card norm">
              <span className="stat-badge-k">||ΔW|| FROBENIUS</span>
              <span className="stat-badge-v">{diffResult.frobenius_norm_delta.toFixed(4)}</span>
            </div>
          </div>

          {/* Top Changed Synapses */}
          <div className="diff-changes-section">
            <div className="section-title">TOP SYNAPTIC DELTAS (ΔW)</div>
            <div className="diff-table-container">
              <table className="diff-table">
                <thead>
                  <tr>
                    <th>Synapse</th>
                    <th>Source → Target</th>
                    <th>W(TA)</th>
                    <th>W(TB)</th>
                    <th>ΔW</th>
                  </tr>
                </thead>
                <tbody>
                  {diffResult.top_changes.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="empty-diff-row">
                        No significant synaptic weight changes between T{stepA} and T{stepB}.
                      </td>
                    </tr>
                  ) : (
                    diffResult.top_changes.map((syn) => {
                      const isLTP = syn.delta_weight > 0
                      return (
                        <tr
                          key={syn.synapse_id}
                          className="diff-row"
                          onClick={() => onSelectSynapse(syn.synapse_id)}
                          title="Click to inspect this synapse"
                        >
                          <td className="syn-id-cell">{syn.synapse_id}</td>
                          <td className="syn-route-cell">
                            {syn.source} → {syn.target}
                          </td>
                          <td className="num-cell">{syn.weight_a.toFixed(3)}</td>
                          <td className="num-cell">{syn.weight_b.toFixed(3)}</td>
                          <td className={`delta-cell ${isLTP ? 'delta-pos' : 'delta-neg'}`}>
                            {isLTP ? `+${syn.delta_weight.toFixed(3)}` : syn.delta_weight.toFixed(3)}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
