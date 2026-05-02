# Strategy Capability Matrix

> Source of truth: `apps/api/src/lib/compiler/supportMap.ts`
> Contract tests: `apps/api/tests/compiler/blockDrift.test.ts`
> Last updated: 2026-04-11 (Phase 6 continuation — 23b2/23b3/23b4 + trailing_stop/close)

## Overview

This document tracks the support status of every block type available in the
Strategy Graph UI (`blockDefs.ts`) across the backend pipeline:
compiler (graph → DSL), and backtest runtime (DSL → execution).

The **authoritative source** for support status is `BLOCK_SUPPORT_MAP` in the
compiler module. This document is a human-readable companion. Contract tests
enforce that the code and this matrix stay in sync.

## Support Levels

| Status | Meaning |
|--------|---------|
| **supported** | Compiler handler exists AND backtest runtime can execute strategies using this block |
| **compile-only** | Compiler handler extracts DSL data, but the backtest runtime does not yet execute it |
| **unsupported** | No compiler handler — block cannot be compiled at all |

## Block Capability Matrix

### Input Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `candles` | ✅ | ✅ | ✅ | **supported** | Core input block, since Phase 3 |
| `constant` | ✅ | ✅ | ✅ | **supported** | Evaluator runtime wired in dslEvaluator |
| `orders_history` | ✅ | ✅ | ✅ | **supported** | Exchange orders history, requires ExchangeConnection (Phase 6 23b3) |
| `executions_history` | ✅ | ✅ | ✅ | **supported** | Exchange executions history, requires ExchangeConnection (Phase 6 23b3) |

### Indicator Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `SMA` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `EMA` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `RSI` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `macd` | ✅ | ✅ | ✅ | **supported** | MACD histogram in evaluator, calcMACD |
| `bollinger` | ✅ | ✅ | ✅ | **supported** | BB lower/upper/middle in evaluator |
| `atr` | ✅ | ✅ | ✅ | **supported** | ATR in evaluator runtime |
| `volume` | ✅ | ✅ | ✅ | **supported** | Volume series from candles |
| `vwap` | ✅ | ✅ | ✅ | **supported** | Session-anchored VWAP #125/#126 |
| `adx` | ✅ | ✅ | ✅ | **supported** | ADX + +DI/-DI #125/#126 |
| `supertrend` | ✅ | ✅ | ✅ | **supported** | ATR-based trend indicator #125/#126 |
| `volume_profile` | ✅ | ✅ | ✅ | **supported** | POC/VAH/VAL in evaluator #135 |

### Logic Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `compare` | ✅ | ✅ | ✅ | **supported** | Since Phase 4 |
| `cross` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `and_gate` | ✅ | ✅ | ✅ | **supported** | Recursive evaluateSignal, conditions.every() |
| `or_gate` | ✅ | ✅ | ✅ | **supported** | Recursive evaluateSignal, conditions.some() |
| `confirm_n_bars` | ✅ | ✅ | ✅ | **supported** | Signal must be true for N consecutive bars (Task 25a) |
| `proximity_filter` | ✅ | ✅ | ✅ | **supported** | Gates signals by proximity to level #135 |
| `annotate_event` | ✅ | ✅ | ✅ | **supported** | Event annotation on equity curve (Phase 6 23b4) |

### Execution Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `enter_long` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `enter_short` | ✅ | ✅ | ✅ | **supported** | Since Phase 4 |
| `enter_adaptive` | ✅ | ✅ | ✅ | **supported** | DSL v2 sideCondition, #130 |
| `close_position` | ✅ | ✅ | ✅ | **supported** | Explicit position close on signal (Phase 6) |

### Risk Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `stop_loss` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `take_profit` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `dca_config` | ✅ | ✅ | ✅ | **supported** | DCA ladder config, #132/#133 |
| `trailing_stop` | ✅ | ✅ | ✅ | **supported** | Trailing stop loss, exitEngine.ts runtime (Phase 6) |

