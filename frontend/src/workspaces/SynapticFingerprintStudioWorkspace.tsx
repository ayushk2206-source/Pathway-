import React, { useState, useEffect } from 'react'
import {
  getFingerprintDemo,
  computeFingerprint,
  getSurfaceVsInternal,
  runCloningTest,
  runCollisionMutation,
  runFingerprintSurgery,
  runCounterfactualFingerprint,
  getMemoryFamilyTree,
  exportFingerprintJson,
} from '../api'
import type {
  SynapticFingerprint,
  FingerprintComparison,
  MemoryDistanceMap,
  MemoryBranchNode,
  FingerprintChallenge,
} from '../types'
import { SynapticFingerprintHero } from '../components/SynapticFingerprintHero'
import { SurfaceVsInternalComparison } from '../components/SurfaceVsInternalComparison'
import { SharedGenomeBreakdown } from '../components/SharedGenomeBreakdown'
import { MemoryFamilyTree } from '../components/MemoryFamilyTree'
import { MemoryDistanceMap2D } from '../components/MemoryDistanceMap2D'
import { ScientificClaimPanel } from '../components/ScientificClaimPanel'
import { FingerprintChallengePanel } from '../components/FingerprintChallengePanel'
import { RawDataModal } from '../components/RawDataModal'
import '../fingerprint.css'

