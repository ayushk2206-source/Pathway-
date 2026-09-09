# Scientific model

This document states — precisely and honestly — what Neural Archaeology
computes, what is synthetic, what is illustrative, and what is **not**
being claimed. The falsifiable claim the platform teaches:

> *A fixed-dimensional evolving state can carry information across long
> sequences without storing every previous token explicitly, but state
> updates are lossy: competing information can interfere, causing
> degradation or forgetting. The behavior depends on update strength,
> state capacity, input order, and computation.*

## 1. The substrate

### State
`x_t ∈ R^d` for four mechanisms; a fixed `d×d` matrix for the Hebbian
mechanism (flat dimension `d²`). The dimension never changes during a
run — information must be *compressed into* the state, not appended to it.

### Events
Each event is a key–value pair: *"the symbol associated with object A is
RED"* becomes `(k_A, v_RED)`. The complete event history is preserved in
the experiment record; every state transition is reproducible.

### Binding (the storage primitive)
`bind(k, v)` is exact circular convolution,

```
bind(k, v)[i] = Σ_j k[j] · v[(i − j) mod d]
```

Object keys are **flat-spectrum vectors** (random Fourier phases, unit
magnitude on every frequency), which makes binding exactly invertible:
`bind(k, rev(k)) = δ` up to float round-off. Reading a value out of a
state is

```
unbind(x, k) = bind(x, rev(k))
```

For a single stored binding this returns `v` to machine precision. This
choice is deliberate: with clean keys, **all degradation visible in the
experiments is attributable to the mechanism and to interference between
stored bindings, not to sloppy numerics.** (This is the classical
Holographic Reduced Representation trick, Plate 1995 — an independent
educational reimplementation, not a claim of novelty.)

### Why superposition interferes (the mathematical core of the claim)
For a superposition `x = Σ_i g_i · bind(k_i, v_i)`, unbinding with `k_q`
returns

```
v_q + Σ_{i≠q} v_i ⊛ (k_i ⊛ rev(k_q))
```

The signal term `v_q` has energy `‖v_q‖²`; each cross-talk term is a
phase-scrambled copy of another stored value with energy ~1 **regardless
of dimension**. Consequences, all directly measurable in the metrics:

- readout quality shrinks like `1/√n` with the number of stored pairs —
  this is the *capacity* of the superposition;
- when a competing key `k_i` is similar to `k_q` (controlled by
  `object_similarity`), the cross-talk term retains a component along
  `v_i` proportional to the key similarity — *similar memories bleed into
  each other*;
- two conflicting bindings of the same key (`A→RED`, then `A→GREEN`)
  are stored with equal strength — superposition **cannot prefer the
  newer one** without an additional mechanism.

## 2. The five mechanisms

All writes use effective gain `g = η · μ · importance · strength`
(`η` = update_strength, `μ` = memory_strength). Mechanisms differ only in
how the state absorbs `g·b`:

| # | Mechanism | Update rule | What it demonstrates |
|---|---|---|---|
| A | `baseline` | `x ← x + g·b` | Pure superposition: no forgetting, no recency; interference is purely cross-talk; conflicts tie |
| B | `leaky` | `x ← (1−λ)·x + g·b` | Exponential forgetting (horizon ~1/λ); recency wins; old bindings fade — *state drift* and *retention loss* are visible |
| C | `competitive` | `x ← top_k(x + g·b)`, `k = max(1, ⌊κ·d⌉)` | k-WTA sparsification: memories compete for winning units; capacity limited by `k`, collisions = interference |
| D | `hebbian` | `M ← (1−λ)M + g·v kᵀ`; recall `M k` | Classical linear associative memory (outer products): clean readout, but conflicting associations accumulate rank-1 terms and old values leak into new reads |
| E | `interference` | `x ← (1−λ)x − γ·⟨x, b̂⟩·b̂ + g·b` | Similarity-gated overwrite: a new memory erases the projection of the old state onto its own direction. Aligned (similar) content is replaced; orthogonal content survives untouched. With γ=1, re-writing the same memory *saturates* at `‖b‖` instead of accumulating |

