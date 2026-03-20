# Strategy Capability Matrix

> Source of truth: `apps/api/src/lib/compiler/supportMap.ts`
> Contract tests: `apps/api/tests/compiler/blockDrift.test.ts`
> Last updated: 2026-03-20 (Issue #123)

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
| `constant` | ✅ | ✅ | ❌ | compile-only | Compiler extracts value; runtime pending (#124) |

### Indicator Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `SMA` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `EMA` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `RSI` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `macd` | ✅ | ✅ | ❌ | compile-only | Handler added #122; runtime pending (#125) |
| `bollinger` | ✅ | ✅ | ❌ | compile-only | Handler added #122; runtime pending (#125) |
| `atr` | ✅ | ✅ | ❌ | compile-only | Handler added #122; runtime pending (#125) |
| `volume` | ✅ | ✅ | ❌ | compile-only | Handler added #122; runtime pending (#125) |

### Logic Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `compare` | ✅ | ✅ | ✅ | **supported** | Since Phase 4 |
| `cross` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `and_gate` | ✅ | ✅ | ❌ | compile-only | Handler added #122; runtime pending (#124) |
| `or_gate` | ✅ | ✅ | ❌ | compile-only | Handler added #122; runtime pending (#124) |

### Execution Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `enter_long` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `enter_short` | ✅ | ✅ | ✅ | **supported** | Since Phase 4 |

### Risk Blocks

| Block | UI | Compiler | Runtime | Status | Notes |
|-------|:--:|:--------:|:-------:|--------|-------|
| `stop_loss` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |
| `take_profit` | ✅ | ✅ | ✅ | **supported** | Since Phase 3 |

## Summary

| Status | Count | Blocks |
|--------|------:|--------|
| **supported** | 10 | candles, SMA, EMA, RSI, compare, cross, enter_long, enter_short, stop_loss, take_profit |
| **compile-only** | 7 | constant, macd, bollinger, atr, volume, and_gate, or_gate |
| **unsupported** | 0 | — |
| **Total** | 17 | |

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
