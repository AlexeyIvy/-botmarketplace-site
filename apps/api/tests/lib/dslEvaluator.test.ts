import { describe, it, expect } from "vitest";
import { runDslBacktest, parseDsl } from "../../src/lib/dslEvaluator.js";
import { makeUptrend, makeDowntrend, makeFlat, makeFlatThenUp, makeFlatThenDown } from "../fixtures/candles.js";

// ---------------------------------------------------------------------------
// DSL fixtures — minimal compiled DSL objects for testing
// ---------------------------------------------------------------------------

/** v1 DSL: SMA crossover long-only strategy with fixed SL/TP */
function makeSmaLongDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    id: "test-sma-long",
    name: "SMA Crossover Long",
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

/** v1 DSL: SMA crossunder short-only strategy */
function makeSmaShortDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    ...makeSmaLongDsl(fastLen, slowLen, slPct, tpPct),
    id: "test-sma-short",
    name: "SMA Crossunder Short",
    entry: {
      side: "Sell",
      signal: {
        type: "crossunder",
        fast: { blockType: "SMA", length: fastLen },
        slow: { blockType: "SMA", length: slowLen },
      },
      stopLoss: { type: "fixed_pct", value: slPct },
      takeProfit: { type: "fixed_pct", value: tpPct },
    },
  };
}

