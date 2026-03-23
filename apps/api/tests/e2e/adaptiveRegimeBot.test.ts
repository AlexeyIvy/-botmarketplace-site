/**
 * Adaptive Regime Bot — End-to-End Tests (#130)
 *
 * Validates the graph → compile → DSL → backtest → runtime pipeline
 * for the Adaptive Regime Bot trend-mode strategy.
 *
 * Test categories:
 *   1. Compilation: graph → compile → valid DSL v1
 *   2. Backtest:    DSL v2 → deterministic, reproducible results
 *   3. Runtime:     signal engine + exit engine correctness
 *   4. Parity:      signal engine fires at same bar as backtest entry
 *
 * All fixtures are deterministic: no randomness, no time-dependence, no I/O.
 */

import { describe, it, expect } from "vitest";
import { compileGraph } from "../../src/lib/compiler/index.js";
import { runBacktest } from "../../src/lib/backtest.js";
import { runDslBacktest } from "../../src/lib/dslEvaluator.js";
import { evaluateEntry, generateOpenIntent } from "../../src/lib/signalEngine.js";
import { evaluateExit, createTrailingStopState } from "../../src/lib/exitEngine.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";

import { makeAdaptiveRegimeBotGraph } from "../fixtures/graphs.js";
import { makeStrongUptrend, makeStrongDowntrend } from "../fixtures/candles.js";
import {
  makeAdaptiveRegimeTrendDsl,
  makeAdaptiveRegimeLongOnlyDsl,
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
// 1. Compilation pipeline: graph → compile → DSL v1
// ---------------------------------------------------------------------------

describe("Adaptive Regime Bot — compilation", () => {
  it("compiles trend-mode graph to valid DSL without errors", () => {
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(
      graph,
      "adaptive-regime-001",
      "Adaptive Regime Bot",
      "BTCUSDT",
      "5m",
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.compiledDsl).toBeDefined();
    const dsl = result.compiledDsl as Record<string, unknown>;
    expect(dsl["dslVersion"]).toBe(1);
    expect(dsl["name"]).toBe("Adaptive Regime Bot");

    const market = dsl["market"] as Record<string, unknown>;
    expect(market["symbol"]).toBe("BTCUSDT");
    expect(market["env"]).toBe("demo");
  });

  it("compiled DSL has correct entry structure", () => {
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(graph, "arb-001", "ARB", "BTCUSDT", "5m");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const dsl = result.compiledDsl as Record<string, unknown>;
    const entry = dsl["entry"] as Record<string, unknown>;

    expect(entry["side"]).toBe("Buy");

    const signal = entry["signal"] as Record<string, unknown>;
    expect(signal["type"]).toBe("compare");
    expect(signal["op"]).toBe(">");

    const left = signal["left"] as Record<string, unknown>;
    expect(left["blockType"]).toBe("adx");

    const sl = entry["stopLoss"] as Record<string, unknown>;
    expect(sl["type"]).toBe("fixed");
    expect(sl["value"]).toBe(2.0);

    const tp = entry["takeProfit"] as Record<string, unknown>;
    expect(tp["type"]).toBe("fixed");
    expect(tp["value"]).toBe(4.0);
  });

  it("compiled DSL includes ADX indicator metadata", () => {
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(graph, "arb-002", "ARB", "BTCUSDT", "5m");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const dsl = result.compiledDsl as Record<string, unknown>;
    const entry = dsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;

    const adxInd = indicators.find((ind) => ind["type"] === "adx");
    expect(adxInd).toBeDefined();
    expect(adxInd!["period"]).toBe(14);
  });

  it("produces no validation warnings for trend-mode graph", () => {
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(graph, "arb-003", "ARB", "BTCUSDT", "5m");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const errors = result.validationIssues.filter((i) => i.severity === "error");
    expect(errors).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// 2. Backtest pipeline: DSL v2 → deterministic results
// ---------------------------------------------------------------------------

describe("Adaptive Regime Bot — backtest", () => {
  it("produces trades on strong uptrend with long-only DSL", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const report = runBacktest(candles, dsl);

    expect(report.candles).toBe(80);
    expect(report.trades).toBeGreaterThan(0);
    expect(report.tradeLog.length).toBe(report.trades);
  });

  it("all trades have valid structure", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const report = runBacktest(candles, dsl);

    for (const trade of report.tradeLog) {
      expect(trade.side).toBe("long");
      expect(trade.entryPrice).toBeGreaterThan(0);
      expect(trade.exitPrice).toBeGreaterThan(0);
      expect(trade.slPrice).toBeLessThan(trade.entryPrice);
      expect(trade.tpPrice).toBeGreaterThan(trade.entryPrice);
      expect(["WIN", "LOSS", "NEUTRAL"]).toContain(trade.outcome);
      expect(["sl", "tp", "end_of_data"]).toContain(trade.exitReason);
      expect(trade.barsHeld).toBeGreaterThanOrEqual(0);
      expect(trade.entryTime).toBeLessThanOrEqual(trade.exitTime);
    }
  });

  it("backtest is deterministic: same input → same output", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    const report1 = runBacktest(candles, dsl);
    const report2 = runBacktest(candles, dsl);

    expect(report1.trades).toBe(report2.trades);
    expect(report1.wins).toBe(report2.wins);
    expect(report1.winrate).toBe(report2.winrate);
    expect(report1.totalPnlPct).toBe(report2.totalPnlPct);
    expect(report1.maxDrawdownPct).toBe(report2.maxDrawdownPct);
    expect(report1.tradeLog).toEqual(report2.tradeLog);
  });

  it("backtest with fees produces different PnL than without", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    const noFees = runBacktest(candles, dsl);
    const withFees = runBacktest(candles, dsl, { feeBps: 10, slippageBps: 5 });

    // Both should produce trades
    expect(noFees.trades).toBeGreaterThan(0);
    expect(withFees.trades).toBeGreaterThan(0);

    // Fees should reduce PnL (or at minimum change it)
    if (noFees.trades > 0 && withFees.trades > 0) {
      expect(withFees.totalPnlPct).not.toBe(noFees.totalPnlPct);
    }
  });

  it("DSL v2 trend mode produces trades on uptrend with dynamic side", () => {
    const candles = makeStrongUptrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();
    const report = runBacktest(candles, dsl);

    expect(report.candles).toBe(100);
    expect(report.trades).toBeGreaterThan(0);

    // In a strong uptrend, close > EMA(50) → sideCondition should pick "long"
    for (const trade of report.tradeLog) {
      expect(trade.side).toBe("long");
    }
  });

  it("DSL v2 trend mode produces short trades on downtrend", () => {
    const candles = makeStrongDowntrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();
    const report = runBacktest(candles, dsl);

    expect(report.candles).toBe(100);
    expect(report.trades).toBeGreaterThan(0);

    // In a strong downtrend, close < EMA(50) → sideCondition should pick "short"
    for (const trade of report.tradeLog) {
      expect(trade.side).toBe("short");
    }
  });

  it("no trades fire with insufficient candles for ADX warm-up", () => {
    // ADX(14) needs 2*14-1 = 27 bars minimum warm-up
    const candles = makeStrongUptrend(20);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const report = runBacktest(candles, dsl);

    expect(report.trades).toBe(0);
  });

  it("entry only fires after ADX becomes available (bar >= 27)", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const report = runBacktest(candles, dsl);

    if (report.trades > 0) {
      const firstEntry = report.tradeLog[0];
      // ADX warm-up: first value at bar 27 (index 27, openTime = base + 27*60000)
      const minEntryTime = 1_700_000_000_000 + 27 * 60_000;
      expect(firstEntry.entryTime).toBeGreaterThanOrEqual(minEntryTime);
    }
  });
});

