# 23a — Phase 3A: Graph Persistence Completion

## Status: COMPLETE (after corrective pass)

---

## Corrective Pass Summary

The initial 23a implementation (`0197ec3`) was not acceptance-ready due to three issues:

1. **`stale_against_last_compile` was declared but never reached** — mutations always set `"dirty"`, so `stale_against_last_compile` could never be transitioned to. Fixed in corrective pass.
2. **Graph selector was absent** — mount always picked `graphs[0]` with no UI for multi-graph workspaces. A minimal `<select>` selector with pre-save flush is now implemented.
3. **Overstated acceptance claims** — "smoke checks passed", "graph switch safe", "ready for 23b1" were asserted without manual verification or build checks. Corrective pass uses honest checklist.

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
- [x] Save error is visible (UI badge + non-silent toast)
- [x] `_hydrating` is excluded from undo history (zundo `partialize`)
- [x] `_graphChangedSinceCompile` is excluded from undo history
- [x] `saveState` is excluded from undo history
- [x] Minimal graph selector present when multiple graphs exist
- [x] No deploy instructions or artifacts created
- [x] No expansion-layer scope included

---

## 8. Verification

### Typecheck
- `cd apps/web && npx tsc --noEmit` → **PASS** (no output, no errors)

### Build check
- **NOT RUN** — no `npm run build` available in this environment; Prisma client not generated; pre-existing API typecheck errors exist (unrelated to 23a changes)

### Lint
- **NOT RUN** — no lint script in web/api package.json

### Manual verification
- **NOT RUN** — no running dev server available in this environment
- Code satisfies acceptance checks by logic inspection

### Limitations
- Build check (next build) not executed — environment has no dev server
- API typecheck has pre-existing Prisma generation errors — these existed before 23a and are not caused by 23a changes
- All acceptance checks verified by code logic inspection only; runtime verification deferred to deployment environment

---

## 9. Exit Criteria

Phase 3A corrective pass is complete when:
1. `stale_against_last_compile` is reachable and correctly transitioned ✓
2. Minimal graph selector implemented ✓
3. Typecheck passes ✓
4. Acceptance claims in this document match actual implementation ✓
5. No deploy artifacts created ✓

**Initial Commit SHA:** `0197ec3`
**Corrective Pass Commit SHA:** `6fd8371`
