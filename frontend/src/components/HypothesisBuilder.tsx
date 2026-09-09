import React, { useState } from 'react'
import type { ForensicsCandidateHypothesis, HypothesisTestResult } from '../types'
import { testDetectiveHypothesis } from '../api'

interface HypothesisBuilderProps {
  caseId: string
  hypotheses: ForensicsCandidateHypothesis[]
  selectedHypothesisId: string | null
  onSelectHypothesis: (id: string) => void
  onTestExecuted: () => void
}

export const HypothesisBuilder: React.FC<HypothesisBuilderProps> = ({
  caseId,
  hypotheses,
  selectedHypothesisId,
  onSelectHypothesis,
  onTestExecuted,
}) => {
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<HypothesisTestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const activeHypothesis = hypotheses.find((h) => h.hypothesis_id === selectedHypothesisId)

  const handleRunTest = async (toolOverride?: string) => {
    if (!activeHypothesis) return
    setTesting(true)
    setError(null)
    try {
      const toolToUse = toolOverride || activeHypothesis.recommended_tool
      const result = await testDetectiveHypothesis(caseId, activeHypothesis.hypothesis_id, toolToUse)
      setTestResult(result)
      onTestExecuted()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hypothesis testing failed')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="hypothesis-panel">
      <div className="panel-title-bar">
        <h3>
          <span>💡</span> Hypothesis Formulation & Empirical Testing
        </h3>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Select candidate cause and test against lab tools
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {hypotheses.map((hyp) => {
          const isSelected = hyp.hypothesis_id === selectedHypothesisId
          return (
            <div
              key={hyp.hypothesis_id}
              className={`hypothesis-item-card ${isSelected ? 'selected' : ''}`}
              onClick={() => {
                onSelectHypothesis(hyp.hypothesis_id)
                setTestResult(null)
              }}
            >
              <div className="hyp-header-row">
                <span className="hyp-label">{hyp.label}</span>
                <span className="hyp-tool-tag">Recommended: {hyp.recommended_tool.toUpperCase()}</span>
              </div>
              <div className="hyp-desc">{hyp.description}</div>
            </div>
          )
        })}
      </div>

      {activeHypothesis && (
        <div className="tool-testing-console">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
              Test Hypothesis: <strong style={{ color: '#38bdf8' }}>{activeHypothesis.label}</strong>
            </span>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Tool: {activeHypothesis.recommended_tool}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              className="test-tool-btn"
              onClick={() => handleRunTest()}
              disabled={testing}
            >
              {testing ? 'Probing Network...' : `🔬 Execute ${activeHypothesis.recommended_tool.toUpperCase()} Test`}
            </button>
            <button
              style={{
                background: 'rgba(51, 65, 85, 0.4)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                color: '#cbd5e1',
                borderRadius: '6px',
                padding: '0.4rem 0.8rem',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
              onClick={() => handleRunTest('xray')}
              disabled={testing}
            >
              Run X-Ray Probe
            </button>
            <button
              style={{
                background: 'rgba(51, 65, 85, 0.4)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                color: '#cbd5e1',
                borderRadius: '6px',
                padding: '0.4rem 0.8rem',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
              onClick={() => handleRunTest('timemachine')}
              disabled={testing}
            >
              Run Time Machine Probe
            </button>
          </div>

          {error && (
            <div style={{ color: '#f87171', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.1)', padding: '0.5rem', borderRadius: '4px' }}>
              {error}
            </div>
          )}

          {testResult && (
            <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Empirical Test Result:</span>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.2rem 0.6rem',
                    borderRadius: '4px',
                    background:
                      testResult.consistency_verdict === 'CONSISTENT'
                        ? 'rgba(16, 185, 129, 0.2)'
                        : testResult.consistency_verdict === 'CONTRADICTED'
                        ? 'rgba(239, 68, 68, 0.2)'
                        : 'rgba(245, 158, 11, 0.2)',
                    color:
                      testResult.consistency_verdict === 'CONSISTENT'
                        ? '#34d399'
                        : testResult.consistency_verdict === 'CONTRADICTED'
                        ? '#f87171'
                        : '#fbbf24',
                    border: '1px solid',
                    borderColor:
                      testResult.consistency_verdict === 'CONSISTENT'
                        ? '#10b981'
                        : testResult.consistency_verdict === 'CONTRADICTED'
                        ? '#ef4444'
                        : '#f59e0b',
                  }}
                >
                  {testResult.consistency_verdict}
                </span>
              </div>
              <div
                style={{
                  fontSize: '0.85rem',
                  lineHeight: 1.45,
                  color: '#e2e8f0',
                  background: 'rgba(15, 23, 42, 0.9)',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  border: '1px solid rgba(148, 163, 184, 0.15)',
                }}
              >
                {testResult.scientific_readout}
              </div>
              <div className="evidence-data-snippet">
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(testResult.measured_evidence, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
