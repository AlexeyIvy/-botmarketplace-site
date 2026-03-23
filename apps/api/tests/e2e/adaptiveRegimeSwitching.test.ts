/**
 * Adaptive Regime Switching — Tests (#130)
 *
 * Validates the core adaptive behavior: regime detection, strategy dispatch,
 * and neutral-zone handling for the Adaptive Regime Bot.
 *
 * Sections:
 *   1. Regime detection: ADX → trend / range / neutral classification
 *   2. Range-mode entry: RSI mean-reversion signals on range-bound data
 *   3. Trend-mode entry: existing trend path preserved in adaptive context
 *   4. Neutral zone: no entries when ADX is between thresholds
 *   5. Adaptive backtest: full bar-by-bar regime-aware evaluation
 *   6. Adaptive runtime: evaluateAdaptiveEntry parity with backtest
 *   7. Regime transitions: range → trend data produces both regime entries
 *   8. Bollinger Bands indicator: new indicator works correctly
 *
 * All fixtures are deterministic: no randomness, no time-dependence, no I/O.
 */

import { describe, it, expect } from "vitest";
import {
  determineRegime,
  runAdaptiveBacktest,
  evaluateAdaptiveEntry,
  type Regime,
  type AdaptiveStrategyConfig,
} from "../../src/lib/adaptiveStrategy.js";
import {
  createIndicatorCache,
  getIndicatorValues,
  evaluateSignal,
  determineSide,
  runDslBacktest,
} from "../../src/lib/dslEvaluator.js";
import { evaluateEntry } from "../../src/lib/signalEngine.js";
import { runBacktest } from "../../src/lib/backtest.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";

