# LAB CHANGE SPEC — Research Lab v2 IDE
**Project:** BotMarketplace
**Repository:** `AlexeyIvy/-botmarketplace-site`
**Status:** Finalized — implementation-ready (Revision 2, March 2026)
**Author role:** Senior Software Engineer / Product Architect
**Reviewed by:** Expert engineering pass (March 2026)
**Scope:** Upgrade `/lab` from MVP JSON/AI editor into scalable research workspace for data acquisition, dataset management, visual strategy composition, validation, and backtest execution.
**Change type:** Additive, backward-compatible, phased implementation.

---

## CHANGE LOG

> Этот блок фиксирует историю ревизий документа.

**Revision 2 — March 2026 (implementation-readiness pass):**
- `LabWorkspace` явно разделён на два состояния: logical (Phase 1, localStorage/Zustand) и persisted DB entity (Phase 3+). Нет риска преждевременной схемы.
- Classic mode усилен: теперь явно mandatory until Phase 4 acceptance, с запретом удаления в Phase 1–3.
- Phase 0 обозначен как обязательный отдельный PR. Добавлена рекомендованная PR-последовательность.
- Phase 2B получил опциональный сплит на 2B1 (endpoint + table) и 2B2 (chart), если объём задачи слишком большой.
- Performance budgets скоупированы на Phase 3+ — больше не блокируют Phase 0/1.
- Уточнена language logical vs persisted объектов по всему документу.
- Статус документа: **FINALIZED — готов к реализации**.

**Revision 1 — March 2026 (initial expert pass):**
- Добавлены явные ссылки на Stage 19 (dataset layer уже реализован).
- Исправлены конфликты имён: `ConnectionProfile` → `ExchangeConnection`, `StrategyWorkspace` → `LabWorkspace`, `BacktestRun` → `BacktestResult`.
- Все API-пути приведены к проектному стандарту `/api/v1/`.
- Добавлена спецификация canvas library (React Flow v11+), graph evaluation semantics, keyboard shortcuts, block library versioning, AI integration, phase dependencies.

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

**Classic mode is MANDATORY until Phase 4 acceptance.**

The existing JSON/DSL editor MUST continue to work during migration.
The visual builder is additive first, not a replacement.

Classic mode rules:
- `DslEditor`, `AiChat`, `BacktestReport`, and `StrategyList` MUST be preserved as a "Classic mode" tab in the new shell.
- Classic mode MUST NOT be removed or disabled during Phases 1, 2, or 3.
- Classic mode MAY be deprecated only after Phase 4 acceptance criteria are fully met — specifically: graph compiles to valid `StrategyVersion` and the compiled DSL has been proven stable in at least one real backtest run.
- Until Phase 4 acceptance, the DSL-based workflow is the **operational fallback** for all users.
- Any implementer that removes Classic mode before Phase 4 acceptance has violated this spec.

> Rationale: Users who already have saved DSL strategies must not lose access to their strategies mid-migration. The graph editor is being added, not substituted.

### 4.5 Safety
No arbitrary user code execution in Lab.
All strategy logic remains schema-validated and compiled into safe declarative forms.

### 4.6 Performance budget

> **Scope:** These budgets are acceptance criteria for **Phase 3 (graph editor) and later** phases only.
> They are NOT blockers for Phase 0 (docs) or Phase 1 (shell layout).
> Phase 1 shell has no canvas and no dataset preview — performance criteria do not apply.

Target budgets (Phase 3+):
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
- request status visibility (Stage 19 POST is synchronous with a 30s transaction timeout; the UI must show a loading state during the POST and handle slow responses gracefully),
- pagination handling,
- partial failure reporting,
- retry/backoff,
- cache visibility,
- gap detection (Stage 19: `gapsCount`, `maxGapMs` in `qualityJson`).

> **Note on Stage 19 execution model:** `POST /api/v1/lab/datasets` is synchronous — it fetches, hashes, and saves in a single Prisma transaction (max ~30s). It is NOT a BullMQ-queued async job. The "fetching" status is a UI-side loading state only, not a DB status value. DB statuses are `READY | PARTIAL | FAILED` (Stage 19 spec §7.2).

### 5.5 Missing typed graph model
A block canvas without a typed node/edge model will become brittle and hard to validate, diff, export, or compile.

---

## 6. Target `/lab` information architecture

## 6.1 Top Context Bar
Persistent bar at top of `/lab`.

Contains:
- session name (Phase 1: hardcoded "Research Lab" or editable string in `useLabGraphStore`; Phase 3+: `LabWorkspace.name` from DB),
- active exchange connection (`ExchangeConnection.label + status`, or "— not selected"),
- environment (`demo`, future `real` behind feature flag),
- current dataset badge (`MarketDataset.id` short + `status`, or "— not selected"),
- current strategy badge (Phase 3+),
- validation state (icon: ok / warning / error; idle in Phase 1),
- run state (idle / running / done; idle in Phase 1).

All values read from `useLabGraphStore`. Context Bar is fully implemented in Phase 1B.

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
- Request progress (spinner shown while POST is in-flight; Stage 19 POST is synchronous, no DB "fetching" status exists)
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

### 6.3.1 Block connection UX (visual interaction model)