Every mechanism exposes `initialize / update / recall /
explain_update (trace) / get_state_snapshot / step_no_input`, per the
platform contract.

## 3. Recall, ground truth, and confidence

A query "what is the symbol of A?" is answered by reading the predicted
value vector `v̂ = recall(state, k_A)`, then matching it against the
symbol library by cosine similarity:

- `prediction` = best-matching symbol label;
- `ground_truth` = the symbol the *history* dictates: the most recent
  binding ("latest") or the pre-conflict binding ("original") — never an
  external oracle;
- `confidence` = cosine of the best library match (how cleanly the readout
  matches *any* known symbol);
- `correctness` = prediction == ground truth;
- `quality` = cosine(v̂, v_truth) — how close the readout is to the true
  value, independent of the label.

## 4. Task generator

Objects (cues) are flat-spectrum keys with controlled pairwise similarity
(`object_similarity`); symbols (values) are unit Gaussian vectors with
controlled pairwise similarity (`symbol_similarity`). Sequences are built
deterministically: baseline bindings, then `n_conflicts` conflicting
reassignments inserted at spread positions (`structured` / `interleaved` /
`randomized` order). Auto-queries: "latest" for every object at the end,
"latest" right after each conflict, and an "original" probe for each
conflicted object (measures whether the superseded binding survives).

Everything here is **synthetic**: vectors are random, facts are invented,
and ground truth is defined by the generated history. This is a feature —
the learner can vary `input order`, `similarity between competing
memories`, `number of events`, `noise`, and `query timing` with full
knowledge of the true answer.

## 5. Metrics — exact definitions

All metrics are pure functions of the experiment record (snapshots +
query results + task history). `cos` is cosine similarity (0 when either
vector is zero). See `core/metrics.py` for the authoritative text.

| Metric | Definition | Scientific reading |
|---|---|---|
| `recall_accuracy` | fraction of queries with `prediction == ground_truth` | does the mechanism answer correctly? |
| `recall_quality` | mean `cos(v̂_q, v_q)` over queries | how faithful is the readout to the true value? |
| `error_rate` | `1 − recall_accuracy` | complement of accuracy |
| `mean_squared_error` | mean `‖v̂_q − v_q‖²` over queries | raw readout error |
| `state_similarity` | mean `cos(x_t, x_{t−1})` over consecutive snapshots | how stable is the state event-to-event? |
| `state_drift` | mean `1 − cos(x_t, x_{t−1})` | how much does the state re-orient per event? (complement) |
| `update_magnitude` | mean `‖x_t − x_{t−1}‖` (Frobenius for matrices) | how hard does each event push the state? |
| `memory_retention` | mean `cos(v̂, v)` over the final "latest" query per object | what survives to the end of the run? |
| `interference_score` | conflicted objects: mean `max(0, cos(v̂_end, v_superseded))` — leakage of the old binding; no conflicts: mean `1 − cos(v̂, v)` (cross-talk) | how much does competing information contaminate the readout? |
| `recovery_score` | mean over conflicts of `quality(final) / quality(immediately after the conflict write)` | does the correct binding strengthen (>1) or erode (<1) after later events? `None` when no conflicts |

`metrics.details` also carries per-object final quality and per-conflict
breakdowns (old/new symbols, leakage, recovery) for forensics.

## 6. What is synthetic, illustrative, or assumed

**Synthetic.** The task facts, the vector encodings, the symbol library,
the query schedule, and therefore all ground truth. The observed
interference is real arithmetic on those synthetic objects — but nothing
here claims the objects themselves model real-world semantics.

**Illustrative.** The analogy to neural/machine memory. The mechanisms
are deliberately named and shaped like memory architectures (Hebbian
associator, sparse codes, decay) to make the behavior legible; they are
1–2 line update rules, not scaled models of biological or industrial
systems. State dimension `d` is not "capacity" in any calibrated sense —
capacity effects (cross-talk ~`1/√n`, sparse-code collisions) are
demonstrated qualitatively.

