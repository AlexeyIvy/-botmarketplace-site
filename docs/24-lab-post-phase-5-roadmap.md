# LAB POST-PHASE-5 ROADMAP — Research Platform Expansion

**Project:** BotMarketplace
**Repository:** `AlexeyIvy/-botmarketplace-site`
**Status:** Planning — verified against existing code and docs (March 2026)
**Author role:** Senior Software Engineer / Product Architect
**Scope:** Forward planning for `/lab` after Phase 5 (backtest runner) is complete. Defines the gap between current implementation and Phase 6, then proposes a genuinely new post-Phase-6 expansion layer.
**Change type:** Docs-only planning document. No code changes, no migrations, no API changes.

---

## 1. Purpose

This document defines what comes next for `/lab` after Phase 5 completion. It does **not** replace or duplicate existing specs.

**What this document does:**
- Records implementation status as of Phase 5 acceptance, distinguishing complete vs incomplete phases
- Identifies the one gating incomplete item (Phase 3A graph persistence) that must close before Phase 6 begins
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

## 2. Current state after Phase 5

### 2.1 Phase implementation status

| Phase | Deliverable | Status | Evidence |
|---|---|---|---|
| Phase 0 | Docs freeze, glossary updates, doc cross-references | ✅ Complete | docs/23 §22 — all doc updates marked Done |
| Phase 1A | LabShell layout, resizable panels, tab bar (`Data / Build / Test / Classic`) | ✅ Complete | `apps/web/src/app/lab/LabShell.tsx` |
| Phase 1B | Context bar, `useLabGraphStore` (Zustand), compile/run state wiring | ✅ Complete | `apps/web/src/app/lab/useLabGraphStore.ts` |
| Phase 2 | Data tab, `MarketDataset.name` column, `DatasetPreview` component | ⚠️ Partial | `apps/web/src/app/lab/DatasetPreview.tsx` exists; full dataset builder form (docs/23 §6.2 controls) not verified complete |
| Phase 3A | Graph load-on-mount + auto-save cycle against DB | ❌ Incomplete | See §3 below |
| Phase 3B | `BlockPalette`, `StrategyNode`, `StrategyEdge`, `InspectorPanel`, `ConnectionContext` | ✅ Complete | `apps/web/src/app/lab/build/` directory |
| Phase 3C | Client-side validation rules, error badges on nodes, `ValidationDrawer` | ✅ Complete | `apps/web/src/app/lab/build/page.tsx`, `StrategyNode.tsx`, `useLabGraphStore.ts` |
| Phase 4A | `graphCompiler.ts` — block-to-DSL compiler, server-side validation | ✅ Complete | `apps/api/src/lib/graphCompiler.ts` |
| Phase 4B | Compile UI, DSL preview tab, server error mapping to nodes | ✅ Complete | `apps/web/src/app/lab/LabShell.tsx` compile flow |
| Phase 5A | `POST /api/v1/lab/backtest`, `BacktestResult` reproducibility binding | ✅ Complete | `apps/api/src/routes/lab.ts` |
| Phase 5B | Backtest results UI: metrics, trades, equity, logs, warnings | ✅ Complete | `apps/web/src/app/lab/test/page.tsx` |
| Phase 6 | Private data blocks, stale-state detection, compare runs, annotate_event | ❌ Not started | Spec in `docs/23 §Phase 6` |

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

## 3. Phase 3A gap: graph persistence (Phase 6 blocker)

**This is the only incomplete gating item before Phase 6 can begin.**

### 3.1 What is missing

The current implementation creates a `StrategyGraph` DB record on-demand during compile only. The frontend Zustand store (`useLabGraphStore`) does not:

1. Load an existing graph from DB when the user opens `/lab` (no `GET /api/v1/lab/graphs/:id` call on mount)
2. Auto-save graph edits back to DB (no `PATCH /api/v1/lab/graphs/:id` on Zustand state change)
3. Show a graph selector if multiple graphs exist for a workspace

