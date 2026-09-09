import type {
  ActivationProfile,
  AnomalyRecord,
  ClusterResult,
  CounterfactualExperiment,
  DiagnosticsProfile,
  EventImpact,
  EventInspector,
  Experiment,
  ExperimentSummary,
  Health,
  HeatmapsData,
  InterferenceRecord,
  MechanismInfo,
  MemoryExplanation,
  MemoryMap2D,
  MemoryRelationshipGraph,
  MemorySnapshot,
  MemoryStrengthProfile,
  MemoryTrace,
  ReinforcementRecord,
  RunRequest,
  SparsityAnalysis,
  StateTrajectory,
  SurgeryDiff,
  XRayReport,
  CandidateHypothesis,
  DiscoveryObservation,
  Investigation,
  InvestigationScorecard,
  MemoryAutopsy,
  MemoryBirthRecord,
  MemoryDeathRecord,
  MinimumIntervention,
  NotebookEntry,
  RobustnessEvaluation,
  SensitivityRecord,
  TestResult,
  CascadeMap,
  CascadeReport,
  CentralityRecord,
  CriticalMemoryRank,
  DependencyMatrix,
  DoseResponseEvaluation,
  FragilityReport,
  GenomeReport,
  InfluenceBreakdown,
  MemoryGenome,
  MemoryLineageGraph,
  PathDependenceEvaluation,
  RecoveryEvaluation,
  RedundancyRecord,
  SandboxBranch,
  AgentCatalogResponse,
  ResearchInvestigation,
  WarRoomState,
} from './types'

const BASE = '/api'

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
      else if (Array.isArray(body?.detail)) detail = body.detail.map((d: { msg?: string }) => d.msg).join('; ')
    } catch {
      /* keep status text */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Health & Mechanisms
// ---------------------------------------------------------------------------
export function getHealth(): Promise<Health> {
  return json<Health>(`${BASE}/health`)
}

export function getMechanisms(): Promise<{ mechanisms: Record<string, MechanismInfo> }> {
  return json(`${BASE}/mechanisms`)
}

// ---------------------------------------------------------------------------
// Experiment Management
// ---------------------------------------------------------------------------
export function listExperiments(): Promise<ExperimentSummary[]> {
  return json<ExperimentSummary[]>(`${BASE}/experiments`)
}

export function getExperiment(id: string): Promise<Experiment> {
  return json<Experiment>(`${BASE}/experiments/${id}`)
}

export function runExperiment(req: RunRequest): Promise<Experiment> {
  return json<Experiment>(`${BASE}/experiments/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runDemoExperiment(): Promise<Experiment> {
  return json<Experiment>(`${BASE}/experiments/demo`, {
    method: 'POST',
  })
}

export function replayExperiment(id: string, params?: Partial<RunRequest['params']>): Promise<Experiment> {
  return json<Experiment>(`${BASE}/experiments/${id}/replay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params ? { params } : {}),
  })
}

// ---------------------------------------------------------------------------
// Phase 05 Memory X-Ray & Analytics Endpoints
// ---------------------------------------------------------------------------
export function getXRaySnapshots(id: string): Promise<{ snapshots: MemorySnapshot[] }> {
  return json<{ snapshots: MemorySnapshot[] }>(`${BASE}/xray/${id}/snapshots`)
}

export function getXRayTrajectory(id: string): Promise<StateTrajectory> {
  return json<StateTrajectory>(`${BASE}/xray/${id}/trajectory`)
}

export function getXRayHeatmaps(id: string): Promise<HeatmapsData> {
  return json<HeatmapsData>(`${BASE}/xray/${id}/heatmaps`)
}

export function getXRayChanges(id: string): Promise<{ changes: Record<string, unknown>[] }> {
  return json<{ changes: Record<string, unknown>[] }>(`${BASE}/xray/${id}/changes`)
}

export function getXRayActivation(id: string, step = 0): Promise<ActivationProfile> {
  return json<ActivationProfile>(`${BASE}/xray/${id}/activation-profile?step=${step}`)
}

export function getXRaySparsity(id: string): Promise<SparsityAnalysis> {
  return json<SparsityAnalysis>(`${BASE}/xray/${id}/sparsity`)
}

export function getXRayStrengths(id: string): Promise<{ strengths: Record<string, MemoryStrengthProfile> }> {
  return json<{ strengths: Record<string, MemoryStrengthProfile> }>(`${BASE}/xray/${id}/strength`)
}

export function getXRayDecay(id: string): Promise<{ decay_curves: Record<string, unknown> }> {
  return json<{ decay_curves: Record<string, unknown> }>(`${BASE}/xray/${id}/decay`)
}

export function getXRayReinforcement(id: string): Promise<{ reinforcement_records: ReinforcementRecord[] }> {
  return json<{ reinforcement_records: ReinforcementRecord[] }>(`${BASE}/xray/${id}/reinforcement`)
}

export function getXRayInterference(id: string): Promise<{ interference_records: InterferenceRecord[] }> {
  return json<{ interference_records: InterferenceRecord[] }>(`${BASE}/xray/${id}/interference`)
}

export function getXRayCompetition(id: string): Promise<MemoryRelationshipGraph> {
  return json<MemoryRelationshipGraph>(`${BASE}/xray/${id}/competition`)
}

export function getXRayClusters(id: string): Promise<{ clusters: ClusterResult[] }> {
  return json<{ clusters: ClusterResult[] }>(`${BASE}/xray/${id}/clusters`)
}

export function getXRayMap(id: string): Promise<MemoryMap2D> {
  return json<MemoryMap2D>(`${BASE}/xray/${id}/map`)
}

export function getXRayNeighbors(id: string, memoryId: string, k = 5): Promise<{ neighbors: { memory_id: string; similarity: number }[] }> {
  return json<{ neighbors: { memory_id: string; similarity: number }[] }>(`${BASE}/xray/${id}/neighbors/${memoryId}?k=${k}`)
}

export function getXRayTrace(id: string, memoryId: string): Promise<MemoryTrace> {
  return json<MemoryTrace>(`${BASE}/xray/${id}/trace/${memoryId}`)
}

export function getXRayEventImpact(id: string): Promise<{ event_impacts: EventImpact[] }> {
  return json<{ event_impacts: EventImpact[] }>(`${BASE}/xray/${id}/event-impact`)
}

