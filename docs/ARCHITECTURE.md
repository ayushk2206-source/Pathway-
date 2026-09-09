# Architecture

Neural Archaeology is a scientific instrument, not a dashboard. The design
rule for every phase: **every future UI element must connect to actual
state or computation produced by the substrate.** Phase 01 builds that
substrate and nothing that fakes it.

## Layering

```
┌─────────────────────────────────────────────────────────────┐
│ frontend/  React + Vite + TypeScript (thin client, no logic)│
│   → minimal lab console: config → run → evidence            │
├─────────────────────────────────────────────────────────────┤
│ backend/   FastAPI + Pydantic (translation + persistence)   │
│   → /api/* routes, request validation, local JSON store     │
├─────────────────────────────────────────────────────────────┤
│ core/      pure NumPy substrate (no framework dependencies)  │
│   → vectors (binding math), mechanisms, task, recall,       │
│     metrics, runner, experiment object                      │
└─────────────────────────────────────────────────────────────┘
```

Dependencies point **down**: `core` never imports `backend` or
`frontend`; `backend` imports `core`; `frontend` talks to `backend` over
HTTP. The core can be tested, embedded, or re-served by another API
without any web layer.

## Module map (`core/`)

| Module | Responsibility |
|---|---|
| `vectors.py` | exact circular-convolution binding; flat-spectrum key construction; similarity-controlled vector families; top-k masking |
| `events.py` | `Event` model — one atomic write with all controls and full history preservation |
| `mechanisms/base.py` | `Mechanism` ABC, `MechanismParams`, five mechanisms (A–E) |
| `mechanisms/__init__.py` | `MECHANISM_REGISTRY` — the plug-in point for future mechanisms |
| `task.py` | `TaskConfig` / `Task` / `Query` — synthetic controlled-memory task generator with conflicts |
| `recall.py` | `execute_query` — readout, symbol-library matching, confidence, correctness |
| `metrics.py` | `METRIC_DEFINITIONS` + `compute_metrics` — pure functions of the experiment record |
| `experiment.py` | `Experiment` + `ExperimentConfig` — complete record, JSON serialization, local save/load |
| `runner.py` | `run_experiment(config)` — the single entry point (section 12 pipeline) |

## Data flow of one experiment

```
ExperimentConfig
   │  seed, mechanism, params, task config
   ▼
generate_task(config, seed)          ──► Task (vectors, events, queries, history)
   ▼
create_mechanism(name, params, seed) ──► Mechanism instance (zeroed state)
   ▼
for each event (sequentially):
   snapshot(state)                    ──► snapshot[t] (vector, trace, query results)
   mech.update(event)                 ──► trace dict (explain_update)
   extra idle steps (update_steps_per_event − 1)
   run queries scheduled at this t    ──► QueryResult (prediction, truth, confidence)
   ▼
compute_metrics(snapshots, results, task)  ──► metrics dict
   ▼
Experiment (serializable, saved to experiments/{id}.json)
```

## Determinism contract

- One `numpy.random.Generator(seed)` per consumer (task generation,
  mechanism noise). All randomness in the whole system derives from the
  experiment seed.
- Per-event input noise uses `default_rng(sha256(f"{seed}::{timestep}"))`
  so any single state transition is reproducible in isolation.
- `np.fft.irfft` (used only to *construct* flat-spectrum keys) is
  deterministic given its input.
- The only non-computational experiment fields are `experiment_id` and
  `created_at` (and event wall-clock `timestamp`). `strip_non_deterministic`
  removes exactly those; determinism tests assert equality on the rest.

Two runs of the same config are byte-identical; `/replay` proves it
end-to-end through the API.

## Mechanism interface (extensibility)

```python
class Mechanism(ABC):
    name: str
    state_is_matrix: bool = False

    def initialize(self) -> None            # zeroed state
    def update(self, event) -> dict         # write rule; returns explanation trace
    def step_no_input(self, n) -> dict      # idle dynamics (decay, …)
    def recall(self, key_vector) -> ndarray # value readout
    def get_state_snapshot(self) -> dict    # serializable state introspection
    def restore_state(self, vector) -> None # for /recall on stored history
```

