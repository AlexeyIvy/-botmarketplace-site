# LAB POST-PHASE-5 ROADMAP — Research Platform Expansion

**Project:** BotMarketplace
**Repository:** `AlexeyIvy/-botmarketplace-site`
**Status:** Planning — verified against existing code and docs (March 2026)
**Author role:** Senior Software Engineer / Product Architect
**Scope:** Forward planning for `/lab` after Phase 5 (backtest runner) is complete. Identifies the primary architectural blocker before Phase 6, defines the graph lifecycle model required for Phase 3A completion, and proposes a genuinely new post-Phase-6 expansion layer.
**Change type:** Docs-only planning document. No code changes, no migrations, no API changes.

---

## Document structure

This document is organized into four distinct layers:

1. **Current implementation audit** (§2) — phase-by-phase status with explicit blocking analysis
2. **Primary architectural blocker** (§3–§5) — Phase 3A graph persistence gap, lifecycle state model, backend contract
3. **Existing next step from docs/23** (§6) — Phase 6 pointer; no re-specification
4. **New proposals beyond docs/23** (§7–§9) — post-Phase-6 expansion; none start before Phase 3A is accepted

---

## 1. Purpose

This document defines what comes next for `/lab` after Phase 5 completion. It does **not** replace or duplicate existing specs.

**What this document does:**
- Records implementation status as of Phase 5 acceptance, distinguishing complete vs incomplete phases and whether each gap blocks Phase 6
- Identifies the primary architectural blocker (Phase 3A graph persistence) that must close before Phase 6 begins
- Establishes the graph lifecycle state model that Phase 3A implementation must satisfy
- Points to Phase 6 scope as already defined in `docs/23` — no re-specification here
- Proposes a new, post-Phase-6 expansion layer (block library Tier 2, multi-dataset binding, parameter sweep) that is **not covered by any existing document**
- Names the task packs that need to be created next

**What this document does NOT do:**
- Re-specify anything already in `docs/23-lab-v2-ide-spec.md` (Phases 0–6) or `docs/22-productization-v2-plan.md` (Stages 7–14)
- Propose code changes or migrations
- Serve as an executable task pack itself

**Primary references:**

| Doc | Covers |
|---|---|
| `docs/23-lab-v2-ide-spec.md` | Canonical Lab v2 spec: Phases 0–6, frozen decisions, block spec |
| `docs/22-productization-v2-plan.md` | Productization v2: Stages 7–14, stage discipline rules |
| `docs/10-strategy-dsl.md` | Strategy DSL contract, block-to-DSL mapping table |
| `docs/07-data-model.md` | Data model including Phase 3+ entities |

---

## 2. Current implementation audit

### 2.1 Phase implementation status

> The "Blocks Phase 6?" column distinguishes gating items from acceptable partial completions.
> Phase 6 requires a stable, persisted graph identity (`StrategyGraph` + `StrategyGraphVersion`).
> Dataset builder completeness and graph persistence are orthogonal concerns — a partial Data tab does not affect graph lifecycle.

