import React, { useState } from 'react'
import type { LearnerHypothesis } from '../types'

interface LearnerHypothesisWidgetProps {
  memoryId: string
  onSaveHypothesis: (expType: string, text: string, outcome: string) => Promise<void>
  recentHypotheses: LearnerHypothesis[]
}

export const LearnerHypothesisWidget: React.FC<LearnerHypothesisWidgetProps> = ({
  memoryId,
  onSaveHypothesis,
  recentHypotheses,
}) => {
  const [expType, setExpType] = useState<string>('INTERFERENCE')
  const [text, setText] = useState<string>('I think intervening writes will degrade recall due to shared weights.')
  const [predictedOutcome, setPredictedOutcome] = useState<string>('RETENTION_DROP')
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    setIsSubmitting(true)
    try {
      await onSaveHypothesis(expType, text, predictedOutcome)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="ledger-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
          <span>🧪</span> LEARNER HYPOTHESIS & PREDICTION
        </h4>
        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
          Target: <strong style={{ color: '#38bdf8' }}>{memoryId}</strong> · Scientific inquiry mode
        </span>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <div>
            <label style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
              Experiment Context:
            </label>
            <select
              value={expType}
              onChange={(e) => setExpType(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 8px',
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#f8fafc',
                borderRadius: '4px',
                fontSize: '0.8rem',
                marginTop: '4px',
              }}
            >
              <option value="INTERFERENCE">Synaptic Interference (Collision)</option>
              <option value="SURGERY">Synaptic Surgery (Clamping)</option>
              <option value="COUNTERFACTUAL">Counterfactual (What-If)</option>
              <option value="DECAY">Passive Synaptic Decay</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
              Predicted Outcome:
            </label>
            <select
              value={predictedOutcome}
              onChange={(e) => setPredictedOutcome(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 8px',
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#38bdf8',
                borderRadius: '4px',
                fontSize: '0.8rem',
                fontWeight: 600,
                marginTop: '4px',
              }}
            >
              <option value="RETENTION_DROP">Retention Degradation (Recall Drop)</option>
              <option value="STABLE">Resilient Stability (Retention Maintained)</option>
              <option value="COMPLETE_LOSS">Catastrophic Forgetting</option>
              <option value="REPRESENTATION_SHIFT">Topological Fingerprint Mutation</option>
            </select>
          </div>
        </div>

        <div>
          <label style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
            Scientific Rationale / Hypothesis:
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={2}
            style={{
              width: '100%',
              padding: '8px',
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f8fafc',
              borderRadius: '4px',
              fontSize: '0.8rem',
              marginTop: '4px',
              resize: 'vertical',
            }}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: '8px 14px',
            background: 'linear-gradient(135deg, #0284c7, #0369a1)',
            border: 'none',
            borderRadius: '4px',
            color: '#fff',
            fontWeight: 700,
            fontSize: '0.8rem',
            cursor: 'pointer',
            alignSelf: 'flex-start',
          }}
        >
          {isSubmitting ? 'Evaluating Hypothesis...' : 'Register Hypothesis & Evaluate Against Model'}
        </button>
      </form>

      {recentHypotheses.length > 0 && (
        <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
            Empirically Tested Hypotheses:
          </span>
          {recentHypotheses.map((h) => (
            <div
              key={h.hypothesis_id}
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '6px',
                padding: '0.6rem 0.8rem',
                fontSize: '0.8rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: '#e2e8f0' }}>"{h.prediction_text}"</span>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: h.is_match ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    color: h.is_match ? '#10b981' : '#ef4444',
                    border: h.is_match ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)',
                  }}
                >
                  {h.is_match ? 'MATCH (CONFIRMED)' : 'DIFFERENCE'}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                {h.difference_explanation}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
