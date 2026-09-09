import React, { useState } from 'react'
import type { StudioGuidedJourney } from '../types'

interface GuidedJourneyModalProps {
  isOpen: boolean
  journey: StudioGuidedJourney
  onClose: () => void
  onApplyStepConfig: (stepIndex: number) => void
}

export const GuidedJourneyModal: React.FC<GuidedJourneyModalProps> = ({
  isOpen,
  journey,
  onClose,
  onApplyStepConfig,
}) => {
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(0)

  if (!isOpen || !journey) return null

  const step = journey.steps[currentStepIdx]

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(3, 7, 18, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1100,
      padding: '1rem',
    }}>
      <div style={{
        background: '#0b1329',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        borderRadius: '10px',
        maxWidth: '580px',
        width: '100%',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Guided Scientific Journey
            </span>
            <h3 style={{ margin: '2px 0 0 0', fontSize: '1rem', fontWeight: 800, color: '#f8fafc' }}>
              {journey.title}
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1rem', cursor: 'pointer' }}>
            ✕
          </button>
        </div>

        {/* Step Progress Bar */}
        <div style={{ display: 'flex', gap: '4px' }}>
          {journey.steps.map((s, idx) => (
            <div
              key={s.step_index}
              onClick={() => setCurrentStepIdx(idx)}
              style={{
                flex: 1,
                height: '4px',
                borderRadius: '2px',
                background: idx === currentStepIdx ? '#38bdf8' : idx < currentStepIdx ? 'rgba(56, 189, 248, 0.4)' : 'rgba(255, 255, 255, 0.1)',
                cursor: 'pointer',
              }}
            />
          ))}
        </div>

        {/* Active Step Content */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#38bdf8' }}>
              STEP {step.step_index} OF {journey.total_steps}: {step.action}
            </span>
          </div>

          <p style={{ margin: 0, fontSize: '0.85rem', color: '#f8fafc', lineHeight: 1.45 }}>
            {step.instruction}
          </p>

          <div style={{
            fontSize: '0.74rem',
            color: '#cbd5e1',
            background: 'rgba(30, 41, 59, 0.5)',
            padding: '0.5rem 0.75rem',
            borderRadius: '6px',
            borderLeft: '3px solid #f59e0b',
          }}>
            <strong>Scientific Focus:</strong> {step.focus}
          </div>
        </div>

        {/* Footer Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
          <button
            onClick={() => setCurrentStepIdx((p) => Math.max(0, p - 1))}
            disabled={currentStepIdx === 0}
            style={{
              padding: '6px 14px',
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '6px',
              color: currentStepIdx === 0 ? '#475569' : '#cbd5e1',
              fontSize: '0.78rem',
              cursor: currentStepIdx === 0 ? 'not-allowed' : 'pointer',
            }}
          >
            ← Previous Step
          </button>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => {
                onApplyStepConfig(step.step_index)
                onClose()
              }}
              style={{
                padding: '6px 14px',
                background: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid #38bdf8',
                borderRadius: '6px',
                color: '#38bdf8',
                fontWeight: 700,
                fontSize: '0.78rem',
                cursor: 'pointer',
              }}
            >
              Apply Step to Studio
            </button>

            {currentStepIdx < journey.total_steps - 1 ? (
              <button
                onClick={() => setCurrentStepIdx((p) => Math.min(journey.total_steps - 1, p + 1))}
                style={{
                  padding: '6px 16px',
                  background: '#38bdf8',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#030712',
                  fontWeight: 800,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                }}
              >
                Next Step →
              </button>
            ) : (
              <button
                onClick={onClose}
                style={{
                  padding: '6px 16px',
                  background: '#10b981',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#030712',
                  fontWeight: 800,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                }}
              >
                Finish Journey ✓
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
