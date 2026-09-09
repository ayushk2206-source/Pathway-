// TypeScript definitions for Neural Archaeology Command Center UI (Phase 06).
// Every visual element and metric reflects real computational backend state.

export interface MechanismParams {
  state_dim: number
  update_strength: number
  memory_strength: number
  decay: number
  interference_strength: number
  sparsity: number
  normalize_state: boolean
  input_noise: number
}

export interface TaskConfig {
  seed?: number | null
  d: number
  n_objects: number
  n_symbols: number
  n_conflicts: number
  object_similarity: number
  symbol_similarity: number
  cycles: number
  order: 'structured' | 'interleaved' | 'randomized'
  probe_original: boolean
  input_noise: number
}

export interface RunRequest {
  seed: number
  mechanism: string
  params: MechanismParams
  task: TaskConfig
  update_steps_per_event: number
}

export interface QueryRecord {
  query_id: string
  timestep: number
  object_label: string
  kind: string
  predicted_label: string
  truth_label: string
  confidence: number
  correctness: boolean
  quality: number
}

export interface Snapshot {
  timestep: number
  event_id: string | null
  state_vector: number[]
  shape: number[]
  norm: number
  active_dimensions: number[]
  num_active: number
  sparsity: number
  mechanism: string
  trace: Record<string, unknown>
  query_results?: QueryRecord[]
}

export interface ExperimentEvent {
  id: string
  timestep: number
  concept_label: string
  attribute_label: string
  key_vector?: number[]
  value_vector?: number[]
}

export interface Experiment {
  experiment_id: string
  seed: number
  mechanism: string
  parameters: MechanismParams
  config: Record<string, unknown>
  task: {
    d: number
    events: { id: string; concept_label: string; attribute_label: string }[]
    last_write: Record<string, [number, string]>
    conflicts: Record<string, unknown>
  }
  events: ExperimentEvent[]
  snapshots: Snapshot[]
  queries: QueryRecord[]
  predictions: QueryRecord[]
  ground_truth: { query_id: string; truth_label: string }[]
  metrics: Record<string, number | null | Record<string, unknown>>
  created_at: string
  version: number
  replay_of: string | null
}

export interface ExperimentSummary {
  experiment_id: string
  mechanism: string
  created_at: string
  num_events: number
  parameters: MechanismParams
  metrics: Record<string, unknown>
  version: number
}

export interface Health {
  status: string
  core_version: string
  schema_version: number
  mechanisms: string[]
}

export interface MechanismInfo {
  name: string
  description: string
  state_is_matrix: boolean
}

// ==========================================
// Phase 05 Memory X-Ray & Analytics Types
// ==========================================

export interface MemorySnapshot {
  snapshot_id: string
  experiment_id: string
  timeline_step: number
  event_id: string | null
  timestamp: string
  state_vector: number[]
  active_units: number[]
  inactive_units: number[]
  sparsity: number
  memory_strength: Record<string, number>
  associations: Record<string, string[]>
  similarity_statistics: {
    mean_sim?: number
    max_sim?: number
    min_sim?: number
    std_sim?: number
  }
}

export interface StateTrajectory {
  experiment_id: string
  steps: number
  dimension: number
  final_norm: number
  cumulative_drift: number
  delta_norms: number[]
  cosine_distances: number[]
}

export interface StateComparison {
  l1_distance: number
  l2_distance: number
  cosine_distance: number
  cosine_similarity: number
  relative_l2: number
}

export interface ActivationProfile {
  step: number
  dimension: number
  mean: number
  std: number
  min: number
  max: number
  l1_norm: number
  l2_norm: number
  sparsity: number
  quantiles: {
    p10: number
    p25: number
    p50: number
    p75: number
    p90: number
  }
  entropy: number
}

export interface SparsityAnalysis {
  experiment_id: string
  dimension: number
  timeline_sparsity: number[]
  mean_sparsity: number
  min_sparsity: number
  max_sparsity: number
  active_units_per_step: number[]
  dead_units: number[]
  dead_units_count: number
  trend: string
}

export interface MemoryStrengthProfile {
  memory_id: string
  concept_label: string
  initial_strength: number
  peak_strength: number
  final_strength: number
  timeline_strengths: number[]
  history?: number[]
  decay_rate: number
  reinforcement_count: number
  pattern: 'EXPONENTIAL' | 'POWER_LAW' | 'LINEAR' | 'NO_DECAY'
}

export interface ReinforcementRecord {
  memory_id: string
  reinforcement_events: string[]
  strength_before: number
  strength_after: number
  net_change: number
  strengthening_ratio: number
}

export interface InterferenceRecord {
  target_memory_id: string
  competing_memory_id: string
  event_id: string
  similarity: number
  strength_before: number
  strength_after: number
  degradation: number
}

export interface GraphEdge {
  source: string
  target: string
  relationship: 'COMPETITION' | 'ASSOCIATION' | 'REINFORCEMENT' | 'INDEPENDENT'
  weight: number
  confidence: number
}

export interface MemoryRelationshipGraph {
  nodes: {
    id: string
    label: string
    strength: number
    cluster: number
  }[]
  edges: GraphEdge[]
  density: number
  average_degree: number
}

export interface ClusterResult {
  cluster_id: number
  members: string[]
  centroid: number[]
  cohesion: number
  separation: number
}

export interface MemoryMapPoint {
  x: number
  y: number
  memory_id: string
  label: string
  strength: number
  cluster: number
  trajectory_tail?: number[][]
}

export interface MemoryMap2D {
  points: MemoryMapPoint[]
  variance_explained: number[]
  projection_method: string
  disclaimer: string
}

// ---------------------------------------------------------------------------
// Phase 15: Synaptic Surgery & Memory X-Ray types
// ---------------------------------------------------------------------------

export interface SurgeryOperation {
  op_id: string
  operation: 'silence' | 'weaken' | 'strengthen' | 'restore' | 'restore_all'
  synapse_ids: string[]
  factor: number | null
  timestamp_step: number
  weight_deltas: Record<string, number>
  description: string
}

export interface SurgeryRecallComparison {
  query_concept: string
  expected_value: string | null
  baseline: {
    predicted: string | null
    confidence: number
    fidelity: number
    readout_norm: number
    top_synapse_ids: string[]
  }
  surgery: {
    predicted: string | null
    confidence: number
    fidelity: number
    readout_norm: number
    top_synapse_ids: string[]
  }
  change: {
    delta_confidence: number
    delta_fidelity: number
    delta_readout_norm: number
    agreement: boolean
  }
  operations_applied: number
  experiment_label: string
  caution_note: string
}

export interface SurgerySession {
  session_id: string
  seed: number
  d: number
  mechanism: string
  baseline_timestep: number
  surgery_op_count: number
  operations: SurgeryOperation[]
  last_comparison: SurgeryRecallComparison | null
  library_size: number
  surgery_matrix_norm: number
  baseline_matrix_norm: number
}

