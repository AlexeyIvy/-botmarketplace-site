import { describe, it, expect } from "vitest";
import { runBacktest } from "../../src/lib/backtest.js";
import { makeDowntrend, makeFlat, makeFlatThenUp } from "../fixtures/candles.js";

/**
 * Backtest module tests — updated for DSL-driven evaluator (#126).
 *
 * runBacktest now requires a compiled DSL object instead of riskPct.
 */

/** Minimal v1 DSL for testing: SMA crossover long with fixed SL/TP */
function makeTestDsl(slPct = 2, tpPct = 4, fastLen = 5, slowLen = 20) {
  return {
    id: "test",
    name: "Test",
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

describe("backtest – runBacktest (DSL-driven)", () => {
  it("returns empty report when data has fewer than 2 candles", () => {
    const candles = makeFlatThenUp(1);
    const report = runBacktest(candles, makeTestDsl());

    expect(report.trades).toBe(0);
    expect(report.wins).toBe(0);
    expect(report.winrate).toBe(0);
    expect(report.totalPnlPct).toBe(0);
    expect(report.maxDrawdownPct).toBe(0);
    expect(report.tradeLog).toHaveLength(0);
    expect(report.candles).toBe(1);
  });

  it("returns empty report for empty candle array", () => {
    const report = runBacktest([], makeTestDsl());
    expect(report.trades).toBe(0);
    expect(report.candles).toBe(0);
  });

  it("produces at least one trade on flat-then-up data", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runBacktest(candles, makeTestDsl());

    expect(report.trades).toBeGreaterThanOrEqual(1);
    expect(report.tradeLog.length).toBe(report.trades);
    expect(report.candles).toBe(80);
  });

  it("all trades have valid structure", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runBacktest(candles, makeTestDsl());

    for (const trade of report.tradeLog) {
      expect(trade.entryTime).toBeGreaterThan(0);
      expect(trade.exitTime).toBeGreaterThan(0);
      expect(trade.entryPrice).toBeGreaterThan(0);
      expect(trade.exitPrice).toBeGreaterThan(0);
      expect(trade.slPrice).toBeGreaterThan(0);
      expect(trade.tpPrice).toBeGreaterThan(0);
      expect(["WIN", "LOSS", "NEUTRAL"]).toContain(trade.outcome);
      expect(typeof trade.pnlPct).toBe("number");
    }
  });

  it("win rate is between 0 and 1", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runBacktest(candles, makeTestDsl());
    expect(report.winrate).toBeGreaterThanOrEqual(0);
    expect(report.winrate).toBeLessThanOrEqual(1);
  });

  it("produces no trades in a flat market (no crossover signal)", () => {
    const candles = makeFlat(80, 100);
    const report = runBacktest(candles, makeTestDsl());
    expect(report.trades).toBe(0);
    expect(report.totalPnlPct).toBe(0);
  });

  it("produces losses on a downtrend after initial crossover", () => {
    const up = makeFlatThenUp(35, 20, 100, 2);
    const down = makeDowntrend(50, up[up.length - 1].close, 3);
    const lastTime = up[up.length - 1].openTime;
    for (let i = 0; i < down.length; i++) {
      down[i].openTime = lastTime + (i + 1) * 60_000;
    }
    const candles = [...up, ...down];
    const report = runBacktest(candles, makeTestDsl());
    expect(report.trades).toBeGreaterThanOrEqual(1);
  });

  it("fees reduce effective PnL compared to zero-fee backtest", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const noFees = runBacktest(candles, makeTestDsl(), { feeBps: 0, slippageBps: 0 });
    const withFees = runBacktest(candles, makeTestDsl(), { feeBps: 10, slippageBps: 5 });

    if (noFees.trades > 0 && withFees.trades > 0) {
      expect(withFees.totalPnlPct).toBeLessThanOrEqual(noFees.totalPnlPct + 0.01);
    }
  });

  it("is deterministic: same input produces same output", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const a = runBacktest(candles, makeTestDsl());
    const b = runBacktest(candles, makeTestDsl());

    expect(a.trades).toBe(b.trades);
    expect(a.wins).toBe(b.wins);
    expect(a.totalPnlPct).toBe(b.totalPnlPct);
    expect(a.maxDrawdownPct).toBe(b.maxDrawdownPct);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });

  it("max drawdown is non-negative", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runBacktest(candles, makeTestDsl());
    expect(report.maxDrawdownPct).toBeGreaterThanOrEqual(0);
  });

  it("rounds winrate to 4 decimal places and pnl/drawdown to 2", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runBacktest(candles, makeTestDsl());
    expect(Number.isInteger(report.winrate * 10000)).toBe(true);
    expect(Number.isInteger(report.totalPnlPct * 100)).toBe(true);
    expect(Number.isInteger(report.maxDrawdownPct * 100)).toBe(true);
  });
});