**Consequence:** Graph state (nodes, edges) is lost on navigation unless the user explicitly runs compile. The `activeGraphId` in the Zustand store is set during compile but is not restored on next page load.

### 3.2 Why this blocks Phase 6

Phase 6 requires:
- **Stale-state detection** — comparing active graph + dataset + connection against the state at last run. Requires a stable, persisted graph identity.
- **Private data blocks** — permission state is tied to `ExchangeConnection`. Meaningful only if the graph persists between sessions.
- **Compare runs** — both runs must reference a specific `StrategyGraphVersion`. Requires full graph persistence lifecycle.

The backend endpoints already exist (`GET /api/v1/lab/graphs`, `POST /api/v1/lab/graphs`, `PATCH` or `PUT` if needed). The gap is frontend-only.

### 3.3 Phase 3A completion scope

1. On `/lab/build` mount: call `GET /api/v1/lab/graphs` → load most-recent graph → populate Zustand `nodes`, `edges`, `activeGraphId`
2. Auto-save: debounced Zustand subscription (1–2s delay) → update `graphJson` in DB
3. Graph selector: minimal control in Context Bar — current graph name, create-new action, switch

**Out of scope for this completion:** graph version branching, team sharing, multi-workspace graphs — all excluded in `docs/23 §26`.

**Task pack to create:** `docs/steps/23a-lab-phase3a-graph-persistence.md`

---

## 4. Phase 6 execution (already spec'd in docs/23)

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

## 5. Overlap analysis: draft topics vs existing docs

The original task referenced a draft ("LAB POST-PHASE-5 ROADMAP — Research Platform Expansion") that was not submitted inline. The table below maps the expected draft topics against repository state.

| Topic | Already in docs/23 | Already in docs/22 | In code | New proposal | Notes |
|---|---|---|---|---|---|
| Phase 6 private data blocks | ✅ §Phase 6 | — | ❌ | — | Fully spec'd; just needs task pack |
| Phase 6 stale-state detection | ✅ §Phase 6 | — | ❌ | — | Fully spec'd |
| Phase 6 compare runs | ✅ §Phase 6, §14 | — | ❌ | — | Endpoint spec'd; UI + endpoint not built |
| Graph persistence (Phase 3A) | ✅ §Phase 3 | — | ❌ | — | Spec'd; identified here as gating blocker |
| Block library expansion (beyond 9 blocks) | ✅ §6.3 (full list) | — | ❌ (partial) | **§6.1** | Not all spec'd blocks are implemented |
| Multi-dataset binding | ✅ §26 (explicitly deferred) | — | ❌ | **§6.2** | One dataset per LabWorkspace — post-Phase-6 expansion |
| Parameter sweep / optimization | — | ✅ §6 (explicitly deferred) | ❌ | **§6.3** | Narrow first proposal in §6.3 |
| DSL ↔ graph bidirectional view | ✅ §9.3 (optional) | — | ❌ | **§6.4** | Spike required; hard reverse-compile problem |
| Subgraphs / nested graphs | ✅ §26 (excluded Phase 3, deferred Phase 6+) | — | ❌ | — | Not proposed here; no spec exists yet |
| Real-time collaboration | ✅ §26 (excluded) | — | ❌ | — | Not proposed; CRDT required |
| Graph version branching | ✅ §26 (excluded) | — | ❌ | — | Not proposed; linear versions only |
| Auth / workspace enforcement | — | ✅ Stage 7 | ✅ | — | Already implemented |
| Exchange Connections | — | ✅ Stage 8 | ✅ | — | Already implemented |
| Research Lab reproducibility | ✅ Phase 5 | ✅ Stage 12 | ✅ | — | Phase 5 satisfies Stage 12 |
| Observability | — | ✅ Stage 13 | Partial | — | Not Lab-specific; see docs/22 |

---

