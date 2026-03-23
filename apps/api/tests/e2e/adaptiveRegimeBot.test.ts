/**
 * Adaptive Regime Bot — Trend-Mode Test Foundation (#130)
 *
 * Validates trend-mode fixtures and runtime/backtest parity for the
 * Adaptive Regime Bot strategy.
 *
 * Current state:
 *   - Compilation tests verify graph→DSL v1 output independently.
 *   - Backtest / signal / exit / parity tests use hand-authored DSL
 *     fixtures (v1 and v2), NOT the compiler output.
 *   - Section 6 proves compiler→consumer continuity: compiled DSL fed
 *     directly into backtest and signal engine with parity checks.
 *   - The compiler emits DSL v1 only; DSL v2 (sideCondition, top-level
 *     exit) is hand-authored for now.
 *
 * NOT covered by this slice:
 *   - Adaptive regime switching (ADX zones → trend vs range mode)
 *   - Range-mode substrategy (BB + RSI)
 *   - Restart/resume/reconciliation acceptance
 *   - Demo lifecycle completeness
 *
 * All fixtures are deterministic: no randomness, no time-dependence, no I/O.
 */

import { describe, it, expect } from "vitest";
import { compileGraph } from "../../src/lib/compiler/index.js";
import { runBacktest } from "../../src/lib/backtest.js";
import {
  runDslBacktest,
  evaluateSignal,
  getIndicatorValues,
  createIndicatorCache,
} from "../../src/lib/dslEvaluator.js";
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
// 1. Compilation: graph → DSL v1 (independent of backtest/runtime tests)
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
// 2. Backtest: hand-authored DSL → deterministic results
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
// 3. Runtime: signal engine + exit engine (hand-authored DSL)
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
// 4. Parity: signal engine ↔ backtest (hand-authored DSL)
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

// ---------------------------------------------------------------------------
// 5. Compiler limitations: document remaining gaps in compiled DSL
// ---------------------------------------------------------------------------

describe("Adaptive Regime Bot — compiler limitations", () => {
  it("compiled DSL is v1 only — no sideCondition or top-level exit", () => {
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(graph, "arb-lim-1", "ARB", "BTCUSDT", "5m");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const dsl = result.compiledDsl as Record<string, unknown>;

    // Compiler currently emits DSL v1
    expect(dsl["dslVersion"]).toBe(1);

    // DSL v2 features are absent from compiled output
    const entry = dsl["entry"] as Record<string, unknown>;
    expect(entry["sideCondition"]).toBeUndefined();
    expect(dsl["exit"]).toBeUndefined();

    // Entry has fixed side (v1 style), not dynamic
    expect(entry["side"]).toBe("Buy");
  });

  it("constant block value is correctly extracted in compiled compare signal", () => {
    // Previously documented as a bug: graphCompiler used params["length"] for all
    // signal nodes, but constant blocks store their value in params["value"].
    // Fixed: compiler now uses nodeToSignalDescriptor() which maps params["value"]
    // to the DSL "length" field for constant blocks.
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(graph, "arb-lim-2", "ARB", "BTCUSDT", "5m");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const dsl = result.compiledDsl as Record<string, unknown>;
    const entry = dsl["entry"] as Record<string, unknown>;
    const signal = entry["signal"] as Record<string, unknown>;
    const right = signal["right"] as Record<string, unknown>;

    expect(right["blockType"]).toBe("constant");
    expect(right["length"]).toBe(25); // Fixed: constant value now correctly extracted
  });

  it("compiled DSL v1 vs hand-authored v2 — structural differences remain", () => {
    // Documents structural differences between compiled (v1) and hand-authored (v2) DSL.
    // Signal semantics now match, but DSL version and exit placement still differ.
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(graph, "arb-lim-3", "ARB", "BTCUSDT", "5m");
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const compiled = result.compiledDsl as Record<string, unknown>;
    const handAuthored = makeAdaptiveRegimeTrendDsl();

    // Version mismatch: compiler emits v1, hand-authored is v2
    expect(compiled["dslVersion"]).toBe(1);
    expect(handAuthored.dslVersion).toBe(2);

    // Compiled has embedded SL/TP in entry; hand-authored has top-level exit
    const compiledEntry = compiled["entry"] as Record<string, unknown>;
    expect(compiledEntry["stopLoss"]).toBeDefined();
    expect(compiledEntry["takeProfit"]).toBeDefined();
    expect(handAuthored.exit).toBeDefined();
    expect((handAuthored.entry as Record<string, unknown>)["stopLoss"]).toBeUndefined();

    // Signal semantics now match: both have ADX > 25 compare signal
    const compiledSignal = compiledEntry["signal"] as Record<string, unknown>;
    const compiledRight = compiledSignal["right"] as Record<string, unknown>;
    expect(compiledRight["length"]).toBe(25); // constant threshold preserved
  });
});

