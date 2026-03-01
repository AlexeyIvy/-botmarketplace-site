# Stage 16 — Settings & Account (v2 final)

## Overview

Add a Settings page at `/settings` with:
- Account info (email from `GET /auth/me`) + Logout
- Theme switcher (CSS vars only, no external packages)
- Exchange Connections management (list / add / test / delete)

Executed in three sub-stages: **16a → 16b → 16c**.

---

## Affected files (canonical)

| File | Purpose |
|------|---------|
| `apps/web/src/app/navbar.tsx` | Add Settings entry point |
| `apps/web/src/lib/api.ts` | **New** — canonical home for `apiFetch`, `apiFetchNoWorkspace`, `clearAuth`, `getToken` |
| `apps/web/src/app/factory/api.ts` | Remove moved helpers; keep only factory-specific logic (or re-export from `lib/api.ts`) |
| `apps/web/src/app/settings/page.tsx` | Settings page shell → populated across 16a/16b/16c |

---

## Stage 16a — Settings entry + Account panel + Logout + API refactor + 401 UX

### Goals

1. **Navbar entry** in `apps/web/src/app/navbar.tsx`:
   - Show `⚙ Settings` link only when auth token is present
   - Routes to `/settings`

2. **Settings page shell** `apps/web/src/app/settings/page.tsx`:
   - **Account** block: display `email` fetched from `GET /auth/me`
   - **Logout** button

3. **Logout behaviour**:
   - Call existing `clearAuth()` (clears `accessToken` + `workspaceId` from localStorage)
   - Redirect to `/login`

4. **API helper refactor** (mandatory, no copy-paste):
   - Move `apiFetch`, `apiFetchNoWorkspace`, `clearAuth`, `getToken` out of
     `apps/web/src/app/factory/api.ts` into `apps/web/src/lib/api.ts`
   - Update all import sites (factory, terminal, new settings page)
   - Do **not** change request behaviour — only move storage location

5. **Centralised 401 UX** (no toast/modal libraries):
   - Inside `apiFetch`, after `fetch()`:
     - if `res.status === 401` → call `clearAuth()`, return a controlled error object
   - In Settings and Terminal UI: render a simple inline banner
     `"Session expired, please log in"` with a link/button to `/login`
   - No new npm packages

### Out of scope 16a
- Theme switcher
- Exchange Connections UI

### Acceptance criteria 16a
- [ ] `/settings` accessible after login, shows authenticated user's email
- [ ] Logout clears token + workspaceId and redirects to `/login`
- [ ] `apiFetch` lives in `lib/api.ts`; no duplication across files
- [ ] 401 responses handled gracefully (inline banner, not raw error text)
- [ ] `next build` passes; smoke suite stays green

---

## Stage 16b — Theme switcher (CSS vars only)

### Goals

1. **Theme options**: System / Dark / Light
2. **Implementation approach** (mandatory):
   - Existing CSS variables are already defined for dark mode (default)
   - Light mode = a second set of CSS vars scoped to class `.theme-light` on `<html>`
   - Dark = default (no class) or `.theme-dark` if already present in global CSS
3. **Persistence**: `localStorage.theme = 'system' | 'dark' | 'light'`
4. **Apply on mount**:
   - Read `localStorage.theme`
   - If `'system'` → read `matchMedia('(prefers-color-scheme: dark)')` once and apply matching class
   - Do **not** subscribe to `matchMedia` changes (deferred)
5. **UI**: plain `<select>` or radio buttons — no UI library components

### Out of scope 16b
- Exchange Connections UI
- Any new npm packages

### Acceptance criteria 16b
- [ ] Theme persists across page refresh
- [ ] All existing pages remain readable in both themes
- [ ] Zero new dependencies added

---

## Stage 16c — Exchange Connections management UI

### Goals

Add an **"Exchange Connections"** block on `/settings`.

#### List
- `GET /exchanges` (workspace-scoped) via `apiFetch` (sends `X-Workspace-Id` header)
- Display only safe fields: `name`, `exchange`, `status`, `createdAt`
- **Never** display `apiKey`, `secret`, or `encryptedSecret`

#### Add form
- Fields: `exchange` (BYBIT is sufficient), `name`, `apiKey`, `secret`
- Submit → `POST /exchanges`
- On success: clear `apiKey`/`secret` from component state immediately, refresh list
- `apiKey`/`secret` must not persist in state longer than needed

#### Test connection
- `POST /exchanges/:id/test`
- Update `status` in the list
- Show result as inline text (e.g. "OK" / "Failed: ...")

#### Delete connection
- `window.confirm('Delete connection?')` — no custom modal
- `DELETE /exchanges/:id`
- Refresh list on success

### Out of scope 16c
- `PATCH /exchanges/:id` (edit connection) — **do not implement**
- Any UI package (headlessui, shadcn, next-themes, etc.)
- Custom modal/toast system

### Acceptance criteria 16c
- [ ] List, add, test, delete all functional
- [ ] 401/403 handled via the 16a centralised banner
- [ ] Secrets (`apiKey`, `secret`, `encryptedSecret`) never rendered or logged
- [ ] `next build` passes; smoke suite stays green

---

## Non-functional constraints (all sub-stages)

- No new npm packages unless absolutely unavoidable (none expected)
- No Tailwind utility additions beyond what already exists
- No `next-themes` or similar theme libraries
- No copy-paste of helper functions — use the refactored `lib/api.ts`
- `window.confirm()` is acceptable for destructive confirmations
- All inline UI feedback via plain React state + simple `<div>` banners

---

## Rollback

Each sub-stage is a separate PR. Revert the PR to roll back without affecting other sub-stages.
