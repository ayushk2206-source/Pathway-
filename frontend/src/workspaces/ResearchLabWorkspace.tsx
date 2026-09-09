import React, { useState, useEffect } from 'react'
import type { CustomExperimentConfig, CustomExperimentResult, ExperimentComparison } from '../types'
import { runCustomResearch, getResearchHistory, compareResearchExperiments } from '../api'

export const ResearchLabWorkspace: React.FC = () => {
  const [name, setName] = useState('Custom Memory Interference Study')
  const [description, setDescription] = useState('Parametric investigation of synaptic capacity and decay')
  const [dimension, setDimension] = useState<number>(16)
  const [decay, setDecay] = useState<number>(0.04)
  const [writeGain, setWriteGain] = useState<number>(1.0)
  const [mechanism, setMechanism] = useState<string>('hebbian_outer_product')
  const [seed, setSeed] = useState<number>(42)
  const [idleSteps, setIdleSteps] = useState<number>(2)
  const [ablateSynapse, setAblateSynapse] = useState<string>('')
  const [protectShared, setProtectShared] = useState<boolean>(false)

  // Memory list builder
  const [memories, setMemories] = useState<
    Array<{ concept: string; value: string; importance: number; strength: number }>
  >([
    { concept: 'signal_a', value: 'alpha_state', importance: 1.0, strength: 1.0 },
    { concept: 'signal_b', value: 'beta_state', importance: 0.8, strength: 0.9 },
  ])

  // Session execution state
  const [running, setRunning] = useState(false)
  const [history, setHistory] = useState<CustomExperimentResult[]>([])
  const [currentResult, setCurrentResult] = useState<CustomExperimentResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Comparative diff state
  const [compareAId, setCompareAId] = useState<string>('')
  const [compareBId, setCompareBId] = useState<string>('')
  const [comparison, setComparison] = useState<ExperimentComparison | null>(null)
  const [comparing, setComparing] = useState(false)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const res = await getResearchHistory()
      setHistory(res.experiments)
      if (res.experiments.length >= 1 && !currentResult) {
        setCurrentResult(res.experiments[0])
      }
      if (res.experiments.length >= 2) {
        setCompareAId(res.experiments[0].experiment_id)
        setCompareBId(res.experiments[1].experiment_id)
      }
    } catch {
      // initial history might be empty
    }
  }

  const handleAddMemory = () => {
    setMemories([
      ...memories,
      {
        concept: `cue_${memories.length + 1}`,
        value: `val_${memories.length + 1}`,
        importance: 1.0,
        strength: 1.0,
      },
    ])
  }

  const handleUpdateMemory = (idx: number, field: string, val: any) => {
    const updated = [...memories]
    updated[idx] = { ...updated[idx], [field]: val }
    setMemories(updated)
  }

  const handleRemoveMemory = (idx: number) => {
    if (memories.length <= 1) return
    const updated = [...memories]
    updated.splice(idx, 1)
    setMemories(updated)
  }

  const handleExecute = async () => {
    setRunning(true)
    setError(null)
    try {
      const payload: Partial<CustomExperimentConfig> = {
        name,
        description,
        dimension,
        decay,
        write_gain: writeGain,
        mechanism,
        seed,
        memories,
        idle_steps: idleSteps,
        ablate_synapse: ablateSynapse.trim() ? ablateSynapse.trim() : null,
        protect_shared_synapses: protectShared,
      }
      const res = await runCustomResearch(payload)
      setCurrentResult(res)
      await fetchHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed')
    } finally {
      setRunning(false)
    }
  }

  const handleCompare = async () => {
    if (!compareAId || !compareBId) return
    setComparing(true)
    try {
      const res = await compareResearchExperiments(compareAId, compareBId)
      setComparison(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed')
    } finally {
      setComparing(false)
    }
  }

  return (
    <div className="forensics-workspace">
      {/* Header */}
      <div className="forensics-header">
        <div className="forensics-title-group">
          <h1>
            <span>🧪</span> Research Lab Workspace
          </h1>
          <p className="forensics-subtitle">
            Parametric Neural Sandbox for Full Empirical Experimentation & Differential Analysis
          </p>
        </div>
        <div className="forensics-header-actions">
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            Logged Experiments: <strong style={{ color: '#38bdf8' }}>{history.length}</strong>
          </span>
        </div>
      </div>

      {/* Main Form & Configuration Grid */}
      <div className="case-briefing-panel">
        <div className="panel-title-bar">
          <h3>
            <span>⚙️</span> Custom Neural Experiment Configuration
          </h3>
          <button
            className="test-tool-btn"
            onClick={handleExecute}
            disabled={running}
            style={{ padding: '0.5rem 1.25rem' }}
          >
            {running ? 'Executing Synaptic Matrix...' : '▶ Run Custom Experiment'}
          </button>
        </div>

        {error && (
          <div style={{ color: '#f87171', background: 'rgba(239, 68, 68, 0.1)', padding: '0.5rem 1rem', borderRadius: '6px' }}>
            {error}
          </div>
        )}

        <div className="research-config-grid">
          <div className="form-control-group">
            <label>Experiment Title</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="form-control-group">
            <label>Research Hypothesis / Description</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="form-control-group">
            <label>Dimension (d)</label>
            <select value={dimension} onChange={(e) => setDimension(Number(e.target.value))}>
              <option value={8}>d=8 (Compact)</option>
              <option value={16}>d=16 (Standard Standardized)</option>
              <option value={32}>d=32 (High Capacity Subspace)</option>
            </select>
          </div>
          <div className="form-control-group">
            <label>Passive Decay Rate (λ)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="0.5"
              value={decay}
              onChange={(e) => setDecay(Number(e.target.value))}
            />
          </div>
          <div className="form-control-group">
            <label>Hebbian Gain (η)</label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="5.0"
              value={writeGain}
              onChange={(e) => setWriteGain(Number(e.target.value))}
            />
          </div>
          <div className="form-control-group">
            <label>Learning Mechanism</label>
            <select value={mechanism} onChange={(e) => setMechanism(e.target.value)}>
              <option value="hebbian_outer_product">Hebbian Outer-Product</option>
              <option value="dense_hopfield">Modern Dense Hopfield</option>
            </select>
          </div>
          <div className="form-control-group">
            <label>RNG Seed</label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
          </div>
          <div className="form-control-group">
            <label>Idle Decay Steps</label>
            <input
              type="number"
              min="0"
              max="20"
              value={idleSteps}
              onChange={(e) => setIdleSteps(Number(e.target.value))}
            />
          </div>
          <div className="form-control-group">
            <label>Ablate Synapse (e.g. syn_k0_v0)</label>
            <input
              placeholder="Leave empty for intact"
              value={ablateSynapse}
              onChange={(e) => setAblateSynapse(e.target.value)}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input
            type="checkbox"
            id="protectShared"
            checked={protectShared}
            onChange={(e) => setProtectShared(e.target.checked)}
          />
          <label htmlFor="protectShared" style={{ fontSize: '0.85rem', color: '#cbd5e1', cursor: 'pointer' }}>
            Enable Counterfactual Protection of Shared Synaptic Coordinates
          </label>
        </div>

        {/* Memory Items Section */}
        <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(148, 163, 184, 0.15)', paddingTop: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9' }}>
              Memories to Sequential Write ({memories.length})
            </span>
            <button
              onClick={handleAddMemory}
              style={{
                background: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid #38bdf8',
                color: '#38bdf8',
                borderRadius: '4px',
                padding: '0.2rem 0.6rem',
                fontSize: '0.75rem',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              + Add Memory
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {memories.map((m, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'center',
                  background: 'rgba(30, 41, 59, 0.5)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid rgba(148, 163, 184, 0.1)',
                }}
              >
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', width: '24px' }}>#{idx + 1}</span>
                <input
                  placeholder="Concept Cue"
                  value={m.concept}
                  onChange={(e) => handleUpdateMemory(idx, 'concept', e.target.value)}
                  style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid #475569', color: '#fff', padding: '0.3rem 0.5rem', borderRadius: '4px', flex: 1 }}
                />
                <input
                  placeholder="Target Value"
                  value={m.value}
                  onChange={(e) => handleUpdateMemory(idx, 'value', e.target.value)}
                  style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid #475569', color: '#fff', padding: '0.3rem 0.5rem', borderRadius: '4px', flex: 1 }}
                />
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="2.0"
                  value={m.strength}
                  onChange={(e) => handleUpdateMemory(idx, 'strength', Number(e.target.value))}
                  style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid #475569', color: '#fff', padding: '0.3rem 0.5rem', borderRadius: '4px', width: '80px' }}
                />
                <button
                  onClick={() => handleRemoveMemory(idx)}
                  disabled={memories.length <= 1}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: memories.length <= 1 ? '#475569' : '#f87171',
                    cursor: memories.length <= 1 ? 'default' : 'pointer',
                    fontSize: '1rem',
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Latest Run Results */}
      {currentResult && (
        <div className="case-briefing-panel">
          <div className="panel-title-bar">
            <h3>
              <span>📊</span> Run Output: {currentResult.config.name} ({currentResult.experiment_id})
            </h3>
            <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8' }}>
              SHA256: {currentResult.reproducible_hash}
            </span>
          </div>

          <div className="briefing-metrics-row">
            <div className="metric-pill">
              <span className="metric-pill-label">Matrix Frobenius Norm</span>
              <span className="metric-pill-val">{currentResult.final_matrix_norm.toFixed(3)}</span>
            </div>
            <div className="metric-pill">
              <span className="metric-pill-label">Active Synapses</span>
              <span className="metric-pill-val">{currentResult.active_synapse_count}</span>
            </div>
            <div className="metric-pill">
              <span className="metric-pill-label">Sparsity</span>
              <span className="metric-pill-val">{(currentResult.sparsity * 100).toFixed(1)}%</span>
            </div>
            <div className="metric-pill">
              <span className="metric-pill-label">Timeline Steps</span>
              <span className="metric-pill-val">{currentResult.timeline_length}</span>
            </div>
          </div>

          <div style={{ marginTop: '0.75rem' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '0.5rem' }}>
              Associative Recall Probes:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
              {currentResult.recalls.map((rec, i) => (
                <div
                  key={i}
                  style={{
                    background: 'rgba(30, 41, 59, 0.7)',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(148, 163, 184, 0.15)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, color: '#f1f5f9' }}>Query: '{rec.concept}'</span>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        padding: '0.1rem 0.4rem',
                        borderRadius: '4px',
                        background: rec.is_correct ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: rec.is_correct ? '#34d399' : '#f87171',
                      }}
                    >
                      {rec.is_correct ? 'CORRECT' : 'FAILED'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Predicted: <strong style={{ color: '#e2e8f0' }}>{rec.predicted_value}</strong> (Ground Truth: {rec.ground_truth})
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#cbd5e1' }}>
                    <span>Fidelity: {rec.fidelity.toFixed(3)}</span>
                    <span>Crosstalk Noise: {rec.crosstalk_noise.toFixed(3)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Comparative Diff Inspector */}
      {history.length >= 2 && (
        <div className="case-briefing-panel">
          <div className="panel-title-bar">
            <h3>
              <span>⚖️</span> Experiment A vs B Comparative Diff Inspector
            </h3>
            <button
              onClick={handleCompare}
              disabled={comparing}
              style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '0.4rem 1rem',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              {comparing ? 'Computing Frobenius Delta...' : 'Compare Experiments'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Experiment A:</span>
              <select
                value={compareAId}
                onChange={(e) => setCompareAId(e.target.value)}
                style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid #475569', color: '#fff', padding: '0.3rem 0.6rem', borderRadius: '4px' }}
              >
                {history.map((h) => (
                  <option key={h.experiment_id} value={h.experiment_id}>
                    {h.experiment_id} — {h.config.name}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Experiment B:</span>
              <select
                value={compareBId}
                onChange={(e) => setCompareBId(e.target.value)}
                style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid #475569', color: '#fff', padding: '0.3rem 0.6rem', borderRadius: '4px' }}
              >
                {history.map((h) => (
                  <option key={h.experiment_id} value={h.experiment_id}>
                    {h.experiment_id} — {h.config.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {comparison && (
            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="briefing-metrics-row">
                <div className="metric-pill">
                  <span className="metric-pill-label">Matrix Frobenius Delta ||W_A - W_B||</span>
                  <span className="metric-pill-val">{comparison.matrix_frobenius_difference.toFixed(4)}</span>
                </div>
                <div className="metric-pill">
                  <span className="metric-pill-label">Norm A vs Norm B</span>
                  <span className="metric-pill-val">{comparison.norm_a.toFixed(2)} vs {comparison.norm_b.toFixed(2)}</span>
                </div>
                <div className="metric-pill">
                  <span className="metric-pill-label">Active Synapses Diff</span>
                  <span className="metric-pill-val">{comparison.active_synapses_a} vs {comparison.active_synapses_b}</span>
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(99, 102, 241, 0.1)',
                  borderLeft: '4px solid #6366f1',
                  padding: '0.75rem 1rem',
                  borderRadius: '0 6px 6px 0',
                  fontSize: '0.88rem',
                  color: '#c7d2fe',
                }}
              >
                <strong>Interpretation:</strong> {comparison.interpretation}
              </div>

              <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                <strong>Recall Deltas Across Memories:</strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginTop: '0.5rem' }}>
                  {comparison.recall_diffs.map((rd, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        padding: '0.4rem 0.75rem',
                        background: 'rgba(30, 41, 59, 0.4)',
                        borderRadius: '4px',
                      }}
                    >
                      <span>Memory '{rd.concept}'</span>
                      <span>
                        Fidelity A: {rd.fidelity_a.toFixed(3)} | Fidelity B: {rd.fidelity_b.toFixed(3)} |{' '}
                        <strong style={{ color: rd.delta >= 0 ? '#34d399' : '#f87171' }}>
                          Δ: {rd.delta >= 0 ? `+${rd.delta.toFixed(3)}` : rd.delta.toFixed(3)}
                        </strong>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Session History Log */}
      <div className="case-briefing-panel">
        <div className="panel-title-bar">
          <h3>
            <span>📜</span> Session Research History Log
          </h3>
        </div>
        {history.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: '0.85rem' }}>No experiments executed yet this session.</div>
        ) : (
          <table className="experiment-history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>d</th>
                <th>Decay</th>
                <th>Memories</th>
                <th>Norm</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr
                  key={h.experiment_id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setCurrentResult(h)}
                >
                  <td style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{h.experiment_id}</td>
                  <td style={{ fontWeight: 600 }}>{h.config.name}</td>
                  <td>{h.config.dimension}</td>
                  <td>{h.config.decay}</td>
                  <td>{h.config.memories.length}</td>
                  <td>{h.final_matrix_norm.toFixed(2)}</td>
                  <td style={{ color: '#94a3b8' }}>{new Date(h.created_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