// ---------------------------------------------------------------------------
// 6. Compiler→Consumer continuity: compiled DSL fed into backtest/runtime
// ---------------------------------------------------------------------------

describe("Adaptive Regime Bot — compiler→consumer continuity", () => {
  // Helper: compile the trend-mode graph and return the DSL
  function compileTrendModeDsl() {
    const graph = makeAdaptiveRegimeBotGraph();
    const result = compileGraph(
      graph,
      "arb-continuity",
      "Adaptive Regime Bot — Compiled",
      "BTCUSDT",
      "5m",
    );
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error("Compilation failed");
    return result.compiledDsl as Record<string, unknown>;
  }

  it("graph fixture compiles successfully with correct threshold semantics", () => {
    const dsl = compileTrendModeDsl();

    expect(dsl["dslVersion"]).toBe(1);
    expect(dsl["enabled"]).toBe(true);

    const entry = dsl["entry"] as Record<string, unknown>;
    const signal = entry["signal"] as Record<string, unknown>;

    // Signal is ADX > 25 (compare type)
    expect(signal["type"]).toBe("compare");
    expect(signal["op"]).toBe(">");

    const left = signal["left"] as Record<string, unknown>;
    expect(left["blockType"]).toBe("adx");
    expect(left["length"]).toBe(14); // period extracted via fallback

    const right = signal["right"] as Record<string, unknown>;
    expect(right["blockType"]).toBe("constant");
    expect(right["length"]).toBe(25); // threshold correctly extracted from params.value

    // SL/TP embedded in entry (v1 style)
    expect(entry["stopLoss"]).toBeDefined();
    expect(entry["takeProfit"]).toBeDefined();
  });

  it("compiled DSL produces trades when fed to backtest on strong uptrend", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);

    const report = runDslBacktest(candles, dsl);

    expect(report.candles).toBe(80);
    expect(report.trades).toBeGreaterThan(0);
    expect(report.tradeLog.length).toBe(report.trades);

    // All trades should be long (compiled DSL is v1 with fixed side "Buy")
    for (const trade of report.tradeLog) {
      expect(trade.side).toBe("long");
      expect(trade.entryPrice).toBeGreaterThan(0);
      expect(trade.exitPrice).toBeGreaterThan(0);
      expect(["WIN", "LOSS", "NEUTRAL"]).toContain(trade.outcome);
      expect(["sl", "tp", "end_of_data"]).toContain(trade.exitReason);
    }
  });

  it("compiled DSL backtest is deterministic", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);

    const r1 = runDslBacktest(candles, dsl);
    const r2 = runDslBacktest(candles, dsl);

    expect(r1.trades).toBe(r2.trades);
    expect(r1.totalPnlPct).toBe(r2.totalPnlPct);
    expect(r1.tradeLog).toEqual(r2.tradeLog);
  });

  it("compiled DSL signal evaluates correctly against indicator values", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);
    const cache = createIndicatorCache();

    const entry = dsl["entry"] as Record<string, unknown>;
    const signal = entry["signal"] as { type: string; op?: string; left?: { blockType: string; length?: number } | null; right?: { blockType: string; length?: number } | null };

    // ADX values should exceed 25 at some point in a strong uptrend
    const adxVals = getIndicatorValues("adx", { period: 14 }, candles, cache);
    const constVals = getIndicatorValues("constant", { length: 25 }, candles, cache);

    // Verify constant fills correctly
    expect(constVals[0]).toBe(25);
    expect(constVals[candles.length - 1]).toBe(25);

    // Find first bar where compiled signal fires
    let firstSignalBar = -1;
    for (let i = 1; i < candles.length; i++) {
      if (evaluateSignal(signal, i, candles, cache)) {
        firstSignalBar = i;
        break;
      }
    }

    expect(firstSignalBar).toBeGreaterThan(0);

    // At the signal bar, ADX should actually be > 25
    const adxAtSignal = adxVals[firstSignalBar];
    expect(adxAtSignal).not.toBeNull();
    expect(adxAtSignal!).toBeGreaterThan(25);
  });

  it("compiled DSL signal engine fires entry on strong uptrend", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);

    let signal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) break;
    }

    expect(signal).not.toBeNull();
    expect(signal!.action).toBe("open");
    expect(signal!.side).toBe("long"); // v1 compiled DSL → always "Buy" → long
    expect(signal!.price).toBeGreaterThan(0);
    expect(signal!.slPrice).toBeLessThan(signal!.price);
    expect(signal!.tpPrice).toBeGreaterThan(signal!.price);
    expect(signal!.signalType).toBe("compare");
  });

  it("compiled DSL: signal engine fires at same candle as backtest first entry", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);

    // Backtest first entry
    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);
    const backtestFirstEntryTime = report.tradeLog[0].entryTime;

    // Signal engine first entry
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
    expect(signalTime).toBe(backtestFirstEntryTime);
  });

  it("compiled DSL: backtest entry side matches signal engine side", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBeGreaterThan(0);
    const backtestSide = report.tradeLog[0].side;

    let signalSide: string | null = null;
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        signalSide = signal.side;
        break;
      }
    }

    expect(signalSide).toBe(backtestSide);
  });

  it("compiled DSL: exit engine triggers on position from compiled artifact", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(80);

    // Use signal engine to find entry from compiled DSL
    let entrySignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      entrySignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (entrySignal) break;
    }
    expect(entrySignal).not.toBeNull();

    // Create a position based on the entry signal
    const position = makePosition({
      avgEntryPrice: entrySignal!.price,
      slPrice: entrySignal!.slPrice,
      tpPrice: entrySignal!.tpPrice,
      side: "LONG",
    });

    // Create a candle that drops below SL
    const slCandle = [
      {
        openTime: 1_700_100_000_000,
        open: entrySignal!.price,
        high: entrySignal!.price + 1,
        low: entrySignal!.slPrice - 1,
        close: entrySignal!.slPrice - 0.5,
        volume: 1000,
      },
    ];

    const exitResult = evaluateExit({
      candles: slCandle,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(entrySignal!.price),
    });

    expect(exitResult).not.toBeNull();
    expect(exitResult!.action).toBe("close");
    expect(exitResult!.reason).toBe("sl");
  });

  it("compiled DSL: no trades with insufficient ADX warm-up candles", () => {
    const dsl = compileTrendModeDsl();
    const candles = makeStrongUptrend(20); // too few for ADX(14)

    const report = runDslBacktest(candles, dsl);
    expect(report.trades).toBe(0);
  });

  it("compiled DSL backtest matches hand-authored v1 backtest results", () => {
    // Both compiled and hand-authored v1 DSL encode the same strategy:
    // ADX(14) > 25, Buy side, SL 2%, TP 4%
    // They should produce identical trade signals.
    const candles = makeStrongUptrend(80);

    const compiled = compileTrendModeDsl();
    const handAuthored = makeAdaptiveRegimeLongOnlyDsl();

    const compiledReport = runDslBacktest(candles, compiled);
    const handReport = runDslBacktest(candles, handAuthored);

    expect(compiledReport.trades).toBe(handReport.trades);
    expect(compiledReport.trades).toBeGreaterThan(0);

    // Entry timing and side should match exactly
    for (let i = 0; i < compiledReport.tradeLog.length; i++) {
      expect(compiledReport.tradeLog[i].entryTime).toBe(handReport.tradeLog[i].entryTime);
      expect(compiledReport.tradeLog[i].side).toBe(handReport.tradeLog[i].side);
      expect(compiledReport.tradeLog[i].exitReason).toBe(handReport.tradeLog[i].exitReason);
    }
  });
});
