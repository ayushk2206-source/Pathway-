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
    }, 500)
  }

  const handleJudgeClick = () => {
    setIsExiting(true)
    setTimeout(() => {
      onEnter()
      if (onLaunchJudgeMode) onLaunchJudgeMode()
    }, 500)
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
    const nodeCount = Math.min(45, Math.floor((width * height) / 28000))
    const nodes: NodePoint[] = []

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: 1.8 + Math.random() * 2.2,
        activation: Math.random() * 0.4,
      })
    }

    const pulses: PulseWave[] = []
    const connectionDist = 175

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
      if (bestDst !== -1 && pulses.length < 10) {
        pulses.push({
          srcIdx: src,
          dstIdx: bestDst,
          progress: 0,
          speed: 0.012 + Math.random() * 0.015,
        })
      }
    }, 280)

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Background atmospheric glow & organic contour
      const bgGrad = ctx.createRadialGradient(mouseX, mouseY, 40, width / 2, height / 2, width * 0.75)
      bgGrad.addColorStop(0, 'rgba(56, 189, 248, 0.06)')
      bgGrad.addColorStop(0.5, 'rgba(180, 83, 60, 0.04)')
      bgGrad.addColorStop(1, 'rgba(4, 6, 10, 0)')
      ctx.fillStyle = bgGrad
      ctx.fillRect(0, 0, width, height)

      // Update and draw connections
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]
        n.x += n.vx
        n.y += n.vy

        if (n.x < 0 || n.x > width) n.vx *= -1
        if (n.y < 0 || n.y > height) n.vy *= -1

        n.activation = Math.max(0.1, n.activation - 0.003)

        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j]
          const dx = n2.x - n.x
          const dy = n2.y - n.y
          const dist = Math.sqrt(dx * dx + dy * dy)

          if (dist < connectionDist) {
            const alpha = (1 - dist / connectionDist) * 0.18
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`
            ctx.lineWidth = 0.85
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
          if (nodes[pulse.dstIdx]) nodes[pulse.dstIdx].activation = 0.85
          pulses.splice(p, 1)
          continue
        }

        const src = nodes[pulse.srcIdx]
        const dst = nodes[pulse.dstIdx]
        if (!src || !dst) {
          pulses.splice(p, 1)
          continue
        }

        const px = src.x + (dst.x - src.x) * pulse.progress
        const py = src.y + (dst.y - src.y) * pulse.progress

        ctx.fillStyle = '#38bdf8'
        ctx.shadowColor = '#38bdf8'
        ctx.shadowBlur = 6
        ctx.beginPath()
        ctx.arc(px, py, 2, 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0
      }

      // Draw node spheres
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]
        const glow = n.activation > 0.35

        ctx.fillStyle = glow ? '#38bdf8' : 'rgba(148, 163, 184, 0.35)'
        if (glow) {
          ctx.shadowColor = 'rgba(56, 189, 248, 0.7)'
          ctx.shadowBlur = 8
        }
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.radius * (glow ? 1.3 : 1), 0, Math.PI * 2)
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

      {/* Floating Top Pill Nav Bar (Inspired by reference screenshot) */}
      <nav className="hero-floating-nav">
        <div className="nav-pill-logo">
          <span className="logo-symbol">◈</span>
          <span className="logo-text">NEURAL ARCHAEOLOGY</span>
        </div>

        <div className="nav-pill-links">
          <button className="nav-link-btn active" onClick={handleEnterClick}>Observatory</button>
          <button className="nav-link-btn" onClick={handleEnterClick}>Synaptic Brain</button>
          <button className="nav-link-btn" onClick={handleEnterClick}>Surgery</button>
          <button className="nav-link-btn" onClick={handleEnterClick}>Counterfactuals</button>
          <button className="nav-link-btn" onClick={handleEnterClick}>Evidence</button>
        </div>

        <div className="nav-pill-action">
          <button className="nav-action-btn" onClick={handleJudgeClick}>
            ★ Judge Mode
          </button>
        </div>
      </nav>

      {/* Center Cinematic Content */}
      <div className="immersion-content">
        {/* Floating Category Pill Badge */}
        <div className="hero-status-pill">
          <span className="status-dot live" />
          <span className="status-pill-text">PEER-REVIEWED SYNAPTIC PLASTICITY INSTRUMENT</span>
        </div>

        {/* Central Display Typography */}
        <h1 className="hero-main-title">
          <span className="title-line-1">NEURAL ARCHAEOLOGY</span>
          <span className="title-line-2">Intelligence Designed To Evolve</span>
        </h1>

        {/* Subtitle description */}
        <p className="hero-description">
          Experience how temporary synaptic connection updates transform static network wiring
          into living short-term memory — enabling fast learning, decay, interference, and recall without retraining.
        </p>

        {/* Action Button Strip */}
        <div className="hero-cta-strip">
          <button
            className="hero-primary-pill-btn"
            onClick={handleEnterClick}
            aria-label="Enter Research Observatory"
          >
            <span>Enter Observatory</span>
            <span className="btn-arrow">&rarr;</span>
          </button>

          {onLaunchJudgeMode && (
            <button
              className="hero-secondary-pill-btn"
              onClick={handleJudgeClick}
              aria-label="Launch Judge Mode 2-minute tour"
            >
              <span>★ Launch Judge Tour (2-Min)</span>
            </button>
          )}
        </div>
      </div>

      {/* Bottom 4-Column Scientific Metric Strip (Inspired by reference screenshot) */}
      <footer className="hero-bottom-telemetry">
        <div className="telemetry-card">
          <div className="telemetry-icon">⋈</div>
          <div className="telemetry-val">128-D</div>
          <div className="telemetry-label">Vector Substrate</div>
        </div>

        <div className="telemetry-card">
          <div className="telemetry-icon">⁒</div>
          <div className="telemetry-val">0.05 / τ</div>
          <div className="telemetry-label">Synaptic Decay Rate</div>
        </div>

        <div className="telemetry-card">
          <div className="telemetry-icon">❊</div>
          <div className="telemetry-val">Zero-Noise</div>
          <div className="telemetry-label">Causal Interventions</div>
        </div>

        <div className="telemetry-card">
          <div className="telemetry-icon">井</div>
          <div className="telemetry-val">Real-Time</div>
          <div className="telemetry-label">Hebbian Plasticity Engine</div>
        </div>
      </footer>
    </div>
  )
}

export default ImmersionEntryHero
