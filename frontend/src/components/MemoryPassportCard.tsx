import React from 'react'
import type { MemoryPassport } from '../types'

interface MemoryPassportCardProps {
  passport: MemoryPassport | null
  onToggleFollow?: () => void
}

export const MemoryPassportCard: React.FC<MemoryPassportCardProps> = ({
  passport,
  onToggleFollow,
}) => {
  if (!passport) {
    return (
      <div className="passport-card" style={{ color: '#94a3b8' }}>
        No memory selected for passport generation.
      </div>
    )
  }

  return (
    <div className="passport-card">
      <div className="passport-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span className="passport-id-badge">{passport.memory_id}</span>
            <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              {passport.concept}
            </span>
            <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
              = "{passport.value}"
            </span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.25rem' }}>
            Created at T{passport.creation_timestep} · Last Accessed T{passport.last_accessed_timestep}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: passport.current_state === 'STABILIZED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(56, 189, 248, 0.2)',
              color: passport.current_state === 'STABILIZED' ? '#10b981' : '#38bdf8',
              border: passport.current_state === 'STABILIZED' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(56, 189, 248, 0.4)',
            }}
          >
            {passport.current_state}
          </span>

          {onToggleFollow && (
            <button
              onClick={onToggleFollow}
              className={`topbar-follow-toggle ${passport.is_following ? 'active' : ''}`}
              title="Toggle persistent tracking across all workspaces"
            >
              <span>{passport.is_following ? '★' : '☆'}</span>
              <span>{passport.is_following ? 'FOLLOWING' : 'FOLLOW'}</span>
            </button>
          )}
        </div>
      </div>

      <div className="passport-stats-grid">
        <div className="passport-stat-item">
          <span className="passport-stat-label">Recall Fidelity</span>
          <span className="passport-stat-value" style={{ color: passport.recall_fidelity > 0.6 ? '#10b981' : '#ef4444' }}>
            {passport.recall_fidelity.toFixed(3)}
          </span>
        </div>

        <div className="passport-stat-item">
          <span className="passport-stat-label">Active Units</span>
          <span className="passport-stat-value">{passport.active_units}</span>
        </div>

        <div className="passport-stat-item">
          <span className="passport-stat-label">Synaptic Mod</span>
          <span className="passport-stat-value">{passport.synaptic_modifications}</span>
        </div>

        <div className="passport-stat-item">
          <span className="passport-stat-label">Network Overlap</span>
          <span className="passport-stat-value">{passport.overlap_count}</span>
        </div>

        <div className="passport-stat-item">
          <span className="passport-stat-label">Fingerprint ||ΔW||</span>
          <span className="passport-stat-value">{passport.fingerprint_norm.toFixed(3)}</span>
        </div>

        <div className="passport-stat-item">
          <span className="passport-stat-label">Branches</span>
          <span className="passport-stat-value">{passport.branch_count}</span>
        </div>
      </div>
    </div>
  )
}
