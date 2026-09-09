import React, { useEffect, useRef, useState, useCallback } from 'react'
import type { MemoryMapPoint, MemoryRelationshipGraph, MemorySnapshot, Snapshot } from '../types'

interface MemoryFieldCanvasProps {
  snapshot: MemorySnapshot | Snapshot | null
  mapPoints: MemoryMapPoint[]
  graph: MemoryRelationshipGraph | null
  selectedMemoryId: string | null
  onSelectMemory: (id: string) => void
  activeTimestep: number
  lastModifiedMemoryId?: string | null
}

// Restrained, semantic cluster palette — no gratuitous cyan everywhere
const CLUSTER_PALETTE = [
  '#38bdf8', // ice-blue (primary accent)
  '#10b981', // emerald
  '#8b5cf6', // violet
  '#f59e0b', // amber
  '#f43f5e', // crimson
  '#64748b', // slate
  '#06b6d4', // cyan
]

// Particle field for ambient depth
interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  opacity: number
  radius: number
}

export const MemoryFieldCanvas: React.FC<MemoryFieldCanvasProps> = ({
  snapshot,
  mapPoints,
  graph,
  selectedMemoryId,
  onSelectMemory,
  activeTimestep,
  lastModifiedMemoryId,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const particlesRef = useRef<Particle[]>([])
  const animFrameRef = useRef<number>(0)
  const phaseRef = useRef(0)

  const [hoveredMemoryId, setHoveredMemoryId] = useState<string | null>(null)
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null)
  const [hoveredData, setHoveredData] = useState<{
    id: string
    concept: string
    strength: number
    cluster: number
    causalCount: number
  } | null>(null)

  // Init ambient particles
  const initParticles = useCallback((w: number, h: number) => {
    const count = Math.min(60, Math.floor((w * h) / 14000))
    particlesRef.current = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
      opacity: 0.04 + Math.random() * 0.08,
      radius: 0.5 + Math.random() * 1.5,
    }))
  }, [])

  // Map layout helpers
  const getLayoutMaps = useCallback(
    (width: number, height: number) => {
      const pad = 64
      const xs = mapPoints.map((p) => p.x)
      const ys = mapPoints.map((p) => p.y)
      const minX = xs.length ? Math.min(...xs) : -1
      const maxX = xs.length ? Math.max(...xs) : 1
      const minY = ys.length ? Math.min(...ys) : -1
      const maxY = ys.length ? Math.max(...ys) : 1
      const rangeX = maxX - minX || 1
      const rangeY = maxY - minY || 1
      const toX = (x: number) => pad + ((x - minX) / rangeX) * (width - 2 * pad)
      const toY = (y: number) => pad + ((y - minY) / rangeY) * (height - 2 * pad)

      // Build screen coords
      const screenCoords: Record<string, { x: number; y: number }> = {}
      if (mapPoints.length) {
        mapPoints.forEach((p) => {
          screenCoords[p.memory_id] = { x: toX(p.x), y: toY(p.y) }
        })
      } else {
        // Circular fallback from strength snapshot
        const hasStr =
          snapshot && 'memory_strength' in snapshot && snapshot.memory_strength
        if (hasStr) {
          const ids = Object.keys((snapshot as MemorySnapshot).memory_strength)
          const count = ids.length
          const cx = width / 2
          const cy = height / 2
          const r = Math.min(width, height) * 0.33
          ids.forEach((id, i) => {
            const theta = (i / count) * Math.PI * 2 - Math.PI / 2
            screenCoords[id] = {
              x: cx + Math.cos(theta) * r,
              y: cy + Math.sin(theta) * r,
            }
          })
        }
      }
      return screenCoords
    },
    [mapPoints, snapshot]
  )

  // Main render loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const render = () => {
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth
      const h = canvas.clientHeight

      if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
        canvas.width = w * dpr
        canvas.height = h * dpr
        initParticles(w, h)
      }

      ctx.save()
      ctx.scale(dpr, dpr)
      ctx.clearRect(0, 0, w, h)

      phaseRef.current = (phaseRef.current + 0.018) % (Math.PI * 2)
      const phase = phaseRef.current

      // ── 1. Ambient Particle Field ────────────────────────────────
      particlesRef.current.forEach((p) => {
        p.x = (p.x + p.vx + w) % w
        p.y = (p.y + p.vy + h) % h
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(148, 163, 184, ${p.opacity})`
        ctx.fill()
      })

      // ── 2. No data state ─────────────────────────────────────────
      const hasStrength = Boolean(
        snapshot &&
          'memory_strength' in snapshot &&
          snapshot.memory_strength &&
          Object.keys(snapshot.memory_strength).length > 0
      )

      if (!mapPoints.length && !hasStrength) {
        ctx.fillStyle = 'rgba(79, 96, 112, 0.4)'
        ctx.font = '12px "Inter", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('Memory field void — run an experiment to observe the substrate', w / 2, h / 2)
        ctx.restore()
        animFrameRef.current = requestAnimationFrame(render)
        return
      }

      const screenCoords = getLayoutMaps(w, h)
      const activeStrengths: Record<string, number> =
        snapshot && 'memory_strength' in snapshot && snapshot.memory_strength
          ? (snapshot as MemorySnapshot).memory_strength
          : {}

      // ── 3. Causal / relationship edges ───────────────────────────
      if (graph?.edges) {
        graph.edges.forEach((edge) => {
          const src = screenCoords[edge.source]
          const tgt = screenCoords[edge.target]
          if (!src || !tgt) return

          const isRelatedToSelected =
            selectedMemoryId &&
            (edge.source === selectedMemoryId || edge.target === selectedMemoryId)
          const isRelatedToHovered =
            hoveredMemoryId &&
            (edge.source === hoveredMemoryId || edge.target === hoveredMemoryId)

          // Base opacity — dim non-focused edges when something is selected/hovered
          let baseAlpha: number
          if (selectedMemoryId || hoveredMemoryId) {
            baseAlpha = isRelatedToSelected || isRelatedToHovered ? 0.6 : 0.04
          } else {
            baseAlpha = Math.max(0.04, edge.weight * 0.35)
          }

          let strokeColor: string
          let dashArr: number[] = []
          let lineW = Math.max(0.5, edge.weight * 2)

          if (edge.relationship === 'COMPETITION') {
            strokeColor = `rgba(244, 63, 94, ${baseAlpha})`
            dashArr = [4, 5]
            lineW = Math.max(0.5, edge.weight * 2.5)
          } else if (edge.relationship === 'REINFORCEMENT') {
            strokeColor = `rgba(16, 185, 129, ${baseAlpha})`
          } else {
            strokeColor = `rgba(148, 163, 184, ${baseAlpha})`
          }

          ctx.beginPath()
          ctx.moveTo(src.x, src.y)
          ctx.lineTo(tgt.x, tgt.y)
          ctx.strokeStyle = strokeColor
          ctx.setLineDash(dashArr)
          ctx.lineWidth = lineW
          ctx.stroke()
          ctx.setLineDash([])
        })
      }

      // ── 4. Trajectory tails ───────────────────────────────────────
      mapPoints.forEach((p) => {
        if (p.trajectory_tail && p.trajectory_tail.length > 1) {
          const coords = getLayoutMaps(w, h)
          const cx = coords[p.memory_id]?.x
          const cy = coords[p.memory_id]?.y
          if (!cx || !cy) return

          const xs2 = mapPoints.map((q) => q.x)
          const ys2 = mapPoints.map((q) => q.y)
          const minX2 = Math.min(...xs2)
          const maxX2 = Math.max(...xs2)
          const minY2 = Math.min(...ys2)
          const maxY2 = Math.max(...ys2)
          const rX2 = maxX2 - minX2 || 1
          const rY2 = maxY2 - minY2 || 1
          const toX2 = (x: number) => 64 + ((x - minX2) / rX2) * (w - 128)
          const toY2 = (y: number) => 64 + ((y - minY2) / rY2) * (h - 128)

          ctx.beginPath()
          const first = p.trajectory_tail[0]
          ctx.moveTo(toX2(first[0]), toY2(first[1]))
          for (let i = 1; i < p.trajectory_tail.length; i++) {
            const pt = p.trajectory_tail[i]
            ctx.lineTo(toX2(pt[0]), toY2(pt[1]))
          }
          ctx.strokeStyle = 'rgba(99, 116, 143, 0.2)'
          ctx.lineWidth = 1
          ctx.setLineDash([2, 4])
          ctx.stroke()
          ctx.setLineDash([])
        }
      })

      // ── 5. Memory Nodes ───────────────────────────────────────────
      const hasHoverFocus = hoveredMemoryId !== null
      const hasSelFocus = selectedMemoryId !== null

      Object.entries(screenCoords).forEach(([mId, pos]) => {
        const pt = mapPoints.find((p) => p.memory_id === mId)
        const strength = activeStrengths[mId] !== undefined
          ? activeStrengths[mId]
          : (pt?.strength ?? 0)
        const clusterIdx = pt ? pt.cluster % CLUSTER_PALETTE.length : 0
        const color = CLUSTER_PALETTE[clusterIdx]

        const isSelected = selectedMemoryId === mId
        const isHovered = hoveredMemoryId === mId
        const isModified = lastModifiedMemoryId === mId
        const isFocused = isSelected || isHovered

        // Dimming for context isolation
        const isRelated = (() => {
          if (!hasHoverFocus && !hasSelFocus) return false
          const focusId = hoveredMemoryId || selectedMemoryId
          if (mId === focusId) return true
          if (!graph?.edges) return false
          return graph.edges.some(
            (e) =>
              (e.source === focusId && e.target === mId) ||
              (e.target === focusId && e.source === mId)
          )
        })()

        // Node opacity: isolated view when focused
        let globalAlpha = 1
        if ((hasHoverFocus || hasSelFocus) && !isFocused && !isRelated) {
          globalAlpha = 0.15
        }
        ctx.globalAlpha = globalAlpha

        // Node radii based on state
        const baseR = 4 + Math.max(0, Math.min(1, strength)) * 14
        const haloR = isSelected
          ? baseR + 8 + Math.sin(phase) * 2.5
          : isModified
          ? baseR + 5 + Math.sin(phase * 1.5) * 2
          : 0

        // Outer halo (selected/modified only)
        if (haloR > 0) {
          ctx.beginPath()
          ctx.arc(pos.x, pos.y, haloR, 0, Math.PI * 2)
          ctx.strokeStyle = isSelected
            ? `rgba(56, 189, 248, ${0.3 + 0.1 * Math.sin(phase)})`
            : `rgba(245, 158, 11, ${0.25 + 0.1 * Math.sin(phase)})`
          ctx.lineWidth = 1
          ctx.stroke()
        }

        // Soft radial glow (strong memories only)
        if (strength > 0.4 || isSelected || isHovered) {
          const glowR = baseR * (isHovered ? 2.8 : 2.2)
          const grad = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, glowR)
          const glowAlpha = isSelected ? 0.25 : isHovered ? 0.2 : strength * 0.12
          grad.addColorStop(0, color.replace(')', `, ${glowAlpha})`).replace('rgb', 'rgba'))

          // Parse hex color to rgba properly
          const hex = color.replace('#', '')
          const r = parseInt(hex.slice(0, 2), 16)
          const g = parseInt(hex.slice(2, 4), 16)
          const b = parseInt(hex.slice(4, 6), 16)
          const glowGrad = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, glowR)
          glowGrad.addColorStop(0, `rgba(${r},${g},${b},${glowAlpha})`)
          glowGrad.addColorStop(1, `rgba(${r},${g},${b},0)`)
          ctx.fillStyle = glowGrad
          ctx.beginPath()
          ctx.arc(pos.x, pos.y, glowR, 0, Math.PI * 2)
          ctx.fill()
        }

        // Solid node body
        const nodeR = isHovered ? baseR * 1.2 : baseR
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, nodeR, 0, Math.PI * 2)
        const hex = color.replace('#', '')
        const r2 = parseInt(hex.slice(0, 2), 16)
        const g2 = parseInt(hex.slice(2, 4), 16)
        const b2 = parseInt(hex.slice(4, 6), 16)
        // Dimmer for dormant (low strength), brighter for active
        const bodyAlpha = 0.35 + Math.min(1, strength) * 0.65
        ctx.fillStyle = isSelected
          ? '#f0f2f5'
          : `rgba(${r2},${g2},${b2},${bodyAlpha})`
        ctx.fill()

        // Node border
        ctx.strokeStyle = isSelected
          ? 'rgba(56, 189, 248, 0.9)'
          : `rgba(${r2},${g2},${b2},0.5)`
        ctx.lineWidth = isSelected ? 1.5 : 1
        ctx.stroke()

        // Decaying: dashed outer ring
        if (strength < 0.2 && !isSelected) {
          ctx.beginPath()
          ctx.arc(pos.x, pos.y, nodeR + 3, 0, Math.PI * 2)
          ctx.setLineDash([2, 3])
          ctx.strokeStyle = `rgba(${r2},${g2},${b2},0.25)`
          ctx.lineWidth = 0.75
          ctx.stroke()
          ctx.setLineDash([])
        }

        // Label — only for hovered/selected or if zoomed enough
        if (isFocused || strength > 0.7) {
          const labelText = pt ? pt.label : mId
          ctx.font = isSelected
            ? '600 11px "JetBrains Mono", monospace'
            : '500 10px "Inter", sans-serif'
          ctx.fillStyle = isSelected
            ? '#f0f2f5'
            : `rgba(${r2},${g2},${b2},${0.5 + strength * 0.5})`
          ctx.textAlign = 'center'
          ctx.fillText(labelText, pos.x, pos.y + nodeR + 12)
        } else if (isModified) {
          const labelText = pt ? pt.label : mId
          ctx.font = '500 10px "Inter", sans-serif'
          ctx.fillStyle = 'rgba(245, 158, 11, 0.7)'
          ctx.textAlign = 'center'
          ctx.fillText(labelText, pos.x, pos.y + nodeR + 12)
        }

        ctx.globalAlpha = 1
      })

      // ── 6. Causal propagation pulse (for lastModifiedMemoryId) ───
      if (lastModifiedMemoryId && screenCoords[lastModifiedMemoryId]) {
        const pos = screenCoords[lastModifiedMemoryId]
        const pulseR = 12 + (phase % (Math.PI / 2)) * 24
        const pulseAlpha = Math.max(0, 0.4 - (phase % (Math.PI / 2)) / (Math.PI / 2) * 0.4)
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, pulseR, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(245, 158, 11, ${pulseAlpha})`
        ctx.lineWidth = 1
        ctx.stroke()
      }

      ctx.restore()
      animFrameRef.current = requestAnimationFrame(render)
    }

    animFrameRef.current = requestAnimationFrame(render)
    return () => cancelAnimationFrame(animFrameRef.current)
  }, [snapshot, mapPoints, graph, selectedMemoryId, hoveredMemoryId, lastModifiedMemoryId, activeTimestep, getLayoutMaps, initParticles])

  // Mouse hit testing
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const rect = canvas.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      setMousePos({ x, y })

      const w = canvas.clientWidth
      const h = canvas.clientHeight
      const coords = getLayoutMaps(w, h)
      const activeStrengths: Record<string, number> =
        snapshot && 'memory_strength' in snapshot && snapshot.memory_strength
          ? (snapshot as MemorySnapshot).memory_strength
          : {}

      let found: string | null = null
      for (const [mId, pos] of Object.entries(coords)) {
        const pt = mapPoints.find((p) => p.memory_id === mId)
        const strength = activeStrengths[mId] !== undefined ? activeStrengths[mId] : (pt?.strength ?? 0)
        const baseR = 4 + Math.max(0, Math.min(1, strength)) * 14
        const hitR = baseR + 6
        if (Math.hypot(x - pos.x, y - pos.y) <= hitR) {
          found = mId

          // Build hover data
          const causalCount = graph?.edges?.filter(
            (e) => e.source === mId || e.target === mId
          ).length ?? 0
          setHoveredData({
            id: mId,
            concept: pt?.label || mId,
            strength,
            cluster: pt?.cluster ?? 0,
            causalCount,
          })
          break
        }
      }

      setHoveredMemoryId(found)
      if (!found) setHoveredData(null)
    },
    [mapPoints, graph, snapshot, getLayoutMaps]
  )

  const handleMouseLeave = useCallback(() => {
    setHoveredMemoryId(null)
    setHoveredData(null)
    setMousePos(null)
  }, [])

  const handleClick = useCallback(() => {
    if (hoveredMemoryId) onSelectMemory(hoveredMemoryId)
  }, [hoveredMemoryId, onSelectMemory])

  const strengthClass = (s: number) =>
    s > 0.6 ? 'emerald' : s > 0.3 ? 'amber' : 'crimson'

  return (
    <div
      style={{ width: '100%', height: '100%', position: 'relative' }}
      className="memory-field-container"
    >
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
          cursor: hoveredMemoryId ? 'pointer' : 'crosshair',
        }}
      />

      {/* ── Floating Precision Annotation ─────────────────────────── */}
      {hoveredData && mousePos && (
        <div
          className="canvas-tooltip"
          style={{
            left: Math.min(mousePos.x + 16, (canvasRef.current?.clientWidth ?? 800) - 200),
            top: mousePos.y - 10,
          }}
        >
          <div className="canvas-tooltip-id">{hoveredData.id}</div>
          {hoveredData.concept !== hoveredData.id && (
            <div className="canvas-tooltip-concept">{hoveredData.concept}</div>
          )}
          <div className="canvas-tooltip-metrics">
            <div className="canvas-tooltip-row">
              <span className="canvas-tooltip-key">strength</span>
              <span
                className="canvas-tooltip-val"
                style={{ color: `var(--${strengthClass(hoveredData.strength)})` }}
              >
                {hoveredData.strength.toFixed(3)}
              </span>
            </div>
            <div className="canvas-tooltip-row">
              <span className="canvas-tooltip-key">cluster</span>
              <span className="canvas-tooltip-val">{hoveredData.cluster}</span>
            </div>
            {hoveredData.causalCount > 0 && (
              <div className="canvas-tooltip-row">
                <span className="canvas-tooltip-key">connections</span>
                <span className="canvas-tooltip-val">{hoveredData.causalCount}</span>
              </div>
            )}
          </div>
          <div className="canvas-tooltip-action">Click to excavate</div>
        </div>
      )}
    </div>
  )
}
