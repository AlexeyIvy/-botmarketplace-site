# LAB IMPROVEMENTS PLAN — Post Phase-4B Hardening & Feature Expansion
**Project:** BotMarketplace
**Repository:** `AlexeyIvy/-botmarketplace-site`
**Status:** Ready for implementation — phased, per-PR delivery
**Author role:** Senior Software Engineer / Product Architect
**Scope:** Bug fixes, architectural hardening, UX improvements, and new features identified after Phase 4B completion. Builds on `docs/23-lab-v2-ide-spec.md` and on the implemented state of `useLabGraphStore`, `LabBuildCanvas`, `blockDefs.ts`, `LabShell`, and `ClassicMode`.
**Change type:** Additive, backward-compatible, phased.

---

## CHANGE LOG

**Revision 1 — March 2026 (initial expert pass):**
- Identified race condition in `hydrateGraph` (three separate `set()` calls).
- Identified module-level mutable timer / sequence state — SSR + test isolation risk.
- Identified dual Inspector layout ambiguity (`LabShell` placeholder vs `InspectorPanel` inside Build tab).
- Identified missing `+ New Graph` affordance — graph selector hidden at single-graph state.
- Identified absent save retry / exponential backoff on `save_error`.
- Identified `ValidationState` badges always `dimmed: true` in Context Bar — critical state not surfaced.
- Identified `Constant` block gap — `Compare` block unusable without numeric constant input.
- Identified missing equity curve in Classic Mode results.
- Identified missing keyboard shortcut help overlay.
- Identified missing `LabEdge` type narrowing (`Edge` → `Edge<StrategyEdgeData>`).
- Identified missing `labApi.ts` — fetch calls scattered across components.
- Identified DSL Preview without syntax highlighting.
- Identified `handleKeyDown` on `window` — not scoped to canvas focus.
- Added new feature specs: Graph rename, Equity Curve, Onboarding state, Parametric Optimization (Grid Search).

---

## 1. Scope and relationship to existing specs

This document extends `docs/23-lab-v2-ide-spec.md` (Lab v2 IDE Spec, Phases 0–6).
It does NOT replace or contradict any frozen decisions from §25 of that spec.

All changes below are additive. Classic mode is preserved. No schema changes before Phase B3.

### Prerequisite phases completed before this doc applies
- Phase 0 through Phase 4B from `docs/23-lab-v2-ide-spec.md` are assumed implemented.
- `useLabGraphStore` with `temporal` / `zundo`, auto-save, hydration, compile pipeline — all exist.
- `LabBuildCanvas`, `BlockPalette`, `InspectorPanel`, `ValidationDrawer`, `StrategyEdge`, `StrategyNode` — all exist.
- `blockDefs.ts` with 10 blocks (SMA, EMA, RSI, Compare, Cross, EnterLong, EnterShort, StopLoss, TakeProfit, Candles) — exists.

---

## 2. Issue registry

Each issue tracked here has a severity, a phase assignment, and a source reference.

| ID | Description | Severity | Phase |
|---|---|---|---|
| BUG-01 | `hydrateGraph` uses three non-atomic `set()` calls — race condition risk | 🔴 HIGH | A1 |
| BUG-02 | Module-level `_validationTimer`, `_saveTimer`, `_nodeSeq` — SSR/test leak | 🔴 HIGH | A1 |
| BUG-03 | `handleKeyDown` bound to `window` — not scoped to canvas focus | 🟡 MEDIUM | A1 |
| BUG-04 | `save_error` state — no retry logic; user stuck until next mutation | 🟡 MEDIUM | A2 |
| UX-01 | Validation/Run badges in Context Bar always `dimmed: true` | 🔴 HIGH | A1 |
| UX-02 | Dual Inspector — `LabShell` placeholder + `InspectorPanel` inside Build tab | 🟡 MEDIUM | A2 |
| UX-03 | Graph selector hidden at single-graph state; no `+ New Graph` button | 🟡 MEDIUM | A2 |
| UX-04 | DSL Preview — plain `JSON.stringify` without syntax highlighting | 🟡 MEDIUM | A2 |
| UX-05 | Empty canvas — no onboarding state, no template shortcut | 🟡 MEDIUM | B1 |
| UX-06 | Graph name hardcoded `"Untitled Graph"` — no rename affordance | 🟡 MEDIUM | B1 |
| UX-07 | No keyboard shortcut help overlay (`?` or `Cmd+/`) | 🟢 LOW | B1 |
| FEAT-01 | Missing `Constant` block — `Compare` block unusable for numeric thresholds | 🔴 HIGH | A2 |
| FEAT-02 | Missing `MACD`, `Bollinger`, `ATR`, `Volume`, `AND/OR Gate` blocks | 🟡 MEDIUM | B2 |
| FEAT-03 | Equity curve absent from Classic Mode results after backtest | 🟡 MEDIUM | B1 |
| FEAT-04 | Port highlight during drag missing — compatible targets not visualised | 🟡 MEDIUM | A2 |
| FEAT-05 | Parametric optimisation (Grid Search) — run sweep over param range | 🟢 LOW | C1 |
| ARCH-01 | `LabEdge` typed as `Edge` — too wide; should be `Edge<StrategyEdgeData>` | 🟡 MEDIUM | A1 |
| ARCH-02 | Fetch logic inside components — no `labApi.ts` abstraction layer | 🟡 MEDIUM | A2 |