> **Phase:** Phase 3 (graph editor implementation).
> This section defines how users visually understand, create, modify, and remove connections between blocks. It is a required design spec for the React Flow custom node/edge implementation.

The connection experience must feel like a **professional strategy IDE**, not a low-code toy. Users building trading strategies need to immediately understand what data flows where, see incompatibility before committing, and maintain clarity as graph density increases.

---

#### Connection layout (port placement)

Every block node renders two distinct sides:

- **Input ports — left side of the node:** aligned vertically in the left column of the node body. Each port shows its label to the right of the handle, inside the node.
- **Output ports — right side of the node:** aligned vertically in the right column of the node body. Each port shows its label to the left of the handle, inside the node.

Port labels:
- Short, lowercase, descriptive: `price`, `signal`, `length`, `risk`, `candles out`.
- Font: same as node body text, 10px, muted foreground color.
- Always visible (not hover-only) so the graph is readable without interaction.

Hit area:
- Visible handle circle: **10px diameter**.
- Invisible click/drag hit area: **24px × 24px** centered on the handle. This prevents misses when clicking quickly on edge-mounted handles.

> **React Flow implementation note:** Use React Flow's `<Handle>` component with custom `className` and explicit `style` overrides. The `<Handle>` renders an invisible hit area by default — do not suppress it.

---

#### Port appearance

Each handle is a **solid circle** whose fill and outline color is determined by its `PortDataType` (see §9.1 for full color table).

Port state rendering rules:

| State | Visual |
|---|---|
| Unconnected, required | Outline ring (2px) in type color; center hollow; subtle pulse animation (2s cycle, scale 1.0→1.1→1.0) to draw attention |
| Unconnected, optional | Outline ring (1px) in type color at 50% opacity; no animation |
| Connected | Solid fill in type color; no animation; small inner dot to reinforce "occupied" |
| Hovered (during drag-to-connect) | Ring scale increases (CSS `transform: scale(1.4)`); glow shadow matches type color |
| Incompatible target (during drag) | Ring turns red (`#D44C4C`); scale decreases (0.85); type color suppressed |

Required port missing connection (validation error state):
- Outline ring color switches to error red `#D44C4C`.
- Warning icon (`⚠`) appears beside the port label.
- This state persists until connection is made or graph is saved as draft.

---

#### Edge appearance

Edges are **cubic bezier curves** drawn by React Flow's default connection renderer (or `SmoothStepEdge` if bezier causes excessive overlap in dense graphs — configurable per graph).

Visual specification:

| Property | Default | Hover | Selected | Stale | Invalid |
|---|---|---|---|---|---|
| Stroke width | 2px | 3px | 3px | 2px | 2px |
| Stroke color | Type color (see §9.1) at 80% opacity | Type color at 100% | Type color at 100% | Type color at 35% opacity | `#D44C4C` |
| Stroke style | Solid | Solid | Solid | Dashed (6px dash, 3px gap) | Dashed (4px dash, 2px gap) |
| Box shadow / glow | None | None | Soft glow (4px blur, type color at 40%) | None | None |
| Label (optional) | Hidden | Shows type abbreviation (e.g., `ℝ`, `𝔹`, `OHLCV`) | Shows full type name | Shows `stale` badge | Shows `type mismatch` |

> **Design principle:** Avoid thick, neon, or busy wires by default. The canvas must remain readable at medium-to-high density. Emphasis should come only from hover, selection, or error state — not from the default resting appearance.

> **React Flow implementation note:** Use `edgeTypes` prop with a custom edge renderer component. The custom edge reads `data.dataType` from the edge object and `data.isStale`, `data.isInvalid` flags to apply the correct style class.

---

#### Connection interaction (drag-to-connect)

**Standard flow:**
1. User hovers over an **output** handle (right side of node) → handle scales up to signal draggability.
2. User drags from output handle → a **provisional connection line** appears (see below).
3. Cursor moves over the canvas → compatible input handles highlight; incompatible handles dim.
4. User drops onto a compatible **input** handle → edge is created, stored in graph state.
5. Undo records the edge addition as a single history entry.

**Provisional connection line (in-flight state):**
- Bezier curve from source handle to cursor.
- Stroke: 2px, neutral gray (`#8090A0`), 60% opacity, dashed (4px dash / 4px gap).
- No type color until connection is completed — type color is applied only when a valid target handle is hovered (instant color switch to matching type color).
- The cursor shows a `crosshair` pointer while dragging.

**Reversed drag (input-to-output):**
- React Flow supports connection initiation from either side (`connectionMode: ConnectionMode.Loose`).
- Dragging from an input handle initiates a connection in the same way; the direction is resolved on drop.
- The connection is still stored with canonical source = output, target = input direction.

> **React Flow implementation note:** Implement using `onConnectStart`, `onConnect`, `onConnectEnd` callbacks. Use `isValidConnection` prop on the `<ReactFlow>` component to enforce type compatibility and cycle detection on every potential drop target.

---

#### Compatible target highlighting during drag

When a connection drag is in progress, all handles on the canvas are re-evaluated as potential targets:

