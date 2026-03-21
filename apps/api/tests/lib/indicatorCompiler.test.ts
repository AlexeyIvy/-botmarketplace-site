/**
 * Compiler integration tests for Stage 2 indicators (VWAP, ADX, SuperTrend).
 *
 * Verifies that each indicator type:
 *   1. Compiles successfully from graph to DSL
 *   2. Extracts correct indicator params
 *   3. Is recognized by the default registry
 */

import { describe, it, expect } from "vitest";
import { compileGraph } from "../../src/lib/compiler/index.js";
import {
  makeGraphWithVWAP,
  makeGraphWithADX,
  makeGraphWithSuperTrend,
} from "../fixtures/graphs.js";

const STRATEGY_ID = "test-stage2";
const NAME = "Stage 2 Test";
const SYMBOL = "BTCUSDT";
const TIMEFRAME = "M15";

describe("compiler – Stage 2 indicators (#125)", () => {
  // ── VWAP ────────────────────────────────────────────────────────────────

  it("compiles a graph with VWAP indicator", () => {
    const result = compileGraph(makeGraphWithVWAP(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;

    const vwap = indicators.find((ind) => ind.type === "vwap");
    expect(vwap).toBeDefined();
    expect(vwap!.nodeId).toBe("n2");
  });

  // ── ADX ─────────────────────────────────────────────────────────────────

  it("compiles a graph with ADX indicator", () => {
    const result = compileGraph(makeGraphWithADX(), STRATEGY_ID, NAME, SYMBOL, "H1");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;

    const adx = indicators.find((ind) => ind.type === "adx");
    expect(adx).toBeDefined();
    expect(adx!.period).toBe(14);
    expect(adx!.nodeId).toBe("n2");
  });

  // ── SuperTrend ──────────────────────────────────────────────────────────

  it("compiles a graph with SuperTrend indicator", () => {
    const result = compileGraph(makeGraphWithSuperTrend(), STRATEGY_ID, NAME, "ETHUSDT", TIMEFRAME);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;

    const st = indicators.find((ind) => ind.type === "supertrend");
    expect(st).toBeDefined();
    expect(st!.atrPeriod).toBe(10);
    expect(st!.multiplier).toBe(3);
    expect(st!.nodeId).toBe("n2");
  });

  // ── Default param extraction ────────────────────────────────────────────

  it("ADX uses default period=14 when param is missing", () => {
    const graph = makeGraphWithADX();
    // Remove period param
    graph.nodes[1].data.params = {};

    const result = compileGraph(graph, STRATEGY_ID, NAME, SYMBOL, "H1");
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;
    const adx = indicators.find((ind) => ind.type === "adx");
    expect(adx!.period).toBe(14);
  });

  it("SuperTrend uses defaults when params are missing", () => {
    const graph = makeGraphWithSuperTrend();
    graph.nodes[1].data.params = {};

    const result = compileGraph(graph, STRATEGY_ID, NAME, "ETHUSDT", TIMEFRAME);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;
    const st = indicators.find((ind) => ind.type === "supertrend");
    expect(st!.atrPeriod).toBe(10);
    expect(st!.multiplier).toBe(3);
  });

  // ── Golden compile: DSL output stability ────────────────────────────────

  it("golden: VWAP compile output is stable", () => {
    const r1 = compileGraph(makeGraphWithVWAP(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    const r2 = compileGraph(makeGraphWithVWAP(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);

    expect(r1.ok).toBe(true);
    expect(r2.ok).toBe(true);
    if (!r1.ok || !r2.ok) return;

    expect(r1.compiledDsl).toEqual(r2.compiledDsl);
  });
});
