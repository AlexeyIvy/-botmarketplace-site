# Stage 20a — Guest Onboarding + Guest Terminal (market-only)

## Status: PLANNED

## 1) Overview

Goal: Allow first-time users to explore the product without registration while strictly gating account-/exchange-dependent features.

This stage introduces:
- First-visit onboarding choice: **Sign in** or **Continue as Guest**
- Terminal becomes usable in Guest mode for **market data only** (charts/ticker/candles/watchlist/indicators).
- Trading features remain gated behind auth.

---

## 2) Scope

### 2.1 Onboarding modal (first visit)
- Show a modal on first site visit:
  - **Sign in** → navigate to `/login`
  - **Continue as guest** → dismiss modal, proceed without token
- Persist decision in localStorage:
  - `localStorage.onboardingSeen = "1"` — set on either choice so modal never shows twice
- **Do NOT introduce** a separate `localStorage.userMode` flag. Guest/auth state is determined exclusively by presence/absence of `accessToken` in localStorage. Two separate flags for the same fact create sync bugs.
- Component: new `apps/web/src/components/OnboardingModal.tsx`
- Integration point: `apps/web/src/app/layout.tsx` — render `<OnboardingModal />` after the `<Navbar />`

### 2.2 Backend — make market-data endpoints public
**This is the most critical change in this stage.**

Currently `apps/api/src/routes/terminal.ts` has `{ onRequest: [app.authenticate] }` on both:
- `GET /terminal/ticker`
- `GET /terminal/candles`

Both must be changed to public (remove the `onRequest` hook). Their comment already says "Bybit data is public" — the guard is inconsistent with that intent. Workspace-scoped endpoints (`/exchanges`, `POST /terminal/orders`, `GET /terminal/orders`) keep their auth requirement unchanged.

### 2.3 Frontend — Guest Terminal access (market-only)
When **no auth token** exists:

**Allow:**
- Chart (candles)
- Ticker
- Watchlist
- Bottom "Ticker" and "Candles" tabs

**Gate (hide or replace with CTA):**
- Order Panel (right column) — replace with a CTA: "Login to trade / connect exchange"
- Bottom "Orders" tab — replace tab content with the same CTA (or hide the tab)
- Do NOT call `/exchanges` — it is workspace-scoped and will 401, which currently triggers the `sessionExpired` banner (a UX bug for guests)

**Fix in `loadAll()` function (`terminal/page.tsx` line 197–203):**

Current code redirects unauthenticated users to `/login` when they click "Load":
```ts
// REMOVE this guard — breaks guest market data loading
async function loadAll() {
  if (!getToken()) {
    router.push("/login");   // ← remove this block
    return;
  }
  await Promise.all([loadTicker(), loadCandles()]);
}
```
After the fix `loadAll()` simply calls `loadTicker()` + `loadCandles()` for all users; those two functions use `apiFetchNoWorkspace` (no auth required after the backend change in §2.2).

**Fix `/exchanges` unconditional call (terminal/page.tsx line 121–131):**

Currently fires on mount for all users. Must be guarded:
```ts
useEffect(() => {
  if (!hasToken) return;   // ← add this guard
  apiFetch<ExchangeConnection[]>("/exchanges").then((res) => { ... });
}, [hasToken]);
```
Without this guard a guest gets a 401 response, `clearAuth()` is called, and the `sessionExpired` banner fires — wrong behaviour.

### 2.4 Smoke-test updates

**Update (not add) existing tests 9.8 and 9.9:**

After making ticker/candles public, the existing assertions flip:
```
# BEFORE (current):
9.8: GET /terminal/ticker without auth → 401
9.9: GET /terminal/candles without auth → 401

# AFTER Stage 20a:
9.8: GET /terminal/ticker without auth → 200
9.9: GET /terminal/candles without auth → 200
```

These tests must be updated in `deploy/smoke-test.sh` in the same PR; otherwise CI will break.

**Add new mini-section "20a — Guest mode"** after section 20 (Stage 19 Datasets), numbered 20a to avoid collision with existing "20." prefix:

```bash
# ─── 20a. Guest mode — market data without auth ──────────────────────────────
header "20a. Guest mode — market data without auth"

# 20a.1 GET /terminal/ticker without auth → 200
GUEST_TICKER=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/ticker?symbol=BTCUSDT")
check "20a.1 GET /terminal/ticker (no auth) → 200" "200" "$GUEST_TICKER"

# 20a.2 GET /terminal/candles without auth → 200
GUEST_CANDLES=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=15&limit=50")
check "20a.2 GET /terminal/candles (no auth) → 200" "200" "$GUEST_CANDLES"

# 20a.3 POST /terminal/orders without auth → 401 (still protected)
GUEST_ORDER=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","side":"BUY","type":"MARKET","qty":0.001}' \
  "$BASE_URL/api/v1/terminal/orders")
check "20a.3 POST /terminal/orders (no auth) → 401" "401" "$GUEST_ORDER"
```

