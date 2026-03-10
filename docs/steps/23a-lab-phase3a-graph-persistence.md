# 23a — Phase 3A: Graph Persistence Completion

## Status: COMPLETE (after verification pass)

---

## Pass History

### Initial implementation (`0197ec3`)
Not acceptance-ready:
1. `stale_against_last_compile` declared but unreachable — mutations always set `"dirty"`.
2. Graph selector absent — mount always picked `graphs[0]` with no UI.
3. Overstated acceptance claims without real verification.

### Corrective pass (`6fd8371`)
- Fixed `stale_against_last_compile` via `_graphChangedSinceCompile` flag.
- Added minimal graph selector with pre-save flush.
- Honest checklist replacing unsupported claims.

### Verification pass (`see below`)
- Ran `next build` — PASS.
- Ran web `tsc --noEmit` — PASS.
- Confirmed all API `lab.ts` errors are pre-existing (identical pre/post 23a).
- Found and fixed stale-cache bug in graph selector: `handleSelectGraph` was using
  `availableGraphs` local state (set at mount) instead of fetching fresh from
  `GET /api/v1/lab/graphs/:id`. In a same-session multi-switch scenario this would
  have silently shown stale graph data and potentially overwritten DB state on next
  autosave. Fixed by fetching fresh from API on each switch.

---

## 1. Scope

Complete graph persistence for the Lab visual strategy builder (`/lab/build`).

Specifically:
- Add `PATCH /api/v1/lab/graphs/:id` backend endpoint for auto-save
- Load/hydrate persisted graph on `/lab/build` mount
- Create first draft if no graph exists yet
- Auto-save graph mutations via debounced PATCH
- Persistence lifecycle state model in Zustand
- Minimal graph selector UI (if workspace has multiple graphs)
- Save state visible in UI (badge + save_error toast)
- Compile is no longer the first persistence path
- `stale_against_last_compile` is a real, reachable state

---

## 2. Scope Boundaries

### In scope (23a only)
- `PATCH /api/v1/lab/graphs/:id` — partial update of `graphJson` (and optionally `name`)
- Mount-time graph load: `GET /api/v1/lab/graphs` → pick most recent → hydrate Zustand
- First-draft creation: if list is empty → `POST /api/v1/lab/graphs` → hydrate Zustand
- Auto-save: debounced 1500ms PATCH after any graph mutation
- `SaveState` type: `"clean" | "dirty" | "saving" | "save_error" | "stale_against_last_compile"`
- Hydration guard: mutations during hydration do not trigger autosave
- Save state badge in Context Bar
- Save error visible to user (non-silent)
- Minimal graph selector: `<select>` in build canvas when workspace has >1 graph; flushes save before switch
- `_hydrating` and `_graphChangedSinceCompile` flags in store (not persisted in undo history)

### Out of scope (23b / Phase 6 / expansion)
- Phase 6 private data blocks
- DSL↔graph reverse compile
- Block library Tier 2
- Parameter sweep
- Research journal
- AI explainability
- compare runs / annotate_event
- Governance/provenance
- Multi-dataset binding
- Any deploy artifacts or release docs
- Full graph management UI (create/rename/delete from UI) — 23b1

---

## 3. Required References

| Document | Relevant Sections |
|---|---|
| `docs/24-lab-post-phase-5-roadmap.md` | §3 (Phase 3A blocker analysis), §4 (invariants), §5 (backend contract) |
| `docs/23-lab-v2-ide-spec.md` | Phase 3A, §6.3 (context bar), §13.3 (validation/save separation) |
| `docs/07-data-model.md` | StrategyGraph, StrategyGraphVersion |
| `apps/api/src/routes/lab.ts` | Current graph endpoints |
| `apps/web/src/app/lab/useLabGraphStore.ts` | Current Zustand store |
| `apps/web/src/app/lab/LabShell.tsx` | Context bar + compile handler |
| `apps/web/src/app/lab/build/page.tsx` | Build canvas page |

---

## 4. Implementation Details

### Backend
- `PATCH /api/v1/lab/graphs/:id`
  - Body: `{ graphJson?: GraphJson; name?: string }`
  - Validates workspace ownership
  - Partial update (only provided fields)
  - Returns updated graph (GRAPH_SELECT)
  - Rate limit: 60/minute

### Frontend — Store (`useLabGraphStore.ts`)
- `SaveState` type with 5 values including `stale_against_last_compile`
- `_hydrating` flag suppresses autosave during hydration
- `_graphChangedSinceCompile` flag drives `stale_against_last_compile` transitions:
  - Set to `true` by all graph mutations
  - Reset to `false` by `setLastCompileResult` (compile saves graph on backend)
- `saveGraphNow` post-save state: if `lastCompileResult !== null && _graphChangedSinceCompile` → `stale_against_last_compile`; else → `clean`
- `setLastCompileResult` cancels pending autosave timer, sets `saveState = "clean"`, resets `_graphChangedSinceCompile`
- `saveGraphNow` skips PATCH if already `clean` OR `stale_against_last_compile` (both mean DB is up to date)

### Frontend — Build Page (`build/page.tsx`)
- Mount effect fetches graph list, stores in `availableGraphs` local state
- If `availableGraphs.length > 1`: renders minimal `<select>` above canvas
- `handleSelectGraph`: awaits `saveGraphNow()` then calls `hydrateGraph()` for target
- Selector disabled during `saving` and `isInitializing`

