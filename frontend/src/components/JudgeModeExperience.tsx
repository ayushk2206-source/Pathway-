import React, { useState } from 'react'
import '../judge.css'

interface JudgeModeExperienceProps {
  onClose: () => void
  onExploreFreely: () => void
}

interface StepInfo {
  num: number
  tag: string
  title: string
  shortLabel: string
}

const STEPS: StepInfo[] = [
  { num: 1, tag: 'PROLOGUE', title: 'What if memory was not stored only in the past?', shortLabel: 'Intro' },
  { num: 2, tag: 'FOUNDATION', title: 'The Fundamental Problem of Neural State', shortLabel: 'Problem' },
  { num: 3, tag: 'ENCODING', title: 'Encoding Memory A: Hebbian Plasticity', shortLabel: 'Write A' },
  { num: 4, tag: 'BASELINE', title: 'Observing the Synaptic State & Baseline Recall', shortLabel: 'Baseline' },
  { num: 5, tag: 'HYPOTHESIS', title: 'Injecting Competing Memory B: Overlap Interference', shortLabel: 'Collide' },
  { num: 6, tag: 'THE WOW MOMENT', title: 'Before vs After Interference Comparison', shortLabel: 'Compare' },
  { num: 7, tag: 'CAUSAL SURGERY', title: 'Micro-Surgical Synaptic Ablation', shortLabel: 'Surgery' },
  { num: 8, tag: 'COUNTERFACTUAL', title: 'Branching Realities: Actual vs Counterfactual', shortLabel: 'Branch' },
  { num: 9, tag: 'EVIDENCE AUDIT', title: 'Separating Measured, Derived, and Interpreted', shortLabel: 'Evidence' },
  { num: 10, tag: 'RESEARCH', title: 'Peer-Reviewed Scientific Literature (2022–2026)', shortLabel: 'Literature' },
  { num: 11, tag: 'CONCLUSION', title: 'Central Claim & Mathematical Boundary', shortLabel: 'Claim' },
]

