import React from 'react'

export type SciBadgeType =
  | 'published'
  | 'pathway'
  | 'live'
  | 'precomputed'
  | 'synthetic'
  | 'simplified'

interface SciBadgeProps {
  type: SciBadgeType
  label?: string
  tooltip?: string
}

const BADGE_CONFIG: Record<SciBadgeType, { defaultLabel: string; className: string; description: string }> = {
  published: {
    defaultLabel: 'PUBLISHED RESEARCH',
    className: 'published',
    description: 'Directly grounded in peer-reviewed scientific literature with DOI reference.',
  },
  pathway: {
    defaultLabel: 'PATHWAY MODEL',
    className: 'pathway',
    description: 'Specific computational implementation inside the Pathway interactive engine.',
  },
  live: {
    defaultLabel: 'LIVE COMPUTATION',
    className: 'live',
    description: 'Dynamically computed in real time via live matrix algebra forward pass.',
  },
  precomputed: {
    defaultLabel: 'PRECOMPUTED BENCHMARK',
    className: 'precomputed',
    description: 'Deterministic benchmark computed offline across parameter sweeps.',
  },
  synthetic: {
    defaultLabel: 'SYNTHETIC PATTERNS',
    className: 'synthetic',
    description: 'Mathematically generated pseudo-random Gaussian vectors for clean didactic demonstration.',
  },
  simplified: {
    defaultLabel: 'TEACHING SIMPLIFICATION',
    className: 'simplified',
    description: 'Deliberately simplified linear model omitting spike timing, biochemical cascades, and dendritic geometry.',
  },
}

export const SciBadge: React.FC<SciBadgeProps> = ({ type, label, tooltip }) => {
  const config = BADGE_CONFIG[type]
  const displayLabel = label || config.defaultLabel
  const titleText = tooltip || config.description

  return (
    <span className={`sci-badge ${config.className}`} title={titleText}>
      {displayLabel}
    </span>
  )
}

export default SciBadge
