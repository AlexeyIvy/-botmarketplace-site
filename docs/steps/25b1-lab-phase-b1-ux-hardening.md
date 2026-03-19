# Phase B1 — UX Hardening: Onboarding, Rename, Equity Curve, Shortcut Help

**Source:** `docs/25-lab-improvements-plan.md` Phase B1
**Depends on:** Phase A2 (#89) merged and deployed
**Master issue:** #104

---

## Tasks completed

### B1-1: Empty canvas onboarding state (#105)

- Added `apps/web/src/app/lab/build/templates.ts` — hardcoded EMA Crossover graph template
  - Chain: `Candles → EMA(9) → EMA(21) → Cross → EnterLong + StopLoss(1%) + TakeProfit(2%)`
  - No API call needed — pure JSON template
- Added conditional hint in `LabBuildCanvas` when `nodes.length === 0`
  - Centered text: "Drag a block from the palette — or press ⌘⇧F to search"
  - Button: "Load EMA Crossover example" → hydrates store with template
- Hint disappears as soon as nodes appear

### B1-2: Graph rename — inline double-click (#106)

- Added inline rename to graph selector bar in `page.tsx`
- Double-click on graph name → `<input>` appears pre-filled
- Enter/blur → commits via `labApi.patchGraph(id, { name })` → updates local `availableGraphs`
- Escape → discards without changes
- PATCH endpoint already accepts `{ name }` — verified at `apps/api/src/routes/lab.ts:174`

### B1-3: Equity curve in Classic Mode backtest results (#107)

- Added `buildEquitySeries()` — normalised equity starting at 100, compounding from `tradeLog.pnlPct`
- Added `EquityCurveChart` component using `lightweight-charts` `LineSeries` (dark theme, 200px)
- Added tab bar to backtest results: "Metrics" | "Equity Curve"
- Handles empty trade log gracefully (shows placeholder text)
- No new dependencies — `lightweight-charts` already installed

### B1-4: Keyboard shortcut help overlay (#108)

- Added `?` button to Context Bar (far right, circular, consistent with dark theme)
- Modal lists all 8 keyboard shortcuts in a clean table
- Modal closes on Escape, backdrop click; does NOT close on content click
- Style: `rgba(10,14,20,0.97)` background, `1px solid rgba(255,255,255,0.1)` border, `border-radius: 8px`

---

## Files changed

| File | Change |
|------|--------|
| `apps/web/src/app/lab/build/page.tsx` | B1-1 empty canvas hint, B1-2 inline rename |
| `apps/web/src/app/lab/build/templates.ts` | **NEW** — EMA Crossover template |
| `apps/web/src/app/lab/LabShell.tsx` | B1-4 shortcut help modal + button |
| `apps/web/src/app/lab/ClassicMode.tsx` | B1-3 equity curve chart + tab bar |
| `docs/00-glossary.md` | Added Equity Curve, Onboarding State, Graph Rename |
| `docs/steps/25b1-lab-phase-b1-ux-hardening.md` | **NEW** — this step doc |

## Verification

- `tsc --noEmit` (web): 0 errors
- `tsc --noEmit` (api): pre-existing errors only (not from this PR)
- `next build`: passes
- No schema migrations
- No new API endpoints (uses existing PATCH /lab/graphs/:id)
- No new npm dependencies
