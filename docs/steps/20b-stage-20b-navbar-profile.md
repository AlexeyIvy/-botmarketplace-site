# Stage 20b — Navbar Profile (email + avatar) + Dropdown Menu

## Status: PLANNED

## 1) Overview

Goal: Improve top-right UX after login:
- Show authenticated user email
- Show avatar (MVP: URL-based, supports GIF)
- Add dropdown menu (Account/Settings/Logout)
- Keep Guest state clean and obvious (no auth token → Guest UI)

This stage is UI/Account polish and does not change trading/backtest logic.

---

## 2) Scope

### 2.1 Navbar — show user identity
When `accessToken` exists:
- Fetch `GET /auth/me`
- Display `user.email` in the top-right area of Navbar
- Display user avatar (see §2.2)

When no token:
- Show existing `Sign in` / `Register`
- Optional: show a small "Guest" badge (do not introduce extra mode flags; guest/auth is derived from token presence, consistent with Stage 20a).

**Implementation note for Navbar `/auth/me` fetch:**
Navbar currently uses `useEffect([pathname])` to check `getToken()`. Extend this same effect to call `apiFetchNoWorkspace<{ user: { id: string; email: string; avatarUrl?: string | null }; workspaceId: string }>("/auth/me")` and store the result in local state (`userInfo`). This means Navbar will automatically refresh on every navigation — acceptable for MVP.

**State sync with Settings page (MVP approach):**
Do NOT introduce a global UserContext for this stage. Accept that after saving avatarUrl in Settings, the Navbar avatar updates on the next navigation (route change), which triggers the existing `useEffect([pathname])`. This is correct MVP behaviour without cross-component state management complexity.

### 2.2 Avatar MVP — URL-based (GIF supported)
Add avatar support without file uploads:

**Backend:**
- Add `avatarUrl` column to `User` (nullable string).
- Add endpoint to update avatar:
  - `PATCH /users/me` (auth required)
  - Body: `{ "avatarUrl": "https://..." }`
  - Validation:
    - allow empty string or null to clear avatar
    - basic length limit (2048 chars)
    - only allow `http://` / `https://` scheme (or null/empty)
- Extend `GET /auth/me` response to include `avatarUrl` (see §4.1 — requires DB lookup, not JWT read).

**Frontend:**
- Settings page (`/settings`):
  - Add an "Avatar" block with:
    - input field "Avatar URL"
    - preview (inline `<img>` if URL is set)
    - save button
  - Use `apiFetchNoWorkspace` for `PATCH /users/me` (no workspace context needed).
  - On successful save, update local `me` state so preview and email in Settings reflect new value.
- Navbar:
  - Render avatar circle (image if `avatarUrl` exists, otherwise initials fallback).
  - Use plain `<img src={avatarUrl}>`, **not** Next.js `<Image>` — avatarUrl is user-supplied from any domain; Next.js Image requires pre-configured domains in `next.config.js`.
  - Accept animated GIF automatically (native `<img>` renders GIF natively).

**Explicitly out of scope for 20b:**
- File upload, image storage, resizing, moderation.
(Those can be a later stage: avatar upload pipeline.)

### 2.3 Dropdown menu (top-right)
Add dropdown menu. **Replace** the existing flat "⚙ Settings" link and "Sign out" button with a single avatar/profile trigger + dropdown:

- Trigger: avatar circle (or initials circle) in top-right, clicking opens dropdown.
- Menu items:
  - "Settings" → `/settings`
  - "Logout" → existing `clearAuth()` + redirect `/login`

Implementation constraints:
- No new UI libraries.
- Use simple React state (`isOpen`) + `useEffect` click-outside close via `useRef` + `document.addEventListener('mousedown', ...)`.
- Close on selection.
- Keep styling consistent with existing inline styles.

---

## 3) Out of scope
- Preferences sync (Stage 20c)
- Symbol browser / realtime quotes (Stage 20d)
- Indicators v2 + Lab demo (Stage 20e)
- Avatar upload/storage

---

## 4) API contract changes

### 4.1 `GET /auth/me` (existing)

Currently returns:
```json
{ "user": { "id": "...", "email": "..." }, "workspaceId": "..." }
```

Updated response:
```json
{ "user": { "id": "...", "email": "...", "avatarUrl": "https://..." }, "workspaceId": "..." }
```

**Critical implementation note:** The current `/auth/me` handler reads only from the JWT payload (`request.user`) — it does NOT query the database. Since `avatarUrl` is never stored in the JWT, a Prisma DB lookup must be added:

```ts
// auth.ts — GET /auth/me
const payload = request.user as { sub: string; email: string };
const user = await prisma.user.findUnique({ where: { id: payload.sub } });
if (!user) return reply.code(401).send(problem(401, "User not found"));
return reply.send({
  user: { id: user.id, email: user.email, avatarUrl: user.avatarUrl ?? null },
  workspaceId: membership?.workspaceId ?? null,
});
```

Without this change, `avatarUrl` will always be `undefined` in the response even after `PATCH /users/me`.

### 4.2 `PATCH /users/me` (new)
- Auth required (`app.authenticate`)
- Input:
  - `{ "avatarUrl": "https://..." }` — set avatar
  - `{ "avatarUrl": null }` or `{ "avatarUrl": "" }` — clear avatar
- Validation:
  - `avatarUrl` must be `null`, empty string, or start with `http://` / `https://`
  - max length 2048 chars
