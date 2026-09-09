# Pathway: Synaptic Plasticity as Short-Term Memory

> **An Interactive Research-Based Learning Artifact for Fast Weight Dynamics**

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-cyan.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 100% Deterministic](https://img.shields.io/badge/tests-deterministic-brightgreen.svg)]()

---

## 1. Executive Summary

**Pathway** is an interactive, research-grade computational learning environment designed to unpack a foundational problem in neural computation: **how neural networks temporarily retain information without overwriting long-term knowledge.**

Rather than treating memory as a black-box vector database or static token lookup, Pathway implements a transparent linear algebraic associative memory engine ($\mathbb{R}^d \to \mathbb{R}^{d \times d} \to \mathbb{R}^d$). Learners interactively write associative patterns ($v \otimes k$), watch fast synaptic matrices evolve, test capacity limits, ablate individual synapses, simulate counterfactual universes, design custom parameter sweeps, and ground every empirical finding in peer-reviewed scientific literature (2022–2026).

---

## 2. The Central Learning Claim

Every workspace, mathematical equation, and diagnostic panel in Pathway exists to explore, measure, or qualify one central scientific claim:

> **"Recent activity can temporarily modify synaptic connections, allowing information to be represented and retrieved through an evolving internal state."**

### Core Principles:
1. **Activity-Dependent Writing:** Coordinated activation between cue $k$ and target value $v$ induces an outer-product update $\Delta W = \eta (v \otimes k^T)$.
2. **Autonomous Exponential Decay:** Transient connections relax passively toward zero resting baseline at rate $\lambda$.
3. **Associative Linear Readout:** Reconstructing memories relies on matrix-vector projection $\hat{v} = W k$.
4. **Dynamic Superposition & Interference:** Successive writes share the same matrix capacity; non-orthogonal cues induce measurable crosstalk.

---

## 3. Theoretical Foundations & Primary Literature

Pathway's computational mechanisms directly map to contemporary peer-reviewed research (2022–2026):

| Primary Paper | Venue & DOI | Core Finding Grounded in Pathway |
|---|---|---|
| **Tyulmankov, Yang, & Abbott (2022)** | *Nature Neuroscience*<br>[10.1038/s41593-022-01037-2](https://doi.org/10.1038/s41593-022-01037-2) | Meta-learned synaptic plasticity decouples fast short-term memory encoding from slow contextual stability. |
| **Krotov (2023)** | *Nature Reviews Physics*<br>[10.1038/s42254-023-00595-y](https://doi.org/10.1038/s42254-023-00595-y) | Modern Hopfield associative memory capacity is fundamentally bounded by cue correlation and recurrent crosstalk. |
| **Whittington et al. (2022)** | *Nature Neuroscience*<br>[10.1038/s41593-022-01150-2](https://doi.org/10.1038/s41593-022-01150-2) | Internal representational geometries diverge from surface stimulus correlations. |
| **Miconi (2023)** | *Neural Computation*<br>[10.1162/neco_a_01584](https://doi.org/10.1162/neco_a_01584) | Differentiable fast weights with decay act as flexible working memory buffers in neural networks. |
| **Kozachkov et al. (2023)** | *Nature Communications*<br>[10.1038/s41467-023-38024-8](https://doi.org/10.1038/s41467-023-38024-8) | Passive decay and active interference jointly govern exponential memory fading. |

---

## 4. Mathematical Formulation

All computations are closed-form, deterministic linear algebra implemented in pure NumPy:

### 4.1 State Dynamics
Given synaptic matrix $W(t) \in \mathbb{R}^{d \times d}$, decay rate $\lambda \in [0, 1]$, write gain $\eta > 0$, and unit vectors $k_t, v_t \in \mathbb{R}^d$:
$$W(t+1) = (1 - \lambda) W(t) + \eta \, (v_t \, k_t^T)$$

### 4.2 Linear Readout Probe
$$\hat{v} = W(t) k_{\text{probe}}$$

### 4.3 Key Metrics
- **Recall Fidelity ($F$):** $\cos(v, \hat{v}) = \frac{v \cdot \hat{v}}{\|v\|_2 \|\hat{v}\|_2}$
- **Crosstalk Residual ($E_{\text{ct}}$):** $\|\hat{v} - v\|_2$
- **Frobenius Energy ($\|W\|_F$):** $\sqrt{\sum_{i,j} W_{i,j}^2} = \sqrt{\operatorname{Tr}(W^T W)}$
- **Active Synapse Fraction ($N_{\text{act}}$):** $\frac{1}{d^2} \sum_{i,j} \mathbb{I}(|W_{i,j}| > 0.01)$
- **Crosstalk Index ($\chi$):** $\frac{|\hat{v} \cdot v_{\text{competing}}|}{\|\hat{v}\|_2 \|v_{\text{competing}}\|_2}$

---

## 5. Interactive Workspaces & Capabilities

Pathway provides a multi-workspace suite addressing every dimension of synaptic memory:

1. **Ecosystem Hub (Phase 21):** Unified visual dashboard linking active memories, matrix energy gauges, health diagnostics, and quick-launch portals.
2. **Synaptic Brain & X-Ray (Phases 13–15):** 2D heatmaps of connection weights $W_{i,j}$, spectral eigenvalue distributions, and unit activation profiles.
3. **Time Machine & History Playback (Phases 14–16):** Step-by-step scrubbing through memory encoding, decay, and reinforcement events.
4. **Synaptic Surgery & Causal Lab (Phases 16–17):** Micro-surgical clamping ($W_{i,j} \leftarrow 0$) of critical synapses to test causal vulnerability.
5. **Counterfactual Divergence Engine (Phases 17–18):** Branching parallel universes at step $t_k$ to compare divergent memory trajectories.
6. **Collision Lab (Phase 17):** Controlled parametric study of cue overlap, destructive interference, and catastrophic forgetting.
7. **Memory Detective (Phase 18):** Case-based forensic investigations: where did the memory go, what changed, and which synapses were responsible?
8. **Adaptive Memory Observatory (Phase 19):** Real-time monitoring of continuous streaming inputs and equilibrium states.
9. **Memory Genome (Phase 20):** SVD/PCA synaptic fingerprinting revealing how distinct internal weight patterns produce identical outputs.
10. **Experiment Studio (Phase 22):** Learner-designed experiments, parametric sweeps, A/B comparisons, and guided scientific journeys.
11. **Scientific Evidence & Research Layer (Phase 23):** Primary literature archive with DOIs, 5-part Evidence Panels, interactive Lineage Graph, and mathematical glossary.

---

## 6. Scientific Integrity & Model Limitations

### What Pathway Models:
- Transparent, reproducible linear associative plasticity ($v \otimes k$).
- Superposition crosstalk and dimensional saturation in recurrent matrices.
- Exponential memory decay and counterfactual divergence under causal intervention.

### What Pathway Does NOT Claim:
- **Not a biophysical simulation:** Does not model spiking action potentials, Hodgkin-Huxley ion kinetics, or dendritic morphology.
- **Not a full cognitive model:** Omits multi-region hippocampal-neocortical transfer, slow consolidation, and sleep replay.
- **Linear simplification:** Real biological synapses feature saturating non-linearities, short-term depression/facilitation, and neuromodulatory gating.

---

## 7. Core Learning Objectives (7 Pillars)

1. Explain how outer-product writing ($v \otimes k$) embeds bindings directly into synaptic connection matrices.
2. Predict and mathematically explain why non-orthogonal cues induce crosstalk during linear readout.
3. Quantify the trade-off between write gain ($\eta$) and memory retention under exponential decay ($\lambda$).
4. Formulate falsifiable hypotheses regarding synaptic vulnerability and verify via targeted surgical ablation.
5. Analyze how identical behavioral outputs can stem from divergent internal synaptic representations.
6. Distinguish measured linear algebraic facts from broader neurobiological hypotheses.
7. Reproduce all experimental findings deterministically using open seeds and equations.

---

## 8. Target Audience & Prerequisites

- **Audience:** Computational neuroscience students, cognitive science researchers, ML engineers, and curious self-learners.
- **Prerequisites:** Basic familiarity with vectors, matrices, dot products, and neural networks.
- **Non-Prerequisites:** No biological lab background, no GPU hardware, and no advanced calculus required.

---

## 9. Technology Stack

- **Backend:** Python 3.14+, FastAPI, Pure NumPy (zero heavy ML frameworks).
- **Frontend:** React 19, TypeScript 5.0+, Vite 6, Native SVG visualization.
- **Design System:** Custom Dark Academic glassmorphism with high-contrast scientific typography.

---

## 10. Quick Start

### 1. Prerequisites
- Python 3.10+ (Python 3.14 recommended) with `uv` package manager.
- Node.js 18+ and `npm`.

### 2. Run the Computational Backend
```bash
# Clone repository
git clone https://github.com/ayushk2206-source/Pathway-.git
cd Pathway-

# Install Python dependencies
uv sync --extra dev

# Launch backend server
uv run uvicorn backend.main:app --reload --port 8000
# Backend API ready at http://localhost:8000
# OpenAPI Docs: http://localhost:8000/docs
```

### 3. Run the Interactive Frontend Console
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
# Interactive Console ready at http://localhost:5173
```

### 4. Run Automated Test Suite
```bash
# Run complete test suite (deterministic, zero external network calls)
uv run pytest -v
```

---

## 11. API Reference (Key Endpoints)

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Core engine version and system status |
| `/api/research/papers` | `GET` | Peer-reviewed literature archive (2022–2026) with DOIs |
| `/api/research/claims` | `GET` | Traceable claims with 5-part Evidence Panels |
| `/api/research/metrics` | `GET` | Formal metric glossary with equations and limitations |
| `/api/research/graph` | `GET` | Concept $\to$ Paper $\to$ Code $\to$ Observation lineage graph |
| `/api/research/disclosures` | `GET` | AI assistance, data disclosures, and learning objectives |
| `/api/research/licenses` | `GET` | Software and asset license registry |
| `/api/research/methodology` | `POST` | Generate reproducible methodology protocol for any configuration |
| `/api/studio/run` | `POST` | Execute custom learner-designed synaptic experiment |
| `/api/studio/sweep` | `POST` | Run 1D parameter sweep across decay, learning rate, or dimension |
| `/api/ecosystem/overview` | `GET` | Unified multi-phase memory ecosystem overview |

---

## 12. Reproducibility & Provenance

Every experiment in Pathway includes an explicit provenance hash derived from:
`SHA-256(experiment_type + dimension + seed + decay + learning_rate + memory_keys)`

Running any experiment with identical configuration parameters reproduces numerical metrics to floating-point precision across all platforms.

---

## 13. Disclosures & Licensing

- **AI Assistance:** Architectural design and development assisted by Google Antigravity AI agents with human scientific verification of all equations and DOIs.
- **Synthetic Data:** 100% synthetic mathematical vectors. Zero patient or PII data.
- **License:** Open-source under the [MIT License](LICENSE). Third-party dependencies: NumPy (BSD-3), React/Vite (MIT). Academic citations referenced under Fair Use.

---

## 14. Citation

If you utilize Pathway in academic coursework, research demonstrations, or educational publications, please cite:

```bibtex
@software{pathway2026synaptic,
  author = {Pathway Research Group},
  title = {Pathway: Interactive Research-Based Learning Artifact for Synaptic Plasticity as Short-Term Memory},
  year = {2026},
  url = {https://github.com/ayushk2206-source/Pathway-},
  version = {0.23.0}
}
```