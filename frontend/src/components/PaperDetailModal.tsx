import React from 'react'
import type { PrimaryResearchPaper } from '../types'
import { SciBadge } from './ScientificBadges'

interface PaperDetailModalProps {
  paper: PrimaryResearchPaper | null
  onClose: () => void
  onExploreInPathway?: (paper: PrimaryResearchPaper) => void
}

export const PaperDetailModal: React.FC<PaperDetailModalProps> = ({
  paper,
  onClose,
  onExploreInPathway,
}) => {
  if (!paper) return null

  return (
    <div className="citation-modal-overlay" onClick={onClose}>
      <div
        className="citation-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <SciBadge type="published" />
            {paper.open_access && (
              <span className="sci-badge live" style={{ fontSize: '0.7rem' }}>
                OPEN ACCESS
              </span>
            )}
          </div>
          <button className="citation-close-btn" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <div>
          <h2 style={{ margin: '0.25rem 0 0.5rem 0', fontSize: '1.25rem', color: '#f8fafc', lineHeight: 1.35 }}>
            {paper.title}
          </h2>
          <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            {paper.authors.join(', ')} ({paper.year})
          </div>
          <div style={{ color: '#64748b', fontSize: '0.8rem', marginTop: '0.2rem' }}>
            <em>{paper.journal}</em> &bull; DOI:{' '}
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="paper-doi-link"
            >
              {paper.doi} &nearr;
            </a>
          </div>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
          {paper.tags.map((tag) => (
            <span
              key={tag}
              style={{
                fontSize: '0.72rem',
                background: 'rgba(56, 189, 248, 0.1)',
                color: '#38bdf8',
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
              }}
            >
              #{tag}
            </span>
          ))}
        </div>

        <div className="paper-key-finding">
          <strong style={{ color: '#34d399', display: 'block', marginBottom: '0.2rem' }}>
            Key Peer-Reviewed Finding:
          </strong>
          {paper.key_finding}
        </div>

        <div className="paper-connection-box">
          <strong style={{ color: '#38bdf8', display: 'block', marginBottom: '0.2rem' }}>
            Pathway Implementation Connection:
          </strong>
          {paper.pathway_connection}
        </div>

        <div className="paper-limitation-box">
          <strong style={{ color: '#f87171', display: 'block', marginBottom: '0.2rem' }}>
            Model Limitations & Biological Boundary:
          </strong>
          {paper.model_limitations}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#38bdf8',
              fontSize: '0.84rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              textDecoration: 'none',
            }}
          >
            Read Original Publisher Article &nearr;
          </a>

          {onExploreInPathway && (
            <button
              className="explore-in-pathway-btn"
              onClick={() => {
                onExploreInPathway(paper)
                onClose()
              }}
            >
              EXPLORE IN PATHWAY &rarr;
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default PaperDetailModal