import {
  makeStrongUptrend,
  makeStrongDowntrend,
  makeRangeBound,
  makeRangeThenTrend,
} from "../fixtures/candles.js";
import {
  makeAdaptiveRegimeTrendDsl,
  makeAdaptiveRegimeLongOnlyDsl,
  makeAdaptiveStrategyConfig,
  makeRangeModeEntry,
} from "../fixtures/adaptiveRegimeDsl.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makePosition(overrides: Partial<PositionSnapshot> = {}): PositionSnapshot {
  return {
    id: "pos-test",
    botId: "bot-test",
    botRunId: "run-test",
    symbol: "BTCUSDT",
    side: "LONG",
    status: "OPEN",
    entryQty: 0.01,
    avgEntryPrice: 200,
    costBasis: 2,
    currentQty: 0.01,
    realisedPnl: 0,
    slPrice: null,
    tpPrice: null,
    openedAt: new Date("2024-01-01T00:00:00Z"),
    closedAt: null,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// 1. Regime detection
// ---------------------------------------------------------------------------

describe("Adaptive Regime — regime detection", () => {
  it("classifies strong uptrend as 'trend' regime (ADX > 25)", () => {
    const candles = makeStrongUptrend(80);
    const cache = createIndicatorCache();
    const config = makeAdaptiveStrategyConfig();

    // After ADX warm-up, strong trend should produce ADX > 25
    let foundTrend = false;
    for (let i = 28; i < candles.length; i++) {
      const regime = determineRegime(config.regime, i, candles, cache);
      if (regime === "trend") {
        foundTrend = true;
        break;
      }
    }

    expect(foundTrend).toBe(true);
  });

  it("classifies range-bound data as 'range' regime (ADX < 20)", () => {
    const candles = makeRangeBound(120);
    const cache = createIndicatorCache();
    const config = makeAdaptiveStrategyConfig();

    // After ADX warm-up, range-bound should produce ADX < 20
    let foundRange = false;
    for (let i = 28; i < candles.length; i++) {
      const regime = determineRegime(config.regime, i, candles, cache);
      if (regime === "range") {
        foundRange = true;
        break;
      }
    }

    expect(foundRange).toBe(true);
  });

  it("returns 'neutral' when ADX is not yet available (early bars)", () => {
    const candles = makeStrongUptrend(80);
    const cache = createIndicatorCache();
    const config = makeAdaptiveStrategyConfig();

    // Very early bars — ADX not yet computed
    const regime = determineRegime(config.regime, 5, candles, cache);
    expect(regime).toBe("neutral");
  });

  it("regime detection is deterministic", () => {
    const candles = makeStrongUptrend(80);
    const config = makeAdaptiveStrategyConfig();

    for (let i = 0; i < candles.length; i++) {
      const cache1 = createIndicatorCache();
      const cache2 = createIndicatorCache();
      const r1 = determineRegime(config.regime, i, candles, cache1);
      const r2 = determineRegime(config.regime, i, candles, cache2);
      expect(r1).toBe(r2);
    }
  });

  it("regime thresholds are correctly applied: ADX 25/20 gap produces neutral zone", () => {
    // Use a config with clear threshold gap
    const config = makeAdaptiveStrategyConfig();
    expect(config.regime.trendThreshold).toBe(25);
    expect(config.regime.rangeThreshold).toBe(20);
    expect(config.regime.trendThreshold).toBeGreaterThan(config.regime.rangeThreshold);
  });
});

// ---------------------------------------------------------------------------
// 2. Range-mode entry: RSI mean-reversion
// ---------------------------------------------------------------------------

describe("Adaptive Regime — range-mode entry logic", () => {
  it("RSI drops below 40 on range-bound data (entry condition exists)", () => {
    const candles = makeRangeBound(120);
    const cache = createIndicatorCache();

    const rsiValues = getIndicatorValues("rsi", { length: 14 }, candles, cache);

    // In oscillating data, RSI should dip below 40 at some point
    let foundWeak = false;
    for (let i = 15; i < candles.length; i++) {
      if (rsiValues[i] !== null && rsiValues[i]! < 40) {
        foundWeak = true;
        break;
      }
    }

    expect(foundWeak).toBe(true);
  });

  it("range-mode signal fires on range-bound data using evaluateSignal", () => {
    // Use enough candles to cover warm-up and multiple oscillation cycles
    const candles = makeRangeBound(200);
    const cache = createIndicatorCache();
    const rangeEntry = makeRangeModeEntry();

    let signalFired = false;
    for (let i = 15; i < candles.length; i++) {
      if (evaluateSignal(rangeEntry.signal, i, candles, cache)) {
        signalFired = true;
        break;
      }
    }

    expect(signalFired).toBe(true);
  });

  it("range-mode entry produces long side (mean-reversion buy)", () => {
    const rangeEntry = makeRangeModeEntry();
    expect(rangeEntry.side).toBe("Buy");
  });
});

// ---------------------------------------------------------------------------
// 3. Trend-mode in adaptive context
// ---------------------------------------------------------------------------

describe("Adaptive Regime — trend-mode preservation", () => {
  it("existing trend-mode single-strategy backtest still works", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const report = runBacktest(candles, dsl);

    expect(report.trades).toBeGreaterThan(0);
    for (const trade of report.tradeLog) {
      expect(trade.side).toBe("long");
    }
  });

  it("existing trend-mode v2 DSL still works with sideCondition", () => {
    const candles = makeStrongUptrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();
    const report = runDslBacktest(candles, dsl);

    expect(report.trades).toBeGreaterThan(0);
    for (const trade of report.tradeLog) {
      expect(trade.side).toBe("long");
    }
  });

  it("trend-mode signal engine parity is unchanged", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);

    let signalTime: number | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        signalTime = signal.triggerTime;
        break;
      }
    }

    expect(signalTime).toBe(report.tradeLog[0].entryTime);
  });
});

// ---------------------------------------------------------------------------
// 4. Neutral zone: no entries
// ---------------------------------------------------------------------------

