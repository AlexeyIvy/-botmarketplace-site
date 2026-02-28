# Stage 15 — Terminal MT4-like Charting UI (v1)
**Status:** Draft v4 (final, after full expert review)
**Target baseline:** RC1 `v0.1.0-rc1` (Stage 14 complete)
**Goal:** Add MT4-like trading terminal experience (charts + indicators + layout) on the website UI, using existing API.

---

## 1) Background & Problem

Current state:
- `/terminal` has market data + candles + manual orders flow (demo-first), but UI is primarily forms/tables.
- Users expect "terminal like MT4": chart-first experience (candles, crosshair, timeframe, indicators).
- If unauthenticated, UI shows raw 401 errors ("Valid Bearer token required") which looks like "site is broken".

---

## 2) Stage 15 Objective

Deliver **MT4-like v1** inside `/terminal`:
- Interactive candlestick chart (primary UI)
- Minimal but "terminal-grade" indicators
- MT4-like layout (watchlist / chart / order panel / bottom tabs)
- Trade markers on chart (based on existing `/terminal/orders`)
- Proper website login UX: user logs in on the site (UI), not via VPS terminal tricks.

---

## 3) Confirmed existing capabilities (checked)

- Candles endpoint exists: `GET /terminal/candles?symbol=&interval=&limit=`
- Orders endpoint exists (for markers): `GET /terminal/orders` (returns last 50; workspace-scoped)
- `apps/web/src/app/terminal/page.tsx` exists and will be updated
- `components/terminal/` directory does NOT exist and should be created (no conflict)
- Intervals supported: `1/5/15/30/60/240/D` (matches API and `INTERVALS` in `terminal/page.tsx`)
- Smoke tests should remain API-level (no Playwright dependency)

**API prefix clarification (frontend behavior):**
Frontend uses `API_PREFIX="/api/v1"` and calls:
- `apiFetchNoWorkspace('/terminal/candles?...')` → actual request is **`GET /api/v1/terminal/candles?...`**

So both statements are true:
- frontend code references `/terminal/...`
- network request goes to `/api/v1/terminal/...`

---

## 4) Critical prerequisites (must be explicit)

### 4.1 Dependency
`lightweight-charts` is NOT installed yet. Add it:

```
pnpm --filter @botmarketplace/web add lightweight-charts@^5
```

Compatibility note:
- lightweight-charts v5 is vanilla JS and does not depend on React renderer, compatible with React 19.

### 4.2 Next.js 15 SSR constraint (important)
lightweight-charts manipulates DOM directly. Chart component MUST be client-only:
- either add `'use client'` at the top of the chart component file,
- OR wrap with `dynamic(() => import(...), { ssr: false })`.

If not done, Next build can fail or runtime can crash.

---

## 5) Scope

### 5.1 Must-have deliverables (end-state after 15a–15d)

A) **Interactive chart on `/terminal`**
- Candlestick chart with:
  - grid
  - crosshair
  - zoom + scroll
  - responsive resize (desktop + mobile; see ResizeObserver requirement below)
- Timeframe selector: `1/5/15/30/60/240/D`
- Data source: candles endpoint via existing frontend fetch mechanism
  - `apiFetchNoWorkspace('/terminal/candles?symbol=...&interval=...&limit=...')`
  - actual network path will be `/api/v1/terminal/candles?...` due to prefix.

B) **Indicators (minimal "terminal-grade" set)**
- Overlays on main chart:
  - MA(20)
  - EMA(50)
- Separate lower pane:
  - RSI(14)
- Volume histogram
- Each indicator has an ON/OFF toggle.

C) **MT4-like layout**
- Left: Watchlist (symbols)
- Center: Chart (main) + optional RSI pane (bottom)
- Right: Order panel (existing)
- Bottom tabs: Orders / Positions / Events / Candles (existing can remain; chart is primary)

D) **Trade markers on chart (confirmed source + correct fetch helper)**
- Use confirmed endpoint: `GET /terminal/orders` (workspace-scoped).
- IMPORTANT: orders fetch MUST use `apiFetch(...)` (because it injects `X-Workspace-Id`).
  - Do NOT use `apiFetchNoWorkspace` for orders.
- Marker time source (confirmed):
  - endpoint returns `createdAt` (ISO string), not `openTime`.
  - convert to unix seconds:
    - `time = Math.floor(new Date(order.createdAt).getTime() / 1000)`
- Display markers:
  - BUY: green arrow up
  - SELL: red arrow down
- Mapping is best-effort: `createdAt` is not candle open time; align to nearest candle visually.

E) **Website login UX fix**
- If unauthenticated on `/terminal`:
  - show clear CTA "Login to load market data"
  - do NOT show raw 401 as primary UX
- Optional: auto-redirect to `/login` on Load attempt if no token.

---

## 6) Technical Approach (with critical implementation rules)

### 6.1 Time units (CRITICAL — ms → s)
API candle `openTime` is in **milliseconds**.
lightweight-charts expects **unix seconds**.

Data mapping rule:
- `time = Math.floor(candle.openTime / 1000)`

This conversion MUST be applied. Without it, chart will render wrong (far future dates) or appear empty.

### 6.2 Resize handling (IMPORTANT)
lightweight-charts does not auto-resize with container changes.
Chart component MUST implement `ResizeObserver`:

- Observe the chart container element
- On resize:
  - `chart.resize(el.clientWidth, el.clientHeight)`
- Cleanup on unmount:
  - `observer.disconnect()`
  - `chart.remove()`

Without this, mobile/desktop layout changes will break chart sizing.

**Container height requirement:**
Container must have an explicit height set (e.g. `height: 500px` or `flex: 1` with a bounded parent)
before the chart is created. A zero-height container renders a blank chart silently, with no errors.

### 6.3 Client-only component (Next.js)
Chart component must be `'use client'` (or dynamic import with `ssr: false`).

### 6.4 Data sources and fetch helpers
- Candles/ticker are non-workspace routes → use `apiFetchNoWorkspace`
- Orders are workspace-scoped → use `apiFetch` (adds `X-Workspace-Id`)

---

## 7) Out of scope (explicitly NOT in Stage 15)

- Full TradingView platform features (drawing studio, Pine scripts, huge indicator library)
- WebSocket streaming
- Advanced order management parity with MT4 (trailing stop, partial close UI, etc.)
- DSL / Lab / Bot runtime changes
- RBAC / refresh tokens scope expansion
- New backend endpoints unless absolutely required (avoid scope creep)

---

## 8) Recommended sub-stages (to fit CloudCode context)

### Stage 15a — Auth UX fix + dependency
Scope:
- Install `lightweight-charts`
- Update `/terminal` UI:
  - if no accessToken → show Login CTA
  - prevent showing raw 401 as the main terminal UX
  - optional: redirect or prompt on Load click without token
Acceptance:
- `/terminal` without login shows CTA (not raw 401)
- No regressions in existing Terminal behavior

### Stage 15b — Core Chart
Scope:
- Create `TerminalChart.tsx` (client-only)
- Render candlesticks + volume histogram
- Connect to real candles endpoint
- Apply CRITICAL time conversion: `time = Math.floor(candle.openTime / 1000)`
- Set explicit container height before chart creation (zero-height = blank chart)
- Implement ResizeObserver + cleanup on unmount
- Timeframe selector, zoom/scroll/crosshair
Acceptance:
- Chart renders with real data for BTCUSDT 15m (or any valid symbol)
- Timeframe switch works
- No crashes on resize (desktop ↔ mobile)

### Stage 15c — Indicators + Toggles
Scope:
- Create `indicators.ts` helpers: MA/EMA/RSI
- Add overlays (MA/EMA) and RSI lower pane
- Add UI toggles for MA/EMA/RSI/Volume

**Note on pane API (lightweight-charts v5):**
Verify the multi-pane API before implementing RSI pane.
In v5, pane assignment uses the `pane` option on series:
`chart.addLineSeries({ pane: 1 })` where `0` = main pane, `1` = lower pane.
Confirm against installed v5 TypeScript types before coding.

Acceptance:
- Toggles show/hide each indicator correctly
- Performance acceptable on mobile (reasonable default limit)

### Stage 15d — MT4 layout + markers + docs + minimal smoke updates
Scope:
- MT4-like layout: watchlist left, chart center, order panel right, bottom tabs
- IMPORTANT: remove `maxWidth: 960` constraint from terminal page wrapper
  - switch to full-width flex/grid layout so 3-column terminal fits
- Mobile: collapse watchlist + order panel (accordion/toggles)
- **Watchlist data source:** static hardcoded list of popular symbols
  - e.g. `BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT`
  - No new backend endpoint needed
- Add chart markers from `GET /terminal/orders`
  - use `apiFetch` (workspace header)
  - marker time from `createdAt` → unix seconds: `Math.floor(new Date(order.createdAt).getTime() / 1000)`
- Finalize docs: `docs/steps/15-stage-15-terminal-mt4-like.md`
- Minimal smoke additions (API-level only), avoid Playwright
Acceptance:
- Layout looks "terminal-like" on desktop and usable on mobile
- Markers render for recent BUY/SELL orders
- No secret leaks and no regressions

---

## 9) Acceptance Criteria (overall Stage 15 end-state)

1) `/terminal` renders interactive candlestick chart (chart-first UI).
2) Chart supports timeframe switch + zoom/scroll + crosshair.
3) Indicators: MA/EMA overlays + RSI pane + Volume histogram with toggles.
4) Auth UX: unauth user sees Login CTA, not raw 401 as primary UX.
5) No regressions in Terminal features.
6) No secret leaks (apiKey/secret/encryptedSecret/passwordHash never shown).
7) Docs updated in repo.

---

## 10) Verification (manual, reproducible)

A) Logged-in:
- Login via `/login`
- Open `/terminal`
- Load BTCUSDT, 15m, 200 candles
- Toggle MA/EMA/RSI/Volume
- Verify zoom/scroll/crosshair

B) Unauthenticated:
- Incognito `/terminal`
- Must show Login CTA
- Load attempt should prompt/redirect, not spam raw 401

C) Errors:
- Invalid symbol: show friendly error, UI remains usable

---

## 11) Deliverables

- PR(s) per sub-stage 15a → 15d (preferred)
- Each PR includes:
  - changed files list
  - verification steps
  - no scope creep
- Final doc lives at:
  - `docs/steps/15-stage-15-terminal-mt4-like.md`