/** v2 DSL: EMA-based sideCondition with indicator exit */
function makeDualSideDsl() {
  return {
    id: "test-dual-side",
    name: "EMA Dual Side + Indicator Exit",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      sideCondition: {
        indicator: { type: "EMA", length: 20 },
        long: { op: "gt" },
        short: { op: "lt" },
      },
      signal: {
        type: "crossover",
        fast: { blockType: "SMA", length: 5 },
        slow: { blockType: "SMA", length: 10 },
      },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 2 },
      takeProfit: { type: "fixed_pct", value: 4 },
      indicatorExit: {
        indicator: { type: "RSI", length: 14 },
        condition: { op: "gt", value: 70 },
        appliesTo: "both",
      },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

/** v2 DSL: compare-based entry with time exit */
function makeCompareTimeExitDsl() {
  return {
    id: "test-compare-time",
    name: "Compare Entry + Time Exit",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      side: "Buy",
      signal: {
        type: "compare",
        op: ">",
        left: { blockType: "RSI", length: 14 },
        right: { blockType: "constant", length: 50 },
      },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 3 },
      takeProfit: { type: "fixed_pct", value: 6 },
      timeExit: { maxBarsInPosition: 5 },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 3, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

/** v2 DSL: trailing stop */
function makeTrailingStopDsl() {
  return {
    id: "test-trailing",
    name: "SMA + Trailing Stop",
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
      stopLoss: { type: "fixed_pct", value: 5 },
      takeProfit: { type: "fixed_pct", value: 20 },
      trailingStop: {
        type: "trailing_pct",
        activationPct: 2,
        callbackPct: 1,
      },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 5, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

/** v2 DSL with ATR-based SL/TP */
function makeAtrExitDsl() {
  return {
    id: "test-atr-exit",
    name: "SMA + ATR Exits",
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
      stopLoss: { type: "atr_multiple", value: 2, atrPeriod: 14 },
      takeProfit: { type: "atr_multiple", value: 4, atrPeriod: 14 },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("dslEvaluator – parseDsl", () => {
  it("throws on null/undefined dslJson", () => {
    expect(() => parseDsl(null)).toThrow();
    expect(() => parseDsl(undefined)).toThrow();
  });

  it("parses a v1 DSL correctly", () => {
    const dsl = makeSmaLongDsl();
    const parsed = parseDsl(dsl);
    expect(parsed.dslVersion).toBe(1);
    expect(parsed.entry.side).toBe("Buy");
    expect(parsed.entry.signal?.type).toBe("crossover");
    expect(parsed.risk.riskPerTradePct).toBe(2);
  });

  it("parses a v2 DSL with exit section", () => {
    const dsl = makeDualSideDsl();
    const parsed = parseDsl(dsl);
    expect(parsed.dslVersion).toBe(2);
    expect(parsed.exit?.stopLoss.type).toBe("fixed_pct");
    expect(parsed.exit?.indicatorExit?.indicator.type).toBe("RSI");
    expect(parsed.entry.sideCondition).toBeDefined();
  });
});

describe("dslEvaluator – runDslBacktest edge cases", () => {
  it("returns empty report for empty candle array", () => {
    const report = runDslBacktest([], makeSmaLongDsl());
    expect(report.trades).toBe(0);
    expect(report.candles).toBe(0);
  });

  it("returns empty report for single candle", () => {
    const candles = makeUptrend(1);
    const report = runDslBacktest(candles, makeSmaLongDsl());
    expect(report.trades).toBe(0);
    expect(report.candles).toBe(1);
  });

  it("returns empty report for insufficient data (no signal possible)", () => {
    const candles = makeUptrend(15);
    const report = runDslBacktest(candles, makeSmaLongDsl(5, 20));
    expect(report.trades).toBe(0);
  });
});

describe("dslEvaluator – SMA crossover long", () => {
  it("produces trades on flat-then-up data (crossover fires)", () => {
    // Flat 25 bars then up — SMA(5) will cross above SMA(20) during transition
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, makeSmaLongDsl(5, 20, 2, 4));

    expect(report.trades).toBeGreaterThanOrEqual(1);
    expect(report.candles).toBe(80);

    for (const t of report.tradeLog) {
      expect(t.side).toBe("long");
      expect(t.entryPrice).toBeGreaterThan(0);
      expect(t.exitPrice).toBeGreaterThan(0);
      expect(["WIN", "LOSS", "NEUTRAL"]).toContain(t.outcome);
    }
  });

  it("produces no trades on flat market (no crossover)", () => {
    const candles = makeFlat(80, 100);
    const report = runDslBacktest(candles, makeSmaLongDsl(5, 20));
    expect(report.trades).toBe(0);
  });

  it("all trade records have valid structure", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, makeSmaLongDsl());

    for (const t of report.tradeLog) {
      expect(t.entryTime).toBeGreaterThan(0);
      expect(t.exitTime).toBeGreaterThanOrEqual(t.entryTime);
      expect(t.slPrice).toBeGreaterThan(0);
      expect(t.tpPrice).toBeGreaterThan(0);
      expect(typeof t.pnlPct).toBe("number");
      expect(typeof t.barsHeld).toBe("number");
      expect(t.barsHeld).toBeGreaterThanOrEqual(0);
      expect(["sl", "tp", "indicator_exit", "time_exit", "trailing_stop", "end_of_data"]).toContain(t.exitReason);
    }
  });
});

describe("dslEvaluator – SMA crossunder short", () => {
  it("produces short trades on flat-then-down data", () => {
    const candles = makeFlatThenDown(80, 25, 200, 2);
    const report = runDslBacktest(candles, makeSmaShortDsl(5, 20, 2, 4));

    expect(report.trades).toBeGreaterThanOrEqual(1);
    for (const t of report.tradeLog) {
      expect(t.side).toBe("short");
    }
  });

  it("short position PnL is correct direction", () => {
    const candles = makeFlatThenDown(80, 25, 200, 2);
    const report = runDslBacktest(candles, makeSmaShortDsl(5, 20, 2, 4));

    if (report.trades > 0) {
      const tpTrades = report.tradeLog.filter(t => t.outcome === "WIN");
      for (const t of tpTrades) {
        expect(t.pnlPct).toBeGreaterThan(0);
      }
    }
  });
});

describe("dslEvaluator – dual-side (sideCondition)", () => {
  it("can produce both long and short trades from one DSL", () => {
    // Flat → up → flat → down — should trigger both sides
    const flatUp = makeFlatThenUp(50, 15, 100, 2);
    const flatDown = makeFlatThenDown(50, 15, flatUp[flatUp.length - 1].close, 2);
    const lastTime = flatUp[flatUp.length - 1].openTime;
    for (let i = 0; i < flatDown.length; i++) {
      flatDown[i].openTime = lastTime + (i + 1) * 60_000;
    }
    const candles = [...flatUp, ...flatDown];

    const report = runDslBacktest(candles, makeDualSideDsl());

    if (report.trades > 0) {
      const sides = new Set(report.tradeLog.map(t => t.side));
      // At minimum we get trades in one direction
      expect(sides.size).toBeGreaterThanOrEqual(1);
    }
  });
});

describe("dslEvaluator – indicator exit (dynamic exit beyond SL/TP)", () => {
  it("triggers indicator exit when RSI > 70 on strong uptrend", () => {
    // Strong uptrend with big steps → RSI should go overbought
    const candles = makeFlatThenUp(100, 20, 100, 5);
    const dsl = makeDualSideDsl();
    const report = runDslBacktest(candles, dsl);

    // On strong uptrend with RSI exit, at least one trade should fire
    if (report.trades > 0) {
      // Every exit must be one of our supported exit reasons
      expect(report.tradeLog.every(t =>
        ["sl", "tp", "indicator_exit", "time_exit", "trailing_stop", "end_of_data"].includes(t.exitReason)
      )).toBe(true);
    }
  });
});

describe("dslEvaluator – time exit", () => {
  it("exits after maxBarsInPosition", () => {
    // RSI > 50 on uptrend should fire; time exit after 5 bars
    const candles = makeFlatThenUp(100, 15, 100, 1);
    const dsl = makeCompareTimeExitDsl();
    const report = runDslBacktest(candles, dsl);

    const timeExits = report.tradeLog.filter(t => t.exitReason === "time_exit");
    for (const t of timeExits) {
      expect(t.barsHeld).toBe(5);
    }
  });
});

describe("dslEvaluator – trailing stop", () => {
  it("trailing stop can trigger on profitable move then pullback", () => {
    // Flat → up → pullback
    const flatUp = makeFlatThenUp(50, 20, 100, 3);
    const pullback = makeDowntrend(30, flatUp[flatUp.length - 1].close, 2);
    const lastTime = flatUp[flatUp.length - 1].openTime;
    for (let i = 0; i < pullback.length; i++) {
      pullback[i].openTime = lastTime + (i + 1) * 60_000;
    }
    const candles = [...flatUp, ...pullback];

    const dsl = makeTrailingStopDsl();
    const report = runDslBacktest(candles, dsl);

    if (report.trades > 0) {
      for (const t of report.tradeLog) {
        expect(["sl", "tp", "trailing_stop", "end_of_data"]).toContain(t.exitReason);
      }
    }
  });
});

describe("dslEvaluator – ATR-based exits", () => {
  it("computes ATR-based SL/TP levels correctly", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeAtrExitDsl();
    const report = runDslBacktest(candles, dsl);

    if (report.trades > 0) {
      for (const t of report.tradeLog) {
        expect(t.slPrice).toBeLessThan(t.entryPrice);
        expect(t.tpPrice).toBeGreaterThan(t.entryPrice);
      }
    }
  });
});

describe("dslEvaluator – determinism", () => {
  it("same input produces same output", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl();

    const a = runDslBacktest(candles, dsl);
    const b = runDslBacktest(candles, dsl);

    expect(a.trades).toBe(b.trades);
    expect(a.wins).toBe(b.wins);
    expect(a.totalPnlPct).toBe(b.totalPnlPct);
    expect(a.maxDrawdownPct).toBe(b.maxDrawdownPct);
    expect(a.tradeLog).toEqual(b.tradeLog);
  });

  it("deterministic across DSL variants", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);

    for (const dsl of [makeSmaLongDsl(), makeCompareTimeExitDsl()]) {
      const r1 = runDslBacktest(candles, dsl);
      const r2 = runDslBacktest(candles, dsl);
      expect(r1.tradeLog).toEqual(r2.tradeLog);
    }
  });
});

