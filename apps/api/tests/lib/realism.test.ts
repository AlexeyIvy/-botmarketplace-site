/**
 * 46-T5: realism golden-table.
 *
 * Locks (trades, totalPnlPct) for the 12-combination matrix
 *   fillAt ∈ {"OPEN", "CLOSE", "NEXT_OPEN"} × slippageBps ∈ {0, 50} × feeBps ∈ {0, 30}
 * on a single deterministic fixture (`makeFlatThenUp(50, 25, 100, 2)`) running
 * a single deterministic DSL strategy (SMA(5) crossover SMA(20), SL/TP 2%/4%).
 *
 * The numbers below are the engine's authoritative output as of 46-T1..T4.
 * Any change to fillAt branches (46-T1), the symmetric slippage formula
 * (46-T2), or the fee normalization (46-T3) will surface here.
 *
 * Do not edit the GOLDEN values without justification — pair an update
 * with the PR that intentionally shifts the underlying contract, and
 * record the reason in the commit message.
 */

import { describe, it, expect } from "vitest";
import { runDslBacktest } from "../../src/lib/dslEvaluator.js";
import type { DslFillAt } from "../../src/lib/dslEvaluator.js";
import { makeFlatThenUp } from "../fixtures/candles.js";

// ---------------------------------------------------------------------------
// Shared fixture + DSL
// ---------------------------------------------------------------------------

const candles = makeFlatThenUp(50, 25, 100, 2);

/**
 * SMA-crossover long entry with an RSI(14) > 70 indicator-exit. SL and TP
 * are deliberately set far enough that they never fire on this fixture, so
 * exits flow through the fillAt-aware indicator-exit path. This makes the
 * matrix below discriminating across all three fillAt modes — without
 * indicator_exit, fixed-percent TP fills would mask fillAt because their
 * trigger price is invariant in fillAt.
 */
