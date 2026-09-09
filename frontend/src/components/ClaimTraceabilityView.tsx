import React from 'react'
import type { ClaimTrace, PrimaryResearchPaper } from '../types'
import { SciBadge } from './ScientificBadges'

interface ClaimTraceabilityViewProps {
  claims: ClaimTrace[]
  papers: PrimaryResearchPaper[]
  onSelectPaperId: (paperId: string) => void
}

export const ClaimTraceabilityView: React.FC<ClaimTraceabilityViewProps> = ({
  claims,
  papers,
  onSelectPaperId,
}) => {
  const paperMap = React.useMemo(() => {
    const map = new Map<string, PrimaryResearchPaper>()
    papers.forEach((p) => map.set(p.paper_id, p))
    return map
  }, [papers])

  return (
    <div className="claims-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.2rem', color: '#f8fafc' }}>
            Evidence & Claim Traceability Architecture
          </h2>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Every claim is explicitly grounded in published literature, tested in Pathway, and qualified by non-claims.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <SciBadge type="simplified" label="EMPIRICAL BOUNDARY" />
          <SciBadge type="pathway" label="5-PART EVIDENCE PANEL" />
        </div>
      </div>

      {claims.map((claim) => {
        return (
          <div key={claim.claim_id} className="claim-card">
            <div className="claim-card-top">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="claim-id">{claim.claim_id}</span>
                <SciBadge type="pathway" label={`EXP: ${claim.pathway_experiment_type}`} />
              </div>

              {/* Citations */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>
                  LITERATURE SOURCES:
                </span>
                {claim.source_paper_ids.map((pid, idx) => {
                  const p = paperMap.get(pid)
                  const label = p ? `${p.authors[0].split(' ')[0]} et al. (${p.year})` : pid
                  return (
                    <button
                      key={pid}
                      className="citation-ref-tag"
                      onClick={() => onSelectPaperId(pid)}
                      title={p ? p.title : pid}
                    >
                      [{idx + 1}] {label}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="claim-statement">
              &ldquo;{claim.claim_text}&rdquo;
            </div>

            {/* 5-Part Evidence Panel */}
            <div className="evidence-5grid">
              {/* 1. What we changed */}
              <div className="evidence-box changed">
                <span className="box-label">
                  <span>&bull;</span> 1. What We Changed
                </span>
                <span className="box-content">
                  Injected structured key-value bindings (<em>v</em> &otimes; <em>k</em>) into recurrent synaptic weight matrix <em>W</em>.
                </span>
              </div>

              {/* 2. What we measured */}
              <div className="evidence-box measured">
                <span className="box-label">
                  <span>&bull;</span> 2. What We Measured
                </span>
                <span className="box-content">
                  <strong>Metrics:</strong> {claim.measured_metrics.join(', ')}.
                </span>
              </div>

              {/* 3. What happened */}
              <div className="evidence-box happened">
                <span className="box-label">
                  <span>&bull;</span> 3. What Happened
                </span>
                <span className="box-content">
                  {claim.observed_finding}
                </span>
              </div>

              {/* 4. What this suggests */}
              <div className="evidence-box suggests">
                <span className="box-label">
                  <span>&bull;</span> 4. What This Suggests
                </span>
                <span className="box-content">
                  {claim.scientific_interpretation}
                </span>
              </div>

              {/* 5. What this does not prove */}
              <div className="evidence-box does-not-prove">
                <span className="box-label">
                  <span>&bull;</span> 5. What This Does NOT Prove
                </span>
                <span className="box-content">
                  {claim.what_this_does_not_prove}
                </span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ClaimTraceabilityView