// ---------------------------------------------------------------------------
// 3. Runtime pipeline: signal engine + exit engine
// ---------------------------------------------------------------------------

describe("Adaptive Regime Bot — signal engine", () => {
  it("generates entry signal on strong uptrend with v1 DSL", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    // Slide a window to find when signal first fires
    let signal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) break;
    }

    expect(signal).not.toBeNull();
    expect(signal!.action).toBe("open");
    expect(signal!.side).toBe("long");
    expect(signal!.price).toBeGreaterThan(0);
    expect(signal!.slPrice).toBeLessThan(signal!.price);
    expect(signal!.tpPrice).toBeGreaterThan(signal!.price);
    expect(signal!.signalType).toBe("compare");
  });

  it("generates entry signal with v2 DSL and sideCondition", () => {
    const candles = makeStrongUptrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();

    let signal = null;
    for (let end = 50; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) break;
    }

    expect(signal).not.toBeNull();
    expect(signal!.side).toBe("long");
    expect(signal!.signalType).toBe("compare");
  });

  it("returns null when position is already open", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const position = makePosition({ status: "OPEN" });

    // Even with strong trend, no signal when position exists
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position });
      expect(signal).toBeNull();
    }
  });

  it("generateOpenIntent produces valid BotIntent descriptor", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    let intent = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      intent = generateOpenIntent(
        { candles: window, dslJson: dsl, position: null },
        { botRunId: "run-arb-1", symbol: "BTCUSDT", sizingQty: 0.01 },
      );
      if (intent) break;
    }

    expect(intent).not.toBeNull();
    expect(intent!.type).toBe("ENTRY");
    expect(intent!.side).toBe("BUY");
    expect(intent!.qty).toBe(0.01);
    expect(intent!.price).toBeGreaterThan(0);
    expect(intent!.intentId).toContain("entry_");
  });

  it("signal engine is deterministic across multiple calls", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const a = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      const b = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      expect(a).toEqual(b);
    }
  });
});