To add a mechanism in a later phase: subclass `Mechanism`, implement
`_absorb` (and `recall` if it differs from the vector readout), register
in `MECHANISM_REGISTRY`. The runner, API, and UI discover mechanisms only
through the registry — no other changes needed.

## API layer (`backend/`)

- `schemas.py` — Pydantic models mirroring core dataclasses (validation
  lives here; core stays framework-free).
- `routes.py` — endpoints; 400 on bad configs, 404 on unknown
  experiments/objects; no auth (Phase 02+).
- `store.py` — in-memory + JSON-file experiment store (local only).
- `main.py` — app factory (`create_app(store=...)` is injectable for
  tests), CORS for the Vite dev server.

## Frontend (`frontend/`)

Minimal on purpose. `App.tsx` holds a configuration form, calls
`/api/experiments/run`, and renders: the computed metrics grid, the
query table (prediction vs ground truth vs confidence), the state
timeline (snapshot norm, active dimensions, mechanism trace), the
conflict list, and the full experiment JSON. All displayed numbers come
from backend computation. Vite proxies `/api` → `127.0.0.1:8000`.

## Storage

Experiments persist as JSON in `experiments/{id}.json` (numpy values are
converted to native floats; Python's JSON float round-trip is exact, so
loads reproduce values bit-for-bit). `data/` is reserved for generated
task datasets in later phases. Both directories are gitignored except
for `.gitkeep`.

## Phase-02 extension seams (already in place)

| Future capability | Seam provided in Phase 01 |
|---|---|
| Timeline & replay UI | snapshots with per-event traces + `event_id` alignment; `/replay` |
| Counterfactual history editing | `TaskConfig.events`/`queries` explicit specs; `Task.from_dict` |
| Neural surgery | `restore_state` + `Mechanism.rule` pure functions |
| Causal / forensic investigation | `explain_update` traces, `details` in metrics, full event history |
| Hypothesis testing | deterministic `run_experiment`; `/compare` side-by-side table |
| Automated experiment design | pure, seedable config → Experiment pipeline |
| Memory-collision arena / mechanism evolution | `MECHANISM_REGISTRY` plug-in point |
| Architecture comparison | identical `Experiment` shape across mechanisms |
| BDH / BDH-CQ demonstrations | same harness; new mechanisms are new registry entries |
| Experiment sharing | stable JSON schema + `experiment_id` (persistence to come) |
| Research notebook / challenges / 2D-3D viz | all read from snapshots, traces, metrics, ground truth |

## Configuration validation

`MechanismParams.validated()` and `TaskConfig.validated()` clamp every
knob into its meaningful domain and raise `ValueError` on nonsense
(negative decay, unknown order, conflicts with a single symbol, …). The
API converts those into 400 responses; Pydantic handles structural 422s.
---

# Phase 02 additions

## New modules

| Module | Responsibility |
|---|---|
| `core/encoder.py` | deterministic synthetic text encoder: `(text, seed, d) → vectors`; independent + batch-correlated modes |
| `core/memory.py` | `Memory` / `TextMemory`, similarity measures, educational interference model, `write_memory` / `recall_memory` with full accounting |
| `core/analysis.py` | state inspection, `compare_states`, timeline, ablation, replay-based contribution, experiment comparison |
| `core/scenarios.py` | ten packaged scenarios + batch generators (retention curve, capacity sweep, order comparison, strength sweep, interference matrix, collision report) |
| `backend/memory_routes.py` | Phase 02 endpoints (mounted under `/api` alongside Phase 01 routes) |

## Design notes

- `TaskConfig.vector_source` (`"random"` | `"text"`) lets any experiment —
  including replay and ablation — choose between RNG-generated vectors and
  the deterministic text encoder. The choice is stored in the config, so
  memory experiments replay exactly.
- The memory engine calls the *same* `Mechanism.update` as Phase 01; it
  only adds accounting (`UpdateResult` splits memory vs interference
  contribution) and text-level ergonomics.
- `Mechanism.binding_vector(event)` was added to the base class so the
  memory-vs-interference split is exact, even under input noise.
- Ablation and contribution replay the history through `run_experiment`
  with explicit event/query specs rebuilt from the stored task record —
  no special code paths, so the numbers are the engine's numbers.