export const SynapticFingerprintStudioWorkspace: React.FC = () => {
  // Core state
  const [concepts, setConcepts] = useState<string[]>([])
  const [selectedConcept, setSelectedConcept] = useState<string>('Concept Alpha')
  const [fingerprint, setFingerprint] = useState<SynapticFingerprint | null>(null)
  const [distanceMap, setDistanceMap] = useState<MemoryDistanceMap | null>(null)
  const [challenges, setChallenges] = useState<FingerprintChallenge[]>([])
  const [comparisons, setComparisons] = useState<FingerprintComparison[]>([])
  const [selectedComparison, setSelectedComparison] = useState<FingerprintComparison | null>(null)
  const [familyTree, setFamilyTree] = useState<MemoryBranchNode | null>(null)

  // Status & Scanning
  const [isScanning, setIsScanning] = useState<boolean>(false)
  const [statusMessage, setStatusMessage] = useState<string>('')

  // Modals & Research Mode
  const [rawDataOpen, setRawDataOpen] = useState<boolean>(false)
  const [surgeryModalOpen, setSurgeryModalOpen] = useState<boolean>(false)
  const [targetSynapse, setTargetSynapse] = useState<[number, number]>([0, 0])
  const [newSurgeryWeight, setNewSurgeryWeight] = useState<number>(0.0)

  // Initial load
  useEffect(() => {
    loadDemo()
  }, [])

  const loadDemo = async () => {
    setIsScanning(true)
    try {
      const res = await getFingerprintDemo(16, 42)
      setConcepts(res.concepts)
      if (res.fingerprints.length > 0) {
        setFingerprint(res.fingerprints[0])
        setSelectedConcept(res.fingerprints[0].concept)
      }
      setDistanceMap(res.distance_map)
      setChallenges(res.challenges)

      // Load pairwise surface vs internal comparisons
      const simRes = await getSurfaceVsInternal({ concepts: res.concepts.slice(0, 4), dimension: 16, seed: 42 })
      setComparisons(simRes.comparisons)
      if (simRes.comparisons.length > 0) {
        setSelectedComparison(simRes.comparisons[0])
      }

      // Load family tree
      const treeRes = await getMemoryFamilyTree(res.concepts[0] || 'Concept Alpha', 16, 42)
      setFamilyTree(treeRes.family_tree)
    } catch (err) {
      console.error('Failed to load fingerprint demo:', err)
      setStatusMessage('Error loading demo data.')
    } finally {
      setIsScanning(false)
    }
  }

  // Handle concept selection
  const handleSelectConcept = async (concept: string) => {
    setSelectedConcept(concept)
    setIsScanning(true)
    try {
      const res = await computeFingerprint({ concept, dimension: 16, seed: 42 })
      setFingerprint(res.fingerprint)

      // Update tree
      const treeRes = await getMemoryFamilyTree(concept, 16, 42)
      setFamilyTree(treeRes.family_tree)
    } catch (err) {
      console.error('Failed to compute fingerprint:', err)
    } finally {
      setIsScanning(false)
    }
  }

  // Handle Cloning Test
  const handleRunCloningTest = async () => {
    setStatusMessage('Executing Before/After memory cloning stability test...')
    try {
      const res = await runCloningTest({
        target_concept: selectedConcept,
        target_value: fingerprint?.value || 'Target Value',
        intervening_concept: 'Intervening Noise',
        intervening_value: 'Noise Target',
        dimension: 16,
        seed: 42,
      })
      setStatusMessage(`Cloning Test: ${res.stability_conclusion}`)
      setFingerprint(res.fingerprint_after)
    } catch (err) {
      console.error('Cloning test error:', err)
      setStatusMessage('Cloning test failed.')
    }
  }

  // Handle Collision Mutation
  const handleRunCollisionMutation = async () => {
    setStatusMessage('Executing Collision Mutation (A ➔ B ➔ A Recall)...')
    try {
      const res = await runCollisionMutation({
        concept_a: selectedConcept,
        value_a: fingerprint?.value || 'Target A',
        concept_b: 'Competing Memory B',
        value_b: 'Target B',
        dimension: 16,
        seed: 42,
      })
      setStatusMessage(`Collision Mutation: ${res.interpretation}`)
      setFingerprint(res.fingerprint_a_after_collision)
    } catch (err) {
      console.error('Collision mutation error:', err)
      setStatusMessage('Collision mutation failed.')
    }
  }

  // Handle Counterfactual
  const handleRunCounterfactual = async () => {
    setStatusMessage('Running counterfactual under reduced plasticity (η=0.05)...')
    try {
      const res = await runCounterfactualFingerprint({
        concept: selectedConcept,
        value: fingerprint?.value || 'Target Value',
        cf_update_strength: 0.05,
        dimension: 16,
        seed: 42,
      })
      setStatusMessage(`Counterfactual: ${res.divergence_summary}`)
      setFingerprint(res.counterfactual_fingerprint)
    } catch (err) {
      console.error('Counterfactual error:', err)
      setStatusMessage('Counterfactual failed.')
    }
  }

  // Handle Synaptic Surgery
  const handlePerformSurgery = async () => {
    if (!fingerprint) return
    setStatusMessage(`Applying surgery to synapse (${targetSynapse[0]}, ${targetSynapse[1]})...`)
    try {
      const res = await runFingerprintSurgery({
        concept: fingerprint.concept,
        value: fingerprint.value,
        target_synapse: targetSynapse,
        new_weight: newSurgeryWeight,
        dimension: 16,
        seed: 42,
      })
      setSurgeryModalOpen(false)
      setFingerprint(res.fingerprint_after)
      setStatusMessage(
        `Surgery applied to (${targetSynapse[0]}, ${targetSynapse[1]}): ` +
        `Recall fidelity changed from ${(res.recall_fidelity_before * 100).toFixed(1)}% to ${(res.recall_fidelity_after * 100).toFixed(1)}%.`
      )
    } catch (err) {
      console.error('Surgery error:', err)
      setStatusMessage('Surgery failed.')
    }
  }

  // Export JSON
  const handleExportJson = async () => {
    if (!fingerprint) return
    try {
      const data = await exportFingerprintJson({
        concept: fingerprint.concept,
        value: fingerprint.value,
        dimension: 16,
        seed: 42,
      })
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `synaptic_fingerprint_${fingerprint.concept.replace(/\s+/g, '_')}.json`
      a.click()
      URL.revokeObjectURL(url)
      setStatusMessage('Fingerprint JSON exported.')
    } catch (err) {
      console.error('Export error:', err)
    }
  }

  return (
    <div className="fingerprint-studio-container">
      {/* Header */}
      <div className="scanner-header">
        <div className="scanner-title-group">
          <h1>
            <span>Memory Genome & Synaptic Fingerprint</span>
          </h1>
          <p className="scanner-subtitle">
            Phase 20: Empirical computational fingerprints, surface vs internal similarity, and synaptic genome evolution
          </p>
        </div>

        <div className="scanner-actions">
          <button className="scanner-btn primary" onClick={handleRunCloningTest}>
            🧬 Cloning Test
          </button>
          <button className="scanner-btn accent" onClick={handleRunCollisionMutation}>
            💥 Collision Mutation
          </button>
          <button className="scanner-btn warning" onClick={handleRunCounterfactual}>
            🔀 Counterfactual
          </button>
          <button className="scanner-btn" onClick={() => setRawDataOpen(true)}>
            📊 Research Mode
          </button>
          <button className="scanner-btn" onClick={handleExportJson}>
            💾 Export JSON
          </button>
        </div>
      </div>

      {statusMessage && (
        <div style={{
          padding: '0.6rem 1rem',
          background: 'rgba(56, 189, 248, 0.15)',
          border: '1px solid #38bdf8',
          borderRadius: '8px',
          fontSize: '0.82rem',
          color: '#e0f2fe',
        }}>
          {statusMessage}
        </div>
      )}

      {/* Concept Selector Ribbon */}
      <div className="scanner-selector-ribbon">
        <div className="concept-chip-group">
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
            Inspect Memory:
          </span>
          {concepts.map((c) => (
            <button
              key={c}
              className={`concept-chip ${selectedConcept === c ? 'active' : ''}`}
              onClick={() => handleSelectConcept(c)}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="dna-scan-indicator">
          <span className="scan-pulse" />
          <span>Dimension d=16 · Hebbian Substrate</span>
        </div>
      </div>

      {/* Main Grid: Hero Fingerprint & Surface vs Internal */}
      <div className="scanner-grid">
        <SynapticFingerprintHero
          fingerprint={fingerprint}
          isScanning={isScanning}
          onSelectSynapse={(row, col) => {
            setTargetSynapse([row, col])
            setNewSurgeryWeight(0.0)
            setSurgeryModalOpen(true)
          }}
        />

        <SurfaceVsInternalComparison
          comparisons={comparisons}
          selectedComparison={selectedComparison}
          onSelectComparison={setSelectedComparison}
        />
      </div>

      {/* Shared Genome (Phase 17 Partition) */}
      <SharedGenomeBreakdown
        comparison={selectedComparison}
        onTriggerSurgery={(r, c) => {
          setTargetSynapse([r, c])
          setNewSurgeryWeight(0.0)
          setSurgeryModalOpen(true)
        }}
      />

      {/* 2D Distance Map & Branch Family Tree */}
      <div className="scanner-grid">
        <MemoryDistanceMap2D
          distanceMap={distanceMap}
          selectedConcept={selectedConcept}
          onSelectConcept={handleSelectConcept}
        />

        <MemoryFamilyTree
          tree={familyTree}
          selectedNodeId="branch_orig"
          onSelectNode={(node) => {
            if (node.fingerprint) {
              setFingerprint(node.fingerprint)
              setSelectedConcept(node.fingerprint.concept)
              setStatusMessage(`Loaded branch [${node.branch_type}]: ${node.label}`)
            }
          }}
        />
      </div>

      {/* Scientific Claim & Learning Challenge */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1.5rem' }}>
        <ScientificClaimPanel
          observedText={selectedComparison ? selectedComparison.explanation : undefined}
        />

        <FingerprintChallengePanel challenges={challenges} />
      </div>

      {/* Synaptic Surgery Modal */}
      {surgeryModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content-card" style={{ maxWidth: '540px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#38bdf8' }}>Synaptic Surgery (Phase 15 Intervention)</h3>
              <button className="scanner-btn" onClick={() => setSurgeryModalOpen(false)}>✕</button>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
              Directly modify synapse <strong>({targetSynapse[0]}, {targetSynapse[1]})</strong> contributing to the fingerprint of <strong>{fingerprint?.concept}</strong> and remeasure recall.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span>New Weight:</span>
              <input
                type="range"
                min="-1.5"
                max="1.5"
                step="0.05"
                value={newSurgeryWeight}
                onChange={(e) => setNewSurgeryWeight(parseFloat(e.target.value))}
                style={{ flex: 1, accentColor: '#38bdf8' }}
              />
              <span style={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#38bdf8' }}>
                {newSurgeryWeight.toFixed(2)}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="scanner-btn" onClick={() => setSurgeryModalOpen(false)}>Cancel</button>
              <button className="scanner-btn primary" onClick={handlePerformSurgery}>Execute Surgery</button>
            </div>
          </div>
        </div>
      )}

      {/* Research Mode Raw Data Modal */}
      <RawDataModal
        isOpen={rawDataOpen}
        title={`Raw Synaptic Fingerprint: ${fingerprint?.concept || ''}`}
        data={fingerprint ? (fingerprint as unknown as Record<string, unknown>) : null}
        onClose={() => setRawDataOpen(false)}
        onExportJson={handleExportJson}
      />
    </div>
  )
}