export interface SynapseXRay {
  synapse_id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  current_weight: number
  baseline_weight: number
  weight_before: number
  delta_weight: number
  abs_weight: number
  tier: string
  polarity: string
  relevance_score: number
  relevance_tier: 'high' | 'moderate' | 'weak' | 'unrelated'
  k_query_component: number
  contribution_to_readout: number
  last_update_timestep: number
  plasticity_trace: number
}

export interface MemoryXRay {
  query_concept: string
  expected_value: string | null
  dimension: number
  seed: number
  branch?: string
  summary: {
    total_synapses_analyzed: number
    highly_relevant: number
    moderately_relevant: number
    weakly_relevant: number
    unrelated: number
  }
  synapses: SynapseXRay[]
  readout: {
    norm: number
    top_confidence: number
    predicted_value: string | null
  }
  transparency: {
    metric_description: string
    disclaimer: string
  }
}

export interface SynapseXRayDetail {
  synapse_id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  baseline_weight: number
  surgery_weight: number
  weight_delta: number
  abs_baseline: number
  abs_surgery: number
  is_modified: boolean
  operations_applied: SurgeryOperation[]
  disclaimer: string
}

export interface MemoryTrace {
  memory_id: string
  concept_label: string
  stages: {
    stage: string
    step: number
    event_id: string
    strength: number
    evidence: string
  }[]
  current_stage: string
  strength_history: number[]
  decay_rate: number
  reinforcement_count: number
  primary_competitor: string | null
  influenced_memories?: Record<string, number>
}

export interface EventImpact {
  event_id: string
  event_index: number
  state_delta_norm: number
  cosine_shift: number
  affected_memories_count: number
  dominant_dimensions: number[]
}

export interface DiagnosticsProfile {
  health_score: number
  capacity_headroom: number
  interference_risk: number
  decay_vulnerability: number
  mean_memory_strength: number
  stability_index: number
}

export interface AnomalyRecord {
  anomaly_type: 'SUDDEN_JUMP' | 'ABNORMAL_DROP' | 'SATURATION' | 'DIMENSION_COLLAPSE'
  step: number
  event_id: string
  severity: number
  description: string
  metric_value: number
  baseline_value: number
  deviation: number
}

export interface MemoryExplanation {
  memory_id: string
  concept_label: string
  current_strength: number
  summary: string
  evidence: string[]
  mitigating_factors: string[]
  aggravating_factors: string[]
}

export interface EventInspector {
  event_index: number
  event_id: string
  concept_label: string
  attribute_label: string
  before_norm: number
  after_norm: number
  delta_norm: number
  cosine_shift: number
  strengthened_memories: string[]
  weakened_memories: string[]
  top_shifted_dimensions: {
    unit: number
    delta: number
    abs_delta: number
  }[]
}

export interface SurgeryDiff {
  original_experiment_id: string
  counterfactual_experiment_id: string
  original_map: MemoryMap2D
  counterfactual_map: MemoryMap2D
  point_shifts: {
    memory_id: string
    label: string
    orig_coords: number[]
    cf_coords: number[]
    shift_magnitude: number
    strength_delta: number
  }[]
  topological_edges: {
    original_edge_count: number
    counterfactual_edge_count: number
    added_edges: GraphEdge[]
    removed_edges: GraphEdge[]
  }
  summary: string
}

export interface XRayReport {
  experiment_id: string
  generated_at: string
  summary: string
  findings: string[]
  anomalies: AnomalyRecord[]
  recommendations: string[]
  evidence_citations: {
    step: number
    metric: string
    value: number
  }[]
}

// ==========================================
// Phase 04 Counterfactual Archaeology Types
// ==========================================

export interface CounterfactualExperiment {
  counterfactual_id: string
  parent_experiment_id: string
  parent_history_id?: string
  title: string
  description: string
  original_configuration: Record<string, unknown>
  intervention: Record<string, unknown>
  intervention_type: string
  intervention_target: unknown
  intervention_parameters: Record<string, unknown>
  original_result: {
    metrics: Record<string, unknown>
    final_state_norm: number
    num_events: number
  }
  counterfactual_result: {
    metrics: Record<string, unknown>
    final_state_norm: number
    num_events: number
    experiment_id?: string
    experiment?: Experiment
  }
  comparison: {
    state_distance_l2: number
    cosine_similarity: number
    relative_l2: number
    first_divergence_step: number | null
    divergence_classification: string
    explanation: string
  }
  divergence: {
    timeline_steps: number[]
    distances_l2: number[]
    cosine_similarities: number[]
    first_divergence_step: number | null
    peak_divergence_step: number | null
    classification: string
  }
  provenance: Record<string, unknown>
  created_at: string
  status: string
}

export interface HeatmapsData {
  time_steps: number[]
  memories: string[]
  memory_matrix: number[][]
  units: number[]
  unit_matrix: number[][]
}

// ==========================================
// Phase 07 Memory Detective & Hypothesis Types
// ==========================================

export interface MeasurableObservation {
  observation_id: string
  target_memory?: string | null
  target_event?: string | null
  metric_name: string
  initial_value: number
  final_value: number
  delta: number
  baseline_value?: number
  observed_value?: number
  relevant_events: string[]
  competing_memories: string[]
  cue_similarity?: number | null
  state_shift?: number | null
  summary: string
  raw_data?: Record<string, unknown>
}

export interface CandidateHypothesis {
  hypothesis_id: string
  statement: string
  mechanism: string
  is_primary: boolean
  supporting_evidence: string[]
  contradicting_evidence: string[]
  required_test: string
  status: 'OBSERVED' | 'CORRELATED' | 'COUNTERFACTUALLY_SUPPORTED' | 'UNSUPPORTED' | 'CONTRADICTED'
  classification: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'INCONCLUSIVE' | 'REFUTED'
  supporting_evidence_count: number
  contradicting_evidence_count: number
  counterfactual_support: number
  alternative_explanations: string[]
  competing_alternatives?: string[]
  data_quality: number
  explanation_score: number
}

export interface TestDesign {
  test_id: string
  hypothesis_id: string
  description: string
  control_description: string
  intervention_description: string
  intervention_type: string
  target_timestep?: number | null
  target_event_id?: string | null
  parameters: Record<string, unknown>
  target_memory?: string | null
}

export interface TestResult {
  test_id: string
  hypothesis_id: string
  control_trajectory: number[]
  intervention_trajectory: number[]
  first_divergence_step?: number | null
  divergence_magnitude: number
  control_outcome_strength: number
  intervention_outcome_strength: number
  recovery_delta: number
  causal_support: string
  evidence_summary: string
  affected_memories: string[]
  divergence_classification: string
}

export interface EvidenceChain {
  hypothesis_id: string
  steps: Record<string, unknown>[]
  verdict: string
}

export interface MemoryBirthRecord {
  memory_id: string
  concept_label: string
  first_appearance_step: number
  first_event_id: string
  initial_strength: number
  initial_state_norm: number
  early_associations: string[]
  early_competitors: string[]
  trajectory_preview: number[]
}

