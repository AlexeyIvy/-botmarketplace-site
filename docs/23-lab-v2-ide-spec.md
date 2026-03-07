# LAB CHANGE SPEC — Research Lab v2 IDE
**Project:** BotMarketplace
**Repository:** `AlexeyIvy/-botmarketplace-site`
**Status:** Reviewed & revised (expert pass)
**Author role:** Senior Software Engineer / Product Architect
**Reviewed by:** Expert engineering pass (March 2026)
**Scope:** Upgrade `/lab` from MVP JSON/AI editor into scalable research workspace for data acquisition, dataset management, visual strategy composition, validation, and backtest execution.
**Change type:** Additive, backward-compatible, phased implementation.

---

## REVIEW NOTES (expert pass)

> Этот блок фиксирует исправления и дополнения, внесённые при экспертной ревизии.
> После финализации документа блок можно убрать.

**Критические исправления:**
- Добавлены явные ссылки на Stage 19 (dataset layer уже реализован — нельзя игнорировать).
- Исправлены конфликты имён: `ConnectionProfile` → `ExchangeConnection`, `StrategyWorkspace` → `LabWorkspace` (во избежание коллизии с multi-tenant `Workspace`), `BacktestRun` → `BacktestResult` (уже существует в schema).
- Все API-пути приведены к проектному стандарту `/api/v1/`.
- Добавлена спецификация библиотеки canvas (React Flow v11+).
- Добавлена семантика выполнения графа (модель time-series нод).
- Добавлены acceptance criteria к каждой фазе (соответствие принятому в проекте формату).
- Добавлена стратегия фонового выполнения запросов (BullMQ, как в BotRun).
- Добавлены бюджеты производительности.
- Добавлена стратегия keyboard shortcuts.
- Добавлена versioning для библиотеки блоков.
- Усилена интеграция AI-функциональности.
- Добавлены явные зависимости между фазами и существующими Stage'ами.

---

## 1. Context and rationale

Current project documentation describes `/lab` primarily as:
- strategy list,
- JSON DSL editor,
- AI chat,
- backtest report.

This is acceptable for MVP, but insufficient for the intended product direction of **botmarketplace.store** as a serious trading research environment.

The target vision requires `/lab` to become a **research IDE**, not just a JSON editor.
The user must be able to:

1. connect an exchange profile (via existing `ExchangeConnection`),
2. select and retrieve market/account data,
3. build reusable datasets (via existing Stage 19 dataset layer),
4. compose strategies visually using typed building blocks,
5. validate strategy logic before execution,
6. run backtests on explicit datasets (via existing `BacktestResult` binding),
7. inspect logs, metrics, warnings, and reproducibility metadata.

This specification defines a phased, non-conflicting path from current MVP `/lab` to **Lab v2**.

---

## 2. Compatibility with current project

This change MUST remain compatible with the current documented architecture:

- Frontend MUST NOT access exchange APIs directly.
- Backend remains the sole holder of secrets and the only component that talks to exchange APIs.
- Strategy execution remains **declarative**, not arbitrary code execution.
- Existing DSL-based strategies remain supported.
- Visual strategy builder MUST compile into the same or next-version declarative strategy representation.
- **All API endpoints follow the project standard `/api/v1/` prefix.**

### 2.1 Dependency on existing stages

This spec builds on work already completed. The following stages MUST be treated as prerequisites:

| Prerequisite Stage | Key artifact used in Lab v2 |
|---|---|
| Stage 7 — Auth Hardening | Workspace isolation, auth middleware |
| Stage 8 — Exchange Connections | `ExchangeConnection` entity, secret encryption |
| Stage 10 — Strategy Authoring | DSL contract, schema validation, `StrategyVersion` |
| Stage 19 — Research Data Pipeline | `MarketCandle`, `MarketDataset`, `datasetHash`, `BacktestResult` |

> **CRITICAL:** Stage 19 already implemented the dataset backend layer — `MarketCandle`, `MarketDataset`, `datasetHash`, quality rules, and `BacktestResult` binding. Lab v2 Phases 2 and 5 MUST build on top of this, not reimplement it.

This means the visual builder is an **authoring layer**, not a runtime scripting engine.

---

## 3. High-level product goal

Transform `/lab` into a desktop-first research environment with four clearly separated concerns:

1. **Source & Access Context**
   Which exchange connection / environment / permissions are active (`ExchangeConnection`).

2. **Dataset Builder**
   What data is being requested, for which instrument(s), timeframe(s), and period — powered by the existing `POST /api/v1/lab/datasets` endpoint (Stage 19).

3. **Strategy Workspace**
   How logic is composed from typed blocks and compiled into declarative strategy representation.

4. **Run & Diagnostics**
   Validation, backtest status, metrics, warnings, logs, stale-state detection — powered by `BacktestResult` (Stage 19).

This separation is mandatory to prevent user confusion and architectural coupling.

---

## 4. Key design principles

### 4.1 Reproducibility
Every backtest or research result MUST be traceable to:
- exchange/source,
- `ExchangeConnection` id,
- `MarketDataset.id` + `MarketDataset.datasetHash` (Stage 19 fields),
- strategy version (`StrategyVersion.id`),
- execution settings (`feeBps`, `slippageBps`, `fillAt`, `engineVersion`).

> These fields already exist in `BacktestResult` after Stage 19. No schema duplication needed.

### 4.2 Inspectability
The user MUST be able to inspect:
- what exact data was loaded (via dataset metadata),
- whether gaps/duplicates exist (via `qualityJson` from Stage 19),
- what each block outputs (via Inspector panel with type preview),
- why validation failed (via ValidationIssue with JSON pointer),
- what changed between runs.

### 4.3 Modularity
Data acquisition, dataset definition, strategy graph, and backtest run MUST exist as separate logical objects.

### 4.4 Backward compatibility
The existing JSON/DSL editor MUST continue to work during migration.
The visual builder is additive first, not a replacement in Phase 1.

