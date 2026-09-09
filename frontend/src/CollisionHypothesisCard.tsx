import React, { useState } from 'react'
import type { CollisionResult } from './types'

interface CollisionHypothesisCardProps {
  result: CollisionResult | null
  onTestHypothesis: (prediction: string) => void
}

export const CollisionHypothesisCard: React.FC<CollisionHypothesisCardProps> = ({
  result,
  onTestHypothesis,
}) => {
  const [selectedPrediction, setSelectedPrediction] = useState<'A_WINS' | 'B_WINS' | 'EQUAL'>('B_WINS')
  const [submitted, setSubmitted] = useState(false)

  const handlePredict = () => {
    setSubmitted(true)
    onTestHypothesis(selectedPrediction)
  }

  let hypothesisOutcome: { status: 'CONFIRMED' | 'REFUTED'; explanation: string } | null = null

  if (submitted && result) {
    const margin = result.dominant_memory_margin
    if (selectedPrediction === 'B_WINS') {
      if (result.memory_dominance === 'MEMORY_B') {
        hypothesisOutcome = {
          status: 'CONFIRMED',
          explanation: `Prediction confirmed: Memory B achieved higher recall fidelity (${result.combined_recall_b.fidelity.toFixed(3)} vs ${result.combined_recall_a.fidelity.toFixed(3)}) due to recency and overwrite of earlier synaptic traces.`,
        }
      } else {
        hypothesisOutcome = {
          status: 'REFUTED',
          explanation: `Prediction refuted: Memory A retained dominance (margin: ${margin.toFixed(3)}). Check importance/strength settings.`,
        }
      }
    } else if (selectedPrediction === 'A_WINS') {
      if (result.memory_dominance === 'MEMORY_A') {
        hypothesisOutcome = {
          status: 'CONFIRMED',
          explanation: `Prediction confirmed: Memory A maintained higher fidelity (${result.combined_recall_a.fidelity.toFixed(3)}).`,
        }
      } else {
        hypothesisOutcome = {
          status: 'REFUTED',
          explanation: `Prediction refuted: Memory B achieved higher fidelity (${result.combined_recall_b.fidelity.toFixed(3)}).`,
        }
      }
    } else {
      if (result.memory_dominance === 'BALANCED') {
        hypothesisOutcome = {
          status: 'CONFIRMED',
          explanation: 'Prediction confirmed: Both memories experienced equal interference within margin of 0.05.',
        }
      } else {
        hypothesisOutcome = {
          status: 'REFUTED',
          explanation: `Prediction refuted: An asymmetric dominance emerged (${result.memory_dominance}).`,
        }
      }
    }
  }

  return (
    <div className="collision-card">
      <div className="collision-card-header">
        <div>
          <h3 className="collision-card-title">🔬 Scientific Hypothesis & Interpretation</h3>
          <p className="collision-card-desc">
            Predict the outcome before running, then compare against verified linear algebraic metrics
          </p>
        </div>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '8px' }}>
          HYPOTHESIS: Which memory will retain higher recall fidelity in this collision condition?
        </label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className={`collision-btn collision-btn-outline ${selectedPrediction === 'B_WINS' ? 'collision-btn-active' : ''}`}
            onClick={() => { setSelectedPrediction('B_WINS'); setSubmitted(false) }}
          >
            Memory B (Recent Write)
          </button>
          <button
            type="button"
            className={`collision-btn collision-btn-outline ${selectedPrediction === 'A_WINS' ? 'collision-btn-active' : ''}`}
            onClick={() => { setSelectedPrediction('A_WINS'); setSubmitted(false) }}
          >
            Memory A (First Write)
          </button>
          <button
            type="button"
            className={`collision-btn collision-btn-outline ${selectedPrediction === 'EQUAL' ? 'collision-btn-active' : ''}`}
            onClick={() => { setSelectedPrediction('EQUAL'); setSubmitted(false) }}
          >
            Symmetric / Equal
          </button>
          <button
            type="button"
            className="collision-btn collision-btn-primary"
            onClick={handlePredict}
          >
            Verify Hypothesis
          </button>
        </div>
      </div>

      {hypothesisOutcome && (
        <div
          style={{
            padding: '12px 14px',
            borderRadius: '6px',
            marginBottom: '16px',
            background: hypothesisOutcome.status === 'CONFIRMED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${hypothesisOutcome.status === 'CONFIRMED' ? '#10b981' : '#ef4444'}`,
          }}
        >
          <div style={{ fontWeight: 700, fontSize: '12px', color: hypothesisOutcome.status === 'CONFIRMED' ? '#34d399' : '#f87171' }}>
            HYPOTHESIS {hypothesisOutcome.status}
          </div>
          <div style={{ fontSize: '11px', color: '#e2e8f0', marginTop: '4px' }}>
            {hypothesisOutcome.explanation}
          </div>
        </div>
      )}

      {result && result.experiment_report && (
        <div className="scientific-report-box">
          <div className="report-lead">Experimental Finding:</div>
          <div>{result.experiment_report.interpretation}</div>
        </div>
      )}
    </div>
  )
}