---

## 3. Phased implementation plan

Each phase is independently completable, reviewable, and fits within a single Claude Code context window.
**One phase = one PR.** Never combine two phases into one PR.

---

## Phase A1 — Critical bug fixes and type hardening

### Goal
Fix all 🔴 HIGH issues and ARCH-01 before any feature work begins.
This phase is purely internal — no visible UI changes except the Context Bar badge colours.

> **No schema migrations. No new API endpoints. No new UI components.**
> This is a surgical code-quality pass only.

### Tasks

**A1-1 — Atomic `hydrateGraph` in `useLabGraphStore`**

Current code (three separate `set()` calls — three renders, race condition window):
```ts
// BEFORE — non-atomic
set({ _hydrating: true });
set({ activeGraphId: graphId, nodes, edges, saveState: "clean" });
set({ _hydrating: false });
```

Fix — collapse into two atomic calls (hydrating flag must be a separate call to force subscribers to see the correct `_hydrating: true` state before node/edge data arrives):
```ts
// AFTER — two calls, still guards correctly
set({ _hydrating: true });
set({
  activeGraphId: graphId,
  nodes,
  edges,
  saveState: "clean",
  _hydrating: false,
});
```
The second `set` is now atomic — all fields (including `_hydrating: false`) land in a single Zustand update, eliminating the window between the node/edge restore and the hydrating-flag clear.

**A1-2 — Move module-level mutable state into store closures**

Current problem:
```ts
// BEFORE — module-level, shared across SSR requests and test runs
let _validationTimer: ReturnType<typeof setTimeout> | null = null;
let _saveTimer: ReturnType<typeof setTimeout> | null = null;
let _nodeSeq = 0;
```

Fix — move into the `create()` closure:
```ts
// AFTER — inside the create() factory, scoped to each store instance
let _validationTimer: ReturnType<typeof setTimeout> | null = null;
let _saveTimer: ReturnType<typeof setTimeout> | null = null;
let _nodeSeq = 0;
// ... rest of (set, get) => ({ ... })
```
Since `useLabGraphStore` is created once at module level in Next.js client context, the closure scope is functionally equivalent. The key gain is test isolation — each `create()` call in tests gets its own timers and sequence counter.

**A1-3 — Scope `handleKeyDown` to canvas focus**

Current problem in `LabBuildCanvas`:
```ts
// BEFORE — fires on any window keydown, including when modals are open
window.addEventListener("keydown", handleKeyDown);
```

Fix — check `document.activeElement` or a canvas-focused ref:
```ts
// AFTER — only act when canvas container is focused or contains focus
const handleKeyDown = useCallback((e: KeyboardEvent) => {
  const canvasEl = canvasContainerRef.current;
  if (!canvasEl) return;
  if (!canvasEl.contains(document.activeElement) && document.activeElement !== document.body) return;
  // ... existing shortcut logic
}, [undo, redo, getNodes, setNodes]);
```
Add `ref={canvasContainerRef}` to the `<div style={{ flex: 1, position: "relative", overflow: "hidden" }}>` wrapper and `tabIndex={0}` to make the canvas container focusable.

**A1-4 — Narrow `LabEdge` type**

In `useLabGraphStore.ts`:
```ts
// BEFORE
export type LabEdge = Edge;

// AFTER
import type { StrategyEdgeData } from "./build/edges/StrategyEdge";
export type LabEdge = Edge<StrategyEdgeData>;
```
This eliminates all `edge.data as StrategyEdgeData` casts in `StrategyEdge.tsx`, `InspectorPanel.tsx`, and `build/page.tsx`. Update all usages accordingly.

**A1-5 — Fix Context Bar validation / run badge dimming**

In `LabShell.tsx`, the badges are hardcoded `dimmed`:
```tsx
// BEFORE — always dimmed, hides critical state
<CtxBadge label="Validation" value={validationState} dimmed />
<CtxBadge label="Run"        value={runState}        dimmed />
```

