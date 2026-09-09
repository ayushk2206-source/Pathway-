import React, { useState } from 'react'
import type { StudioExperimentNote } from '../types'

interface ExperimentNotesWidgetProps {
  experimentId: string
  notes: StudioExperimentNote
  onSaveNotes: (updatedNotes: StudioExperimentNote) => Promise<void>
}

export const ExperimentNotesWidget: React.FC<ExperimentNotesWidgetProps> = ({
  experimentId,
  notes,
  onSaveNotes,
}) => {
  const [question, setQuestion] = useState(notes.question || '')
  const [hypothesis, setHypothesis] = useState(notes.hypothesis || '')
  const [observation, setObservation] = useState(notes.observation || '')
  const [conclusion, setConclusion] = useState(notes.conclusion || '')
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<string | null>(null)

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      await onSaveNotes({ question, hypothesis, observation, conclusion })
      setSaveStatus('Notes saved to session.')
      setTimeout(() => setSaveStatus(null), 2500)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.75)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '8px',
      padding: '1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '0.82rem', fontWeight: 800, color: '#f8fafc' }}>
          📝 EXPERIMENTAL LAB NOTES ({experimentId})
        </h4>
        {saveStatus && (
          <span style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 700 }}>
            ✓ {saveStatus}
          </span>
        )}
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div>
          <label style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
            Scientific Question
          </label>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Can temporary synaptic changes preserve a memory?"
            style={{ width: '100%', background: '#090d16', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', boxSizing: 'border-box' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
            Hypothesis
          </label>
          <input
            type="text"
            value={hypothesis}
            onChange={(e) => setHypothesis(e.target.value)}
            placeholder="e.g. Stronger interference degrades recall."
            style={{ width: '100%', background: '#090d16', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', boxSizing: 'border-box' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
            Empirical Observation
          </label>
          <input
            type="text"
            value={observation}
            onChange={(e) => setObservation(e.target.value)}
            placeholder="e.g. Recall dropped by 0.18."
            style={{ width: '100%', background: '#090d16', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', boxSizing: 'border-box' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
            Conclusion
          </label>
          <input
            type="text"
            value={conclusion}
            onChange={(e) => setConclusion(e.target.value)}
            placeholder="e.g. Superposition limits induce crosstalk."
            style={{ width: '100%', background: '#090d16', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', boxSizing: 'border-box' }}
          />
        </div>

        <button
          type="submit"
          disabled={isSaving}
          style={{
            alignSelf: 'flex-end',
            padding: '4px 12px',
            background: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid #38bdf8',
            borderRadius: '5px',
            color: '#38bdf8',
            fontSize: '0.74rem',
            fontWeight: 700,
            cursor: 'pointer',
            marginTop: '2px',
          }}
        >
          {isSaving ? 'Saving...' : 'Save Notes'}
        </button>
      </form>
    </div>
  )
}
