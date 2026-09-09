import React from 'react'

interface ScientificClaimPanelProps {
  observedText?: string
  interpretationText?: string
}

export const ScientificClaimPanel: React.FC<ScientificClaimPanelProps> = ({
  observedText = "Two memories share 17 measured computational structures with 23% Jaccard overlap.",
  interpretationText = "Their internal representations overlap under the selected linear algebraic measurement; this indicates resource contention rather than biological identity.",
}) => {
  return (
    <div className="claim-panel-container">
      <div className="claim-box">
        <span className="claim-tag observed">● OBSERVED (Measured State)</span>
        <div className="claim-text">{observedText}</div>
      </div>

      <div className="claim-box">
        <span className="claim-tag interpretation">◈ INTERPRETATION (Scientific Hypothesis)</span>
        <div className="claim-text">{interpretationText}</div>
      </div>
    </div>
  )
}