### SMC Pattern Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `liquidity_sweep` | ✅ | ✅ | ✅ | **supported** | Swing sweep detection, pattern engine #137/#138 |
| `fair_value_gap` | ✅ | ✅ | ✅ | **supported** | 3-candle imbalance detection #137/#138 |
| `order_block` | ✅ | ✅ | ✅ | **supported** | Institutional OB detection #137/#138 |
| `market_structure_shift` | ✅ | ✅ | ✅ | **supported** | BOS/CHoCH detection #137/#138 |

## Implemented Strategy Presets

> Source of truth: `apps/api/prisma/seed/presets/<slug>.json` (DSL + default config)
> Golden fixtures: `apps/api/tests/fixtures/strategies/<slug>.golden.json`
>
> Each preset below is built entirely on top of the `supported` blocks above —
> no preset is allowed to depend on a `compile-only` block. The status column
> tracks delivery into Lab Library, not the underlying block runtime.

| Preset | Visibility | Timeframe(s) | Status | Plan |
|---|---|---|---|---|
| `adaptive-regime` | PUBLIC | M5 (single-TF, with H1/H4 regime refs via `sourceTimeframe`) | **delivered** | `docs/53` |
| `dca-momentum` | PUBLIC | M15 (single-TF) | **delivered** | `docs/54` |
| `mtf-scalper` | PUBLIC | M1 / M5 / M15 (multi-TF bundle) | **delivered** | `docs/54` |
| `smc-liquidity-sweep` | PUBLIC | M15 / H1 / H4 (multi-TF bundle, pattern blocks) | **delivered** | `docs/54` |
| `funding-arb` | _planned BETA_ | n/a (multi-leg perp + spot) | **in progress** | `docs/55` |

**Status legend (preset-level):**

| Status | Meaning |
|--------|---------|
| **delivered** | Preset shipped: DSL frozen via golden fixture, primitive-only construction verified by sanity tests, visible in Lab Library at the listed visibility. |
| **in progress** | DSL or runtime work landed on `main` but at least one closing task (acceptance run, BETA publish, etc.) is still open. See referenced plan for the open T-task list. |
| **planned** | Spec exists, no implementation work merged. |

## Summary

| Status | Count | Blocks |
|--------|------:|--------|
| **supported** | 33 | All blocks fully functional across UI → Compiler → Runtime |
| **compile-only** | 0 | — |
| **unsupported** | 0 | — |
| **Total** | 33 | |

## How Drift Detection Works

1. **UI block added without backend support** → contract test fails:
   - `"every UI block type has a compiler handler"` catches missing handler
   - `"every UI block type is listed in BLOCK_SUPPORT_MAP"` catches missing support entry

2. **Compiler handler added without UI block** → contract test fails:
   - `"every compiler handler corresponds to a UI block"` catches orphaned handlers

3. **Support map out of sync** → contract test fails:
   - `"support map has exactly the same block types as UI"` catches any mismatch
   - Snapshot tests catch accidental status changes

4. **Category mismatch** → contract test fails:
   - `"compiler handler category matches UI block category"` catches inconsistencies

## Adding a New Block

1. Add the block definition to `apps/web/src/app/lab/build/blockDefs.ts`
2. Create a `BlockHandler` in `apps/api/src/lib/compiler/blockHandlers.ts`
3. Register it in `defaultHandlers()`
4. Add an entry to `BLOCK_SUPPORT_MAP` in `apps/api/src/lib/compiler/supportMap.ts`
5. Update the snapshot test expectations in `blockDrift.test.ts`
6. Update this document
7. Run `pnpm --filter @botmarketplace/api test` to verify

## Promoting a Block from compile-only → supported

1. Implement runtime execution in the backtest engine
2. Update the status in `BLOCK_SUPPORT_MAP`
3. Update the snapshot test expectations
4. Update this document