export interface MemoryDeathRecord {
  memory_id: string
  concept_label: string
  last_strong_step: number
  last_strong_strength: number
  effective_loss_step: number
  final_strength: number
  decline_events: string[]
  dominant_contributor: string
  counterfactual_survival_possible: boolean
  evidence: string
}

export interface MemoryAutopsy {
  memory_id: string
  concept_label: string
  formation: {
    concept_label?: string
    appearance_step: number
    event_id: string
    initial_strength: number
    initial_state_norm: number
  }
  reinforcement: {
    count: number
    reinforcement_count: number
    events: string[]
    average_boost: number
  }
  competition: {
    competing_count: number
    competing_memories_count: number
    primary_competitor?: { memory_id: string; label: string; similarity: number } | null
    all_competitors: { memory_id: string; label: string; similarity: number }[]
  }
  weakening_inflection?: {
    step: number
    drop: number
    culprit_event: string
    pre_strength: number
    post_strength: number
  } | null
  survival_factors: string[]
  counterfactual_removal_impact: Record<string, unknown>
  failure_profile?: {
    memory_id: string
    strength_drop: number
    conflicting_writes_count: number
    failure_causes: string[]
    is_failed: boolean
  } | null
  survival_profile?: {
    memory_id: string
    initial_strength: number
    final_strength: number
    retention_ratio: number
    survival_reasons: string[]
    is_surviving: boolean
  } | null
  supporting_evidence: string[]
}

export interface SensitivityRecord {
  memory_id: string
  perturbation: string
  interfering_event_id?: string | null
  effect_size: number
  direction: string
  isolated_cause: boolean
  downstream_affected_count: number
  counterfactual_tested: boolean
}

export interface MinimumIntervention {
  target_memory: string
  target_outcome: string
  smallest_intervention_type: string
  parameter_threshold: number
  effect_size: number
  intervention_details: Record<string, unknown>
}

export interface RobustnessEvaluation {
  memory_id: string
  classification: string
  variations_tested: number
  variance: number
  persistence_rate: number
}

export interface DiscoveryObservation {
  discovery_id: string
  experiment_id: string
  title: string
  description: string
  category: string
  target_memory?: string | null
  relevant_events: string[]
  metrics: Record<string, number>
  novelty: string
  seed_question: string
}

export interface NotebookEntry {
  entry_id: string
  experiment_id: string
  investigation_id?: string | null
  timestamp: string
  title: string
  notes: string
  content?: string
  author: string
  tags: string[]
  linked_entities: Record<string, unknown>
  conclusion: string
}

export interface InvestigationScorecard {
  investigation_id: string
  experiment_id: string
  question: string
  primary_hypothesis: string
  verdict: string
  counterfactual_evidence: string[]
  supporting_evidence_count: number
  alternative_explanations: string[]
  epistemic_limitations: string[]
  conclusion: string
}

export interface Investigation {
  investigation_id: string
  experiment_id: string
  question: string
  intent: string
  target_memory?: string | null
  target_event?: string | null
  observations: MeasurableObservation[]
  candidate_hypotheses: CandidateHypothesis[]
  tests: TestDesign[]
  results: TestResult[]
  evidence_chain: EvidenceChain[]
  status: 'OBSERVING' | 'HYPOTHESIZING' | 'TESTING' | 'CONFIRMED' | 'REFUTED' | 'INCONCLUSIVE'
  created_at: string
  reproduced_from?: string | null
  scorecard?: InvestigationScorecard | null
}

// ============================================================================
// Phase 08: Memory Genome + Cascade Engine
// ============================================================================

export type CascadeEffectType = 'DIRECT' | 'SECONDARY' | 'TERTIARY' | 'UNCHANGED'
export type DoseResponsePattern = 'LINEAR' | 'THRESHOLD' | 'RESILIENT' | 'FRAGILE'
export type FragilityClassification = 'CRITICAL' | 'REDUNDANT' | 'ISOLATED' | 'BALANCED'
export type RecoveryStatus = 'PERMANENT' | 'RECOVERED' | 'RESIDUAL_DAMAGE'
export type OrderSensitivity = 'ORDER_SENSITIVE' | 'ORDER_ROBUST'

export interface AssociationEntry {
  target_memory: string
  concept_label: string
  similarity: number
}

export interface CompetitorEntry {
  target_memory: string
  concept_label: string
  similarity: number
  overlap_score: number
}

export interface ReinforcementRecord {
  step: number
  event_id: string
  strength_before: number
  strength_after: number
  delta: number
}

export interface RetrievalRecord {
  step: number
  event_id: string
  fidelity: number
  success: boolean
}

export interface GenomeDNAStrip {
  origin_bias: number
  reinforcement_level: number
  association_density: number
  competition_pressure: number
  retrieval_resilience: number
  historical_drift: number
  downstream_criticality: number
  fragility_index: number
}

export interface MemoryGenome {
  memory_id: string
  concept_label: string
  origin_event: string
  origin_step: number
  formation_events: string[]
  associations: AssociationEntry[]
  competitors: CompetitorEntry[]
  reinforcement_history: ReinforcementRecord[]
  retrieval_history: RetrievalRecord[]
  state_dependencies: string[]
  downstream_influence: string[]
  trajectory: number[]
  current_strength: number
  stability: number
  sensitivity: number
  influence_score: number
  dna_strip: GenomeDNAStrip
  provenance: Record<string, unknown>
}

export interface MemoryLineageNode {
  id: string
  label: string
  node_type: string
  step: number
  details?: Record<string, unknown>
}

export interface MemoryLineageEdge {
  source: string
  target: string
  relation: string
  strength: number
}

export interface MemoryLineageGraph {
  nodes: MemoryLineageNode[]
  edges: MemoryLineageEdge[]
  root_id: string
}

export interface CascadeNode {
  memory_id: string
  concept_label: string
  effect_type: CascadeEffectType
  original_strength: number
  counterfactual_strength: number
  strength_delta: number
  cascade_depth: number
  step_affected: number
  divergence_delta: number
}

export interface CascadeMap {
  target_memory: string
  intervention: string
  dose: number
  nodes: Record<string, CascadeNode>
  cascade_depth: number
  total_affected: number
  direct_affected_count: number
  secondary_affected_count: number
  tertiary_affected_count: number
  cascade_magnitude: number
  first_divergence_step: number
  divergence_order: string[]
}

export interface InfluenceBreakdown {
  target_memory: string
  reach_score: number
  magnitude_score: number
  depth_score: number
  persistence_score: number
  composite_influence: number
  normalized_rank?: number
}

export interface CentralityRecord {
  memory_id: string
  concept_label: string
  in_degree: number
  out_degree: number
  eigenvector: number
  betweenness: number
  centrality_score: number
}

export interface CriticalMemoryRank {
  memory_id: string
  concept_label: string
  system_disruption: number
  affected_count: number
  classification: FragilityClassification
}

export interface FragilityReport {
  target_memory: string
  classification: FragilityClassification
  single_point_of_failure: boolean
  downstream_loss_if_removed: number
  system_coherence_drop: number
  compensation_available: boolean
  explanation: string
}