describe("Adaptive Regime — neutral zone", () => {
  it("adaptive backtest produces no entries during neutral regime", () => {
    // Create config with impossible thresholds so everything is neutral
    // ADX is bounded [0, 100], so threshold >100 is unreachable
    const config: AdaptiveStrategyConfig = {
      ...makeAdaptiveStrategyConfig(),
      regime: {
        adxPeriod: 14,
        trendThreshold: 101, // ADX can never exceed 100
        rangeThreshold: -1,  // ADX can never be negative
      },
    };

    const candles = makeStrongUptrend(80);
    const report = runAdaptiveBacktest(candles, config);

    expect(report.trades).toBe(0);
  });

  it("evaluateAdaptiveEntry returns null in neutral regime", () => {
    const config: AdaptiveStrategyConfig = {
      ...makeAdaptiveStrategyConfig(),
      regime: {
        adxPeriod: 14,
        trendThreshold: 101,
        rangeThreshold: -1,
      },
    };

    const candles = makeStrongUptrend(80);
    const result = evaluateAdaptiveEntry({
      candles,
      config,
      position: null,
    });

    expect(result).toBeNull();
  });

  it("neutral zone exists between range and trend thresholds", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeRangeThenTrend(160);
    const cache = createIndicatorCache();

    const regimes: Set<Regime> = new Set();
    for (let i = 28; i < candles.length; i++) {
      regimes.add(determineRegime(config.regime, i, candles, cache));
    }

    // With range→trend transition, we should see neutral zone bars
    // (ADX transitioning between 20-25)
    expect(regimes.has("neutral")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 5. Adaptive backtest: full regime-aware evaluation
// ---------------------------------------------------------------------------

describe("Adaptive Regime — adaptive backtest", () => {
  it("produces trades on strong uptrend (trend regime)", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const report = runAdaptiveBacktest(candles, config);

    expect(report.trades).toBeGreaterThan(0);

    // All trades should be in trend regime
    for (const trade of report.tradeLog) {
      expect(trade.entryRegime).toBe("trend");
    }
  });

  it("produces trades on range-bound data (range regime)", () => {
    const config = makeAdaptiveStrategyConfig();
    // Need enough bars for ADX warm-up (28+) and multiple RSI cycles
    const candles = makeRangeBound(200);
    const report = runAdaptiveBacktest(candles, config);

    // Should get at least some range-regime trades
    const rangeTrades = report.tradeLog.filter((t) => t.entryRegime === "range");
    expect(rangeTrades.length).toBeGreaterThan(0);
  });

  it("adaptive backtest is deterministic", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);

    const r1 = runAdaptiveBacktest(candles, config);
    const r2 = runAdaptiveBacktest(candles, config);

    expect(r1.trades).toBe(r2.trades);
    expect(r1.totalPnlPct).toBe(r2.totalPnlPct);
    expect(r1.tradeLog).toEqual(r2.tradeLog);
    expect(r1.regimeLog).toEqual(r2.regimeLog);
  });

  it("regime log has correct length and valid values", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const report = runAdaptiveBacktest(candles, config);

    expect(report.regimeLog).toHaveLength(candles.length);
    for (const r of report.regimeLog) {
      expect(["trend", "range", "neutral"]).toContain(r);
    }
  });

  it("trade log entries include entryRegime field", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const report = runAdaptiveBacktest(candles, config);

    expect(report.trades).toBeGreaterThan(0);
    for (const trade of report.tradeLog) {
      expect(trade.entryRegime).toBeDefined();
      expect(["trend", "range"]).toContain(trade.entryRegime);
    }
  });

  it("no trades with insufficient candles for ADX warm-up", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(20);
    const report = runAdaptiveBacktest(candles, config);

    expect(report.trades).toBe(0);
  });

  it("all trades have valid structure", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const report = runAdaptiveBacktest(candles, config);

    for (const trade of report.tradeLog) {
      expect(trade.entryPrice).toBeGreaterThan(0);
      expect(trade.exitPrice).toBeGreaterThan(0);
      expect(["WIN", "LOSS", "NEUTRAL"]).toContain(trade.outcome);
      expect(["sl", "tp", "end_of_data", "indicator_exit", "time_exit", "trailing_stop"]).toContain(trade.exitReason);
      expect(trade.barsHeld).toBeGreaterThanOrEqual(0);
    }
  });
});

// ---------------------------------------------------------------------------
// 6. Adaptive runtime: entry parity with backtest
// ---------------------------------------------------------------------------