export function getXRayImportance(id: string): Promise<{ importance_profiles: Record<string, Record<string, unknown>> }> {
  return json<{ importance_profiles: Record<string, Record<string, unknown>> }>(`${BASE}/xray/${id}/importance`)
}

export function getXRayExplanation(id: string, memoryId: string): Promise<MemoryExplanation> {
  return json<MemoryExplanation>(`${BASE}/xray/${id}/explanation/${memoryId}`)
}

export function getXRayInspector(id: string, eventIdx: number): Promise<EventInspector> {
  return json<EventInspector>(`${BASE}/xray/${id}/inspector/${eventIdx}`)
}

export function getXRayDiagnostics(id: string): Promise<DiagnosticsProfile> {
  return json<DiagnosticsProfile>(`${BASE}/xray/${id}/diagnostics`)
}

export function getXRayAnomalies(id: string): Promise<{ anomalies: AnomalyRecord[] }> {
  return json<{ anomalies: AnomalyRecord[] }>(`${BASE}/xray/${id}/anomalies`)
}

export function getXRayReport(id: string): Promise<XRayReport> {
  return json<XRayReport>(`${BASE}/xray/${id}/report`)
}

export function executeXRayQuery(id: string, query: string, params: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
  return json<Record<string, unknown>>(`${BASE}/xray/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ experiment_id: id, query, params }),
  })
}

export function compareSurgery(originalId: string, counterfactualId: string): Promise<SurgeryDiff> {
  return json<SurgeryDiff>(`${BASE}/xray/surgery-diff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_experiment_id: originalId,
      counterfactual_experiment_id: counterfactualId,
    }),
  })
}

// ---------------------------------------------------------------------------
// Phase 04 Counterfactual Endpoints
// ---------------------------------------------------------------------------
export function runCounterfactual(req: {
  experiment_id: string
  intervention: {
    intervention_type: string
    target_timestep?: number
    target_event_id?: string
    parameters?: Record<string, unknown>
    description?: string
  }
  strategy?: string
  title?: string
  description?: string
}): Promise<CounterfactualExperiment> {
  return json<CounterfactualExperiment>(`${BASE}/counterfactual/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runSurgery(req: {
  experiment_id: string
  target_timestep: number
  new_strength: number
  title?: string
  description?: string
}): Promise<CounterfactualExperiment> {
  return json<CounterfactualExperiment>(`${BASE}/counterfactual/surgery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runAblation(req: {
  experiment_id: string
  target_timestep: number
  title?: string
  description?: string
}): Promise<CounterfactualExperiment> {
  return json<CounterfactualExperiment>(`${BASE}/counterfactual/ablation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getCounterfactual(id: string): Promise<CounterfactualExperiment> {
  return json<CounterfactualExperiment>(`${BASE}/counterfactual/${id}`)
}

export function getCounterfactualsByParent(parentId: string): Promise<CounterfactualExperiment[]> {
  return json<CounterfactualExperiment[]>(`${BASE}/counterfactual/by-parent/${parentId}`)
}

// ---------------------------------------------------------------------------
// Phase 07 Detective & Hypothesis Engine Endpoints
// ---------------------------------------------------------------------------

export function parseDetectiveQuestion(question: string): Promise<{
  question: string
  intent: string
  target_memory?: string | null
  target_event?: string | null
  parameters: Record<string, unknown>
  suggested_tests: string[]
  required_data: string[]
  confidence: number
}> {
  return json(`${BASE}/detective/parse-question`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}

export function runInvestigation(req: {
  experiment_id: string
  question: string
  target_memory?: string | null
  execute_tests?: boolean
}): Promise<Investigation> {
  return json<Investigation>(`${BASE}/detective/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function generateHypotheses(req: {
  experiment_id: string
  target_memory: string
  intent?: string
}): Promise<{
  experiment_id: string
  target_memory: string
  hypotheses: CandidateHypothesis[]
}> {
  return json(`${BASE}/detective/hypotheses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function executeDetectiveTest(req: {
  experiment_id: string
  hypothesis_id: string
  test_design: Record<string, unknown>
}): Promise<{
  test_result: TestResult
  evidence_chain: Record<string, unknown>
  updated_hypothesis: CandidateHypothesis
}> {
  return json(`${BASE}/detective/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function fetchAutopsy(
  experimentId: string,
  memoryId: string,
): Promise<{
  autopsy: MemoryAutopsy
  birth_record?: MemoryBirthRecord | null
  death_record?: MemoryDeathRecord | null
  survival_analysis?: Record<string, unknown>
  failure_analysis?: Record<string, unknown>
}> {
  return json(`${BASE}/detective/autopsy/${experimentId}/${memoryId}`)
}

export function fetchSensitivity(
  experimentId: string,
  memoryId: string,
  interferingEventId?: string,
): Promise<{
  experiment_id: string
  memory_id: string
  sensitivity: SensitivityRecord
  minimum_intervention: MinimumIntervention
  robustness: RobustnessEvaluation
}> {
  const q = interferingEventId ? `?interfering_event_id=${encodeURIComponent(interferingEventId)}` : ''
  return json(`${BASE}/detective/sensitivity/${experimentId}/${memoryId}${q}`)
}

export function fetchDiscoveryFeed(experimentId: string): Promise<{
  experiment_id: string
  discoveries_count: number
  discoveries: DiscoveryObservation[]
}> {
  return json(`${BASE}/detective/discovery/${experimentId}`)
}

export function listInvestigations(experimentId?: string): Promise<{
  total: number
  investigations: Investigation[]
}> {
  const q = experimentId ? `?experiment_id=${encodeURIComponent(experimentId)}` : ''
  return json(`${BASE}/detective/investigations${q}`)
}

export function fetchInvestigation(investigationId: string): Promise<Investigation> {
  return json<Investigation>(`${BASE}/detective/investigations/${investigationId}`)
}

export function reproduceInvestigation(
  investigationId: string,
  targetExperimentId?: string,
): Promise<Investigation> {
  return json<Investigation>(`${BASE}/detective/investigations/${investigationId}/reproduce`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_experiment_id: targetExperimentId }),
  })
}

export function diffInvestigations(id1: string, id2: string): Promise<Record<string, unknown>> {
  return json(`${BASE}/detective/investigations/${id1}/diff/${id2}`)
}

export function fetchScorecard(investigationId: string): Promise<InvestigationScorecard> {
  return json<InvestigationScorecard>(`${BASE}/detective/investigations/${investigationId}/scorecard`)
}

export function fetchNotebook(experimentId: string): Promise<{
  experiment_id: string
  entries: NotebookEntry[]
}> {
  return json(`${BASE}/detective/notebook?experiment_id=${encodeURIComponent(experimentId)}`)
}

export function saveNotebookEntry(req: {
  experiment_id: string
  title: string
  content: string
  author?: string
  linked_investigation_id?: string
  tags?: string[]
}): Promise<NotebookEntry> {
  return json<NotebookEntry>(`${BASE}/detective/notebook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function deleteNotebookEntry(
  experimentId: string,
  entryId: string,
): Promise<{ status: string; entry_id: string }> {
  return json(`${BASE}/detective/notebook/${experimentId}/${entryId}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Phase 08: Memory Genome + Cascade Engine
// ============================================================================

export function getMemoryGenome(
  experimentId: string,
  memoryId: string,
): Promise<{ genome: MemoryGenome }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}`)
}

export function getMemoryLineage(
  experimentId: string,
  memoryId: string,
): Promise<{ lineage: MemoryLineageGraph }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}/lineage`)
}

export function runCascade(req: {
  experiment_id: string
  target_memory: string
  intervention: string
  dose: number
}): Promise<{
  cascade: CascadeMap
  influence_breakdown: InfluenceBreakdown
  surprise: boolean
}> {
  return json(`${BASE}/genome/cascade`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getCentrality(
  experimentId: string,
): Promise<{ centrality: CentralityRecord[] }> {
  return json(`${BASE}/genome/${experimentId}/centrality`)
}

export function getCriticalMemories(
  experimentId: string,
): Promise<{ critical_memories: CriticalMemoryRank[] }> {
  return json(`${BASE}/genome/${experimentId}/critical-memories`)
}

export function getFragility(
  experimentId: string,
  memoryId: string,
): Promise<{ fragility: FragilityReport }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}/fragility`)
}

export function getRedundancy(
  experimentId: string,
  memoryId: string,
): Promise<{ redundancy: RedundancyRecord }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}/redundancy`)
}

export function runDoseResponse(req: {
  experiment_id: string
  target_memory: string
}): Promise<{ dose_response: DoseResponseEvaluation }> {
  return json(`${BASE}/genome/dose-response`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runRecoveryTest(req: {
  experiment_id: string
  target_memory: string
}): Promise<{ recovery: RecoveryEvaluation }> {
  return json(`${BASE}/genome/recovery-test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getPathDependence(
  experimentId: string,
): Promise<{ path_dependence: PathDependenceEvaluation }> {
  return json(`${BASE}/genome/${experimentId}/path-dependence`)
}

export function createSandboxBranch(req: {
  experiment_id: string
  parent_id: string
  intervention: Record<string, unknown>
}): Promise<{ branch: SandboxBranch }> {
  return json(`${BASE}/genome/sandbox/branch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function listSandboxBranches(
  experimentId: string,
): Promise<{ branches: SandboxBranch[] }> {
  return json(`${BASE}/genome/sandbox/branches/${experimentId}`)
}

export function compareBranches(req: {
  experiment_id: string
  intervention_a: Record<string, unknown>
  intervention_b: Record<string, unknown>
}): Promise<{ comparison: Record<string, unknown> }> {
  return json(`${BASE}/genome/sandbox/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getDependencyMatrix(
  experimentId: string,
  metric: string = 'association',
): Promise<{ dependency_matrix: DependencyMatrix }> {
  return json(`${BASE}/genome/${experimentId}/dependency-matrix?metric=${encodeURIComponent(metric)}`)
}

export function getGenomeReport(
  experimentId: string,
  memoryId: string,
): Promise<{ report: GenomeReport }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}/report`)
}

export function getCascadeReport(
  experimentId: string,
  memoryId: string,
  intervention: string = 'remove',
): Promise<{ cascade_report: CascadeReport }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}/cascade-report?intervention=${encodeURIComponent(intervention)}`)
}

export function getAutomaticQuestions(
  experimentId: string,
  memoryId: string,
): Promise<{ questions: string[] }> {
  return json(`${BASE}/genome/${experimentId}/${encodeURIComponent(memoryId)}/questions`)
}

// ============================================================================
// Phase 09: Autonomous Discovery Engine / Agency API
// ============================================================================

export function listAgents(): Promise<AgentCatalogResponse> {
  return json<AgentCatalogResponse>(`${BASE}/agency/agents`)
}

export function createAgencyInvestigation(
  researchQuestion: string,
): Promise<ResearchInvestigation> {
  return json<ResearchInvestigation>(`${BASE}/agency/investigations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ research_question: researchQuestion }),
  })
}

