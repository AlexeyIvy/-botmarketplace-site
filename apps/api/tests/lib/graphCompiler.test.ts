import { describe, it, expect } from "vitest";
import { compileGraph } from "../../src/lib/graphCompiler.js";
import {
  makeMinimalValidGraph,
  makeGraphMissingCandles,
  makeGraphMissingEntry,
  makeGraphDualEntry,
  makeEmptyGraph,
} from "../fixtures/graphs.js";

const STRATEGY_ID = "test-strat-001";
const NAME = "Test Strategy";
const SYMBOL = "BTCUSDT";
const TIMEFRAME = "M15";

describe("graphCompiler – compileGraph", () => {
  // ── Success cases ────────────────────────────────────────────────────────

  it("compiles a minimal valid graph to DSL", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.compiledDsl).toBeDefined();
    expect(result.compiledDsl["id"]).toBe(STRATEGY_ID);
    expect(result.compiledDsl["name"]).toBe(NAME);
    expect(result.compiledDsl["dslVersion"]).toBe(1);
    expect(result.compiledDsl["enabled"]).toBe(true);
  });

  it("sets correct market fields from arguments", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    if (!result.ok) throw new Error("Expected compile success");

    const market = result.compiledDsl["market"] as Record<string, unknown>;
    expect(market["exchange"]).toBe("bybit");
    expect(market["env"]).toBe("demo");
    expect(market["category"]).toBe("linear");
    expect(market["symbol"]).toBe(SYMBOL);
  });

  it("extracts entry side as Buy for enter_long block", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    if (!result.ok) throw new Error("Expected compile success");

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    expect(entry["side"]).toBe("Buy");
  });

  it("extracts indicators from graph nodes", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    if (!result.ok) throw new Error("Expected compile success");

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<{ type: string; length: number }>;
    expect(indicators).toHaveLength(2);
    expect(indicators[0].type).toBe("SMA");
    expect(indicators[0].length).toBe(10);
    expect(indicators[1].type).toBe("SMA");
    expect(indicators[1].length).toBe(20);
  });

  it("extracts crossover signal info", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    if (!result.ok) throw new Error("Expected compile success");

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const signal = entry["signal"] as Record<string, unknown>;
    expect(signal["type"]).toBe("crossover");
    expect(signal["fast"]).toBeTruthy();
    expect(signal["slow"]).toBeTruthy();
  });

  it("extracts stop loss and take profit values", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    if (!result.ok) throw new Error("Expected compile success");

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const sl = entry["stopLoss"] as Record<string, unknown>;
    const tp = entry["takeProfit"] as Record<string, unknown>;
    expect(sl["type"]).toBe("fixed");
    expect(sl["value"]).toBe(2.0);
    expect(tp["type"]).toBe("fixed");
    expect(tp["value"]).toBe(4.0);
  });

  it("includes default execution, risk, and guards sections", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    if (!result.ok) throw new Error("Expected compile success");

    expect(result.compiledDsl["execution"]).toBeDefined();
    expect(result.compiledDsl["risk"]).toBeDefined();
    expect(result.compiledDsl["guards"]).toBeDefined();

    const guards = result.compiledDsl["guards"] as Record<string, unknown>;
    expect(guards["maxOpenPositions"]).toBe(1);
    expect(guards["pauseOnError"]).toBe(true);
  });

  it("compiled DSL passes schema validation (no schema errors)", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    // If compileGraph returns ok:true, it already passed validateDsl internally.
    // This test verifies the integration between compiler and validator.
    expect(result.ok).toBe(true);
    expect(result.validationIssues.every((i) => i.severity !== "error")).toBe(true);
  });

  // ── Failure cases ────────────────────────────────────────────────────────

  it("fails when candles block is missing", () => {
    const result = compileGraph(makeGraphMissingCandles(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    expect(result.validationIssues.some((i) => i.message.includes("Candles"))).toBe(true);
  });

  it("fails when entry block is missing", () => {
    const result = compileGraph(makeGraphMissingEntry(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    expect(result.validationIssues.some((i) => i.message.includes("Enter Long or Enter Short"))).toBe(true);
  });

  it("fails when both enter_long and enter_short are present", () => {
    const result = compileGraph(makeGraphDualEntry(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    expect(result.validationIssues.some((i) => i.message.includes("both Enter Long and Enter Short"))).toBe(true);
  });

  it("fails on empty graph", () => {
    const result = compileGraph(makeEmptyGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    // Must have at least candles + entry errors
    expect(result.validationIssues.length).toBeGreaterThanOrEqual(2);
  });

  it("returns multiple errors when several required blocks are missing", () => {
    const result = compileGraph(makeEmptyGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    const errors = result.validationIssues.filter((i) => i.severity === "error");
    // Missing: candles, entry, stop_loss, take_profit
    expect(errors.length).toBeGreaterThanOrEqual(3);
  });
});
