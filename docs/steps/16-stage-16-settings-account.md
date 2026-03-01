# Stage 16 — Settings & Account UX (v2)
**Status:** Approved (post-review v2)
**Baseline:** `main` after Stage 15 (Terminal chart + MT4-like layout completed)
**Goal:** Add a user Settings layer: profile / session / theme / exchange connections management — so the platform feels like a product, not a collection of pages.

---

## 1) Background & Problem

Currently the user:
- can log in and use Terminal/Lab/Factory
- but there is no single place for "who am I / logout / theme / settings / connected exchanges"
- UX on expired session / 401 often looks like an "error", not "please login"

---

## 2) Stage 16 Objective

Deliver a full Settings layer:
- settings entry point in the header
- Settings page at `/settings` with:
  1. Current user (email)
  2. Logout
  3. Theme switcher (Light / Dark / System)
  4. Exchange Connections management UI (list / add / test / delete)
  5. Session-expired UX (clear and friendly)

Stage 16 is UX + UI, with minimal safe API calls. No new large features.

---

## 3) Scope (Must-have)

### A) Settings entry point
- In `apps/web/src/app/navbar.tsx` add:
  - ⚙️ Settings icon/text — visible only when token exists
  - leads to `/settings`
- Settings accessible only after login:
  - if no token → redirect to `/login`

### B) Current user block
- Show:
  - `email` of the currently logged-in user
  - (optional) `workspaceId` (copyable) — handy for debugging
- Data source:
  - `GET /auth/me` — exists, returns `{ user: { id, email }, workspaceId }`
  - use `apiFetchNoWorkspace` (auth-only, no X-Workspace-Id header needed)

### C) Logout
- "Logout" button
- Behaviour:
  - call existing `clearAuth()` (removes `accessToken` + `workspaceId` from localStorage)
  - redirect to `/login`
- Important: no backend token revoke / refresh tokens (separate feature). Client-side only.

### D) Theme switcher
- Options: `System` / `Dark` / `Light`
- Implementation — CSS variables only, no Tailwind, no new packages (e.g. next-themes):
  - Theme is controlled by a class on `<html>`: no class = dark (default), `.theme-light` = light
  - `globals.css` already defines CSS vars for dark; add a `.theme-light {}` block overriding the same vars
  - Persistence: `localStorage.setItem('theme', 'system'|'dark'|'light')`
  - On mount: read `localStorage.theme`; if `'system'`, read `window.matchMedia('(prefers-color-scheme: dark)')` once and apply class accordingly. Do NOT subscribe to system theme changes (deferred).
- Requirement: must not break the existing dark UI; all pages must remain readable in both modes.

### E) Exchange Connections UI
Separate block "Exchange Connections" on the Settings page.

Must have:
1. **List** connections (for current workspace):
   - safe fields only: `name`, `exchange`, `status`, `createdAt`
   - buttons: `Test`, `Delete`
   - use `apiFetch` (with `X-Workspace-Id` header)
2. **Add connection** (form):
   - exchange dropdown (BYBIT is sufficient for now)
   - name, apiKey, secret
   - `POST /exchanges`
   - after success: refresh list; immediately clear apiKey/secret from component state
3. **Test connection**:
   - `POST /exchanges/:id/test`
   - show result inline; update status in list
4. **Delete**:
   - confirmation: `window.confirm('Delete connection?')` — sufficient, no modal library needed
   - `DELETE /exchanges/:id`
   - refresh list on success

**Out of scope for Stage 16 — explicitly not doing:**
- UI for `PATCH /exchanges/:id` (edit connection credentials) — API endpoint exists but UI is out of scope
- Any UI library (headlessui / shadcn / next-themes) — do not add

Security:
- Never display or log `apiKey`, `secret`, `encryptedSecret` — backend already filters these from responses
- All requests use `apiFetch` with `X-Workspace-Id`

### F) Session-expired UX
- Centralised 401 intercept **inside `apiFetch`** (see 16a refactor below):
  - if `res.status === 401` → call `clearAuth()` and return a controlled error result
- In UI (Settings, Terminal, etc.): show a simple inline banner:
  - "Session expired, please login" + link/button to `/login`
- No toast library, no modal library, no new packages.

---

## 4) Out of scope (NOT in Stage 16)

- Refresh tokens, token rotation, logout-all-devices (separate stage)
- RBAC / permissions UI (owner / admin / member)
- Real-money safety workflows (2FA, withdrawal locks)
- Notifications system (Stage 17)
- Multi-workspace switching (separate stage)
- Edit connection UI (`PATCH /exchanges/:id`) — API exists, UI is not in scope
- Any new npm packages for UI components or theme management

---

## 5) Critical refactor — must happen in 16a