**Compatible input handle** (type matches, no cycle would be created):
- Pulse ring animation activates (scale 1.0→1.2→1.0, 0.8s cycle).
- Ring color matches source output type color at 100%.
- Surrounding node body gets a subtle left-border highlight (3px, type color at 60%).

**Incompatible input handle** (type mismatch or would create a cycle):
- Handle opacity → 25%.
- Handle ring → red (`#D44C4C`).
- Surrounding node opacity → 60%.
- If user hovers the incompatible handle, a small tooltip appears near cursor (see §6.3.1 Validation feedback).

**Unrelated handles (not input or already-connected inputs):**
- No change in appearance; reduces visual noise.

**Canvas nodes with no compatible input at all:**
- Node opacity → 60% to recede into background.

> **Implementation:** Use a React context value (e.g., `dragSourcePortType`) that is set on `onConnectStart` and cleared on `onConnectEnd`. Each handle reads this value to compute its current visual state class. This avoids prop-drilling and re-renders being triggered by a single cursor position.

---

#### Validation feedback at connection time

Feedback must be **immediate and visible**. Silent failure (edge simply not created, no explanation) is prohibited.

| Rejection reason | Feedback |
|---|---|
| Type mismatch | Inline tooltip near cursor: `"Type mismatch: Series⟨number⟩ → Signal not compatible"`. Handle ring turns red. No edge is created. |
| Would create a cycle | Toast notification (top-right, 3s, dismissable): `"Cannot connect: this would create a cycle in the graph"`. |
| Connecting output-to-output | Tooltip: `"Connect an output to an input port"`. No edge created. |
| Connecting input-to-input | Tooltip: `"Connect from an output port"`. No edge created. |

Tooltip style:
- Small rounded chip (not full modal).
- Background: dark overlay (`rgba(20,24,30,0.92)`), white text, 12px font.
- Appears within 150ms of hover on incompatible target.
- Disappears when cursor moves away.

> `isValidConnection` must return `false` for all rejection cases. The tooltip is rendered by `onConnectEnd` if `isValidConnection` returned false for the last hovered target.

---

#### Port cardinality rules

| Port type | Cardinality | Enforcement |
|---|---|---|
| Input port | Accepts **exactly one** incoming edge | If a second edge is dropped onto an occupied input, the existing edge is removed and the new edge takes its place |
| Output port | May fan out to **any number of targets** | No limit; multiple edges from one output are valid |

**Replace-on-drop behavior for occupied inputs:**
1. User drags a new edge and drops onto an input port that already has an incoming edge.
2. The old edge animates out (fade + shrink, 150ms).
3. The new edge animates in (grow + fade in, 150ms).
4. Both operations are recorded as a single undo history entry (remove old + add new = 1 undo step).
5. No confirmation dialog is shown — the replacement is immediate and undoable.

> Rationale: Confirmation dialogs interrupt flow and are not expected in professional graph editors. Undo (`Cmd+Z`) is the correct recovery path. This matches the UX convention in tools like Figma, Blender node editor, and TouchDesigner.

---

#### Hover and selection behavior

**Hovering an edge:**
- Edge stroke width increases to 3px; opacity to 100%.
- Both connected handles (source and target) scale up and glow.
- A floating label appears near the midpoint of the edge showing: source node name → target node name + port name + type abbreviation (e.g., `EMA → Compare [price | ℝ]`).
- Connected source and target node cards receive a subtle highlight border (1px, type color at 40%).

**Selecting an edge (click):**
- Edge receives selection highlight (glow shadow).
- Inspector panel shows: source port, target port, data type, edge id, stale/invalid flag.
- `Delete` / `Backspace` removes the selected edge (single undo entry).

**Hovering a node:**
- All edges connected to the node highlight (same as edge hover state).
- Unconnected handles pulse briefly to remind user of available connections.

**Selecting a node:**
- Connected edges highlight.
- Inspector opens immediately (no click delay needed).
- If multiple nodes selected: Inspector shows summary (count, types, validation status).

---

#### Disconnect behavior

| Action | Result |
|---|---|
| Select edge → `Delete` / `Backspace` | Edge removed; both port handles return to unconnected state |
| Right-click edge → "Remove connection" | Same as above (context menu alternative) |
| Select node → `Delete` | Node removed; all connected edges removed automatically; affected downstream nodes marked `stale` |
| Drag edge endpoint off handle (React Flow "detach") | Edge removed (if `edgesReconnectable` is enabled in Phase 3B) |

On any edge removal:
- Downstream nodes that depended on the disconnected port are immediately marked `validationState: 'stale'`.
- Required input ports left unconnected switch to their error visual state.
- The diagnostics drawer updates its issue list within one render cycle.

---

#### Stale and invalid downstream propagation

When a node's output changes — or a node is removed — downstream state must be visually invalidated immediately (before any recomputation):

**Stale propagation rules (client-side, Phase 3):**
1. When an edge is removed, all nodes reachable downstream via remaining edges from that source are marked `validationState: 'stale'`.
2. When a node's parameter changes, that node and all downstream nodes are marked `stale`.
3. When a block library version mismatch is detected on load, affected nodes are marked `stale` with tooltip: `"Block updated — parameters may have changed"`.