Fix — derive `dimmed` from state value:
```tsx
// AFTER — dimmed only when idle; error state surfaces with full colour
<CtxBadge
  label="Validation"
  value={validationState}
  dimmed={validationState === "idle"}
  variant={validationState === "error" ? "error" : validationState === "warning" ? "warning" : undefined}
/>
<CtxBadge
  label="Run"
  value={runState}
  dimmed={runState === "idle"}
  variant={runState === "failed" ? "error" : undefined}
/>
```
The `CtxBadge` component must accept an optional `variant` prop (`"error" | "warning" | undefined`) and apply a colour token accordingly (red for error, amber for warning).

### Acceptance checks
- [ ] `hydrateGraph` uses exactly two `set()` calls; second call is atomic for nodes/edges/activeGraphId/saveState/`_hydrating:false`
- [ ] Module-level timer and sequence variables are inside the `create()` closure
- [ ] `LabEdge` type is `Edge<StrategyEdgeData>`; zero `as StrategyEdgeData` casts remain
- [ ] Pressing `Cmd+Z` while a modal is open over the canvas does NOT trigger undo on the graph
- [ ] Context Bar validation badge is red when graph has errors, amber when warnings, grey only when idle
- [ ] Context Bar run badge is red when run state is `failed`, grey only when `idle`
- [ ] No schema migrations in this PR
- [ ] No new API endpoints in this PR
- [ ] All existing tests pass

---

## Phase A2 — Save retry, API abstraction, Constant block, Inspector layout

### Goal
Fix remaining 🟡 MEDIUM bugs and add the `Constant` block (FEAT-01, blocking real strategy composition).

> **No schema migrations. One new block definition. No new API endpoints beyond existing patterns.**

### Tasks

**A2-1 — Save retry with exponential backoff**

Current `saveGraphNow` on failure:
```ts
} catch {
  set({ saveState: "save_error" });
  return false;
}
```

The user sees `save_error` indefinitely until they mutate the graph. No automatic recovery.

Fix — implement retry with exponential backoff (max 3 attempts):
```ts
// Inside saveGraphNow — attempt loop
const MAX_RETRIES = 3;
let attempt = 0;
while (attempt < MAX_RETRIES) {
  try {
    const res = await fetch(...);
    if (res.ok) { /* success path */ return true; }
    if (res.status >= 400 && res.status < 500) {
      // Client error (e.g. 404 graph not found) — do not retry
      set({ saveState: "save_error" });
      return false;
    }
  } catch { /* network error — retry */ }
  attempt++;
  if (attempt < MAX_RETRIES) {
    await new Promise(r => setTimeout(r, 500 * Math.pow(2, attempt - 1))); // 500ms, 1s, 2s
  }
}
set({ saveState: "save_error" });
return false;
```

Also add a **"Retry save"** button to the Context Bar `SaveState` badge when state is `save_error`:
```tsx
{saveState === "save_error" && (
  <button onClick={() => void saveGraphNow()} style={retrySaveButtonStyle}>
    Retry save
  </button>
)}
```

**A2-2 — Extract `labApi.ts`**

Create `apps/web/src/app/lab/labApi.ts` with typed fetch helpers:
```ts
// All fetch calls related to /api/v1/lab/graphs moved here
export async function listGraphs(): Promise<PersistedGraph[]> { ... }
export async function createGraph(name: string, graphJson: GraphJson): Promise<PersistedGraph> { ... }
export async function patchGraph(id: string, graphJson: GraphJson): Promise<void> { ... }
export async function fetchGraph(id: string): Promise<PersistedGraph> { ... }
```

Remove all inline `fetch()` calls from `LabBuildCanvas` and replace with `labApi.*` calls.
This is a refactor — zero behavior change. No new endpoints.

**A2-3 — Resolve dual Inspector layout**

Current situation:
- `LabShell` renders a right-panel `InspectorPlaceholder` (always visible, static).
- `LabBuildCanvas` renders its own `InspectorPanel` with real selection data (inside the Build tab area).

This creates two visual "inspector" regions on screen simultaneously.

Fix (Option A — preferred): Remove `InspectorPlaceholder` from `LabShell`'s right panel. Let each tab own its right-side content:
- Build tab: renders its own `InspectorPanel` internally (already does this).
- Data tab: no inspector (or future dataset-field inspector).
- Test tab: no inspector (or future run-parameter inspector).
- Classic mode: no inspector.

The LabShell right panel is replaced with a slot that is either empty or filled by the active tab's component.