| Phase | Deliverable | Status | Blocks Phase 6? | Evidence |
|---|---|---|---|---|
| Phase 0 | Docs freeze, glossary updates, doc cross-references | ✅ Complete | No | `docs/23 §22` — all doc updates marked Done |
| Phase 1A | LabShell layout, resizable panels, tab bar (`Data / Build / Test / Classic`) | ✅ Complete | No | `apps/web/src/app/lab/LabShell.tsx` |
| Phase 1B | Context bar, `useLabGraphStore` (Zustand), compile/run state wiring | ✅ Complete | No | `apps/web/src/app/lab/useLabGraphStore.ts` |
| Phase 2 | Data tab, `MarketDataset.name` column, `DatasetPreview` component | ⚠️ Partial | **No** — see note | `apps/web/src/app/lab/data/page.tsx` implements §6.2 controls; chart view (Phase 2B2) not verified complete |
| Phase 3A | Graph load-on-mount + auto-save cycle against DB | ❌ Incomplete | **Yes** — see §3 | No mount-time graph load; no auto-save path; compile is current sole persistence trigger |
| Phase 3B | `BlockPalette`, `StrategyNode`, `StrategyEdge`, `InspectorPanel`, `ConnectionContext` | ✅ Complete | No | `apps/web/src/app/lab/build/` directory |
| Phase 3C | Client-side validation rules, error badges on nodes, `ValidationDrawer` | ✅ Complete | No | `apps/web/src/app/lab/build/page.tsx`, `StrategyNode.tsx`, `useLabGraphStore.ts` |
| Phase 4A | `graphCompiler.ts` — block-to-DSL compiler, server-side validation | ✅ Complete | No | `apps/api/src/lib/graphCompiler.ts` |
| Phase 4B | Compile UI, DSL preview tab, server error mapping to nodes | ✅ Complete | No | `apps/web/src/app/lab/LabShell.tsx` compile flow |
| Phase 5A | `POST /api/v1/lab/backtest`, `BacktestResult` reproducibility binding | ✅ Complete | No | `apps/api/src/routes/lab.ts` |
| Phase 5B | Backtest results UI: metrics, trades, equity, logs, warnings | ✅ Complete | No | `apps/web/src/app/lab/test/page.tsx` |
| Phase 6 | Private data blocks, stale-state detection, compare runs, annotate_event | ❌ Not started | N/A (starting point) | Spec in `docs/23 §Phase 6` |

**Note on Phase 2 Partial:**
`apps/web/src/app/lab/data/page.tsx` (line 6 header) explicitly implements the §6.2 mandatory controls: exchange, symbol, interval, date range, client-side validation. `DatasetPreview` implements the paginated table view (Phase 2B1). The OHLCV chart via `lightweight-charts` (Phase 2B2) is not verified complete.

This gap does **not** block Phase 6. Phase 6 depends on:
- A stable, persisted `StrategyGraph` identity → gated by Phase 3A
- `ExchangeConnection` state for private data blocks → already implemented (Stage 8)

Neither dependency requires Phase 2B2 completion. Phase 2B2 is recommended before Phase 6 work begins, but it is not a hard gate. It should be tracked as a standalone cleanup item, not treated as a Phase 6 prerequisite.

### 2.2 Block library — current vs spec'd

The compiler currently handles 9 blocks. `docs/23 §6.3` defines the full intended library.

| Block | Implemented | Notes |
|---|---|---|
| candles | ✅ | Input block |
| SMA, EMA, RSI | ✅ | Indicator blocks |
| compare, cross | ✅ | Logic blocks |
| enter_long, enter_short | ✅ | Execution blocks |
| stop_loss, take_profit | ✅ | Risk blocks |
| ATR | ❌ | Referenced in stop_loss (type: "atr") but no standalone ATR indicator block |
| MACD, VWAP, volatility, volume metrics | ❌ | Spec'd in docs/23 §6.3; not in `blockDefs.ts` |
| Transform blocks (merge, resample, filter, etc.) | ❌ | Spec'd in docs/23 §6.3 |
| Logic blocks (AND/OR/NOT, confirm N bars, debounce) | ❌ | Spec'd in docs/23 §6.3 |
| Risk blocks (trailing stop, max drawdown, daily loss stop, etc.) | ❌ | Spec'd in docs/23 §6.3 |
| Debug/observability blocks | ❌ | Spec'd in docs/23 §6.3 (log value, annotate event, inspect series) |

---

## 3. Primary architectural blocker: Phase 3A graph persistence

**Phase 3A is the only identified blocking gap in the graph lifecycle before Phase 6 can begin.**

This statement is scoped to the graph lifecycle. Other partial items (see §2.1 Phase 2 note) exist but do not affect the graph identity required by Phase 6.

### 3.1 What is missing

The current implementation creates a `StrategyGraph` DB record on-demand during compile only. **Compile must not be the first — or the only — persistence path.** The graph must be persisted as a draft independently of whether the user ever compiles.

The frontend Zustand store (`useLabGraphStore`) does not:

1. Load an existing graph from DB when the user opens `/lab/build` (no `GET /api/v1/lab/graphs` call on mount)
2. Auto-save graph edits back to DB (no debounced `PATCH /api/v1/lab/graphs/:id` on Zustand state change)
3. Handle the empty-state case: when `GET /api/v1/lab/graphs` returns no records, a first draft must be created (via `POST /api/v1/lab/graphs`) before the canvas is interactive
4. Show a graph selector if multiple graphs exist for a workspace