> Concretely: `DslEditor`, `AiChat`, `BacktestReport`, and `StrategyList` components must be preserved as subviews in the new shell until Phase 4 is accepted.

### 4.5 Safety
No arbitrary user code execution in Lab.
All strategy logic remains schema-validated and compiled into safe declarative forms.

### 4.6 Performance budget
The Lab must remain usable with:
- up to 200 nodes on the canvas at 60 fps during pan/zoom,
- Inspector update latency < 100ms on node select,
- Dataset preview render < 500ms for up to 10,000 rows (virtualized table),
- Page initial load < 3s (LCP) on standard connection.

---

## 5. Core problems in the previous concept

The earlier UI concept is directionally good, but not sufficiently mature from an engineering standpoint.

### 5.1 Data and strategy are too tightly mixed
Without explicit dataset objects, changing timeframe or period creates ambiguity:
- does it rebuild data?
- does it invalidate strategy outputs?
- are indicators stale?
- are previous results still valid?

### 5.2 No first-class dataset object
A market data query is not enough.
A dataset must be a persistent, inspectable entity.
> **Note:** Stage 19 resolves this at the backend level. The gap in Lab v2 is the UI layer.

### 5.3 No clear work modes
The screen needs explicit modes or panels for:
- Data,
- Build,
- Test.

### 5.4 Missing API/quality constraints
Real exchange integration requires:
- rate limit awareness (Stage 19: 10 req/min POST `/lab/datasets`),
- request status (async job via BullMQ),
- pagination handling,
- partial failure reporting,
- retry/backoff,
- cache visibility,
- gap detection (Stage 19: `gapsCount`, `maxGapMs` in `qualityJson`).

### 5.5 Missing typed graph model
A block canvas without a typed node/edge model will become brittle and hard to validate, diff, export, or compile.

---

## 6. Target `/lab` information architecture

## 6.1 Top Context Bar
Persistent bar at top of `/lab`.

Contains:
- workspace/research session name (`LabWorkspace.name`),
- active exchange connection (`ExchangeConnection.label + status`),
- environment (`demo`, future `real` behind feature flag),
- current dataset badge (`MarketDataset.id` short + `status`),
- current strategy badge,
- validation state (icon: ok / warning / error),
- run state (idle / running / done).

Purpose:
- always show the current context,
- reduce ambiguity,
- make stale-state visible.

---

## 6.2 Dataset Builder panel
Primary upper work area.

> **Implementation note:** This panel is the UI frontend to the existing Stage 19 backend endpoints (`POST/GET /api/v1/lab/datasets`). No new backend entities needed in Phase 2.