**Visual representation of stale state:**
- Node card: muted header color + `stale` chip badge (amber, uppercase, 10px).
- Connected edges to/from stale node: dashed stroke (see edge table above).
- Inspector shows stale badge and suggests "Re-validate graph" action.

**Required input port disconnected after node removal:**
- Port renders in its required-but-unconnected error state immediately.
- The node with the disconnected required input shows `validationState: 'error'`.
- Diagnostics drawer shows: `"[NodeName] input '[portName]' is required but has no source"`.

---

#### Usability enhancements

These are implementation details that separate a professional experience from a functional one:

| Enhancement | Specification |
|---|---|
| **Connection preview tooltip** | When user hovers an output handle (before starting drag), show a small chip near the handle with the output type (e.g., `→ Series⟨number⟩`). Disappears on drag start. Appears after 400ms hover delay. |
| **Auto-pan at viewport edge** | During drag-to-connect, if cursor approaches within 60px of viewport edge, canvas pans in that direction. Pan speed scales with proximity to edge (min: 2px/frame, max: 12px/frame). React Flow has partial built-in support via `autoPanOnConnect`. |
| **Success micro-animation** | On successful connection: the new edge briefly animates in (300ms ease-out stroke-dashoffset travel from source to target). Subtle, professional — avoids gamification. |
| **Reason hint on incompatible hover** | When cursor hovers on a dimmed incompatible handle for >150ms, tooltip shows the concrete mismatch reason (not just "incompatible"). Implementation: computed in `isValidConnection` and stored in a ref for the tooltip renderer. |
| **Snap-to-grid** | Optional grid snapping for node positions (toggle, default off). Dragging nodes snaps to 8px grid when enabled. Does not affect edge routing. |
| **Minimap edge color** | Minimap (React Flow built-in) should show edge lines in a neutral mid-gray; do not render per-type colors in minimap (too dense at small scale). |

---

#### Visual design recommendations (dark theme)

The canvas uses the project's dark theme (trading convention, per `docs/12-ui-ux.md`).

Design principles for the connection system:
- Wire colors must be **distinguishable** but **not dominant**. They are guides, not decorations.
- Default state is quiet; activity and error states use intensity and saturation.
- Avoid glowing neon wires at rest. Save glow effects for hover and selection only.
- The canvas background should be a near-black (`#0F1217`) with a subtle dot-grid or fine line-grid (`#1E2530` at 40% opacity). Grid helps spatial orientation without adding noise.
- Node card headers use **category color** (muted, desaturated) as a left border accent, not as full background fill. This keeps nodes readable at all zoom levels.

Port type color palette (dark theme):

| Type | Color | Hex | Use |
|---|---|---|---|
| `Series<OHLCV>` | Steel blue | `#5B9BD5` | Raw market data; data source blocks |
| `Series<number>` | Amber | `#D4A44C` | Numeric indicator output; most common |
| `Series<boolean>` | Violet | `#9580C8` | Boolean condition series |
| `Signal` | Emerald | `#52A97C` | Entry/exit trigger (most important output type) |
| `RiskParams` | Coral | `#D46060` | Risk configuration; draws attention by design |
| `OrderModel` | Slate | `#6A849E` | Order execution config; structural, de-emphasized |

> These colors are chosen to be distinguishable on dark backgrounds without relying solely on hue (variance in luminance + hue reduces colorblind impact). A future accessibility pass should verify WCAG AA contrast against the canvas background for all six colors.

---

#### Accessibility and future keyboard support

Phase 3 MVP:
- All `<Handle>` components must have `aria-label` set to the full port description:
  `aria-label="EMA output: Series<number>"` / `aria-label="Compare input 'price': Series<number>, required"`.
- All edges in the React Flow graph receive `aria-label`:
  `aria-label="Edge from EMA output to Compare price input, type Series<number>"`.
- These labels enable screen reader traversal of the graph structure.

Future (Phase 6, not required in Phase 3):
- Tab navigation through nodes, then handles within a node.
- `Enter` on a source handle begins keyboard-driven connection mode.
- Arrow keys select next compatible handle.
- `Enter` again confirms connection.
- `Escape` cancels connection.

> **Non-blocking requirement:** The Phase 3 implementation must not make keyboard connection support impossible to add later. Do not use event capture patterns that would prevent Tab focus on handles.

---

#### Acceptance additions for Phase 3 (connection UX)

These criteria must pass before Phase 3 is considered complete:

- [ ] Dragging from an output handle produces a visible provisional line
- [ ] Compatible input handles highlight (ring pulse) during drag
- [ ] Incompatible input handles dim (opacity 25%) + turn red during drag
- [ ] Dropping on incompatible target: shows tooltip with mismatch reason, no edge created
- [ ] Creating a cycle: toast notification shown, no edge created
- [ ] Dropping on occupied input: old edge removed (animated), new edge connected, both recorded as one undo step
- [ ] `Cmd+Z` correctly undoes the last connection action
- [ ] Selecting an edge: glow + Inspector updates with edge details
- [ ] `Delete` on selected edge: edge removed, downstream nodes go stale
- [ ] Deleting a node: all connected edges removed, downstream ports show required-missing error state
- [ ] Required unconnected ports render in error state (red ring + ⚠ label)
- [ ] Stale nodes show amber `stale` badge in node card header
- [ ] Edge labels appear on hover (source → target + type)
- [ ] Edges render in correct type color (verify all 6 types)
- [ ] Success animation plays on new connection (300ms, not jarring)
- [ ] Auto-pan activates when dragging near viewport edge
- [ ] `aria-label` present on all handles and edges (verify with browser accessibility inspector)
- [ ] Performance: 200 nodes, 300 edges → 60fps during pan/zoom (Chrome DevTools Performance tab)

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

