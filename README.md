# Neural Archaeology

**Excavate the hidden life of machine memory.**

An educational AI research platform for studying **long-horizon evolving
state**: how a fixed-dimensional state carries information across long
sequences, why state updates are lossy, and how competing information
interferes, degrades, or is forgotten.

This is not a chatbot, not a static visualization, and not an LLM wrapper.
It is a real computational substrate: deterministic NumPy state-update
mechanisms, a synthetic controlled-memory task, snapshots after every
event, exact ground truth, and measurable interference — served by a
FastAPI backend with a minimal React console on top.

> **Honesty contract**: the mechanisms are independent educational toys,
> not implementations of BDH or any production memory architecture. Read
> [`docs/SCIENTIFIC_MODEL.md`](docs/SCIENTIFIC_MODEL.md) for exactly what
> is computed, what is synthetic, and what is not being claimed.

---

## Quick start

```bash
# 1. install Python dependencies (creates .venv)
uv sync --extra dev

# 2. run the backend
uv run uvicorn backend.main:app --reload --port 8000
# → http://localhost:8000/docs  (OpenAPI)
# → http://localhost:8000/health

# 3. run the frontend console (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173  (proxies /api to :8000)

# 4. run the test suite
uv run pytest
```

## Project layout

```
core/          computational substrate (pure NumPy, no framework deps)
  mechanisms/  the five pluggable state-update mechanisms (A–E)
  task.py      synthetic controlled-memory task generator + queries
  runner.py    run_experiment(config) — the single entry point
  metrics.py   exact metric definitions + computation
  experiment.py  Experiment object, JSON serialization, local persistence
backend/       FastAPI application (routes, schemas, local store)
frontend/      minimal React + Vite + TypeScript lab console
tests/         pytest suite (determinism, math, serialization, API)
docs/          ARCHITECTURE.md, SCIENTIFIC_MODEL.md, EXPERIMENTS.md
experiments/   saved experiment JSON (created at runtime)
data/          generated task datasets (created at runtime)
```

## One-line summary of the model

- State `x_t ∈ R^d` (or a fixed `d×d` matrix for the Hebbian mechanism).
- Each event binds `key ⊛ value` (exact circular convolution) and updates
  the state via one of five mechanisms with gain
  `update_strength × memory_strength × importance × strength`.
- Recall reads a value out of the current state with the query key;
  prediction = best match in the symbol library; ground truth is defined
  by the recorded history ("latest" or "original" binding).
- The claim — *state is lossy; competing information interferes* — falls
  out of the math: superposition cross-talk, exponential decay, k-WTA
  collisions, matrix rank accumulation, and similarity-gated erasure.

## API surface (all under `/api`, see docs/EXPERIMENTS.md)

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness, versions, mechanism list |
| `GET /mechanisms` | mechanism registry + metric definitions |
| `POST /experiments/run` | run one experiment (returns full record) |
| `POST /experiments/generate` | materialize a task without running it |
| `GET /experiments/{id}` | fetch a stored experiment |
| `POST /experiments/{id}/replay` | exact replay (or param-override probe) |
| `POST /recall` | probe stored state at any point in its history |
| `POST /compare` | run configs side by side and return a metrics table |

## Phase roadmap

**Phase 01**: scientific substrate — core, mechanisms, task, metrics,
runner, API, tests, minimal console, docs.

**Phase 02 (done)**: the memory engine — deterministic text encoder,
`Memory` model, write/recall with memory-vs-interference accounting,
similarity measures, educational interference model, retention curves,
capacity sweeps, order comparisons, memory-collision reports, ablation
(counterfactual replay), replay-based contribution estimates, cross-
experiment comparison, ten packaged scenarios, and the Phase 02 API
(see `docs/EXPERIMENTS.md`).

**Phase 03+**: timeline & replay UI, neural surgery, causal/forensic
investigation, hypothesis testing, automated experiment design,
mechanism evolution, architecture comparison, BDH/BDH-CQ demonstrations,
experiment sharing, research notebook, challenge system, and 2D/3D
visualization. Everything the substrate produces (snapshots, traces,
metrics, ground truth, ablations) is already structured to feed those
phases. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).