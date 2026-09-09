import React, { useState } from 'react'
import type { FingerprintChallenge } from '../types'
import { verifyFingerprintChallenge } from '../api'

interface FingerprintChallengePanelProps {
  challenges: FingerprintChallenge[]
}

export const FingerprintChallengePanel: React.FC<FingerprintChallengePanelProps> = ({
  challenges,
}) => {
  const [activeIdx, setActiveIdx] = useState<number>(0)
  const [selectedOpt, setSelectedOpt] = useState<string>('')
  const [result, setResult] = useState<{ is_correct: boolean; explanation: string } | null>(null)

  if (!challenges || challenges.length === 0) return null

  const currentCh = challenges[activeIdx]

  const handleVerify = async () => {
    if (!selectedOpt) return
    try {
      const res = await verifyFingerprintChallenge({
        challenge_id: currentCh.challenge_id,
        selected_option: selectedOpt,
      })
      setResult({ is_correct: res.is_correct, explanation: res.explanation })
    } catch (err) {
      console.error('Failed to verify challenge:', err)
    }
  }

  return (
    <div className="challenge-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#c084fc', textTransform: 'uppercase' }}>
          🧠 Learning Challenge: Predict ➔ Run ➔ Observe
        </span>
        <div style={{ display: 'flex', gap: '0.3rem' }}>
          {challenges.map((c, i) => (
            <button
              key={c.challenge_id}
              className={`concept-chip ${activeIdx === i ? 'active' : ''}`}
              style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
              onClick={() => {
                setActiveIdx(i)
                setSelectedOpt('')
                setResult(null)
              }}
            >
              #{i + 1}
            </button>
          ))}
        </div>
      </div>

      <div style={{ fontSize: '0.85rem', color: '#f8fafc', fontWeight: 600 }}>
        {currentCh.prompt}
      </div>

      <div className="challenge-options-row">
        {currentCh.options.map((opt) => (
          <button
            key={opt}
            className={`challenge-opt-btn ${selectedOpt === opt ? 'active' : ''}`}
            onClick={() => setSelectedOpt(opt)}
          >
            {opt}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.25rem' }}>
        <button
          className="scanner-btn primary"
          onClick={handleVerify}
          disabled={!selectedOpt}
        >
          Check Prediction
        </button>

        {result && (
          <span style={{
            fontSize: '0.8rem',
            fontWeight: 600,
            color: result.is_correct ? '#34d399' : '#f87171',
          }}>
            {result.is_correct ? '✓ Correct Hypothesis! ' : '✗ Divergence Observed. '}
            {result.explanation}
          </span>
        )}
      </div>
    </div>
  )
}