### Object status legend
- **Exists** — already in codebase, use as-is, no new schema work needed.
- **Logical only** — concept used in UI, no DB entity yet; lifecycle is client-side state (localStorage / Zustand store).
- **New (Phase N)** — DB entity required; persistence begins at the stated phase.
- **In-memory** — lives only in frontend memory during session; never persisted to DB.

| Object | Status | Notes |
|---|---|---|
| `ExchangeConnection` | **Exists** (Stage 8) | Use as-is; replaces "ConnectionProfile" |
| `MarketDataset` | **Exists** (Stage 19) | Use as-is; replaces "Dataset" + "DatasetVersion" |
| `BacktestResult` | **Exists** (Stage 19) | Use as-is; replaces "BacktestRun" |
| `StrategyVersion` | **Exists** (Stage 10) | Source of truth for compiled strategy |
| `LabWorkspace` | **Logical only → New (Phase 3)** | Phase 1–2: client-side session state only (localStorage + Zustand). Phase 3: becomes persisted DB entity when graph storage is needed. See §17 for schema. |
| `StrategyGraph` | **New (Phase 3)** | Requires DB when graph persistence begins in Phase 3 |
| `StrategyGraphVersion` | **New (Phase 4)** | Immutable snapshot created on compile |
| `ValidationIssue` | **In-memory** | Per-node/edge validation result; never persisted; reconstructed on each graph edit |

> **CRITICAL — LabWorkspace persistence timing:**
> In Phase 1, `LabWorkspace` does NOT require any DB schema change.
> Phase 1 only needs: `useLabGraphStore` (Zustand) with `activeConnectionId`, `activeDatasetId`, `activeGraphId` — stored in component state and optionally persisted to localStorage.
> The `LabWorkspace` DB table is introduced in Phase 3 when graph drafts must survive page reload.
> Implementers MUST NOT create a `LabWorkspace` DB migration as part of Phase 0 or Phase 1.

> **Naming convention note:** `LabWorkspace` is distinct from the multi-tenant `Workspace` entity (Stage 7 auth, `workspaceId` isolation). They are separate concepts and separate DB tables.

---

## 8. Dataset object — Lab v2 perspective

> **Stage 19 implemented the full backend.** Lab v2 only needs UI and endpoint wiring.

The `MarketDataset` entity (Stage 19) already covers:
- `id`, `workspaceId`, `exchange`, `symbol`, `interval`, `fromTsMs`, `toTsMs`
- `fetchedAt`, `datasetHash`, `candleCount`, `qualityJson`, `status`
- `engineVersion`

Statuses from Stage 19: `READY`, `PARTIAL`, `FAILED` (these are the only DB status values).

UI-side derived states (not persisted, live only in `useLabGraphStore`):
- `draft` — form filled but not yet submitted
- `submitting` — POST in flight (show spinner/progress)
- `loading_preview` — fetching preview rows after READY

### One missing field (propose addition)
- `name` (string, optional): user-friendly label for saved datasets.
  Current `MarketDataset` schema has no display name → add as nullable string in Phase 2 migration.

### Dataset creation flow in UI

> **Stage 19 POST is synchronous** — it runs the full fetch + hash + quality inside a single Prisma transaction (up to ~30s).
> There is no async BullMQ queue for dataset creation. The POST returns the final `READY | PARTIAL | FAILED` status.

UI flow:
1. User fills Dataset Builder form → UI validates locally (symbol exists in `InstrumentCache`, range ≤ 365d, estimated candles ≤ 100k)
2. UI sets local state → `submitting`, shows progress indicator
3. UI calls `POST /api/v1/lab/datasets` — blocks until complete (max ~30s)
4. Backend returns `{ datasetId, datasetHash, status, qualityJson, candleCount }` — final status
5. UI updates `useLabGraphStore.activeDatasetId` and Context Bar badge
6. On `READY`: Dataset Builder shows preview and quality summary
7. On `PARTIAL`: show persistent warning banner + still show preview
8. On `FAILED`: show error with `qualityJson.sanityDetails`

Optional enhancement (not required for Phase 2A): if user navigates away during a long POST, re-enter Dataset Builder, and the dataset is found via `GET /api/v1/lab/datasets` with a matching params — UI may display the already-computed result without re-fetching.

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

### 9.1 Port data type semantics and color system

The six `PortDataType` values correspond to specific semantic roles in the strategy execution model.
Each type has an assigned color used across all visual surfaces (handles, edges, Inspector type badges).