export interface RedundancyRecord {
  target_memory: string
  concept_label: string
  is_redundant: boolean
  backup_memories: string[]
  backup_scores: number[]
  functional_overlap_score: number
  safe_to_prune: boolean
}

export interface DosePoint {
  dose: number
  remaining_strength: number
  system_divergence: number
}

export interface DoseResponseEvaluation {
  target_memory: string
  points: DosePoint[]
  pattern: DoseResponsePattern
  inflection_detected: boolean
  threshold_dose?: number | null
  explanation: string
}

export interface RecoveryEvaluation {
  target_memory: string
  before_intervention: number
  during_intervention: number
  after_recovery: number
  status: RecoveryStatus
  residual_damage: number
  explanation: string
}

export interface PathDependenceEvaluation {
  sequence_a: string[]
  sequence_b: string[]
  final_distance_l2: number
  order_sensitivity: OrderSensitivity
  diverging_memories: string[]
}

export interface SandboxBranch {
  branch_id: string
  parent_id: string
  experiment_id: string
  created_at: string
  intervention: Record<string, unknown>
  snapshots_count: number
  final_divergence_l2: number
  state_summary?: Record<string, unknown>
}

export interface DependencyMatrix {
  experiment_id: string
  metric: string
  memory_ids: string[]
  labels: string[]
  matrix: number[][]
}

export interface GenomeReport {
  memory_id: string
  concept_label: string
  experiment_id: string
  timestamp: string
  origin_summary: string
  current_strength: number
  stability: number
  sensitivity: number
  associations_count: number
  competitors_count: number
  reinforcements_count: number
  retrievals_count: number
  dna_strip: GenomeDNAStrip
  fragility_status: string
  proactive_recommendations: string[]
}

export interface CascadeReport {
  target_memory: string
  intervention: string
  dose: number
  timestamp: string
  cascade_depth: number
  cascade_magnitude: number
  first_divergence_step: number
  affected_counts: Record<string, number>
  top_disrupted_memories: Array<{ memory_id: string; delta: number; effect: string }>
  quantitative_summary: string
}

// ============================================================================
// Phase 09: Autonomous Discovery Engine / Agency Workspace
// ============================================================================

export interface AgentOutputRecord {
  agent: string
  mission_id: string
  assumptions: string[]
  analysis: string
  evidence: Record<string, unknown>[]
  objections: string[]
  recommendation: string
  verdict: string
  confidence: number
  proposed_next_action?: string | null
  provenance: Record<string, unknown>
  created_at: string
}

export interface DisagreementRecord {
  disagreement_id: string
  agent_a: string
  agent_b: string
  topic: string
  underlying_issue: string
  resolved: boolean
  resolution_experiment_id?: string | null
}

export interface SynthesisRecord {
  verdict: string
  summary: string
  recommendation: string
  confidence: number
  supporting_evidence_count: number
  open_objections: string[]
}

