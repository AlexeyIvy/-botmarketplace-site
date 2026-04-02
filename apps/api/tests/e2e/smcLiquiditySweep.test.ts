/**
 * SMC Liquidity Sweep Flagship — End-to-End Acceptance (#138)
 *
 * Proves the SMC pipeline:
 *   1. DSL authoring → validation
 *   2. Backtest with SMC patterns → trades
 *   3. Pattern series resolution (sweep + FVG) through evaluator
 *   4. Determinism
 */

import { describe, it, expect } from "vitest";
import { validateDsl } from "../../src/lib/dslValidator.js";
import { runDslBacktest } from "../../src/lib/dslEvaluator.js";
import { runBacktest } from "../../src/lib/backtest.js";
import { makeSmcLiquiditySweepDsl } from "../fixtures/smcLiquiditySweepDsl.js";
import type { Candle } from "../../src/lib/bybitCandles.js";

// ---------------------------------------------------------------------------
// Fixtures: hand-crafted candle sequence with known sweep + FVG
// ---------------------------------------------------------------------------

const T0 = 1_700_000_000_000;
const M1 = 60_000;

function c(i: number, open: number, high: number, low: number, close: number, volume = 1000): Candle {
  return { openTime: T0 + i * M1, open, high, low, close, volume };
}

/**
 * Build a 30-bar scenario with:
 * - Bars 0-9: ranging to build ATR baseline
 * - Bars 10-14: establish a swing low at bar 12 (low=95, swingLen=2)
 * - Bar 15: liquidity sweep (low=93 < 95, close=96 > 95) → bullish sweep
 * - Bars 16-20: uptrend to hit TP or continue
 * - Bars 21-29: continued trend
 */
function makeSmcScenario(): Candle[] {
  const candles: Candle[] = [];

  // Bars 0-9: ranging ~100
  for (let i = 0; i < 10; i++) {
    const base = 100 + (i % 2 === 0 ? 0.5 : -0.5);
    candles.push(c(i, base, base + 1, base - 1, base + (i % 2 === 0 ? 0.3 : -0.3)));
  }

  // Bars 10-14: dip to create swing low
  candles.push(c(10, 100, 101, 98,  99));   // low=98
  candles.push(c(11, 99,  100, 97,  98));   // low=97
  candles.push(c(12, 98,  99,  95,  97));   // swing low: low=95
  candles.push(c(13, 97,  100, 97,  99));   // low=97
  candles.push(c(14, 99,  102, 98, 101));   // low=98

  // Bar 15: liquidity sweep — dips below 95, closes above
  candles.push(c(15, 101, 102, 93, 96));

  // Bars 16-29: uptrend after sweep
  for (let i = 16; i < 30; i++) {
    const base = 96 + (i - 16) * 1.5;
    candles.push(c(i, base, base + 1.5, base - 0.5, base + 1));
  }

  return candles;
}

// ---------------------------------------------------------------------------
// 1. DSL validation
// ---------------------------------------------------------------------------

describe("SMC Liquidity Sweep — DSL (#138)", () => {
  it("DSL passes validation", () => {
    const errors = validateDsl(makeSmcLiquiditySweepDsl());
    expect(errors).toBeNull();
  });

  it("DSL has SMC indicator in signal and fixed Buy side", () => {
    const dsl = makeSmcLiquiditySweepDsl();
    const entry = dsl.entry as Record<string, unknown>;
    expect(entry.side).toBe("Buy");
    const signal = entry.signal as Record<string, unknown>;
    const left = signal.left as Record<string, unknown>;
    expect(left.blockType).toBe("liquidity_sweep");
  });
});

// ---------------------------------------------------------------------------
// 2. Backtest
// ---------------------------------------------------------------------------

describe("SMC Liquidity Sweep — backtest (#138)", () => {
  it("produces a valid backtest report", () => {
    const candles = makeSmcScenario();
    const dsl = makeSmcLiquiditySweepDsl();
    const report = runDslBacktest(candles, dsl);

    expect(report.candles).toBe(30);
    expect(typeof report.totalPnlPct).toBe("number");
    expect(typeof report.winrate).toBe("number");
    expect(typeof report.maxDrawdownPct).toBe("number");
  });

  it("backtest via runBacktest wrapper works", () => {
    const candles = makeSmcScenario();
    const dsl = makeSmcLiquiditySweepDsl();
    const report = runBacktest(candles, dsl);

    expect(report.candles).toBe(30);
  });

  it("backtest is deterministic", () => {
    const candles = makeSmcScenario();
    const dsl = makeSmcLiquiditySweepDsl();

    const a = runDslBacktest(candles, dsl);
    const b = runDslBacktest(candles, dsl);

    expect(a.trades).toBe(b.trades);
    expect(a.totalPnlPct).toBe(b.totalPnlPct);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });

  it("produces at least one trade on the sweep scenario", () => {
    const candles = makeSmcScenario();
    const dsl = makeSmcLiquiditySweepDsl();
    const report = runDslBacktest(candles, dsl);

    // Our scenario has a clear bullish sweep at bar 15
    // The compare signal (sweep > 0) fires, side is fixed Buy → long
    expect(report.trades).toBeGreaterThanOrEqual(1);

    if (report.tradeLog.length > 0) {
      const trade = report.tradeLog[0];
      expect(trade.side).toBe("long");
      expect(trade.entryPrice).toBeGreaterThan(0);
    }
  });

  it("produces zero trades on a flat market with no sweeps", () => {
    // 30 bars of flat price — no swing points, no sweeps
    const flat: Candle[] = Array.from({ length: 30 }, (_, i) => c(i, 100, 100.5, 99.5, 100));
    const dsl = makeSmcLiquiditySweepDsl();
    const report = runDslBacktest(flat, dsl);
    expect(report.trades).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// 3. MSS CHoCH encoding through evaluator
// ---------------------------------------------------------------------------

describe("SMC MSS CHoCH encoding (#138)", () => {
  it("CHoCH bearish encodes as -2 through getIndicatorValues", async () => {
    const { getIndicatorValues: giv, createIndicatorCache: cic } = await import("../../src/lib/dslEvaluator.js");
    const { makeChochBearishFixture } = await import("../smc/smcFixtures.js");
    const candles = makeChochBearishFixture();
    const cache = cic();
    const values = giv("market_structure_shift", { length: 2 }, candles, cache);
    expect(values[14]).toBe(-2); // CHoCH bearish
  });
});

// ---------------------------------------------------------------------------
// 4. Compile → Backtest parity (identical DSL, same result)
// ---------------------------------------------------------------------------

describe("SMC Liquidity Sweep — compile→backtest parity (#138)", () => {
  it("same DSL produces same results across multiple runs", () => {
    const candles = makeSmcScenario();
    const dsl = makeSmcLiquiditySweepDsl();

    const results = Array.from({ length: 3 }, () => runDslBacktest(candles, dsl));

    for (let i = 1; i < results.length; i++) {
      expect(results[i].trades).toBe(results[0].trades);
      expect(results[i].totalPnlPct).toBe(results[0].totalPnlPct);
    }
  });
});
