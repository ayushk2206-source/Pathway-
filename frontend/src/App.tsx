import { useEffect, useRef, useState } from 'react'
import type {
  ActivationProfile,
  AnomalyRecord,
  ClusterResult,
  CounterfactualExperiment,
  DiagnosticsProfile,
  EventInspector,
  Experiment,
  ExperimentSummary,
  HeatmapsData,
  InterferenceRecord,
  MechanismInfo,
  MemoryExplanation,
  MemoryMap2D,
  MemoryRelationshipGraph,
  MemoryStrengthProfile,
  MemoryTrace,
  RunRequest,
  SparsityAnalysis,
} from './types'
import {
  getExperiment,
  getHealth,
  getMechanisms,
  getXRayActivation,
  getXRayAnomalies,
  getXRayClusters,
  getXRayCompetition,
  getXRayDiagnostics,
  getXRayExplanation,
  getXRayHeatmaps,
  getXRayInspector,
  getXRayInterference,
  getXRayMap,
  getXRaySparsity,
  getXRayStrengths,
  getXRayTrace,
  listExperiments,
  replayExperiment,
  runDemoExperiment,
  runExperiment,
} from './api'
import { TopBar } from './components/TopBar'
import { CommandRail, type WorkspaceId } from './components/CommandRail'
import { CommandPalette } from './components/CommandPalette'
import { EvidenceModal } from './components/EvidenceModal'
import { KeyboardShortcutsModal } from './components/KeyboardShortcutsModal'
import { MemoryInspectorDrawer } from './components/MemoryInspectorDrawer'
import { ObservatoryWorkspace } from './workspaces/ObservatoryWorkspace'
import { ObservatoryStudioWorkspace } from './workspaces/ObservatoryStudioWorkspace'
import { SynapticBrainWorkspace } from './workspaces/SynapticBrainWorkspace'
import { SurgeryWorkspace } from './workspaces/SurgeryWorkspace'
import { MemoryCollisionWorkspace } from './MemoryCollisionWorkspace'
import { MemoryLabWorkspace } from './workspaces/MemoryLabWorkspace'
import { MemoryXRayWorkspace } from './workspaces/MemoryXRayWorkspace'
import { TimelineWorkspace } from './workspaces/TimelineWorkspace'
import { MemoryMapWorkspace } from './workspaces/MemoryMapWorkspace'
import { CounterfactualWorkspace } from './workspaces/CounterfactualWorkspace'
import { ExperimentsWorkspace } from './workspaces/ExperimentsWorkspace'
import { ReportsWorkspace } from './workspaces/ReportsWorkspace'
import { MemoryDetectiveWorkspace } from './workspaces/MemoryDetectiveWorkspace'
import { ResearchLabWorkspace } from './workspaces/ResearchLabWorkspace'
import { GenomeWorkspace } from './workspaces/GenomeWorkspace'
import { AgencyWorkspace } from './workspaces/AgencyWorkspace'
import { CausalWorkspace } from './workspaces/CausalWorkspace'
import { MemoryEcosystemWorkspace } from './workspaces/MemoryEcosystemWorkspace'
import { ExperimentStudioWorkspace } from './workspaces/ExperimentStudioWorkspace'
import { ScientificResearchWorkspace } from './workspaces/ScientificResearchWorkspace'
import { ImmersionEntryHero } from './components/ImmersionEntryHero'
import { ImmersiveNavDock } from './components/ImmersiveNavDock'
import { CustomPointer } from './components/CustomPointer'
import { JudgeModeExperience } from './components/JudgeModeExperience'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ProceduralBackground } from './components/ProceduralBackground'
import './App.css'
import './forensics.css'
import './immersive.css'
import './judge.css'