export interface ResearchInvestigation {
  investigation_id: string
  research_question: string
  status: string
  round_number: number
  initial_hypotheses: Record<string, unknown>[]
  active_hypotheses: Record<string, unknown>[]
  experiments: Record<string, unknown>[]
  counterfactuals: Record<string, unknown>[]
  agent_missions: Record<string, unknown>[]
  agent_outputs: AgentOutputRecord[]
  observations: Record<string, unknown>[]
  disagreements: DisagreementRecord[]
  synthesis: SynthesisRecord | Record<string, unknown>
  unresolved_questions: string[]
  next_actions: string[]
  provenance: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface WarRoomStation {
  name: string
  role: string
  current_status: string
  last_action: string
  confidence?: number | null
  verdict?: string | null
  objection_count?: number
}

export interface WarRoomState {
  investigation_id: string
  question: string
  status: string
  round_number: number
  stations: Record<string, WarRoomStation>
  consensus_meter: number
  timeline: string[]
}

export interface AgentCatalogEntry {
  slug: string
  name: string
  division: string
  vibe: string
  attribution: string
  instructions: string
}

export interface AgentCatalogResponse {
  total: number
  agents: AgentCatalogEntry[]
}

// ============================================================================
// Phase 01: Live Synaptic Brain Types
// ============================================================================

export interface SynapticNeuron {
  id: string
  index: number
  neuron_type: 'input_key' | 'output_value' | 'state_unit'
  label: string
  activation: number
  baseline_activation: number
  inflow_weight: number
  outflow_weight: number
  dominant_concepts: string[]
}

export interface SynapticConnection {
  id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  weight: number
  weight_before: number
  delta_weight: number
  abs_weight: number
  tier: 'weak' | 'medium' | 'strong'
  polarity: 'excitatory' | 'inhibitory' | 'neutral'
  plasticity_trace: number
  last_update_timestep: number
}

export interface SynapticPathway {
  active_key_indices: number[]
  active_value_indices: number[]
  active_synapse_ids: string[]
  transmission_energy: number
}

export interface SynapticExplanation {
  event_label: string
  event_type: 'WRITE' | 'RECALL' | 'DECAY' | 'INIT'
  active_units: number
  synaptic_updates: number
  mean_weight_change: number
  max_weight_change: number
  state_change_pct: number
  norm_before: number
  norm_after: number
  write_gain: number
  decay_applied: number
  scientific_note: string
}

export interface SynapticRecallCandidate {
  memory_id: string
  concept: string
  value: string
  similarity: number
}

export interface SynapticRecallResult {
  query_concept: string
  predicted_value: string | null
  confidence: number
  ground_truth: string | null
  is_correct: boolean | null
  candidate_matches: SynapticRecallCandidate[]
  fidelity: number
  crosstalk_noise: number
  readout_vector: number[]
}

export interface SynapticTimelineEvent {
  step: number
  event_type: string
  label: string
  matrix_norm: number
  active_synapses: number
  details: Record<string, unknown>
}

export interface SynapticNetworkState {
  timestep: number
  dimension: number
  mechanism: string
  total_synapses: number
  active_synapses_count: number
  mean_synaptic_weight: number
  max_synaptic_weight: number
  matrix_norm: number
  sparsity: number
  neurons: SynapticNeuron[]
  synapses: SynapticConnection[]
  last_pathway: SynapticPathway | null
  last_explanation: SynapticExplanation | null
  last_recall: SynapticRecallResult | null
  history_timeline: SynapticTimelineEvent[]
  matrix_weights?: number[][] | null
}

export interface SynapseHistoryPoint {
  step: number
  weight: number
  abs_weight: number
  event_type: string
  label: string
}

export interface SynapseHistory {
  synapse_id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  initial_weight: number
  max_weight: number
  current_weight: number
  total_change: number
  update_count: number
  history: SynapseHistoryPoint[]
}

export interface MemoryTrailPoint {
  step: number
  fidelity: number
  strength: number
  readout_norm: number
  event_type: string
  label: string
  active_synapses: string[]
}

export interface MemoryHistory {
  concept: string
  value: string
  written_step: number
  peak_synaptic_strength: number
  current_strength: number
  retention_rate: number
  recall_fidelity: number
  trail: MemoryTrailPoint[]
}

export interface SynapseDelta {
  synapse_id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  weight_a: number
  weight_b: number
  delta_weight: number
  mag_change: number
}

export interface StateDiffResult {
  step_a: number
  step_b: number
  step_a_label: string
  step_b_label: string
  frobenius_norm_delta: number
  mean_abs_delta: number
  max_delta: number
  strengthened_count: number
  weakened_count: number
  unchanged_count: number
  top_changes: SynapseDelta[]
  delta_matrix: number[][]
}

export interface TimeMachineHistoryResponse {
  total_steps: number
  current_timestep: number
  timeline: SynapticTimelineEvent[]
  active_synapses_count: number
  matrix_norm: number
}

export interface TimeMachineProtocolResponse {
  status: string
  protocol_name: string
  steps_count: number
  timeline: Array<{ step: number; label: string; event_type: string }>
  current_state: SynapticNetworkState
}

export interface SynapticInfo {
  title: string
  topic: string
  description: string
  mathematical_model: {
    hebbian_write: string
    associative_recall: string
    decay_rule: string
    similarity_metric: string
  }
  disclaimer: string
}

// ==========================================
// Phase 16 Counterfactual / What-If Engine Types
// ==========================================

export interface SynapticInterventionPayload {
  experiment_id: string
  intervention_type: 'synapse_prevent_strengthen' | 'synapse_silence' | 'synapse_scale' | 'change_decay' | 'change_plasticity'
  synapse_id?: string
  target_timestep?: number
  factor?: number
  new_decay?: number
  new_update_strength?: number
  title?: string
  hypothesis?: string
}

export interface SynapticInterventionResponse {
  status: string
  counterfactual: CounterfactualExperiment
  counterfactual_id: string
  branch_point: number
  variable_controlled: string
  metrics_original: Record<string, number>
  metrics_counterfactual: Record<string, number>
}

export interface SynapticDeltaItem {
  synapse_id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  original_weight: number
  counterfactual_weight: number
  delta: number
  abs_delta: number
  polarity_change: 'strengthened' | 'weakened'
}

export interface QueryOutcomeComparison {
  query_id: string
  object_label: string
  original_prediction: string | null
  counterfactual_prediction: string | null
  truth_label?: string | null
  original_confidence: number
  counterfactual_confidence: number
  confidence_delta: number
  outcome_diverged: boolean
}

export interface SynapticCompareResponse {
  step_idx: number
  divergence_step: number | null
  is_post_divergence: boolean
  matrix_frobenius_delta: number
  max_synaptic_delta: number
  changed_synapses_count: number
  original_network: SynapticNetworkState
  counterfactual_network: SynapticNetworkState
  synaptic_deltas: SynapticDeltaItem[]
  outcome_deltas: Record<string, { original: number; counterfactual: number; delta: number }>
  query_comparison: QueryOutcomeComparison[]
  variable_controlled: string
}

export interface ExperimentBranchSummary {
  branch_id: string
  title: string
  description: string
  intervention_type: string
  divergence_step: number
  target_synapse?: string
  original_accuracy?: number
  counterfactual_accuracy?: number
  accuracy_delta: number
  created_at: string
  status: string
}

export interface ExperimentBranchesResponse {
  experiment_id: string
  total_branches: number
  branches: ExperimentBranchSummary[]
}

// ---------------------------------------------------------------------------
// Phase 17: Memory Collision & Interference Lab Types
// ---------------------------------------------------------------------------

export interface CollisionMemory {
  concept: string
  value: string
  importance: number
  strength: number
}

export interface CollisionConfig {
  seed: number
  dimension: number
  decay: number
  update_strength: number
  memory_a: CollisionMemory
  memory_b: CollisionMemory
  memory_c?: CollisionMemory | null
  order: 'A_THEN_B' | 'B_THEN_A'
  temporal_delay: number
  overlap_preset: 'LOW' | 'MODERATE' | 'HIGH' | 'CUSTOM'
  concept_similarity: number
}

export interface SynapticPathwayClassification {
  synapse_id: string
  source: string
  target: string
  source_idx: number
  target_idx: number
  classification: 'A_ONLY' | 'B_ONLY' | 'SHARED' | 'UNCHANGED'
  weight_after_first: number
  weight_delta_second: number
  final_weight: number
  overwrite_magnitude: number
}

export interface CollisionRecallStats {
  concept: string
  value: string
  fidelity: number
  strength: number
  readout_norm: number
  is_correct: boolean
  crosstalk_leakage?: number
  gain?: number
  matrix_norm?: number
}

export interface CollisionTimelineStep {
  step: number
  event_type: string
  label: string
  concept?: string
  matrix_weights?: number[][]
  matrix_norm: number
  delta_norm?: number
  fidelity?: number
  crosstalk?: number
}

export interface CollisionResult {
  collision_id: string
  config: CollisionConfig
  representational_overlap: number
  synaptic_overlap_fraction: number
  matrix_correlation: number
  timeline: CollisionTimelineStep[]
  isolated_recall_a: CollisionRecallStats
  isolated_recall_b: CollisionRecallStats
  combined_recall_a: CollisionRecallStats
  combined_recall_b: CollisionRecallStats
  computational_interference_a: number
  computational_interference_b: number
  overall_computational_interference: number
  memory_dominance: 'MEMORY_A' | 'MEMORY_B' | 'BALANCED'
  dominant_memory_margin: number
  a_only_synapses: string[]
  b_only_synapses: string[]
  shared_synapses: string[]
  collision_map: SynapticPathwayClassification[]
  experiment_report: {
    question: string
    conditions: Record<string, unknown>
    overlap_measure: Record<string, unknown>
    results: Record<string, unknown>
    interpretation: string
  }
  final_network_state: SynapticNetworkState
  isolated_recall_c?: CollisionRecallStats | null
  combined_recall_c?: CollisionRecallStats | null
}

export interface RecallMatrixRow {
  condition: string
  concept_similarity: number
  representational_overlap: number
  synaptic_overlap_fraction: number
  recall_a: number
  recall_b: number
  interference: number
  shared_synapses: number
  dominant: string
}

export interface ThreeConditionResult {
  recall_matrix: RecallMatrixRow[]
  low_result: CollisionResult
  moderate_result: CollisionResult
  high_result: CollisionResult
}

export interface OrderComparisonResult {
  comparison_title: string
  matrix_frobenius_difference: number
  order_a_then_b: {
    order: string
    recall_a: number
    recall_b: number
    interference_a: number
    interference_b: number
    dominant_memory: string
  }
  order_b_then_a: {
    order: string
    recall_a: number
    recall_b: number
    interference_a: number
    interference_b: number
    dominant_memory: string
  }
  order_asymmetry_detected: boolean
  scientific_note: string
  result_ab: CollisionResult
  result_ba: CollisionResult
}

export interface CollisionSurgeryResult {
  status: string
  operation: string
  target_synapse: string
  original_weight: number
  post_surgery_weight: number
  weight_delta: number
  recall_a_before: number
  recall_a_after: number
  recall_a_delta: number
  recall_b_before: number
  recall_b_after: number
  recall_b_delta: number
  matrix_frobenius_delta: number
}

export interface CollisionCounterfactualResult {
  status: string
  counterfactual_title: string
  protected_synapses_count: number
  original_recall_a: number
  counterfactual_recall_a: number
  recall_a_improvement: number
  original_recall_b: number
  counterfactual_recall_b: number
  recall_b_delta: number
  matrix_distance_frobenius: number
  scientific_conclusion: string
}

// ============================================================================
// Phase 18: Memory Detective & Research Lab Forensics
// ============================================================================

export interface ForensicsEvidenceItem {
  evidence_id: string
  title: string
  category: 'SYNAPTIC_WEIGHT' | 'RECALL_MEASUREMENT' | 'COLLISION_OVERLAP' | 'SURGERY_EFFECT' | 'COUNTERFACTUAL_PROOF'
  timestep: number
  description: string
  data_point: Record<string, unknown>
  is_critical: boolean
  discovered?: boolean
}

export interface ForensicsCandidateHypothesis {
  hypothesis_id: string
  label: string
  description: string
  recommended_tool: 'xray' | 'timemachine' | 'surgery' | 'counterfactual' | 'collision' | 'synaptic'
  is_correct?: boolean | null
  explanation?: string | null
}

export interface ClaimTraceabilityItem {
  claim: string
  paper_citation: string
  experiment_ref: string
  observation: string
}

export interface InvestigationCase {
  case_id: string
  case_code: string
  title: string
  difficulty: 'INTRODUCTORY' | 'INTERMEDIATE' | 'ADVANCED'
  briefing: string
  question: string
  target_memory: string
  initial_recall: number
  final_recall: number
  total_timesteps: number
  intervention_step?: number | null
  available_tools: string[]
  candidate_hypotheses: ForensicsCandidateHypothesis[]
  available_evidence: ForensicsEvidenceItem[]
  ground_truth_hypothesis_id?: string | null
  ground_truth_explanation?: string | null
  underlying_data?: Record<string, unknown>
  claim_traceability: ClaimTraceabilityItem[]
}

export interface DetectiveScore {
  score: number
  rating: 'MASTER_DETECTIVE' | 'SOUND_INVESTIGATOR' | 'APPRENTICE' | 'NEEDS_WORK'
  hypothesis_correct: boolean
  confidence_accuracy: string
  evidence_score: number
  reasoning_score: number
  economy_score: number
  feedback: string
  explanation_chain: string[]
}

export interface HypothesisTestResult {
  hypothesis_id: string
  hypothesis_label: string
  recommended_tool: string
  tool_invoked: string
  status: string
  measured_evidence: Record<string, unknown>
  consistency_verdict: 'CONSISTENT' | 'CONTRADICTED' | 'INCONCLUSIVE'
  scientific_readout: string
}

export interface CustomExperimentConfig {
  experiment_id: string
  name: string
  description: string
  seed: number
  dimension: number
  decay: number
  mechanism: string
  write_gain: number
  memories: Array<{ concept: string; value: string; importance: number; strength: number }>
  idle_steps: number
  ablate_synapse?: string | null
  protect_shared_synapses: boolean
}

export interface CustomExperimentResult {
  experiment_id: string
  config: CustomExperimentConfig
  created_at: string
  final_matrix_norm: number
  active_synapse_count: number
  sparsity: number
  recalls: Array<{
    concept: string
    predicted_value: string
    ground_truth: string
    fidelity: number
    is_correct: boolean
    crosstalk_noise: number
  }>
  timeline_length: number
  reproducible_hash: string
  notes: string
}

export interface ExperimentComparison {
  exp_a_id: string
  exp_b_id: string
  matrix_frobenius_difference: number
  norm_a: number
  norm_b: number
  active_synapses_a: number
  active_synapses_b: number
  recall_diffs: Array<{
    concept: string
    fidelity_a: number
    fidelity_b: number
    delta: number
  }>
  interpretation: string
}

export interface ScientificSource {
  id: string
  title: string
  authors: string
  journal: string
  year: number
  doi: string
  key_finding: string
  relevance: string
}

export interface LearningObjective {
  id: string
  title: string
  principle: string
  scientific_rule: string
}

export interface ForensicsSourcesResponse {
  sources: ScientificSource[]
  claims: ClaimTraceabilityItem[]
}

// ==========================================
// Phase 19 Adaptive Memory Observatory Types
// ==========================================

export type WeatherCategory =
  | 'UNCHANGED'
  | 'RECENTLY_STRENGTHENED'
  | 'RECENTLY_WEAKENED'
  | 'CURRENTLY_ACTIVE'
  | 'INACTIVE_ZERO'

export type AdaptationEventType =
  | 'MEMORY_WRITE'
  | 'STATE_SHIFT'
  | 'INTERFERENCE'
  | 'RECALL_RECOVERY'
  | 'SYNAPTIC_MODIFICATION'
  | 'PASSIVE_DECAY'
  | 'BASELINE'

export interface StreamEvent {
  event_id: string
  step: number
  event_type: string
  key_label: string
  environment_id: string
  decay_rate: number
  learning_rate: number
  timestamp?: number
  metadata?: Record<string, unknown>
}

export interface ObservatoryProbe {
  concept: string
  target_pattern: number[]
  cue_pattern: number[]
  retrieved_pattern: number[]
  fidelity: number
  crosstalk: number
  is_stable: boolean
}

export interface SynapticWeatherPoint {
  row: number
  col: number
  weight: number
  prev_weight: number
  delta: number
  transmission_energy: number
  category: WeatherCategory
}

export interface ObservatorySnapshot {
  step: number
  event_id: string
  environment_id: string
  adaptation_event: AdaptationEventType
  adaptation_description: string
  matrix_norm: number
  sparsity: number
  active_synapse_count: number
  mean_weight: number
  max_weight: number
  probes: ObservatoryProbe[]
  weights_preview: number[][]
  active_transmissions: Array<[number, number]>
  weather_map: SynapticWeatherPoint[]
}

export interface ChangeDetection {
  step_from: number
  step_to: number
  strengthened_count: number
  weakened_count: number
  unchanged_count: number
  max_delta: number
  mean_delta: number
  frobenius_delta: number
  probe_fidelity_deltas: Record<string, number>
  top_modified_synapses: Array<{
    row: number
    col: number
    from_weight: number
    to_weight: number
    delta: number
  }>
  summary: string
}

export interface StabilityPlasticityMetrics {
  total_synapses: number
  unchanged_synapses: number
  adapted_synapses: number
  stability_ratio: number
  plasticity_extent: number
  average_weight_shift: number
  high_plasticity_count: number
  consolidated_count: number
}

export interface EnvironmentShiftReport {
  env_a: string
  env_b: string
  drift_distance: number
  interference_detected: boolean
  retroactive_retention: number
  summary: string
}

export interface LearnerPrediction {
  prediction_id: string
  session_id: string
  target_env: string
  predicted_category: string
  hypothesis: string
  confidence: number
  actual_category?: string
  is_correct?: boolean
  validation_summary?: string
}

export interface ObservatorySession {
  session_id: string
  name: string
  description: string
  dimension: number
  default_learning_rate: number
  default_decay_rate: number
  is_continuous: boolean
  snapshots: ObservatorySnapshot[]
  events: StreamEvent[]
  predictions: LearnerPrediction[]
  created_at: string
  parent_session_id?: string
  branch_point_step?: number
  branch_type?: 'SURGERY' | 'COUNTERFACTUAL' | 'NONE'
}

export interface ObservatoryComparison {
  session_a_id: string
  session_b_id: string
  session_a_name: string
  session_b_name: string
  steps_compared: number
  frobenius_divergence_series: number[]
  final_frobenius_distance: number
  probe_divergence: Record<string, {
    fidelity_a: number
    fidelity_b: number
    divergence: number
  }>
  stability_difference: number
  plasticity_difference: number
  narrative_conclusion: string
}

export interface ObservatoryPreset {
  id: string
  name: string
  description: string
  scenario: string
  events_count: number
}

// ==========================================
// Phase 20 Memory Genome & Synaptic Fingerprint Types
// ==========================================

export interface SynapticFingerprint {
  memory_id: string
  concept: string
  value: string
  timestep: number
  dimension: number
  active_key_units: number[]
  active_value_units: number[]
  active_unit_count: number
  modified_synapses: Array<[number, number, number]> // [row, col, delta_weight]
  modified_synapse_count: number
  synaptic_strength_stats: {
    mean: number
    std: number
    min: number
    max: number
    l2_norm: number
    frobenius_contribution: number
  }
  activation_distribution: {
    mean: number
    variance: number
    sparsity: number
    max_val: number
  }
  sparsity: number
  recall_performance: {
    fidelity: number
    crosstalk_noise: number
    confidence: number
  }
  representation_vector: number[]
  derivation_metadata: Record<string, unknown>
}

export interface FingerprintComparison {
  memory_a_id: string
  memory_b_id: string
  concept_a: string
  concept_b: string
  surface_similarity: number
  internal_similarity: number
  synaptic_overlap_jaccard: number
  shared_synapses: Array<[number, number, number, number]> // [row, col, delta_a, delta_b]
  a_only_synapses: Array<[number, number, number]>
  b_only_synapses: Array<[number, number, number]>
  recall_divergence: number
  similarity_discrepancy: number
  explanation: string
}

export interface FingerprintEvolution {
  memory_id: string
  concept: string
  timesteps: number[]
  fingerprints: SynapticFingerprint[]
  active_unit_trajectory: number[]
  modified_synapse_trajectory: number[]
  fidelity_trajectory: number[]
  frobenius_contribution_trajectory: number[]
}

export interface MemoryDistancePoint {
  memory_id: string
  concept: string
  value: string
  x: number
  y: number
  active_units: number
  recall_fidelity: number
  is_outlier: boolean
  outlier_reasons: string[]
}

export interface MemoryDistanceMap {
  points: MemoryDistancePoint[]
  projection_method: string
  variance_explained: number | null
  description: string
}

export interface MemoryBranchNode {
  node_id: string
  label: string
  branch_type: 'ORIGINAL' | 'COLLISION' | 'SURGERY' | 'COUNTERFACTUAL'
  step: number
  parent_id: string | null
  fingerprint: SynapticFingerprint | null
  children: MemoryBranchNode[]
}

export interface OutlierReport {
  memory_id: string
  concept: string
  is_outlier: boolean
  z_scores: Record<string, number>
  reasons: string[]
}

export interface FingerprintChallenge {
  challenge_id: string
  challenge_type: 'MOST_SIMILAR_INTERNAL' | 'MOST_CHANGED_INTERFERENCE'
  prompt: string
  target_memory: string
  options: string[]
  correct_option: string
  explanation: string
}

// ---------------------------------------------------------------------------
// Phase 21: Memory Ecosystem / Unified Synaptic Memory World Types
// ---------------------------------------------------------------------------

export interface MemoryPassport {
  memory_id: string
  concept: string
  value: string
  current_state: string
  creation_timestep: number
  last_accessed_timestep: number
  access_count: number
  recall_fidelity: number
  active_units: number
  synaptic_modifications: number
  overlap_count: number
  fingerprint_norm: number
  experiment_count: number
  branch_count: number
  parent_memory_id: string | null
  is_following: boolean
}

export interface LifecycleStage {
  stage_id: 'ENCODE' | 'WRITE' | 'STABILIZE' | 'RECALL' | 'INTERFERE' | 'ADAPT' | 'INSPECT' | 'COUNTERFACTUAL'
  name: string
  description: string
  target_workspace: string
  status: 'PENDING' | 'COMPLETED' | 'CURRENT' | 'DEGRADED' | 'SKIPPED'
  metrics: Record<string, unknown>
  timestamp?: string | null
}

export interface MemoryLifecycle {
  memory_id: string
  concept: string
  current_stage_id: string
  stages: LifecycleStage[]
}

export interface UnifiedTimelineEvent {
  event_id: string
  event_type: 'MEMORY_CREATED' | 'SYNAPTIC_WRITE' | 'RECALL' | 'INTERFERENCE' | 'SURGERY' | 'COUNTERFACTUAL' | 'FINGERPRINT_CAPTURED' | 'INSPECTION'
  step_index: number
  session_time: string
  memory_id: string
  experiment_id: string
  title: string
  description: string
  producing_experiment: string
  metrics_before: Record<string, unknown>
  metrics_after: Record<string, unknown>
  delta_metrics: Record<string, unknown>
}

export interface MemoryBranch {
  branch_id: string
  parent_id: string | null
  branch_type: 'ORIGINAL' | 'COLLISION' | 'SURGERY' | 'COUNTERFACTUAL'
  memory_id: string
  label: string
  created_at: string
  fidelity: number
  synaptic_drift: number
  children: MemoryBranch[]
}

export interface MemoryCheckpoint {
  checkpoint_id: string
  memory_id: string
  label: string
  step_index: number
  weights_summary: Record<string, number>
  created_at: string
}

export interface SynapticChangeLedger {
  transition_name: string
  memory_id: string
  concept: string
  before: Record<string, unknown>
  after: Record<string, unknown>
  delta: Record<string, unknown>
  scientific_claims: { type: 'OBSERVED' | 'MEASURED' | 'INFERRED' | 'TEACHING_SIMPLIFICATION'; statement: string }[]
}

export interface MemoryRelationship {
  source_id: string
  source_concept: string
  target_id: string
  target_concept: string
  relationship_type: 'SHARED_STATE' | 'SYNAPTIC_OVERLAP' | 'DERIVED_FROM' | 'INTERFERENCE' | 'COUNTERFACTUAL_OF'
  weight: number
  evidence: Record<string, unknown>
}

export interface LearnerHypothesis {
  hypothesis_id: string
  memory_id: string
  experiment_type: string
  prediction_text: string
  predicted_outcome: string
  observed_outcome?: string | null
  is_match?: boolean | null
  difference_explanation?: string | null
  timestamp?: string
}

export interface EcosystemOverview {
  active_memory_id: string
  is_following: boolean
  active_passport: MemoryPassport
  passports: MemoryPassport[]
  total_memories: number
  total_events: number
  scientific_claim: string
}

// ---------------------------------------------------------------------------
// Phase 22: Experiment Studio Types
// ---------------------------------------------------------------------------

export type StudioExperimentType =
  | 'ENCODING'
  | 'INTERFERENCE'
  | 'SURGERY'
  | 'COUNTERFACTUAL'
  | 'PERSISTENCE'
  | 'COMPARISON'

export interface StudioExperimentConfig {
  experiment_id?: string
  name: string
  experiment_type: StudioExperimentType
  seed: number
  d: number
  decay: number
  update_strength: number
  mechanism: string

