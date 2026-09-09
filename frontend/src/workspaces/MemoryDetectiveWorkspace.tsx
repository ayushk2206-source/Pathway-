import React, { useState, useEffect } from 'react'
import type {
  InvestigationCase,
  DetectiveScore,
  ScientificSource,
  LearningObjective,
} from '../types'
import {
  getDetectiveCases,
  getDetectiveCase,
  submitDetectiveVerdict,
  getForensicsSources,
  getForensicsObjectives,
} from '../api'
import { EvidenceBoard } from '../components/EvidenceBoard'
import { HypothesisBuilder } from '../components/HypothesisBuilder'
import { ExplanationBuilder } from '../components/ExplanationBuilder'

export const MemoryDetectiveWorkspace: React.FC = () => {
  const [cases, setCases] = useState<InvestigationCase[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-001')
  const [activeCase, setActiveCase] = useState<InvestigationCase | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Investigation session state
  const [collectedEvidenceIds, setCollectedEvidenceIds] = useState<string[]>([])
  const [selectedHypothesisId, setSelectedHypothesisId] = useState<string | null>(null)
  const [learnerConfidence, setLearnerConfidence] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('MEDIUM')
  const [testsRunCount, setTestsRunCount] = useState<number>(0)
  const [explanationChain, setExplanationChain] = useState<string[]>([
    'MEMORY_WRITE',
    'SYNAPTIC_UPDATE',
  ])

  // Verdict submission and score
  const [submittingVerdict, setSubmittingVerdict] = useState<boolean>(false)
  const [verdictScore, setVerdictScore] = useState<DetectiveScore | null>(null)
  const [revealedExplanation, setRevealedExplanation] = useState<string | null>(null)

  // Scientific Sources & Learning Objectives Modal / Section
  const [showSourcesModal, setShowSourcesModal] = useState<boolean>(false)
  const [sources, setSources] = useState<ScientificSource[]>([])
  const [objectives, setObjectives] = useState<LearningObjective[]>([])

  useEffect(() => {
    fetchInitialData()
  }, [])

  useEffect(() => {
    if (selectedCaseId) {
      loadCase(selectedCaseId)
    }
  }, [selectedCaseId])

  const fetchInitialData = async () => {
    setLoading(true)
    try {
      const [casesRes, sourcesRes, objRes] = await Promise.all([
        getDetectiveCases(true),
        getForensicsSources(),
        getForensicsObjectives(),
      ])
      setCases(casesRes.cases)
      setSources(sourcesRes.sources)
      setObjectives(objRes.objectives)
      if (casesRes.cases.length > 0) {
        setSelectedCaseId(casesRes.cases[0].case_id)
      }
    } catch (err) {
      console.error('Failed to load detective cases:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCase = async (caseId: string) => {
    try {
      const res = await getDetectiveCase(caseId, true)
      setActiveCase(res.case)
      // Reset investigation state for new case
      setCollectedEvidenceIds([])
      setSelectedHypothesisId(null)
      setTestsRunCount(0)
      setVerdictScore(null)
      setRevealedExplanation(null)
      setExplanationChain(['MEMORY_WRITE', 'SYNAPTIC_UPDATE'])
    } catch (err) {
      console.error(`Failed to load case ${caseId}:`, err)
    }
  }

  const handleToggleCollect = (evidenceId: string) => {
    setCollectedEvidenceIds((prev) =>
      prev.includes(evidenceId) ? prev.filter((id) => id !== evidenceId) : [...prev, evidenceId],
    )
  }

  const handleSubmitVerdict = async () => {
    if (!activeCase || !selectedHypothesisId) return
    setSubmittingVerdict(true)
    try {
      const res = await submitDetectiveVerdict(activeCase.case_id, {
        chosen_hypothesis_id: selectedHypothesisId,
        collected_evidence_ids: collectedEvidenceIds,
        tests_run_count: testsRunCount,
        learner_confidence: learnerConfidence,
        explanation_chain: explanationChain,
      })
      setVerdictScore(res.score)
      setRevealedExplanation(res.ground_truth_explanation)
    } catch (err) {
      console.error('Failed to submit verdict:', err)
    } finally {
      setSubmittingVerdict(false)
    }
  }

  if (loading || !activeCase) {
    return (
      <div className="forensics-workspace" style={{ textAlign: 'center', padding: '4rem' }}>
        <h2 style={{ color: '#38bdf8' }}>Loading Investigation Archive...</h2>
        <p style={{ color: '#94a3b8' }}>Synthesizing linear algebra matrices and historical mystery logs</p>
      </div>
    )
  }

  return (
    <div className="forensics-workspace">
      {/* Header */}
      <div className="forensics-header">
        <div className="forensics-title-group">
          <h1>
            <span>◎</span> Memory Detective: Forensic Laboratory
          </h1>
          <p className="forensics-subtitle">
            Blind Scientific Investigation — Uncover the Exact Synaptic Mechanisms Behind Memory Fate
          </p>
        </div>
        <div className="forensics-header-actions">
          <button
            className="forensics-tab-pill"
            onClick={() => setShowSourcesModal(true)}
          >
            📚 Scientific Sources & Objectives ({sources.length})
          </button>
        </div>
      </div>

      {/* Case Selector Carousel */}
      <div className="case-selector-strip">
        {cases.map((c) => {
          const isSelected = c.case_id === selectedCaseId
          return (
            <div
              key={c.case_id}
              className={`case-card-btn ${isSelected ? 'selected' : ''}`}
              onClick={() => setSelectedCaseId(c.case_id)}
            >
              <div className="case-badge-row">
                <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8' }}>
                  {c.case_id}
                </span>
                <span className={`case-badge-difficulty ${c.difficulty.toLowerCase()}`}>
                  {c.difficulty}
                </span>
              </div>
              <div className="case-card-title">{c.title}</div>
              <div className="case-card-stat">
                Target: <strong style={{ color: '#38bdf8' }}>'{c.target_memory}'</strong> | Steps: {c.total_timesteps}
              </div>
            </div>
          )
        })}
      </div>

      {/* Case Briefing & Mystery Alert */}
      <div className="case-briefing-panel">
        <div className="panel-title-bar">
          <h3>
            <span>📋</span> Active Case Briefing: {activeCase.title}
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#fbbf24', fontWeight: 600 }}>
            🔒 BLIND MODE ACTIVE (Ground truth hidden)
          </span>
        </div>

        <div className="briefing-alert">
          <div className="briefing-question">Mystery Question: {activeCase.question}</div>
          <div className="briefing-text">{activeCase.briefing}</div>
        </div>

        <div className="briefing-metrics-row">
          <div className="metric-pill">
            <span className="metric-pill-label">Target Memory</span>
            <span className="metric-pill-val" style={{ color: '#38bdf8' }}>{activeCase.target_memory}</span>
          </div>
          <div className="metric-pill">
            <span className="metric-pill-label">Initial Recall Fidelity</span>
            <span className="metric-pill-val">{activeCase.initial_recall.toFixed(3)}</span>
          </div>
          <div className="metric-pill">
            <span className="metric-pill-label">Observed Final Recall</span>
            <span className="metric-pill-val" style={{ color: activeCase.final_recall < activeCase.initial_recall ? '#f87171' : '#34d399' }}>
              {activeCase.final_recall.toFixed(3)}
            </span>
          </div>
          <div className="metric-pill">
            <span className="metric-pill-label">Total Timesteps</span>
            <span className="metric-pill-val">{activeCase.total_timesteps}</span>
          </div>
          <div className="metric-pill">
            <span className="metric-pill-label">Investigation Tools</span>
            <span className="metric-pill-val" style={{ fontSize: '0.9rem', color: '#94a3b8' }}>
              {activeCase.available_tools.join(', ')}
            </span>
          </div>
        </div>
      </div>

      {/* Main Two-Column Detective Layout */}
      <div className="detective-main-grid">
        {/* Left Column: Evidence Board & Explanation Builder */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <EvidenceBoard
            evidence={activeCase.available_evidence}
            collectedIds={collectedEvidenceIds}
            onToggleCollect={handleToggleCollect}
          />
          <ExplanationBuilder
            chain={explanationChain}
            onChangeChain={setExplanationChain}
          />
        </div>

        {/* Right Column: Hypothesis Formulation, Empirical Testing & Verdict Submission */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <HypothesisBuilder
            caseId={activeCase.case_id}
            hypotheses={activeCase.candidate_hypotheses}
            selectedHypothesisId={selectedHypothesisId}
            onSelectHypothesis={setSelectedHypothesisId}
            onTestExecuted={() => setTestsRunCount((c) => c + 1)}
          />

          {/* Verdict Action Card */}
          <div className="verdict-action-box">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#f8fafc' }}>
                ⚖️ Final Scientific Verdict Submission
              </span>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                Tests Run: <strong style={{ color: '#38bdf8' }}>{testsRunCount}</strong>
              </span>
            </div>

            <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
              Declare your confidence in the primary causal hypothesis before submitting:
            </div>

            <div className="confidence-selector-row">
              {(['LOW', 'MEDIUM', 'HIGH'] as const).map((conf) => (
                <button
                  key={conf}
                  className={`confidence-pill ${learnerConfidence === conf ? 'selected' : ''}`}
                  onClick={() => setLearnerConfidence(conf)}
                >
                  {conf} CONFIDENCE
                </button>
              ))}
            </div>

            <button
              className="submit-verdict-btn"
              onClick={handleSubmitVerdict}
              disabled={!selectedHypothesisId || submittingVerdict}
            >
              {submittingVerdict ? 'Grading Investigation...' : 'Submit Formal Verdict & Unseal Case'}
            </button>
          </div>

          {/* Detective Scorecard Banner */}
          {verdictScore && (
            <div className="scorecard-banner">
              <div className="scorecard-header">
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase' }}>
                    Detective Evaluation Score
                  </span>
                  <div className="score-badge">{verdictScore.score}/100</div>
                </div>
                <div className={`rating-pill ${verdictScore.rating.toLowerCase()}`}>
                  {verdictScore.rating.replace('_', ' ')}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', fontSize: '0.82rem', color: '#cbd5e1' }}>
                <span>Hypothesis: <strong>{verdictScore.hypothesis_correct ? 'CORRECT (+40)' : 'INCORRECT (+10)'}</strong></span>
                <span>Evidence Coverage: <strong>{verdictScore.evidence_score}/40</strong></span>
                <span>Economy: <strong>{verdictScore.economy_score}/20</strong></span>
              </div>

              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  fontSize: '0.88rem',
                  color: '#e2e8f0',
                  lineHeight: 1.45,
                }}
              >
                {verdictScore.feedback}
              </div>

              {revealedExplanation && (
                <div
                  style={{
                    background: 'rgba(56, 189, 248, 0.1)',
                    borderLeft: '4px solid #38bdf8',
                    padding: '0.75rem 1rem',
                    borderRadius: '0 6px 6px 0',
                    fontSize: '0.85rem',
                    color: '#bae6fd',
                    lineHeight: 1.45,
                  }}
                >
                  <strong>Unsealed Ground Truth Mechanism:</strong> {revealedExplanation}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Sources & Objectives Modal */}
      {showSourcesModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem',
          }}
        >
          <div
            style={{
              background: '#0f172a',
              border: '1px solid #38bdf8',
              borderRadius: '12px',
              maxWidth: '900px',
              width: '100%',
              maxHeight: '85vh',
              overflowY: 'auto',
              padding: '2rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ margin: 0, color: '#38bdf8', fontSize: '1.4rem' }}>
                📚 Primary Scientific Literature & Core Learning Objectives
              </h2>
              <button
                onClick={() => setShowSourcesModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Verified Sources */}
            <div>
              <h3 style={{ color: '#f8fafc', fontSize: '1.1rem', marginBottom: '0.75rem' }}>
                Peer-Reviewed Primary Sources (2022–2026)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {sources.map((s) => (
                  <div key={s.id} className="sources-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong style={{ color: '#f1f5f9' }}>{s.title}</strong>
                      <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{s.journal} ({s.year})</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>{s.authors}</div>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                      <em>Key Finding:</em> {s.key_finding}
                    </div>
                    <a
                      href={`https://doi.org/${s.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="source-doi-link"
                    >
                      DOI: {s.doi} ↗
                    </a>
                  </div>
                ))}
              </div>
            </div>

            {/* Core Learning Objectives */}
            <div>
              <h3 style={{ color: '#f8fafc', fontSize: '1.1rem', marginBottom: '0.75rem' }}>
                Core Scientific Learning Objectives
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {objectives.map((obj) => (
                  <div
                    key={obj.id}
                    style={{
                      background: 'rgba(30, 41, 59, 0.5)',
                      padding: '0.75rem 1rem',
                      borderRadius: '6px',
                      border: '1px solid rgba(148, 163, 184, 0.15)',
                    }}
                  >
                    <div style={{ fontWeight: 600, color: '#38bdf8', fontSize: '0.9rem' }}>
                      {obj.title}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#e2e8f0', marginTop: '0.2rem' }}>
                      <strong>Principle:</strong> {obj.principle}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                      <em>Computational Rule:</em> {obj.scientific_rule}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