Fix (Option B — simpler, less correct): Keep `InspectorPlaceholder` in `LabShell` but hide it when the Build tab is active, to avoid visual collision.

**Use Option A** — it is architecturally correct and removes confusion permanently.

**A2-4 — Add `+ New Graph` button and always-visible graph selector**

Current: graph selector is hidden when only one graph exists; no way to create a second graph without knowing the API exists.

Fix in `LabBuildCanvas`:
```tsx
// Always show the graph selector bar (even with one graph)
// Add a "+ New Graph" button beside the selector
<div style={graphSelectorBarStyle}>
  <span style={graphSelectorLabelStyle}>Graph:</span>
  <select value={activeGraphId ?? ""} onChange={...} style={graphSelectorStyle}>
    {availableGraphs.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
  </select>
  <button onClick={handleNewGraph} style={newGraphButtonStyle} title="Create new graph">
    + New
  </button>
</div>
```

`handleNewGraph` calls `labApi.createGraph("Untitled Graph", { nodes: [], edges: [] })`, then appends the new graph to `availableGraphs` and switches to it via `handleSelectGraph`.

**A2-5 — DSL Preview syntax highlighting**

Replace plain `<pre>{JSON.stringify(...)}</pre>` with a lightweight token coloriser:

```tsx
function JsonHighlight({ value }: { value: unknown }) {
  const raw = JSON.stringify(value, null, 2);
  // Tokenise: string values → green, keys → blue, numbers → amber, booleans/null → violet
  const html = raw
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let cls = "json-number";
        if (/^"/.test(match)) cls = /:$/.test(match) ? "json-key" : "json-string";
        else if (/true|false/.test(match)) cls = "json-bool";
        else if (/null/.test(match)) cls = "json-null";
        return `<span class="${cls}">${match}</span>`;
      });
  return <pre dangerouslySetInnerHTML={{ __html: html }} style={dslPreviewStyle} />;
}
```

Add CSS classes `json-key`, `json-string`, `json-number`, `json-bool`, `json-null` to the Lab stylesheet with appropriate colours from the project's dark theme palette.

> Security note: `dangerouslySetInnerHTML` is safe here — input is `JSON.stringify` output which contains no user HTML. Still: wrap in `DOMPurify.sanitize()` per project security policy (§15.1 of `docs/23-lab-v2-ide-spec.md`).

**A2-6 — Add `Constant` block to `blockDefs.ts`**

The `Compare` block accepts two `Series<number>` inputs. Without a `Constant` block, users cannot compare an indicator output against a fixed number (e.g., RSI > 30). This is FEAT-01 — blocks real strategy composition.

```ts
// In blockDefs.ts
{
  type: "constant",
  label: "Constant",
  category: "input",
  description: "Emits a fixed numeric value as a constant series.",
  inputs: [],
  outputs: [
    { id: "value", label: "value", dataType: "Series<number>" }
  ],
  params: [
    {
      id: "value",
      label: "Value",
      type: "number",
      defaultValue: 0,
      min: -1_000_000,
      max: 1_000_000,
      step: 0.01,
      description: "The constant numeric value emitted on every bar.",
    }
  ],
}
```

This block has no inputs, one output, and one editable parameter. It requires no backend change.

**A2-7 — Port highlight during drag (FEAT-04)**

`ConnectionContext` already exposes `sourceType` to all child components. Wire it to handle rendering.

In `StrategyNode.tsx`, read `sourceType` from `useConnectionContext()`. For each handle:
```tsx
const { sourceType } = useConnectionContext();
const isDragging = sourceType !== null;
const isCompatible = isDragging && isPortTypeCompatible(sourceType, port.dataType);
const isIncompatible = isDragging && !isCompatible;

// Apply to handle style:
style={{
  ...handleBaseStyle,
  opacity: isIncompatible ? 0.25 : 1,
  transform: isCompatible ? "scale(1.4)" : isIncompatible ? "scale(0.85)" : "scale(1)",
  boxShadow: isCompatible ? `0 0 6px ${PORT_TYPE_COLOR[port.dataType]}` : "none",
  borderColor: isIncompatible ? "#D44C4C" : PORT_TYPE_COLOR[port.dataType],
  transition: "all 0.12s ease",
}}
```

This satisfies the §6.3.1 spec requirement for compatible-target highlighting during drag.

