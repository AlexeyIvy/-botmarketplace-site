# Phase B2 — Block Library Expansion (MACD, Bollinger, ATR, Volume, AND, OR)

**Source:** `docs/25-lab-improvements-plan.md` Phase B2
**Depends on:** Phase B1 merged and deployed
**Scope:** FEAT-02 — 6 new block definitions in `blockDefs.ts`

---

## Tasks completed

### B2-1: MACD block

- Type: `macd` | Category: `indicator`
- Input: `price` (`Series<number>`)
- Outputs (3): `macd`, `signal`, `histogram` — all `Series<number>`
- Params: `fastPeriod` (12), `slowPeriod` (26), `signalPeriod` (9)

### B2-2: Bollinger Bands block

- Type: `bollinger` | Category: `indicator`
- Input: `candles` (`Series<OHLCV>`)
- Outputs (3): `upper`, `middle`, `lower` — all `Series<number>`
- Params: `period` (20), `stdDevMult` (2.0)

### B2-3: ATR block

- Type: `atr` | Category: `indicator`
- Input: `candles` (`Series<OHLCV>`)
- Output (1): `atr` (`Series<number>`)
- Params: `period` (14)

### B2-4: Volume block

- Type: `volume` | Category: `indicator`
- Input: `candles` (`Series<OHLCV>`)
- Output (1): `volume` (`Series<number>`)
- Params: none

### B2-5: AND gate

- Type: `and_gate` | Category: `logic`
- Inputs: `a`, `b` (`Series<boolean>`)
- Output (1): `out` (`Series<boolean>`)
- Params: none

### B2-6: OR gate

- Type: `or_gate` | Category: `logic`
- Inputs: `a`, `b` (`Series<boolean>`)
- Output (1): `out` (`Series<boolean>`)
- Params: none

---

## Files changed

| File | Change |
|------|--------|
| `apps/web/src/app/lab/build/blockDefs.ts` | Added 6 new block definitions (B2-1 through B2-6) |
| `docs/25-lab-improvements-plan.md` | Marked FEAT-02 and B2 acceptance checks as completed |
| `docs/steps/25b2-lab-phase-b2-block-library.md` | **NEW** — this step doc |

## validationTypes.ts — no changes needed

`validationTypes.ts` uses `BLOCK_DEF_MAP` dynamically to resolve block definitions at runtime. It does not contain a hardcoded list of block types. Adding new blocks to `BLOCK_DEFS` automatically makes them available to the validation engine — no code changes required in `validationTypes.ts`.

## Verification

- Total blocks in `blockDefs.ts`: **17** (10 original + 1 constant + 6 new)
- `grep` for all 6 types: all present in `blockDefs.ts`
- `tsc --noEmit` (web): **0 errors**
- `next build`: **success** (16/16 pages)
- No schema migrations
- No new API endpoints
- No new npm dependencies