**Consequence:** Graph state (nodes, edges) is lost on navigation unless the user explicitly compiles. The `activeGraphId` in the Zustand store is set during compile but is not restored on next page load.

### 3.2 Persistence semantics

The Phase 3A implementation must distinguish these three concepts explicitly:

| Concept | Definition |
|---|---|
| **Unsaved local graph state** | Nodes/edges in Zustand only; not written to DB. Exists between user edits and autosave debounce firing. Lost on page reload. |
| **Persisted graph draft** | `graphJson` written to `StrategyGraph` in DB via `PATCH /api/v1/lab/graphs/:id`. Survives reload. Not a compiled version. A graph can be a valid persisted draft without ever being compiled. |
| **Compiled graph version** | A `StrategyGraphVersion` record produced by the compile step. References a specific snapshot of `graphJson`. The backtest runs against this. The live draft may have diverged from the last compiled version. |

These are three distinct states. A compile action produces a `StrategyGraphVersion` from the current draft, but it does not substitute for the auto-save path. A persisted draft that has never been compiled is the normal state for a graph mid-construction.

### 3.3 Required persistence behaviors

**1. Mount — graph found:**
Call `GET /api/v1/lab/graphs` on `/lab/build` mount → load most-recent graph for the active workspace → populate Zustand `nodes`, `edges`, `activeGraphId`. The canvas must not render interactable content before this load completes.

**2. Mount — empty response:**
If `GET /api/v1/lab/graphs` returns an empty list for the workspace, immediately call `POST /api/v1/lab/graphs` to create the first empty draft → then populate Zustand as above. The user must not see an error or a blank non-interactive canvas because no graph exists yet.

**3. Auto-save:**
Debounced Zustand subscription (1–2s delay) → `PATCH /api/v1/lab/graphs/:id` with current `graphJson`.

Auto-save **must not fire during initial hydration.** The debounce subscription must be attached only after the mount load sequence (steps 1 or 2 above) completes successfully. Attaching the subscription before hydration completes will trigger a spurious write on every mount.

**4. Graph switch with dirty state:**
If the user switches to a different graph while the current graph has unsaved local changes (state `dirty`), the implementation must either: (a) flush the auto-save immediately before switching, or (b) prompt the user. Silently discarding dirty state on switch is not acceptable behavior.

**5. Undo/redo interaction with auto-save:**
Undo/redo operations modify `nodes`/`edges` in Zustand and must trigger the auto-save debounce. This is the correct behavior — undo/redo state must survive reload. The debounce timer resets on each undo/redo action, coalescing rapid keyboard undo sequences into a single write.

**6. Graph selector:**
Minimal control in Context Bar — current graph name, create-new action, switch between graphs for the workspace.

**Out of scope for Phase 3A:** graph version branching, team sharing, multi-workspace graphs — all excluded in `docs/23 §26`.

**Task pack to create:** `docs/steps/23a-lab-phase3a-graph-persistence.md`

### 3.4 Why this blocks Phase 6

Phase 6 requires:
- **Stale-state detection** — comparing active graph + dataset + connection against the state at last run. Requires a stable, persisted graph identity that exists independently of compile.
- **Private data blocks** — permission state is tied to `ExchangeConnection`. Meaningful only if the graph persists between sessions.
- **Compare runs** — both runs must reference a specific `StrategyGraphVersion`. Requires a full graph persistence lifecycle to be stable.

---

## 4. Graph lifecycle state model

The Phase 3A implementation must track graph save state explicitly and independently from validation state and compile state. The following save states are required:

| State | Meaning |
|---|---|
| `clean` | Local Zustand state matches last persisted `graphJson` in DB |
| `dirty` | Local Zustand state has unsaved changes; auto-save debounce timer running |
| `saving` | `PATCH /api/v1/lab/graphs/:id` in flight |
| `save_error` | Last `PATCH` failed; user must be notified; retry available |
| `stale_against_last_compile` | Graph has been edited since the last compile; the active `StrategyGraphVersion` no longer matches current draft |

**Critical invariants — these must not be violated:**