## 6. Post-Phase-6 expansion proposals

These are genuinely new proposals not covered by `docs/23` or `docs/22`. None should be executed until Phase 6 is accepted.

### 6.1 Block library Tier 2

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

### 6.2 Multi-dataset binding

**Context:** `docs/23 §26` explicitly defers this: "One active dataset per LabWorkspace in Phase 3." The correct MVP boundary. This proposal is for post-Phase-6 only.

**Proposal:**
- `LabWorkspace` holds up to 3 dataset slots (primary + 2 comparison)
- `candles` block has a slot selector (`primary | comparison-1 | comparison-2`)
- Backtest always runs on `primary` slot — comparison slots are visual reference only
- `LabWorkspace.datasetSlots: uuid[]` field addition (schema change — requires `docs/07-data-model.md` update before implementation)

**Constraint:** This requires a `LabWorkspace` schema migration. Must not be implemented without first updating `docs/07-data-model.md` and getting that doc change reviewed. Schema changes are not part of this planning document.

**Task pack to create:** `docs/steps/26-lab-multi-dataset.md`

### 6.3 Parameter sweep (basic)

**Context:** `docs/22 §6` explicitly defers "complex optimization/parameter search" from Productization v2. This proposal is a deliberately narrow first step — not a full optimizer.

**Proposal:**
- "Sweep" UI in Test mode: select one indicator parameter, define a range + step
- Triggers N sequential backtest runs via existing `POST /api/v1/lab/backtest`
- Results table: one row per run, columns = key metrics (net PnL, winrate, max drawdown)
- No multi-parameter grid search, no genetic algorithms — those are separate product features

**Constraint:** Each sweep run is an independent `BacktestResult` record. No new "sweep run" DB entity in the initial implementation. Sweep state is UI-only. Rate limit: respect existing `POST /lab/backtest` limits.

**Task pack to create:** `docs/steps/27-lab-param-sweep.md`

### 6.4 DSL ↔ graph bidirectional view (spike-first)

**Context:** `docs/23 §9.3` mentions this as a Phase 6 optional: "DSL editor and graph editor become interchangeable views where feasible."

**Proposal:**
- Forward direction (graph → DSL): already done in Phase 4B as read-only DSL preview
- Reverse direction (DSL → graph): parse a DSL JSON → reconstruct graph nodes/edges in canvas

**Hard constraint:** A technical spike is required before any implementation commitment. Reverse compile is significantly harder than forward compile — the DSL is lossy relative to graph layout. The spike must answer: which DSL constructs are reversible and which are not.

**Do not create a task pack for this until the spike produces a written feasibility note.** A failed or scoped-down spike is a valid outcome.

---

## 7. Scope boundaries

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

## 8. Recommended execution order

```
1. Phase 3A completion          → docs/steps/23a-lab-phase3a-graph-persistence.md
2. Phase 6 execution            → docs/steps/23b-lab-phase6.md  (per docs/23 §Phase 6)
3. Block library Tier 2         → docs/steps/25-lab-block-tier2.md  (after Phase 6 accepted)
4. Multi-dataset binding        → docs/steps/26-lab-multi-dataset.md  (after Tier 2; schema decision required)
5. Parameter sweep              → docs/steps/27-lab-param-sweep.md  (after multi-dataset)
6. DSL ↔ graph bidirectional    → spike first; no task pack until feasibility confirmed
```

The task packs listed above do not exist yet. They must be created before any implementation begins. Each task pack must follow the format defined in `docs/22 §8`.

---

## 9. Stage acceptance discipline

All task packs derived from this roadmap must comply with the acceptance rule from `docs/22 §7`:

1. All required outputs delivered
2. Acceptance checks are verifiable by commands/steps
3. PR history shows no scope creep
4. Documentation updated in the same PR
5. Handover note prepared for the next task pack

This applies equally to Phase completion items (Phase 3A) and new expansion proposals (§6).
