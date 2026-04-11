# Expansion Layer — Task Breakdown (Post Phase 6 Completion)

**Project:** BotMarketplace Lab v2
**Repository:** `AlexeyIvy/-botmarketplace-site`
**Created:** 2026-04-11
**Status:** Active — execution starts with task pack 26
**Depends on:** Completion layer fully accepted (23a, 23b1-23b4 all merged)
**Parent doc:** `docs/24-lab-post-phase-5-roadmap.md` §8-§9

---

## Current state (baseline)

| Metric | Value |
|--------|-------|
| HEAD on main | `db8745e` (docs update post Phase 6) |
| Block count | 33 supported (UI → Compiler → Runtime) |
| Tests | 1568 passing (1 pre-existing: positionManager Prisma module) |
| Smoke tests | 88/88 green |
| Completion layer | 5/5 task packs merged (23a, 23b1, 23b2, 23b3, 23b4) |
| Expansion layer | 25b done; 25a mostly done (1 block missing) |

---

## Task packs — execution order

### Task 26 — Governance / Provenance ✅ DONE

**Priority:** HIGH (next in chain)
**Depends on:** 23b1 (Compare Runs) ✅ done
**Unblocks:** 27 (Parameter sweep), 28 (Research journal), 29 (AI explainability)
**Status:** Completed — PR #245

**Scope:**

1. **Version labels** ✅ — user can attach a label to a `StrategyGraphVersion`
   - UI: label input field in LabShell context bar after compile success (inline edit, max 100 chars)
   - API: `PATCH /api/v1/lab/graph-versions/:id` with `{ label: string | null }`
   - Schema: `label String?` column added to `StrategyGraphVersion`
   - Display: label shown in ProvenanceBlock (Compare Runs + Metrics tab)

2. **Baseline designation** ✅ — user marks one compiled version as baseline
   - UI: "Set baseline" toggle button in LabShell context bar after compile
   - API: `POST /api/v1/lab/graph-versions/:id/baseline` (toggle; clears previous per strategy)
   - Schema: `isBaseline Boolean @default(false)` on `StrategyGraphVersion`
   - Display: BASELINE badge in ProvenanceBlock; golden border highlight

3. **Lineage display** ✅ — results view shows provenance chain
   - Compare Runs: enriched response with `lineage` object (graphName, label, isBaseline, graphVersion)
   - ProvenanceBlock extended: shows Graph name, Label, Graph version, BASELINE badge
   - Metrics tab: inline ProvenanceBlock for single-run lineage context
   - New: `GET /lab/graph-versions?graphId=X` lists all compiled versions with governance fields

**Key files:**
- `apps/web/src/app/lab/test/page.tsx` — ProvenanceBlock + LineageInfo type + compare integration
- `apps/web/src/app/lab/LabShell.tsx` — label input + baseline button in context bar
- `apps/web/src/app/lab/labApi.ts` — patchGraphVersion, setGraphVersionBaseline helpers
- `apps/api/src/routes/lab.ts` — 3 new endpoints + enhanced compare response + graphVersionId in compile
- `apps/api/prisma/schema.prisma` — `StrategyGraphVersion` label + isBaseline
- `apps/api/tests/routes/lab.test.ts` — 20+ new route tests for governance endpoints

**Acceptance criteria:**
- [x] Version label editable after compile
- [x] Baseline designation toggleable (one per strategy)
- [x] Lineage block visible in Test tab results
- [x] Compare Runs shows lineage with label + baseline
- [x] All existing tests still pass + new route tests added
- [x] Migration runs cleanly on existing data (additive: nullable + default false)

---

### Task 27 — Parameter Sweep

**Priority:** HIGH
**Depends on:** 26 (Governance) ✅ done
**Status:** Completed — PR #246
**Note:** Backend endpoints already exist (`POST /lab/backtest/sweep`, `GET /lab/backtest/sweep/:id`, `GET /lab/backtest/sweeps`). UI skeleton exists in `OptimisePanel.tsx`.

