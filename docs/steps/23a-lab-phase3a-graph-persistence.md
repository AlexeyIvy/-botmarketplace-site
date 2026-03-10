# 23a — Phase 3A: Graph Persistence Completion

## Status: COMPLETE

---

## 1. Scope

Complete graph persistence for the Lab visual strategy builder (`/lab/build`).

Specifically:
- Add `PATCH /api/v1/lab/graphs/:id` backend endpoint for auto-save
- Load/hydrate persisted graph on `/lab/build` mount
- Create first draft if no graph exists yet
- Auto-save graph mutations via debounced PATCH
- Persistence lifecycle state model in Zustand
- Safe graph switching (if multiple graphs exist)
- Save state visible in UI (badge + save_error toast)
- Compile is no longer the first persistence path

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
- Graph switch: flush save before switch or explicit prompt; no silent data loss
- `_hydrating` flag in store (not persisted in undo history)

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

## 4. Required Output Format

### Plan
- Contract verification report (backend current state vs docs)
- Drift list if any
- Implementation approach for each sub-task

### Implementation

#### Backend
- `PATCH /api/v1/lab/graphs/:id`
  - Body: `{ graphJson?: GraphJson; name?: string }`
  - Validates workspace ownership
  - Partial update (only provided fields)
  - Returns updated graph (GRAPH_SELECT)
  - Rate limit: 60/minute

#### Frontend — Store (`useLabGraphStore.ts`)
- New type: `SaveState = "clean" | "dirty" | "saving" | "save_error" | "stale_against_last_compile"`
- New state fields:
  - `saveState: SaveState` (default: `"clean"`)
  - `_hydrating: boolean` (not in undo partialize; not persisted in DB)
- New actions:
  - `setSaveState(state: SaveState)`
  - `hydrateGraph(graphId: string, nodes: LabNode[], edges: LabEdge[])` — sets nodes/edges/activeGraphId + saveState=clean; does NOT schedule autosave
  - `saveGraphNow()` — immediately flush PATCH (for graph switch before save fires)
- Modified actions (add `dirty` + `scheduleAutoSave` if not `_hydrating`):
  - `onNodesChange`, `onEdgesChange`, `setNodes`, `setEdges`, `addNode`, `updateNodeParam`, `markDownstreamStale`
- Auto-save debounce: 1500ms, module-level ref
- Auto-save sets `saveState = "saving"` → `"clean"` or `"save_error"` on completion
- Invariants enforced: `saveState` is independent of `validationState` and `compileState`

#### Frontend — Build Page (`build/page.tsx`)
- `useGraphInit` effect on mount:
  1. `GET /api/v1/lab/graphs` — list workspace graphs
  2. If `graphs.length > 0`: pick `graphs[0]` (most recent, already sorted by `updatedAt desc`)
  3. If `graphs.length === 0`: `POST /api/v1/lab/graphs` with `{ name: "Untitled Graph", graphJson: { nodes: [], edges: [] } }`
  4. Call `hydrateGraph(id, nodes, edges)` from store
  5. Canvas shows loading state during hydration (`_hydrating = true`)
- Canvas blocked from interaction until hydration complete (no hidden writes)

#### Frontend — LabShell (`LabShell.tsx`)
- Add save state badge to Context Bar: "Saved", "Saving…", "Unsaved", "Save Error"
- Save error → show red badge + toast notification
- Compile handler: no longer creates new graph (relies on `activeGraphId` from mount hydration)

### Verification
- Typecheck passes
- Lint passes (if configured)
- Existing tests pass (if any graph-related tests exist)
- Backend + frontend build checks pass
- Manual verification (see §6)

### Handover
- `docs/steps/23a-lab-phase3a-graph-persistence.md` updated with COMPLETE status
- Git commit SHA recorded
- 23b1 ready to begin

---

## 5. Acceptance Checks

1. Open `/lab/build` with existing persisted graph → graph hydrates, nodes/edges visible
2. Open `/lab/build` with no persisted graph → first draft created, empty canvas
3. Add/move/delete node → autosave fires after 1500ms debounce
4. Reload page → graph state persists correctly
5. Undo/redo → each undo/redo triggers autosave debounce
6. Compile still works after persisted reload (compile uses existing `activeGraphId`)
7. Save failure → red badge visible in Context Bar, non-silent
8. Switch between graphs (if multiple) → dirty state flushed before switch, no silent loss
9. `saveState` never changes `validationState`
10. `saveState` never changes `compileState`
11. Hydration does not trigger autosave (no spurious PATCH on initial load)
12. All existing flows (validate, compile, backtest, DSL preview, `/lab/data`, `/lab/test`) still work

---

## 6. Review Checklist

- [ ] Backend PATCH endpoint validates workspace ownership
- [ ] Backend PATCH endpoint does not allow mutation of `workspaceId` or other protected fields
- [ ] Auto-save does not fire when `_hydrating = true`
- [ ] `saveState` transitions are correct: dirty → saving → clean | save_error
- [ ] `saveState` is excluded from `compileState` logic
- [ ] `saveState` is excluded from `validationState` logic
- [ ] Compile flow does not create new graph if `activeGraphId` is already set
- [ ] Graph switch flushes or confirms dirty state (no silent data loss)
- [ ] Save error is visible (UI badge + non-silent)
- [ ] `_hydrating` is excluded from undo history (zundo `partialize`)
- [ ] `saveState` is excluded from undo history
- [ ] No deploy instructions or artifacts created
- [ ] No expansion-layer scope included

---

## 7. Exit Criteria

Phase 3A is complete when:
1. All acceptance checks pass
2. All review checklist items pass
3. `docs/steps/23a-lab-phase3a-graph-persistence.md` updated to `Status: COMPLETE`
4. Commit SHA recorded in this document
5. No regressions in existing graph/build/test/data flows
6. Typecheck and lint pass

**Commit SHA:** `0197ec3`