export default function App() {
  // Navigation & Workspace state
  const [isImmersionPortalOpen, setIsImmersionPortalOpen] = useState(true)
  const [isJudgeModeOpen, setIsJudgeModeOpen] = useState(false)
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false)
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>('synaptic')
  const [observatoryMode, setObservatoryMode] = useState<'studio' | 'overview'>('studio')
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [isShortcutsOpen, setIsShortcutsOpen] = useState(false)
  const [isFollowingMemory, setIsFollowingMemory] = useState(true)
  const [evidenceData, setEvidenceData] = useState<{ title: string; details: Record<string, unknown> } | null>(null)

  // Core Data State
  const [mechanisms, setMechanisms] = useState<Record<string, MechanismInfo>>({})
  const [experimentsList, setExperimentsList] = useState<ExperimentSummary[]>([])
  const [experiment, setExperiment] = useState<Experiment | null>(null)
  const [isBusy, setIsBusy] = useState(false)
  const [apiStatus, setApiStatus] = useState('ONLINE (200 OK)')

  // Timeline & Playback
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [lastModifiedMemoryId, setLastModifiedMemoryId] = useState<string | null>(null)

  // Selected Memory for Forensic Inspection
  const [selectedMemoryId, setSelectedMemoryId] = useState<string | null>(null)
  const [selectedStrengthProfile, setSelectedStrengthProfile] = useState<MemoryStrengthProfile | null>(null)
  const [selectedTrace, setSelectedTrace] = useState<MemoryTrace | null>(null)
  const [selectedExplanation, setSelectedExplanation] = useState<MemoryExplanation | null>(null)

  // Subsystem Analytics
  const [memoryMap, setMemoryMap] = useState<MemoryMap2D | null>(null)
  const [graph, setGraph] = useState<MemoryRelationshipGraph | null>(null)
  const [clusters, setClusters] = useState<ClusterResult[]>([])
  const [interference, setInterference] = useState<InterferenceRecord[]>([])
  const [diagnostics, setDiagnostics] = useState<DiagnosticsProfile | null>(null)
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([])
  const [heatmaps, setHeatmaps] = useState<HeatmapsData | null>(null)
  const [activationProfile, setActivationProfile] = useState<ActivationProfile | null>(null)
  const [sparsityAnalysis, setSparsityAnalysis] = useState<SparsityAnalysis | null>(null)
  const [eventInspector, setEventInspector] = useState<EventInspector | null>(null)
  const [counterfactuals, setCounterfactuals] = useState<CounterfactualExperiment[]>([])

  // Initial Boot: Health, Mechanisms, Archive Listing
  useEffect(() => {
    getHealth()
      .then((h) => setApiStatus(`v${h.core_version} · ONLINE`))
      .catch(() => setApiStatus('OFFLINE (BACKEND UNREACHABLE)'))

    getMechanisms()
      .then((m) => setMechanisms(m.mechanisms))
      .catch(() => {})

    listExperiments()
      .then((list) => {
        setExperimentsList(list)
        if (list.length > 0 && !experiment) {
          loadExperiment(list[0].experiment_id)
        }
      })
      .catch(() => {})
  }, [])

  // Auto-fetch analytics whenever active experiment changes
  const loadExperiment = async (id: string) => {
    setIsBusy(true)
    try {
      const exp = await getExperiment(id)
      setExperiment(exp)
      setCurrentStep(exp.snapshots.length ? exp.snapshots.length - 1 : 0)

      // Fetch X-Ray data in parallel
      const [mMap, compGraph, clus, interf, diag, anoms, hmaps, spars] = await Promise.all([
        getXRayMap(id).catch(() => null),
        getXRayCompetition(id).catch(() => null),
        getXRayClusters(id).then((r) => r.clusters).catch(() => []),
        getXRayInterference(id).then((r) => r.interference_records).catch(() => []),
        getXRayDiagnostics(id).catch(() => null),
        getXRayAnomalies(id).then((r) => r.anomalies).catch(() => []),
        getXRayHeatmaps(id).catch(() => null),
        getXRaySparsity(id).catch(() => null),
      ])

      setMemoryMap(mMap)
      setGraph(compGraph)
      setClusters(clus)
      setInterference(interf)
      setDiagnostics(diag)
      setAnomalies(anoms)
      setHeatmaps(hmaps)
      setSparsityAnalysis(spars)

      if (mMap?.points?.length) {
        setSelectedMemoryId(mMap.points[0].memory_id)
      }
    } catch (e) {
      alert(`Failed to load experiment: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsBusy(false)
    }
  }

  // Update step-dependent inspection (activation & before/after microscope)
  useEffect(() => {
    if (!experiment) return
    const stepIdx = currentStep

    getXRayActivation(experiment.experiment_id, stepIdx)
      .then((act) => setActivationProfile(act))
      .catch(() => {})

    if (stepIdx > 0 && stepIdx <= experiment.events.length) {
      getXRayInspector(experiment.experiment_id, stepIdx - 1)
        .then((insp) => setEventInspector(insp))
        .catch(() => {})
    } else {
      setEventInspector(null)
    }
  }, [experiment, currentStep])

  // Update selected memory details when selectedMemoryId changes
  useEffect(() => {
    if (!experiment || !selectedMemoryId) return

    Promise.all([
      getXRayStrengths(experiment.experiment_id).catch(() => null),
      getXRayTrace(experiment.experiment_id, selectedMemoryId).catch(() => null),
      getXRayExplanation(experiment.experiment_id, selectedMemoryId).catch(() => null),
    ]).then(([strRes, trRes, expRes]) => {
      if (strRes?.strengths?.[selectedMemoryId]) {
        setSelectedStrengthProfile(strRes.strengths[selectedMemoryId])
      }
      setSelectedTrace(trRes)
      setSelectedExplanation(expRes)
    })
  }, [experiment, selectedMemoryId])

  // Playback timer loop
  const isPlayingRef = useRef(isPlaying)
  isPlayingRef.current = isPlaying

  useEffect(() => {
    if (!isPlaying || !experiment) return
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (!experiment.snapshots.length) return 0
        if (prev >= experiment.snapshots.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 600)
    return () => clearInterval(interval)
  }, [isPlaying, experiment])

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Avoid hotkeys when typing in inputs/textareas
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA') {
        return
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setIsCommandPaletteOpen((prev) => !prev)
        return
      }

      if (e.key === 'Escape') {
        setIsCommandPaletteOpen(false)
        setIsShortcutsOpen(false)
        setEvidenceData(null)
        setSelectedMemoryId(null)
        return
      }

      if (e.key === ' ') {
        e.preventDefault()
        setIsPlaying((p) => !p)
        return
      }

      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        setCurrentStep((s) => Math.max(0, s - 1))
        return
      }

      if (e.key === 'ArrowRight') {
        e.preventDefault()
        if (experiment) {
          setCurrentStep((s) => Math.min(experiment.snapshots.length - 1, s + 1))
        }
        return
      }

      if (e.key === '?') {
        e.preventDefault()
        setIsShortcutsOpen((p) => !p)
        return
      }

      switch (e.key.toLowerCase()) {
        case 'e':
          setActiveWorkspace('ecosystem')
          break
        case 'p':
          setActiveWorkspace('studio')
          break
        case 's':
          setActiveWorkspace('synaptic')
          break
        case 'x':
          setActiveWorkspace('xray')
          break
        case 'c':
          setActiveWorkspace('counterfactual')
          break
        case 'm':
          setActiveWorkspace('map')
          break
        case 'd':
          setActiveWorkspace('detective')
          break
        case 'g':
          setActiveWorkspace('genome')
          break
        case 'a':
          setActiveWorkspace('agency')
          break
        case 'l':
          setActiveWorkspace('causal')
          break
        case 'r':
          handleReplay()
          break
        case '[':
        case ']':
          setIsSidebarExpanded((p) => !p)
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [experiment])

  // Actions
  const handleLaunchDemo = async () => {
    setIsBusy(true)
    try {
      const demo = await runDemoExperiment()
      setExperiment(demo)
      const list = await listExperiments()
      setExperimentsList(list)
      loadExperiment(demo.experiment_id)
      setActiveWorkspace('observatory')
    } catch (e) {
      alert(`Demo failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const handleReplay = async () => {
    if (!experiment || isBusy) return
    setIsBusy(true)
    try {
      const replayed = await replayExperiment(experiment.experiment_id)
      setExperiment(replayed)
      setCurrentStep(0)
      setIsPlaying(true)
    } catch (e) {
      alert(`Replay failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setIsBusy(false)
    }
  }

  const handleRunNewExperiment = async (req: RunRequest) => {
    setIsBusy(true)
    try {
      const newExp = await runExperiment(req)
      setExperiment(newExp)
      const list = await listExperiments()
      setExperimentsList(list)
      await loadExperiment(newExp.experiment_id)
      setActiveWorkspace('observatory')
    } finally {
      setIsBusy(false)
    }
  }

  const handleCounterfactualCreated = (cf: CounterfactualExperiment) => {
    setCounterfactuals((prev) => [cf, ...prev])
  }

  const availableMemories = memoryMap?.points.map((p) => p.memory_id) || []

  return (
    <div className="app-shell" style={{ position: 'relative' }}>
      <ProceduralBackground />
      <CustomPointer mode="default" />

      {isImmersionPortalOpen && (
        <ImmersionEntryHero
          onEnter={() => setIsImmersionPortalOpen(false)}
          onLaunchJudgeMode={() => {
            setIsImmersionPortalOpen(false)
            setIsJudgeModeOpen(true)
          }}
        />
      )}

      {/* Primary Scientific TopBar Navigation */}
      <TopBar
        currentExperiment={experiment}
        experiments={experimentsList}
        onSelectExperiment={loadExperiment}
        onLaunchDemo={handleLaunchDemo}
        onReplay={handleReplay}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenShortcuts={() => setIsShortcutsOpen(true)}
        onOpenJudgeMode={() => setIsJudgeModeOpen(true)}
        isBusy={isBusy}
        selectedMemoryId={selectedMemoryId}
        isFollowingMemory={isFollowingMemory}
        onToggleFollowMemory={() => setIsFollowingMemory((p) => !p)}
      />

      {/* Main Workspace Layout */}
      <div className="workspace-layout">
        <CommandRail
          activeWorkspace={activeWorkspace}
          onSelectWorkspace={setActiveWorkspace}
          engineDim={experiment?.task.d || 128}
          apiStatus={apiStatus}
          isExpanded={isSidebarExpanded}
          onToggleExpand={() => setIsSidebarExpanded((p) => !p)}
        />

        <main className="main-canvas">
          <ErrorBoundary fallbackTitle={`${activeWorkspace.toUpperCase()} SUBSYSTEM TELEMETRY`}>
            {activeWorkspace === 'ecosystem' && (
              <MemoryEcosystemWorkspace
                onNavigateToWorkspace={(ws) => setActiveWorkspace(ws as WorkspaceId)}
                onSelectGlobalMemory={(id) => setSelectedMemoryId(id)}
              />
            )}

            {activeWorkspace === 'synaptic' && (
              <SynapticBrainWorkspace
                experiment={experiment}
                currentStep={currentStep}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'surgery' && (
              <SurgeryWorkspace
                experiment={experiment}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'collision' && (
              <MemoryCollisionWorkspace />
            )}

            {activeWorkspace === 'observatory' && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, width: '100%', height: '100%' }}>
                <div style={{
                  display: 'flex',
                  gap: '0.5rem',
                  padding: '0.4rem 1.25rem',
                  background: 'rgba(15, 23, 42, 0.9)',
                  borderBottom: '1px solid rgba(51, 65, 85, 0.5)',
                  alignItems: 'center',
                }}>
                  <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 700 }}>
                    Observatory Mode:
                  </span>
                  <button
                    className={`preset-chip ${observatoryMode === 'studio' ? 'active' : ''}`}
                    onClick={() => setObservatoryMode('studio')}
                  >
                    ⚡ Adaptive Studio (Phase 19)
                  </button>
                  <button
                    className={`preset-chip ${observatoryMode === 'overview' ? 'active' : ''}`}
                    onClick={() => setObservatoryMode('overview')}
                  >
                    ○ Classic Overview (Phase 13)
                  </button>
                </div>

                {observatoryMode === 'studio' ? (
                  <ObservatoryStudioWorkspace />
                ) : (
                  <ObservatoryWorkspace
                    experiment={experiment}
                    currentStep={currentStep}
                    onStepChange={setCurrentStep}
                    onJumpToEvent={(idx) => {
                      setCurrentStep(idx + 1)
                      if (experiment?.events[idx]) {
                        setLastModifiedMemoryId(experiment.events[idx].id)
                      }
                    }}
                    isPlaying={isPlaying}
                    onTogglePlay={() => setIsPlaying(!isPlaying)}
                    onStepForward={() => {
                      if (experiment) setCurrentStep((s) => Math.min(experiment.snapshots.length - 1, s + 1))
                    }}
                    onStepBackward={() => setCurrentStep((s) => Math.max(0, s - 1))}
                    mapPoints={memoryMap?.points || []}
                    graph={graph}
                    selectedMemoryId={selectedMemoryId}
                    onSelectMemory={setSelectedMemoryId}
                    lastModifiedMemoryId={lastModifiedMemoryId}
                    eventInspector={eventInspector}
                    onLaunchDemo={handleLaunchDemo}
                    onOpenCreateExperiment={() => setActiveWorkspace('lab')}
                  />
                )}
              </div>
            )}

            {activeWorkspace === 'lab' && (
              <MemoryLabWorkspace
                mechanisms={mechanisms}
                onRunExperiment={handleRunNewExperiment}
                isBusy={isBusy}
              />
            )}

            {activeWorkspace === 'xray' && (
              <MemoryXRayWorkspace
                experiment={experiment}
                currentStep={currentStep}
                onStepChange={setCurrentStep}
                activationProfile={activationProfile}
                sparsityAnalysis={sparsityAnalysis}
                diagnostics={diagnostics}
                anomalies={anomalies}
                eventInspector={eventInspector}
                memoryMap={memoryMap}
                selectedMemoryId={selectedMemoryId}
                onSelectMemory={setSelectedMemoryId}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'timeline' && (
              <TimelineWorkspace
                experiment={experiment}
                currentStep={currentStep}
                onStepChange={setCurrentStep}
                selectedMemoryId={selectedMemoryId}
                trace={selectedTrace}
                heatmaps={heatmaps}
                onSelectMemory={setSelectedMemoryId}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'map' && (
              <MemoryMapWorkspace
                experiment={experiment}
                memoryMap={memoryMap}
                graph={graph}
                clusters={clusters}
                interferenceRecords={interference}
                selectedMemoryId={selectedMemoryId}
                onSelectMemory={setSelectedMemoryId}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'counterfactual' && (
              <CounterfactualWorkspace
                experiment={experiment}
                counterfactuals={counterfactuals}
                onCounterfactualCreated={handleCounterfactualCreated}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'experiments' && (
              <ExperimentsWorkspace
                currentExperiment={experiment}
                experiments={experimentsList}
                onSelectExperiment={loadExperiment}
                onLaunchDemo={handleLaunchDemo}
              />
            )}

            {activeWorkspace === 'reports' && (
              <ReportsWorkspace
                experiment={experiment}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'detective' && (
              <MemoryDetectiveWorkspace />
            )}

            {activeWorkspace === 'research' && (
              <ResearchLabWorkspace />
            )}

            {activeWorkspace === 'genome' && (
              <GenomeWorkspace
                experiment={experiment}
                selectedMemoryId={selectedMemoryId}
                onSelectMemory={setSelectedMemoryId}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'agency' && (
              <AgencyWorkspace />
            )}

            {activeWorkspace === 'causal' && (
              <CausalWorkspace
                experiment={experiment}
                onViewEvidence={(title, details) => setEvidenceData({ title, details })}
              />
            )}

            {activeWorkspace === 'studio' && (
              <ExperimentStudioWorkspace
                onNavigateToWorkspace={(ws) => setActiveWorkspace(ws as WorkspaceId)}
              />
            )}

            {activeWorkspace === 'evidence' && (
              <ScientificResearchWorkspace
                onNavigateWorkspace={(ws) => setActiveWorkspace(ws as WorkspaceId)}
              />
            )}
          </ErrorBoundary>
        </main>
      </div>

      {/* Floating Scientific Instrument Navigation Dock */}
      <ImmersiveNavDock
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={(ws) => {
          if (ws === 'judge') {
            setIsJudgeModeOpen(true)
          } else {
            setActiveWorkspace(ws)
          }
        }}
        onOpenPortal={() => setIsImmersionPortalOpen(true)}
        onOpenJudgeMode={() => setIsJudgeModeOpen(true)}
      />

      {/* Judge Mode Evaluation Tour Modal */}
      {(isJudgeModeOpen || activeWorkspace === 'judge') && (
        <JudgeModeExperience
          onClose={() => {
            setIsJudgeModeOpen(false)
            if (activeWorkspace === 'judge') setActiveWorkspace('ecosystem')
          }}
          onExploreFreely={() => {
            setIsJudgeModeOpen(false)
            if (activeWorkspace === 'judge') setActiveWorkspace('ecosystem')
          }}
        />
      )}

      {/* Forensic Slide-Over Inspector */}
      {selectedMemoryId && (
        <MemoryInspectorDrawer
          memoryId={selectedMemoryId}
          strengthProfile={selectedStrengthProfile}
          trace={selectedTrace}
          explanation={selectedExplanation}
          clusterId={memoryMap?.points.find((p) => p.memory_id === selectedMemoryId)?.cluster ?? 0}
          onClose={() => setSelectedMemoryId(null)}
          onTraceMemory={() => setActiveWorkspace('timeline')}
          onXRayMemory={() => setActiveWorkspace('xray')}
          onSurgeryMemory={() => setActiveWorkspace('counterfactual')}
          onCounterfactual={() => setActiveWorkspace('counterfactual')}
          onInvestigateMemory={(id) => {
            setSelectedMemoryId(id)
            setActiveWorkspace('detective')
          }}
          onViewEvidence={(title, details) => setEvidenceData({ title, details })}
        />
      )}

      {/* Command Palette Overlay (⌘K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onNavigate={(ws) => {
          setActiveWorkspace(ws)
          setIsCommandPaletteOpen(false)
        }}
        onLaunchDemo={handleLaunchDemo}
        onReplay={handleReplay}
        onSelectMemory={(id) => {
          setSelectedMemoryId(id)
          setIsCommandPaletteOpen(false)
        }}
        availableMemories={availableMemories}
      />

      {/* Computational Provenance Evidence Modal */}
      <EvidenceModal
        isOpen={!!evidenceData}
        title={evidenceData?.title || 'Evidence'}
        details={evidenceData?.details || null}
        onClose={() => setEvidenceData(null)}
      />

      {/* Keyboard Shortcuts Reference Dialog (?) */}
      <KeyboardShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />
    </div>
  )
}