`apiFetch`, `apiFetchNoWorkspace`, `clearAuth`, `getToken`, `setToken`, `getWorkspaceId`, `setWorkspaceId`
currently live in `apps/web/src/app/factory/api.ts` (factory-specific file).

**Required in 16a:**
- Move these helpers to `apps/web/src/lib/api.ts` (create file)
- Update all imports in:
  - `apps/web/src/app/factory/` (all files that import from `factory/api.ts`)
  - `apps/web/src/app/terminal/` (if applicable)
  - new `apps/web/src/app/settings/` files
- Do NOT copy-paste; do NOT change behaviour — only change file location and update imports.

---

## 6) Implementation split (3 PRs)

### Stage 16a — Settings entry + Account panel + Logout + API refactor + 401 UX
**Files changed:**
- `apps/web/src/lib/api.ts` — NEW (moved from factory/api.ts)
- `apps/web/src/app/factory/api.ts` — remove helpers, import from lib/api.ts
- `apps/web/src/app/terminal/page.tsx` — update import if needed
- `apps/web/src/app/navbar.tsx` — add ⚙️ Settings entry
- `apps/web/src/app/settings/page.tsx` — NEW: account panel + logout

**Acceptance:**
- `/settings` accessible after login; shows email from `GET /auth/me`
- Logout clears token + workspaceId, redirects to `/login`
- `apiFetch` lives in `lib/api.ts`, zero duplication
- 401 response triggers `clearAuth()` and shows inline "Session expired" banner
- Build passes, smoke suite green

**Out of scope for 16a:** theme switcher, exchange connections UI

---

### Stage 16b — Theme switcher (CSS vars only)
**Files changed:**
- `apps/web/src/app/globals.css` — add `.theme-light {}` CSS vars block
- `apps/web/src/app/settings/page.tsx` — add theme switcher UI (System/Dark/Light)
- `apps/web/src/app/layout.tsx` — apply theme class on mount from localStorage

**Acceptance:**
- Theme persists across page refresh
- All pages readable in both dark and light modes
- No new npm dependencies

**Out of scope for 16b:** exchange connections UI

---

### Stage 16c — Exchange Connections management UI
**Files changed:**
- `apps/web/src/app/settings/page.tsx` — add Exchange Connections block

**Acceptance:**
- list / add / test / delete all work for current workspace
- apiKey/secret/encryptedSecret never displayed or logged
- 401/403 handled gracefully via 16a intercept + inline banner
- Build passes, smoke green

**Out of scope for 16c:** edit connection UI, UI libraries, new npm packages

---

## 7) Existing endpoints (do not re-implement)

| Endpoint | Method | Purpose |
|---|---|---|
| `/auth/me` | GET | Current user email + workspaceId |
| `/exchanges` | GET | List connections (workspace-scoped) |
| `/exchanges` | POST | Create connection |
| `/exchanges/:id/test` | POST | Test connectivity |
| `/exchanges/:id` | DELETE | Delete connection |
| `/exchanges/:id` | PATCH | Update credentials — **API only, no UI in Stage 16** |

---

## 8) Acceptance Criteria (full Stage 16)

1. Header has Settings entry (⚙️), visible only when logged in, leads to `/settings`.
2. Settings page shows current user email and Logout button.
3. Logout clears session and redirects to `/login`; returning to `/terminal` requires login.
4. Theme switcher works: System / Dark / Light, persists across refresh.
5. Exchange Connections: list / add / test / delete work for current workspace.
6. Secrets (apiKey / secret / encryptedSecret) never appear in UI or logs.
7. On 401: friendly inline "Session expired → Login" CTA, no raw 401 text.
8. Build passes, smoke suite green, no new npm dependencies.

---

## 9) Verification (manual, reproducible)

**A) Account**
- Login → open `/settings` → see email
- Click Logout → redirect to `/login`
- Navigate to `/terminal` → should require login

**B) Theme**
- Toggle System → Light → Dark
- Refresh page → selected theme persists
- Check readability of Terminal/Lab/Factory in light mode

**C) Exchange connections**
- Create a connection → confirm apiKey/secret not visible in list
- Test connection → status updates inline
- Delete → confirm dialog → item removed from list
- Verify network responses contain no `encryptedSecret`

**D) Session expired**
- Delete `accessToken` from localStorage manually
- Perform an action in Settings or Terminal → see "Session expired" inline banner, not raw 401

---

## 10) Deliverables

- PRs: `claude/stage-16a-*`, `claude/stage-16b-*`, `claude/stage-16c-*` → merged to `main`
- Updated docs: this file (`docs/steps/16-stage-16-settings-account.md`)
- Stage report per PR:
  - PR link
  - changed files
  - verification steps
  - deviations (if any)
