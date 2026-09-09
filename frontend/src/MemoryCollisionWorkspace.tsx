import React, { useEffect, useState } from 'react'
import {
  runCollisionCounterfactual,
  runCollisionExperiment,
  runCollisionSurgery,
  runOrderComparison,
  runThreeConditionSuite,
} from './api'
import { CollisionHypothesisCard } from './CollisionHypothesisCard'
import { CollisionPathwayMap } from './CollisionPathwayMap'
import { CollisionRecallMatrix } from './CollisionRecallMatrix'
import { CollisionTimelineScrubber } from './CollisionTimelineScrubber'
import './collision.css'
import type {
  CollisionConfig,
  CollisionCounterfactualResult,
  CollisionResult,
  CollisionSurgeryResult,
  OrderComparisonResult,
  SynapticPathwayClassification,
  ThreeConditionResult,
} from './types'

export const MemoryCollisionWorkspace: React.FC = () => {
  // Configuration state
  const [config, setConfig] = useState<CollisionConfig>({
    seed: 42,
    dimension: 16,
    decay: 0.05,
    update_strength: 1.0,
    memory_a: { concept: 'apple_cue', value: 'red_fruit', importance: 1.0, strength: 1.0 },
    memory_b: { concept: 'cherry_cue', value: 'tart_fruit', importance: 1.0, strength: 1.0 },
    memory_c: null,
    order: 'A_THEN_B',
    temporal_delay: 0,
    overlap_preset: 'MODERATE',
    concept_similarity: 0.45,
  })

  const [hasMemoryC, setHasMemoryC] = useState(false)
  const [activeTab, setActiveTab] = useState<'map' | 'matrix' | 'order' | 'cf'>('map')

  // Experiment outcomes
  const [result, setResult] = useState<CollisionResult | null>(null)
  const [threeConditionResult, setThreeConditionResult] = useState<ThreeConditionResult | null>(null)
  const [orderResult, setOrderResult] = useState<OrderComparisonResult | null>(null)
  const [surgeryResult, setSurgeryResult] = useState<CollisionSurgeryResult | null>(null)
  const [counterfactualResult, setCounterfactualResult] = useState<CollisionCounterfactualResult | null>(null)

  // Interactive selection
  const [selectedSynapse, setSelectedSynapse] = useState<SynapticPathwayClassification | null>(null)
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  // Initial run on mount
  useEffect(() => {
    handleRunCollision(config)
  }, [])

  const handleRunCollision = async (cfgToRun: CollisionConfig) => {
    setLoading(true)
    setStatusMessage('Simulating memory collision on synaptic matrix...')
    try {
      const res = await runCollisionExperiment(cfgToRun)
      setResult(res)
      setActiveStepIndex(res.timeline.length - 1)
      if (res.shared_synapses.length > 0) {
        const sharedItem = res.collision_map.find((m) => m.synapse_id === res.shared_synapses[0])
        if (sharedItem) setSelectedSynapse(sharedItem)
      } else {
        setSelectedSynapse(res.collision_map[0] || null)
      }
      setStatusMessage(`Collision experiment completed. ${res.shared_synapses.length} colliding synapses detected.`)
    } catch (err: unknown) {
      setStatusMessage(`Error running collision: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRunThreeConditions = async () => {
    setLoading(true)
    setStatusMessage('Evaluating Low, Moderate, and High overlap conditions...')
    try {
      const res = await runThreeConditionSuite({
        seed: config.seed,
        dimension: config.dimension,
        decay: config.decay,
        update_strength: config.update_strength,
        memory_a: config.memory_a,
        memory_b: config.memory_b,
        order: config.order,
        temporal_delay: config.temporal_delay,
      })
      setThreeConditionResult(res)
      setActiveTab('matrix')
      setStatusMessage('3-condition Recall Matrix generated successfully.')
    } catch (err: unknown) {
      setStatusMessage(`Error in 3-condition suite: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRunOrderComparison = async () => {
    setLoading(true)
    setStatusMessage('Comparing A -> B versus B -> A write sequences...')
    try {
      const res = await runOrderComparison({
        seed: config.seed,
        dimension: config.dimension,
        decay: config.decay,
        update_strength: config.update_strength,
        memory_a: config.memory_a,
        memory_b: config.memory_b,
        overlap_preset: config.overlap_preset,
        concept_similarity: config.concept_similarity,
        temporal_delay: config.temporal_delay,
      })
      setOrderResult(res)
      setActiveTab('order')
      setStatusMessage('Order comparison completed. Temporal sequence asymmetry recorded.')
    } catch (err: unknown) {
      setStatusMessage(`Error in order comparison: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSurgery = async (operation: 'silence' | 'weaken' | 'strengthen') => {
    if (!selectedSynapse) return
    setLoading(true)
    setStatusMessage(`Performing synaptic surgery (${operation}) on ${selectedSynapse.synapse_id}...`)
    try {
      const res = await runCollisionSurgery({
        config,
        synapse_id: selectedSynapse.synapse_id,
        operation,
        factor: operation === 'weaken' ? 0.5 : operation === 'strengthen' ? 2.0 : 0.0,
      })
      setSurgeryResult(res)
      setStatusMessage(
        `Surgery applied to ${res.target_synapse}: Recall A delta ${res.recall_a_delta > 0 ? '+' : ''}${res.recall_a_delta.toFixed(3)}, Recall B delta ${res.recall_b_delta > 0 ? '+' : ''}${res.recall_b_delta.toFixed(3)}.`
      )
    } catch (err: unknown) {
      setStatusMessage(`Surgery failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCounterfactual = async () => {
    setLoading(true)
    setStatusMessage('Evaluating counterfactual branch: What if Memory B never touched shared synapses?...')
    try {
      const res = await runCollisionCounterfactual({
        config,
      })
      setCounterfactualResult(res)
      setActiveTab('cf')
      setStatusMessage(
        `Counterfactual complete: Protecting ${res.protected_synapses_count} synapses changed Recall A from ${res.original_recall_a.toFixed(3)} to ${res.counterfactual_recall_a.toFixed(3)}.`
      )
    } catch (err: unknown) {
      setStatusMessage(`Counterfactual failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleOverlapPresetChange = (preset: 'LOW' | 'MODERATE' | 'HIGH' | 'CUSTOM') => {
    let sim = config.concept_similarity
    if (preset === 'LOW') sim = 0.0
    else if (preset === 'MODERATE') sim = 0.45
    else if (preset === 'HIGH') sim = 0.85

    const updated = { ...config, overlap_preset: preset, concept_similarity: sim }
    setConfig(updated)
    handleRunCollision(updated)
  }

  const activeWeights = result?.timeline?.[activeStepIndex]?.matrix_weights || null

  return (
    <div className="collision-workspace">
      {/* Header Bar */}
      <header className="collision-header">
        <div className="collision-header-left">
          <span className="collision-badge">Phase 17</span>
          <div>
            <h1 className="collision-title">Memory Collision & Interference Lab</h1>
            <p className="collision-subtitle">
              Investigate what happens when multiple memories compete for overlapping synaptic resources
            </p>
          </div>
        </div>

        <div className="collision-header-actions">
          <button
            type="button"
            className="collision-btn collision-btn-primary"
            onClick={() => handleRunCollision(config)}
            disabled={loading}
          >
            {loading ? 'Simulating...' : '⚡ Run Collision (A + B)'}
          </button>
          <button
            type="button"
            className="collision-btn collision-btn-outline"
            onClick={handleRunThreeConditions}
            disabled={loading}
          >
            📊 Recall Matrix
          </button>
          <button
            type="button"
            className="collision-btn collision-btn-outline"
            onClick={handleRunOrderComparison}
            disabled={loading}
          >
            ⇄ Order Comparison
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="collision-tabs">
        <button
          type="button"
          className={`collision-tab-item ${activeTab === 'map' ? 'active' : ''}`}
          onClick={() => setActiveTab('map')}
        >
          🗺️ Collision Map & Pathways
        </button>
        <button
          type="button"
          className={`collision-tab-item ${activeTab === 'matrix' ? 'active' : ''}`}
          onClick={() => setActiveTab('matrix')}
        >
          📊 Recall Matrix (3 Conditions)
        </button>
        <button
          type="button"
          className={`collision-tab-item ${activeTab === 'order' ? 'active' : ''}`}
          onClick={() => setActiveTab('order')}
        >
          ⇄ Order Matters (A→B vs B→A)
        </button>
        <button
          type="button"
          className={`collision-tab-item ${activeTab === 'cf' ? 'active' : ''}`}
          onClick={() => setActiveTab('cf')}
        >
          🔮 Counterfactual Protection
        </button>
      </nav>

      {/* Body Content */}
      <main className="collision-body">
        {/* Status Message */}
        {statusMessage && (
          <div
            style={{
              padding: '10px 14px',
              background: '#0b1329',
              border: '1px solid #1e3a8a',
              borderRadius: '6px',
              fontSize: '11px',
              color: '#93c5fd',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>ℹ️</span>
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Stats Row */}
        {result && (
          <section className="stat-pill-row" aria-label="Collision Metrics">
            <div className="stat-pill">
              <span className="stat-pill-title">Rep. Overlap (Cosine)</span>
              <span className="stat-pill-value" style={{ color: '#38bdf8' }}>
                {result.representational_overlap.toFixed(3)}
              </span>
            </div>
            <div className="stat-pill stat-pill-highlight">
              <span className="stat-pill-title">Synaptic Overlap</span>
              <span className="stat-pill-value">
                {(result.synaptic_overlap_fraction * 100).toFixed(1)}%
              </span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-title">Shared Synapses</span>
              <span className="stat-pill-value" style={{ color: '#fbbf24' }}>
                {result.shared_synapses.length}
              </span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-title">Memory A Combined Fidelity</span>
              <span className="stat-pill-value" style={{ color: '#38bdf8' }}>
                {result.combined_recall_a.fidelity.toFixed(3)}
              </span>
              <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                Isolated: {result.isolated_recall_a.fidelity.toFixed(3)} (Δ{' '}
                {result.computational_interference_a.toFixed(3)})
              </span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-title">Memory B Combined Fidelity</span>
              <span className="stat-pill-value" style={{ color: '#c084fc' }}>
                {result.combined_recall_b.fidelity.toFixed(3)}
              </span>
              <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                Isolated: {result.isolated_recall_b.fidelity.toFixed(3)} (Δ{' '}
                {result.computational_interference_b.toFixed(3)})
              </span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-title">Interference Dominance</span>
              <span className="stat-pill-value" style={{ fontSize: '14px', color: '#f8fafc' }}>
                {result.memory_dominance}
              </span>
              <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                Margin: {result.dominant_memory_margin.toFixed(3)}
              </span>
            </div>
          </section>
        )}

        {/* Experiment Configuration Panel */}
        <section className="collision-card" aria-label="Experiment Setup">
          <div className="collision-card-header">
            <div>
              <h2 className="collision-card-title">⚙️ Memory & Collision Parameters</h2>
              <p className="collision-card-desc">
                Define the competing memories, representational similarity, decay rate, and temporal spacing
              </p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className={`collision-btn ${config.overlap_preset === 'LOW' ? 'collision-btn-active' : 'collision-btn-outline'}`}
                onClick={() => handleOverlapPresetChange('LOW')}
              >
                Low (0.0)
              </button>
              <button
                type="button"
                className={`collision-btn ${config.overlap_preset === 'MODERATE' ? 'collision-btn-active' : 'collision-btn-outline'}`}
                onClick={() => handleOverlapPresetChange('MODERATE')}
              >
                Moderate (0.45)
              </button>
              <button
                type="button"
                className={`collision-btn ${config.overlap_preset === 'HIGH' ? 'collision-btn-active' : 'collision-btn-outline'}`}
                onClick={() => handleOverlapPresetChange('HIGH')}
              >
                High (0.85)
              </button>
            </div>
          </div>

          <div className="memory-config-grid">
            {/* Memory A Box */}
            <div className="memory-box memory-box-a">
              <div className="memory-box-label" style={{ color: '#38bdf8' }}>
                <span>Memory A (First Write)</span>
                <span className="color-dot-a"></span>
              </div>
              <div className="collision-input-group">
                <label>Concept / Cue</label>
                <input
                  type="text"
                  className="collision-input"
                  value={config.memory_a.concept}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      memory_a: { ...config.memory_a, concept: e.target.value },
                    })
                  }
                />
              </div>
              <div className="collision-input-group">
                <label>Target Value</label>
                <input
                  type="text"
                  className="collision-input"
                  value={config.memory_a.value}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      memory_a: { ...config.memory_a, value: e.target.value },
                    })
                  }
                />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <div className="collision-input-group" style={{ flex: 1 }}>
                  <label>Importance (η multiplier)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="5.0"
                    className="collision-input"
                    value={config.memory_a.importance}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        memory_a: { ...config.memory_a, importance: parseFloat(e.target.value) || 1.0 },
                      })
                    }
                  />
                </div>
                <div className="collision-input-group" style={{ flex: 1 }}>
                  <label>Strength Factor</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="5.0"
                    className="collision-input"
                    value={config.memory_a.strength}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        memory_a: { ...config.memory_a, strength: parseFloat(e.target.value) || 1.0 },
                      })
                    }
                  />
                </div>
              </div>
            </div>

            {/* Memory B Box */}
            <div className="memory-box memory-box-b">
              <div className="memory-box-label" style={{ color: '#c084fc' }}>
                <span>Memory B (Second Write)</span>
                <span className="color-dot-b"></span>
              </div>
              <div className="collision-input-group">
                <label>Concept / Cue</label>
                <input
                  type="text"
                  className="collision-input"
                  value={config.memory_b.concept}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      memory_b: { ...config.memory_b, concept: e.target.value },
                    })
                  }
                />
              </div>
              <div className="collision-input-group">
                <label>Target Value</label>
                <input
                  type="text"
                  className="collision-input"
                  value={config.memory_b.value}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      memory_b: { ...config.memory_b, value: e.target.value },
                    })
                  }
                />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <div className="collision-input-group" style={{ flex: 1 }}>
                  <label>Importance (η multiplier)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="5.0"
                    className="collision-input"
                    value={config.memory_b.importance}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        memory_b: { ...config.memory_b, importance: parseFloat(e.target.value) || 1.0 },
                      })
                    }
                  />
                </div>
                <div className="collision-input-group" style={{ flex: 1 }}>
                  <label>Strength Factor</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="5.0"
                    className="collision-input"
                    value={config.memory_b.strength}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        memory_b: { ...config.memory_b, strength: parseFloat(e.target.value) || 1.0 },
                      })
                    }
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Additional Multi-Memory C Option */}
          {hasMemoryC && config.memory_c && (
            <div className="memory-box memory-box-c" style={{ marginTop: '12px' }}>
              <div className="memory-box-label" style={{ color: '#34d399' }}>
                <span>Memory C (Third Colliding Memory)</span>
                <span className="color-dot-c"></span>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div className="collision-input-group" style={{ flex: 1 }}>
                  <label>Concept / Cue</label>
                  <input
                    type="text"
                    className="collision-input"
                    value={config.memory_c.concept}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        memory_c: { ...config.memory_c!, concept: e.target.value },
                      })
                    }
                  />
                </div>
                <div className="collision-input-group" style={{ flex: 1 }}>
                  <label>Target Value</label>
                  <input
                    type="text"
                    className="collision-input"
                    value={config.memory_c.value}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        memory_c: { ...config.memory_c!, value: e.target.value },
                      })
                    }
                  />
                </div>
              </div>
            </div>
          )}

          {/* Sliders & Toggles */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '16px' }}>
            <div>
              <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                CONCEPT SIMILARITY (Overlap: {config.concept_similarity.toFixed(2)})
              </label>
              <input
                type="range"
                min="0.0"
                max="0.95"
                step="0.05"
                value={config.concept_similarity}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    overlap_preset: 'CUSTOM',
                    concept_similarity: parseFloat(e.target.value),
                  })
                }
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                TEMPORAL DELAY (Idle decay steps: {config.temporal_delay})
              </label>
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={config.temporal_delay}
                onChange={(e) => setConfig({ ...config, temporal_delay: parseInt(e.target.value, 10) })}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                SYNAPTIC DECAY (λ = {config.decay})
              </label>
              <input
                type="range"
                min="0.0"
                max="0.3"
                step="0.01"
                value={config.decay}
                onChange={(e) => setConfig({ ...config, decay: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingTop: '16px' }}>
              <label style={{ fontSize: '11px', color: '#cbd5e1', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <input
                  type="checkbox"
                  checked={hasMemoryC}
                  onChange={(e) => {
                    setHasMemoryC(e.target.checked)
                    setConfig({
                      ...config,
                      memory_c: e.target.checked ? { concept: 'gamma_cue', value: 'green_fruit', importance: 1.0, strength: 1.0 } : null,
                    })
                  }}
                />
                Enable Memory C
              </label>
            </div>
          </div>
        </section>

        {/* Tab 1: Collision Map & Pathways */}
        {activeTab === 'map' && (
          <>
            {/* Timeline Scrubber */}
            {result && (
              <section className="collision-card" aria-label="Collision Time Machine">
                <CollisionTimelineScrubber
                  timeline={result.timeline}
                  activeStepIndex={activeStepIndex}
                  onSelectStep={(idx) => setActiveStepIndex(idx)}
                />
              </section>
            )}

            <div className="collision-row-2-1">
              {/* Left Column: Visual Pathway Map */}
              <section className="collision-card" aria-label="Synaptic Matrix Map">
                <div className="collision-card-header">
                  <div>
                    <h2 className="collision-card-title">🗺️ Synaptic Collision Field ({config.dimension}×{config.dimension})</h2>
                    <p className="collision-card-desc">
                      Click any synapse cell to inspect weight history, overwrite magnitude, and perform surgery
                    </p>
                  </div>
                  {result && (
                    <span style={{ fontSize: '11px', color: '#fbbf24', fontWeight: 600 }}>
                      ★ {result.shared_synapses.length} Shared Colliding Synapses
                    </span>
                  )}
                </div>

                <CollisionPathwayMap
                  result={result}
                  selectedSynapse={selectedSynapse}
                  onSelectSynapse={(syn) => setSelectedSynapse(syn)}
                  currentWeights={activeWeights}
                />
              </section>

              {/* Right Column: Synapse Inspector & Surgery */}
              <section className="collision-card" aria-label="Synaptic Surgery Inspector">
                <div className="collision-card-header">
                  <div>
                    <h2 className="collision-card-title">🔬 Synaptic Inspector & Surgery</h2>
                    <p className="collision-card-desc">
                      Detailed accounting of synaptic update history and direct causal surgery
                    </p>
                  </div>
                </div>

                {selectedSynapse ? (
                  <div className="synapse-detail-panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '12px', color: '#f8fafc' }}>
                        {selectedSynapse.synapse_id}
                      </span>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background:
                            selectedSynapse.classification === 'SHARED'
                              ? '#78350f'
                              : selectedSynapse.classification === 'A_ONLY'
                              ? '#0369a1'
                              : selectedSynapse.classification === 'B_ONLY'
                              ? '#581c87'
                              : '#1e293b',
                          color:
                            selectedSynapse.classification === 'SHARED'
                              ? '#fde047'
                              : selectedSynapse.classification === 'A_ONLY'
                              ? '#7dd3fc'
                              : selectedSynapse.classification === 'B_ONLY'
                              ? '#e9d5ff'
                              : '#94a3b8',
                        }}
                      >
                        {selectedSynapse.classification}
                      </span>
                    </div>

                    <div className="synapse-detail-grid">
                      <div className="synapse-detail-item">
                        <span className="synapse-detail-key">Connection</span>
                        <span className="synapse-detail-val">
                          {selectedSynapse.source} → {selectedSynapse.target}
                        </span>
                      </div>
                      <div className="synapse-detail-item">
                        <span className="synapse-detail-key">After Write A</span>
                        <span className="synapse-detail-val">
                          {selectedSynapse.weight_after_first.toFixed(4)}
                        </span>
                      </div>
                      <div className="synapse-detail-item">
                        <span className="synapse-detail-key">Delta Write B</span>
                        <span className="synapse-detail-val">
                          {selectedSynapse.weight_delta_second.toFixed(4)}
                        </span>
                      </div>
                      <div className="synapse-detail-item">
                        <span className="synapse-detail-key">Final Matrix Weight</span>
                        <span className="synapse-detail-val" style={{ color: '#38bdf8' }}>
                          {selectedSynapse.final_weight.toFixed(4)}
                        </span>
                      </div>
                      <div className="synapse-detail-item">
                        <span className="synapse-detail-key">Overwrite Magnitude</span>
                        <span className="synapse-detail-val" style={{ color: '#fbbf24' }}>
                          {selectedSynapse.overwrite_magnitude.toFixed(4)}
                        </span>
                      </div>
                      <div className="synapse-detail-item">
                        <span className="synapse-detail-key">Active In Memory</span>
                        <span className="synapse-detail-val">
                          {selectedSynapse.classification === 'SHARED'
                            ? 'Both A & B'
                            : selectedSynapse.classification === 'A_ONLY'
                            ? 'A Only'
                            : selectedSynapse.classification === 'B_ONLY'
                            ? 'B Only'
                            : 'None'}
                        </span>
                      </div>
                    </div>

                    {/* Surgical Intervention Controls */}
                    <div style={{ marginTop: '12px' }}>
                      <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
                        Surgically Alter This Synapse (Phase 15 Integration)
                      </span>
                      <div className="surgery-controls">
                        <button
                          type="button"
                          className="collision-btn collision-btn-outline"
                          style={{ flex: 1, padding: '6px 8px', fontSize: '10px' }}
                          onClick={() => handleSurgery('silence')}
                          disabled={loading}
                        >
                          Silence (W=0)
                        </button>
                        <button
                          type="button"
                          className="collision-btn collision-btn-outline"
                          style={{ flex: 1, padding: '6px 8px', fontSize: '10px' }}
                          onClick={() => handleSurgery('weaken')}
                          disabled={loading}
                        >
                          Weaken (×0.5)
                        </button>
                        <button
                          type="button"
                          className="collision-btn collision-btn-outline"
                          style={{ flex: 1, padding: '6px 8px', fontSize: '10px' }}
                          onClick={() => handleSurgery('strengthen')}
                          disabled={loading}
                        >
                          Strengthen (×2.0)
                        </button>
                      </div>
                    </div>

                    {surgeryResult && surgeryResult.target_synapse === selectedSynapse.synapse_id && (
                      <div
                        style={{
                          marginTop: '12px',
                          padding: '10px',
                          borderRadius: '4px',
                          background: 'rgba(56, 189, 248, 0.1)',
                          border: '1px solid #38bdf8',
                          fontSize: '10px',
                        }}
                      >
                        <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '4px' }}>
                          SURGICAL POST-EVALUATION
                        </div>
                        <div>Weight: {surgeryResult.original_weight.toFixed(3)} → {surgeryResult.post_surgery_weight.toFixed(3)}</div>
                        <div>
                          Recall A: {surgeryResult.recall_a_before.toFixed(3)} → {surgeryResult.recall_a_after.toFixed(3)} (
                          {surgeryResult.recall_a_delta >= 0 ? '+' : ''}{surgeryResult.recall_a_delta.toFixed(3)})
                        </div>
                        <div>
                          Recall B: {surgeryResult.recall_b_before.toFixed(3)} → {surgeryResult.recall_b_after.toFixed(3)} (
                          {surgeryResult.recall_b_delta >= 0 ? '+' : ''}{surgeryResult.recall_b_delta.toFixed(3)})
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ color: '#64748b', fontSize: '11px', textAlign: 'center', padding: '30px 10px' }}>
                    Select a synapse in the map to inspect its weights and perform surgical intervention.
                  </div>
                )}

                {/* Counterfactual Quick Action */}
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #1e293b' }}>
                  <button
                    type="button"
                    className="collision-btn collision-btn-warning"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={handleCounterfactual}
                    disabled={loading || !result || result.shared_synapses.length === 0}
                  >
                    🔮 Counterfactual: What if B never touched shared synapses?
                  </button>
                </div>
              </section>
            </div>

            {/* Scientific Hypothesis & Interpretation Card */}
            <CollisionHypothesisCard
              result={result}
              onTestHypothesis={() => {}}
            />
          </>
        )}

        {/* Tab 2: Recall Matrix */}
        {activeTab === 'matrix' && (
          <section className="collision-card" aria-label="Three Conditions Recall Matrix">
            <div className="collision-card-header">
              <div>
                <h2 className="collision-card-title">📊 3-Condition Recall Matrix</h2>
                <p className="collision-card-desc">
                  Low (0.0) vs Moderate (0.45) vs High (0.85) overlap across identical computational baselines
                </p>
              </div>
            </div>

            <CollisionRecallMatrix
              threeConditionResult={threeConditionResult}
              activeConditionName={config.overlap_preset}
              onSelectCondition={(condName) => {
                if (condName.includes('LOW')) handleOverlapPresetChange('LOW')
                else if (condName.includes('MODERATE')) handleOverlapPresetChange('MODERATE')
                else if (condName.includes('HIGH')) handleOverlapPresetChange('HIGH')
              }}
              onRunThreeConditions={handleRunThreeConditions}
              loading={loading}
            />
          </section>
        )}

        {/* Tab 3: Order Comparison */}
        {activeTab === 'order' && (
          <section className="collision-card" aria-label="Order Comparison">
            <div className="collision-card-header">
              <div>
                <h2 className="collision-card-title">⇄ Order Matters: (A → B) vs (B → A)</h2>
                <p className="collision-card-desc">
                  Discover temporal sequence asymmetry and non-commutative matrix update effects
                </p>
              </div>
              <button
                type="button"
                className="collision-btn collision-btn-primary"
                onClick={handleRunOrderComparison}
                disabled={loading}
              >
                {loading ? 'Comparing...' : 'Run Order Comparison'}
              </button>
            </div>

            {orderResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  {/* Order A then B */}
                  <div style={{ padding: '16px', background: '#0b1120', borderRadius: '6px', border: '1px solid #1e3a8a' }}>
                    <div style={{ fontWeight: 700, fontSize: '13px', color: '#93c5fd', marginBottom: '8px' }}>
                      SEQUENCE: Write A → Write B
                    </div>
                    <div style={{ fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div>Recall A Fidelity: <strong>{orderResult.order_a_then_b.recall_a.toFixed(3)}</strong></div>
                      <div>Recall B Fidelity: <strong>{orderResult.order_a_then_b.recall_b.toFixed(3)}</strong></div>
                      <div>Dominant Memory: <span style={{ color: '#fbbf24' }}>{orderResult.order_a_then_b.dominant_memory}</span></div>
                    </div>
                  </div>

                  {/* Order B then A */}
                  <div style={{ padding: '16px', background: '#0b1120', borderRadius: '6px', border: '1px solid #6b21a8' }}>
                    <div style={{ fontWeight: 700, fontSize: '13px', color: '#e9d5ff', marginBottom: '8px' }}>
                      SEQUENCE: Write B → Write A
                    </div>
                    <div style={{ fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div>Recall A Fidelity: <strong>{orderResult.order_b_then_a.recall_a.toFixed(3)}</strong></div>
                      <div>Recall B Fidelity: <strong>{orderResult.order_b_then_a.recall_b.toFixed(3)}</strong></div>
                      <div>Dominant Memory: <span style={{ color: '#fbbf24' }}>{orderResult.order_b_then_a.dominant_memory}</span></div>
                    </div>
                  </div>
                </div>

                <div className="scientific-report-box">
                  <div className="report-lead">
                    Matrix Distance: ‖W_(A→B) - W_(B→A)‖_F = {orderResult.matrix_frobenius_difference.toFixed(4)}
                  </div>
                  <div>{orderResult.scientific_note}</div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                Click "Run Order Comparison" to evaluate whether write order alters recall outcomes.
              </div>
            )}
          </section>
        )}

        {/* Tab 4: Counterfactual Protection */}
        {activeTab === 'cf' && (
          <section className="collision-card" aria-label="Counterfactual Analysis">
            <div className="collision-card-header">
              <div>
                <h2 className="collision-card-title">🔮 Counterfactual Branch: Protected Synapses</h2>
                <p className="collision-card-desc">
                  Causal proof: "What if Memory B had never modified the shared synapses?"
                </p>
              </div>
              <button
                type="button"
                className="collision-btn collision-btn-warning"
                onClick={handleCounterfactual}
                disabled={loading}
              >
                {loading ? 'Evaluating...' : 'Re-run Counterfactual'}
              </button>
            </div>

            {counterfactualResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                  <div className="stat-pill">
                    <span className="stat-pill-title">Protected Synapses</span>
                    <span className="stat-pill-value" style={{ color: '#fbbf24' }}>
                      {counterfactualResult.protected_synapses_count}
                    </span>
                  </div>
                  <div className="stat-pill">
                    <span className="stat-pill-title">Memory A Original Recall</span>
                    <span className="stat-pill-value" style={{ color: '#94a3b8' }}>
                      {counterfactualResult.original_recall_a.toFixed(3)}
                    </span>
                  </div>
                  <div className="stat-pill stat-pill-highlight">
                    <span className="stat-pill-title">Memory A Counterfactual Recall</span>
                    <span className="stat-pill-value">
                      {counterfactualResult.counterfactual_recall_a.toFixed(3)}
                    </span>
                    <span style={{ fontSize: '10px', color: '#34d399' }}>
                      Gain: +{counterfactualResult.recall_a_improvement.toFixed(3)}
                    </span>
                  </div>
                  <div className="stat-pill">
                    <span className="stat-pill-title">Memory B Counterfactual Recall</span>
                    <span className="stat-pill-value" style={{ color: '#c084fc' }}>
                      {counterfactualResult.counterfactual_recall_b.toFixed(3)}
                    </span>
                  </div>
                </div>

                <div className="scientific-report-box">
                  <div className="report-lead">{counterfactualResult.counterfactual_title}</div>
                  <div>{counterfactualResult.scientific_conclusion}</div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                Click "Re-run Counterfactual" to execute this causal what-if branch.
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  )
}
