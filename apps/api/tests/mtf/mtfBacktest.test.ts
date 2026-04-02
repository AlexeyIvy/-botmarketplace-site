/**
 * MTF Backtest Integration Tests (#134 — Slice 3)
 *
 * Tests that runDslBacktest accepts optional MtfBacktestContext
 * and existing single-TF behavior is unchanged.
 */

import { describe, it, expect } from "vitest";
import { runDslBacktest } from "../../src/lib/dslEvaluator.js";
import { runBacktest } from "../../src/lib/backtest.js";
import { createCandleBundle, INTERVAL_MS, type Interval } from "../../src/lib/mtf/intervalAlignment.js";
import { makeFlatThenUp } from "../fixtures/candles.js";
import type { Candle } from "../../src/lib/bybitCandles.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const ALIGNED_START = 1700006400000;

function makeAlignedCandles(interval: Interval, count: number, startPrice = 100, step = 1): Candle[] {
  const ms = INTERVAL_MS[interval];
  return Array.from({ length: count }, (_, i) => ({
    openTime: ALIGNED_START + i * ms,
    open: startPrice + i * step - step * 0.3,
    high: startPrice + i * step + step * 0.5,
    low: startPrice + i * step - step * 0.5,
    close: startPrice + i * step,
    volume: 1000 + i,
  }));
}

function makeSmaLongDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    id: "test-mtf",
    name: "MTF Test",
    dslVersion: 1,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      side: "Buy",
      signal: {
        type: "crossover",
        fast: { blockType: "SMA", length: fastLen },
        slow: { blockType: "SMA", length: slowLen },
      },
      stopLoss: { type: "fixed_pct", value: slPct },
      takeProfit: { type: "fixed_pct", value: tpPct },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: slPct, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("MTF backtest — backward compatibility", () => {
  it("runDslBacktest works without mtfContext (existing behavior)", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl();
    const report = runDslBacktest(candles, dsl);

    expect(report.trades).toBeGreaterThanOrEqual(1);
    expect(report.candles).toBe(80);
  });

  it("runDslBacktest with undefined mtfContext behaves identically", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl();

    const a = runDslBacktest(candles, dsl, {});
    const b = runDslBacktest(candles, dsl, {}, undefined);

    expect(a.trades).toBe(b.trades);
    expect(a.totalPnlPct).toBe(b.totalPnlPct);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });

  it("runBacktest wrapper passes mtfContext through", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl();

    // No MTF context — should work identically
    const a = runBacktest(candles, dsl);
    const b = runBacktest(candles, dsl, {}, undefined);

    expect(a.trades).toBe(b.trades);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });
});

describe("MTF backtest — with CandleBundle", () => {
  it("accepts CandleBundle context without errors", () => {
    const c1m = makeAlignedCandles("1m", 80, 100, 1);
    const c5m = makeAlignedCandles("5m", 16, 100, 5);

    const bundle = createCandleBundle("1m", { "1m": c1m, "5m": c5m });
    const dsl = makeSmaLongDsl();

    // The DSL doesn't reference sourceTimeframe yet, so bundle is accepted but unused
    const report = runDslBacktest(c1m, dsl, {}, { bundle });

    expect(report.candles).toBe(80);
    // Should produce same results as without bundle (no sourceTimeframe in signals)
    const reportNoBundlе = runDslBacktest(c1m, dsl);
    expect(report.trades).toBe(reportNoBundlе.trades);
    expect(report.tradeLog).toEqual(reportNoBundlе.tradeLog);
  });

  it("is deterministic with MTF context", () => {
    const c1m = makeAlignedCandles("1m", 80, 100, 1);
    const c5m = makeAlignedCandles("5m", 16, 100, 5);
    const bundle = createCandleBundle("1m", { "1m": c1m, "5m": c5m });
    const dsl = makeSmaLongDsl();

    const a = runDslBacktest(c1m, dsl, {}, { bundle });
    const b = runDslBacktest(c1m, dsl, {}, { bundle });

    expect(a.trades).toBe(b.trades);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });
});
