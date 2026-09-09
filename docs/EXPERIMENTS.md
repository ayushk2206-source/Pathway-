# Experiments & API

## Running the stack

```bash
# backend — http://localhost:8000  (OpenAPI docs at /docs)
uv run uvicorn backend.main:app --reload --port 8000

# frontend — http://localhost:5173 (proxies /api → :8000)
cd frontend && npm install && npm run dev

# tests
uv run pytest            # 76 tests
cd frontend && npm run build   # typecheck + production build
```

## API reference

Base path `/api`. No authentication (Phase 02+). Errors: `400` invalid
config, `404` unknown id/object, `422` malformed payload.

### `GET /health`
Liveness + versions + mechanism keys.
```json
{"status": "ok", "core_version": "0.1.0", "schema_version": 1,
 "mechanisms": ["baseline", "leaky", "competitive", "hebbian", "interference"]}
```

### `GET /mechanisms`
Registry metadata (descriptions, whether the state is a matrix) plus
`metric_definitions`.

### `POST /experiments/run`
Run one experiment. Body is the full config (all fields optional; shown
here with defaults):

```json
{
  "seed": 7,
  "mechanism": "leaky",
  "params": {
    "state_dim": 128, "update_strength": 1.0, "memory_strength": 1.0,
    "decay": 0.0, "interference_strength": 0.5, "sparsity": 0.1,
    "normalize_state": false, "input_noise": 0.0
  },
  "task": {
    "d": 128, "n_objects": 6, "n_symbols": 4, "n_conflicts": 2,
    "object_similarity": 0.0, "symbol_similarity": 0.0, "cycles": 1,
    "order": "interleaved", "probe_original": true, "input_noise": 0.0
  },
  "update_steps_per_event": 1
}
```

Returns the complete `Experiment` (below) and persists it to
`experiments/{id}.json`.

### `POST /experiments/generate`
Materialize a task without running it: body `{"seed": 9, "task": {...}}` →
`{seed, d, objects, symbols, events, queries, initial_assignment, last_write, conflicts}`.

### `GET /experiments/{id}`
Fetch a stored experiment.

### `POST /experiments/{id}/replay`
Re-run the stored config. Empty body `{}` reproduces the original run
**exactly** (determinism proof; response has `replay_of`). Optional
`{"params": {"decay": 0.9}}` re-runs with *only* those mechanism fields
overridden — a sensitivity probe. Editing the event history
(counterfactuals) is Phase 02.

### `POST /recall`
Probe a stored experiment's state at any point in its history:

```json
{"experiment_id": "…", "object_label": "obj_A", "timestep": -1,
 "expected_symbol_label": null}
```

`timestep` = events processed (-1 = end). Restores the recorded state into
the mechanism, reads out the value for the object's key, matches the
symbol library, and returns prediction/truth/confidence/correctness/
quality/top matches plus a snapshot summary. Ground truth defaults to the
history's latest binding at that timestep unless overridden.

### `POST /compare`
Run up to 12 configs side by side:

```json
{"configs": [{"seed": 7, "mechanism": "baseline", "params": {"state_dim": 64}, "task": {"d": 64}},
             {"seed": 7, "mechanism": "leaky",   "params": {"state_dim": 64, "decay": 0.4}, "task": {"d": 64}}]}
```

Returns `results` (each with experiment_id, mechanism, metrics, config)
and `comparison_table` (metric → list of values, one per run).

## Experiment JSON shape (abridged)