### Acceptance checks
- [ ] `save_error` state triggers automatic retry (up to 3 attempts, exponential backoff)
- [ ] "Retry save" button is visible in Context Bar when `saveState === "save_error"`
- [ ] All inline `fetch()` calls in `LabBuildCanvas` are replaced by `labApi.*` calls
- [ ] `labApi.ts` exports: `listGraphs`, `createGraph`, `patchGraph`, `fetchGraph`
- [ ] `InspectorPlaceholder` removed from `LabShell` right panel; Build tab owns its own Inspector
- [ ] No duplicate inspector panels visible when Build tab is active
- [ ] Graph selector bar is always visible (even with one graph)
- [ ] `+ New Graph` button creates a new `"Untitled Graph"` and switches to it
- [ ] DSL Preview renders JSON with key/string/number/bool/null colouring
- [ ] `Constant` block appears in palette under "Input" category
- [ ] `Constant` block can be connected to `Compare` block's second input
- [ ] Strategy `Candles → RSI → Compare(RSI output, Constant(30)) → Cross → EnterLong` passes validation
- [ ] During drag from an output handle, compatible input handles scale up and glow; incompatible handles dim to 25% opacity and show red border
- [ ] No schema migrations in this PR
- [ ] No new backend API endpoints in this PR

---

## Phase B1 — UX hardening: onboarding state, graph rename, equity curve, shortcut help

### Goal
Polish the user experience for first-time and returning users. Three visible improvements and one foundational one.

> **One new backend field: `MarketDataset.name` is already proposed in Phase 2 of doc 23. For graph rename, only the existing `PATCH /api/v1/lab/graphs/:id` endpoint is used — no new endpoints needed.**

### Tasks

**B1-1 — Empty canvas onboarding state**

When `nodes.length === 0`, render a centred hint in the canvas area:
```tsx
{nodes.length === 0 && (
  <div style={emptyCanvasHintStyle}>
    <p style={emptyCanvasHintTextStyle}>
      Drag a block from the palette — or press{" "}
      <kbd style={kbdStyle}>⌘⇧F</kbd> to search
    </p>
    <button
      onClick={() => handleLoadTemplate("ema-crossover")}
      style={loadTemplateButtonStyle}
    >
      Load EMA Crossover example
    </button>
  </div>
)}
```

`handleLoadTemplate("ema-crossover")` hydrates the store with a pre-built graph containing:
`Candles → EMA(9) → EMA(21) → Cross → EnterLong + StopLoss(1%) + TakeProfit(2%)`

The template is a hardcoded JSON object in `build/templates.ts` — no API call needed.

**B1-2 — Graph rename (inline, double-click)**

In the graph selector bar, make the graph name inline-editable:
```tsx
{isRenaming ? (
  <input
    autoFocus
    value={draftName}
    onChange={e => setDraftName(e.target.value)}
    onBlur={() => { void commitRename(); setIsRenaming(false); }}
    onKeyDown={e => {
      if (e.key === "Enter") { void commitRename(); setIsRenaming(false); }
      if (e.key === "Escape") setIsRenaming(false);
    }}
    style={renameInputStyle}
  />
) : (
  <span
    onDoubleClick={() => { setDraftName(currentGraphName); setIsRenaming(true); }}
    style={graphNameLabelStyle}
    title="Double-click to rename"
  >
    {currentGraphName}
  </span>
)}
```

`commitRename` calls `labApi.patchGraph(activeGraphId, { name: draftName })` (extend `patchGraph` to accept a partial payload: `{ name?: string; graphJson?: GraphJson }`).

No new endpoint — `PATCH /api/v1/lab/graphs/:id` already exists. Backend just needs to accept `name` in the body (verify in `apps/api/src/routes/lab/graphs/[id]/route.ts`).

**B1-3 — Equity curve in Classic Mode backtest results**

After a backtest completes in `ClassicMode`, the `tradeLog` array is already present in the response. Render an equity curve using `lightweight-charts` (already installed):

```ts
// Compute equity series from tradeLog
function buildEquitySeries(tradeLog: TradeLine[]): LineData[] {
  let equity = 100; // normalised starting equity
  return tradeLog.map(trade => {
    equity *= (1 + trade.pnlPct / 100);
    return { time: trade.exitTime as UTCTimestamp, value: equity };
  });
}
```

Add an "Equity Curve" tab to `BacktestReport` (alongside the existing Metrics tab).
Use `createChart` + `addLineSeries` from `lightweight-charts` — same pattern as Terminal chart.

Container height: 200px. Dark theme. No additional dependencies needed.

**B1-4 — Keyboard shortcut help overlay**

Add a `?` icon button to the Context Bar (far right, before user menu if present).
On click, open a non-blocking modal overlay listing all keyboard shortcuts:

| Shortcut | Action |
|---|---|
| `⌘Z` | Undo |
| `⌘Y` / `⌘⇧Z` | Redo |
| `⌘A` | Select all nodes |
| `Del` / `⌫` | Delete selected |
| `⌘⇧F` | Search block palette |
| `Esc` | Deselect all |
| `⌘S` | Save graph now |
| `?` | Toggle this help |

