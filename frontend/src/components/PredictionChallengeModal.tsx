import React from 'react'

interface PredictionChallengeModalProps {
  isOpen: boolean
  questionText: string
  selectedChoice: string | null
  onSelectChoice: (choice: string) => void
  onConfirmRun: () => void
  onClose: () => void
}

const CHOICES = [
  { id: 'A', label: 'A. Recall Improves', desc: 'The intervention enhances or reinforces active synaptic connections.' },
  { id: 'B', label: 'B. Recall Decreases', desc: 'Interference or decay disrupts the weight matrix, introducing noise.' },
  { id: 'C', label: 'C. Recall Remains Stable', desc: 'The target subspace is largely orthogonal to the intervention.' },
  { id: 'D', label: 'D. Unsure / Formulating Inquiry', desc: 'Awaiting empirical observation without pre-commitment.' },
]

export const PredictionChallengeModal: React.FC<PredictionChallengeModalProps> = ({
  isOpen,
  questionText,
  selectedChoice,
  onSelectChoice,
  onConfirmRun,
  onClose,
}) => {
  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(3, 7, 18, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem',
    }}>
      <div className="studio-challenge-card" style={{ maxWidth: '520px', width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>🧪</span> PRE-EXPERIMENT PREDICTION CHALLENGE
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1rem', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        <p style={{ margin: 0, fontSize: '0.85rem', color: '#f8fafc', lineHeight: 1.45, fontWeight: 600 }}>
          {questionText || 'What do you predict will happen to Memory A under this experimental condition?'}
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.25rem' }}>
          {CHOICES.map((c) => (
            <button
              key={c.id}
              className={`studio-choice-btn ${selectedChoice === c.id ? 'selected' : ''}`}
              onClick={() => onSelectChoice(c.id)}
            >
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontWeight: 700 }}>{c.label}</span>
                <span style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '2px' }}>{c.desc}</span>
              </div>
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
          <button
            onClick={onClose}
            style={{ padding: '6px 14px', background: 'transparent', border: '1px solid rgba(255, 255, 255, 0.15)', borderRadius: '6px', color: '#94a3b8', fontSize: '0.8rem', cursor: 'pointer' }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirmRun}
            disabled={!selectedChoice}
            style={{
              padding: '6px 16px',
              background: selectedChoice ? 'linear-gradient(135deg, #f59e0b, #d97706)' : 'rgba(245, 158, 11, 0.2)',
              border: 'none',
              borderRadius: '6px',
              color: '#030712',
              fontWeight: 800,
              fontSize: '0.8rem',
              cursor: selectedChoice ? 'pointer' : 'not-allowed',
            }}
          >
            LOCK PREDICTION & RUN EXPERIMENT ▶
          </button>
        </div>
      </div>
    </div>
  )
}