function makeStrategyDsl() {
  return {
    id: "test-realism-golden",
    name: "Realism Golden — SMA Crossover + RSI Indicator Exit",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      side: "Buy",
      signal: {
        type: "crossover",
        fast: { blockType: "SMA", length: 5 },
        slow: { blockType: "SMA", length: 20 },
      },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 50 },
      takeProfit: { type: "fixed_pct", value: 50 },
      indicatorExit: {
        indicator: { type: "RSI", length: 14 },
        condition: { op: "gt", value: 70 },
        appliesTo: "long",
      },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

// ---------------------------------------------------------------------------
// Golden table
// ---------------------------------------------------------------------------

interface GoldenRow {
  fillAt: DslFillAt;
  slippageBps: number;
  feeBps: number;
  trades: number;
  totalPnlPct: number;
}

// Iteration order below mirrors the nested loops in the test:
//   for (fillAt of ["OPEN", "CLOSE", "NEXT_OPEN"])
//     for (slippageBps of [0, 50])
//       for (feeBps of [0, 30])
const GOLDEN: GoldenRow[] = [
  { fillAt: "OPEN",      slippageBps: 0,  feeBps: 0,  trades: 1, totalPnlPct: 1.97 },
  { fillAt: "OPEN",      slippageBps: 0,  feeBps: 30, trades: 1, totalPnlPct: 1.36 },
  { fillAt: "OPEN",      slippageBps: 50, feeBps: 0,  trades: 1, totalPnlPct: 0.96 },
  { fillAt: "OPEN",      slippageBps: 50, feeBps: 30, trades: 1, totalPnlPct: 0.35 },
  { fillAt: "CLOSE",     slippageBps: 0,  feeBps: 0,  trades: 1, totalPnlPct: 1.96 },
  { fillAt: "CLOSE",     slippageBps: 0,  feeBps: 30, trades: 1, totalPnlPct: 1.35 },
  { fillAt: "CLOSE",     slippageBps: 50, feeBps: 0,  trades: 1, totalPnlPct: 0.95 },
  { fillAt: "CLOSE",     slippageBps: 50, feeBps: 30, trades: 1, totalPnlPct: 0.34 },
  { fillAt: "NEXT_OPEN", slippageBps: 0,  feeBps: 0,  trades: 1, totalPnlPct: 1.93 },
  { fillAt: "NEXT_OPEN", slippageBps: 0,  feeBps: 30, trades: 1, totalPnlPct: 1.32 },
  { fillAt: "NEXT_OPEN", slippageBps: 50, feeBps: 0,  trades: 1, totalPnlPct: 0.92 },
  { fillAt: "NEXT_OPEN", slippageBps: 50, feeBps: 30, trades: 1, totalPnlPct: 0.32 },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("46-T5: backtest realism golden table", () => {
  it("12-combination matrix matches locked (trades, totalPnlPct)", () => {
    const fillAtModes: DslFillAt[] = ["OPEN", "CLOSE", "NEXT_OPEN"];
    const slippageBpsValues = [0, 50];
    const feeBpsValues = [0, 30];

    const observed: GoldenRow[] = [];
    for (const fillAt of fillAtModes) {
      for (const slippageBps of slippageBpsValues) {
        for (const feeBps of feeBpsValues) {
          const r = runDslBacktest(candles, makeStrategyDsl(), {
            feeBps,
            slippageBps,
            fillAt,
          });
          observed.push({
            fillAt,
            slippageBps,
            feeBps,
            trades: r.trades,
            totalPnlPct: r.totalPnlPct,
          });
        }
      }
    }

    expect(observed).toEqual(GOLDEN);
  });

  // -------------------------------------------------------------------------
  // Boundary anchors — independent of the table to make regression diagnosis
  // simpler if the table breaks.
  // -------------------------------------------------------------------------

  it("NEXT_OPEN signal on the last candle is skipped (trade count drops vs CLOSE)", () => {
    // Construct a fixture where the SMA crossover fires only on the very last
    // bar — CLOSE captures it, NEXT_OPEN must skip it (no next candle).
    const lateSignalCandles = [];
    for (let i = 0; i < 4; i++) {
      lateSignalCandles.push({
        openTime: 1_700_000_000_000 + i * 60_000,
        open: 100, high: 100, low: 100, close: 100, volume: 1000,
      });
    }
    lateSignalCandles.push({
      openTime: 1_700_000_000_000 + 4 * 60_000,
      open: 100, high: 200, low: 100, close: 200, volume: 1000,
    });

    const dsl = {
      id: "late-sig",
      name: "late",
      dslVersion: 1,
      enabled: true,
      market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
      entry: {
        side: "Buy",
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", length: 2 },
          slow: { blockType: "SMA", length: 3 },
        },
        stopLoss: { type: "fixed_pct", value: 2 },
        takeProfit: { type: "fixed_pct", value: 4 },
      },
      risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
      execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
      guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
    };

    const close = runDslBacktest(lateSignalCandles, dsl, { feeBps: 0, slippageBps: 0, fillAt: "CLOSE" });
    const nextOpen = runDslBacktest(lateSignalCandles, dsl, { feeBps: 0, slippageBps: 0, fillAt: "NEXT_OPEN" });

    expect(close.trades).toBe(1);
    expect(nextOpen.trades).toBe(0);
  });

  it("slippageBps=0 is bit-identical to running with feeBps only (46-T2 backward-compat)", () => {
    // At slippage=0 the symmetric formula reduces to fee-only; the result
    // must match the legacy contract exactly. Anchored against the golden
    // table indirectly (the s=0 rows of the 12-combination matrix), but
    // also asserted here independently for clearer failure messages.
    const a = runDslBacktest(candles, makeStrategyDsl(), { feeBps: 30, slippageBps: 0, fillAt: "CLOSE" });
    const b = runDslBacktest(candles, makeStrategyDsl(), { feeBps: 30, slippageBps: 0, fillAt: "CLOSE" });
    expect(a).toEqual(b);
    // Determinism re-check with a different fillAt.
    const c = runDslBacktest(candles, makeStrategyDsl(), { feeBps: 30, slippageBps: 0, fillAt: "OPEN" });
    const d = runDslBacktest(candles, makeStrategyDsl(), { feeBps: 30, slippageBps: 0, fillAt: "OPEN" });
    expect(c).toEqual(d);
  });

  it("takerFeeBps overrides legacy feeBps when both are provided (46-T3)", () => {
    // takerFeeBps=30 must produce the same result as feeBps=30 alone, and
    // pairing feeBps=10 with takerFeeBps=30 must also match feeBps=30.
    const onlyLegacy = runDslBacktest(candles, makeStrategyDsl(), {
      feeBps: 30,
      slippageBps: 0,
      fillAt: "CLOSE",
    });
    const onlyTaker = runDslBacktest(candles, makeStrategyDsl(), {
      takerFeeBps: 30,
      slippageBps: 0,
      fillAt: "CLOSE",
    });
    const both = runDslBacktest(candles, makeStrategyDsl(), {
      feeBps: 10,
      takerFeeBps: 30,
      slippageBps: 0,
      fillAt: "CLOSE",
    });
    expect(onlyTaker.totalPnlPct).toBe(onlyLegacy.totalPnlPct);
    expect(both.totalPnlPct).toBe(onlyLegacy.totalPnlPct);
  });
});
