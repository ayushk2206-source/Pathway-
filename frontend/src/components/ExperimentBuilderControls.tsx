import React from 'react'
import type { StudioExperimentConfig, StudioExperimentType } from '../types'

interface ExperimentBuilderControlsProps {
  config: StudioExperimentConfig
  onChangeConfig: (newConfig: StudioExperimentConfig) => void
  oneVariableLock: boolean
  onToggleOneVariableLock: () => void
  disabled?: boolean
}

export const ExperimentBuilderControls: React.FC<ExperimentBuilderControlsProps> = ({
  config,
  onChangeConfig,
  oneVariableLock,
  onToggleOneVariableLock,
  disabled = false,
}) => {
  const updateField = <K extends keyof StudioExperimentConfig>(
    key: K,
    val: StudioExperimentConfig[K]
  ) => {
    onChangeConfig({
      ...config,
      [key]: val,
      changed_variable: key,
    })
  }

  return (
    <div className="studio-control-rail">
      {/* Title & One-Variable Lock */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.05em' }}>
          ⚙ EXPERIMENT CONFIGURATION
        </h3>
        <button
          onClick={onToggleOneVariableLock}
          style={{
            padding: '3px 8px',
            fontSize: '0.68rem',
            fontWeight: 700,
            borderRadius: '4px',
            cursor: 'pointer',
            background: oneVariableLock ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.05)',
            border: `1px solid ${oneVariableLock ? '#38bdf8' : 'rgba(255, 255, 255, 0.15)'}`,
            color: oneVariableLock ? '#38bdf8' : '#94a3b8',
          }}
          title="When locked, changing a variable marks it as the single independent variable while holding others constant."
        >
          {oneVariableLock ? '🔒 ONE-VARIABLE LOCKED' : '🔓 UNLOCKED'}
        </button>
      </div>

      {/* Experiment Type Selector */}
      <div className="studio-param-field">
        <div className="studio-param-header">
          <span className="studio-param-title">Experiment Type</span>
          <span className="studio-param-value-pill">{config.experiment_type}</span>
        </div>
        <select
          value={config.experiment_type}
          onChange={(e) => updateField('experiment_type', e.target.value as StudioExperimentType)}
          disabled={disabled || oneVariableLock}
          style={{
            background: '#0f172a',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#f8fafc',
            padding: '4px 6px',
            borderRadius: '4px',
            fontSize: '0.78rem',
            cursor: 'pointer',
          }}
        >
          <option value="ENCODING">ENCODING (Basic Hebbian Write)</option>
          <option value="INTERFERENCE">INTERFERENCE (Competing Memory)</option>
          <option value="SURGERY">SURGERY (Targeted Synapse Clamp)</option>
          <option value="COUNTERFACTUAL">COUNTERFACTUAL (Alternate Plasticity)</option>
          <option value="PERSISTENCE">PERSISTENCE (Decay Time Series)</option>
          <option value="COMPARISON">COMPARISON (Dual Concept Structure)</option>
        </select>
        <div className="studio-param-desc">
          Defines the experimental paradigm executed against the underlying Synaptic Brain substrate.
        </div>
      </div>

      {/* Target Memory A Inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        <div className="studio-param-field">
          <div className="studio-param-header">
            <span className="studio-param-title">Cue Concept (k)</span>
          </div>
          <input
            type="text"
            value={config.concept_a}
            onChange={(e) => updateField('concept_a', e.target.value)}
            disabled={disabled}
            style={{
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#38bdf8',
              padding: '4px 6px',
              borderRadius: '4px',
              fontSize: '0.78rem',
              fontWeight: 700,
            }}
          />
        </div>
        <div className="studio-param-field">
          <div className="studio-param-header">
            <span className="studio-param-title">Target Value (v)</span>
          </div>
          <input
            type="text"
            value={config.value_a}
            onChange={(e) => updateField('value_a', e.target.value)}
            disabled={disabled}
            style={{
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#34d399',
              padding: '4px 6px',
              borderRadius: '4px',
              fontSize: '0.78rem',
              fontWeight: 700,
            }}
          />
        </div>
      </div>

      {/* Plasticity Learning Rate (η) */}
      <div className="studio-param-field">
        <div className="studio-param-header">
          <span className="studio-param-title">Plasticity Rate (η)</span>
          <span className="studio-param-value-pill">{config.update_strength.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min={0.1}
          max={2.0}
          step={0.05}
          value={config.update_strength}
          onChange={(e) => updateField('update_strength', parseFloat(e.target.value))}
          disabled={disabled}
          className="studio-slider"
        />
        <div className="studio-param-range">
          <span>0.1 (Gentle trace)</span>
          <span>2.0 (High gain)</span>
        </div>
        <div className="studio-param-desc">
          Hebbian learning rate scaling factor η in update ΔW = η(v ⊗ k). Higher values create larger initial synaptic changes.
        </div>
      </div>

      {/* Synaptic Decay (λ) */}
      <div className="studio-param-field">
        <div className="studio-param-header">
          <span className="studio-param-title">Synaptic Decay Rate (λ)</span>
          <span className="studio-param-value-pill">{config.decay.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min={0.0}
          max={0.5}
          step={0.01}
          value={config.decay}
          onChange={(e) => updateField('decay', parseFloat(e.target.value))}
          disabled={disabled}
          className="studio-slider"
        />
        <div className="studio-param-range">
          <span>0.00 (Permanent)</span>
          <span>0.50 (Rapid leak)</span>
        </div>
        <div className="studio-param-desc">
          Exponential fading parameter λ in W(t+1) = (1 - λ)W(t) + ΔW. Controls the temporal forgetting horizon.
        </div>
      </div>

      {/* Dynamic Conditional Controls */}
      {config.experiment_type === 'INTERFERENCE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '0.5rem', background: 'rgba(245, 158, 11, 0.05)', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#fbbf24' }}>⚡ INTERFERENCE PARAMETERS</span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
            <input
              type="text"
              placeholder="Interfering concept"
              value={config.interfering_concept}
              onChange={(e) => updateField('interfering_concept', e.target.value)}
              style={{ background: '#0f172a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px', borderRadius: '4px', fontSize: '0.75rem' }}
            />
            <input
              type="text"
              placeholder="Interfering value"
              value={config.interfering_value}
              onChange={(e) => updateField('interfering_value', e.target.value)}
              style={{ background: '#0f172a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px', borderRadius: '4px', fontSize: '0.75rem' }}
            />
          </div>
          <div className="studio-param-header" style={{ marginTop: '4px' }}>
            <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Interference Strength</span>
            <span className="studio-param-value-pill">{config.interfering_strength.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0.0}
            max={2.0}
            step={0.1}
            value={config.interfering_strength}
            onChange={(e) => updateField('interfering_strength', parseFloat(e.target.value))}
            className="studio-slider"
          />
        </div>
      )}

      {config.experiment_type === 'SURGERY' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '0.5rem', background: 'rgba(236, 72, 153, 0.05)', borderRadius: '6px', border: '1px solid rgba(236, 72, 153, 0.2)' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#f472b6' }}>⚕ MICRO-SURGERY INTERVENTION</span>
          <select
            value={config.surgery_action}
            onChange={(e) => updateField('surgery_action', e.target.value as any)}
            style={{ background: '#0f172a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', padding: '4px', borderRadius: '4px', fontSize: '0.75rem' }}
          >
            <option value="zero">Zero Weight (Ablate connection)</option>
            <option value="clamp_high">Clamp High (+2.0 maximum excitation)</option>
            <option value="invert">Invert Polarity (Excitatory &lt;-&gt; Inhibitory)</option>
            <option value="attenuate">Attenuate by 80%</option>
          </select>
        </div>
      )}

      {config.experiment_type === 'PERSISTENCE' && (
        <div className="studio-param-field">
          <div className="studio-param-header">
            <span className="studio-param-title">Decay Cycles (Steps)</span>
            <span className="studio-param-value-pill">{config.decay_cycles}</span>
          </div>
          <input
            type="range"
            min={1}
            max={20}
            step={1}
            value={config.decay_cycles}
            onChange={(e) => updateField('decay_cycles', parseInt(e.target.value, 10))}
            className="studio-slider"
          />
          <div className="studio-param-desc">
            Number of consecutive resting cycles without inputs to observe exponential fading.
          </div>
        </div>
      )}

      {/* Seed & Matrix Dimension */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        <div className="studio-param-field">
          <div className="studio-param-header">
            <span className="studio-param-title">Seed (Determinism)</span>
          </div>
          <input
            type="number"
            value={config.seed}
            onChange={(e) => updateField('seed', parseInt(e.target.value, 10) || 42)}
            disabled={disabled}
            style={{
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#f8fafc',
              padding: '4px 6px',
              borderRadius: '4px',
              fontSize: '0.78rem',
              fontFamily: 'monospace',
            }}
          />
        </div>
        <div className="studio-param-field">
          <div className="studio-param-header">
            <span className="studio-param-title">Substrate Dim (d)</span>
          </div>
          <select
            value={config.d}
            onChange={(e) => updateField('d', parseInt(e.target.value, 10))}
            disabled={disabled || oneVariableLock}
            style={{
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#f8fafc',
              padding: '4px 6px',
              borderRadius: '4px',
              fontSize: '0.78rem',
            }}
          >
            <option value={8}>8 x 8 (64 synapses)</option>
            <option value={16}>16 x 16 (256 synapses)</option>
            <option value={32}>32 x 32 (1024 synapses)</option>
          </select>
        </div>
      </div>
    </div>
  )
}
