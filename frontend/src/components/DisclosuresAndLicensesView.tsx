import React from 'react'
import type { DisclosuresData, SourceLicenseRecord } from '../types'
import { SciBadge } from './ScientificBadges'

interface DisclosuresAndLicensesViewProps {
  disclosures: DisclosuresData | null
  licenses: SourceLicenseRecord[]
}

export const DisclosuresAndLicensesView: React.FC<DisclosuresAndLicensesViewProps> = ({
  disclosures,
  licenses,
}) => {
  if (!disclosures) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading disclosures...</div>
  }

  return (
    <div className="disclosures-container">
      {/* AI Assistance Disclosure */}
      <div className="disclosure-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>1. AI Assistance & Human Oversight Disclosure</h2>
          <SciBadge type="simplified" label="TRANSPARENCY" />
        </div>
        <div style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.5 }}>
          <p style={{ margin: '0 0 0.5rem 0' }}>
            <strong>Tools Employed:</strong> {disclosures.ai_assistance.tools_used.join(', ')}.
          </p>
          <p style={{ margin: '0 0 0.5rem 0' }}>
            <strong>Role of AI:</strong> {disclosures.ai_assistance.role}
          </p>
          <p style={{ margin: '0 0 0.5rem 0' }}>
            <strong>Human Verification Protocol:</strong> {disclosures.ai_assistance.human_verification}
          </p>
          <p style={{ margin: 0 }}>
            <strong>Reproducibility:</strong> {disclosures.ai_assistance.reproducibility}
          </p>
        </div>
      </div>

      {/* Synthetic Data Disclosure */}
      <div className="disclosure-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>2. Data Origin & Synthetic Data Disclosure</h2>
          <SciBadge type="synthetic" />
        </div>
        <div style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.5 }}>
          <p style={{ margin: '0 0 0.5rem 0' }}>
            <strong>Data Nature:</strong> {disclosures.data_disclosure.data_nature}
          </p>
          <p style={{ margin: '0 0 0.5rem 0' }}>
            <strong>Generation Method:</strong> {disclosures.data_disclosure.generation_method}
          </p>
          <p style={{ margin: '0 0 0.5rem 0' }}>
            <strong>Privacy & Ethics:</strong> Patient or PII data present ={' '}
            <span style={{ color: '#4ade80', fontWeight: 'bold' }}>
              {disclosures.data_disclosure.patient_or_pii_data ? 'YES' : 'FALSE (ZERO real biological or personal data)'}
            </span>.
          </p>
        </div>
      </div>

      {/* Core Learning Objectives */}
      <div className="disclosure-section">
        <h2>3. Core Learning Objectives (7 Pillars)</h2>
        <ul style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.88rem', color: '#e2e8f0' }}>
          {disclosures.learning_objectives.map((obj, idx) => (
            <li key={idx} style={{ lineHeight: 1.45 }}>{obj}</li>
          ))}
        </ul>
      </div>

      {/* Target Audience & Prerequisites */}
      <div className="disclosure-section">
        <h2>4. Who Is This For? (Audience & Prerequisites)</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', fontSize: '0.86rem' }}>
          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.85rem', borderRadius: '8px' }}>
            <strong style={{ color: '#38bdf8', display: 'block', marginBottom: '0.4rem' }}>
              TARGET AUDIENCE:
            </strong>
            <ul style={{ margin: 0, paddingLeft: '1rem' }}>
              {disclosures.prerequisites.target_audience.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.85rem', borderRadius: '8px' }}>
            <strong style={{ color: '#34d399', display: 'block', marginBottom: '0.4rem' }}>
              RECOMMENDED BACKGROUND:
            </strong>
            <ul style={{ margin: 0, paddingLeft: '1rem' }}>
              {disclosures.prerequisites.required_knowledge.map((k, i) => (
                <li key={i}>{k}</li>
              ))}
            </ul>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '0.85rem', borderRadius: '8px' }}>
            <strong style={{ color: '#f87171', display: 'block', marginBottom: '0.4rem' }}>
              EXPLICIT NON-PREREQUISITES:
            </strong>
            <ul style={{ margin: 0, paddingLeft: '1rem' }}>
              {disclosures.prerequisites.non_prerequisites.map((np, i) => (
                <li key={i}>{np}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* System Limitations */}
      <div className="disclosure-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>5. Model Limitations & Scientific Boundary</h2>
          <SciBadge type="simplified" label="DIDACTIC MODEL" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {disclosures.limitations.map((lim, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(239, 68, 68, 0.08)',
                borderLeft: '3px solid #ef4444',
                padding: '0.6rem 0.85rem',
                borderRadius: '0 6px 6px 0',
                fontSize: '0.85rem',
                color: '#fca5a5',
                lineHeight: 1.45,
              }}
            >
              {lim}
            </div>
          ))}
        </div>
      </div>

      {/* Software & Asset License Registry */}
      <div className="disclosure-section">
        <h2>6. Source & License Registry</h2>
        <div style={{ overflowX: 'auto' }}>
          <table className="license-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Component / Name</th>
                <th>Source</th>
                <th>Version</th>
                <th>License</th>
                <th>Usage</th>
              </tr>
            </thead>
            <tbody>
              {licenses.map((lic, idx) => (
                <tr key={idx}>
                  <td>
                    <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#38bdf8' }}>
                      {lic.category}
                    </span>
                  </td>
                  <td><strong>{lic.name}</strong></td>
                  <td>
                    {lic.source.startsWith('http') ? (
                      <a href={lic.source} target="_blank" rel="noopener noreferrer" style={{ color: '#38bdf8' }}>
                        Link &nearr;
                      </a>
                    ) : (
                      lic.source
                    )}
                  </td>
                  <td>{lic.version}</td>
                  <td>
                    <span style={{ color: '#34d399', fontWeight: 600 }}>{lic.license}</span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{lic.usage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default DisclosuresAndLicensesView