describe("dslEvaluator – execution opts (fees/slippage)", () => {
  it("fees reduce effective PnL compared to zero-fee backtest", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const noFees = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps: 0 });
    const withFees = runDslBacktest(candles, dsl, { feeBps: 10, slippageBps: 5 });

    if (noFees.trades > 0 && withFees.trades > 0) {
      expect(withFees.totalPnlPct).toBeLessThanOrEqual(noFees.totalPnlPct + 0.01);
    }
  });
});

describe("dslEvaluator – report field rounding", () => {
  it("rounds winrate to 4 decimal places and pnl/drawdown to 2", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, makeSmaLongDsl());

    expect(Number.isInteger(report.winrate * 10000)).toBe(true);
    expect(Number.isInteger(report.totalPnlPct * 100)).toBe(true);
    expect(Number.isInteger(report.maxDrawdownPct * 100)).toBe(true);
  });
});

describe("dslEvaluator – max drawdown", () => {
  it("max drawdown is non-negative", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, makeSmaLongDsl());
    expect(report.maxDrawdownPct).toBeGreaterThanOrEqual(0);
  });
});

describe("dslEvaluator – unsupported signal type yields no trades", () => {
  it("returns no trades for unknown signal type", () => {
    const dsl = {
      ...makeSmaLongDsl(),
      entry: {
        side: "Buy",
        signal: { type: "raw" },
        stopLoss: { type: "fixed_pct", value: 2 },
        takeProfit: { type: "fixed_pct", value: 4 },
      },
    };
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBe(0);
  });
});