| Invariant | Implication |
|---|---|
| **Save state ≠ validation state** | A graph can be `dirty` and pass all client-side validation rules, or be `clean` and fail them. These are independent concerns tracked in separate store fields. |
| **Save state ≠ compile state** | A graph can be `clean` (persisted) but never compiled. A graph can be `saving` while also `stale_against_last_compile`. Do not conflate persistence status with compile readiness. |
| **Dirty graph ≠ invalid graph** | The compile button must remain available for a `dirty` graph. Auto-save failure must not block compile. Validation errors must not prevent saves. |

Violating these invariants produces UX bugs (e.g., graying out compile because save is in flight) and architectural coupling that would make Phase 6 stale-state detection unreliable.

---

## 5. Backend contract for graph persistence

`docs/23 §13` specifies the canonical endpoints:

```
GET   /api/v1/lab/graphs               — list graphs for workspace
GET   /api/v1/lab/graphs/:id           — load specific graph
POST  /api/v1/lab/graphs               — create new graph draft
PATCH /api/v1/lab/graphs/:id           — save draft (patch semantics, auto-save friendly)
```

`PATCH` (not `PUT`) is the canonical auto-save endpoint. Patch semantics — partial `graphJson` updates are acceptable; full replacement is not required on each debounce fire.

**Verification required:** The first task in `docs/steps/23a-lab-phase3a-graph-persistence.md` must verify that these endpoints exist as spec'd in the current backend (`apps/api/src/routes/lab.ts`) and that their request/response shapes match `docs/23 §13`. If drift is found between the spec and the current implementation, the task pack must include an explicit endpoint alignment step before frontend work begins. Do not assume backend contract matches spec without verification.

---

## 6. Phase 6 execution (already spec'd in docs/23)

Phase 6 scope is fully defined in `docs/23 §Phase 6`. Do not re-specify it here.

Summary of what Phase 6 covers (for reference only):