**Assumed.** Keys flat-spectrum and unit-norm; values unit-norm; the
symbol library is known to the recall procedure (the learner "knows the
alphabet", not the associations); events arrive one at a time in a known
order; no drift or non-stationarity in the encodings themselves.

## 7. What is NOT being claimed

- The mechanisms are **not** BDH, not BDH-CQ, and not any production
  memory architecture or LLM component. They are independent educational
  toys for comparing state-update behaviors on one harness.
- Interference observed here is **not** evidence about how any real
  neural network forgets; it is a demonstration of the mathematics of
  superposition, decay, sparsity, and associative matrices.
- `recall_quality`/`confidence` are arithmetic similarities, not
  probabilities and not calibrated uncertainties.
- The platform is not a measurement instrument for real systems; it is a
  sandbox in which the learner controls every variable and every answer
  is verifiable.

## 8. Reproducibility

Same `ExperimentConfig` ⇒ identical events, vectors, snapshots, traces,
queries, and metrics (asserted by tests; provable via `/replay`). The
seed is part of the experiment record, and per-event noise seeds are
derived deterministically, so any single state transition can be
replayed in isolation.
---

# Part II — Phase 02 memory engine

## 10. State representation

Identical to Phase 01: `x_t ∈ R^d` (or the Hebbian `d×d` matrix). Nothing
changed about the substrate; Phase 02 adds a *memory layer* on top of it.

## 11. Memory representation

A **Memory** is a named key–value pair:

```
Memory { id, concept, key (concept text), value (value text),
         key_vector, value_vector, vector = bind(key_vector, value_vector),
         importance, strength, creation_timestep, last_accessed_timestep,
         access_count, source_event_id, metadata }
```

Text is converted to vectors by the **deterministic synthetic encoder**
(`core/encoder.py`), reproducible from `(text, seed, d)`: concept texts
become flat-spectrum key vectors (exact-binding property preserved), value
texts become unit Gaussian vectors. **This is an educational encoder, not
a language embedding model** — similar spellings do not imply similar
vectors; semantic similarity must be *controlled explicitly* via
`concept_similarity` / `value_similarity` (batch-correlated encoding).
Documented in `core/encoder.py`.

## 12. Update rule (write)

`write_memory(mech, memory, timestep)` builds the exact Phase 01 event and
applies the mechanism's rule unchanged. It returns an `UpdateResult` that
*splits the state change*:

```
update_vector      = x_after − x_before
memory_contribution    = gain · bind(k, v)          (the write term)
interference_contribution = update_vector − memory_contribution
```

For the baseline mechanism the interference contribution is exactly 0; for
leaky it is the decay `−λ·x_before`; for interference it adds the erasure
`−γ⟨x,b̂⟩b̂`; for competitive it captures whatever the k-WTA competition
removed. Every split is exact by construction and independently verifiable.

## 13. Recall rule (query)

`recall_memory(mech, query, library, …)`:

1. encodes the query concept (deterministic),
2. reads the value out of the current state: `v̂ = recall(mech, k_query)`,
3. ranks the library by `similarity(v̂, memory.value_vector)` under the
   configured measure,
4. prediction = best match; confidence = its similarity; correctness is
   only computed when an `expected_value` is supplied — pure probes return
   `ground_truth: null`, never an invented answer.

## 14. Similarity measures

| measure | formula | meaning |
|---|---|---|
| `cosine` (default) | `<a,b>/(‖a‖‖b‖)` | directional similarity, scale-free |
| `euclidean` | `1/(1+‖a−b‖)` | distance inverted; magnitude matters |
| `dot` | `<a,b>` | raw overlap; larger states score higher |

## 15. Interference

**Our educational model** (a baseline formulation, not a universal law):

```
interference(A, B) = similarity(A, B) × update_strength × competition_factor
```

The platform never uses this formula as ground truth. The *measured*
interference — leakage of a superseded value into a readout, cross-talk
noise, decay erosion — comes from actually running the mechanisms, and
`collision_report` reports **both** the model's prediction and the
measurement so learners can compare them. Controls: similarity (key/value
correlation), update strength (write gains), competition (sparsity /
interference strength γ), decay.

## 16. Decay / forgetting

`decay_rate` (λ) is applied per update step: `x ← (1−λ)x + …`. The
engine genuinely simulates intervening timesteps (`step_no_input` and
long filler sequences in `retention_curve`), so "write A → 10 unrelated
events → query A" vs "… → 100 events → …" produce measurably different
retention. Settings: none (0), weak (~0.1), moderate (~0.3), strong (≥0.6).

## 17. Capacity

`state_dim` (d) is fully configurable and genuinely changes the geometry:
superposition cross-talk scales as `1/√n` at fixed d, so the *same task*
at d=8 vs d=128 yields different retention and interference
(`capacity_sweep`). Same seed + same event texts keep the comparison fair;
only the state's size changes.

## 18. Ablation & counterfactuals

`ablate_event(experiment, event_id)` removes one event, replays the full
history deterministically, and compares. Ground truth is **recomputed from
the counterfactual history** (never carried over); queries scheduled after
the removed event shift back one step; queries about an object whose every
write was ablated are dropped (they have no referent). `reproduced_from_config`
asserts the original run replays byte-identically first.

## 19. Contribution estimation

`analyze_memory_contribution(experiment, memory_id)` estimates a memory's
contribution by replaying the history with and without it and measuring
the final-state difference (`relative_l2`) and recall deltas.

**Limitation (deliberate)**: this is a *replay-based estimate*, **not
true causal attribution**. The mechanisms are nonlinear and interacting
(decay, competition, erasure), so removing one memory changes the whole
trajectory; a linear attribution would be misleading. The response states
this limitation explicitly.

## 20. Comparison

`compare_experiments(a, b)` diffs configuration, metrics, final states
(only when shapes match; Hebbian's d² state is shape-mismatched against
vector states and reported as such), and per-query predictions/outcomes.
It works across mechanisms.

## 21. What is and is not claimed (Phase 02)

**Is:** real, deterministic arithmetic on synthetic vectors; a documented
educational encoder; an explicit, labeled interference model; replay-based
estimates with stated limits.

**Is not:** any claim that the encoder captures meaning, that the
interference formula is general science, that contribution scores are
causal, or that any mechanism equals BDH / BDH-CQ / a production memory
system. BDH-style demonstrations, when they arrive, will be *separate*
mechanisms in the same registry — never presented as equivalent to these
toys.

## 22. Phase 03 — The Experiment Lab

Phase 03 transforms Neural Archaeology from an observational simulator into a
formal experimental laboratory following a disciplined inquiry workflow:

```
QUESTION → HYPOTHESIS → EXPERIMENT → CONTROL → RUN → OBSERVATION → ANALYSIS → CONCLUSION → NEXT EXPERIMENT
```

### Variable Registry and Explicit Roles
Every experimental factor is registered with strict typing, physical/numerical
bounds, and validation rules:
- **Independent Variables**: System knobs manipulated to observe causal effects
  (`memory_similarity`, `update_strength`, `decay`, `interference_strength`,
  `sparsity`, `state_dim`, `n_conflicts`, `input_noise`, `cycles`).
- **Dependent Metrics**: Quantitative outcome signals computed over deterministic
  vector arithmetic (`memory_retention`, `interference_score`, `recall_accuracy`,
  `signal_to_noise_ratio`, `recovery_score`, `write_norm`, `superposition_entropy`,
  `ablation_impact`, `effective_capacity`, `mean_retrieval_cosine`).
- **Controlled Variables**: Background parameters held strictly invariant across
  all conditions to isolate the independent variable.

### Multi-Trial Statistical Rigor
Experiments support multi-trial execution using SHA-256 derived deterministic seeds
(`derive_trial_seed(master_seed, trial_index)`). Aggregation computes mean,
standard deviation, variance, standard error, median, and 95% Student's
t-distribution confidence intervals.

### Controlled Comparisons & Baseline Counterfactuals
`run_controlled_comparison(baseline, treatment)` runs exact counterfactual pairs,
evaluating metric deltas (`Δ = treatment - baseline`), relative percentage shifts,
and vector state differences (`cosine_similarity`, `l2_distance`, `relative_l2`).

### 1D Sweeps, 2D Landscapes & Non-Linearity Detection
`run_parameter_sweep` and `run_grid_sweep` evaluate system response across parameter
axes. `detect_nonlinear_patterns` characterizes non-linear phenomena:
- **Peak (Inverted-U)**: Optimal intermediate parameter value with dropoffs on both sides.
- **Valley (U-shaped)**: Destructive interference dip with recovery.
- **Threshold / Inflection**: Isolated steep gradient surge where metric transitions rapidly.
- **Plateau / Saturation**: Metric stabilizes into asymptotic flatline over extended parameter range.
- **Monotonic**: Consistent growth or decay.
- **Unstable Region**: High fluctuation or sign-alternation under competitive dynamics.

### Hypothesis Testing, Competing Hypotheses & Discriminating Experiments
- **Hypothesis Formulation**: Pre-trial formal declaration of expected direction
  (`INCREASE`, `DECREASE`, `NON_MONOTONIC`, `INVARIANT`) and prior confidence.
- **Evidence Updating**: Post-trial empirical comparison computes observed direction,
  verdict, and adjusts posterior confidence using conservative Bayesian-style bounds
  without overwriting initial predictions.
- **Competing Hypotheses**: Group of mutually exclusive or alternative explanations
  evaluated side-by-side against the same empirical benchmark.
- **Discriminating Experiment Design**: Deterministically identifies the parameter
  regime that maximizes the predicted delta between competing explanations.

### Research Lineage Directed Graphs
`ExperimentGraph` tracks the full provenance of scientific exploration:
- Nodes: `EXPERIMENT`, `HYPOTHESIS`, `FINDING`.
- Directed Edges: `TESTS`, `SUPPORTS`, `CONTRADICTS`, `FOLLOWS_FROM`, `REPRODUCES`, `REFINES`.
- Lineage sub-graphs enable tracing how an initial exploration sparked a hypothesis,
  how a subsequent experiment contradicted it, and how an anomaly inspired a refined theory.

## 23. Scientific Epistemology & Honest Reporting

Neural Archaeology enforces disciplined scientific reporting:
1. **No False Claims of Absolute Truth**: Empirical results "support" or "weaken"
   hypotheses; they do not "prove" universal biological or machine learning truths.
2. **Contextual Scope**: Numerical findings are simulation properties of holographic
   binding and specified memory updates under controlled synthetic conditions.
3. **Reproducibility Guarantee**: Every experiment record embeds complete metadata,
   derived seed lineage, and exact floating-point tolerances ($10^{-9}$), enabling
   bit-exact verification across environments.

## 24. Phase 04 — Counterfactual Memory Archaeology

Phase 04 introduces counterfactual memory archaeology — the ability to branch
historical timelines, introduce precise interventions, re-simulate dynamic memory
trajectories, and rigorously quantify downstream divergence without mutating the
original record.

```
ORIGINAL TIMELINE (Immutable Root)
  t0 ─── t1 ─── t2 ─── t3 ─── t4 ─── t5
                 │
                 └── [Intervention: Change Strength / Ablate / Modify]
                       │
                       ▼
                 BRANCHED TIMELINE (Simulated Alternate History)
                   t2' ─── t3' ─── t4' ─── t5'
                       │
                       ▼
                 DIVERGENCE TRACKING (Propagation Dynamics & Classification)
```

### 1. The Immutability Invariant
The original experiment and its underlying event sequence are strictly immutable.
Any intervention spawns a new `CounterfactualExperiment` node referencing the parent
via `parent_experiment_id`, recording the intervention specification, branch type,
and execution parameters.

### 2. The Intervention Taxonomy
Interventions represent controlled perturbations to history:
- **Structural Event Operations**:
  - `REMOVE_EVENT` (ablation): Delete an event from the historical sequence.
  - `DUPLICATE_EVENT`: Re-insert an event immediately following itself.
  - `REPLACE_EVENT`: Substitute a binding with a different key/value or parameters.
  - `MODIFY_EVENT` (surgery): Modify field values (strength, importance, labels).
  - `MOVE_EVENT`: Relocate an event to earlier or later in sequence.
- **Parametric Perturbations**:
  - `CHANGE_STRENGTH`: Scale or set individual event write gain.
  - `CHANGE_SIMILARITY`: Shift the key vector toward another concept vector.
- **Dynamic State Surgeries**:
  - `RESET_MEMORY`: Re-initialize state vector to zero at a specific timestep.
  - `FREEZE_MEMORY`: Lock state vector across a temporal interval (no updates).
  - `INJECT_MEMORY`: Insert a novel synthetic event at an arbitrary timestep.
- **Temporal Surgeries**:
  - `TEMPORAL_DELETE`: Excise an entire temporal window $[t_{start}, t_{end}]$.
  - `TEMPORAL_FREEZE`: Suspend memory state evolution across $[t_{start}, t_{end}]$.
  - `TEMPORAL_SCALE`: Scale update strengths by factor $\alpha$ across a temporal window.

### 3. Divergence Propagation & Classification
State divergence between original state $s_t$ and counterfactual state $s'_t$ is
tracked across all timesteps $t$:
- **Metric Suite**:
  - Euclidean distance: $d_{L2}(t) = \|s'_t - s_t\|_2$
  - Relative distance: $d_{rel}(t) = \frac{\|s'_t - s_t\|_2}{\|s_t\|_2 + \epsilon}$
  - Directional alignment: $\cos(s_t, s'_t)$
  - Memory Partitioning: `affected_memories` vs `unaffected_memories` based on
    query-level retrieval deviations.
- **Propagation Dynamics Classification**:
  - `IMMEDIATE`: Jump to peak divergence at intervention step, remaining stable.
  - `DELAYED`: Initial latency before downstream divergence manifests.
  - `CUMULATIVE`: Monotonically increasing divergence across subsequent writes.
  - `EXPLOSIVE`: Super-linear accelerating divergence propagation downstream.
  - `DAMPED`: Initial peak followed by steady attenuation or recovery.
  - `OSCILLATING`: Repeated inflection and fluctuation across writes.
  - `LOCALIZED`: Disruption confined to targeted object; overall manifold stable.
  - `GLOBAL`: Wide catastrophic disruption across >= 70% of memory representations.
  - `TRANSIENT`: Sharp divergence returning to near-zero ($< 10^{-4}$).
  - `PERSISTENT`: Substantial divergence remaining at final evaluation timestep.
  - `CONVERGENT`: Trajectories re-converging toward similar final representations.

### 4. Forensic Contribution Analysis & Forgetting Reconstruction
When a memory $M_k$ is forgotten or degraded in the final state, forensic analysis
executes counterfactual ablations across all historical writes $t \in [0, T-1]$:
$$\Delta \text{Metric}(t) = \text{Metric}(\text{Ablated}_t) - \text{Metric}(\text{Original})$$
Events are ranked by their empirical counterfactual effect size, identifying the
specific historical write that caused the greatest retroactive interference.

### 5. Minimal Intervention Optimization
Given a target improvement $\delta^*$ on an objective metric, the search engine
evaluates candidate interventions across param ranges and identifies the
minimal intervention:
$$\text{argmin}_{I \in \mathcal{I}} \|I\| \quad \text{s.t.} \quad \Delta \text{Metric}(I) \ge \delta^*$$
where $\|I\|$ is the normalized intervention magnitude ($|\Delta \text{strength}|$,
$|\Delta t| / T$, or discrete change magnitude).

### 6. Causal Framing & Epistemology
In accordance with platform scientific principles:
- Divergences are labeled as *"observed counterfactual divergence under simulated replay"*,
  never dogmatic real-world causality.
- All counterfactual simulations execute through the exact mathematical memory engine;
  mock results and synthetic interpolations are strictly forbidden.
- Re-simulation is verified to within $10^{-9}$ floating-point tolerance, ensuring
  deterministic reproducibility across platforms.