Test 20a.3 confirms the auth boundary is correct — placing orders still requires login.

---

## 3) Out of scope
- User profile/avatar
- Preferences sync
- Exchange/market symbol browser
- Realtime quotes / WebSocket streaming
- Lab demo mode
- Advanced indicators (come in a later stage)

---

## 4) Affected files

| File | Change | Priority |
|---|---|---|
| `apps/api/src/routes/terminal.ts` | Remove `onRequest: [app.authenticate]` from `GET /terminal/ticker` and `GET /terminal/candles` | **Required** |
| `apps/web/src/app/terminal/page.tsx` | Remove `/login` redirect in `loadAll()`; guard `/exchanges` call with `if (!hasToken) return`; hide Order Panel and Orders tab for guests; add CTA | **Required** |
| `apps/web/src/components/OnboardingModal.tsx` | New component: first-visit modal with Sign in / Continue as guest | **Required** |
| `apps/web/src/app/layout.tsx` | Mount `<OnboardingModal />` after `<Navbar />` | **Required** |
| `deploy/smoke-test.sh` | Update tests 9.8 & 9.9 (401 → 200); add section "20a" with tests 20a.1–20a.3 | **Required** |
| `apps/web/src/app/navbar.tsx` | Optional: show "Guest" badge in the nav auth area when not logged in | Optional |

---

## 5) Acceptance criteria

- [ ] First-time visit (incognito) shows the onboarding modal exactly once; refreshing the page does not show it again.
- [ ] Both "Sign in" and "Continue as guest" dismiss the modal and set `localStorage.onboardingSeen = "1"`.
- [ ] Guest can open `/terminal`, click "Load", and see chart candles + ticker data (no auth required).
- [ ] Guest sees Watchlist, can switch symbols, and load data for each.
- [ ] Guest does **not** see the Order Panel (replaced by "Login to trade" CTA).
- [ ] Guest does **not** see filled order history (Orders tab hidden or shows CTA).
- [ ] No background calls to `/exchanges` or `/terminal/orders` when not authed (verify in DevTools Network tab).
- [ ] The "Session expired" banner does **not** appear for guests.
- [ ] Authenticated users: all existing functionality unchanged (Order Panel visible, orders loadable).
- [ ] Smoke tests 9.8 and 9.9 pass with 200 (no auth); smoke test 20a.1–20a.3 all pass.

---

## 6) Verification commands

### Manual (browser)
1. Open site in Incognito → onboarding modal appears.
2. Click "Continue as guest" → terminal page opens.
3. Select BTCUSDT, click Load → candles chart renders, ticker shows price data.
4. Confirm Order Panel is absent or shows a CTA ("Login to trade").
5. Open DevTools → Network → confirm no calls to `/api/v1/exchanges` or `/api/v1/terminal/orders`.
6. Refresh page → onboarding modal does **not** reappear.
7. Log in → terminal loads fully with Order Panel and order history.

### API sanity (curl)
```bash
# Public market data — must work without auth
curl -s "$BASE_URL/api/v1/terminal/ticker?symbol=BTCUSDT" | jq .lastPrice
curl -s "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=15&limit=50" | jq 'length'

# Order placement — must still require auth
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","side":"BUY","type":"MARKET","qty":0.001}' \
  "$BASE_URL/api/v1/terminal/orders"
# Expected: 401
```

---

## 7) Smoke-suite additions (`deploy/smoke-test.sh`)

See §2.4 for the exact bash code to add/update. Summary:

| Test | Change |
|---|---|
| 9.8 — ticker without auth | Update expected: 401 → **200** |
| 9.9 — candles without auth | Update expected: 401 → **200** |
| 20a.1 — guest ticker → 200 | **New** |
| 20a.2 — guest candles → 200 | **New** |
| 20a.3 — guest POST orders → 401 | **New** (auth boundary sanity) |

---

## 8) Security notes

Making ticker/candles public exposes no user data or secrets — these endpoints proxy Bybit's public market data. The decision to require auth was defensive but unnecessary. Rate limiting (`@fastify/rate-limit`) remains in place to prevent abuse.

Workspace-scoped endpoints (`/exchanges`, `POST /terminal/orders`, `GET /terminal/orders`, `GET /terminal/orders/:id`) keep their auth + workspace checks unchanged.
