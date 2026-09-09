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