export function runAgencyInvestigation(
  researchQuestion: string,
  maxRounds: number = 2,
): Promise<ResearchInvestigation> {
  return json<ResearchInvestigation>(`${BASE}/agency/investigations/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ research_question: researchQuestion, max_rounds: maxRounds }),
  })
}

export function listAgencyInvestigations(): Promise<{
  total: number
  investigations: ResearchInvestigation[]
}> {
  return json(`${BASE}/agency/investigations`)
}

export function getAgencyInvestigation(id: string): Promise<ResearchInvestigation> {
  return json<ResearchInvestigation>(`${BASE}/agency/investigations/${id}`)
}

export function getWarRoom(id: string): Promise<{ war_room: WarRoomState }> {
  return json(`${BASE}/agency/investigations/${id}/war-room`)
}

export function challengeFinding(req: {
  finding: string
  context: Record<string, unknown>
}): Promise<{
  objections: string[]
  verdict: string
  confidence: number
  analysis: string
}> {
  return json(`${BASE}/agency/challenge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function exportAntigravitySkills(): Promise<{
  total_exported: number
  skills: Record<string, unknown>[]
}> {
  return json(`${BASE}/agency/antigravity/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
}

// ============================================================================
// Phase 10: Causal Memory Lab
// ============================================================================

export function causalCreateScenario(req: {
  experiment_id: string
  target_memory: string
  intervention: string
  timing?: number
  strength?: number
  duration?: number
  label?: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/scenarios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalListScenarios(experimentId?: string): Promise<Record<string, unknown>[]> {
  const q = experimentId ? `?experiment_id=${encodeURIComponent(experimentId)}` : ''
  return json(`${BASE}/causal/scenarios${q}`)
}

export function causalValidateScenario(req: {
  experiment_id: string
  target_memory?: string
  intervention: string
  timing?: number
  strength?: number
  label?: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/scenarios/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalEstimateCost(req: {
  experiment_id: string
  runs_required?: number
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/scenarios/estimate-cost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalRunCounterfactual(req: {
  experiment_id: string
  target_memory: string
  intervention: string
  timing?: number
  strength?: number
  duration?: number
  label?: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/counterfactual/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalGetDivergence(counterfactualId: string): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/divergence/${encodeURIComponent(counterfactualId)}`)
}

export function causalGetFirstDivergence(counterfactualId: string): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/first-divergence/${encodeURIComponent(counterfactualId)}`)
}

export function causalGetCascadeTrace(
  experimentId: string,
  memoryId: string,
  interventionType: string = 'remove',
  dose: number = 1.0,
): Promise<Record<string, unknown>> {
  return json(
    `${BASE}/causal/cascade-trace/${encodeURIComponent(experimentId)}/${encodeURIComponent(memoryId)}?intervention_type=${encodeURIComponent(interventionType)}&dose=${dose}`,
  )
}

export function causalGetCriticalWindows(
  experimentId: string,
  memoryId: string,
): Promise<Record<string, unknown>> {
  return json(
    `${BASE}/causal/critical-windows/${encodeURIComponent(experimentId)}/${encodeURIComponent(memoryId)}`,
  )
}

export function causalGetCausalGraph(
  experimentId: string,
  memoryId: string,
  interventionType: string = 'remove',
  dose: number = 1.0,
): Promise<Record<string, unknown>> {
  return json(
    `${BASE}/causal/graph/${encodeURIComponent(experimentId)}/${encodeURIComponent(memoryId)}?intervention_type=${encodeURIComponent(interventionType)}&dose=${dose}`,
  )
}

export function causalTestEdge(req: {
  experiment_id: string
  source_memory: string
  target_memory: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/edge/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalRunMultiIntervention(req: {
  experiment_id: string
  interventions: { memory_id: string; intervention: string; dose?: number }[]
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/multi-intervention`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalRunSwap(req: {
  experiment_id: string
  memory_a: string
  memory_b: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/swap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalRunRecovery(req: {
  experiment_id: string
  target_memory: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/recovery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalGetRecoveryCurve(
  experimentId: string,
  memoryId: string,
): Promise<Record<string, unknown>> {
  return json(
    `${BASE}/causal/recovery-curve/${encodeURIComponent(experimentId)}/${encodeURIComponent(memoryId)}`,
  )
}

export function causalGetMatrix(
  experimentId: string,
  memories?: string,
): Promise<Record<string, unknown>> {
  const q = memories ? `?memories=${encodeURIComponent(memories)}` : ''
  return json(`${BASE}/causal/matrix/${encodeURIComponent(experimentId)}${q}`)
}

export function causalGetTemporalMap(
  experimentId: string,
  memoryId: string,
  nBins: number = 6,
): Promise<Record<string, unknown>> {
  return json(
    `${BASE}/causal/temporal-map/${encodeURIComponent(experimentId)}/${encodeURIComponent(memoryId)}?n_bins=${nBins}`,
  )
}

export function causalGetLedger(): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/ledger`)
}

export function causalRegisterClaim(req: {
  source_memory: string
  target_memory: string
  statement: string
  status?: string
  evidence_experiment_ids?: string[]
  interventions?: number
  replications?: number
  effect_consistency?: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/claims`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalGetConflicts(): Promise<Record<string, unknown>[]> {
  return json(`${BASE}/causal/conflicts`)
}

export function causalCreateReport(req: {
  experiment_id: string
  question: string
  scenario?: string
  baseline?: string
  intervention?: string
  temporal_window?: string
  first_divergence?: string
  cascade?: string
  effect?: string
  alternative_paths?: string
  replication?: string
  limitations?: string
  conclusion?: string
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function causalListReports(experimentId?: string): Promise<Record<string, unknown>[]> {
  const q = experimentId ? `?experiment_id=${encodeURIComponent(experimentId)}` : ''
  return json(`${BASE}/causal/reports${q}`)
}

export function causalGetReport(reportId: string): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/reports/${encodeURIComponent(reportId)}`)
}

export function causalGetReplay(
  experimentId: string,
  counterfactualId: string,
): Promise<Record<string, unknown>> {
  return json(
    `${BASE}/causal/replay/${encodeURIComponent(experimentId)}/${encodeURIComponent(counterfactualId)}`,
  )
}

export function causalGetQueue(): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/queue`)
}

export function causalControlQueue(action: 'pause' | 'resume' | 'stop' | 'clear'): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/queue/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
}

export function causalHandoffToDiscovery(req: {
  experiment_id: string
  title: string
  pattern_type: string
  description?: string
  evidence?: Record<string, unknown>
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/causal/discovery/handoff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// ============================================================================
// Phase 01: Live Synaptic Brain API
// ============================================================================

export function getSynapticInfo(): Promise<import('./types').SynapticInfo> {
  return json(`${BASE}/synaptic/info`)
}

export function getSynapticState(
  dimension: number = 16,
  decay: number = 0.05,
  seed: number = 42,
): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/state?dimension=${dimension}&decay=${decay}&seed=${seed}`)
}

export function writeSynapticMemory(req: {
  concept: string
  value: string
  importance?: number
  strength?: number
  decay?: number
  update_strength?: number
  memory_strength?: number
  seed?: number
  dimension?: number
}): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/write`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function recallSynapticMemory(req: {
  query_concept: string
  expected_value?: string
  measure?: string
  top_k?: number
  seed?: number
  dimension?: number
}): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/recall`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function decaySynapticBrain(
  steps: number = 1,
  decay: number = 0.05,
): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/decay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ steps, decay }),
  })
}

export function resetSynapticBrain(
  dimension: number = 16,
  decay: number = 0.05,
  seed: number = 42,
): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/reset?dimension=${dimension}&decay=${decay}&seed=${seed}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
}

export function runSynapticScenario(
  scenario: string,
  dimension: number = 16,
  decay: number = 0.05,
  seed: number = 42,
): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/scenario`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, dimension, decay, seed }),
  })
}

export function getSynapticFromExperiment(
  experimentId: string,
  stepIdx: number,
  displayDim: number = 16,
): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/experiment/${encodeURIComponent(experimentId)}/step/${stepIdx}?display_dim=${displayDim}`)
}

export function getSynapticHistory(): Promise<import('./types').TimeMachineHistoryResponse> {
  return json(`${BASE}/synaptic/history`)
}

export function getSynapticSnapshot(stepIdx: number): Promise<import('./types').SynapticNetworkState> {
  return json(`${BASE}/synaptic/snapshot/${stepIdx}`)
}

export function getSynapseHistory(synapseId: string): Promise<import('./types').SynapseHistory> {
  return json(`${BASE}/synaptic/synapse/${encodeURIComponent(synapseId)}/history`)
}

export function getMemoryHistory(concept: string): Promise<import('./types').MemoryHistory> {
  return json(`${BASE}/synaptic/memory/${encodeURIComponent(concept)}/history`)
}

export function diffSynapticStates(req: {
  step_a: number
  step_b: number
  experiment_id?: string
}): Promise<import('./types').StateDiffResult> {
  return json(`${BASE}/synaptic/diff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runSynapticProtocol(req?: {
  protocol_name?: string
  dimension?: number
  decay?: number
  seed?: number
}): Promise<import('./types').TimeMachineProtocolResponse> {
  return json(`${BASE}/synaptic/protocol`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req || {}),
  })
}

