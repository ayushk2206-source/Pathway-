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
    const nodeCount = Math.min(Math.floor((width * height) / 18000), 75);
    const particles: Particle[] = [];

    for (let i = 0; i < nodeCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        radius: Math.random() * 1.8 + 0.8,
        baseAlpha: Math.random() * 0.4 + 0.2,
        phase: Math.random() * Math.PI * 2,
      });
    }

    let time = 0;

    const render = () => {
      time += 0.015;
      ctx.clearRect(0, 0, width, height);

      // Deep atmospheric background gradients
      const radialGradient = ctx.createRadialGradient(
        width * 0.5,
        height * 0.35,
        50,
        width * 0.5,
        height * 0.4,
        Math.max(width, height) * 0.8
      );
      radialGradient.addColorStop(0, 'rgba(10, 20, 35, 0.4)');
      radialGradient.addColorStop(0.5, 'rgba(6, 9, 14, 0.7)');
      radialGradient.addColorStop(1, 'rgba(3, 4, 7, 0.95)');

      ctx.fillStyle = radialGradient;
      ctx.fillRect(0, 0, width, height);

      // Subtle computational coordinate grid
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.015)';
      ctx.lineWidth = 1;
      const gridSize = 80;
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

      // Update and draw synaptic filaments (connections)
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        p1.x += p1.vx;
        p1.y += p1.vy;

        // Bounce boundaries
        if (p1.x < 0 || p1.x > width) p1.vx *= -1;
        if (p1.y < 0 || p1.y > height) p1.vy *= -1;

        // Connect nearby nodes with synaptic plasticity filaments
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = 170;

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.18;
            const pulse = (Math.sin(time * 2 + p1.phase + p2.phase) + 1) * 0.5;

            ctx.strokeStyle = `rgba(0, 240, 255, ${alpha * (0.6 + 0.4 * pulse)})`;
            ctx.lineWidth = 0.8 + 0.6 * pulse;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }

        // Draw Node Soma
        const pulse = (Math.sin(time * 3 + p1.phase) + 1) * 0.5;
        const currentAlpha = p1.baseAlpha * (0.7 + 0.3 * pulse);

        ctx.fillStyle = `rgba(0, 240, 255, ${currentAlpha})`;
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius * (1 + 0.2 * pulse), 0, Math.PI * 2);
        ctx.fill();

        // Node aura
        ctx.fillStyle = `rgba(0, 240, 255, ${currentAlpha * 0.15})`;
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius * 4, 0, Math.PI * 2);
        ctx.fill();
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