describe("Adaptive Regime Bot — exit engine", () => {
  it("triggers SL exit when price drops below stop loss", () => {
    // Create a position with known SL/TP levels
    const entryPrice = 200;
    const slPct = 2;
    const slPrice = entryPrice * (1 - slPct / 100); // 196
    const tpPrice = entryPrice * (1 + 4 / 100); // 208

    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice,
      tpPrice,
    });

    // Create a candle that drops below SL
    const candles = [
      { openTime: 1_700_000_000_000, open: 200, high: 201, low: 195, close: 196, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(entryPrice),
    });

    expect(result).not.toBeNull();
    expect(result!.action).toBe("close");
    expect(result!.reason).toBe("sl");
    expect(result!.price).toBe(slPrice);
  });

  it("triggers TP exit when price rises above take profit", () => {
    const entryPrice = 200;
    const slPrice = entryPrice * (1 - 2 / 100); // 196
    const tpPrice = entryPrice * (1 + 4 / 100); // 208

    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice,
      tpPrice,
    });

    // Candle that reaches TP
    const candles = [
      { openTime: 1_700_000_000_000, open: 205, high: 210, low: 204, close: 209, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 5,
      trailingState: createTrailingStopState(entryPrice),
    });

    expect(result).not.toBeNull();
    expect(result!.action).toBe("close");
    expect(result!.reason).toBe("tp");
    expect(result!.price).toBe(tpPrice);
  });

  it("returns null when price is between SL and TP", () => {
    const entryPrice = 200;
    const slPrice = entryPrice * (1 - 2 / 100);
    const tpPrice = entryPrice * (1 + 4 / 100);

    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice,
      tpPrice,
    });

    // Candle that stays between SL and TP
    const candles = [
      { openTime: 1_700_000_000_000, open: 201, high: 203, low: 199, close: 202, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 3,
      trailingState: createTrailingStopState(entryPrice),
    });

    expect(result).toBeNull();
  });

  it("SL has higher priority than TP when both trigger on same candle", () => {
    const entryPrice = 200;
    const slPrice = entryPrice * (1 - 2 / 100); // 196
    const tpPrice = entryPrice * (1 + 4 / 100); // 208

    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice,
      tpPrice,
    });

    // Wide candle that hits both SL and TP
    const candles = [
      { openTime: 1_700_000_000_000, open: 200, high: 210, low: 190, close: 200, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(entryPrice),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("sl");
  });

  it("returns null for closed position", () => {
    const position = makePosition({ status: "CLOSED" });
    const candles = [
      { openTime: 1_700_000_000_000, open: 200, high: 300, low: 100, close: 200, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeAdaptiveRegimeLongOnlyDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(200),
    });

    expect(result).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 4. Parity: signal engine ↔ backtest evaluator
// ---------------------------------------------------------------------------

describe("Adaptive Regime Bot — parity", () => {
  it("signal engine fires at same candle as backtest first entry (v1 DSL)", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);

    const firstTradeTime = report.tradeLog[0].entryTime;

    // Find when signal engine fires
    let signalTime: number | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        signalTime = signal.triggerTime;
        break;
      }
    }

    expect(signalTime).not.toBeNull();
    expect(signalTime).toBe(firstTradeTime);
  });

  it("signal engine fires at same candle as backtest first entry (v2 DSL)", () => {
    const candles = makeStrongUptrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);

    const firstTradeTime = report.tradeLog[0].entryTime;

    let signalTime: number | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        signalTime = signal.triggerTime;
        break;
      }
    }

    expect(signalTime).not.toBeNull();
    expect(signalTime).toBe(firstTradeTime);
  });

  it("backtest entry side matches signal engine side on uptrend (v2)", () => {
    const candles = makeStrongUptrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);

    const firstTradeSide = report.tradeLog[0].side;

    let signalSide: string | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        signalSide = signal.side;
        break;
      }
    }

    expect(signalSide).toBe(firstTradeSide);
  });

  it("backtest entry side matches signal engine side on downtrend (v2)", () => {
    const candles = makeStrongDowntrend(100);
    const dsl = makeAdaptiveRegimeTrendDsl();

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);

    const firstTradeSide = report.tradeLog[0].side;

    let signalSide: string | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        signalSide = signal.side;
        break;
      }
    }

    expect(signalSide).toBe(firstTradeSide);
  });
});
