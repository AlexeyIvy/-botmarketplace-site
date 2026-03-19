# Phase C1 — Parametric Optimisation (Grid Search)

**Date:** 2026-03-19
**Branch:** `claude/prepare-c1-prompt-DporU`
**Depends on:** Phase B2 (PR #110)
**Spec:** `docs/25-lab-improvements-plan.md` → Phase C1

---

## Summary

Phase C1 adds parametric optimisation (Grid Search) to the Research Lab.
Users can sweep one numeric block parameter over a range and compare
backtest results in a sortable table, finding optimal parameter values
without manual re-running.

---

## Tasks completed

| ID | Task | Status |
|----|------|--------|
| C1-1 | `BacktestSweep` Prisma model + migration | Done |
| C1-2 | `POST /api/v1/lab/backtest/sweep` endpoint | Done |
| C1-3 | `GET /api/v1/lab/backtest/sweep/:id` endpoint | Done |
| C1-4 | `OptimisePanel.tsx` frontend component | Done |
| C1-5 | Integrate "Optimise" sub-tab into Test page | Done |
| C1-6 | Step doc + build verification | Done |

---

## Backend changes

### New Prisma model: `BacktestSweep`

```prisma
enum SweepStatus {
  PENDING
  RUNNING
  DONE
  FAILED
}

model BacktestSweep {
  id                String      @id @default(cuid())
  workspaceId       String
  strategyVersionId String
  datasetId         String
  sweepParamJson    Json
  feeBps            Int
  slippageBps       Int
  status            SweepStatus @default(PENDING)
  progress          Int         @default(0)
  runCount          Int
  resultsJson       Json?
  bestParamValue    Float?
  createdAt         DateTime    @default(now())
  updatedAt         DateTime    @updatedAt

  workspace Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  @@index([workspaceId])
  @@index([workspaceId, createdAt(sort: Desc)])
}
```

### Migration

`20260319a_phase_c1_backtest_sweep`

### New API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/lab/backtest/sweep` | Start a parametric sweep |
| GET | `/api/v1/lab/backtest/sweep/:id` | Poll sweep status/results |
| GET | `/api/v1/lab/backtest/sweeps` | List sweeps for workspace |

### Guards

- `runCount > 50` → HTTP 422
- Max 2 concurrent sweeps per workspace → HTTP 429
- Rate limit: 5 POST/min per workspace

### Existing backtest endpoint

`POST /api/v1/lab/backtest` — **NOT modified**. The original backtest
flow is completely unaffected by these changes.

---

## Frontend changes

### New component: `OptimisePanel.tsx`

Location: `apps/web/src/app/lab/test/OptimisePanel.tsx`

Key state variables:
- `selectedBlockId` / `selectedParamName` — sweep target
- `rangeFrom` / `rangeTo` / `rangeStep` — sweep range
- `activeSweep` — current `SweepResult` being polled
- `sortKey` / `sortDir` — table sort state

Fetch calls:
- `POST /lab/backtest/sweep` — start sweep
- `GET /lab/backtest/sweep/:id` — poll (every 2s)

### Test page integration

"Run Backtest | Optimise" top-level tab bar added to `lab/test/page.tsx`.
The existing "Run Backtest" sub-tab is completely unaffected.

---

## Build verification

- `tsc --noEmit` (api): 0 errors
- `tsc --noEmit` (web): 0 errors
- `next build`: all 16 pages pass
- `npx prisma validate`: schema valid

---

## Files changed/created

### Created
- `apps/api/prisma/migrations/20260319a_phase_c1_backtest_sweep/migration.sql`
- `apps/web/src/app/lab/test/OptimisePanel.tsx`
- `docs/steps/25c1-lab-phase-c1-grid-search.md`

### Modified
- `apps/api/prisma/schema.prisma` — added `SweepStatus` enum, `BacktestSweep` model, `backtestSweeps` relation on `Workspace`
- `apps/api/src/routes/lab.ts` — added sweep endpoints + `runSweepAsync` + `computeSharpe`
- `apps/web/src/app/lab/test/page.tsx` — added top-level tab bar, imported `OptimisePanel`