Modal style: dark overlay (consistent with `ValidationDrawer` and `Toast` styling — `rgba(10,14,20,0.97)` background, `1px solid rgba(255,255,255,0.1)` border, `border-radius: 8px`).

### Acceptance checks
- [ ] Empty canvas shows hint text and "Load EMA Crossover example" button
- [ ] Clicking the template button populates canvas with EMA Crossover graph
- [ ] Graph name is double-clickable in selector bar; input appears inline
- [ ] Pressing Enter or blurring commits rename; pressing Escape discards
- [ ] Renamed graph name persists across page reload (confirmed via PATCH to backend)
- [ ] Classic Mode backtest result shows "Equity Curve" tab with rendered line chart
- [ ] Equity curve is deterministic — same trade log produces same chart
- [ ] `?` button in Context Bar opens shortcut help modal
- [ ] Shortcut help modal lists all 8 shortcuts accurately
- [ ] Modal closes on `Esc` or clicking outside
- [ ] No schema migrations in this PR
- [ ] `PATCH /api/v1/lab/graphs/:id` accepts `{ name: string }` payload (backend update required if not already)

---

## Phase B2 — Block library expansion (FEAT-02)

### Goal
Add 6 missing blocks that cover the most common trading strategy patterns.
All blocks are added to `blockDefs.ts` and require no backend changes.

> **No schema migrations. No new API endpoints. No changes outside `blockDefs.ts` and `validationTypes.ts`.**

### New blocks

**B2-1 — `macd` block**

```ts
{
  type: "macd",
  label: "MACD",
  category: "indicator",
  description: "Moving Average Convergence Divergence.",
  inputs: [{ id: "price", label: "price", dataType: "Series<number>", required: true }],
  outputs: [
    { id: "macd",      label: "macd",      dataType: "Series<number>" },
    { id: "signal",    label: "signal",    dataType: "Series<number>" },
    { id: "histogram", label: "histogram", dataType: "Series<number>" },
  ],
  params: [
    { id: "fastPeriod",   label: "Fast Period",   type: "number", defaultValue: 12, min: 1,  max: 200 },
    { id: "slowPeriod",   label: "Slow Period",   type: "number", defaultValue: 26, min: 1,  max: 500 },
    { id: "signalPeriod", label: "Signal Period", type: "number", defaultValue: 9,  min: 1,  max: 100 },
  ],
}
```

**B2-2 — `bollinger` block**

```ts
{
  type: "bollinger",
  label: "Bollinger Bands",
  category: "indicator",
  outputs: [
    { id: "upper",  label: "upper",  dataType: "Series<number>" },
    { id: "middle", label: "middle", dataType: "Series<number>" },
    { id: "lower",  label: "lower",  dataType: "Series<number>" },
  ],
  params: [
    { id: "period",    label: "Period",    type: "number", defaultValue: 20, min: 2, max: 500 },
    { id: "stdDevMult", label: "Std Dev ×", type: "number", defaultValue: 2.0, min: 0.1, max: 10, step: 0.1 },
  ],
}
```

**B2-3 — `atr` block**

```ts
{
  type: "atr",
  label: "ATR",
  category: "indicator",
  inputs: [{ id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true }],
  outputs: [{ id: "atr", label: "atr", dataType: "Series<number>" }],
  params: [
    { id: "period", label: "Period", type: "number", defaultValue: 14, min: 1, max: 500 },
  ],
}
```

**B2-4 — `volume` block**

```ts
{
  type: "volume",
  label: "Volume",
  category: "indicator",
  description: "Extracts the volume series from OHLCV candles.",
  inputs: [{ id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true }],
  outputs: [{ id: "volume", label: "volume", dataType: "Series<number>" }],
  params: [],
}
```

**B2-5 — `and_gate` block**

```ts
{
  type: "and_gate",
  label: "AND",
  category: "logic",
  description: "True only when all inputs are true on the same bar.",
  inputs: [
    { id: "a", label: "a", dataType: "Series<boolean>", required: true },
    { id: "b", label: "b", dataType: "Series<boolean>", required: true },
  ],
  outputs: [{ id: "out", label: "out", dataType: "Series<boolean>" }],
  params: [],
}
```

**B2-6 — `or_gate` block**

```ts
{
  type: "or_gate",
  label: "OR",
  category: "logic",
  inputs: [
    { id: "a", label: "a", dataType: "Series<boolean>", required: true },
    { id: "b", label: "b", dataType: "Series<boolean>", required: true },
  ],
  outputs: [{ id: "out", label: "out", dataType: "Series<boolean>" }],
  params: [],
}
```

