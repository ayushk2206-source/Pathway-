import React, { useEffect, useState } from 'react'

interface CustomPointerProps {
  mode?: 'default' | 'inspect' | 'surgery' | 'probe'
}

export const CustomPointer: React.FC<CustomPointerProps> = ({ mode = 'default' }) => {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Check if touch device or reduced motion is preferred
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (isTouch || prefersReducedMotion) {
      return
    }

    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY })
      if (!isVisible) setIsVisible(true)
    }

    const handleMouseLeave = () => {
      setIsVisible(false)
    }

    window.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [isVisible])

  if (!position || !isVisible) return null

  return (
    <>
      <div
        className="custom-pointer-dot"
        style={{ left: `${position.x}px`, top: `${position.y}px` }}
      />
      <div
        className={`custom-pointer-ring ${mode}`}
        style={{ left: `${position.x}px`, top: `${position.y}px` }}
      />
    </>
  )
}

export default CustomPointer