```json
{
  "experiment_id": "a1b2c3d4e5f60718",
  "seed": 7,
  "mechanism": "leaky",
  "parameters": {"state_dim": 128, "decay": 0.3, "update_strength": 1.0, "memory_strength": 1.0,
                 "interference_strength": 0.5, "sparsity": 0.1, "normalize_state": false, "input_noise": 0.0},
  "config": { "seed": 7, "mechanism": "leaky", "params": {…}, "task": {…}, "update_steps_per_event": 1 },
  "task": { "d": 128, "objects": {"obj_A": [ …128 floats… ], …},
            "symbols": {"sym_RED": […], …}, "events": […], "queries": […],
            "initial_assignment": {"obj_A": "sym_RED", …},
            "last_write": {"obj_A": [9, "sym_GREEN"], …},
            "conflicts": {"obj_A": [{"old_symbol": "sym_RED", "new_symbol": "sym_GREEN", "timestep": 6}]} },
  "events": [ {"id": "e0000", "timestep": 0, "concept_label": "obj_A", "attribute_label": "sym_RED",
               "key_vector": […], "value_vector": […], "importance": 1.0, "strength": 1.0,
               "noise": 0.0, "seed": null, "metadata": {}, "timestamp": "…"} ],
  "snapshots": [
    {"timestep": 0, "event_id": null, "state_vector": [0,0,…], "shape": [128], "norm": 0.0,
     "active_dimensions": [], "num_active": 0, "sparsity": 0.0, "mechanism": "leaky",
     "trace": {"mechanism": "leaky", "note": "initial state (zero) before any event"}},
    {"timestep": 1, "event_id": "e0000", "state_vector": […], "norm": 1.0, …,
     "trace": {"mechanism": "leaky", "write_gain": 1.0, "decay_applied": 0.3, …,
               "note": "scaled state by (1-λ)=0.7000, then added binding"},
     "query_results": [{"query_id": "q000", "object_label": "obj_A", "kind": "latest", …}]}
  ],
  "queries": [ {"query_id": "q000", "timestep": 0, "object_label": "obj_A", "kind": "latest",
                "predicted_vector": […], "predicted_label": "sym_RED", "truth_label": "sym_RED",
                "confidence": 0.99, "correctness": true, "quality": 0.99, "top_matches": […] } ],
  "predictions": [ …query summaries… ],
  "ground_truth": [ {"query_id": "q000", "timestep": 0, "object_label": "obj_A",
                     "kind": "latest", "truth_label": "sym_RED"} ],
  "metrics": { "recall_accuracy": 0.9, "recall_quality": 0.81, "error_rate": 0.1,
               "mean_squared_error": 0.31, "state_similarity": 0.62, "state_drift": 0.38,
               "update_magnitude": 1.04, "memory_retention": 0.83,
               "interference_score": 0.18, "recovery_score": 0.67,
               "details": {"num_queries": 10, "num_snapshots": 10, "conflict_keys": ["obj_A", "obj_B"],
                           "per_object_final_quality": {"obj_A": 0.71, …},
                           "per_conflict": {"obj_A": {"old_symbol": "sym_RED", "new_symbol": "sym_GREEN",
                                           "final_quality": 0.71, "after_write_quality": 0.99,
                                           "old_leakage": 0.24, "recovery": 0.72}}} },
  "created_at": "…", "version": 1, "replay_of": null
}
```

## Recipe: demonstrate the core claim in five runs

1. **Baseline, no conflicts** (`n_conflicts: 0`, `object_similarity: 0`):
   near-perfect recall — superposition handles dissimilar memories.
2. **Baseline, add conflicts** (`n_conflicts: 2`): latest and original
   probes tie; `interference_score` rises — superposition has no recency.
3. **Leaky, same conflicts, `decay: 0.5`**: latest wins
   (`recall_accuracy` up), original fades (`interference_score` down) —
   forgetting resolves interference at the cost of retention.
4. **Competitive, `sparsity: 0.05`**: capacity-limited sparse code;
   retention drops as events pile up (collisions).
5. **Interference, `interference_strength: 1.0` with similar objects**
   (`object_similarity: 0.8`): similar memories overwrite each other;
   `recovery_score` shows the new binding surviving.

Every number in that story is a real metric of real arithmetic — that is
the entire point of the platform.
---

# Part II — Phase 02 memory engine API