  concept_a: string
  value_a: string
  importance_a: number
  strength_a: number

  interfering_concept: string
  interfering_value: string
  interfering_strength: number
  intervening_steps: number

  surgery_target_row: number
  surgery_target_col: number
  surgery_action: 'zero' | 'clamp_high' | 'invert' | 'attenuate'

  cf_param_name: string
  cf_param_value: number

  decay_cycles: number

  comparison_concept: string
  comparison_value: string

  controlled_variables: string[]
  changed_variable?: string | null
}

export interface StudioHypothesis {
  hypothesis_text: string
  predicted_outcome: string
  predicted_challenge_choice?: string | null
  actual_outcome?: string | null
  support_status?: 'SUPPORTED' | 'NOT SUPPORTED' | 'MIXED / INCONCLUSIVE' | null
}

export interface StudioComputationStep {
  step_name: 'INPUT' | 'ACTIVITY' | 'SYNAPTIC_WRITE' | 'STATE_UPDATE' | 'RECALL' | 'MEASUREMENT'
  order_index: number
  detail: string
  metrics: Record<string, unknown>
}

export interface StudioSynapticDeltaRecord {
  row: number
  col: number
  weight_before: number
  weight_after: number
  delta: number
  pct_change: number
  tag: 'OBSERVED' | 'MEASURED' | 'DERIVED' | 'SIMPLIFIED'
}

export interface StudioExperimentResult {
  experiment_id: string
  config: StudioExperimentConfig
  hypothesis: StudioHypothesis
  baseline_metrics: {
    fidelity: number
    crosstalk: number
    matrix_norm: number
    active_synapses: number
    sparsity: number
  }
  experiment_metrics: {
    fidelity: number
    crosstalk: number
    matrix_norm: number
    active_synapses: number
    sparsity: number
  }
  delta_metrics: {
    fidelity_delta: number
    crosstalk_delta: number
    matrix_norm_delta: number
    active_synapses_delta: number
    sparsity_delta: number
  }
  pipeline_steps: StudioComputationStep[]
  top_synaptic_changes: StudioSynapticDeltaRecord[]
  observation_statements: string[]
  interpretation_statements: string[]
  experiment_graph_active_stage: string
  is_deterministic: boolean
  seed_used: number
  timestamp: string
}

export interface StudioABComparison {
  exp_a: StudioExperimentResult
  exp_b: StudioExperimentResult
  diff_summary: {
    fidelity_diff: number
    crosstalk_diff: number
    matrix_norm_diff: number
    active_synapses_diff: number
  }
  differing_parameters: Record<string, [unknown, unknown]>
}

export interface StudioSweepPoint {
  param_value: number
  fidelity: number
  crosstalk: number
  matrix_norm: number
  active_synapses: number
}

export interface StudioSweepResult {
  param_name: string
  param_range: number[]
  points: StudioSweepPoint[]
  correlation: number
  trend_interpretation: string
}

export interface StudioExperimentTemplate {
  id: string
  title: string
  type: StudioExperimentType
  description: string
  config: Partial<StudioExperimentConfig>
  recommended_question: string
}

export interface StudioHistoryItem {
  experiment_id: string
  name: string
  experiment_type: string
  concept_a: string
  value_a: string
  fidelity: number
  delta_fidelity: number
  hypothesis_status?: string | null
  timestamp: string
}

export interface StudioGuidedJourneyStep {
  step_index: number
  action: string
  instruction: string
  focus: string
}

export interface StudioGuidedJourney {
  title: string
  total_steps: number
  steps: StudioGuidedJourneyStep[]
}

export interface StudioExperimentNote {
  question: string
  hypothesis: string
  observation: string
  conclusion: string
}

// ==========================================
// Phase 23 Scientific Evidence & Research Layer
// ==========================================

export interface PrimaryResearchPaper {
  paper_id: string
  title: string
  authors: string[]
  year: number
  journal: string
  doi: string
  url: string
  open_access: boolean
  tags: string[]
  key_finding: string
  supported_claim: string
  pathway_connection: string
  model_limitations: string
}

export interface ClaimTrace {
  claim_id: string
  claim_text: string
  source_paper_ids: string[]
  pathway_experiment_type: string
  measured_metrics: string[]
  observed_finding: string
  scientific_interpretation: string
  what_this_does_not_prove: string
}

export interface MetricDefinition {
  metric_id: string
  name: string
  symbol: string
  formula: string
  unit: string
  definition: string
  interpretation: string
  limitation: string
}

export interface ResearchGraphNode {
  id: string
  label: string
  node_type: 'CONCEPT' | 'PAPER' | 'IMPLEMENTATION' | 'EXPERIMENT' | 'OBSERVATION'
  summary: string
  details?: Record<string, unknown>
}

export interface ResearchGraphEdge {
  source: string
  target: string
  relation: string
}

export interface ResearchGraphData {
  nodes: ResearchGraphNode[]
  edges: ResearchGraphEdge[]
  total_nodes: number
  total_edges: number
}

export interface SourceLicenseRecord {
  category: 'CODE' | 'LIBRARIES' | 'DATA' | 'FONTS_ICONS' | 'PAPERS'
  name: string
  source: string
  version: string
  license: string
  usage: string
}

export interface DisclosuresData {
  ai_assistance: {
    tools_used: string[]
    role: string
    human_verification: string
    reproducibility: string
  }
  data_disclosure: {
    data_nature: string
    generation_method: string
    reproducibility: string
    patient_or_pii_data: boolean
  }
  prerequisites: {
    target_audience: string[]
    required_knowledge: string[]
    optional_helpful_background: string[]
    non_prerequisites: string[]
  }
  learning_objectives: string[]
  limitations: string[]
}

export interface MethodologyData {
  experiment_type: string
  input_specification: string
  model_architecture: string
  mathematical_operation: string
  readout_probe: string
  evaluation_metrics: string[]
  reproducibility: {
    engine: string
    seed: number
    deterministic: boolean
    software_stack: string
    hardware_invariance: string
  }
  limitations_and_non_claims: string[]
}