export function getExperimentSynapticHistory(
  experimentId: string,
  displayDim: number = 16,
): Promise<{ experiment_id: string; total_steps: number; states: import('./types').SynapticNetworkState[] }> {
  return json(`${BASE}/synaptic/experiment/${encodeURIComponent(experimentId)}/history?display_dim=${displayDim}`)
}

// ---------------------------------------------------------------------------
// Phase 15: Synaptic Surgery & Memory X-Ray API
// ---------------------------------------------------------------------------

export function lockSurgeryBaseline(req?: {
  dimension?: number
  seed?: number
  decay?: number
}): Promise<{ status: string; message: string; session: import('./types').SurgerySession }> {
  return json(`${BASE}/surgery/lock`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req || {}),
  })
}

export function getSurgeryState(): Promise<{
  locked: boolean
  session: import('./types').SurgerySession | null
  message: string
}> {
  return json(`${BASE}/surgery/state`)
}

export function weakenSynapses(
  synapseIds: string[],
  factor: number = 0.5,
): Promise<{ operation: import('./types').SurgeryOperation; session: import('./types').SurgerySession }> {
  return json(`${BASE}/surgery/weaken`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synapse_ids: synapseIds, factor }),
  })
}

export function strengthenSynapses(
  synapseIds: string[],
  factor: number = 2.0,
): Promise<{ operation: import('./types').SurgeryOperation; session: import('./types').SurgerySession }> {
  return json(`${BASE}/surgery/strengthen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synapse_ids: synapseIds, factor }),
  })
}

export function silenceSynapses(
  synapseIds: string[],
): Promise<{ operation: import('./types').SurgeryOperation; session: import('./types').SurgerySession }> {
  return json(`${BASE}/surgery/silence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synapse_ids: synapseIds }),
  })
}