- Private data input blocks: `ordersHistory`, `executionsHistory` — greyed out without active `ExchangeConnection`
- Visual distinction for private blocks: orange dot + lock icon
- Stale-state detection: badges after dataset, connection, or graph change
- Compare runs view: side-by-side `BacktestResult` metrics (`GET /api/v1/lab/backtests/compare` — already spec'd in `docs/23 §14`)
- Advanced diagnostics: `annotate_event` block marks equity curve points

**Prerequisite:** Phase 3A completion (§3 above).

**Task pack to create:** `docs/steps/23b-lab-phase6.md`

---

## 7. Overlap analysis: draft topics vs existing docs

| Topic | Already in docs/23 | Already in docs/22 | In code | New proposal | Notes |
|---|---|---|---|---|---|
| Phase 6 private data blocks | ✅ §Phase 6 | — | ❌ | — | Fully spec'd; just needs task pack |
| Phase 6 stale-state detection | ✅ §Phase 6 | — | ❌ | — | Fully spec'd |
| Phase 6 compare runs | ✅ §Phase 6, §14 | — | ❌ | — | Endpoint spec'd; UI + endpoint not built |
| Graph persistence (Phase 3A) | ✅ §Phase 3 | — | ❌ | — | Spec'd; identified here as gating blocker |
| Block library expansion (beyond 9 blocks) | ✅ §6.3 (full list) | — | ❌ (partial) | **§8.1** | Not all spec'd blocks are implemented |
| Multi-dataset binding | ✅ §26 (explicitly deferred) | — | ❌ | **§8.2** | Post-Phase-6 and post-governance only; see §8.2 |
| Parameter sweep / optimization | — | ✅ §6 (explicitly deferred) | ❌ | **§8.3** | Narrow bounded proposal; see §8.3 for hard scope constraints |
| DSL ↔ graph bidirectional view | ✅ §9.3 (optional) | — | ❌ | **§8.4** | High-risk; spike-only; not to be scheduled before persistence/governance stable |
| Subgraphs / nested graphs | ✅ §26 (excluded Phase 3, deferred Phase 6+) | — | ❌ | — | Not proposed here; no spec exists yet |
| Real-time collaboration | ✅ §26 (excluded) | — | ❌ | — | Not proposed; CRDT required |
| Graph version branching | ✅ §26 (excluded) | — | ❌ | — | Not proposed; linear versions only |
| Auth / workspace enforcement | — | ✅ Stage 7 | ✅ | — | Already implemented |
| Exchange Connections | — | ✅ Stage 8 | ✅ | — | Already implemented |
| Research Lab reproducibility | ✅ Phase 5 | ✅ Stage 12 | ✅ | — | Phase 5 satisfies Stage 12 |
| Observability | — | ✅ Stage 13 | Partial | — | Not Lab-specific; see docs/22 |

---

## 8. Post-Phase-6 expansion proposals

These are genuinely new proposals not covered by `docs/23` or `docs/22`.

**None of these should begin before Phase 3A is accepted AND Phase 6 is accepted.** See §9 (Immediate next action) for the authoritative execution gate.

### 8.1 Block library Tier 2

**Context:** Current 9-block library covers minimal viable strategy composition. `docs/23 §6.3` lists the full intended library; the compiler infrastructure is ready to receive new block types.

**Proposed tier 2 blocks (first batch):**

| Block | Category | DSL target field | Prerequisite |
|---|---|---|---|
| ATR | Indicator | `indicators[].type: "ATR"` | Needed for stop_loss `type: "atr"` to be useful |
| MACD | Indicator | `indicators[].type: "MACD"` | Common strategy primitive |
| AND / OR / NOT | Logic | `signals[].logic` compound | Multi-signal strategies |
| confirm N bars | Logic | `signals[].confirm` | Signal persistence filter |
| trailing_stop | Risk | `risk.trailingStop` | Already in DSL spec §6; block missing |
| close | Execution | `execution.closeSignal` | Exit signal complement |

**Constraint:** Any new block type that requires extending `StrategyVersion.body` schema must first update `docs/10-strategy-dsl.md`. No undocumented DSL extensions.

**Task pack to create:** `docs/steps/25-lab-block-tier2.md`

### 8.2 Multi-dataset binding

> **Priority: Not immediate. Post-Phase-6 and post-governance only. Requires a separate schema decision before any implementation can begin.**

**Context:** `docs/23 §26` explicitly defers this: "One active dataset per LabWorkspace in Phase 3." This proposal is for after Phase 6 is accepted and the governance layer (docs/22 Stages 7–10) is confirmed stable.

**Proposal:**
- `LabWorkspace` holds up to 3 dataset slots (primary + 2 comparison)
- `candles` block has a slot selector (`primary | comparison-1 | comparison-2`)
- Backtest always runs on `primary` slot — comparison slots are visual reference only
- `LabWorkspace.datasetSlots: uuid[]` field addition (schema change — requires `docs/07-data-model.md` update before implementation)

**Constraints:**
- Requires a `LabWorkspace` schema migration. Must not be implemented without first updating `docs/07-data-model.md` and getting that doc change reviewed.
- Must not begin before Phase 6 is accepted.
- Must not begin before the governance layer (docs/22 Stages 7–10) is confirmed stable — multi-dataset binding interacts with workspace-level permissions.
- The task pack for this proposal must not be created until the schema decision is documented in `docs/07-data-model.md`.

**Task pack to create:** `docs/steps/26-lab-multi-dataset.md` — blocked on Phase 6 acceptance + schema decision.

### 8.3 Parameter sweep (basic)

> **Scope is explicitly bounded. Any implementation that exceeds the constraints below is out of scope and the PR must be rejected.**

**Context:** `docs/22 §6` explicitly defers "complex optimization/parameter search" from Productization v2. This proposal is a deliberately narrow first step — not a full optimizer.

**Proposal:**
- "Sweep" UI in Test mode: select **one indicator parameter only**, define a range + step
- Triggers N sequential backtest runs via existing `POST /api/v1/lab/backtest`
- Results table: one row per run, columns = key metrics (net PnL, winrate, max drawdown)

**Hard scope boundaries (any deviation requires a new planning doc):**
- One parameter only — no multi-parameter grid search in this version
- Maximum run count capped (suggested: 20 runs per sweep)
- Sequential execution only — no parallel run orchestration
- No optimizer / genetic algorithm / Bayesian search — those are separate product features
- No "best strategy" auto-selection logic
- No new DB entity in the first version — sweep state is UI-only; each run is an independent `BacktestResult` record
- Rate limits: respect existing `POST /lab/backtest` limits per workspace

**Task pack to create:** `docs/steps/27-lab-param-sweep.md`

### 8.4 DSL ↔ graph bidirectional view

> **Risk classification: HIGH. Not immediate. Spike-only first. Must not be scheduled before the persistence layer (Phase 3A) and governance layer are stable.**

**Context:** `docs/23 §9.3` mentions this as a Phase 6 optional: "DSL editor and graph editor become interchangeable views where feasible."

**Proposal:**
- Forward direction (graph → DSL): already done in Phase 4B as read-only DSL preview
- Reverse direction (DSL → graph): parse a DSL JSON → reconstruct graph nodes/edges in canvas

**Hard constraint:** A technical spike is required before any implementation commitment. Reverse compile is significantly harder than forward compile — the DSL is lossy relative to graph layout. The spike must answer: which DSL constructs are reversible and which are not. A failed or scoped-down spike is a valid outcome.

**Do not create a task pack for this until all three conditions are met:**
1. Phase 3A is accepted
2. Phase 6 is accepted
3. The spike produces a written feasibility note

---

## 9. Immediate next action

**This section is the authoritative statement of what happens next. It overrides any ordering inference from other sections.**

- **Next task pack to create:** `docs/steps/23a-lab-phase3a-graph-persistence.md`
- **No other proposal in this document should start before `docs/steps/23a` is accepted.**
- After `docs/steps/23a` is accepted: create `docs/steps/23b-lab-phase6.md` (per `docs/23 §Phase 6`).
- After Phase 6 is accepted: block library Tier 2 (§8.1) may be scheduled.
- Multi-dataset binding (§8.2), parameter sweep (§8.3), and DSL↔graph (§8.4) are not near-term items. Each has explicit preconditions listed in its section that must be satisfied before a task pack is created.

---

## 10. Scope boundaries

This roadmap explicitly does NOT propose:

| Out-of-scope item | Reason |
|---|---|
| Subgraphs / nested graphs | Excluded in `docs/23 §26`; no design spec exists |
| Real-time collaborative canvas | Excluded in `docs/23 §26`; requires CRDT/OT infrastructure |
| Graph version branching / merge | Excluded in `docs/23 §26`; `StrategyGraphVersion` is linear |
| Portfolio optimizer / multi-strategy optimization | Separate product feature; no spec |
| Production-grade multi-tenant architecture | Out of scope per `docs/22 §6` |
| Mobile / touch canvas | Desktop-first; excluded in `docs/23 §26` |
| High-availability / cluster orchestration | Out of scope per `docs/22 §6` |
| Arbitrary custom code blocks (user JS/Python) | Security model violation; excluded in `docs/23 §26` |
| Changes to Stages 7–14 scope | Those stages are defined in `docs/22`; not modified here |

---

## 11. Recommended execution order

```
1. Phase 3A completion          → docs/steps/23a-lab-phase3a-graph-persistence.md
2. Phase 6 execution            → docs/steps/23b-lab-phase6.md  (per docs/23 §Phase 6)
3. Block library Tier 2         → docs/steps/25-lab-block-tier2.md  (after Phase 6 accepted)
4. Multi-dataset binding        → docs/steps/26-lab-multi-dataset.md  (after Phase 6 + governance stable; schema decision required)
5. Parameter sweep              → docs/steps/27-lab-param-sweep.md  (after Phase 6 accepted; bounded scope per §8.3)
6. DSL ↔ graph bidirectional    → spike first; no task pack until feasibility confirmed AND Phase 6 accepted
```

The task packs listed above do not exist yet. They must be created before any implementation begins. Each task pack must follow the format defined in `docs/22 §8`.

---

## 12. Stage acceptance discipline

All task packs derived from this roadmap must comply with the acceptance rule from `docs/22 §7`:

1. All required outputs delivered
2. Acceptance checks are verifiable by commands/steps
3. PR history shows no scope creep
4. Documentation updated in the same PR
5. Handover note prepared for the next task pack

This applies equally to Phase completion items (Phase 3A) and new expansion proposals (§8).