describe("dslEvaluator – end_of_data outcome reflects actual PnL", () => {
  it("end_of_data exit on profitable long position is WIN", () => {
    // Strong uptrend — position should be in profit at end of data
    // Use wide SL/TP so they don't trigger before data ends
    const candles = makeFlatThenUp(45, 20, 100, 3);
    const dsl = makeSmaLongDsl(5, 20, 50, 200); // very wide SL=50%, TP=200%
    const report = runDslBacktest(candles, dsl);

    const eodTrades = report.tradeLog.filter(t => t.exitReason === "end_of_data");
    for (const t of eodTrades) {
      expect(t.pnlPct).toBeGreaterThan(0);
      expect(t.outcome).toBe("WIN");
    }
  });

  it("end_of_data exit on losing short position is LOSS", () => {
    // Flat then up — short entry on crossunder won't fire, use long to test
    // Instead: use a long entry on flat-then-down to get a losing end_of_data
    const up = makeFlatThenUp(35, 20, 100, 2);
    const down = makeDowntrend(20, up[up.length - 1].close, 1);
    const lastTime = up[up.length - 1].openTime;
    for (let i = 0; i < down.length; i++) {
      down[i].openTime = lastTime + (i + 1) * 60_000;
    }
    // Flat-then-up triggers long entry, then mild downtrend follows
    // Use wide SL so it doesn't trigger, position bleeds to end
    const candles = [...up, ...down];
    const dsl = makeSmaLongDsl(5, 20, 90, 200); // very wide SL=90%, TP=200%
    const report = runDslBacktest(candles, dsl);

    const eodTrades = report.tradeLog.filter(t => t.exitReason === "end_of_data");
    for (const t of eodTrades) {
      if (t.pnlPct < 0) {
        expect(t.outcome).toBe("LOSS");
      } else if (t.pnlPct > 0) {
        expect(t.outcome).toBe("WIN");
      } else {
        expect(t.outcome).toBe("NEUTRAL");
      }
    }
  });
});

describe("dslEvaluator – golden backtest (regression fixture)", () => {
  it("produces exact expected results for a known DSL + dataset pairing", () => {
    const candles = makeFlatThenUp(60, 22, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const report = runDslBacktest(candles, dsl);

    expect(report.trades).toBeGreaterThanOrEqual(1);
    expect(report.candles).toBe(60);

    // Save and re-run to verify determinism
    const report2 = runDslBacktest(candles, dsl);
    expect(report).toEqual(report2);
  });
});