### Mandatory controls
- Exchange (select from user's `ExchangeConnection` list)
- Environment (`demo` only in MVP; `real` behind feature flag)
- Market type (`linear` first, future `inverse`, `spot`)
- Symbol / instrument selector (from `InstrumentCache`)
- Data type selector (`candles` first; `fundingHistory`, `openInterest` later)
- Timeframe selector (maps to `CandleInterval` enum from Stage 19: M1 | M5 | M15 | M30 | H1 | H4 | D1)
- Date range / period selector (max 365 days per Stage 19 limits)
- Timezone selector

### Recommended controls
- Price source (`last`, `mark`, `index`) where applicable
- Max candles warning (UI warns when approaching 100k limit from Stage 19)
- Missing data policy (`leave`, `mark`, `fill`, `reject`)
- Save as dataset toggle
- Dataset name + optional version note

### Status widgets
- Row count (from `MarketDataset.candleCount`)
- Coverage period (`coverageStart` / `coverageEnd`)
- Detected gaps (from `qualityJson.gapsCount`, `qualityJson.maxGapMs`)
- Duplicate attempts (from `qualityJson.dupeAttempts`)
- Last sync time (`MarketDataset.fetchedAt`)
- Fetch job progress (polling `GET /api/v1/lab/datasets/:id` every 2s while `status = fetching`)
- Warning banner (shown when `MarketDataset.status = PARTIAL`)
- Rate limit indicator (show when approaching 10 req/min POST limit)

### Dataset preview modes
- table view (virtualized, max 10k rows displayed)
- chart view (OHLCV candlestick using existing `lightweight-charts`)
- metadata/schema view (show full `qualityJson` + `datasetHash`)

---

## 6.3 Strategy Workspace (canvas)
Primary central composition area.

**Canvas library: React Flow v11+ (XYFlow)**

Rationale:
- Most mature React graph editor library (2024–2026).
- Built-in pan/zoom/minimap/multi-select.
- TypeScript-first with strong generic node/edge types.
- Supports custom node renderers (needed for Inspector-linked nodes).
- Active maintenance, large ecosystem.

Alternative considered: rete.js (more opinionated), custom (too costly). React Flow wins for speed/maintainability.

> **Architecture decision:** The canvas state is managed via a dedicated Zustand store (`useLabGraphStore`) separate from the global app store. This prevents graph state from polluting global state and enables undo/redo via Zustand middleware.

### Workspace regions
- left: block palette (categorized, searchable)
- center: canvas (React Flow)
- right: Inspector panel (see 6.4)
- optional bottom drawer: node output preview / logs

### Undo/redo architecture
Use Zustand with `temporal` middleware (`zundo`) to implement command-history undo/redo.

Keyboard shortcuts (mandatory for desktop-first):
| Shortcut | Action |
|---|---|
| `Cmd/Ctrl+Z` | Undo |
| `Cmd/Ctrl+Shift+Z` or `Cmd/Ctrl+Y` | Redo |
| `Delete` / `Backspace` | Remove selected node(s)/edge(s) |
| `Cmd/Ctrl+A` | Select all |
| `Cmd/Ctrl+D` | Duplicate selected node |
| `Cmd/Ctrl+G` | Group selected nodes |
| `Escape` | Deselect all |
| `Space` + drag | Pan canvas |
| `Cmd/Ctrl+Shift+F` | Search block palette |
| `Cmd/Ctrl+S` | Save graph draft |

### Graph evaluation semantics (node computation model)

Each node in the graph represents a **pure time-series transform**:
- Input ports accept typed series (e.g., `Series<OHLCV>`, `Series<number>`)
- Output ports emit typed series
- Evaluation is **pull-based**: backtest engine pulls from leaf output nodes
- Evaluation order: topological sort of DAG
- Cycles are rejected (except explicitly supported feedback loops, deferred)

This model ensures:
- deterministic execution,
- compilability to DSL,
- inspectability of per-node output.

### Block categories

#### Input blocks
- candles (`Series<OHLCV>` — bound to `MarketDataset`)
- trades (deferred, Phase 6)
- funding (deferred, Phase 6)
- open interest (deferred, Phase 6)
- positions history (private, Phase 6)
- executions history (private, Phase 6)

#### Transform blocks
- merge (combine two series)
- resample (change timeframe)
- filter (rows by condition)
- rolling window (N-bar window)
- normalize (z-score, min-max)
- session filter (time-of-day mask)
- shift / lag (N-bar offset)
- aggregate (sum, mean, max, min over period)

#### Indicator blocks
- SMA
- EMA
- RSI
- ATR
- MACD
- VWAP
- volatility (rolling std)
- volume metrics (OBV, VWMA)
- custom formula (from safe predefined operator set — no eval/Function())

#### Logic blocks
- compare (`>`, `<`, `==`, `>=`, `<=`)
- threshold (constant or ATR-multiple)
- cross (crossover/crossunder)
- if/else (route signal)
- AND / OR / NOT
- confirm N bars (signal must persist N bars)
- debounce / cooldown (min interval between signals)

#### Position / execution blocks
- enter long
- enter short
- close
- reduce
- reverse
- order model (Market/Limit)
- slippage model (maps to `slippageBps`)
- fee model (maps to `feeBps`)

#### Risk blocks (MANDATORY — graph validation fails without at least one)
- stop loss (fixed or ATR-multiple)
- take profit (fixed or R-multiple)
- trailing stop
- max drawdown stop
- daily loss stop (`dailyLossLimitUsd` from DSL)
- max concurrent positions
- max orders per minute (`maxOrdersPerMinute` from DSL)
- cooldown after loss (`cooldownSeconds` from DSL)

#### Debug / observability blocks
- log value (writes to Run diagnostics log)
- annotate event (marks point on equity curve)
- inspect series (show values in Inspector)
- explain branch (label for which logical path was taken)
- simulation marker (visual label on chart)

---

## 6.4 Inspector panel (mandatory)

When a node is selected, Inspector shows:
- node name/type + block library version,
- input ports (name + type + connected source or "unconnected"),
- output ports (name + type + shape preview),
- parameter form (inline edit with validation),
- inline validation errors (with JSON pointer),
- output shape/type preview (e.g., `Series<number>[1440]`),
- dependency chain summary,
- compatibility notes (e.g., "expects M15 series, connected M1 — mismatch"),
- stale status badge if upstream changed.

AI integration: Inspector includes a "Explain this block" button that sends block type + params to the AI endpoint (Stage 17 pattern) and shows explanation inline.

Without this panel the visual builder will not scale past simple demos.

---

## 6.5 Results / diagnostics drawer

Docked at bottom or on right. Resizable (min-height 120px, default 300px). Collapsible.

Tabs:
- **Validation** — list of `ValidationIssue` objects with node links
- **Backtest metrics** — PnL, winrate, drawdown, trades (from `BacktestResult`)
- **Trades** — per-trade table
- **Equity curve** — chart (lightweight-charts, same lib as Terminal)
- **Logs** — structured event log from backtest run
- **Warnings** — dataset quality warnings, stale-state warnings
- **Compare runs** — side-by-side metrics of two `BacktestResult` records (Phase 6)

Dataset snapshot block (pinned at top of Results drawer, after Stage 19):
- datasetId, datasetHash (first 8 chars), fetchedAt, candleCount
- gapsCount, maxGapMs, dupeAttempts, sanityIssuesCount
- feeBps, slippageBps, fillAt, engineVersion

---

## 7. Required domain objects

The frontend/backend contract evolves around these logical entities.

| Object | Status | Notes |
|---|---|---|
| `ExchangeConnection` | Exists (Stage 8) | Use as-is; replaces "ConnectionProfile" |
| `MarketDataset` | Exists (Stage 19) | Use as-is; replaces "Dataset" + "DatasetVersion" |
| `BacktestResult` | Exists (Stage 19) | Use as-is; replaces "BacktestRun" |
| `StrategyVersion` | Exists (Stage 10) | Source of truth for compiled strategy |
| `LabWorkspace` | New | Editable container for Lab session (see §17) |
| `StrategyGraph` | New | Versioned typed graph representation |
| `StrategyGraphVersion` | New | Immutable graph snapshot (complements `StrategyVersion`) |
| `ValidationIssue` | New (in-memory initially) | Per-node/per-edge validation result |

> **Naming convention note:** The name `StrategyWorkspace` from earlier drafts is replaced by `LabWorkspace` to avoid collision with the multi-tenant `Workspace` concept used throughout the project (auth, workspace isolation, `workspaceId` checks).

---

## 8. Dataset object — Lab v2 perspective

> **Stage 19 implemented the full backend.** Lab v2 only needs UI and endpoint wiring.

The `MarketDataset` entity (Stage 19) already covers:
- `id`, `workspaceId`, `exchange`, `symbol`, `interval`, `fromTsMs`, `toTsMs`
- `fetchedAt`, `datasetHash`, `candleCount`, `qualityJson`, `status`
- `engineVersion`

Statuses from Stage 19: `READY`, `PARTIAL`, `FAILED`
Add UI-side derived state: `fetching` (polling in progress), `draft` (not yet submitted)

### One missing field (propose addition)
- `name` (string, optional): user-friendly label for saved datasets
  Current schema has no display name → add to `MarketDataset` as nullable string in the next schema migration.

### Dataset creation flow in UI
1. User fills Dataset Builder form → UI validates locally (symbol exists, range ≤ 365d, candles ≤ 100k estimate)
2. UI calls `POST /api/v1/lab/datasets` (existing endpoint)
3. Backend returns `datasetId` + initial status
4. UI polls `GET /api/v1/lab/datasets/:id` every 2s while `status !== READY | PARTIAL | FAILED`
5. On completion, Dataset Builder shows preview and quality summary

---

## 9. Strategy graph object specification

The visual strategy builder uses a typed graph representation powered by React Flow.

### Node model (TypeScript)
```typescript
interface LabGraphNode {
  id: string;                          // React Flow node id
  type: string;                        // block type key (e.g., "indicator.ema")
  blockLibraryVersion: string;         // semver of block library (for migration)
  label: string;                       // user-editable label
  position: { x: number; y: number }; // canvas position
  params: Record<string, unknown>;     // block-specific parameters
  inputPorts: PortDefinition[];
  outputPorts: PortDefinition[];
  validationState: 'ok' | 'warning' | 'error' | 'stale';
  uiState: { collapsed?: boolean; selected?: boolean };
}

interface PortDefinition {
  id: string;
  name: string;
  dataType: PortDataType;              // see §9.1
  required: boolean;
}

type PortDataType =
  | 'Series<OHLCV>'
  | 'Series<number>'
  | 'Series<boolean>'
  | 'Signal'
  | 'RiskParams'
  | 'OrderModel';
```

### Edge model
```typescript
interface LabGraphEdge {
  id: string;
  sourceNodeId: string;
  sourcePortId: string;
  targetNodeId: string;
  targetPortId: string;
  dataType: PortDataType;  // must match source output + target input
}
```

### Graph model
```typescript
interface StrategyGraph {
  id: string;
  labWorkspaceId: string;
  name: string;
  dslVersionTarget: number;            // target DSL version for compiler
  blockLibraryVersion: string;         // semver of block lib at save time
  nodes: LabGraphNode[];
  edges: LabGraphEdge[];
  metadata: {
    createdAt: string;
    updatedAt: string;
    authorNote?: string;
  };
  validationSummary: {
    status: 'ok' | 'warning' | 'error';
    issueCount: number;
  };
}
```

### Mandatory validation rules
- Port data types must be compatible (enforced at connect time client-side).
- Cycles must be rejected (cycle detection on each edge add).
- Graph must have at least one Input block, one Risk block, and one Execution block to be valid.
- Graph must compile into declarative strategy representation (server-side validation in Phase 4).
- `blockLibraryVersion` must match current version; migration required if stale.

### Block library versioning
Block definitions are versioned with semver (`MAJOR.MINOR.PATCH`).

Rules:
- `PATCH`: bug fix, no schema change — transparent.
- `MINOR`: new optional parameter — graph loads without change.
- `MAJOR`: breaking parameter/port change — migration function required.

Each `StrategyGraphVersion` stores `blockLibraryVersion`.
On load, if block library has advanced MAJOR, the UI warns: "Graph was built with block library v1.x — migration available".
Migration functions are defined in `packages/shared/src/blockMigrations/`.

---

## 10. Relationship between graph and DSL

### Rule
Visual builder is not a separate execution engine.
It is an authoring interface that compiles into the project's declarative strategy model (`StrategyVersion`).

### Compilation contract
Graph compiler (`POST /api/v1/lab/graphs/:id/compile`) produces a `StrategyVersion.body` JSON that:
- conforms to `strategy.schema.json` (shared package, Stage 10),
- preserves all risk guards present in the graph,
- is validated by Ajv server-side before being saved as a `StrategyVersion`.

### Implementation approach
- Phase 1: visual builder works in parallel with existing DSL editor (both available as tabs).
- Phase 4: graph compiler produces canonical DSL JSON; generated DSL is shown as read-only preview.
- Phase 6: DSL editor and graph editor become interchangeable views where feasible (optional).

### Mandatory guarantee
The backend remains the source of truth for final strategy validation.

---

## 11. Exchange data scope for Lab

### 11.1 Public market data (Phase 1–5)
Primary focus — already supported by Stage 19:
- candles (`MarketCandle`) ✓
- tickers (proxied in Terminal, available for Lab)
- funding history (deferred to Phase 6)
- open interest (deferred to Phase 6)

### 11.2 Private account data (Phase 6)
Planned but not in early phases:
- orders history
- executions
- positions history

**Security rule:** Private data requests MUST go through the authenticated `ExchangeConnection` flow. Frontend never touches exchange API directly.

### 11.3 Visual distinction (mandatory)
Public and private data MUST be visually distinguished:
- public sources: blue indicator dot
- private sources: orange indicator dot + lock icon
- UI must not request private endpoints without confirmed `ExchangeConnection` selection

---

## 12. Stale-state and invalidation rules

### If dataset changes:
Mark `StrategyGraph.validationSummary` as `stale`.
Show badge: `"Dataset changed — recompute required"`.

### If upstream graph block changes:
Mark dependent nodes' `validationState` as `stale` until re-evaluated.
Debounced re-evaluation: 500ms after last edit.

### If ExchangeConnection changes (or is deleted):
Mark all `MarketDataset` objects linked to that connection as `potentially inaccessible`.
Show warning in Context Bar.

### If validation schema changes (DSL version bump):
Require server-side revalidation on next compile attempt.

### If block library MAJOR version changes:
Show global warning banner in Lab: "Strategy graph requires migration".

### If `MarketDataset.status = PARTIAL`:
Show persistent warning in Dataset Builder and Results drawer.

---

## 13. Validation model

### 13.1 Dataset validation (client-side, before POST)
- required parameters present (exchange, symbol, interval, fromTs, toTs),
- estimated candle count ≤ 100,000 (pre-check formula: `(toTs - fromTs) / intervalMs`),
- date range ≤ 365 days,
- symbol exists in `InstrumentCache`.

### 13.2 Quality validation (server-side, returned in `qualityJson`)
Already implemented in Stage 19:
- gaps detected (`gapsCount`, `maxGapMs`),
- duplicates detected (`dupeAttempts`),
- sanity issues (`sanityIssuesCount`, `sanityDetails`),
- status: `READY` | `PARTIAL` | `FAILED`.

### 13.3 Graph validation (client-side + server-side)
Client-side (real-time, debounced 500ms):
- disconnected required ports,
- invalid block parameters,
- port type mismatch,
- missing entry block,
- missing risk block,
- cycle detection.

Server-side (on save + compile):
- graph compiles to valid DSL,
- required risk guards present (`pauseOnError`, `maxOrdersPerMinute`, `maxOpenPositions`),
- strategy executable in current environment.

### 13.4 Strategy validation (server-side, on compile)
- compiled DSL passes Ajv validation against `strategy.schema.json`,
- required risk guards present,
- DSL version matches `dslVersionTarget`.

---

## 14. UI/UX requirements for Lab v2

### 14.1 Desktop-first
Maintain current project principle: desktop-first (1280px+), mobile-last.
Lab UI is not functional on mobile — show "Please use desktop" placeholder below 768px.

### 14.2 Dense professional layout
Lab is an IDE, not a marketing page.
Panels: resizable via drag handle. Min widths defined:
- Dataset panel: min 280px
- Canvas: min 400px
- Inspector: min 240px
- Results drawer: min 120px height

### 14.3 Strong visual hierarchy — semantic color mapping
| Semantic | Color |
|---|---|
| data / source | blue (`--color-data`) |
| transforms | violet (`--color-transform`) |
| indicators | cyan (`--color-indicator`) |
| signals / logic | green (`--color-signal`) |
| risk | orange (`--color-risk`) |
| execution | teal (`--color-execution`) |
| errors | red (`--color-error`) |
| stale | amber (`--color-stale`) |
| private data | orange dot + lock |

These map to design tokens in `packages/shared/src/tokens/lab.ts`.

### 14.4 Canvas usability (mandatory)
- zoom (mouse wheel, pinch)
- pan (space + drag, or middle mouse)
- minimap (React Flow built-in)
- node search (Cmd+Shift+F, filters palette and highlights on canvas)
- multi-select (shift+click or drag box)
- delete / duplicate node (see keyboard shortcuts §6.3)
- undo/redo (Zustand temporal middleware)
- auto-layout button (uses Dagre or ELK for automatic DAG layout)
- snap-to-grid (optional toggle)
- fit-to-view (Cmd+Shift+0)

### 14.5 Explainability
Each major object exposes human-readable summary:
- dataset: "BTCUSDT M15, 90 days, 8,640 candles, READY"
- strategy: "MA Crossover with RSI filter + 1% SL + 2% TP"
- validation issue: "Block 'EMA' output (Series<number>) connected to 'Compare' input (expects Series<OHLCV>) — type mismatch"

AI integration for explainability:
- "Explain validation error" — sends error + node context to AI (Stage 17 pattern)
- "Suggest fix" — AI proposes parameter change or alternative block
- "Generate graph from description" — AI sketch mode: user describes strategy in text, AI produces initial graph skeleton
- "Explain this block" — Inspector AI tooltip (always available)

---

## 15. Security and trust boundary rules

### 15.1 Frontend
Frontend MUST NOT:
- store API secrets (use only masked display of `ExchangeConnection`),
- call exchange private endpoints directly,
- bypass backend validation,
- execute any user-provided code (graph blocks are pure typed config, not scripts),
- render AI-generated markdown without sanitization (DOMPurify, as per project security policy).

### 15.2 Backend
Backend MUST:
- hold and use secrets securely (via existing Stage 8 encryption),
- enforce object-level access (`workspaceId` checks, as per Stage 7),
- validate all dataset requests (rate limits: 10 req/min POST, 60 req/min GET, per Stage 19),
- validate compiled strategy representations (Ajv + `strategy.schema.json`),
- enforce dataset access by `workspaceId` (user A cannot access user B's datasets).

### 15.3 AI features
AI may assist with:
- generating graph skeletons (skeleton only, no auto-execution),
- generating DSL,
- explaining validation issues,
- suggesting block parameters,
- summarizing strategy logic in plain language.

AI MUST NOT:
- receive `ExchangeConnection` secrets,
- place trades directly,
- bypass validation pipeline,
- have access to private account data unless explicitly scoped.

AI prompt construction MUST include redaction filter (no secrets, no PII) — consistent with existing security policy.

---

## 16. API contract changes

All endpoints use `/api/v1/` prefix (project standard).

### Dataset endpoints (Stage 19 — already implemented)
- `POST /api/v1/lab/datasets` — create dataset definition + fetch
- `GET /api/v1/lab/datasets` — list datasets for workspace
- `GET /api/v1/lab/datasets/:id` — get dataset + quality metadata
- `GET /api/v1/lab/datasets/:id/preview` — **New in Phase 2** — paginated candle rows for table/chart view

### Graph / strategy endpoints (New in Phase 3–4)
- `POST /api/v1/lab/graphs` — save LabWorkspace + StrategyGraph draft
- `GET /api/v1/lab/graphs/:id` — load graph
- `GET /api/v1/lab/graphs` — list graphs for workspace
- `POST /api/v1/lab/graphs/:id/validate` — server-side graph validation
- `POST /api/v1/lab/graphs/:id/compile` — compile graph to DSL → creates `StrategyVersion`
- `PATCH /api/v1/lab/graphs/:id` — save draft (auto-save friendly, patch semantics)

### Backtest endpoints (Stage 19 extended in Phase 5)
- `POST /api/v1/lab/backtest` — run backtest with `datasetId` + `strategyVersionId` + execution params
- `GET /api/v1/lab/backtest/:id` — get run status + report
- `GET /api/v1/lab/backtests` — list runs for workspace
- `GET /api/v1/lab/backtests/compare?a=:id&b=:id` — **New in Phase 6** — side-by-side metrics

### Rate limits for new endpoints
- `POST /api/v1/lab/graphs/:id/compile`: 20 req/min per workspace
- `POST /api/v1/lab/graphs/:id/validate`: 60 req/min per workspace
- `PATCH /api/v1/lab/graphs/:id`: 120 req/min per workspace (auto-save)

---

## 17. Data model changes (proposed additions)

Existing entities used as-is: `ExchangeConnection`, `MarketDataset`, `MarketCandle`, `BacktestResult`, `StrategyVersion`.

### New: `LabWorkspace`
Editable research session container.
- `id` (ulid, PK)
- `workspaceId` (FK → Workspace)
- `name` (string)
- `activeExchangeConnectionId` (FK → ExchangeConnection, nullable)
- `activeDatasetId` (FK → MarketDataset, nullable)
- `createdAt`, `updatedAt`

### New: `StrategyGraph`
Visual graph draft (editable).
- `id` (ulid, PK)
- `labWorkspaceId` (FK → LabWorkspace)
- `name` (string)
- `dslVersionTarget` (int)
- `blockLibraryVersion` (string, semver)
- `graphJson` (jsonb) — serialized `StrategyGraph` object
- `validationSummaryJson` (jsonb, nullable)
- `compiledStrategyVersionId` (FK → StrategyVersion, nullable)
- `createdAt`, `updatedAt`

### New: `StrategyGraphVersion` (Phase 4)
Immutable snapshot of graph at compile time.
- `id` (ulid, PK)
- `strategyGraphId` (FK → StrategyGraph)
- `version` (int, 1..N)
- `blockLibraryVersion` (string)
- `graphSnapshotJson` (jsonb)
- `strategyVersionId` (FK → StrategyVersion)
- `createdAt`

### Migration principle
All additions are additive (new tables, nullable FK columns).
No breaking changes to existing `Bot`, `BotRun`, `BotSpecVersion`, `BacktestResult` schemas.
New nullable fields on `MarketDataset`: `name` (string, nullable).

---

## 18. Non-goals for this change set

Explicitly OUT OF SCOPE for Lab v2 phases:

- arbitrary scripting execution (no `eval`, no user-defined functions),
- real trading from visual builder (demo only until explicit decision),
- multi-user collaboration on one graph (post-v2),
- portfolio-level optimizer (post-v2),
- advanced distributed backtest cluster (post-v2),
- mobile optimization (project principle: mobile-last),
- external non-exchange data lake (post-v2),
- cross-exchange order routing (post-v2),
- HFT simulation (< 1-minute latency modeling),
- partial fill modeling in backtest (simplified model: full fill at close).

---

## 19. Phased implementation plan

Each phase is independently completable, reviewable, and has explicit acceptance criteria.

---

## Phase 0 — Documentation alignment and contract freezing

### Goal
Align docs and freeze the architectural direction before implementation.

### Tasks
- Update `docs/12-ui-ux.md` Lab section with Lab v2 workspace model.
- Add this spec as `docs/23-lab-v2-ide-spec.md`.
- Update `docs/00-glossary.md`:
  - add: `LabWorkspace`, `StrategyGraph`, `StrategyGraphVersion`, `ValidationIssue`, `BlockLibraryVersion`
  - clarify: `Dataset` → points to `MarketDataset` (Stage 19)
  - clarify: `BacktestRun` → is `BacktestResult` in codebase
- Update `docs/07-data-model.md` with `LabWorkspace`, `StrategyGraph`, `StrategyGraphVersion`.
- Confirm non-breaking relation to existing DSL and Stage 19.
- Add React Flow v11+ as approved canvas library to `docs/17-tech-stack.md`.

### Acceptance checks
- [ ] No glossary term ambiguity between Lab v2 and existing docs
- [ ] `LabWorkspace` does not conflict with `Workspace` usage anywhere
- [ ] React Flow added to tech stack doc
- [ ] Stage 19 referenced in Phase 2 and Phase 5 with explicit "build on top of, not reimplement" note

---

## Phase 1 — Lab shell refactor (UI only, no backend dependency)

### Goal
Create the new `/lab` screen structure without breaking existing functionality.

### Tasks
**1A — Panel layout:**
- Replace current single-center layout with multi-panel shell:
  - top context bar (static, no data),
  - dataset panel (placeholder with loading state),
  - strategy workspace (placeholder canvas area),
  - inspector panel (placeholder),
  - diagnostics drawer (collapsed placeholder).
- Use CSS Grid / Flexbox with resize handles (use `react-resizable-panels` library).
- Preserve existing `StrategyList`, `DslEditor`, `AiChat`, `BacktestReport` as a "Classic mode" tab.

**1B — Lab state / store wiring:**
- Create `useLabGraphStore` (Zustand) with:
  - `activeConnectionId`, `activeDatasetId`, `activeGraphId`
  - `validationState`, `runState`
  - `nodes[]`, `edges[]` (empty, ready for Phase 3)
  - undo/redo history (zundo temporal middleware)
- Wire Context Bar to `useLabGraphStore`.
- Add routing for Lab modes: `/lab` (default), `/lab/data`, `/lab/build`, `/lab/test`.

### Acceptance checks
- [ ] `/lab` loads without error
- [ ] All 4 panels render with placeholders
- [ ] Classic mode tab shows existing DslEditor + AiChat + BacktestReport
- [ ] Context Bar renders (connection: "none selected", dataset: "none selected")
- [ ] Resize handles work (drag dataset panel height)
- [ ] `useLabGraphStore` exists and is connected to Context Bar
- [ ] No backend changes required

---

## Phase 2 — Dataset builder MVP (public market data only)

### Goal
Introduce dataset definition and preview workflow using the existing Stage 19 backend.

### Tasks
**2A — Dataset form UI:**
- Dataset Builder panel with all mandatory controls (§6.2).
- Client-side pre-validation (symbol from `InstrumentCache`, range ≤ 365d, estimated candles ≤ 100k).
- On submit: `POST /api/v1/lab/datasets` → receive `datasetId`.
- Poll `GET /api/v1/lab/datasets/:id` every 2s while `status = fetching` (reuse SWR polling pattern from BotRun status).

**2B — Preview table/chart:**
- Table view: paginated virtualized table (use `@tanstack/react-virtual`).
- Chart view: reuse `lightweight-charts` (same lib as Terminal) for OHLCV display.
- Wire to `GET /api/v1/lab/datasets/:id/preview` (new endpoint, paginated).

**2C — Quality summary:**
- Quality badge (READY / PARTIAL / FAILED with color coding).
- Expand to show: `gapsCount`, `maxGapMs`, `dupeAttempts`, `sanityIssuesCount`.
- Warning banner when `status = PARTIAL`.
- Update Context Bar dataset badge from `useLabGraphStore`.

### New backend (minimal):
- `GET /api/v1/lab/datasets/:id/preview?page=&pageSize=` — returns paginated rows from `MarketCandle` for the dataset's range.

### Acceptance checks
- [ ] User selects exchange + symbol + interval + range → submits
- [ ] Progress indicator shows while fetching
- [ ] On READY: table shows candle data, chart shows OHLCV
- [ ] Quality badge shows correct status
- [ ] PARTIAL triggers visible warning
- [ ] Range > 365d is blocked client-side with clear error
- [ ] Rate limit (10/min) error is shown gracefully
- [ ] Context Bar updates with dataset badge after selection

---

## Phase 3 — Typed graph editor MVP

### Goal
Introduce usable visual strategy composition using React Flow.

### Tasks
**3A — Graph canvas base:**
- React Flow canvas with pan/zoom/minimap.
- `useLabGraphStore` nodes/edges wired to React Flow state.
- Keyboard shortcuts: Delete, Cmd+Z, Cmd+Y, Escape, Cmd+A.
- Auto-save draft to backend (`PATCH /api/v1/lab/graphs/:id`) with 2s debounce.
- Auto-layout button (Dagre integration).

**3B — Node palette + Inspector:**
- Searchable block palette (left panel) with all block categories (§6.3).
- Phase 3 MVP blocks: `candles`, `SMA`, `EMA`, `RSI`, `compare`, `cross`, `enter_long`, `enter_short`, `stop_loss`, `take_profit`.
- Custom React Flow node renderer for each block type (color by category, port indicators).
- Inspector panel: parameter form, port info, validation errors for selected node.
- Port type compatibility enforced at connect time (client-side).

**3C — Graph validation rules:**
- Client-side graph validation (cycle detection, type mismatch, missing required blocks).
- Debounced re-validation (500ms after last edit).
- Validation issues shown in Inspector + Validation tab in drawer.
- "Missing risk block" rule enforced (graph is invalid without at least one risk block).

### Acceptance checks
- [ ] Canvas loads with empty graph
- [ ] Drag blocks from palette to canvas
- [ ] Connect two compatible ports — edge appears
- [ ] Connect incompatible ports — edge rejected with error
- [ ] Delete node removes connected edges
- [ ] Cmd+Z undoes last action
- [ ] Graph with: candles → EMA → cross → enter_long + stop_loss + take_profit passes validation
- [ ] Graph without risk block shows validation error
- [ ] Inspector shows correct params and port info for selected node
- [ ] Auto-save triggers after 2s of inactivity

---

## Phase 4 — Graph-to-DSL compiler

### Goal
Bridge visual builder to existing strategy engine.

### Tasks
**4A — Graph schema + compiler backend:**
- Define canonical mapping: graph block types → DSL fields (documented in `docs/10-strategy-dsl.md` addition).
- Implement `POST /api/v1/lab/graphs/:id/compile` endpoint:
  - validate graph server-side,
  - compile to `StrategyVersion.body` JSON,
  - validate against `strategy.schema.json` (Ajv),
  - create `StrategyVersion` + `StrategyGraphVersion` records.
- Return: `{ strategyVersionId, compiledDsl, validationIssues }`.

**4B — Compiler MVP UI:**
- "Compile & Save" button in Context Bar.
- Show generated DSL in read-only tab alongside canvas ("DSL Preview" tab).
- Show server-side validation errors mapped back to nodes in canvas.
- On success: Context Bar shows "Strategy v{n} saved" badge.

### Acceptance checks
- [ ] Simple crossover strategy graph compiles without error
- [ ] Compiled DSL validates against `strategy.schema.json`
- [ ] `StrategyVersion` record created in DB
- [ ] Server-side validation errors highlight correct nodes in canvas
- [ ] DSL Preview tab shows generated JSON
- [ ] Existing DSL-authored strategies unaffected

---

## Phase 5 — Backtest integration with explicit dataset binding

### Goal
Make backtests reproducible and inspectable using Stage 19 `BacktestResult`.

### Tasks
**5A — Run creation + report shell:**
- Backtest form in Results drawer: select `MarketDataset` + `StrategyVersion` + `feeBps` + `slippageBps`.
- `POST /api/v1/lab/backtest` with `datasetId` + `strategyVersionId` + execution params.
- Poll run status every 2s (existing pattern from BotRun).
- Results drawer Backtest metrics tab shows PnL, winrate, drawdown, trades on completion.

**5B — Metrics/trades/log tabs:**
- Trades tab: per-trade table with entry/exit/pnl/side.
- Equity curve tab: lightweight-charts line chart.
- Logs tab: structured event log from run.
- Dataset snapshot block (§6.5) shown at top of Results drawer.

### Acceptance checks
- [ ] User selects dataset + strategy version + execution params → run starts
- [ ] Progress indicator during run
- [ ] On completion: metrics tab shows PnL/winrate/drawdown/trades
- [ ] Trades tab shows per-trade data
- [ ] Equity curve renders
- [ ] Dataset snapshot shows datasetId/hash/feeBps/engineVersion
- [ ] Same inputs → same results on re-run (determinism check)
- [ ] `BacktestResult.datasetId` + `datasetHash` + `engineVersion` persisted

---

## Phase 6 — Private data support and advanced diagnostics

### Goal
Expand Lab toward richer research workflows.

### Tasks
- Add private historical data categories (`ordersHistory`, `executionsHistory`) where `ExchangeConnection` is active.
- Visual distinction: orange dot + lock icon for private source nodes in palette.
- Permission check: private blocks are greyed out without active `ExchangeConnection`.
- Stale-state detection across dataset/profile/graph changes.
- Compare runs view in Results drawer (`GET /api/v1/lab/backtests/compare`).
- Advanced diagnostics: annotate events on equity curve via `annotate_event` blocks.

### Acceptance checks
- [ ] Private data blocks disabled without ExchangeConnection
- [ ] Private data blocks enabled with valid ExchangeConnection
- [ ] Public/private distinction visually clear
- [ ] Stale state badges shown after dataset or connection change
- [ ] Compare runs shows two results side-by-side

---

## 20. Phase sizing guidance for Claude Code

Claude Code MUST receive work in chunks no larger than one lettered sub-phase.
Do not combine 3A + 3B + 3C into one task.

### Recommended execution slices
- Phase 0: docs + glossary update (1 task)
- Phase 1A: panel layout only (1 task)
- Phase 1B: Lab state/store wiring (1 task)
- Phase 2A: dataset form UI (1 task)
- Phase 2B: preview table/chart + `/preview` endpoint (1 task)
- Phase 2C: quality summary UI (1 task)
- Phase 3A: graph canvas base + keyboard shortcuts (1 task)
- Phase 3B: node palette + Inspector (1 task)
- Phase 3C: client-side validation rules (1 task)
- Phase 4A: compiler backend + graph schema (1 task)
- Phase 4B: compiler UI + DSL preview (1 task)
- Phase 5A: run creation + report shell (1 task)
- Phase 5B: metrics/trades/equity/log tabs (1 task)
- Phase 6: private data + stale-state + compare (2 tasks)

---

## 21. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Graph builder disconnected from runtime | HIGH | Builder compiles to canonical DSL; runtime uses `StrategyVersion`, not graph directly |
| Stage 19 reimplemented accidentally | HIGH | Phase 2 explicitly uses existing endpoints; no new Dataset tables |
| `LabWorkspace` confused with `Workspace` | MEDIUM | Consistent naming in code (`LabWorkspace` vs `Workspace`); separate DB table |
| React Flow performance with 200+ nodes | MEDIUM | Use `nodeTypes` memoization; virtualize palette; performance budget enforced in Phase 3 |
| Graph file size too large (jsonb) | MEDIUM | Max graph size guard: 500 nodes / 1000 edges; compress before store |
| Block library version divergence | MEDIUM | `blockLibraryVersion` field + migration functions; UI warns on stale graph |
| Dataset object scope too large too early | LOW | Phase 2 is UI-only on top of Stage 19 backend; no new DB entities in Phase 2 |
| UI complexity overwhelms users | LOW | Clear `Data / Build / Test` modes; contextual explanations; "Classic mode" preserved |
| Exchange-specific complexity in frontend | LOW | Frontend uses normalized backend contracts; exchange quirks handled in backend |

---

## 22. Required updates to existing docs

| Doc | What to update |
|---|---|
| `docs/12-ui-ux.md` | Replace Lab layout section with Lab v2 four-panel model |
| `docs/02-requirements-functional.md` | Add: dataset builder, graph builder, reproducible backtests (Phase 5) |
| `docs/04-architecture.md` | Add: LabWorkspace, StrategyGraph, graph compiler service |
| `docs/07-data-model.md` | Add: LabWorkspace, StrategyGraph, StrategyGraphVersion; reference Stage 19 entities |
| `docs/10-strategy-dsl.md` | Add: visual graph compiles into declarative DSL; block-to-DSL mapping table |
| `docs/17-tech-stack.md` | Add: React Flow v11+ (canvas), `react-resizable-panels`, `@tanstack/react-virtual`, `zundo` |
| `docs/00-glossary.md` | Add: LabWorkspace, StrategyGraph, ValidationIssue, BlockLibraryVersion, CandleInterval |

---

## 23. Acceptance criteria for Lab v2 rollout

Lab v2 can be considered successfully introduced when:

1. `/lab` clearly separates source context, dataset building, strategy composition, and results (Phase 1).
2. User can create a dataset definition and preview it without backend changes beyond Stage 19 (Phase 2).
3. User can create a visual strategy graph with client-side validation (Phase 3).
4. Graph can compile into a valid declarative `StrategyVersion` (Phase 4).
5. Backtest can be run against explicit `MarketDataset` + `StrategyVersion` pair with reproducible results (Phase 5).
6. UI surfaces stale-state and validation issues clearly (all phases).
7. Existing DSL workflow is not broken during migration (all phases).
8. All keyboard shortcuts work (Phase 3).
9. Performance budget met: 200 nodes at 60fps, inspector < 100ms (Phase 3).
10. Block library versioning is in place (Phase 3).

---

## 24. Final engineering recommendation

Do NOT rebuild Lab as one giant feature.
Implement it as an additive phased IDE migration.

Priority order MUST be:
1. shell structure (Phase 1),
2. dataset definition UI on existing backend (Phase 2),
3. graph model + canvas (Phase 3),
4. compiler (Phase 4),
5. reproducible runs (Phase 5).

**Critical implementation guidance:**
- Phase 2 is purely UI — no backend entities needed. Stage 19 already built the data layer.
- Phase 3 requires a canvas library decision (React Flow v11+) before any code is written.
- Phase 4 requires a formal block-to-DSL mapping table defined in `docs/10-strategy-dsl.md` before the compiler is coded.
- Phase 5 extends `BacktestResult` (which already has `datasetId`/`datasetHash`/`engineVersion` from Stage 19) — binding is mostly UI work.

This sequence minimizes rework, keeps the system compatible with the current architecture, and creates the strongest foundation for future AI-assisted strategy research inside botmarketplace.store.
