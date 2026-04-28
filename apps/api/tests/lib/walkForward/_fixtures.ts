/**
 * Shared candle + DSL fixtures for walk-forward unit tests.
 *
 * The split / run / aggregate test files each had their own ad-hoc setup
 * before 48-T7; this module centralises the common building blocks so a
 * change to the canonical shape only needs one edit.
 *
 * Do NOT edit these arrays/objects without justification — they back the
 * walk-forward unit tests' regression contract.
 */

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * 100 flat-price candles. Useful for split tests where price action is
 * irrelevant — we only assert on indices and ranges.
 */
export function makeFlatCandles(n: number): Candle[] {
  return Array.from({ length: n }, (_, i) => ({
    openTime: 1_700_000_000_000 + i * 60_000,
    open: 100,
    high: 100,
    low: 100,
    close: 100,
    volume: 1000,
  }));
}

/**
 * Minimal SMA crossover long DSL — matches makeSmaLongDsl in
 * dslEvaluator.test.ts so per-fold runs go through the same compiled
 * strategy as the rest of the test suite.
 */
export function smaLongDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    id: "wf-fixture-sma",
    name: "Walk-forward fixture SMA Long",
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
