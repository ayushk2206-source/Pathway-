import React, { useMemo, useState } from 'react'
import type { SynapticConnection, SynapticNeuron, SynapticPathway } from '../types'

interface SynapticNetworkCanvasProps {
  dimension: number
  neurons: SynapticNeuron[]
  synapses: SynapticConnection[]
  lastPathway: SynapticPathway | null
  selectedNeuronId: string | null
  selectedSynapseId: string | null
  onSelectNeuron: (neuronId: string | null) => void
  onSelectSynapse: (synapseId: string | null) => void
  layoutMode: 'bipartite' | 'radial' | 'matrix'
  showLabels?: boolean
  showAllSynapses?: boolean
}

export const SynapticNetworkCanvas: React.FC<SynapticNetworkCanvasProps> = ({
  dimension,
  neurons,
  synapses,
  lastPathway,
  selectedNeuronId,
  selectedSynapseId,
  onSelectNeuron,
  onSelectSynapse,
  layoutMode,
  showLabels = true,
  showAllSynapses = true,
}) => {
  const [hoveredNeuronId, setHoveredNeuronId] = useState<string | null>(null)
  const [hoveredSynapseId, setHoveredSynapseId] = useState<string | null>(null)

  const width = 740
  const height = 520
  const padding = 50

  // Quick lookup maps
  const activeSynapseSet = useMemo(() => {
    return new Set(lastPathway?.active_synapse_ids || [])
  }, [lastPathway])

  const activeKeySet = useMemo(() => {
    return new Set(lastPathway?.active_key_indices || [])
  }, [lastPathway])

  const activeValueSet = useMemo(() => {
    return new Set(lastPathway?.active_value_indices || [])
  }, [lastPathway])

  // Split neurons into input keys and output values
  const keyNeurons = useMemo(() => neurons.filter((n) => n.neuron_type === 'input_key'), [neurons])
  const valueNeurons = useMemo(() => neurons.filter((n) => n.neuron_type === 'output_value'), [neurons])

  // Compute node coordinates based on layout
  const nodePositions = useMemo(() => {
    const pos = new Map<string, { x: number; y: number }>()

    if (layoutMode === 'bipartite') {
      // Input Key units on left, Output Value units on right
      const kCount = keyNeurons.length || dimension
      const vCount = valueNeurons.length || dimension

      const kStep = (height - 2 * padding) / Math.max(1, kCount - 1)
      const vStep = (height - 2 * padding) / Math.max(1, vCount - 1)

      keyNeurons.forEach((n, idx) => {
        pos.set(n.id, { x: padding + 60, y: padding + idx * kStep })
      })

      valueNeurons.forEach((n, idx) => {
        pos.set(n.id, { x: width - padding - 60, y: padding + idx * vStep })
      })
    } else if (layoutMode === 'radial') {
      // Radial ring: Key neurons on outer left semicircle, Value neurons on outer right semicircle
      const centerX = width / 2
      const centerY = height / 2
      const radius = Math.min(width, height) / 2 - padding - 20

      const kCount = keyNeurons.length || dimension
      const vCount = valueNeurons.length || dimension

      keyNeurons.forEach((n, idx) => {
        // Left arc from pi/2 to 3pi/2
        const angle = Math.PI / 2 + (Math.PI * (idx + 0.5)) / Math.max(1, kCount)
        pos.set(n.id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        })
      })

      valueNeurons.forEach((n, idx) => {
        // Right arc from -pi/2 to pi/2
        const angle = -Math.PI / 2 + (Math.PI * (idx + 0.5)) / Math.max(1, vCount)
        pos.set(n.id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        })
      })
    }

    return pos
  }, [layoutMode, keyNeurons, valueNeurons, dimension, width, height, padding])

  // Max weight for relative normalization
  const maxWeight = useMemo(() => {
    return synapses.reduce((acc, s) => Math.max(acc, s.abs_weight), 0.001)
  }, [synapses])

  // Determine if a synapse is connected to hovered or selected neuron
  const isSynapseRelevant = (s: SynapticConnection) => {
    if (selectedSynapseId && s.id === selectedSynapseId) return true
    if (hoveredSynapseId && s.id === hoveredSynapseId) return true
    if (hoveredNeuronId) {
      return s.source === hoveredNeuronId || s.target === hoveredNeuronId
    }
    if (selectedNeuronId) {
      return s.source === selectedNeuronId || s.target === selectedNeuronId
    }
    return false
  }

  // Filter synapses to render
  const visibleSynapses = useMemo(() => {
    if (showAllSynapses) return synapses
    return synapses.filter((s) => s.abs_weight > 0.01 || activeSynapseSet.has(s.id))
  }, [synapses, showAllSynapses, activeSynapseSet])

  return (
    <div className="synaptic-canvas-container">
      {layoutMode === 'matrix' ? (
        /* Matrix Heatmap Crossbar View */
        <div className="synaptic-matrix-view">
          <div className="matrix-view-header">
            <span className="matrix-view-title">Synaptic Weight Crossbar Matrix W (d={dimension}×{dimension})</span>
            <span className="matrix-view-legend">
              <span className="dot excitatory" /> Excitatory (+)
              <span className="dot inhibitory" /> Inhibitory (−)
              <span className="dot neutral" /> Resting (0)
            </span>
          </div>

          <div
            className="synaptic-matrix-grid"
            style={{
              gridTemplateColumns: `repeat(${dimension}, minmax(18px, 1fr))`,
            }}
          >
            {Array.from({ length: dimension }).map((_, i) =>
              Array.from({ length: dimension }).map((_, j) => {
                const synId = `syn_k${j}_v${i}`
                const syn = synapses.find((s) => s.id === synId)
                const weight = syn?.weight ?? 0
                const isSelected = selectedSynapseId === synId
                const isActive = activeSynapseSet.has(synId)

                const intensity = Math.min(1, Math.abs(weight) / maxWeight)
                const isExcitatory = weight > 1e-5
                const isInhibitory = weight < -1e-5

                const bg = isExcitatory
                  ? `rgba(56, 189, 248, ${0.15 + intensity * 0.85})`
                  : isInhibitory
                  ? `rgba(244, 63, 94, ${0.15 + intensity * 0.85})`
                  : 'rgba(255, 255, 255, 0.03)'

                return (
                  <button
                    key={`${i}-${j}`}
                    type="button"
                    className={`matrix-cell ${isSelected ? 'selected' : ''} ${isActive ? 'active-path' : ''}`}
                    style={{ backgroundColor: bg }}
                    onClick={() => onSelectSynapse(synId)}
                    title={`Synapse K${j} -> V${i} | Weight: ${weight.toFixed(4)}`}
                  >
                    {dimension <= 16 && (
                      <span className="matrix-cell-text">
                        {Math.abs(weight) > 0.05 ? weight.toFixed(2) : ''}
                      </span>
                    )}
                  </button>
                )
              })
            )}
          </div>
          <div className="matrix-axis-labels">
            <span>← Pre-synaptic Key Inputs (K) →</span>
            <span>↓ Post-synaptic Value Outputs (V)</span>
          </div>
        </div>
      ) : (
        /* SVG 2D Neural Network Topology View */
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="synaptic-svg"
          onClick={() => {
            onSelectNeuron(null)
            onSelectSynapse(null)
          }}
        >
          <defs>
            {/* Background scientific grid */}
            <pattern id="synapticGrid" width="24" height="24" patternUnits="userSpaceOnUse">
              <path d="M 24 0 L 0 0 0 24" fill="none" stroke="rgba(255, 255, 255, 0.025)" strokeWidth="1" />
            </pattern>

            {/* Glowing marker for pathway impulses */}
            <filter id="synapticGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>

            <linearGradient id="excitatoryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#34d399" />
            </linearGradient>

            <linearGradient id="inhibitoryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fb923c" />
              <stop offset="100%" stopColor="#f43f5e" />
            </linearGradient>
          </defs>

          {/* Grid Background */}
          <rect width={width} height={height} fill="url(#synapticGrid)" />

          {/* Layer Headers for Bipartite */}
          {layoutMode === 'bipartite' && (
            <g className="layer-headers" opacity="0.6">
              <text x={padding + 60} y={padding - 18} fill="var(--cyan)" fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)">
                PRE-SYNAPTIC KEY (K)
              </text>
              <text x={width - padding - 60} y={padding - 18} fill="var(--emerald)" fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)">
                POST-SYNAPTIC VALUE (V)
              </text>
            </g>
          )}

          {/* Synaptic Connections (Edges) */}
          <g className="synapses-layer">
            {visibleSynapses.map((syn) => {
              const srcPos = nodePositions.get(syn.source)
              const tgtPos = nodePositions.get(syn.target)
              if (!srcPos || !tgtPos) return null

              const isSelected = selectedSynapseId === syn.id
              const isHovered = hoveredSynapseId === syn.id
              const isRelevant = isSynapseRelevant(syn)
              const isActive = activeSynapseSet.has(syn.id)

              const weightNorm = Math.min(1, syn.abs_weight / maxWeight)
              const isExcitatory = syn.polarity === 'excitatory'

              // Visual encoding for strength
              let strokeWidth = 1.0
              if (syn.tier === 'strong') strokeWidth = 3.6
              else if (syn.tier === 'medium') strokeWidth = 2.0
              else strokeWidth = 1.0

              if (isActive || isSelected || isHovered) {
                strokeWidth += 1.6
              }

              let opacity = 0.15 + weightNorm * 0.75
              if (hoveredNeuronId || selectedNeuronId) {
                opacity = isRelevant ? 0.95 : 0.05
              } else if (isActive) {
                opacity = 0.95
              }

              const strokeColor = isExcitatory
                ? isActive
                  ? '#38bdf8'
                  : 'rgba(56, 189, 248, ' + opacity + ')'
                : syn.polarity === 'inhibitory'
                ? isActive
                  ? '#f43f5e'
                  : 'rgba(244, 63, 94, ' + opacity + ')'
                : 'rgba(148, 163, 184, 0.12)'

              // Curved bezier path for organic scientific look
              const midX = (srcPos.x + tgtPos.x) / 2
              const midY = (srcPos.y + tgtPos.y) / 2
              const dx = tgtPos.x - srcPos.x
              const dy = tgtPos.y - srcPos.y
              const curveOffset = layoutMode === 'radial' ? 30 : (syn.target_idx - syn.source_idx) * 2.5

              const cpX = midX - dy * 0.08 + (layoutMode === 'radial' ? (midX - width / 2) * 0.2 : 0)
              const cpY = midY + dx * 0.08 + curveOffset * 0.4

              const pathD = `M ${srcPos.x} ${srcPos.y} Q ${cpX} ${cpY} ${tgtPos.x} ${tgtPos.y}`

              return (
                <g key={syn.id}>
                  <path
                    d={pathD}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    className={`synapse-path ${isActive ? 'synapse-active-pulse' : ''}`}
                    filter={isActive ? 'url(#synapticGlow)' : undefined}
                    onClick={(e) => {
                      e.stopPropagation()
                      onSelectSynapse(syn.id)
                    }}
                    onMouseEnter={() => setHoveredSynapseId(syn.id)}
                    onMouseLeave={() => setHoveredSynapseId(null)}
                    style={{ cursor: 'pointer' }}
                  />
                  {/* Weight label on active or selected synapses */}
                  {(isSelected || isActive) && syn.abs_weight > 0.01 && (
                    <text
                      x={cpX}
                      y={cpY - 4}
                      fill={isExcitatory ? '#38bdf8' : '#f43f5e'}
                      fontSize="9"
                      fontFamily="var(--font-mono)"
                      textAnchor="middle"
                      className="synapse-weight-tag"
                    >
                      {syn.weight > 0 ? '+' : ''}{syn.weight.toFixed(3)}
                    </text>
                  )}
                </g>
              )
            })}
          </g>

          {/* Neurons (Nodes) */}
          <g className="neurons-layer">
            {neurons.map((neuron) => {
              const pos = nodePositions.get(neuron.id)
              if (!pos) return null

              const isKey = neuron.neuron_type === 'input_key'
              const isSelected = selectedNeuronId === neuron.id
              const isHovered = hoveredNeuronId === neuron.id
              const isActive = isKey ? activeKeySet.has(neuron.index) : activeValueSet.has(neuron.index)

              const activationAbs = Math.abs(neuron.activation)
              const nodeRadius = 8 + Math.min(6, activationAbs * 8)

              let fillColor = isKey ? 'var(--cyan)' : 'var(--emerald)'
              if (neuron.activation < -0.05) {
                fillColor = 'var(--crimson)'
              } else if (Math.abs(neuron.activation) < 0.01) {
                fillColor = '#334155'
              }

              return (
                <g
                  key={neuron.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={(e) => {
                    e.stopPropagation()
                    onSelectNeuron(neuron.id)
                  }}
                  onMouseEnter={() => setHoveredNeuronId(neuron.id)}
                  onMouseLeave={() => setHoveredNeuronId(null)}
                  style={{ cursor: 'pointer' }}
                  className="neuron-group"
                >
                  {/* Outer active halo */}
                  {(isActive || isSelected || isHovered) && (
                    <circle
                      r={nodeRadius + 6}
                      fill="none"
                      stroke={fillColor}
                      strokeWidth="1.5"
                      strokeDasharray="3 2"
                      opacity="0.7"
                      className="neuron-halo-pulse"
                    />
                  )}

                  {/* Node Circle */}
                  <circle
                    r={nodeRadius}
                    fill={fillColor}
                    fillOpacity={0.85}
                    stroke={isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.4)'}
                    strokeWidth={isSelected ? 2.5 : 1}
                    filter={isActive ? 'url(#synapticGlow)' : undefined}
                  />

                  {/* Numeric Index */}
                  <text
                    y="3.5"
                    fill="#05070c"
                    fontSize="9"
                    fontWeight="700"
                    fontFamily="var(--font-mono)"
                    textAnchor="middle"
                  >
                    {neuron.index}
                  </text>

                  {/* Label */}
                  {showLabels && (
                    <text
                      x={isKey ? -16 : 16}
                      y="4"
                      fill={isActive ? '#ffffff' : 'var(--text-muted)'}
                      fontSize="10"
                      fontFamily="var(--font-mono)"
                      textAnchor={isKey ? 'end' : 'start'}
                    >
                      {isKey ? `K-${neuron.index}` : `V-${neuron.index}`}
                      {neuron.activation !== 0 && ` (${neuron.activation > 0 ? '+' : ''}${neuron.activation.toFixed(2)})`}
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        </svg>
      )}
    </div>
  )
}