**Scope:**

1. **Sweep form** — select one parameter, define range + step
   - Parameter picker: dropdown of all numeric params from current compiled strategy
   - Range inputs: start, end, step
   - Max runs cap: 20 (hard limit per docs/24 §8.3)
   - Validation: step > 0, (end - start) / step <= 20

2. **Sequential execution** — trigger N runs via existing sweep endpoint
   - Progress indicator (X/N completed)
   - Poll sweep status (reuse existing polling pattern from backtest)
   - Cancel support (optional, nice-to-have)

3. **Results table** — one row per run, columns = key metrics
   - Columns: param value, PnL %, winrate, max drawdown, trades
   - Sort by any column
   - Highlight best/worst per metric
   - Link each row to full backtest detail

**Key files:**
- `apps/web/src/app/lab/test/OptimisePanel.tsx` — main sweep UI
- `apps/api/src/routes/lab.ts` — sweep endpoints (already exist, verify)
- `apps/api/tests/routes/lab.test.ts` — sweep route tests

**Acceptance criteria:**
- [x] User can select one numeric parameter and define range/step
- [x] Sweep triggers sequential backtest runs (max 20)
- [x] Results table shows metrics per parameter value
- [x] Sorting and best/worst highlighting work
- [x] Click row → view full backtest detail (switches to backtest tab)
- [x] All existing tests pass + sweep tests updated

---

### Task 25a (completion) — confirm_n_bars Logic Block

**Priority:** MEDIUM
**Depends on:** — (independent)
**Status:** Completed — PR #247
**Note:** Only 1 block missing from the Tier 2 indicators/logic set.

**Scope:**

1. Add `confirm_n_bars` block to `blockDefs.ts`
   - Category: logic
   - Inputs: signal (Series\<boolean\>)
   - Outputs: confirmed (Series\<boolean\>)
   - Params: bars (number, default 3, min 1, max 50)
   - Description: "Requires signal to be true for N consecutive bars before firing."

2. Compiler handler in `blockHandlers.ts`
3. Register in `defaultHandlers()`
4. Add to `BLOCK_SUPPORT_MAP` in `supportMap.ts`
5. Update `blockDrift.test.ts` snapshot (33 → 34)
6. Update `docs/strategies/08-strategy-capability-matrix.md`
7. Update `docs/10-strategy-dsl.md` mapping table

**Acceptance criteria:**
- [x] Block appears in BlockPalette under Logic
- [x] Compiles to DSL
- [x] Contract tests pass (34 blocks)
- [x] Evaluator runtime: signal confirmed after N consecutive true bars
- [x] All existing tests pass + 6 new confirm_n_bars tests

---

### Task 28 — Research Journal

**Priority:** MEDIUM
**Depends on:** 26 (Governance)

**Scope:**

1. **Schema** — journal entry model
   - `LabJournalEntry`: id, strategyGraphVersionId, backtestResultId (nullable), hypothesis, whatChanged, expectedResult, actualResult, nextStep, status (baseline | promote | discard | keep_testing), createdAt, updatedAt
   - Prisma migration

2. **API endpoints**
   - `POST /api/v1/lab/journal` — create entry
   - `GET /api/v1/lab/journal?graphVersionId=X` — list entries
   - `PATCH /api/v1/lab/journal/:id` — update entry
   - `DELETE /api/v1/lab/journal/:id` — delete entry

3. **UI** — journal panel in Test tab
   - New tab "Journal" in ResultDetail tabs
   - Form: hypothesis, what_changed, expected_result fields
   - After backtest: actual_result, next_step, status dropdown
   - Read-only display alongside provenance block
   - Plain text only — no AI generation in this task pack

**Key files:**
- `prisma/schema.prisma` — new model
- `apps/api/src/routes/lab.ts` — journal endpoints
- `apps/web/src/app/lab/test/page.tsx` — Journal tab