export function restoreSynapses(
  synapseIds: string[],
): Promise<{ operation: import('./types').SurgeryOperation; session: import('./types').SurgerySession }> {
  return json(`${BASE}/surgery/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synapse_ids: synapseIds }),
  })
}

export function resetSurgery(): Promise<{
  operation: import('./types').SurgeryOperation
  session: import('./types').SurgerySession
}> {
  return json(`${BASE}/surgery/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
}

export function runSurgeryRecall(req: {
  query_concept: string
  expected_value?: string
  measure?: string
  top_k?: number
}): Promise<{
  comparison: import('./types').SurgeryRecallComparison
  session: import('./types').SurgerySession
}> {
  return json(`${BASE}/surgery/recall`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getSynapseXRay(synapseId: string): Promise<import('./types').SynapseXRayDetail> {
  return json(`${BASE}/surgery/synapse/${encodeURIComponent(synapseId)}/xray`)
}

export function getMemoryXRay(req: {
  query_concept: string
  expected_value?: string
  dimension?: number
  seed?: number
  decay?: number
  branch?: 'live' | 'baseline' | 'surgery'
}): Promise<import('./types').MemoryXRay> {
  return json(`${BASE}/surgery/xray/memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// ==========================================
// Phase 16 Counterfactual / What-If Engine API
// ==========================================

export function runSynapticCounterfactual(
  req: import('./types').SynapticInterventionPayload,
): Promise<import('./types').SynapticInterventionResponse> {
  return json(`${BASE}/counterfactual/synaptic-intervention`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function compareSynapticCounterfactual(
  originalExperimentId: string,
  counterfactualId: string,
  stepIdx: number,
  displayDim: number = 16,
): Promise<import('./types').SynapticCompareResponse> {
  return json(`${BASE}/counterfactual/synaptic-compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_experiment_id: originalExperimentId,
      counterfactual_id: counterfactualId,
      step_idx: stepIdx,
      display_dim: displayDim,
    }),
  })
}

export function getExperimentBranches(
  experimentId: string,
): Promise<import('./types').ExperimentBranchesResponse> {
  return json(`${BASE}/counterfactual/branches/${encodeURIComponent(experimentId)}`)
}

// ============================================================================
// Phase 17: Memory Collision & Interference Lab API
// ============================================================================

