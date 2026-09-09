import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  baseAlpha: number;
  phase: number;
}

interface SignalPulse {
  p1Idx: number;
  p2Idx: number;
  progress: number;
  speed: number;
}

export const ProceduralBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Generate synaptic nodes
    const nodeCount = Math.min(Math.floor((width * height) / 22000), 65);
    const particles: Particle[] = [];

    for (let i = 0; i < nodeCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.28,
        vy: (Math.random() - 0.5) * 0.28,
        radius: Math.random() * 1.6 + 0.8,
        baseAlpha: Math.random() * 0.35 + 0.15,
        phase: Math.random() * Math.PI * 2,
      });
    }

    const pulses: SignalPulse[] = [];
    let time = 0;

    const render = () => {
      time += 0.012;
      ctx.clearRect(0, 0, width, height);

      // 1. Deep cinematic void background
      ctx.fillStyle = '#05070b';
      ctx.fillRect(0, 0, width, height);

      // 2. Soft atmospheric lighting & warm terracotta contour (inspired by reference art)
      const topMatrixGrad = ctx.createLinearGradient(0, 0, 0, height * 0.55);
      topMatrixGrad.addColorStop(0, 'rgba(30, 24, 45, 0.45)');
      topMatrixGrad.addColorStop(0.4, 'rgba(15, 20, 35, 0.3)');
      topMatrixGrad.addColorStop(1, 'rgba(5, 7, 11, 0)');
      ctx.fillStyle = topMatrixGrad;
      ctx.fillRect(0, 0, width, height);

      // Soft central landscape glow contour
      const contourGrad = ctx.createRadialGradient(
        width * 0.5,
        height * 0.58,
        width * 0.05,
        width * 0.5,
        height * 0.6,
        width * 0.65
      );
      contourGrad.addColorStop(0, 'rgba(180, 83, 60, 0.09)');
      contourGrad.addColorStop(0.35, 'rgba(120, 53, 36, 0.05)');
      contourGrad.addColorStop(0.7, 'rgba(10, 16, 28, 0.3)');
      contourGrad.addColorStop(1, 'rgba(5, 7, 11, 0.95)');
      ctx.fillStyle = contourGrad;
      ctx.fillRect(0, 0, width, height);

      // 3. Subtle computational coordinate grid
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.018)';
      ctx.lineWidth = 1;
      const gridSize = 90;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // 4. Update and draw synaptic filaments (connections)
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        p1.x += p1.vx;
        p1.y += p1.vy;

        // Soft bounce boundaries
        if (p1.x < 0 || p1.x > width) p1.vx *= -1;
        if (p1.y < 0 || p1.y > height) p1.vy *= -1;

        // Connect nearby nodes with synaptic plasticity filaments
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = 160;

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.16;
            const pulse = (Math.sin(time * 2 + p1.phase + p2.phase) + 1) * 0.5;

            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha * (0.6 + 0.4 * pulse)})`;
            ctx.lineWidth = 0.75 + 0.4 * pulse;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Occasionally spawn traveling signal pulse along synapse
            if (Math.random() < 0.0006 && pulses.length < 12) {
              pulses.push({
                p1Idx: i,
                p2Idx: j,
                progress: 0,
                speed: 0.012 + Math.random() * 0.015,
              });
            }
          }
        }

        // Draw Node Soma
        const pulse = (Math.sin(time * 2.5 + p1.phase) + 1) * 0.5;
        const currentAlpha = p1.baseAlpha * (0.7 + 0.3 * pulse);

        ctx.fillStyle = `rgba(56, 189, 248, ${currentAlpha})`;
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius * (1 + 0.15 * pulse), 0, Math.PI * 2);
        ctx.fill();

        // Node aura
        ctx.fillStyle = `rgba(56, 189, 248, ${currentAlpha * 0.12})`;
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius * 3.5, 0, Math.PI * 2);
        ctx.fill();
      }

      // 5. Render traveling synaptic action potential pulses
      for (let k = pulses.length - 1; k >= 0; k--) {
        const pulse = pulses[k];
        pulse.progress += pulse.speed;
        if (pulse.progress >= 1) {
          pulses.splice(k, 1);
          continue;
        }

        const p1 = particles[pulse.p1Idx];
        const p2 = particles[pulse.p2Idx];
        if (!p1 || !p2) {
          pulses.splice(k, 1);
          continue;
        }

        const px = p1.x + (p2.x - p1.x) * pulse.progress;
        const py = p1.y + (p2.y - p1.y) * pulse.progress;

        ctx.fillStyle = '#38bdf8';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(px, py, 1.8, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
};