### Frontend — LabShell (`LabShell.tsx`)
- `stale_against_last_compile` badge label: "Saved · recompile needed" (amber colour)
- Other labels: Saved (green), Unsaved (dim), Saving… (amber), Save Error (red)

---

## 5. State Transition Table

| Event | From | To |
|---|---|---|
| Mount hydration | any | `clean` |
| Any graph mutation | `clean` / `stale_against_last_compile` | `dirty` |
| Autosave starts | `dirty` | `saving` |
| Save success, no prior compile | `saving` | `clean` |
| Save success, compile exists + changed | `saving` | `stale_against_last_compile` |
| Save fails | `saving` | `save_error` |
| Compile success | any | `clean` (compile saves graph on backend) |
| Mutation after compile | `clean` | `dirty` (with `_graphChangedSinceCompile=true`) |
| Next save after above | `saving` → | `stale_against_last_compile` |

---

## 6. Acceptance Checks

1. Open `/lab/build` with existing persisted graph → graph hydrates, nodes/edges visible
2. Open `/lab/build` with no persisted graph → first draft created, empty canvas
3. Add/move/delete node → autosave fires after 1500ms debounce
4. Reload page → graph state persists correctly
5. Undo/redo → each undo/redo triggers autosave debounce
6. Compile → `saveState` becomes `clean`, `_graphChangedSinceCompile` reset
7. Mutate after compile → save fires → `saveState` becomes `stale_against_last_compile`
8. Badge shows "Saved · recompile needed" in amber for `stale_against_last_compile`
9. Save failure → red badge visible in Context Bar, non-silent toast
10. Multiple graphs → `<select>` dropdown visible; switching flushes dirty state first
11. `saveState` never changes `validationState`
12. `saveState` never changes `compileState`
13. Hydration does not trigger autosave (no spurious PATCH on initial load)

---

## 7. Review Checklist

- [x] Backend PATCH endpoint validates workspace ownership
- [x] Backend PATCH endpoint does not allow mutation of `workspaceId` or other protected fields
- [x] Auto-save does not fire when `_hydrating = true`
- [x] `saveState` transitions are correct: dirty → saving → clean | save_error | stale_against_last_compile
- [x] `stale_against_last_compile` is reachable (implemented via `_graphChangedSinceCompile`)
- [x] `saveState` is excluded from `compileState` logic
- [x] `saveState` is excluded from `validationState` logic
- [x] Compile flow does not create new graph if `activeGraphId` is already set
- [x] Graph switch flushes dirty state before hydrating new graph
- [x] Graph switch fetches fresh graph data from API (not stale local cache)
- [x] Save error is visible (UI badge + non-silent toast)
- [x] `_hydrating` is excluded from undo history (zundo `partialize`)
- [x] `_graphChangedSinceCompile` is excluded from undo history
- [x] `saveState` is excluded from undo history
- [x] Minimal graph selector present when multiple graphs exist
- [x] No deploy instructions or artifacts created
- [x] No expansion-layer scope included

---

## 8. Verification

### Web typecheck
- `cd apps/web && npx tsc --noEmit` → **PASS** (no output, no errors)
- Reconfirmed after verification pass fix — still **PASS**

### Web build
- `cd apps/web && npx next build` → **PASS**
- All 16 pages generated including `/lab/build` (8.93 kB, no errors)

### API typecheck
- `cd apps/api && npx tsc --noEmit` → **FAILS** with 27 errors
- **All errors are pre-existing** — confirmed by running same command against pre-23a main branch
- 23a PATCH endpoint (`lab.ts:160-198`) contributes **zero new errors**
- Pre-existing errors are caused by un-generated Prisma client (missing `prisma generate`)
  and are unrelated to any 23a changes

### Lint
- **NOT RUN** — no lint script in web/api package.json

### Manual/runtime verification
- **NOT RUN** — no running dev server available in this environment
- Acceptance checks verified by code logic inspection + static analysis

### Bug found and fixed during verification
`handleSelectGraph` in `build/page.tsx` was using stale `availableGraphs` local state
(populated at mount, never refreshed) to hydrate on graph switch. In a same-session
multi-switch scenario (A→B→A), this would show stale data and risk overwriting correct
DB state on the next autosave. Fixed: now fetches fresh from `GET /api/v1/lab/graphs/:id`
before hydrating. Web typecheck and build remain PASS after fix.

### Limitations
- No running dev server; manual runtime verification not executed
- API typecheck fails due to un-generated Prisma client (environment limitation, pre-existing)

---

## 9. Exit Criteria

Phase 3A verification pass is complete when:
1. `stale_against_last_compile` is reachable and correctly transitioned ✓
2. Minimal graph selector implemented ✓
3. Graph selector uses fresh API data on switch (stale-cache bug fixed) ✓
4. Web typecheck passes ✓
5. Web build (`next build`) passes ✓
6. API typecheck errors confirmed as pre-existing (zero new errors from 23a) ✓
7. Acceptance claims in this document match actual implementation ✓
8. No deploy artifacts created ✓
9. Runtime verification: NOT RUN (no dev server in environment; remains open limitation)

**Initial Commit SHA:** `0197ec3`
**Corrective Pass Commit SHA:** `6fd8371`
**Verification Pass Commit SHA:** *(see git log)*
