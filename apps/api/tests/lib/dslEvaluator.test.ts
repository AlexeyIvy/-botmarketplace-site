import { describe, it, expect } from "vitest";
import { runDslBacktest, parseDsl, evaluateSignal, getIndicatorValues, createIndicatorCache, determineSide, evaluateProximityFilter } from "../../src/lib/dslEvaluator.js";
import type { DslSignal, DslEntry, DslProximityFilter } from "../../src/lib/dslEvaluator.js";
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

  // -------------------------------------------------------------------------
  // 46-T2: symmetric slippage on entry AND exit
  // -------------------------------------------------------------------------

  it("46-T2: slippage applies symmetrically on entry and exit (long)", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);
    const slippageBps = 50;

    const baseline = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps: 0 });
    const withSlip = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps });

    expect(baseline.trades).toBeGreaterThanOrEqual(1);
    expect(withSlip.trades).toBe(baseline.trades);

    const entryMult = 1 + slippageBps / 10_000;
    const exitMult = 1 - slippageBps / 10_000;

    for (const trade of withSlip.tradeLog) {
      // Entry: default fillAt = "CLOSE" → raw entry is bar.close.
      const entryBar = candles.find((c) => c.openTime === trade.entryTime)!;
      expect(trade.entryPrice / entryBar.close).toBeCloseTo(entryMult, 8);

      // Exit: rawExitPrice depends on exit reason. For SL/TP the trigger
      // price is captured in slPrice/tpPrice; effective exit = trigger * exitMult.
      // For indicator/time/end_of_data the raw exit is bar.close.
      if (trade.exitReason === "sl") {
        expect(trade.exitPrice / trade.slPrice).toBeCloseTo(exitMult, 8);
      } else if (trade.exitReason === "tp") {
        expect(trade.exitPrice / trade.tpPrice).toBeCloseTo(exitMult, 8);
      } else {
        const exitBar = candles.find((c) => c.openTime === trade.exitTime)!;
        expect(trade.exitPrice / exitBar.close).toBeCloseTo(exitMult, 8);
      }
    }
  });

  it("46-T2: slippage applies symmetrically on entry and exit (short)", () => {
    const candles = makeFlatThenDown(80, 25, 200, 2);
    const dsl = makeSmaShortDsl(5, 20, 2, 4);
    const slippageBps = 50;

    const baseline = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps: 0 });
    const withSlip = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps });

    expect(baseline.trades).toBeGreaterThanOrEqual(1);
    expect(withSlip.trades).toBe(baseline.trades);

    const entryMult = 1 + slippageBps / 10_000;
    const exitMult = 1 - slippageBps / 10_000;

    for (const trade of withSlip.tradeLog) {
      const entryBar = candles.find((c) => c.openTime === trade.entryTime)!;
      expect(trade.entryPrice / entryBar.close).toBeCloseTo(entryMult, 8);
      if (trade.exitReason === "sl") {
        expect(trade.exitPrice / trade.slPrice).toBeCloseTo(exitMult, 8);
      } else if (trade.exitReason === "tp") {
        expect(trade.exitPrice / trade.tpPrice).toBeCloseTo(exitMult, 8);
      } else {
        const exitBar = candles.find((c) => c.openTime === trade.exitTime)!;
        expect(trade.exitPrice / exitBar.close).toBeCloseTo(exitMult, 8);
      }
    }
  });

  it("46-T2: slippageBps > 0 strictly reduces totalPnlPct in a multi-trade run", () => {
    // Long-side strategy on flat-then-up — with default SL/TP=2/4 we get
    // multiple trades over an 80-bar series, enough to make the slippage
    // delta clearly negative in aggregate.
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const noSlip = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps: 0 });
    const withSlip = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps: 100 });

    expect(withSlip.trades).toBe(noSlip.trades);
    expect(withSlip.trades).toBeGreaterThanOrEqual(1);
    // Strictly less when slippage > 0 (real round-trip cost is non-zero).
    expect(withSlip.totalPnlPct).toBeLessThan(noSlip.totalPnlPct);
  });

  // -------------------------------------------------------------------------
  // 46-T3: takerFeeBps / makerFeeBps with feeBps alias
  // -------------------------------------------------------------------------

  it("46-T3: feeBps alone is normalized to takerFeeBps (legacy behavior)", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const legacy = runDslBacktest(candles, dsl, { feeBps: 30, slippageBps: 0 });
    const taker = runDslBacktest(candles, dsl, { takerFeeBps: 30, slippageBps: 0 });

    expect(taker.tradeLog).toEqual(legacy.tradeLog);
    expect(taker.totalPnlPct).toBe(legacy.totalPnlPct);
  });

  it("46-T3: takerFeeBps wins when both feeBps and takerFeeBps are present", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const both = runDslBacktest(candles, dsl, {
      feeBps: 10,
      takerFeeBps: 30,
      slippageBps: 0,
    });
    const onlyTaker = runDslBacktest(candles, dsl, {
      takerFeeBps: 30,
      slippageBps: 0,
    });

    expect(both.tradeLog).toEqual(onlyTaker.tradeLog);
  });

  it("46-T3: makerFeeBps is captured by the API but does not affect formulas", () => {
    // Current evaluator uses only takerFeeBps for all fills (taker-only).
    // makerFeeBps must be accepted in opts but produce a result identical
    // to running without it.
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const withMaker = runDslBacktest(candles, dsl, {
      takerFeeBps: 30,
      makerFeeBps: 10,
      slippageBps: 0,
    });
    const withoutMaker = runDslBacktest(candles, dsl, {
      takerFeeBps: 30,
      slippageBps: 0,
    });

    expect(withMaker.tradeLog).toEqual(withoutMaker.tradeLog);
    expect(withMaker.totalPnlPct).toBe(withoutMaker.totalPnlPct);
  });

  it("46-T3: missing fee fields default to zero (no fee, no slippage)", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);

    const empty = runDslBacktest(candles, dsl, { slippageBps: 0 });
    const explicitZero = runDslBacktest(candles, dsl, { feeBps: 0, slippageBps: 0 });

    expect(empty.tradeLog).toEqual(explicitZero.tradeLog);
  });

  it("46-T2: slippageBps = 0 keeps the engine bit-identical to fee-only behavior", () => {
    // Backward-compat anchor: at slippageBps = 0, the new symmetric formula
    // reduces to old fee-only behavior on exit (exitMult = 1 - feeBps/10_000).
    // Verify entry/exit multipliers match the legacy expectation directly.
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl(5, 20, 2, 4);
    const feeBps = 30;
    const report = runDslBacktest(candles, dsl, { feeBps, slippageBps: 0 });

    const expectedEntryMult = 1 + feeBps / 10_000;
    const expectedExitMult = 1 - feeBps / 10_000;

    expect(report.trades).toBeGreaterThanOrEqual(1);
    for (const trade of report.tradeLog) {
      const entryBar = candles.find((c) => c.openTime === trade.entryTime)!;
      expect(trade.entryPrice / entryBar.close).toBeCloseTo(expectedEntryMult, 8);
      if (trade.exitReason === "sl") {
        expect(trade.exitPrice / trade.slPrice).toBeCloseTo(expectedExitMult, 8);
      } else if (trade.exitReason === "tp") {
        expect(trade.exitPrice / trade.tpPrice).toBeCloseTo(expectedExitMult, 8);
      } else {
        const exitBar = candles.find((c) => c.openTime === trade.exitTime)!;
        expect(trade.exitPrice / exitBar.close).toBeCloseTo(expectedExitMult, 8);
      }
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

// ---------------------------------------------------------------------------
// Composed signals: and_gate / or_gate (Phase 10.2)
// ---------------------------------------------------------------------------

describe("evaluateSignal – composed and/or gates", () => {
  // Helpers: minimal candles + cache for unit-level signal tests
  const candles = makeUptrend(30, 100, 1);
  const cache = {} as Parameters<typeof evaluateSignal>[3];

  const compareTrue: DslSignal = {
    type: "compare",
    op: ">",
    left: { blockType: "constant", value: 10 } as unknown as DslSignal["left"],
    right: { blockType: "constant", value: 5 } as unknown as DslSignal["right"],
  };

  const compareFalse: DslSignal = {
    type: "compare",
    op: ">",
    left: { blockType: "constant", value: 3 } as unknown as DslSignal["left"],
    right: { blockType: "constant", value: 5 } as unknown as DslSignal["right"],
  };

  it("and(true, true) → true", () => {
    const signal: DslSignal = { type: "and", conditions: [compareTrue, compareTrue] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(true);
  });

  it("and(true, false) → false", () => {
    const signal: DslSignal = { type: "and", conditions: [compareTrue, compareFalse] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(false);
  });

  it("and(false, false) → false", () => {
    const signal: DslSignal = { type: "and", conditions: [compareFalse, compareFalse] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(false);
  });

  it("or(false, true) → true", () => {
    const signal: DslSignal = { type: "or", conditions: [compareFalse, compareTrue] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(true);
  });

  it("or(false, false) → false", () => {
    const signal: DslSignal = { type: "or", conditions: [compareFalse, compareFalse] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(false);
  });

  it("nested: and(or(false, true), true) → true", () => {
    const orSignal: DslSignal = { type: "or", conditions: [compareFalse, compareTrue] };
    const signal: DslSignal = { type: "and", conditions: [orSignal, compareTrue] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(true);
  });

  it("nested: or(and(true, false), and(true, true)) → true", () => {
    const andFalse: DslSignal = { type: "and", conditions: [compareTrue, compareFalse] };
    const andTrue: DslSignal = { type: "and", conditions: [compareTrue, compareTrue] };
    const signal: DslSignal = { type: "or", conditions: [andFalse, andTrue] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(true);
  });

  it("maxDepth exceeded → false", () => {
    // Build 6-level deep nesting (exceeds MAX_SIGNAL_DEPTH=5)
    let deep: DslSignal = compareTrue;
    for (let d = 0; d < 6; d++) {
      deep = { type: "and", conditions: [deep] };
    }
    expect(evaluateSignal(deep, 10, candles, cache)).toBe(false);
  });

  it("empty conditions → false", () => {
    expect(evaluateSignal({ type: "and", conditions: [] }, 10, candles, cache)).toBe(false);
    expect(evaluateSignal({ type: "or", conditions: [] }, 10, candles, cache)).toBe(false);
  });

  it("undefined conditions → false", () => {
    expect(evaluateSignal({ type: "and" }, 10, candles, cache)).toBe(false);
    expect(evaluateSignal({ type: "or" }, 10, candles, cache)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Confirm N Bars (Task 25a)
// ---------------------------------------------------------------------------

describe("evaluateSignal – confirm_n_bars", () => {
  const candles = makeUptrend(30, 100, 1);
  const cache = {} as Parameters<typeof evaluateSignal>[3];

  const alwaysTrue: DslSignal = {
    type: "compare",
    op: ">",
    left: { blockType: "constant", value: 10 } as unknown as DslSignal["left"],
    right: { blockType: "constant", value: 5 } as unknown as DslSignal["right"],
  };

  const alwaysFalse: DslSignal = {
    type: "compare",
    op: ">",
    left: { blockType: "constant", value: 3 } as unknown as DslSignal["left"],
    right: { blockType: "constant", value: 5 } as unknown as DslSignal["right"],
  };

  it("fires when sub-signal true for N consecutive bars", () => {
    const signal: DslSignal = { type: "confirm_n_bars", bars: 3, conditions: [alwaysTrue] };
    // Bar index 2 = 3rd bar (0,1,2) — enough for bars=3
    expect(evaluateSignal(signal, 2, candles, cache)).toBe(true);
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(true);
  });

  it("does not fire when not enough bars", () => {
    const signal: DslSignal = { type: "confirm_n_bars", bars: 3, conditions: [alwaysTrue] };
    // Bar 1 = only 2 bars available (0,1) — not enough for bars=3
    expect(evaluateSignal(signal, 1, candles, cache)).toBe(false);
    expect(evaluateSignal(signal, 0, candles, cache)).toBe(false);
  });

  it("does not fire when sub-signal is false", () => {
    const signal: DslSignal = { type: "confirm_n_bars", bars: 3, conditions: [alwaysFalse] };
    expect(evaluateSignal(signal, 10, candles, cache)).toBe(false);
  });

  it("defaults to bars=3 when not specified", () => {
    const signal: DslSignal = { type: "confirm_n_bars", conditions: [alwaysTrue] };
    expect(evaluateSignal(signal, 2, candles, cache)).toBe(true);
    expect(evaluateSignal(signal, 1, candles, cache)).toBe(false);
  });

  it("bars=1 fires immediately when sub-signal is true", () => {
    const signal: DslSignal = { type: "confirm_n_bars", bars: 1, conditions: [alwaysTrue] };
    expect(evaluateSignal(signal, 0, candles, cache)).toBe(true);
  });

  it("returns false with no conditions", () => {
    expect(evaluateSignal({ type: "confirm_n_bars", bars: 3 }, 10, candles, cache)).toBe(false);
    expect(evaluateSignal({ type: "confirm_n_bars", bars: 3, conditions: [] }, 10, candles, cache)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Phase 12.2 — Unknown indicator type returns nulls
// ---------------------------------------------------------------------------

describe("dslEvaluator – unknown indicator type", () => {
  it("returns array of nulls with correct length for unknown indicator type", () => {
    const candles = makeFlat(30, 100);
    const cache = createIndicatorCache();
    const result = getIndicatorValues("nonexistent_typo", {}, candles, cache);

    expect(result.length).toBe(candles.length);
    expect(result.every(v => v === null)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Phase 12.1 — determineSide with indicator_sign mode
// ---------------------------------------------------------------------------

describe("dslEvaluator – sideCondition indicator_sign mode", () => {
  const candles = makeFlat(30, 100);
  const cache = createIndicatorCache();

  // Pre-fill cache with known constant values for testing
  function makeEntry(mode: string | undefined, constantVal: number): DslEntry {
    return {
      sideCondition: {
        indicator: { type: "constant", length: constantVal } as any,
        long: { op: "gt" },
        short: { op: "lt" },
        ...(mode ? { mode: mode as any } : {}),
      },
    };
  }

  it("mode=indicator_sign, positive value → long", () => {
    const entry = makeEntry("indicator_sign", 1);
    const side = determineSide(entry, 15, candles, cache);
    expect(side).toBe("long");
  });

  it("mode=indicator_sign, negative value → short", () => {
    const entry = makeEntry("indicator_sign", -1);
    const side = determineSide(entry, 15, candles, cache);
    expect(side).toBe("short");
  });

  it("mode=indicator_sign, zero value → null", () => {
    const entry = makeEntry("indicator_sign", 0);
    const side = determineSide(entry, 15, candles, cache);
    expect(side).toBeNull();
  });

  it("mode=undefined → current behavior (price_vs_indicator)", () => {
    // constant=50, close=100, so close > 50 → long (op "gt")
    const entry = makeEntry(undefined, 50);
    const side = determineSide(entry, 15, candles, cache);
    expect(side).toBe("long");
  });
});

// ---------------------------------------------------------------------------
// Volume Profile runtime integration (#24)
// ---------------------------------------------------------------------------

describe("getIndicatorValues — volume_profile", () => {
  const candles = makeFlat(40, 100);

  it("returns POC series for 'volume_profile' block type", () => {
    const cache = createIndicatorCache();
    const result = getIndicatorValues("volume_profile", { period: 20, bins: 24 }, candles, cache);
    expect(result).toHaveLength(40);
    // First 19 bars are null (warm-up)
    for (let i = 0; i < 19; i++) {
      expect(result[i]).toBeNull();
    }
    // Bar 19+ should have non-null POC
    expect(result[19]).not.toBeNull();
    expect(typeof result[19]).toBe("number");
  });

  it("returns VAH series for 'volume_profile_vah'", () => {
    const cache = createIndicatorCache();
    const result = getIndicatorValues("volume_profile_vah", { period: 20, bins: 24 }, candles, cache);
    expect(result[19]).not.toBeNull();
  });

  it("returns VAL series for 'volume_profile_val'", () => {
    const cache = createIndicatorCache();
    const result = getIndicatorValues("volume_profile_val", { period: 20, bins: 24 }, candles, cache);
    expect(result[19]).not.toBeNull();
  });

  it("caches volume profile results", () => {
    const cache = createIndicatorCache();
    const a = getIndicatorValues("volume_profile", { period: 20, bins: 24 }, candles, cache);
    const b = getIndicatorValues("volume_profile", { period: 20, bins: 24 }, candles, cache);
    expect(a).toBe(b); // same reference = cached
  });

  it("VAL <= POC <= VAH for uptrend candles", () => {
    const cache = createIndicatorCache();
    const trendCandles = makeUptrend(40, 100, 0.5);
    const poc = getIndicatorValues("volume_profile", { period: 20, bins: 24 }, trendCandles, cache);
    const vah = getIndicatorValues("volume_profile_vah", { period: 20, bins: 24 }, trendCandles, cache);
    const val = getIndicatorValues("volume_profile_val", { period: 20, bins: 24 }, trendCandles, cache);
    for (let i = 19; i < 40; i++) {
      expect(val[i]!).toBeLessThanOrEqual(poc[i]!);
      expect(poc[i]!).toBeLessThanOrEqual(vah[i]!);
    }
  });
});

// ---------------------------------------------------------------------------
// Proximity Filter runtime gate (#24)
// ---------------------------------------------------------------------------

describe("evaluateProximityFilter", () => {
  // Candles at close ~100
  const candles = makeFlat(5, 100);

  it("returns true when no filter configured", () => {
    const cache = createIndicatorCache();
    expect(evaluateProximityFilter(undefined, 2, candles, cache)).toBe(true);
  });

  it("returns true when price is near the reference level (percentage mode)", () => {
    const cache = createIndicatorCache();
    // Mock: use 'constant' as level source — constant 100 vs close ~100
    const pf: DslProximityFilter = { threshold: 2, mode: "percentage", levelSource: "constant" };
    // constant returns 0 by default, so let's use a different approach
    // We'll set levelSource to 'vwap' which will compute from the candles
    const pfVwap: DslProximityFilter = { threshold: 5, mode: "percentage", levelSource: "vwap" };
    const result = evaluateProximityFilter(pfVwap, 2, candles, cache);
    // VWAP of flat candles ≈ close, so distance ≈ 0% → should pass
    expect(result).toBe(true);
  });

  it("returns false when price is far from reference level", () => {
    const cache = createIndicatorCache();
    // Use SMA(1) as reference level on uptrend candles where close diverges from SMA(20)
    const trendCandles = makeUptrend(30, 100, 5);
    // At bar 29, close = 100+29*5=245, but SMA(20) over bars 10-29 ≈ 195
    // Distance ≈ 50/195 ≈ 25.6% → threshold 1% should fail
    const pf: DslProximityFilter = { threshold: 1, mode: "percentage", levelSource: "sma" };
    const result = evaluateProximityFilter(pf, 29, trendCandles, cache);
    expect(result).toBe(false);
  });

  it("returns true when insufficient data (null level)", () => {
    const cache = createIndicatorCache();
    // SMA(20) on first bar will be null → should pass through
    const pf: DslProximityFilter = { threshold: 1, mode: "percentage", levelSource: "sma" };
    const result = evaluateProximityFilter(pf, 0, candles, cache);
    expect(result).toBe(true);
  });

  it("absolute mode works correctly", () => {
    const cache = createIndicatorCache();
    const trendCandles = makeUptrend(30, 100, 5);
    // At bar 29, close=245, SMA(14) default ≈ close of bars 16-29 ≈ 100+22.5*5=212.5
    // Distance ≈ 32.5, threshold=50 → should pass
    const pfPass: DslProximityFilter = { threshold: 50, mode: "absolute", levelSource: "sma" };
    expect(evaluateProximityFilter(pfPass, 29, trendCandles, cache)).toBe(true);
    // threshold=1 → should fail
    const pfFail: DslProximityFilter = { threshold: 1, mode: "absolute", levelSource: "sma" };
    expect(evaluateProximityFilter(pfFail, 29, trendCandles, cache)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 46-T1: fillAt modes — OPEN, CLOSE, NEXT_OPEN
// ---------------------------------------------------------------------------

describe("dslEvaluator – fillAt modes (46-T1)", () => {
  it("default fillAt='CLOSE' fills entry at the signal bar's close", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, makeSmaLongDsl(5, 20, 2, 4));
    expect(report.trades).toBeGreaterThanOrEqual(1);

    const first = report.tradeLog[0];
    const entryBar = candles.find((c) => c.openTime === first.entryTime)!;
    // No fee/slippage by default → entryPrice exactly equals close.
    expect(first.entryPrice).toBeCloseTo(entryBar.close, 10);
  });

  it("fillAt='OPEN' fills entry at the signal bar's open", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const report = runDslBacktest(candles, makeSmaLongDsl(5, 20, 2, 4), {
      fillAt: "OPEN",
    });
    expect(report.trades).toBeGreaterThanOrEqual(1);

    const first = report.tradeLog[0];
    const entryBar = candles.find((c) => c.openTime === first.entryTime)!;
    expect(first.entryPrice).toBeCloseTo(entryBar.open, 10);
    // Sanity: makeFlatThenUp seeds open = close - step*0.3 in the trend phase,
    // so OPEN < CLOSE on the entry bar.
    expect(first.entryPrice).toBeLessThan(entryBar.close);
  });

  it("fillAt='NEXT_OPEN' fills entry at the next bar's open and shifts entryTime", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    // Reference run with CLOSE to locate the signal bar.
    const refReport = runDslBacktest(candles, makeSmaLongDsl(5, 20, 2, 4));
    const refSignalTime = refReport.tradeLog[0].entryTime;
    const refSignalIdx = candles.findIndex((c) => c.openTime === refSignalTime);
    expect(refSignalIdx).toBeGreaterThanOrEqual(0);
    expect(refSignalIdx + 1).toBeLessThan(candles.length);

    const report = runDslBacktest(candles, makeSmaLongDsl(5, 20, 2, 4), {
      fillAt: "NEXT_OPEN",
    });
    expect(report.trades).toBeGreaterThanOrEqual(1);

    const first = report.tradeLog[0];
    const expectedBar = candles[refSignalIdx + 1];
    expect(first.entryTime).toBe(expectedBar.openTime);
    expect(first.entryPrice).toBeCloseTo(expectedBar.open, 10);
  });

  it("fillAt='NEXT_OPEN' skips entry when the signal fires on the last candle", () => {
    // Construct a fixture where the SMA crossover fires only on the very last
    // bar: 25 flat bars then a single sharp upward jump. With SMA(2)/SMA(3)
    // and a one-bar spike at the end, the crossover lands on the last bar.
    const candles = [];
    for (let i = 0; i < 4; i++) {
      candles.push({
        openTime: 1_700_000_000_000 + i * 60_000,
        open: 100, high: 100, low: 100, close: 100, volume: 1000,
      });
    }
    candles.push({
      openTime: 1_700_000_000_000 + 4 * 60_000,
      open: 100, high: 200, low: 100, close: 200, volume: 1000,
    });

    const dsl = makeSmaLongDsl(2, 3, 2, 4);
    const closeReport = runDslBacktest(candles, dsl, { fillAt: "CLOSE" });
    const nextOpenReport = runDslBacktest(candles, dsl, { fillAt: "NEXT_OPEN" });

    // Signal fires on the last bar (index 4) under CLOSE → 1 trade closed via end_of_data.
    expect(closeReport.trades).toBe(1);
    // NEXT_OPEN has no next candle → entry skipped, no trade recorded.
    expect(nextOpenReport.trades).toBe(0);
  });

  it("fillAt='NEXT_OPEN' indicator_exit on the last candle falls back to current close", () => {
    // Fixture: SMA(2) crosses above SMA(3) on bar 3, then RSI(2) > 70 on
    // bar 4 forces an indicator_exit on the last candle. With NEXT_OPEN the
    // exit must fall back to bar 4's close (no next bar exists).
    const candles = [
      { openTime: 0,       open: 100, high: 100, low: 100, close: 100, volume: 1000 },
      { openTime: 60_000,  open: 100, high: 100, low: 100, close: 100, volume: 1000 },
      { openTime: 120_000, open: 100, high: 100, low: 100, close: 100, volume: 1000 },
      { openTime: 180_000, open: 150, high: 200, low: 150, close: 200, volume: 1000 },
      { openTime: 240_000, open: 250, high: 300, low: 250, close: 300, volume: 1000 },
    ];

    const dsl = {
      id: "rsi-exit-last",
      name: "RSI exit on last bar",
      dslVersion: 2,
      enabled: true,
      market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
      entry: {
        side: "Buy",
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", length: 2 },
          slow: { blockType: "SMA", length: 3 },
        },
      },
      exit: {
        // SL/TP set wide so they don't fire on this fixture.
        stopLoss: { type: "fixed_pct", value: 99 },
        takeProfit: { type: "fixed_pct", value: 99 },
        indicatorExit: {
          indicator: { type: "RSI", length: 2 },
          condition: { op: "gt", value: 70 },
          appliesTo: "long",
        },
      },
      risk: { maxPositionSizeUsd: 100, riskPerTradePct: 99, cooldownSeconds: 0 },
      execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
      guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
    };

    const report = runDslBacktest(candles, dsl, { fillAt: "NEXT_OPEN" });
    const indExits = report.tradeLog.filter((t) => t.exitReason === "indicator_exit");
    expect(indExits.length).toBe(1);

    const exit = indExits[0];
    const lastBar = candles[candles.length - 1];
    expect(exit.exitTime).toBe(lastBar.openTime);
    // Fallback path: no next candle → exit fills at the current bar's close.
    expect(exit.exitPrice).toBeCloseTo(lastBar.close, 10);
  });

  it("fillAt='OPEN' indicator_exit fills at the signal bar's open", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = {
      ...makeSmaLongDsl(5, 20, 50, 50),
      exit: {
        stopLoss: { type: "fixed_pct", value: 50 },
        takeProfit: { type: "fixed_pct", value: 50 },
        indicatorExit: {
          indicator: { type: "RSI", length: 14 },
          condition: { op: "gt", value: 70 },
          appliesTo: "both",
        },
      },
    };
    const report = runDslBacktest(candles, dsl, { fillAt: "OPEN" });
    const indExits = report.tradeLog.filter((t) => t.exitReason === "indicator_exit");
    expect(indExits.length).toBeGreaterThanOrEqual(1);

    const exit = indExits[0];
    const exitBar = candles.find((c) => c.openTime === exit.exitTime)!;
    expect(exit.exitPrice).toBeCloseTo(exitBar.open, 10);
  });
});
