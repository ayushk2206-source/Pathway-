import React, { useEffect, useRef, useState } from 'react'

interface ImmersionEntryHeroProps {
  onEnter: () => void
  onLaunchJudgeMode?: () => void
}

interface NodePoint {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  activation: number
}

interface PulseWave {
  srcIdx: number
  dstIdx: number
  progress: number
  speed: number
}

export const ImmersionEntryHero: React.FC<ImmersionEntryHeroProps> = ({ onEnter, onLaunchJudgeMode }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [isExiting, setIsExiting] = useState(false)

  const handleEnterClick = () => {
    setIsExiting(true)
    setTimeout(() => {
      onEnter()
    }, 600)
  }

  const handleJudgeClick = () => {
    setIsExiting(true)
    setTimeout(() => {
      onEnter()
      if (onLaunchJudgeMode) onLaunchJudgeMode()
    }, 600)
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)

    // Generate network nodes
    const nodeCount = Math.min(50, Math.floor((width * height) / 25000))
    const nodes: NodePoint[] = []

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: 2 + Math.random() * 2.5,
        activation: Math.random() * 0.5,
      })
    }

    // Synaptic pulses propagating along edges
    const pulses: PulseWave[] = []
    const connectionDist = 180

    let mouseX = width / 2
    let mouseY = height / 2

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX
      mouseY = e.clientY
    }

    window.addEventListener('mousemove', handleMouseMove)

    // Spawn periodic pulses
    const pulseInterval = setInterval(() => {
      if (nodes.length < 2) return
      const src = Math.floor(Math.random() * nodes.length)
      // Find nearest neighbor
      let bestDst = -1
      let bestDist = Infinity
      for (let j = 0; j < nodes.length; j++) {
        if (j === src) continue
        const dx = nodes[j].x - nodes[src].x
        const dy = nodes[j].y - nodes[src].y
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d < connectionDist && d < bestDist) {
          bestDist = d
          bestDst = j
        }
      }
      if (bestDst !== -1) {
        pulses.push({
          srcIdx: src,
          dstIdx: bestDst,
          progress: 0,
          speed: 0.015 + Math.random() * 0.02,
        })
      }
    }, 200)

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Background ambient gradient
      const bgGrad = ctx.createRadialGradient(mouseX, mouseY, 40, width / 2, height / 2, width * 0.7)
      bgGrad.addColorStop(0, 'rgba(14, 165, 233, 0.07)')
      bgGrad.addColorStop(1, 'rgba(3, 7, 18, 0)')
      ctx.fillStyle = bgGrad
      ctx.fillRect(0, 0, width, height)

      // Update and draw nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]
        n.x += n.vx
        n.y += n.vy

        if (n.x < 0 || n.x > width) n.vx *= -1
        if (n.y < 0 || n.y > height) n.vy *= -1

        // Decay activation toward base
        n.activation = Math.max(0.1, n.activation - 0.005)

        // Draw connections to nearby nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j]
          const dx = n2.x - n.x
          const dy = n2.y - n.y
          const dist = Math.sqrt(dx * dx + dy * dy)

          if (dist < connectionDist) {
            const alpha = (1 - dist / connectionDist) * 0.22
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.moveTo(n.x, n.y)
            ctx.lineTo(n2.x, n2.y)
            ctx.stroke()
          }
        }
      }

      // Update and render pulses
      for (let p = pulses.length - 1; p >= 0; p--) {
        const pulse = pulses[p]
        pulse.progress += pulse.speed

        if (pulse.progress >= 1) {
          nodes[pulse.dstIdx].activation = 0.9
          pulses.splice(p, 1)
          continue
        }

        const src = nodes[pulse.srcIdx]
        const dst = nodes[pulse.dstIdx]
        const px = src.x + (dst.x - src.x) * pulse.progress
        const py = src.y + (dst.y - src.y) * pulse.progress

        ctx.fillStyle = '#38bdf8'
        ctx.shadowColor = '#38bdf8'
        ctx.shadowBlur = 8
        ctx.beginPath()
        ctx.arc(px, py, 2.5, 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0
      }

      // Draw node spheres
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]
        const glow = n.activation > 0.4

        ctx.fillStyle = glow ? '#38bdf8' : 'rgba(148, 163, 184, 0.4)'
        if (glow) {
          ctx.shadowColor = 'rgba(56, 189, 248, 0.8)'
          ctx.shadowBlur = 10
        }
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.radius * (glow ? 1.4 : 1), 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0
      }

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('mousemove', handleMouseMove)
      clearInterval(pulseInterval)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <div className={`immersion-hero-overlay ${isExiting ? 'exiting' : ''}`}>
      <canvas ref={canvasRef} className="immersion-canvas-bg" />

      <div className="immersion-content">
        <div className="immersion-badge-row">
          <span className="immersion-sys-tag">DIGITAL NEUROSCIENCE LABORATORY</span>
          <span
            style={{
              fontSize: '0.72rem',
              color: '#34d399',
              background: 'rgba(16, 185, 129, 0.15)',
              padding: '0.25rem 0.6rem',
              borderRadius: '9999px',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              fontWeight: 700,
            }}
          >
            PEER-REVIEWED FOUNDATIONS
          </span>
        </div>

        <h1 className="immersion-title">PATHWAY</h1>

        <div className="immersion-subtitle">
          SYNAPTIC PLASTICITY AS SHORT-TERM MEMORY
        </div>

        <p className="immersion-description">
          Experience the hidden life of machine memory.
          Watch incoming activity temporarily modify synaptic connections,
          trace representational divergence, ablate critical weights, and
          discover how information is remembered, interfered with, and forgotten.
        </p>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            className="immersion-enter-btn"
            onClick={handleEnterClick}
            aria-label="Enter the memory system"
          >
            <span>ENTER THE MEMORY SYSTEM</span>
            <span style={{ fontSize: '1.15rem' }}>&rarr;</span>
          </button>

          {onLaunchJudgeMode && (
            <button
              className="immersion-enter-btn"
              onClick={handleJudgeClick}
              aria-label="Launch Judge Mode 2-minute tour"
              style={{
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(217, 119, 6, 0.3) 100%)',
                borderColor: '#f59e0b',
                color: '#fbbf24',
                boxShadow: '0 0 25px rgba(245, 158, 11, 0.4)',
              }}
            >
              <span>★ LAUNCH JUDGE MODE (2-MIN TOUR)</span>
              <span style={{ fontSize: '1.15rem' }}>&rarr;</span>
            </button>
          )}
        </div>

        <div className="immersion-footnote">
          [TEACHING VISUALIZATION: SYNAPTIC ACTIVATION FIELD &bull; PURE LINEAR ALGEBRA SUBSTRATE]
        </div>
      </div>
    </div>
  )
}

export default ImmersionEntryHero
