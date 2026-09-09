import React, { useState } from 'react'
import type { PrimaryResearchPaper } from '../types'
import { SciBadge } from './ScientificBadges'

interface ResearchPaperExplorerProps {
  papers: PrimaryResearchPaper[]
  availableTags: string[]
  onSelectPaper: (paper: PrimaryResearchPaper) => void
  onExploreInPathway?: (paper: PrimaryResearchPaper) => void
}

export const ResearchPaperExplorer: React.FC<ResearchPaperExplorerProps> = ({
  papers,
  availableTags,
  onSelectPaper,
  onExploreInPathway,
}) => {
  const [selectedTag, setSelectedTag] = useState<string>('ALL')

  const filteredPapers = selectedTag === 'ALL'
    ? papers
    : papers.filter((p) =>
        p.tags.some((t) => t.toLowerCase().includes(selectedTag.toLowerCase()))
      )

  return (
    <div className="paper-explorer-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.2rem', color: '#f8fafc' }}>
            Primary Peer-Reviewed Research Archive (2022–2026)
          </h2>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Verified literature directly grounding Pathway's synaptic memory mechanisms.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <SciBadge type="published" label="PEER-REVIEWED" />
          <SciBadge type="pathway" label="IMPLEMENTATION-LINKED" />
        </div>
      </div>

      <div className="tag-filter-bar">
        <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600, marginRight: '0.25rem' }}>
          FILTER BY TOPIC:
        </span>
        {availableTags.map((tag) => (
          <button
            key={tag}
            className={`tag-btn ${selectedTag === tag ? 'active' : ''}`}
            onClick={() => setSelectedTag(tag)}
          >
            {tag}
          </button>
        ))}
      </div>

      <div className="papers-grid">
        {filteredPapers.map((paper) => (
          <div key={paper.paper_id} className="paper-card">
            <div className="paper-card-header">
              <div>
                <h3
                  className="paper-title"
                  style={{ cursor: 'pointer' }}
                  onClick={() => onSelectPaper(paper)}
                >
                  {paper.title}
                </h3>
                <div className="paper-authors" style={{ marginTop: '0.25rem' }}>
                  {paper.authors.join(', ')} ({paper.year})
                </div>
              </div>
              <SciBadge type="published" label={`${paper.year}`} />
            </div>

            <div className="paper-meta-row">
              <span>{paper.journal}</span>
              <span>&bull;</span>
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="paper-doi-link"
                onClick={(e) => e.stopPropagation()}
              >
                DOI: {paper.doi} &nearr;
              </a>
              {paper.open_access && (
                <span style={{ color: '#4ade80', fontSize: '0.75rem', fontWeight: 600 }}>
                  [OPEN ACCESS]
                </span>
              )}
            </div>

            <div className="paper-key-finding">
              <strong style={{ color: '#34d399', display: 'block', fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                EMPIRICAL / THEORETICAL FINDING:
              </strong>
              {paper.key_finding}
            </div>

            <div className="paper-connection-box">
              <strong style={{ color: '#38bdf8', display: 'block', fontSize: '0.78rem', marginBottom: '0.15rem' }}>
                PATHWAY DIRECT CONNECTION:
              </strong>
              {paper.pathway_connection}
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.25rem' }}>
              {paper.tags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    fontSize: '0.72rem',
                    background: 'rgba(56, 189, 248, 0.08)',
                    color: '#94a3b8',
                    padding: '0.1rem 0.4rem',
                    borderRadius: '4px',
                  }}
                >
                  #{tag}
                </span>
              ))}
            </div>

            <div className="paper-card-actions">
              <button
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  color: '#94a3b8',
                  fontSize: '0.78rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
                onClick={() => onSelectPaper(paper)}
              >
                View Full Details &rarr;
              </button>

              {onExploreInPathway && (
                <button
                  className="explore-in-pathway-btn"
                  onClick={() => onExploreInPathway(paper)}
                >
                  EXPLORE IN PATHWAY &rarr;
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ResearchPaperExplorer