| Type | Semantic role | Color name | Hex | Compatible with |
|---|---|---|---|---|
| `Series<OHLCV>` | Raw market candle stream | Steel blue | `#5B9BD5` | Input: resample, transform, indicator blocks |
| `Series<number>` | Numeric indicator output | Amber | `#D4A44C` | Input: compare, threshold, arithmetic, signal blocks |
| `Series<boolean>` | Boolean condition series | Violet | `#9580C8` | Input: AND/OR/NOT, confirm, cross, if/else blocks |
| `Signal` | Entry/exit trigger event | Emerald | `#52A97C` | Input: execution blocks (enter_long, enter_short, close) |
| `RiskParams` | Risk configuration object | Coral | `#D46060` | Input: Risk block required port only |
| `OrderModel` | Order execution parameters | Slate | `#6A849E` | Input: Execution block configuration port |

**Type compatibility rules:**
- Types are **strict** — `Series<number>` cannot connect to a `Series<boolean>` port.
- There are no implicit coercions at the graph level.
- Future: a `cast` block (numeric → boolean threshold) may be introduced as an explicit transform node, not as an implicit edge coercion.
- `Series<OHLCV>` is the only source type for indicator blocks; indicator blocks emit `Series<number>`.

---

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

### Persistence timeline — when each new entity is introduced

| Entity | First introduced as DB schema | Phase | Migration required? |
|---|---|---|---|
| `LabWorkspace` | **Phase 3** | When graph drafts need persistence across page reload | Yes — new table |
| `StrategyGraph` | **Phase 3** | Same time as LabWorkspace | Yes — new table |
| `StrategyGraphVersion` | **Phase 4** | On first graph compile | Yes — new table |
| `MarketDataset.name` | **Phase 2** | Minimal nullable column | Yes — nullable column add |

> **Phase 0 and Phase 1: ZERO schema migrations required.**
> Phase 2 requires exactly one minimal schema change: adding `name` (nullable string) to `MarketDataset`.
> All new tables are introduced in Phase 3 at the earliest.

---

### LabWorkspace — Phase 1 lifecycle (client-side only)

In Phase 1, `LabWorkspace` exists only as **Zustand store state**, optionally backed by `localStorage`.

Phase 1 `useLabGraphStore` state shape (NO DB):
```typescript
// Client-side session state — no backend persistence in Phase 1
interface LabSessionState {
  activeConnectionId: string | null;   // ExchangeConnection id
  activeDatasetId: string | null;      // MarketDataset id
  activeGraphId: string | null;        // StrategyGraph id (null until Phase 3)
  validationState: 'ok' | 'warning' | 'error' | 'stale' | 'idle';
  runState: 'idle' | 'running' | 'done' | 'failed';
  nodes: [];                           // empty until Phase 3
  edges: [];                           // empty until Phase 3
}
```

This state is sufficient for Phase 1 Context Bar rendering and Phase 2 Dataset Builder wiring.

---

### New: `LabWorkspace` (Phase 3 DB entity)

Introduced when graph persistence is needed.
- `id` (ulid, PK)
- `workspaceId` (FK → Workspace)
- `name` (string)
- `activeExchangeConnectionId` (FK → ExchangeConnection, nullable)
- `activeDatasetId` (FK → MarketDataset, nullable)
- `createdAt`, `updatedAt`

### New: `StrategyGraph` (Phase 3)
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
New nullable field on `MarketDataset`: `name` (string, nullable) — Phase 2.

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

> **This phase MUST be completed as a standalone, separate PR before any UI work starts.**
> Rationale: freezing the vocabulary, naming, and API contracts before code is written prevents the most expensive class of bugs — architectural misunderstandings baked into implementation.
> Phase 0 contains no code changes. It is documentation-only.

### Recommended PR sequence

```
PR 1 — Phase 0:   docs-only, no code
PR 2 — Phase 1A:  panel layout (no backend)
PR 3 — Phase 1B:  Lab store wiring (no backend)
PR 4 — Phase 2A:  dataset form UI
PR 5 — Phase 2B:  preview table/chart + /preview endpoint
PR 6 — Phase 2C:  quality summary UI
...
```

> Each PR must be independently reviewable and deployable.
> Do NOT combine Phase 0 with Phase 1A or any UI work.
> Do NOT start Phase 1A until Phase 0 is merged and reviewed.

### Tasks
- Update `docs/12-ui-ux.md` Lab section with Lab v2 workspace model (4-panel layout, Classic mode note).
- Add this spec as `docs/23-lab-v2-ide-spec.md` (already done — verify content is final).
- Update `docs/00-glossary.md`:
  - add: `LabWorkspace`, `StrategyGraph`, `StrategyGraphVersion`, `ValidationIssue`, `BlockLibraryVersion`, `CandleInterval`
  - clarify: `Dataset` → points to `MarketDataset` (Stage 19)
  - clarify: `BacktestRun` → is `BacktestResult` in codebase
  - add note: `LabWorkspace` ≠ `Workspace` (different concepts, different DB tables)
- Update `docs/07-data-model.md`:
  - reference `LabWorkspace`, `StrategyGraph`, `StrategyGraphVersion` as **future entities** (Phase 3+)
  - reference Stage 19 `MarketDataset` and `BacktestResult` as existing entities
- Confirm non-breaking relation to existing DSL (Stage 10) and Stage 19.
- Add React Flow v11+ as approved canvas library to `docs/17-tech-stack.md`.
- Add `react-resizable-panels`, `@tanstack/react-virtual`, `zundo` to `docs/17-tech-stack.md`.