### Acceptance checks
- [ ] All 6 new blocks appear in the Block Palette under correct categories
- [ ] `MACD` block shows 3 output ports (macd, signal, histogram)
- [ ] `Bollinger` block shows 3 output ports (upper, middle, lower)
- [ ] `ATR` block connects to `Candles` output (`Series<OHLCV>`) without type mismatch
- [ ] `Volume` block connects to `Candles` output (`Series<OHLCV>`) without type mismatch
- [ ] `AND` / `OR` gates accept `Series<boolean>` inputs and emit `Series<boolean>` output
- [ ] Strategy `Candles → MACD → cross(macd, signal) → AND(cross, RSI filter) → EnterLong` is connectable without validation errors
- [ ] No schema migrations in this PR
- [ ] No new API endpoints in this PR

---

## Phase C1 — Parametric optimisation (Grid Search)

### Goal
Allow users to sweep one strategy parameter over a range and compare backtest results.
This is the most impactful feature for serious traders — finding optimal parameter values without manual re-running.

> **Requires new backend endpoint: `POST /api/v1/lab/backtest/sweep`.**
> **Requires one new DB table: `BacktestSweep` (see §C1 data model below).**
> This is the first phase in this document that requires a schema migration.

### Product flow

1. User opens "Optimise" panel in the Test tab (new sub-tab alongside the existing Run Backtest form).
2. User selects:
   - Target block + parameter to sweep (e.g., `EMA` block → `length` param)
   - Sweep range: `from`, `to`, `step` (e.g., 5 → 50, step 5 → 10 runs)
   - Dataset + strategy version (same as standard backtest)
   - Metric to maximise: `pnl` | `winRate` | `sharpe` | `maxDrawdown`
3. User clicks "Run Sweep" → `POST /api/v1/lab/backtest/sweep` is called.
4. Backend runs N sequential backtests (one per parameter value), stores each as a `BacktestResult`, aggregates into a `BacktestSweep` record.
5. Frontend polls `GET /api/v1/lab/backtest/sweep/:id` until `status = DONE`.
6. Results shown as a sortable table: `[paramValue, pnl, winRate, drawdown, trades]`.
7. User clicks any row to open the full `BacktestResult` report for that run.

### Backend changes

**New endpoint: `POST /api/v1/lab/backtest/sweep`**

Request body:
```ts
interface SweepRequest {
  datasetId:         string;
  strategyVersionId: string;
  sweepParam: {
    blockId:   string;   // node id in the graph
    paramName: string;   // parameter key in blockDefs
    from:      number;
    to:        number;
    step:      number;
  };
  feeBps:      number;
  slippageBps: number;
}
```

Response:
```ts
interface SweepResponse {
  sweepId: string;
  runCount: number;
  estimatedSeconds: number;
}
```

**New endpoint: `GET /api/v1/lab/backtest/sweep/:id`**

Response:
```ts
interface SweepResult {
  id:        string;
  status:    "pending" | "running" | "done" | "failed";
  progress:  number;   // 0..runCount
  runCount:  number;
  results:   SweepRow[];
  bestRow?:  SweepRow;
  createdAt: string;
  updatedAt: string;
}

interface SweepRow {
  paramValue:      number;
  backtestResultId: string;
  pnlPct:          number;
  winRate:         number;
  maxDrawdownPct:  number;
  tradeCount:      number;
  sharpe:          number | null;
}
```

**New DB table: `BacktestSweep`**

```prisma
model BacktestSweep {
  id                String          @id @default(cuid())
  workspaceId       String
  strategyVersionId String
  datasetId         String
  sweepParamJson    Json            // { blockId, paramName, from, to, step }
  feeBps            Int
  slippageBps       Int
  status            SweepStatus     @default(PENDING)
  progress          Int             @default(0)
  runCount          Int
  resultsJson       Json?           // SweepRow[]
  bestParamValue    Float?
  createdAt         DateTime        @default(now())
  updatedAt         DateTime        @updatedAt
  workspace         Workspace       @relation(fields: [workspaceId], references: [id])
}

enum SweepStatus {
  PENDING
  RUNNING
  DONE
  FAILED
}
```

### Frontend changes

**New panel: `OptimisePanel.tsx`** in `apps/web/src/app/lab/test/`

- Rendered in the Test tab as a second sub-tab: `Run Backtest | Optimise`.
- Form: block selector (dropdown from current graph nodes), param selector, range inputs, metric selector.
- Run button triggers POST → shows progress bar (polling every 2s).
- Results rendered as sortable `<table>` with 5 columns.
- "Best" row highlighted in amber.
- Clicking a row opens `BacktestResult` report in a slide-over panel.

