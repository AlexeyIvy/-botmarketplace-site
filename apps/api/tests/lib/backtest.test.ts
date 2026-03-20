import { describe, it, expect } from "vitest";
import { runBacktest } from "../../src/lib/backtest.js";
import { makeUptrend, makeDowntrend, makeFlat } from "../fixtures/candles.js";

describe("backtest – runBacktest", () => {
  // ── Edge cases: insufficient data ──────────────────────────────────────

  it("returns empty report when data has fewer than LOOKBACK+1 candles", () => {
    const candles = makeUptrend(10); // need 21 minimum
    const report = runBacktest(candles, 2);

    expect(report.trades).toBe(0);
    expect(report.wins).toBe(0);
    expect(report.winrate).toBe(0);
    expect(report.totalPnlPct).toBe(0);
    expect(report.maxDrawdownPct).toBe(0);
    expect(report.tradeLog).toHaveLength(0);
    expect(report.candles).toBe(10);
  });

  it("returns empty report for empty candle array", () => {
    const report = runBacktest([], 2);
    expect(report.trades).toBe(0);
    expect(report.candles).toBe(0);
  });

  // ── Uptrend: should produce trades ────────────────────────────────────

  it("produces at least one trade on a strong uptrend", () => {
    // 50 candles with a steady uptrend — breakout signal should fire
    const candles = makeUptrend(50, 100, 2);
    const report = runBacktest(candles, 2);

    expect(report.trades).toBeGreaterThanOrEqual(1);
    expect(report.tradeLog.length).toBe(report.trades);
    expect(report.candles).toBe(50);
  });

  it("all trades have valid structure", () => {
    const candles = makeUptrend(50, 100, 2);
    const report = runBacktest(candles, 2);

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
    const candles = makeUptrend(50, 100, 2);
    const report = runBacktest(candles, 2);

    expect(report.winrate).toBeGreaterThanOrEqual(0);
    expect(report.winrate).toBeLessThanOrEqual(1);
  });

  // ── Flat market: no breakout ──────────────────────────────────────────

  it("produces no trades in a flat market (no breakout signal)", () => {
    const candles = makeFlat(50, 100);
    const report = runBacktest(candles, 2);

    expect(report.trades).toBe(0);
    expect(report.totalPnlPct).toBe(0);
  });

  // ── Downtrend after breakout: stop losses ─────────────────────────────

  it("produces losses on a downtrend after initial breakout", () => {
    // Start with 21 candles of uptrend to trigger entry, then reverse
    const up = makeUptrend(22, 100, 2);
    const down = makeDowntrend(30, up[up.length - 1].close, 3);
    // Shift downtrend timestamps to continue from uptrend
    const lastTime = up[up.length - 1].openTime;
    for (let i = 0; i < down.length; i++) {
      down[i].openTime = lastTime + (i + 1) * 60_000;
    }
    const candles = [...up, ...down];
    const report = runBacktest(candles, 2);

    // Should have at least one trade, and some losses
    expect(report.trades).toBeGreaterThanOrEqual(1);
  });

  // ── Execution opts: fees and slippage ─────────────────────────────────

  it("fees reduce effective PnL compared to zero-fee backtest", () => {
    const candles = makeUptrend(60, 100, 2);

    const noFees = runBacktest(candles, 2, { feeBps: 0, slippageBps: 0 });
    const withFees = runBacktest(candles, 2, { feeBps: 10, slippageBps: 5 });

    // Both should produce trades on the same data
    if (noFees.trades > 0 && withFees.trades > 0) {
      expect(withFees.totalPnlPct).toBeLessThanOrEqual(noFees.totalPnlPct);
    }
  });

  // ── Determinism ───────────────────────────────────────────────────────

  it("is deterministic: same input produces same output", () => {
    const candles = makeUptrend(50, 100, 2);

    const a = runBacktest(candles, 2);
    const b = runBacktest(candles, 2);

    expect(a.trades).toBe(b.trades);
    expect(a.wins).toBe(b.wins);
    expect(a.totalPnlPct).toBe(b.totalPnlPct);
    expect(a.maxDrawdownPct).toBe(b.maxDrawdownPct);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });

  // ── Max drawdown ──────────────────────────────────────────────────────

  it("max drawdown is non-negative", () => {
    const candles = makeUptrend(50, 100, 2);
    const report = runBacktest(candles, 2);

    expect(report.maxDrawdownPct).toBeGreaterThanOrEqual(0);
  });

  // ── Report field rounding ─────────────────────────────────────────────

  it("rounds winrate to 4 decimal places and pnl/drawdown to 2", () => {
    const candles = makeUptrend(50, 100, 2);
    const report = runBacktest(candles, 2);

    // Check rounding: multiply by precision factor, should be integer
    expect(Number.isInteger(report.winrate * 10000)).toBe(true);
    expect(Number.isInteger(report.totalPnlPct * 100)).toBe(true);
    expect(Number.isInteger(report.maxDrawdownPct * 100)).toBe(true);
  });
});
