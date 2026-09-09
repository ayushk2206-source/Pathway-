import React from 'react'

interface BranchingTimelineVisualizerProps {
  totalSteps: number
  divergenceStep: number
  currentStep: number
  onSelectStep: (step: number) => void
  events: Array<{ concept_label?: string; attribute_label?: string; symbol_label?: string }>
  targetSynapse?: string
  modifiedVariable?: string
  originalMetric?: number
  counterfactualMetric?: number
}

export const BranchingTimelineVisualizer: React.FC<BranchingTimelineVisualizerProps> = ({
  totalSteps,
  divergenceStep,
  currentStep,
  onSelectStep,
  events,
  targetSynapse,
  modifiedVariable,
  originalMetric,
  counterfactualMetric,
}) => {
  const steps = Array.from({ length: Math.max(totalSteps, 1) }, (_, i) => i)

  return (
    <div className="branching-timeline-card">
      <div className="branching-timeline-header">
        <div className="header-left">
          <span className="branch-glyph">⑂</span>
          <span className="branch-title">BRANCHING COMPUTATIONAL TIMELINE</span>
          {modifiedVariable && (
            <span className="controlled-var-badge">VARIABLE CONTROLLED</span>
          )}
        </div>
        <div className="divergence-point-info">
          <span className="div-tag">DIVERGENCE AT T={divergenceStep}</span>
          {targetSynapse && <span className="syn-tag">{targetSynapse}</span>}
        </div>
      </div>

      <div className="timeline-svg-container">
        <svg viewBox={`0 0 ${Math.max(680, steps.length * 75 + 120)} 170`} className="branching-svg">
          <defs>
            <linearGradient id="origGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#818cf8" />
            </linearGradient>
            <linearGradient id="cfGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>

          {/* Baseline Timeline Bar */}
          <line
            x1="50"
            y1="50"
            x2={50 + (steps.length - 1) * 75}
            y2="50"
            stroke="#1e293b"
            strokeWidth="6"
            strokeLinecap="round"
          />
          <line
            x1="50"
            y1="50"
            x2={50 + (steps.length - 1) * 75}
            y2="50"
            stroke="url(#origGrad)"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* Divergence Branch Line */}
          {divergenceStep < steps.length && (
            <>
              {/* Divergence Diagonal split curve */}
              <path
                d={`M ${50 + divergenceStep * 75} 50 C ${50 + divergenceStep * 75 + 30} 50, ${50 + divergenceStep * 75 + 20} 115, ${50 + (divergenceStep + 1) * 75} 115`}
                fill="none"
                stroke="#f59e0b"
                strokeWidth="2.5"
                strokeDasharray="4 3"
              />
              {/* Counterfactual Timeline Bar */}
              <line
                x1={50 + (divergenceStep + 1) * 75}
                y1="115"
                x2={50 + (steps.length - 1) * 75}
                y2="115"
                stroke="url(#cfGrad)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </>
          )}

          {/* Timeline Nodes */}
          {steps.map((step) => {
            const cx = 50 + step * 75
            const isDivergence = step === divergenceStep
            const isSelected = step === currentStep
            const isPostDivergence = step >= divergenceStep
            const ev = events[step]
            const evLabel = ev ? `${ev.concept_label || 'ev'}` : `T${step}`

            return (
              <g key={step} className="timeline-step-node" onClick={() => onSelectStep(step)} style={{ cursor: 'pointer' }}>
                {/* Baseline Node */}
                <circle
                  cx={cx}
                  cy="50"
                  r={isSelected ? 9 : 6}
                  fill={isSelected ? '#38bdf8' : '#0f172a'}
                  stroke={isDivergence ? '#f59e0b' : '#38bdf8'}
                  strokeWidth={isDivergence ? 3 : 2}
                />
                <text
                  x={cx}
                  y="30"
                  textAnchor="middle"
                  fill={isSelected ? '#38bdf8' : '#94a3b8'}
                  fontSize="11"
                  fontFamily="monospace"
                  fontWeight={isSelected ? 'bold' : 'normal'}
                >
                  T{step}
                </text>
                <text
                  x={cx}
                  y="40"
                  textAnchor="middle"
                  fill="#64748b"
                  fontSize="9"
                >
                  {evLabel.slice(0, 7)}
                </text>

                {/* Counterfactual Node if post-divergence */}
                {isPostDivergence && step > divergenceStep && (
                  <>
                    <circle
                      cx={cx}
                      cy="115"
                      r={isSelected ? 8 : 5}
                      fill={isSelected ? '#ef4444' : '#1e1b4b'}
                      stroke="#ef4444"
                      strokeWidth={isSelected ? 2.5 : 1.5}
                    />
                    <text
                      x={cx}
                      y="135"
                      textAnchor="middle"
                      fill={isSelected ? '#ef4444' : '#f87171'}
                      fontSize="10"
                      fontFamily="monospace"
                    >
                      T{step}*
                    </text>
                  </>
                )}

                {/* Divergence Junction marker */}
                {isDivergence && (
                  <g>
                    <circle cx={cx} cy="50" r="14" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="2 2" />
                    <text x={cx} y="75" textAnchor="middle" fill="#fbbf24" fontSize="10" fontWeight="bold">
                      FORK
                    </text>
                  </g>
                )}
              </g>
            )
          })}

          {/* End Labels */}
          <text
            x={60 + (steps.length - 1) * 75}
            y="54"
            fill="#38bdf8"
            fontSize="11"
            fontFamily="monospace"
            fontWeight="bold"
          >
            ORIGINAL {originalMetric !== undefined ? `(${(originalMetric * 100).toFixed(0)}%)` : ''}
          </text>
          {divergenceStep < steps.length && (
            <text
              x={60 + (steps.length - 1) * 75}
              y="119"
              fill="#ef4444"
              fontSize="11"
              fontFamily="monospace"
              fontWeight="bold"
            >
              WHAT IF {counterfactualMetric !== undefined ? `(${(counterfactualMetric * 100).toFixed(0)}%)` : ''}
            </text>
          )}
        </svg>
      </div>

      {/* Scrubbing bar */}
      <div className="timeline-scrubber-bar">
        <label className="scrubber-label">
          TIMESTEP SCRUBBER: <strong>T{currentStep}</strong> {currentStep >= divergenceStep ? '(POST-DIVERGENCE)' : '(IDENTICAL HISTORY)'}
        </label>
        <input
          type="range"
          min="0"
          max={Math.max(steps.length - 1, 0)}
          value={currentStep}
          onChange={(e) => onSelectStep(Number(e.target.value))}
          className="timeline-slider"
        />
        <div className="scrubber-tags">
          <span className="tag-orig">T0 (Initial)</span>
          <span className="tag-fork">T{divergenceStep} (Fork)</span>
          <span className="tag-end">T{steps.length - 1} (Final)</span>
        </div>
      </div>
    </div>
  )
}