### Acceptance checks
- [ ] No glossary term ambiguity between Lab v2 and existing docs
- [ ] `LabWorkspace` does not conflict with `Workspace` usage anywhere in docs
- [ ] `docs/12-ui-ux.md` Lab section reflects 4-panel model and Classic mode mandatory status
- [ ] React Flow v11+ added to tech stack doc
- [ ] Stage 19 explicitly referenced in Phase 2 and Phase 5 with "build on top of, not reimplement" note
- [ ] `docs/07-data-model.md` lists new entities as future (Phase 3+), not current
- [ ] No code changes in this PR

---

## Phase 1 — Lab shell refactor (UI only, no backend dependency)

### Goal
Create the new `/lab` screen structure without breaking existing functionality.

> **No backend changes. No schema migrations. No new API endpoints.**
> Phase 1 is purely frontend layout and client-side state.

### LabWorkspace in Phase 1 — client-side only

`LabWorkspace` in this phase is **not a DB entity**. It is the `useLabGraphStore` Zustand store.
The store holds session state (`activeConnectionId`, `activeDatasetId`) in component memory,
optionally persisted to `localStorage` for page-reload survival.

**No `LabWorkspace` table migration is needed in Phase 1.**
DB entity `LabWorkspace` is introduced in Phase 3.

### Classic mode — MANDATORY in Phase 1

`StrategyList`, `DslEditor`, `AiChat`, and `BacktestReport` MUST be preserved in their current form as a "Classic mode" tab.
Phase 1 does not modify these components — it only wraps them in the new shell layout.
An implementer who removes or degrades Classic mode components in this phase has violated the spec.

### Tasks

**1A — Panel layout:**
- Replace current single-center layout with multi-panel shell using `react-resizable-panels`:
  - top context bar (static, no data — all fields show "— not selected"),
  - left/main area with tabs: `[Classic mode]` (default) | `[Data]` | `[Build]` | `[Test]` (last 3 placeholders),
  - right inspector placeholder (collapsible),
  - bottom diagnostics drawer (collapsed placeholder).
- Classic mode tab contains existing `StrategyList` + `DslEditor` + `AiChat` + `BacktestReport` unchanged.
- Default tab on page load: **Classic mode** (not Data or Build — those are placeholders).
- No canvas library installed yet. Canvas area in [Build] tab is a plain `<div>` placeholder with text "Strategy canvas coming in Phase 3".

**1B — Lab state / store wiring:**
- Create `useLabGraphStore` (Zustand) with:
  - `activeConnectionId: string | null`
  - `activeDatasetId: string | null`
  - `activeGraphId: string | null` (unused until Phase 3)
  - `validationState: 'idle' | 'ok' | 'warning' | 'error' | 'stale'`
  - `runState: 'idle' | 'running' | 'done' | 'failed'`
  - `nodes: []` (empty array, ready for Phase 3)
  - `edges: []` (empty array, ready for Phase 3)
  - undo/redo history (zundo temporal middleware — installed now, wired to empty state)
- Wire Context Bar to `useLabGraphStore` (shows "— not selected" when null).
- Add routing for Lab tabs: `/lab` (default → Classic mode), `/lab/data`, `/lab/build`, `/lab/test`.
- Optional: persist `activeConnectionId` and `activeDatasetId` to `localStorage` (low priority).

### Acceptance checks
- [ ] `/lab` loads without error
- [ ] All panel regions render: Context Bar, tabbed main area, inspector placeholder, diagnostics drawer
- [ ] Default tab is Classic mode — `DslEditor` + `AiChat` + `BacktestReport` render and function unchanged
- [ ] `[Data]` tab shows placeholder text (no dataset form yet)
- [ ] `[Build]` tab shows placeholder text (no canvas yet)
- [ ] `[Test]` tab shows placeholder text
- [ ] Context Bar renders with "— not selected" for connection and dataset
- [ ] Resize handles work (drag panel widths/heights)
- [ ] `useLabGraphStore` initializes correctly (no errors)
- [ ] `useLabGraphStore` is connected to Context Bar
- [ ] No backend changes, no new API endpoints, no DB migrations

---

## Phase 2 — Dataset builder MVP (public market data only)

### Goal
Introduce dataset definition and preview workflow using the existing Stage 19 backend.

### Tasks
**2A — Dataset form UI:**
- Dataset Builder panel with all mandatory controls (§6.2).
- Client-side pre-validation (symbol from `InstrumentCache`, range ≤ 365d, estimated candles ≤ 100k).
- On submit: show `submitting` spinner → call `POST /api/v1/lab/datasets` (synchronous, blocks up to ~30s).
- POST returns final status (`READY | PARTIAL | FAILED`) and full metadata — no polling required.
- Optional: if user navigates away, use `GET /api/v1/lab/datasets` list to find an existing dataset matching the request params.

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