export function runCollisionExperiment(
  req: import('./types').CollisionConfig,
): Promise<import('./types').CollisionResult> {
  return json(`${BASE}/collision/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runThreeConditionSuite(req: {
  seed: number
  dimension: number
  decay: number
  update_strength: number
  memory_a: import('./types').CollisionMemory
  memory_b: import('./types').CollisionMemory
  order: 'A_THEN_B' | 'B_THEN_A'
  temporal_delay: number
}): Promise<import('./types').ThreeConditionResult> {
  return json(`${BASE}/collision/three-conditions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runOrderComparison(req: {
  seed: number
  dimension: number
  decay: number
  update_strength: number
  memory_a: import('./types').CollisionMemory
  memory_b: import('./types').CollisionMemory
  overlap_preset: string
  concept_similarity: number
  temporal_delay: number
}): Promise<import('./types').OrderComparisonResult> {
  return json(`${BASE}/collision/order-comparison`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runCollisionSurgery(req: {
  config: import('./types').CollisionConfig
  synapse_id: string
  operation: 'silence' | 'weaken' | 'strengthen'
  factor?: number
}): Promise<import('./types').CollisionSurgeryResult> {
  return json(`${BASE}/collision/surgery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runCollisionCounterfactual(req: {
  config: import('./types').CollisionConfig
  shared_synapse_ids?: string[]
}): Promise<import('./types').CollisionCounterfactualResult> {
  return json(`${BASE}/collision/counterfactual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// ============================================================================
// Phase 18: Memory Detective & Research Lab Forensics API
// ============================================================================

export function getDetectiveCases(
  blind: boolean = true,
): Promise<{ total: number; cases: import('./types').InvestigationCase[] }> {
  return json(`${BASE}/forensics/cases?blind=${blind}`)
}

export function getDetectiveCase(
  caseId: string,
  blind: boolean = true,
): Promise<{ case: import('./types').InvestigationCase }> {
  return json(`${BASE}/forensics/cases/${encodeURIComponent(caseId)}?blind=${blind}`)
}

export function testDetectiveHypothesis(
  caseId: string,
  hypothesisId: string,
  tool: string = 'xray',
): Promise<import('./types').HypothesisTestResult> {
  return json(`${BASE}/forensics/cases/${encodeURIComponent(caseId)}/test-hypothesis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hypothesis_id: hypothesisId, tool }),
  })
}

export function submitDetectiveVerdict(
  caseId: string,
  payload: {
    chosen_hypothesis_id: string
    collected_evidence_ids: string[]
    tests_run_count: number
    learner_confidence: string
    explanation_chain: string[]
  },
): Promise<{
  case_id: string
  score: import('./types').DetectiveScore
  ground_truth_explanation: string
}> {
  return json(`${BASE}/forensics/cases/${encodeURIComponent(caseId)}/submit-verdict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function runCustomResearch(
  config: Partial<import('./types').CustomExperimentConfig>,
): Promise<import('./types').CustomExperimentResult> {
  return json(`${BASE}/forensics/research/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
}

export function getResearchHistory(): Promise<{
  total: number
  experiments: import('./types').CustomExperimentResult[]
}> {
  return json(`${BASE}/forensics/research/history`)
}

export function compareResearchExperiments(
  expAId: string,
  expBId: string,
): Promise<import('./types').ExperimentComparison> {
  return json(`${BASE}/forensics/research/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exp_a_id: expAId, exp_b_id: expBId }),
  })
}

export function getForensicsSources(): Promise<import('./types').ForensicsSourcesResponse> {
  return json(`${BASE}/forensics/sources`)
}

export function getForensicsObjectives(): Promise<{
  total: number
  objectives: import('./types').LearningObjective[]
}> {
  return json(`${BASE}/forensics/objectives`)
}

// ==========================================
// Phase 19 Adaptive Memory Observatory API
// ==========================================

export function getObservatoryPresets(): Promise<{
  presets: import('./types').ObservatoryPreset[]
}> {
  return json(`${BASE}/observatory/presets`)
}

export function listObservatorySessions(): Promise<{
  total: number
  sessions: Array<{
    session_id: string
    name: string
    description: string
    created_at: string
    total_steps: number
    dimension: number
  }>
}> {
  return json(`${BASE}/observatory/sessions`)
}

export function getObservatorySession(
  sessionId: string,
): Promise<{
  session: import('./types').ObservatorySession
  env_report?: import('./types').EnvironmentShiftReport
}> {
  return json(`${BASE}/observatory/sessions/${encodeURIComponent(sessionId)}`)
}

export function runObservatoryStream(req: {
  name: string
  description?: string
  dimension?: number
  default_learning_rate?: number
  default_decay_rate?: number
  events: Array<{
    event_id: string
    step: number
    event_type: string
    key_label: string
    environment_id: string
    decay_rate?: number
    learning_rate?: number
    cue_pattern?: number[]
    target_pattern?: number[]
    metadata?: Record<string, unknown>
  }>
  probes?: Array<{
    concept: string
    cue_pattern: number[]
    target_pattern: number[]
  }>
}): Promise<{
  session: import('./types').ObservatorySession
  env_report?: import('./types').EnvironmentShiftReport
}> {
  return json(`${BASE}/observatory/stream/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function diffObservatoryStates(req: {
  session_id: string
  step_from: number
  step_to: number
  threshold?: number
}): Promise<{
  diff: import('./types').ChangeDetection
}> {
  return json(`${BASE}/observatory/diff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getStabilityPlasticity(
  sessionId: string,
  stepA: number,
  stepB: number,
): Promise<{
  metrics: import('./types').StabilityPlasticityMetrics
}> {
  return json(
    `${BASE}/observatory/stability-plasticity/${encodeURIComponent(sessionId)}?step_a=${stepA}&step_b=${stepB}`,
  )
}

export function branchObservatoryIntervention(req: {
  session_id: string
  branch_step: number
  target_synapse: [number, number]
  new_weight: number
  branch_name?: string
}): Promise<{
  branch_session: import('./types').ObservatorySession
}> {
  return json(`${BASE}/observatory/branch/intervention`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function branchObservatoryCounterfactual(req: {
  session_id: string
  branch_step: number
  altered_learning_rate?: number
  altered_decay_rate?: number
  branch_name?: string
}): Promise<{
  branch_session: import('./types').ObservatorySession
}> {
  return json(`${BASE}/observatory/branch/counterfactual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function compareObservatorySessions(
  sessionAId: string,
  sessionBId: string,
): Promise<{
  comparison: import('./types').ObservatoryComparison
}> {
  return json(`${BASE}/observatory/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_a_id: sessionAId, session_b_id: sessionBId }),
  })
}

export function submitObservatoryPrediction(req: {
  session_id: string
  target_env: string
  predicted_category: string
  hypothesis: string
  confidence?: number
}): Promise<{
  prediction: import('./types').LearnerPrediction
}> {
  return json(`${BASE}/observatory/prediction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function exportObservatoryDetectiveCase(req: {
  session_id: string
  target_concept: string
  interference_step?: number
}): Promise<{
  detective_case_id: string
  title: string
  message: string
}> {
  return json(`${BASE}/observatory/export-to-detective`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function exportObservatorySessionJson(
  sessionId: string,
): Promise<Record<string, unknown>> {
  return json(`${BASE}/observatory/sessions/${encodeURIComponent(sessionId)}/export-json`)
}

// ==========================================
// Phase 20 Memory Genome & Synaptic Fingerprint API
// ==========================================

export function getFingerprintDemo(dimension: number = 16, seed: number = 42): Promise<{
  fingerprints: import('./types').SynapticFingerprint[]
  distance_map: import('./types').MemoryDistanceMap
  outliers: import('./types').OutlierReport[]
  challenges: import('./types').FingerprintChallenge[]
  concepts: string[]
}> {
  return json(`${BASE}/fingerprint/demo?dimension=${dimension}&seed=${seed}`)
}

export function computeFingerprint(req: {
  concept: string
  value?: string
  dimension?: number
  seed?: number
  update_strength?: number
  decay?: number
}): Promise<{
  fingerprint: import('./types').SynapticFingerprint
}> {
  return json(`${BASE}/fingerprint/compute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function compareFingerprints(req: {
  concept_a: string
  concept_b: string
  value_a?: string
  value_b?: string
  dimension?: number
  seed?: number
}): Promise<{
  fingerprint_a: import('./types').SynapticFingerprint
  fingerprint_b: import('./types').SynapticFingerprint
  comparison: import('./types').FingerprintComparison
}> {
  return json(`${BASE}/fingerprint/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getSurfaceVsInternal(req: {
  concepts: string[]
  dimension?: number
  seed?: number
}): Promise<{
  comparisons: import('./types').FingerprintComparison[]
  total_pairs: number
}> {
  return json(`${BASE}/fingerprint/surface-vs-internal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runCloningTest(req: {
  target_concept: string
  target_value?: string
  intervening_concept?: string
  intervening_value?: string
  dimension?: number
  seed?: number
}): Promise<{
  target_concept: string
  fingerprint_before: import('./types').SynapticFingerprint
  fingerprint_after: import('./types').SynapticFingerprint
  comparison: import('./types').FingerprintComparison
  stability_conclusion: string
}> {
  return json(`${BASE}/fingerprint/cloning-test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runCollisionMutation(req: {
  concept_a: string
  value_a?: string
  concept_b: string
  value_b?: string
  dimension?: number
  seed?: number
}): Promise<{
  concept_a: string
  concept_b: string
  fingerprint_a_before: import('./types').SynapticFingerprint
  fingerprint_b: import('./types').SynapticFingerprint
  fingerprint_a_after_collision: import('./types').SynapticFingerprint
  mutation_comparison: import('./types').FingerprintComparison
  interpretation: string
}> {
  return json(`${BASE}/fingerprint/collision-mutation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runFingerprintSurgery(req: {
  concept: string
  value?: string
  target_synapse: [number, number]
  new_weight: number
  dimension?: number
  seed?: number
}): Promise<{
  concept: string
  target_synapse: [number, number]
  weight_before: number
  weight_after: number
  fingerprint_before: import('./types').SynapticFingerprint
  fingerprint_after: import('./types').SynapticFingerprint
  comparison: import('./types').FingerprintComparison
  recall_fidelity_before: number
  recall_fidelity_after: number
}> {
  return json(`${BASE}/fingerprint/surgery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runCounterfactualFingerprint(req: {
  concept: string
  value?: string
  cf_update_strength: number
  dimension?: number
  seed?: number
}): Promise<{
  concept: string
  original_fingerprint: import('./types').SynapticFingerprint
  counterfactual_fingerprint: import('./types').SynapticFingerprint
  comparison: import('./types').FingerprintComparison
  divergence_summary: string
}> {
  return json(`${BASE}/fingerprint/counterfactual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getMemoryDistanceMap(dimension: number = 16, seed: number = 42): Promise<{
  distance_map: import('./types').MemoryDistanceMap
}> {
  return json(`${BASE}/fingerprint/distance-map?dimension=${dimension}&seed=${seed}`)
}

export function getFingerprintOutliers(dimension: number = 16, seed: number = 42): Promise<{
  outliers: import('./types').OutlierReport[]
}> {
  return json(`${BASE}/fingerprint/outliers?dimension=${dimension}&seed=${seed}`)
}

export function getMemoryFamilyTree(concept: string, dimension: number = 16, seed: number = 42): Promise<{
  family_tree: import('./types').MemoryBranchNode
}> {
  return json(`${BASE}/fingerprint/family-tree/${encodeURIComponent(concept)}?dimension=${dimension}&seed=${seed}`)
}

export function getFingerprintChallenges(): Promise<{
  challenges: import('./types').FingerprintChallenge[]
}> {
  return json(`${BASE}/fingerprint/challenges`)
}

export function verifyFingerprintChallenge(req: {
  challenge_id: string
  selected_option: string
}): Promise<{
  challenge_id: string
  is_correct: boolean
  correct_option: string
  explanation: string
}> {
  return json(`${BASE}/fingerprint/challenges/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function exportFingerprintJson(req: {
  concept: string
  value?: string
  dimension?: number
  seed?: number
  update_strength?: number
  decay?: number
}): Promise<Record<string, unknown>> {
  return json(`${BASE}/fingerprint/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// ---------------------------------------------------------------------------
// Phase 21: Memory Ecosystem / Unified Synaptic Memory World API
// ---------------------------------------------------------------------------

export function getEcosystemOverview(): Promise<import('./types').EcosystemOverview> {
  return json(`${BASE}/ecosystem/overview`)
}

export function getMemoryEcosystemDetails(memoryId: string): Promise<{
  passport: import('./types').MemoryPassport
  lifecycle: import('./types').MemoryLifecycle
  branch_tree: import('./types').MemoryBranch
  checkpoints: import('./types').MemoryCheckpoint[]
  ledger: import('./types').SynapticChangeLedger
}> {
  return json(`${BASE}/ecosystem/memory/${encodeURIComponent(memoryId)}`)
}

export function selectActiveMemory(memoryId: string, follow?: boolean): Promise<{
  success: boolean
  active_memory_id: string
  is_following: boolean
  passport: import('./types').MemoryPassport
}> {
  return json(`${BASE}/ecosystem/select-memory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ memory_id: memoryId, follow }),
  })
}

export function getUnifiedTimeline(memoryId?: string): Promise<{
  memory_id?: string
  total_events: number
  events: import('./types').UnifiedTimelineEvent[]
}> {
  const q = memoryId ? `?memory_id=${encodeURIComponent(memoryId)}` : ''
  return json(`${BASE}/ecosystem/timeline${q}`)
}

export function getMemoryRelationships(): Promise<{
  total_relationships: number
  relationships: import('./types').MemoryRelationship[]
}> {
  return json(`${BASE}/ecosystem/relationships`)
}

export function getSynapticChangeLedger(memoryId: string, transition?: string): Promise<{
  ledger: import('./types').SynapticChangeLedger
}> {
  const q = transition ? `?transition=${encodeURIComponent(transition)}` : ''
  return json(`${BASE}/ecosystem/ledger/${encodeURIComponent(memoryId)}${q}`)
}

export function submitLearnerHypothesis(req: {
  memory_id: string
  experiment_type: string
  prediction_text: string
  predicted_outcome: string
}): Promise<{
  hypothesis: import('./types').LearnerHypothesis
}> {
  return json(`${BASE}/ecosystem/hypothesis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function listLearnerHypotheses(memoryId?: string): Promise<{
  hypotheses: import('./types').LearnerHypothesis[]
}> {
  const q = memoryId ? `?memory_id=${encodeURIComponent(memoryId)}` : ''
  return json(`${BASE}/ecosystem/hypotheses${q}`)
}

export function createMemoryCheckpoint(req: {
  memory_id: string
  label: string
}): Promise<{
  checkpoint: import('./types').MemoryCheckpoint
}> {
  return json(`${BASE}/ecosystem/checkpoint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function listMemoryCheckpoints(memoryId: string): Promise<{
  memory_id: string
  checkpoints: import('./types').MemoryCheckpoint[]
}> {
  return json(`${BASE}/ecosystem/checkpoints/${encodeURIComponent(memoryId)}`)
}

export function compareMemoryStates(req: {
  state_a: Record<string, unknown>
  state_b: Record<string, unknown>
}): Promise<{
  comparison: {
    frobenius_drift: number
    active_ratio_shift: number
    shared_stability: number
    scientific_interpretation: string
  }
}> {
  return json(`${BASE}/ecosystem/compare-states`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function replayMemoryHistory(memoryId: string): Promise<{
  memory_id: string
  concept: string
  total_steps: number
  playback_steps: {
    step_index: number
    event_type: string
    title: string
    description: string
    producing_experiment: string
    session_time: string
    metrics: Record<string, unknown>
    is_simplification: boolean
    label: string
  }[]
  disclaimer: string
}> {
  return json(`${BASE}/ecosystem/replay/${encodeURIComponent(memoryId)}`)
}

// ==========================================
// Phase 22 Experiment Studio API
// ==========================================

export function getStudioTemplates(): Promise<{
  templates: import('./types').StudioExperimentTemplate[]
  count: number
}> {
  return json(`${BASE}/studio/templates`)
}

export function getStudioGuidedJourney(): Promise<{
  journey: import('./types').StudioGuidedJourney
}> {
  return json(`${BASE}/studio/guided-journey`)
}

export function runStudioExperiment(req: {
  config: import('./types').StudioExperimentConfig
  hypothesis?: import('./types').StudioHypothesis
  notes?: import('./types').StudioExperimentNote | Record<string, string>
}): Promise<{
  result: import('./types').StudioExperimentResult
}> {
  return json(`${BASE}/studio/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function compareStudioAB(req: {
  config_a: import('./types').StudioExperimentConfig
  config_b: import('./types').StudioExperimentConfig
}): Promise<{
  comparison: import('./types').StudioABComparison
}> {
  return json(`${BASE}/studio/ab-compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function runStudioSweep(req: {
  base_config: import('./types').StudioExperimentConfig
  param_name: string
  param_values?: number[]
}): Promise<{
  sweep: import('./types').StudioSweepResult
}> {
  return json(`${BASE}/studio/sweep`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function listStudioHistory(): Promise<{
  history: import('./types').StudioHistoryItem[]
  total: number
}> {
  return json(`${BASE}/studio/history`)
}

export function getStudioExperiment(experimentId: string): Promise<{
  experiment: import('./types').StudioExperimentResult
  notes: import('./types').StudioExperimentNote
}> {
  return json(`${BASE}/studio/experiment/${encodeURIComponent(experimentId)}`)
}

export function branchStudioExperiment(req: {
  experiment_id: string
  modified_param: string
  new_value: unknown
}): Promise<{
  result: import('./types').StudioExperimentResult
}> {
  return json(`${BASE}/studio/branch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function saveStudioNotes(req: {
  experiment_id: string
  question: string
  hypothesis: string
  observation: string
  conclusion: string
}): Promise<{
  status: string
  notes: import('./types').StudioExperimentNote
}> {
  return json(`${BASE}/studio/save-notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function exportStudioExperiment(experimentId: string): Promise<Record<string, unknown>> {
  return json(`${BASE}/studio/export/${encodeURIComponent(experimentId)}`)
}

// ==========================================
// Phase 23 Scientific Evidence & Research API
// ==========================================

export function listResearchPapers(tag?: string): Promise<{
  papers: import('./types').PrimaryResearchPaper[]
  total: number
  available_tags: string[]
}> {
  const q = tag && tag !== 'ALL' ? `?tag=${encodeURIComponent(tag)}` : ''
  return json(`${BASE}/research/papers${q}`)
}

export function getResearchPaper(paperId: string): Promise<{
  paper: import('./types').PrimaryResearchPaper
}> {
  return json(`${BASE}/research/papers/${encodeURIComponent(paperId)}`)
}

export function listResearchClaims(): Promise<{
  claims: import('./types').ClaimTrace[]
  total: number
}> {
  return json(`${BASE}/research/claims`)
}

export function listResearchMetrics(): Promise<{
  metrics: import('./types').MetricDefinition[]
  total: number
}> {
  return json(`${BASE}/research/metrics`)
}

export function getResearchGraph(): Promise<import('./types').ResearchGraphData> {
  return json(`${BASE}/research/graph`)
}

export function getResearchDisclosures(): Promise<import('./types').DisclosuresData> {
  return json(`${BASE}/research/disclosures`)
}

export function listResearchLicenses(): Promise<{
  licenses: import('./types').SourceLicenseRecord[]
  total: number
}> {
  return json(`${BASE}/research/licenses`)
}

export function generateExperimentMethodology(req: {
  experiment_type: string
  config: Record<string, unknown>
}): Promise<{
  methodology: import('./types').MethodologyData
}> {
  return json(`${BASE}/research/methodology`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}