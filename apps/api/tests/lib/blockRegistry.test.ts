import { describe, it, expect } from "vitest";
import {
  BlockRegistry,
  createRegistry,
  defaultHandlers,
  compileGraph,
  compileGraphWithRegistry,
} from "../../src/lib/compiler/index.js";
import type { BlockHandler, GraphJson } from "../../src/lib/compiler/index.js";
import { makeMinimalValidGraph } from "../fixtures/graphs.js";

const STRATEGY_ID = "test-strat-001";
const NAME = "Test Strategy";
const SYMBOL = "BTCUSDT";
const TIMEFRAME = "M15";

// ---------------------------------------------------------------------------
// BlockRegistry unit tests
// ---------------------------------------------------------------------------

describe("BlockRegistry", () => {
  it("registers and retrieves a handler", () => {
    const registry = new BlockRegistry();
    const handler: BlockHandler = {
      blockType: "test_block",
      category: "input",
      validate() {},
      extract() {
        return { data: true };
      },
    };
    registry.register(handler);
    expect(registry.has("test_block")).toBe(true);
    expect(registry.get("test_block")).toBe(handler);
  });

  it("throws on duplicate registration", () => {
    const registry = new BlockRegistry();
    const handler: BlockHandler = {
      blockType: "dup",
      category: "input",
      validate() {},
      extract() {
        return {};
      },
    };
    registry.register(handler);
    expect(() => registry.register(handler)).toThrow("duplicate handler");
  });

  it("returns undefined for unregistered type", () => {
    const registry = new BlockRegistry();
    expect(registry.get("nonexistent")).toBeUndefined();
    expect(registry.has("nonexistent")).toBe(false);
  });

  it("lists all registered types", () => {
    const registry = createRegistry(defaultHandlers());
    const types = registry.registeredTypes();
    expect(types).toContain("candles");
    expect(types).toContain("SMA");
    expect(types).toContain("EMA");
    expect(types).toContain("RSI");
    expect(types).toContain("cross");
    expect(types).toContain("compare");
    expect(types).toContain("enter_long");
    expect(types).toContain("enter_short");
    expect(types).toContain("stop_loss");
    expect(types).toContain("take_profit");
  });

  it("default registry covers all MVP block types", () => {
    const registry = createRegistry(defaultHandlers());
    const expectedTypes = [
      "candles", "constant",
      "SMA", "EMA", "RSI", "macd", "bollinger", "atr", "volume",
      "cross", "compare", "and_gate", "or_gate",
      "enter_long", "enter_short",
      "stop_loss", "take_profit",
    ];
    for (const t of expectedTypes) {
      expect(registry.has(t)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// Unsupported block type tests
// ---------------------------------------------------------------------------

describe("compileGraph – unsupported block types", () => {
  it("rejects a graph containing an unregistered block type", () => {
    const graph: GraphJson = {
      nodes: [
        { id: "n1", data: { blockType: "candles", params: {} } },
        { id: "n2", data: { blockType: "unknown_magic_block", params: {} } },
        { id: "n3", data: { blockType: "enter_long", params: {} } },
        { id: "n4", data: { blockType: "stop_loss", params: { type: "fixed", value: 1 } } },
        { id: "n5", data: { blockType: "take_profit", params: { type: "fixed", value: 2 } } },
      ],
      edges: [],
    };
    const result = compileGraph(graph, STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    expect(
      result.validationIssues.some((i) =>
        i.message.includes("Unsupported block type") && i.message.includes("unknown_magic_block")
      ),
    ).toBe(true);
  });

  it("error for unsupported block includes the nodeId", () => {
    const graph: GraphJson = {
      nodes: [
        { id: "n1", data: { blockType: "candles", params: {} } },
        { id: "n99", data: { blockType: "mystery", params: {} } },
      ],
      edges: [],
    };
    const result = compileGraph(graph, STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(false);
    const unsupported = result.validationIssues.find((i) => i.message.includes("mystery"));
    expect(unsupported?.nodeId).toBe("n99");
  });
});

// ---------------------------------------------------------------------------
// Custom handler registration test
// ---------------------------------------------------------------------------

describe("compileGraphWithRegistry – custom handlers", () => {
  it("accepts a custom block type via a custom registry", () => {
    const customHandler: BlockHandler = {
      blockType: "custom_indicator",
      category: "indicator",
      validate() {},
      extract() {
        return { indicators: [{ type: "custom_indicator", nodeId: "nc", customParam: 42 }] };
      },
    };

    const handlers = [...defaultHandlers(), customHandler];
    const registry = createRegistry(handlers);

    // Graph with the custom block type
    const graph: GraphJson = {
      nodes: [
        { id: "n1", data: { blockType: "candles", params: {} } },
        { id: "nc", data: { blockType: "custom_indicator", params: { customParam: 42 } } },
        { id: "n2", data: { blockType: "SMA", params: { length: 10 } } },
        { id: "n3", data: { blockType: "SMA", params: { length: 20 } } },
        { id: "n4", data: { blockType: "cross", params: { mode: "crossover" } } },
        { id: "n5", data: { blockType: "enter_long", params: {} } },
        { id: "n6", data: { blockType: "stop_loss", params: { type: "fixed", value: 2.0 } } },
        { id: "n7", data: { blockType: "take_profit", params: { type: "fixed", value: 4.0 } } },
      ],
      edges: [
        { id: "e1", source: "n1", target: "n2", sourceHandle: null, targetHandle: null },
        { id: "e2", source: "n1", target: "n3", sourceHandle: null, targetHandle: null },
        { id: "e3", source: "n2", target: "n4", sourceHandle: null, targetHandle: "a" },
        { id: "e4", source: "n3", target: "n4", sourceHandle: null, targetHandle: "b" },
        { id: "e5", source: "n4", target: "n5", sourceHandle: null, targetHandle: "signal" },
        { id: "e6", source: "n6", target: "n5", sourceHandle: null, targetHandle: "risk" },
        { id: "e7", source: "n7", target: "n5", sourceHandle: null, targetHandle: null },
      ],
    };

    const result = compileGraphWithRegistry(registry, graph, STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    // The custom indicator should appear in the indicators array
    const entry = result.compiledDsl["entry"] as Record<string, unknown>;
    const indicators = entry["indicators"] as Array<Record<string, unknown>>;
    expect(indicators.some((ind) => ind["type"] === "custom_indicator")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Golden tests — DSL output stability
// ---------------------------------------------------------------------------

describe("compileGraph – golden output stability", () => {
  it("minimal valid graph produces stable DSL output", () => {
    const result = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    // Snapshot the full DSL structure
    expect(result.compiledDsl).toEqual({
      id: "test-strat-001",
      name: "Test Strategy",
      dslVersion: 1,
      enabled: true,
      market: {
        exchange: "bybit",
        env: "demo",
        category: "linear",
        symbol: "BTCUSDT",
      },
      timeframes: ["M15"],
      entry: {
        side: "Buy",
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", nodeId: "n2", length: 10 },
          slow: { blockType: "SMA", nodeId: "n3", length: 20 },
        },
        indicators: [
          { type: "SMA", length: 10, nodeId: "n2" },
          { type: "SMA", length: 20, nodeId: "n3" },
        ],
        order: { type: "Market", maxSlippageBps: 50 },
        stopLoss: { type: "fixed", value: 2.0 },
        takeProfit: { type: "fixed", value: 4.0 },
      },
      risk: {
        maxPositionSizeUsd: 100,
        cooldownSeconds: 60,
        riskPerTradePct: 2.0,
      },
      execution: {
        orderType: "Market",
        clientOrderIdPrefix: "lab_",
        maxSlippageBps: 50,
      },
      guards: {
        maxOpenPositions: 1,
        maxOrdersPerMinute: 10,
        pauseOnError: true,
      },
    });
  });

  it("enter_short graph produces Sell side with correct DSL shape", () => {
    const graph: GraphJson = {
      nodes: [
        { id: "n1", data: { blockType: "candles", params: {} } },
        { id: "n2", data: { blockType: "RSI", params: { length: 14 } } },
        { id: "n3", data: { blockType: "constant", params: { value: 70 } } },
        { id: "n4", data: { blockType: "compare", params: { op: ">" } } },
        { id: "n5", data: { blockType: "enter_short", params: {} } },
        { id: "n6", data: { blockType: "stop_loss", params: { type: "fixed", value: 1.5 } } },
        { id: "n7", data: { blockType: "take_profit", params: { type: "fixed", value: 3.0 } } },
      ],
      edges: [
        { id: "e1", source: "n1", target: "n2", sourceHandle: null, targetHandle: null },
        { id: "e2", source: "n2", target: "n4", sourceHandle: null, targetHandle: "a" },
        { id: "e3", source: "n3", target: "n4", sourceHandle: null, targetHandle: "b" },
        { id: "e4", source: "n4", target: "n5", sourceHandle: null, targetHandle: "signal" },
        { id: "e5", source: "n6", target: "n5", sourceHandle: null, targetHandle: "risk" },
      ],
    };

    const result = compileGraph(graph, "strat-short-001", "Short RSI", "ETHUSDT", "H1");
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.compiledDsl).toEqual({
      id: "strat-short-001",
      name: "Short RSI",
      dslVersion: 1,
      enabled: true,
      market: {
        exchange: "bybit",
        env: "demo",
        category: "linear",
        symbol: "ETHUSDT",
      },
      timeframes: ["H1"],
      entry: {
        side: "Sell",
        signal: {
          type: "compare",
          op: ">",
          left: { blockType: "RSI", nodeId: "n2", length: 14 },
          right: { blockType: "constant", nodeId: "n3", length: 70 },
        },
        indicators: [
          { type: "RSI", length: 14, nodeId: "n2" },
        ],
        order: { type: "Market", maxSlippageBps: 50 },
        stopLoss: { type: "fixed", value: 1.5 },
        takeProfit: { type: "fixed", value: 3.0 },
      },
      risk: {
        maxPositionSizeUsd: 100,
        cooldownSeconds: 60,
        riskPerTradePct: 1.5,
      },
      execution: {
        orderType: "Market",
        clientOrderIdPrefix: "lab_",
        maxSlippageBps: 50,
      },
      guards: {
        maxOpenPositions: 1,
        maxOrdersPerMinute: 10,
        pauseOnError: true,
      },
    });
  });
});

// ---------------------------------------------------------------------------
// Legacy re-export compatibility
// ---------------------------------------------------------------------------

describe("legacy graphCompiler re-export", () => {
  it("compileGraph from legacy path produces identical output", async () => {
    const legacy = await import("../../src/lib/graphCompiler.js");
    const resultNew = compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);
    const resultLegacy = legacy.compileGraph(makeMinimalValidGraph(), STRATEGY_ID, NAME, SYMBOL, TIMEFRAME);

    expect(resultNew.ok).toBe(true);
    expect(resultLegacy.ok).toBe(true);
    if (resultNew.ok && resultLegacy.ok) {
      expect(resultNew.compiledDsl).toEqual(resultLegacy.compiledDsl);
    }
  });
});