- Output: `200 { "user": { "id": "...", "email": "...", "avatarUrl": "..." } }`

---

## 5) Affected files

| File | Change | Priority |
|---|---|---|
| `apps/api/prisma/schema.prisma` | add `User.avatarUrl String?` | **Required** |
| `apps/api/prisma/migrations/*` | migration adding `avatarUrl` column (`prisma migrate dev --name add_user_avatar_url`) | **Required** |
| `apps/api/src/routes/auth.ts` | add `prisma.user.findUnique` in `/auth/me` handler; include `avatarUrl` in response | **Required** |
| `apps/api/src/routes/users.ts` (new) | implement `PATCH /users/me` with auth + validation | **Required** |
| **`apps/api/src/app.ts`** | **import + register `userRoutes` — without this `PATCH /users/me` returns 404** | **Required** |
| `apps/web/src/app/navbar.tsx` | fetch `/auth/me` via `apiFetchNoWorkspace`; show email + avatar circle + dropdown menu; replace flat Settings+SignOut with dropdown trigger | **Required** |
| `apps/web/src/app/settings/page.tsx` | extend `Me` type with `avatarUrl?: string \| null`; add Avatar URL input + preview + save block using `apiFetchNoWorkspace` for `PATCH /users/me` | **Required** |

---

## 6) Acceptance criteria

**Navbar:**
- [ ] After login, Navbar displays authenticated email (from `/auth/me` DB lookup).
- [ ] Avatar circle renders `<img src>` if `avatarUrl` is set; otherwise shows initials fallback.
- [ ] Dropdown menu opens/closes correctly and contains Settings + Logout.
- [ ] Click outside dropdown closes it.
- [ ] Logout clears token + workspaceId and redirects to `/login` (existing behavior).
- [ ] The flat "⚙ Settings" link and "Sign out" button are replaced by the dropdown pattern (not duplicated).

**Settings:**
- [ ] User can set avatarUrl in Settings and see inline preview.
- [ ] After saving, Settings avatar preview updates immediately.
- [ ] Navbar avatar updates on next navigation (route change) — acceptable MVP.
- [ ] User can clear avatarUrl (set null/empty) and fallback initials are shown.
- [ ] `PATCH /users/me` uses `apiFetchNoWorkspace` (no `X-Workspace-Id` header needed).

**Security:**
- [ ] No secrets are logged or rendered.
- [ ] Avatar URL is treated as untrusted input (length + scheme validation on backend).
- [ ] Plain `<img src>` used for avatarUrl — no Next.js `<Image>` domain config required.

---

## 7) Verification commands

### Manual (browser)
1. Login.
2. Confirm Navbar shows email.
3. Go to `/settings` → set Avatar URL (try a GIF) → Save.
4. Navigate to another page → confirm Navbar avatar updates.
5. Open dropdown menu → Settings works, Logout works.
6. Clear avatar → Save → navigate → fallback initials show.

### API sanity (curl)
```bash
# Auth check — confirm avatarUrl is in response
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/v1/auth/me" | jq .

# Update avatar
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"avatarUrl":"https://example.com/avatar.gif"}' \
  "$BASE_URL/api/v1/users/me" | jq .

# Confirm reflected in /auth/me (requires DB lookup in handler)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/v1/auth/me" | jq .user.avatarUrl

# Clear avatar
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"avatarUrl":null}' \
  "$BASE_URL/api/v1/users/me" | jq .user.avatarUrl
# Expected: null
```

---

## 8) Review notes (corrections vs original draft)

The following issues were identified during codebase review and corrected in this document:

**CRITICAL — `apps/api/src/app.ts` missing from Affected files**
New `users.ts` route must be imported and registered in `app.ts` (same pattern as all other routes). Without this, `PATCH /api/v1/users/me` returns 404. This file was absent from the original draft's affected files list.

**CRITICAL — `/auth/me` reads JWT payload only, not database**
Current `auth.ts` handler returns only `{ id: payload.sub, email: payload.email }` from the JWT — no Prisma query. Since `avatarUrl` is never stored in the JWT, a `prisma.user.findUnique` call must be added to the handler. Without this, `avatarUrl` is always `undefined` even after a successful `PATCH /users/me`.

**IMPORTANT — State sync mechanism made explicit**
Original spec said "immediately or after refresh" without specifying how. Corrected: Navbar refetches `/auth/me` on every pathname change (already in `useEffect([pathname])`) — no UserContext needed for MVP. "Immediately" in Settings is achieved by updating local `me` state after save.

**IMPORTANT — `apiFetchNoWorkspace` for `PATCH /users/me`**
`/users/me` is a user-scoped endpoint, not workspace-scoped. Must use `apiFetchNoWorkspace` (Bearer token only, no `X-Workspace-Id`). Using `apiFetch` would add an unnecessary workspace resolution step.

**IMPORTANT — Plain `<img>` not Next.js `<Image>`**
Next.js `<Image>` requires domain allowlisting in `next.config.js`. Since avatarUrl is user-supplied from arbitrary domains, use native `<img src>` tag.

**MINOR — Existing flat Settings+SignOut buttons must be replaced**
Original spec said "add dropdown" without clarifying that the existing "⚙ Settings" Link and "Sign out" button (navbar.tsx:81-106) must be removed and replaced by the dropdown trigger. Clarified in §2.3.

**MINOR — `Me` type in settings/page.tsx needs `avatarUrl`**
Existing `interface Me { id: string; email: string }` must be extended with `avatarUrl?: string | null`.
