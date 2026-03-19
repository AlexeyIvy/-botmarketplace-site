// ---------------------------------------------------------------------------
// Phase B1-1 — Hardcoded graph templates for empty canvas onboarding
// Chain: Candles → EMA(9) → EMA(21) → Cross → EnterLong + StopLoss(1%) + TakeProfit(2%)
// ---------------------------------------------------------------------------

import type { LabNode, LabEdge } from "../useLabGraphStore";
import type { LabNodeData } from "./blockDefs";
import type { StrategyEdgeData } from "./edges/StrategyEdge";
import type { PortDataType } from "./blockDefs";

interface GraphTemplate {
  id: string;
  label: string;
  description: string;
  nodes: LabNode[];
  edges: LabEdge[];
}

const EMA_CROSSOVER_NODES: LabNode[] = [
  {
    id: "tpl_candles",
    type: "strategyNode",
    position: { x: 60, y: 200 },
    data: { blockType: "candles", params: {}, isStale: false } as LabNodeData,
  },
  {
    id: "tpl_ema9",
    type: "strategyNode",
    position: { x: 300, y: 100 },
    data: { blockType: "EMA", params: { length: 9 }, isStale: false } as LabNodeData,
  },
  {
    id: "tpl_ema21",
    type: "strategyNode",
    position: { x: 300, y: 300 },
    data: { blockType: "EMA", params: { length: 21 }, isStale: false } as LabNodeData,
  },
  {
    id: "tpl_cross",
    type: "strategyNode",
    position: { x: 540, y: 200 },
    data: { blockType: "cross", params: { mode: "crossover" }, isStale: false } as LabNodeData,
  },
  {
    id: "tpl_sl",
    type: "strategyNode",
    position: { x: 540, y: 400 },
    data: { blockType: "stop_loss", params: { type: "fixed", value: 1 }, isStale: false } as LabNodeData,
  },
  {
    id: "tpl_tp",
    type: "strategyNode",
    position: { x: 540, y: 540 },
    data: { blockType: "take_profit", params: { type: "fixed", value: 2 }, isStale: false } as LabNodeData,
  },
  {
    id: "tpl_enter",
    type: "strategyNode",
    position: { x: 800, y: 300 },
    data: { blockType: "enter_long", params: {}, isStale: false } as LabNodeData,
  },
];

function tplEdge(
  id: string,
  source: string,
  sourceHandle: string,
  target: string,
  targetHandle: string,
  dataType: PortDataType,
): LabEdge {
  return {
    id,
    source,
    sourceHandle,
    target,
    targetHandle,
    type: "strategyEdge",
    data: { dataType, isStale: false, isInvalid: false } as StrategyEdgeData,
  };
}

const EMA_CROSSOVER_EDGES: LabEdge[] = [
  // Candles → EMA(9)
  tplEdge("tpl_e1", "tpl_candles", "candles_out", "tpl_ema9", "candles", "Series<OHLCV>"),
  // Candles → EMA(21)
  tplEdge("tpl_e2", "tpl_candles", "candles_out", "tpl_ema21", "candles", "Series<OHLCV>"),
  // EMA(9) → Cross.a
  tplEdge("tpl_e3", "tpl_ema9", "ema", "tpl_cross", "a", "Series<number>"),
  // EMA(21) → Cross.b
  tplEdge("tpl_e4", "tpl_ema21", "ema", "tpl_cross", "b", "Series<number>"),
  // Cross → EnterLong.signal
  tplEdge("tpl_e5", "tpl_cross", "signal", "tpl_enter", "signal", "Series<boolean>"),
  // Candles → StopLoss
  tplEdge("tpl_e6", "tpl_candles", "candles_out", "tpl_sl", "candles", "Series<OHLCV>"),
  // Candles → TakeProfit
  tplEdge("tpl_e7", "tpl_candles", "candles_out", "tpl_tp", "candles", "Series<OHLCV>"),
  // StopLoss → EnterLong.risk
  tplEdge("tpl_e8", "tpl_sl", "risk", "tpl_enter", "risk", "RiskParams"),
  // TakeProfit — second risk param not supported by Enter Long (single risk input),
  // so we leave TP unconnected as a visual reference. Users can rewire as needed.
];

export const GRAPH_TEMPLATES: GraphTemplate[] = [
  {
    id: "ema-crossover",
    label: "EMA Crossover",
    description: "Candles → EMA(9) → EMA(21) → Cross → Enter Long + Stop Loss(1%)",
    nodes: EMA_CROSSOVER_NODES,
    edges: EMA_CROSSOVER_EDGES,
  },
];

export function getTemplate(id: string): GraphTemplate | undefined {
  return GRAPH_TEMPLATES.find((t) => t.id === id);
}