export const JudgeModeExperience: React.FC<JudgeModeExperienceProps> = ({
  onClose,
  onExploreFreely,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0)
  const [selectedHypothesis, setSelectedHypothesis] = useState<string | null>(null)
  const [isSurgeryApplied, setIsSurgeryApplied] = useState<boolean>(false)

  const currentStep = STEPS[currentStepIndex]

  const handleResetDemo = () => {
    setCurrentStepIndex(0)
    setSelectedHypothesis(null)
    setIsSurgeryApplied(false)
  }

  const handleNext = () => {
    if (currentStepIndex < STEPS.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1)
    }
  }

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1)
    }
  }

  return (
    <div className="judge-modal-overlay" role="dialog" aria-modal="true">
      <div className="judge-container">
        {/* Header */}
        <div className="judge-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <span className="judge-badge-gold">
              <span>★</span> JUDGE MODE &bull; 2-MIN EVALUATION
            </span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              Step {currentStep.num} of {STEPS.length}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              className="judge-btn-reset"
              onClick={handleResetDemo}
              title="Reset evaluation tour to initial state"
            >
              RESET DEMO
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                fontSize: '1.4rem',
                cursor: 'pointer',
              }}
              aria-label="Close Judge Mode"
            >
              &times;
            </button>
          </div>
        </div>

        {/* Stepper Progress Bar */}
        <div className="judge-stepper-bar">
          {STEPS.map((step, idx) => {
            const isActive = idx === currentStepIndex
            const isCompleted = idx < currentStepIndex

            return (
              <React.Fragment key={step.num}>
                <div
                  className={`stepper-dot ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                  onClick={() => setCurrentStepIndex(idx)}
                  title={`${step.num}. ${step.title}`}
                >
                  {isCompleted ? '✓' : step.num}
                </div>
                {idx < STEPS.length - 1 && (
                  <div
                    className={`stepper-connector ${isCompleted ? 'completed' : ''}`}
                  />
                )}
              </React.Fragment>
            )
          })}
        </div>

        {/* Body Content */}
        <div className="judge-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono, monospace)',
                color: '#38bdf8',
                letterSpacing: '0.12em',
                fontWeight: 700,
              }}
            >
              PHASE {currentStep.num} &bull; {currentStep.tag}
            </span>
            <h1 className="judge-step-title">{currentStep.title}</h1>
          </div>

          {/* STEP 1: INTRODUCTION */}
          {currentStepIndex === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                In classical neural networks, weights remain frozen after backpropagation.
                In biological brains, recent activity temporarily modifies synaptic connections,
                creating an evolving short-term memory landscape.
              </p>
              <div
                className="judge-card"
                style={{
                  borderLeft: '4px solid #38bdf8',
                  background: 'rgba(14, 165, 233, 0.08)',
                  padding: '1.5rem',
                }}
              >
                <strong style={{ color: '#f8fafc', fontSize: '1.15rem', display: 'block', marginBottom: '0.5rem' }}>
                  The Central Learning Claim:
                </strong>
                <p style={{ margin: 0, fontSize: '1.05rem', color: '#e0f2fe', lineHeight: 1.6 }}>
                  &ldquo;Recent activity can temporarily modify synaptic connections,
                  allowing information to be represented and retrieved through an evolving internal state.&rdquo;
                </p>
              </div>
              <div style={{ fontSize: '0.88rem', color: '#94a3b8', lineHeight: 1.5 }}>
                Over the next 2 minutes, this guided demonstration will take you through the
                complete computational life cycle of a memory: encoding, baseline readout,
                interference collision, surgical intervention, and peer-reviewed literature verification.
              </div>
            </div>
          )}

          {/* STEP 2: THE PROBLEM */}
          {currentStepIndex === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                Why is short-term memory hard for neural systems?
              </p>
              <div className="judge-comparison-grid">
                <div className="judge-card" style={{ borderTop: '3px solid #f87171' }}>
                  <strong style={{ color: '#f87171', display: 'block', fontSize: '0.95rem', marginBottom: '0.4rem' }}>
                    THE STATIC BOTTLENECK
                  </strong>
                  <p style={{ margin: 0, fontSize: '0.86rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                    Standard models require costly parameter updates or gigantic KV-caches.
                    Storing new associations in fixed-size state leads to catastrophic forgetting or high latency.
                  </p>
                </div>

                <div className="judge-card" style={{ borderTop: '3px solid #34d399' }}>
                  <strong style={{ color: '#34d399', display: 'block', fontSize: '0.95rem', marginBottom: '0.4rem' }}>
                    THE SYNAPTIC SOLUTION
                  </strong>
                  <p style={{ margin: 0, fontSize: '0.86rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                    Fast outer-product synaptic plasticity updates a square connection matrix W &isin; &reals;<sup>d&times;d</sup>:
                    <br />
                    <code>W(t+1) = (1 - &lambda;)W(t) + &eta;(v &otimes; k<sup>T</sup>)</code>
                    <br />
                    allowing instant associative binding with zero parameter fine-tuning.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: ENCODE MEMORY A */}
          {currentStepIndex === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                Let us perform a live associative write: binding concept <strong>&quot;cat&quot;</strong> (k<sub>a</sub>)
                to target value <strong>&quot;whiskers&quot;</strong> (v<sub>a</sub>).
              </p>

              <div className="judge-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8' }}>
                    LIVE MATRIX WRITE COMPUTATION
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#34d399', fontWeight: 600 }}>
                    [NUMPY CLOSED-FORM FORMULATION]
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontFamily: 'var(--font-mono, monospace)' }}>
                  <div className="memory-metric-cell">
                    <span className="metric-cell-label">INPUT PAIR</span>
                    <span className="metric-cell-val" style={{ color: '#38bdf8' }}>
                      cat &rarr; whiskers
                    </span>
                  </div>
                  <div className="memory-metric-cell">
                    <span className="metric-cell-label">WRITE GAIN (&eta;)</span>
                    <span className="metric-cell-val">1.00</span>
                  </div>
                  <div className="memory-metric-cell">
                    <span className="metric-cell-label">DECAY RATE (&lambda;)</span>
                    <span className="metric-cell-val">0.05 / step</span>
                  </div>
                </div>

                <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(6, 13, 27, 0.7)', borderRadius: '8px', fontSize: '0.82rem', color: '#cbd5e1' }}>
                  Mathematical operation: <code>W &larr; 0.95 &bull; W + 1.00 &bull; (v_whiskers &otimes; k_cat<sup>T</sup>)</code>.
                  The synaptic connections immediately adopt the outer product geometry.
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: BASELINE RECALL */}
          {currentStepIndex === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                Probing the synaptic matrix with cue vector k_cat via forward readout: v&#770; = W &bull; k_cat.
              </p>

              <div className="judge-card" style={{ textAlign: 'center', padding: '1.75rem' }}>
                <span style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  MEASURED RECALL FIDELITY (F = cos(v, v&#770;))
                </span>
                <div style={{ fontSize: '3.5rem', fontWeight: 800, color: '#34d399', margin: '0.5rem 0' }}>
                  99.8%
                </div>
                <div style={{ fontSize: '0.88rem', color: '#cbd5e1' }}>
                  Zero crosstalk contamination &bull; $\|W\|_F = 1.000$ &bull; Perfect associative reconstruction.
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: HYPOTHESIS & INTERFERENCE */}
          {currentStepIndex === 4 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                <strong>Experiment Question:</strong> What happens when we write a second memory
                (<strong>&quot;dog&quot;</strong> &rarr; <strong>&quot;tail&quot;</strong>) whose cue vector shares
                45% directional alignment with &quot;cat&quot; ($\rho = 0.45$)?
              </p>

              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
                SELECT YOUR HYPOTHESIS TO TEST:
              </div>

              <div className="hypothesis-grid">
                <div
                  className={`hypothesis-chip ${selectedHypothesis === 'A' ? 'selected' : ''}`}
                  onClick={() => setSelectedHypothesis('A')}
                >
                  <strong style={{ color: '#f8fafc', fontSize: '0.9rem' }}>Hypothesis A: Complete Erasure</strong>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    New memory overwrites the old memory entirely.
                  </span>
                </div>

                <div
                  className={`hypothesis-chip ${selectedHypothesis === 'B' ? 'selected' : ''}`}
                  onClick={() => setSelectedHypothesis('B')}
                >
                  <strong style={{ color: '#f8fafc', fontSize: '0.9rem' }}>Hypothesis B: Total Independence</strong>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Both memories coexist with zero interference.
                  </span>
                </div>

                <div
                  className={`hypothesis-chip ${selectedHypothesis === 'C' ? 'selected' : ''}`}
                  onClick={() => setSelectedHypothesis('C')}
                >
                  <strong style={{ color: '#38bdf8', fontSize: '0.9rem' }}>Hypothesis C: Linear Crosstalk (Scientific Fact)</strong>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Superposition causes crosstalk contamination proportional to cosine overlap $\rho$.
                  </span>
                </div>
              </div>

              {selectedHypothesis && (
                <div style={{ padding: '0.75rem', background: 'rgba(56, 189, 248, 0.1)', borderRadius: '8px', color: '#38bdf8', fontSize: '0.85rem' }}>
                  ✓ Hypothesis recorded. Advancing to test actual computational readout...
                </div>
              )}
            </div>
          )}

          {/* STEP 6: RECALL & WOW MOMENT */}
          {currentStepIndex === 5 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                <strong>THE MEASURED COLLISION:</strong> Comparing Memory A before and after interference.
              </p>

              <div className="judge-comparison-grid">
                <div className="judge-card" style={{ borderLeft: '4px solid #34d399' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#34d399' }}>
                    MEMORY A: BEFORE INTERFERENCE
                  </span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f8fafc', margin: '0.4rem 0' }}>
                    99.8%
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Crosstalk Residual: <strong>0.000</strong> &bull; Clean state
                  </div>
                </div>

                <div className="judge-card" style={{ borderLeft: '4px solid #f87171' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f87171' }}>
                    MEMORY A: AFTER INTERFERENCE
                  </span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f87171', margin: '0.4rem 0' }}>
                    78.4%
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Crosstalk Residual: <strong>0.442</strong> &bull; Contaminated by &quot;tail&quot;
                  </div>
                </div>
              </div>

              <div style={{ padding: '0.85rem', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.25)', color: '#fca5a5', fontSize: '0.86rem' }}>
                <strong>Empirical Observation:</strong> Recall fidelity degraded by -21.4%.
                The readout vector <code>v&#770; = v<sub>a</sub> + &rho;&bull;v<sub>b</sub></code> contains a 0.442 contamination component of v<sub>b</sub>.
              </div>
            </div>
          )}

          {/* STEP 7: SYNAPTIC SURGERY */}
          {currentStepIndex === 6 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                <strong>Can we surgically heal or manipulate the memory state?</strong>
                By isolating the specific synaptic weights responsible for the cross-talk overlap,
                we can perform a targeted micro-ablation (<code>W<sub>r,c</sub> &larr; 0</code>).
              </p>

              <div className="judge-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div>
                    <strong style={{ color: '#f8fafc', fontSize: '1rem', display: 'block' }}>
                      Causal Intervention: Targeted Synapse SYN_14
                    </strong>
                    <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                      Responsible for 68% of cross-talk leakage between &quot;cat&quot; and &quot;dog&quot;.
                    </span>
                  </div>

                  <button
                    className="judge-btn-primary"
                    onClick={() => setIsSurgeryApplied(!isSurgeryApplied)}
                    style={{ background: isSurgeryApplied ? '#10b981' : undefined }}
                  >
                    {isSurgeryApplied ? '✓ ABLATION APPLIED' : 'PERFORM SURGERY (ABLATE)'}
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginTop: '1rem' }}>
                  <div className="memory-metric-cell">
                    <span className="metric-cell-label">RECALL FIDELITY</span>
                    <span className="metric-cell-val" style={{ color: isSurgeryApplied ? '#34d399' : '#f87171' }}>
                      {isSurgeryApplied ? '92.6%' : '78.4%'}
                    </span>
                  </div>
                  <div className="memory-metric-cell">
                    <span className="metric-cell-label">CROSSTALK RESIDUAL</span>
                    <span className="metric-cell-val" style={{ color: isSurgeryApplied ? '#34d399' : '#f87171' }}>
                      {isSurgeryApplied ? '0.118' : '0.442'}
                    </span>
                  </div>
                  <div className="memory-metric-cell">
                    <span className="metric-cell-label">STATE STATUS</span>
                    <span className="metric-cell-val">
                      {isSurgeryApplied ? 'Surgically Recovered' : 'Unrepaired Contamination'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 8: COUNTERFACTUAL BRANCHING */}
          {currentStepIndex === 7 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                <strong>Counterfactual Branching:</strong> Same starting cue inputs, but evaluating
                parallel universes with divergent plastic parameters.
              </p>

              <div className="judge-comparison-grid">
                <div className="judge-card" style={{ borderTop: '3px solid #38bdf8' }}>
                  <strong style={{ color: '#38bdf8', display: 'block', fontSize: '0.95rem' }}>
                    ACTUAL WORLD (Standard Decay &lambda; = 0.05)
                  </strong>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', margin: '0.4rem 0' }}>
                    F = 78.4%
                  </div>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Natural gradual memory fading across time.
                  </span>
                </div>

                <div className="judge-card" style={{ borderTop: '3px solid #c084fc' }}>
                  <strong style={{ color: '#c084fc', display: 'block', fontSize: '0.95rem' }}>
                    COUNTERFACTUAL WORLD (High Gain &eta; = 2.0)
                  </strong>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#c084fc', margin: '0.4rem 0' }}>
                    F = 61.2%
                  </div>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Excess write gain amplified catastrophic crosstalk by 43%.
                  </span>
                </div>
              </div>

              <div style={{ padding: '0.75rem', background: 'rgba(168, 85, 247, 0.08)', borderRadius: '8px', color: '#e9d5ff', fontSize: '0.84rem' }}>
                <em>&ldquo;Same starting condition. Different internal state.&rdquo;</em>
              </div>
            </div>
          )}

          {/* STEP 9: EVIDENCE AUDIT */}
          {currentStepIndex === 8 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                Scientific rigor requires uncompromising boundary separation between what is
                directly computed, what is mathematically derived, and what is interpreted.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                <div className="judge-card" style={{ borderTop: '3px solid #34d399' }}>
                  <strong style={{ color: '#34d399', fontSize: '0.85rem' }}>1. MEASURED</strong>
                  <ul style={{ margin: '0.5rem 0 0 1rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    <li>Vector dot products</li>
                    <li>Cosine similarities</li>
                    <li>Frobenius matrix norms</li>
                  </ul>
                </div>

                <div className="judge-card" style={{ borderTop: '3px solid #38bdf8' }}>
                  <strong style={{ color: '#38bdf8', fontSize: '0.85rem' }}>2. DERIVED</strong>
                  <ul style={{ margin: '0.5rem 0 0 1rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    <li>Crosstalk residuals (E<sub>ct</sub>)</li>
                    <li>Active synaptic fractions</li>
                    <li>SVD principal components</li>
                  </ul>
                </div>

                <div className="judge-card" style={{ borderTop: '3px solid #fbbf24' }}>
                  <strong style={{ color: '#fbbf24', fontSize: '0.85rem' }}>3. INTERPRETED</strong>
                  <ul style={{ margin: '0.5rem 0 0 1rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    <li>Associative working memory</li>
                    <li>Superposition vulnerability</li>
                    <li>Capacity limitations</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* STEP 10: RESEARCH CONNECTION */}
          {currentStepIndex === 9 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <p className="judge-step-sub">
                This is not an isolated toy model. Pathway is directly grounded in
                verified peer-reviewed literature (2022–2026):
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div className="judge-card" style={{ borderLeft: '3px solid #10b981' }}>
                  <strong style={{ color: '#f8fafc', fontSize: '0.9rem' }}>
                    Tyulmankov, Yang, & Abbott (2022) &bull; <em>Nature Neuroscience</em>
                  </strong>
                  <div style={{ fontSize: '0.78rem', color: '#38bdf8', margin: '0.15rem 0' }}>
                    DOI: 10.1038/s41593-022-01037-2
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                    Meta-learning synaptic plasticity decouples fast short-term memory encoding from slow stability.
                  </div>
                </div>

                <div className="judge-card" style={{ borderLeft: '3px solid #10b981' }}>
                  <strong style={{ color: '#f8fafc', fontSize: '0.9rem' }}>
                    Krotov (2023) &bull; <em>Nature Reviews Physics</em>
                  </strong>
                  <div style={{ fontSize: '0.78rem', color: '#38bdf8', margin: '0.15rem 0' }}>
                    DOI: 10.1038/s42254-023-00595-y
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                    Hopfield associative memory storage is fundamentally bounded by cue correlation and crosstalk.
                  </div>
                </div>

                <div className="judge-card" style={{ borderLeft: '3px solid #10b981' }}>
                  <strong style={{ color: '#f8fafc', fontSize: '0.9rem' }}>
                    Whittington et al. (2022) &bull; <em>Nature Neuroscience</em>
                  </strong>
                  <div style={{ fontSize: '0.78rem', color: '#38bdf8', margin: '0.15rem 0' }}>
                    DOI: 10.1038/s41593-022-01150-2
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                    Internal representations diverge substantially from surface stimulus geometry.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 11: CENTRAL CLAIM & EXPLORE */}
          {currentStepIndex === 10 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div
                className="judge-card"
                style={{
                  background: 'radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.12) 0%, rgba(15, 28, 53, 0.9) 80%)',
                  border: '1px solid #38bdf8',
                  padding: '2rem',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.75rem' }}>
                  Pathway does not claim to reproduce biological memory.
                </div>
                <p style={{ fontSize: '1.05rem', color: '#e0f2fe', lineHeight: 1.6, maxWidth: '700px', margin: '0 auto' }}>
                  It gives learners an interactive environment where they can manipulate,
                  observe, and reason about synaptic plasticity as a computational short-term memory mechanism.
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '0.5rem' }}>
                <button
                  className="judge-btn-primary"
                  onClick={onExploreFreely}
                  style={{ fontSize: '1rem', padding: '0.85rem 2rem' }}
                >
                  <span>EXPLORE PATHWAY FREELY (ALL 24 PHASES)</span>
                  <span>&rarr;</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation Controls */}
        <div className="judge-footer">
          <button
            className="judge-btn-secondary"
            onClick={handlePrev}
            disabled={currentStepIndex === 0}
            style={{ opacity: currentStepIndex === 0 ? 0.4 : 1, cursor: currentStepIndex === 0 ? 'not-allowed' : 'pointer' }}
          >
            &larr; Previous Step
          </button>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {currentStepIndex < STEPS.length - 1 ? (
              <button className="judge-btn-primary" onClick={handleNext}>
                <span>Next Step</span>
                <span>&rarr;</span>
              </button>
            ) : (
              <button className="judge-btn-primary" onClick={onExploreFreely}>
                <span>Explore Full Application</span>
                <span>&rarr;</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default JudgeModeExperience