## Memory engine endpoints (all under `/api`)

| Endpoint | Purpose |
|---|---|
| `POST /memory/write` | encode one text memory, write into a fresh mechanism, return `UpdateResult` accounting |
| `POST /memory/recall` | write a list of memories, then query a concept; returns `RecallResult` + all writes |
| `POST /experiments/memory` | full memory experiment (text-encoded), persisted & replayable |
| `POST /experiments/collision` | two memories sharing a controlled-similarity concept → full collision report |
| `POST /experiments/retention` | retention curve: write A → N unrelated events → query A, for N in `lags` |
| `POST /experiments/ablation` | `{experiment_id, event_id}` → remove event, replay, compare |
| `POST /experiments/compare` | `{experiment_id_a, experiment_id_b}` → cross-experiment diff (any mechanisms) |
| `GET /experiments/{id}/state/{timestep}` | numeric state inspection (vector, norm, delta, top dims, contributions) |
| `GET /experiments/{id}/timeline` | compact visualization-ready timeline |
| `POST /experiments/{id}/memory-contribution` | replay-based contribution estimate (limitations stated in response) |
| `POST /experiments/capacity` | identical task at several `state_dim`s |
| `POST /experiments/order` | identical memories in several orders, pairwise state diffs |
| `POST /experiments/interference-matrix` | similarity × interfering-write-strength grid, every cell a real run |
| `GET /scenarios` | the ten scenario generators with objectives |
| `POST /experiments/scenario` | `{name, overrides}` → run a scenario (persists the experiment) |

## Example: memory recall

```
POST /api/memory/recall
{"seed": 5, "mechanism": "baseline", "params": {"state_dim": 64},
 "memories": [{"concept": "capital_of_france", "value": "Paris"},
              {"concept": "capital_of_spain", "value": "Madrid"}],
 "query": {"concept": "capital_of_france"},
 "expected_value": "Paris"}
```
→ `recall.predicted_value == "Paris"`, `correct == true`, confidence ≈ 1.0,
plus candidates, relevant dimensions, and the full write accounting.

## Example: collision report (abridged)

```
POST /api/experiments/collision
{"mechanism": "interference", "params": {"state_dim": 128, "interference_strength": 0.8},
 "concept": "enclosure_7", "value_a": "TIGER", "value_b": "LION", "similarity": 0.8}
```
→ `representation_similarity.key_similarity ≈ 0.79`,
`recall.predicted_value`, `retention.original_memory`,
`retention.new_memory`, `interference_score.measured` **and** `.modeled`
(educational model vs measurement), plus `state_before/after_a/after_b`.

## The seven Phase-02 demos

1. **Write A=RED, 10 unrelated events, query A** →
   `POST /api/experiments/retention` with `lags: [0, 10]`; compare
   retention at lag 0 (≈1.0) vs lag 10 (<1.0).
2. **A=RED then A=BLUE, query A** → `POST /api/experiments/scenario`
   `{"name": "conflicting_memory"}`; leaky predicts the newer value,
   baseline ties (equal candidate scores).
3. **Same seed twice** → any endpoint; `POST /api/experiments/{id}/replay`
   reproduces the record byte-for-byte; ablation reports
   `reproduced_from_config: true`.
4. **update_strength 0.1 vs 0.9** → `POST /api/memory/write` twice; the
   returned `update_result.update_magnitude` differs by construction.
5. **A→B→C→D vs D→C→B→A** → `POST /api/experiments/order`; the
   `pairwise_differences` show non-zero L2 distances between final states.
6. **Full history vs ablated** → `POST /api/experiments/ablation`; the
   counterfactual run has one fewer event, a different final state
   (`difference.state.l2_distance > 0`), and recomputed ground truth.
7. **Interference matrix** → `POST /api/experiments/interference-matrix`;
   every cell is a real run (no fabricated heatmap values).

All values above come from the deterministic engine — run any of them
twice and the numbers are identical.
