/**
 * Shared graph fixtures for compiler tests.
 */

import type { GraphJson } from "../../src/lib/compiler/index.js";

/**
 * Minimal valid graph: candles → SMA(10) → SMA(20) → cross → enter_long ← stop_loss + take_profit
 */
export function makeMinimalValidGraph(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: { symbol: "BTCUSDT", interval: "M15" } } },
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
}

/** Graph missing candles block. */
export function makeGraphMissingCandles(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "enter_long", params: {} } },
      { id: "n2", data: { blockType: "stop_loss", params: { type: "fixed", value: 1 } } },
      { id: "n3", data: { blockType: "take_profit", params: { type: "fixed", value: 2 } } },
    ],
    edges: [
      { id: "e1", source: "n2", target: "n1", sourceHandle: null, targetHandle: "risk" },
    ],
  };
}

/** Graph with no entry block. */
export function makeGraphMissingEntry(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: { symbol: "BTCUSDT", interval: "M15" } } },
      { id: "n2", data: { blockType: "stop_loss", params: { type: "fixed", value: 1 } } },
      { id: "n3", data: { blockType: "take_profit", params: { type: "fixed", value: 2 } } },
    ],
    edges: [],
  };
}

/** Graph with both enter_long and enter_short (invalid in Phase 4). */
export function makeGraphDualEntry(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: {} } },
      { id: "n2", data: { blockType: "enter_long", params: {} } },
      { id: "n3", data: { blockType: "enter_short", params: {} } },
      { id: "n4", data: { blockType: "stop_loss", params: { type: "fixed", value: 1 } } },
      { id: "n5", data: { blockType: "take_profit", params: { type: "fixed", value: 2 } } },
    ],
    edges: [],
  };
}

/** Empty graph. */
export function makeEmptyGraph(): GraphJson {
  return { nodes: [], edges: [] };
}

// ---------------------------------------------------------------------------
// Stage 2 indicator graphs (#125)
// ---------------------------------------------------------------------------

/** Graph with VWAP indicator: candles → VWAP → cross(vwap, SMA) → enter_long ← SL + TP */
export function makeGraphWithVWAP(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: { symbol: "BTCUSDT", interval: "M15" } } },
      { id: "n2", data: { blockType: "vwap", params: {} } },
      { id: "n3", data: { blockType: "SMA", params: { length: 20 } } },
      { id: "n4", data: { blockType: "cross", params: { mode: "crossover" } } },
      { id: "n5", data: { blockType: "enter_long", params: {} } },
      { id: "n6", data: { blockType: "stop_loss", params: { type: "fixed", value: 1.5 } } },
      { id: "n7", data: { blockType: "take_profit", params: { type: "fixed", value: 3.0 } } },
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
}

/** Graph with ADX indicator: candles → ADX(14) → compare(adx > 25) → enter_long ← SL + TP */
export function makeGraphWithADX(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: { symbol: "BTCUSDT", interval: "H1" } } },
      { id: "n2", data: { blockType: "adx", params: { period: 14 } } },
      { id: "n3", data: { blockType: "constant", params: { value: 25 } } },
      { id: "n4", data: { blockType: "compare", params: { op: ">" } } },
      { id: "n5", data: { blockType: "enter_long", params: {} } },
      { id: "n6", data: { blockType: "stop_loss", params: { type: "fixed", value: 2.0 } } },
      { id: "n7", data: { blockType: "take_profit", params: { type: "fixed", value: 4.0 } } },
    ],
    edges: [
      { id: "e1", source: "n1", target: "n2", sourceHandle: null, targetHandle: null },
      { id: "e2", source: "n2", target: "n4", sourceHandle: "adx", targetHandle: "a" },
      { id: "e3", source: "n3", target: "n4", sourceHandle: "value", targetHandle: "b" },
      { id: "e4", source: "n4", target: "n5", sourceHandle: null, targetHandle: "signal" },
      { id: "e5", source: "n6", target: "n5", sourceHandle: null, targetHandle: "risk" },
      { id: "e6", source: "n7", target: "n5", sourceHandle: null, targetHandle: null },
    ],
  };
}

/**
 * Adaptive Regime Bot — trend mode graph.
 * candles → ADX(14) → compare(adx > 25) → enter_long ← stop_loss(2%) + take_profit(4%)
 *
 * This represents the trend-detection entry: when ADX > 25 (strong trend), enter long.
 * Used for graph → compile → DSL pipeline validation.
 */
export function makeAdaptiveRegimeBotGraph(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: { symbol: "BTCUSDT", interval: "M5" } } },
      { id: "n2", data: { blockType: "adx", params: { period: 14 } } },
      { id: "n3", data: { blockType: "constant", params: { value: 25 } } },
      { id: "n4", data: { blockType: "compare", params: { op: ">" } } },
      { id: "n5", data: { blockType: "enter_long", params: {} } },
      { id: "n6", data: { blockType: "stop_loss", params: { type: "fixed", value: 2.0 } } },
      { id: "n7", data: { blockType: "take_profit", params: { type: "fixed", value: 4.0 } } },
    ],
    edges: [
      { id: "e1", source: "n1", target: "n2", sourceHandle: null, targetHandle: null },
      { id: "e2", source: "n2", target: "n4", sourceHandle: "adx", targetHandle: "a" },
      { id: "e3", source: "n3", target: "n4", sourceHandle: "value", targetHandle: "b" },
      { id: "e4", source: "n4", target: "n5", sourceHandle: null, targetHandle: "signal" },
      { id: "e5", source: "n6", target: "n5", sourceHandle: null, targetHandle: "risk" },
      { id: "e6", source: "n7", target: "n5", sourceHandle: null, targetHandle: null },
    ],
  };
}

/** Graph with SuperTrend indicator: candles → SuperTrend(10,3) → compare → enter_short ← SL + TP */
export function makeGraphWithSuperTrend(): GraphJson {
  return {
    nodes: [
      { id: "n1", data: { blockType: "candles", params: { symbol: "ETHUSDT", interval: "M15" } } },
      { id: "n2", data: { blockType: "supertrend", params: { atrPeriod: 10, multiplier: 3 } } },
      { id: "n3", data: { blockType: "constant", params: { value: 0 } } },
      { id: "n4", data: { blockType: "compare", params: { op: "<" } } },
      { id: "n5", data: { blockType: "enter_short", params: {} } },
      { id: "n6", data: { blockType: "stop_loss", params: { type: "fixed", value: 1.0 } } },
      { id: "n7", data: { blockType: "take_profit", params: { type: "fixed", value: 2.0 } } },
    ],
    edges: [
      { id: "e1", source: "n1", target: "n2", sourceHandle: null, targetHandle: null },
      { id: "e2", source: "n2", target: "n4", sourceHandle: "direction", targetHandle: "a" },
      { id: "e3", source: "n3", target: "n4", sourceHandle: "value", targetHandle: "b" },
      { id: "e4", source: "n4", target: "n5", sourceHandle: null, targetHandle: "signal" },
      { id: "e5", source: "n6", target: "n5", sourceHandle: null, targetHandle: "risk" },
      { id: "e6", source: "n7", target: "n5", sourceHandle: null, targetHandle: null },
    ],
  };
}