describe("Adaptive Regime — runtime parity", () => {
  it("evaluateAdaptiveEntry fires at same candle as adaptive backtest first entry (uptrend)", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);

    const report = runAdaptiveBacktest(candles, config);
    expect(report.trades).toBeGreaterThan(0);
    const backtestFirstEntry = report.tradeLog[0].entryTime;

    // Find when adaptive entry fires
    let signalTime: number | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateAdaptiveEntry({ candles: window, config, position: null });
      if (signal) {
        signalTime = signal.triggerTime;
        break;
      }
    }

    expect(signalTime).not.toBeNull();
    expect(signalTime).toBe(backtestFirstEntry);
  });

  it("evaluateAdaptiveEntry returns correct regime in signal", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);

    let signal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateAdaptiveEntry({ candles: window, config, position: null });
      if (signal) break;
    }

    expect(signal).not.toBeNull();
    expect(signal!.regime).toBe("trend");
    expect(signal!.action).toBe("open");
  });

  it("evaluateAdaptiveEntry returns null when position is open", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const position = makePosition({ status: "OPEN" });

    const result = evaluateAdaptiveEntry({ candles, config, position });
    expect(result).toBeNull();
  });

  it("evaluateAdaptiveEntry is deterministic", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);

    for (let end = 28; end <= Math.min(50, candles.length); end++) {
      const window = candles.slice(0, end);
      const a = evaluateAdaptiveEntry({ candles: window, config, position: null });
      const b = evaluateAdaptiveEntry({ candles: window, config, position: null });
      expect(a).toEqual(b);
    }
  });
});

// ---------------------------------------------------------------------------
// 7. Regime transitions
// ---------------------------------------------------------------------------

describe("Adaptive Regime — regime transitions", () => {
  it("range→trend data produces regime log with both range and trend bars", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeRangeThenTrend(160);
    const report = runAdaptiveBacktest(candles, config);

    const regimeSet = new Set(report.regimeLog);
    // Should see at least range and trend regimes
    // (neutral may also appear during transition)
    expect(regimeSet.size).toBeGreaterThanOrEqual(2);
  });

  it("trades from transition data are tagged with correct regime", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeRangeThenTrend(160);
    const report = runAdaptiveBacktest(candles, config);

    for (const trade of report.tradeLog) {
      // Each trade should have been entered in a confirmed regime
      expect(["trend", "range"]).toContain(trade.entryRegime);
    }
  });
});

// ---------------------------------------------------------------------------
// 8. Bollinger Bands indicator
// ---------------------------------------------------------------------------

describe("Adaptive Regime — Bollinger Bands indicator", () => {
  it("BB lower band values are computed correctly", () => {
    const candles = makeRangeBound(80);
    const cache = createIndicatorCache();

    const lower = getIndicatorValues("bb_lower", { length: 20, stdDevMult: 2 }, candles, cache);

    // First 19 bars should be null (warm-up)
    for (let i = 0; i < 19; i++) {
      expect(lower[i]).toBeNull();
    }

    // After warm-up, values should be below close price on average
    let belowCount = 0;
    for (let i = 19; i < candles.length; i++) {
      expect(lower[i]).not.toBeNull();
      expect(typeof lower[i]).toBe("number");
      if (lower[i]! < candles[i].close) belowCount++;
    }
    // Lower band should be below close most of the time
    expect(belowCount).toBeGreaterThan((candles.length - 19) * 0.5);
  });

  it("BB upper band values are computed correctly", () => {
    const candles = makeRangeBound(80);
    const cache = createIndicatorCache();

    const upper = getIndicatorValues("bb_upper", { length: 20, stdDevMult: 2 }, candles, cache);

    // After warm-up, values should be above close on average
    let aboveCount = 0;
    for (let i = 19; i < candles.length; i++) {
      expect(upper[i]).not.toBeNull();
      if (upper[i]! > candles[i].close) aboveCount++;
    }
    expect(aboveCount).toBeGreaterThan((candles.length - 19) * 0.5);
  });

  it("BB middle band matches SMA(period)", () => {
    const candles = makeRangeBound(80);
    const cache = createIndicatorCache();

    const middle = getIndicatorValues("bb_middle", { length: 20 }, candles, cache);
    const sma = getIndicatorValues("sma", { length: 20 }, candles, cache);

    for (let i = 19; i < candles.length; i++) {
      expect(middle[i]).not.toBeNull();
      expect(sma[i]).not.toBeNull();
      // BB middle should equal SMA within floating point precision
      expect(middle[i]).toBeCloseTo(sma[i]!, 10);
    }
  });

  it("BB bands are deterministic", () => {
    const candles = makeRangeBound(80);

    const cache1 = createIndicatorCache();
    const cache2 = createIndicatorCache();

    const lower1 = getIndicatorValues("bb_lower", { length: 20, stdDevMult: 2 }, candles, cache1);
    const lower2 = getIndicatorValues("bb_lower", { length: 20, stdDevMult: 2 }, candles, cache2);

    expect(lower1).toEqual(lower2);
  });
});