**Acceptance criteria:**
- [ ] CRUD for journal entries works
- [ ] Journal entries linked to graph version and/or backtest result
- [ ] Journal tab visible in Test results view
- [ ] Status field filterable (baseline/promote/discard/keep_testing)
- [ ] All existing tests pass + journal route tests added

---

### Task 29 — AI Explainability

**Priority:** LOW
**Depends on:** 26 (Governance), 28 (Research journal)

**Scope:**

1. **Explain graph** — LLM summarizes strategy in plain language
   - Input: compiled DSL + graph structure
   - Output: 2-3 sentence strategy description
   - UI: "Explain" button in Build tab toolbar

2. **Explain validation issue** — LLM explains error + suggests fix
   - Input: validation issue + node context
   - Output: explanation + suggested action
   - UI: tooltip/popover on validation error badge

3. **Explain run delta** — LLM summarizes differences between two runs
   - Input: Compare Runs metrics + graph diff + parameter diff
   - Output: "What changed and likely why" summary
   - UI: panel below Compare Runs metrics table

4. **Suggest safer risk config** — flag risky SL/TP configurations
   - Input: current risk block params
   - Output: warning + suggested tighter bounds
   - UI: warning banner in Build tab inspector when editing risk blocks

**Hard safety boundaries (docs/24 §8.5):**
- No bypass of compiler — suggestions go through graph editor + compile flow
- No bypass of validation — AI cannot produce invalid graph states
- No trade execution — operates on backtest data only
- No secret access — no API keys, credentials, or private data beyond current session

**Key files:**
- New: `apps/api/src/lib/aiExplain.ts` — LLM integration module
- `apps/api/src/routes/lab.ts` — explain endpoints
- `apps/web/src/app/lab/build/page.tsx` — Explain button
- `apps/web/src/app/lab/test/page.tsx` — Run delta panel

**Acceptance criteria:**
- [ ] All 4 explain features produce useful output
- [ ] Safety boundaries enforced (no trade execution, no secrets, no validation bypass)
- [ ] Graceful degradation when LLM unavailable
- [ ] All existing tests pass

---

## Blocked tasks (gate conditions not met)

### Multi-dataset binding (task 30)

**Gate conditions — ALL must be met:**
- [ ] Phase 6 accepted ✅
- [ ] Governance (26) accepted and stable
- [ ] Compare/provenance workflows validated as useful
- [ ] Schema decision documented in docs/07

### DSL ↔ Graph bidirectional

**Gate conditions — ALL must be met:**
- [ ] Phase 3A accepted ✅
- [ ] Phase 6 accepted ✅
- [ ] Technical feasibility spike completed with written note

---

## Remaining spec'd blocks (not yet implemented)

From `docs/23 §6.3` — deferred to future expansion, no task pack assigned:

| Category | Blocks | Count |
|----------|--------|-------|
| Transform | merge, resample, filter, rolling_window, normalize, session_filter, shift_lag, aggregate | 8 |
| Indicator | custom_formula | 1 |
| Logic | threshold, if_else, debounce_cooldown | 3 |
| Execution | reduce, reverse, order_model, slippage_model, fee_model | 5 |
| Risk | max_drawdown_stop, daily_loss_stop, max_concurrent_positions, max_orders_per_minute, cooldown_after_loss | 5 |
| Debug | log_value, inspect_series, explain_branch, simulation_marker | 4 |
| **Total** | | **26** |

These blocks are not assigned to any task pack. They may be added incrementally as user needs emerge, following the standard "Adding a New Block" workflow in `docs/strategies/08-strategy-capability-matrix.md`.

---

## Execution rules (inherited from docs/24 §9)

1. **Sequential execution** — no task pack starts before its dependency is merged
2. **One PR per task pack** — no scope creep, no adjacent merging
3. **Acceptance checklist** — all items verified before merge
4. **Documentation** — updated in the same PR
5. **Tests** — all existing tests must pass + new tests for new features