### Sweep limits (backend guards)
- Max `runCount` per sweep: 50 runs.
- Max concurrent sweeps per workspace: 2.
- Individual run timeout: 60s (same as standard backtest).
- Rate limit: 5 POST `/backtest/sweep` per minute per workspace.

If `runCount` exceeds 50, backend returns HTTP 422 with message: `"Sweep exceeds maximum of 50 runs. Narrow the range or increase the step."`

### Acceptance checks
- [ ] "Optimise" sub-tab visible in Test tab
- [ ] User can select any block and any numeric param from the current graph
- [ ] Range validation: `from < to`, `step > 0`, computed `runCount ≤ 50`
- [ ] POST `/api/v1/lab/backtest/sweep` creates `BacktestSweep` record with status `PENDING`
- [ ] Progress bar increments as sweep runs (polling every 2s)
- [ ] On completion: results table shows one row per parameter value
- [ ] Table is sortable by any column
- [ ] "Best" row highlighted
- [ ] Clicking a row opens the corresponding `BacktestResult` full report
- [ ] runCount > 50 shows error with clear message
- [ ] `BacktestSweep` table migration runs without errors
- [ ] Existing backtest flow unaffected
- [ ] Rate limit (5/min) returns HTTP 429 gracefully

---

## 4. Phase sizing summary for Claude Code

Each phase below maps to exactly one PR. Pass the entire phase section (including all tasks and acceptance checks) to the executor as the task specification.

| Phase | Content | PR | Schema migrations | Estimated size |
|---|---|---|---|---|
| **A1** | Atomic hydrate, module-level timers, keyboard scope, LabEdge type, Context Bar badge | PR 1 | None | Small |
| **A2** | Save retry, labApi.ts, Inspector layout, new graph button, DSL highlight, Constant block, port highlight | PR 2 | None | Medium |
| **B1** | Empty canvas onboarding, graph rename, equity curve, shortcut help | PR 3 | None (PATCH name field only) | Medium |
| **B2** | 6 new blocks: MACD, Bollinger, ATR, Volume, AND, OR | PR 4 | None | Small |
| **C1** | Grid Search / Parametric Optimisation | PR 5 | `BacktestSweep` table | Large |

---

## 5. Frozen decisions (this document)

The following decisions are closed and must not be re-opened in implementation PRs without a separate architecture review.

- **`hydrateGraph` atomicity:** two-call pattern (`_hydrating: true` first, then all state + `_hydrating: false` together) is the canonical fix. Do not use a single flat `set()` for all five fields — the guard flag must precede state restoration.
- **`labApi.ts` as the sole fetch abstraction for `/api/v1/lab/graphs/*`:** no inline `fetch()` calls in components. Components call `labApi.*`.
- **`Constant` block in `blockDefs.ts` (not a backend service):** it emits a constant value as a client-side graph primitive. No server execution. No new API.
- **Equity curve from `tradeLog`:** computed client-side from the existing backtest response. `lightweight-charts` is the rendering library. No new endpoint.
- **Grid Search:** implemented as a sequential server-side sweep (not parallel), stored in `BacktestSweep`. Max 50 runs per sweep. No background queue (same synchronous model as standard backtests, chained).

---

## 6. Required updates to existing docs

| Doc | What to update | Phase |
|---|---|---|
| `docs/00-glossary.md` | Add: `Constant block`, `BacktestSweep`, `Grid Search`, `Port highlight` | A2 |
| `docs/10-strategy-dsl.md` | Add: block-to-DSL mapping entries for `macd`, `bollinger`, `atr`, `volume`, `and_gate`, `or_gate`, `constant` | B2 |
| `docs/07-data-model.md` | Add: `BacktestSweep` entity (Phase C1) | C1 |
| `docs/12-api-contracts.md` | Add: `POST /api/v1/lab/backtest/sweep`, `GET /api/v1/lab/backtest/sweep/:id` | C1 |
| `docs/23-lab-v2-ide-spec.md` | Mark Phase 3B acceptance criteria `[x]` for port highlight (after A2) | A2 |

---

## 7. Non-goals (explicitly out of scope for this document)

- Multi-user collaboration on one graph.
- Parallel (multi-worker) sweep execution.
- Sweep over more than one parameter simultaneously (2D heatmap).
- AI-assisted parameter suggestion (separate feature spec needed).
- Mobile layout for the Optimise panel.
- Export sweep results to CSV from UI (can be done via direct `BacktestSweep` data in a future pass).