**3B — Node palette + Inspector + connection UX:**
- Searchable block palette (left panel) with all block categories (§6.3).
- Phase 3 MVP blocks: `candles`, `SMA`, `EMA`, `RSI`, `compare`, `cross`, `enter_long`, `enter_short`, `stop_loss`, `take_profit`.
- Custom React Flow node renderer for each block type (color by category; handles styled per §6.3.1 and §9.1).
- Full block connection UX as specified in §6.3.1: handle styling, edge colors, drag-to-connect, compatible-target highlighting, incompatible-target feedback, cardinality enforcement, stale state propagation.
- Inspector panel: parameter form, port info (with type color badges), validation errors for selected node.
- Port type compatibility enforced at connect time (client-side, per `isValidConnection` callback).
- Type mismatch and cycle tooltips/toasts per §6.3.1 validation feedback table.

**3C — Graph validation rules:**
- Client-side graph validation (cycle detection, type mismatch, missing required blocks).
- Debounced re-validation (500ms after last edit).
- Validation issues shown in Inspector + Validation tab in drawer.
- "Missing risk block" rule enforced (graph is invalid without at least one risk block).
- Required unconnected input ports render in error state automatically after validation.

### Acceptance checks
- [ ] Canvas loads with empty graph
- [ ] Drag blocks from palette to canvas
- [ ] Connect two compatible ports — edge appears in correct type color
- [ ] Connect incompatible ports — edge rejected; tooltip shows mismatch reason
- [ ] Connect to produce a cycle — toast shown, no edge created
- [ ] Drop on occupied input — old edge replaced (animated), single undo step
- [ ] Delete node removes connected edges; downstream nodes marked stale
- [ ] Cmd+Z undoes last connection/deletion action
- [ ] Graph with: candles → EMA → cross → enter_long + stop_loss + take_profit passes validation
- [ ] Graph without risk block shows validation error; required port renders red ring + ⚠
- [ ] Inspector shows correct params and port info (including type color) for selected node
- [ ] Selecting an edge highlights source/target nodes and shows edge label
- [ ] Auto-save triggers after 2s of inactivity
- [ ] All port handles and edges have `aria-label` (verify with DevTools accessibility panel)
- [ ] 200 nodes + 300 edges renders at ≥ 60fps during pan/zoom

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

> **Phase 0 is always a separate task/PR from any implementation phase.**
> Never combine Phase 0 docs work with Phase 1 shell work.

### Recommended execution slices

| Slice | Content | PR |
|---|---|---|
| Phase 0 | docs + glossary update | PR 1 |
| Phase 1A | panel layout (no backend) | PR 2 |
| Phase 1B | Lab state/store wiring | PR 3 |
| Phase 2A | dataset form UI | PR 4 |
| Phase 2B | preview table/chart + `/preview` endpoint | PR 5 |
| Phase 2C | quality summary UI | PR 6 |
| Phase 3A | graph canvas base + keyboard shortcuts | PR 7 |
| Phase 3B | node palette + Inspector | PR 8 |
| Phase 3C | client-side validation rules | PR 9 |
| Phase 4A | compiler backend + graph schema | PR 10 |
| Phase 4B | compiler UI + DSL preview | PR 11 |
| Phase 5A | run creation + report shell | PR 12 |
| Phase 5B | metrics/trades/equity/log tabs | PR 13 |
| Phase 6 | private data + stale-state + compare | PR 14–15 |

### Phase 2B optional split

If Phase 2B proves too large in a single PR, it MAY be split:
- **Phase 2B1**: `/preview` endpoint (backend) + virtualized table view (frontend)
- **Phase 2B2**: chart view (OHLCV candlestick via `lightweight-charts`)

This split is optional. Default is 2B as one unit. Only split if implementation size warrants it.

Do not split for other reasons (e.g., "cleanliness") — extra PRs add review overhead.

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
| `docs/07-data-model.md` | Add planned entities as **future (Phase 3+)**: `LabWorkspace`, `StrategyGraph`, `StrategyGraphVersion`; reference existing Stage 19 entities (`MarketDataset`, `BacktestResult`) |
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
0. **docs freeze (Phase 0)** — ALWAYS FIRST, standalone PR,
1. shell structure (Phase 1A + 1B),
2. dataset definition UI on existing backend (Phase 2),
3. graph model + canvas (Phase 3),
4. compiler (Phase 4),
5. reproducible runs (Phase 5).

**Critical implementation guidance:**
- **Phase 0 must be a separate PR from Phase 1** — no mixing docs with code.
- **Phase 2 is purely UI** — no new backend entities. Stage 19 already built the data layer. Phase 2 requires one minimal schema change: `MarketDataset.name` (nullable string).
- **Phase 3 requires a canvas library decision** (React Flow v11+) confirmed before any code is written. Also introduces the first DB migrations: `LabWorkspace` + `StrategyGraph` tables.
- **Phase 4 requires a formal block-to-DSL mapping table** defined in `docs/10-strategy-dsl.md` before the compiler is coded.
- **Phase 5 extends `BacktestResult`** (which already has `datasetId`/`datasetHash`/`engineVersion` from Stage 19) — binding is mostly UI work.
- **Classic mode (DslEditor + AiChat + BacktestReport) MUST NOT be removed** until Phase 4 is accepted.

This sequence minimizes rework, keeps the system compatible with the current architecture, and creates the strongest foundation for future AI-assisted strategy research inside botmarketplace.store.
