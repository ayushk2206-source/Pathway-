import React, { useEffect, useState } from 'react'
import type {
  ClaimTrace,
  DisclosuresData,
  MetricDefinition,
  PrimaryResearchPaper,
  ResearchGraphData,
  SourceLicenseRecord,
} from '../types'
import {
  getResearchDisclosures,
  getResearchGraph,
  listResearchClaims,
  listResearchLicenses,
  listResearchMetrics,
  listResearchPapers,
} from '../api'
import { ResearchPaperExplorer } from '../components/ResearchPaperExplorer'
import { ClaimTraceabilityView } from '../components/ClaimTraceabilityView'
import { ResearchLineageGraph } from '../components/ResearchLineageGraph'
import { MetricGlossaryView } from '../components/MetricGlossaryView'
import { DisclosuresAndLicensesView } from '../components/DisclosuresAndLicensesView'
import { PaperDetailModal } from '../components/PaperDetailModal'
import { SciBadge } from '../components/ScientificBadges'
import '../evidence.css'

interface ScientificResearchWorkspaceProps {
  onNavigateWorkspace?: (workspace: string, params?: Record<string, unknown>) => void
}

type TabKey = 'PAPERS' | 'CLAIMS' | 'LINEAGE' | 'METRICS' | 'DISCLOSURES'

export const ScientificResearchWorkspace: React.FC<ScientificResearchWorkspaceProps> = ({
  onNavigateWorkspace,
}) => {
  const [activeTab, setActiveTab] = useState<TabKey>('PAPERS')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [papers, setPapers] = useState<PrimaryResearchPaper[]>([])
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [claims, setClaims] = useState<ClaimTrace[]>([])
  const [metrics, setMetrics] = useState<MetricDefinition[]>([])
  const [graphData, setGraphData] = useState<ResearchGraphData | null>(null)
  const [disclosures, setDisclosures] = useState<DisclosuresData | null>(null)
  const [licenses, setLicenses] = useState<SourceLicenseRecord[]>([])

  // Modal detail state
  const [modalPaper, setModalPaper] = useState<PrimaryResearchPaper | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)

    Promise.all([
      listResearchPapers(),
      listResearchClaims(),
      listResearchMetrics(),
      getResearchGraph(),
      getResearchDisclosures(),
      listResearchLicenses(),
    ])
      .then(([papersRes, claimsRes, metricsRes, graphRes, discRes, licRes]) => {
        if (!mounted) return
        setPapers(papersRes.papers || [])
        setAvailableTags(papersRes.available_tags || ['ALL'])
        setClaims(claimsRes.claims || [])
        setMetrics(metricsRes.metrics || [])
        setGraphData(graphRes)
        setDisclosures(discRes)
        setLicenses(licRes.licenses || [])
        setLoading(false)
      })
      .catch((err) => {
        if (!mounted) return
        console.error('Failed to load scientific research data', err)
        setError(err.message || 'Failed to load scientific research data')
        setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [])

  const handleSelectPaperId = (paperId: string) => {
    const found = papers.find((p) => p.paper_id === paperId)
    if (found) {
      setModalPaper(found)
    }
  }

  const handleExploreInPathway = (paper: PrimaryResearchPaper) => {
    if (!onNavigateWorkspace) return
    // Route to appropriate workspace based on paper's topic
    if (paper.paper_id.includes('tyulmankov') || paper.paper_id.includes('miconi')) {
      onNavigateWorkspace('studio', { seed: 42, decay: 0.05 })
    } else if (paper.paper_id.includes('krotov')) {
      onNavigateWorkspace('collision', { concept_a: 'cat', concept_b: 'dog' })
    } else if (paper.paper_id.includes('whittington')) {
      onNavigateWorkspace('genome', { concept: 'cat' })
    } else {
      onNavigateWorkspace('detective', {})
    }
  }

  return (
    <div className="evidence-workspace">
      {/* Header */}
      <div className="evidence-header">
        <div>
          <h1>
            <span>Scientific Evidence & Research Layer</span>
            <SciBadge type="published" label="PEER-REVIEWED" />
          </h1>
          <p>
            Rigorous scientific provenance for <em>Synaptic Plasticity as Short-Term Memory</em>.
            Every Pathway simulation maps to published neurocomputational literature (2022–2026),
            distinguishing measured algebraic reality from biological analogies.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
          <SciBadge type="pathway" label="PATHWAY ENGINE v0.23" />
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {papers.length} Papers &bull; {claims.length} Claims &bull; {metrics.length} Metrics
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="evidence-tabs">
        <button
          className={`evidence-tab-btn ${activeTab === 'PAPERS' ? 'active' : ''}`}
          onClick={() => setActiveTab('PAPERS')}
        >
          <span>&curren;</span> Primary Literature ({papers.length})
        </button>
        <button
          className={`evidence-tab-btn ${activeTab === 'CLAIMS' ? 'active' : ''}`}
          onClick={() => setActiveTab('CLAIMS')}
        >
          <span>&diams;</span> Traceable Claims ({claims.length})
        </button>
        <button
          className={`evidence-tab-btn ${activeTab === 'LINEAGE' ? 'active' : ''}`}
          onClick={() => setActiveTab('LINEAGE')}
        >
          <span>&sect;</span> Research Lineage Graph
        </button>
        <button
          className={`evidence-tab-btn ${activeTab === 'METRICS' ? 'active' : ''}`}
          onClick={() => setActiveTab('METRICS')}
        >
          <span>&fnof;</span> Mathematical Glossary ({metrics.length})
        </button>
        <button
          className={`evidence-tab-btn ${activeTab === 'DISCLOSURES' ? 'active' : ''}`}
          onClick={() => setActiveTab('DISCLOSURES')}
        >
          <span>&para;</span> Disclosures & Licenses
        </button>
      </div>

      {/* Content Area */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          Loading peer-reviewed research layer...
        </div>
      ) : error ? (
        <div style={{ padding: '2rem', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', borderRadius: '8px' }}>
          <strong>Error:</strong> {error}
        </div>
      ) : (
        <>
          {activeTab === 'PAPERS' && (
            <ResearchPaperExplorer
              papers={papers}
              availableTags={availableTags}
              onSelectPaper={(p) => setModalPaper(p)}
              onExploreInPathway={handleExploreInPathway}
            />
          )}

          {activeTab === 'CLAIMS' && (
            <ClaimTraceabilityView
              claims={claims}
              papers={papers}
              onSelectPaperId={handleSelectPaperId}
            />
          )}

          {activeTab === 'LINEAGE' && graphData && (
            <ResearchLineageGraph
              graphData={graphData}
              onSelectPaperId={handleSelectPaperId}
            />
          )}

          {activeTab === 'METRICS' && (
            <MetricGlossaryView metrics={metrics} />
          )}

          {activeTab === 'DISCLOSURES' && (
            <DisclosuresAndLicensesView
              disclosures={disclosures}
              licenses={licenses}
            />
          )}
        </>
      )}

      {/* Paper Citation Modal */}
      <PaperDetailModal
        paper={modalPaper}
        onClose={() => setModalPaper(null)}
        onExploreInPathway={handleExploreInPathway}
      />
    </div>
  )
}

export default ScientificResearchWorkspace
