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

// ---------------------------------------------------------------------------
// Flagship #2 — Adaptive Regime Bot (docs/strategies/03)
// ADX(14) trend filter + EMA(50) side condition → Enter Adaptive
// Trend mode: ADX > 25 → trade in EMA direction
// SL 2%, TP 4%
// ---------------------------------------------------------------------------

const ADAPTIVE_REGIME_NODES: LabNode[] = [
  {
    id: "ar_candles",
    type: "strategyNode",
    position: { x: 60, y: 250 },
    data: { blockType: "candles", params: {}, isStale: false } as LabNodeData,
  },
  {
    id: "ar_adx",
    type: "strategyNode",
    position: { x: 300, y: 100 },
    data: { blockType: "adx", params: { period: 14 }, isStale: false } as LabNodeData,
  },
  {
    id: "ar_const25",
    type: "strategyNode",
    position: { x: 300, y: 250 },
    data: { blockType: "constant", params: { value: 25 }, isStale: false } as LabNodeData,
  },
  {
    id: "ar_cmp",
    type: "strategyNode",
    position: { x: 520, y: 170 },
    data: { blockType: "compare", params: { op: ">" }, isStale: false } as LabNodeData,
  },
  {
    id: "ar_ema50",
    type: "strategyNode",
    position: { x: 300, y: 420 },
    data: { blockType: "EMA", params: { length: 50 }, isStale: false } as LabNodeData,
  },
  {
    id: "ar_sl",
    type: "strategyNode",
    position: { x: 520, y: 480 },
    data: { blockType: "stop_loss", params: { type: "fixed", value: 2.0 }, isStale: false } as LabNodeData,
  },
  {
    id: "ar_enter",
    type: "strategyNode",
    position: { x: 780, y: 300 },
    data: {
      blockType: "enter_adaptive",
      params: { source: "close", longOp: "gt", shortOp: "lt" },
      isStale: false,
    } as LabNodeData,
  },
];

const ADAPTIVE_REGIME_EDGES: LabEdge[] = [
  tplEdge("ar_e1", "ar_candles", "candles_out", "ar_adx", "candles", "Series<OHLCV>"),
  tplEdge("ar_e2", "ar_adx", "adx", "ar_cmp", "a", "Series<number>"),
  tplEdge("ar_e3", "ar_const25", "value", "ar_cmp", "b", "Series<number>"),
  tplEdge("ar_e4", "ar_cmp", "result", "ar_enter", "signal", "Series<boolean>"),
  tplEdge("ar_e5", "ar_candles", "candles_out", "ar_ema50", "candles", "Series<OHLCV>"),
  tplEdge("ar_e6", "ar_ema50", "ema", "ar_enter", "sideIndicator", "Series<number>"),
  tplEdge("ar_e7", "ar_candles", "candles_out", "ar_sl", "candles", "Series<OHLCV>"),
  tplEdge("ar_e8", "ar_sl", "risk", "ar_enter", "risk", "RiskParams"),
];

// ---------------------------------------------------------------------------
// Flagship #5 — DCA Momentum Bot (docs/strategies/06)
// SMA(5)/SMA(20) crossover → Enter Long + DCA Config (3 SOs, 1% step)
// Simple averaging strategy for beginners
// ---------------------------------------------------------------------------

const DCA_MOMENTUM_NODES: LabNode[] = [
  {
    id: "dca_candles",
    type: "strategyNode",
    position: { x: 60, y: 200 },
    data: { blockType: "candles", params: {}, isStale: false } as LabNodeData,
  },
  {
    id: "dca_sma5",
    type: "strategyNode",
    position: { x: 300, y: 100 },
    data: { blockType: "SMA", params: { length: 5 }, isStale: false } as LabNodeData,
  },
  {
    id: "dca_sma20",
    type: "strategyNode",
    position: { x: 300, y: 300 },
    data: { blockType: "SMA", params: { length: 20 }, isStale: false } as LabNodeData,
  },
  {
    id: "dca_cross",
    type: "strategyNode",
    position: { x: 540, y: 200 },
    data: { blockType: "cross", params: { mode: "crossover" }, isStale: false } as LabNodeData,
  },
  {
    id: "dca_config",
    type: "strategyNode",
    position: { x: 540, y: 420 },
    data: {
      blockType: "dca_config",
      params: {
        baseOrderSizeUsd: 100,
        maxSafetyOrders: 3,
        priceStepPct: 1.0,
        stepScale: 1.0,
        volumeScale: 1.5,
        takeProfitPct: 1.5,
      },
      isStale: false,
    } as LabNodeData,
  },
  {
    id: "dca_enter",
    type: "strategyNode",
    position: { x: 800, y: 300 },
    data: { blockType: "enter_long", params: {}, isStale: false } as LabNodeData,
  },
];

const DCA_MOMENTUM_EDGES: LabEdge[] = [
  tplEdge("dca_e1", "dca_candles", "candles_out", "dca_sma5", "candles", "Series<OHLCV>"),
  tplEdge("dca_e2", "dca_candles", "candles_out", "dca_sma20", "candles", "Series<OHLCV>"),
  tplEdge("dca_e3", "dca_sma5", "sma", "dca_cross", "a", "Series<number>"),
  tplEdge("dca_e4", "dca_sma20", "sma", "dca_cross", "b", "Series<number>"),
  tplEdge("dca_e5", "dca_cross", "signal", "dca_enter", "signal", "Series<boolean>"),
  tplEdge("dca_e6", "dca_config", "risk", "dca_enter", "risk", "RiskParams"),
];

// ---------------------------------------------------------------------------
// Flagship #4 — MTF Confluence Scalper (docs/strategies/05)
// EMA(20) on 5m context for side + SMA(5)/SMA(10) cross on 1m for entry
// SL 1%, TP 2%
// ---------------------------------------------------------------------------

const MTF_SCALPER_NODES: LabNode[] = [
  {
    id: "mtf_candles",
    type: "strategyNode",
    position: { x: 60, y: 250 },
    data: { blockType: "candles", params: {}, isStale: false } as LabNodeData,
  },
  {
    id: "mtf_sma5",
    type: "strategyNode",
    position: { x: 300, y: 100 },
    data: { blockType: "SMA", params: { length: 5 }, isStale: false } as LabNodeData,
  },
  {
    id: "mtf_sma10",
    type: "strategyNode",
    position: { x: 300, y: 250 },
    data: { blockType: "SMA", params: { length: 10 }, isStale: false } as LabNodeData,
  },
  {
    id: "mtf_cross",
    type: "strategyNode",
    position: { x: 520, y: 170 },
    data: { blockType: "cross", params: { mode: "crossover" }, isStale: false } as LabNodeData,
  },
  {
    id: "mtf_ema20_5m",
    type: "strategyNode",
    position: { x: 300, y: 420 },
    data: { blockType: "EMA", params: { length: 20, sourceTimeframe: "5m" }, isStale: false } as LabNodeData,
  },
  {
    id: "mtf_sl",
    type: "strategyNode",
    position: { x: 520, y: 480 },
    data: { blockType: "stop_loss", params: { type: "fixed", value: 1.0 }, isStale: false } as LabNodeData,
  },
  {
    id: "mtf_enter",
    type: "strategyNode",
    position: { x: 780, y: 300 },
    data: {
      blockType: "enter_adaptive",
      params: { source: "close", longOp: "gt", shortOp: "lt" },
      isStale: false,
    } as LabNodeData,
  },
];

const MTF_SCALPER_EDGES: LabEdge[] = [
  tplEdge("mtf_e1", "mtf_candles", "candles_out", "mtf_sma5", "candles", "Series<OHLCV>"),
  tplEdge("mtf_e2", "mtf_candles", "candles_out", "mtf_sma10", "candles", "Series<OHLCV>"),
  tplEdge("mtf_e3", "mtf_sma5", "sma", "mtf_cross", "a", "Series<number>"),
  tplEdge("mtf_e4", "mtf_sma10", "sma", "mtf_cross", "b", "Series<number>"),
  tplEdge("mtf_e5", "mtf_cross", "signal", "mtf_enter", "signal", "Series<boolean>"),
  tplEdge("mtf_e6", "mtf_candles", "candles_out", "mtf_ema20_5m", "candles", "Series<OHLCV>"),
  tplEdge("mtf_e7", "mtf_ema20_5m", "ema", "mtf_enter", "sideIndicator", "Series<number>"),
  tplEdge("mtf_e8", "mtf_candles", "candles_out", "mtf_sl", "candles", "Series<OHLCV>"),
  tplEdge("mtf_e9", "mtf_sl", "risk", "mtf_enter", "risk", "RiskParams"),
];

// ---------------------------------------------------------------------------
// Flagship #1 — SMC Liquidity Sweep (docs/strategies/02)
// Liquidity Sweep > 0 (bullish) → Enter Long
// SL 2%, TP 4%
// ---------------------------------------------------------------------------

const SMC_SWEEP_NODES: LabNode[] = [
  {
    id: "smc_candles",
    type: "strategyNode",
    position: { x: 60, y: 200 },
    data: { blockType: "candles", params: {}, isStale: false } as LabNodeData,
  },
  {
    id: "smc_sweep",
    type: "strategyNode",
    position: { x: 300, y: 100 },
    data: { blockType: "liquidity_sweep", params: { swingLen: 3, maxAge: 50 }, isStale: false } as LabNodeData,
  },
  {
    id: "smc_const0",
    type: "strategyNode",
    position: { x: 300, y: 280 },
    data: { blockType: "constant", params: { value: 0 }, isStale: false } as LabNodeData,
  },
  {
    id: "smc_cmp",
    type: "strategyNode",
    position: { x: 540, y: 180 },
    data: { blockType: "compare", params: { op: ">" }, isStale: false } as LabNodeData,
  },
  {
    id: "smc_sl",
    type: "strategyNode",
    position: { x: 540, y: 380 },
    data: { blockType: "stop_loss", params: { type: "fixed", value: 2.0 }, isStale: false } as LabNodeData,
  },
  {
    id: "smc_enter",
    type: "strategyNode",
    position: { x: 800, y: 280 },
    data: { blockType: "enter_long", params: {}, isStale: false } as LabNodeData,
  },
];

const SMC_SWEEP_EDGES: LabEdge[] = [
  tplEdge("smc_e1", "smc_candles", "candles_out", "smc_sweep", "candles", "Series<OHLCV>"),
  tplEdge("smc_e2", "smc_sweep", "sweep", "smc_cmp", "a", "Series<number>"),
  tplEdge("smc_e3", "smc_const0", "value", "smc_cmp", "b", "Series<number>"),
  tplEdge("smc_e4", "smc_cmp", "result", "smc_enter", "signal", "Series<boolean>"),
  tplEdge("smc_e5", "smc_candles", "candles_out", "smc_sl", "candles", "Series<OHLCV>"),
  tplEdge("smc_e6", "smc_sl", "risk", "smc_enter", "risk", "RiskParams"),
];

// ---------------------------------------------------------------------------
// Template registry
// ---------------------------------------------------------------------------

export const GRAPH_TEMPLATES: GraphTemplate[] = [
  {
    id: "ema-crossover",
    label: "EMA Crossover",
    description: "Candles → EMA(9) → EMA(21) → Cross → Enter Long + Stop Loss(1%)",
    nodes: EMA_CROSSOVER_NODES,
    edges: EMA_CROSSOVER_EDGES,
  },
  {
    id: "adaptive-regime-bot",
    label: "Adaptive Regime Bot",
    description: "ADX trend filter + EMA(50) direction → Adaptive entry. Trades trend when ADX > 25.",
    nodes: ADAPTIVE_REGIME_NODES,
    edges: ADAPTIVE_REGIME_EDGES,
  },
  {
    id: "dca-momentum-bot",
    label: "DCA Momentum Bot",
    description: "SMA(5)/SMA(20) crossover → Long + DCA ladder (3 safety orders, 1.5% TP from avg).",
    nodes: DCA_MOMENTUM_NODES,
    edges: DCA_MOMENTUM_EDGES,
  },
  {
    id: "mtf-confluence-scalper",
    label: "MTF Confluence Scalper",
    description: "SMA cross on 1m + EMA(20) on 5m context for direction. Multi-timeframe scalping.",
    nodes: MTF_SCALPER_NODES,
    edges: MTF_SCALPER_EDGES,
  },
  {
    id: "smc-liquidity-sweep",
    label: "SMC Liquidity Sweep",
    description: "Detects liquidity sweeps at swing highs/lows → Enter on bullish sweep. SL 2%, TP 4%.",
    nodes: SMC_SWEEP_NODES,
    edges: SMC_SWEEP_EDGES,
  },
];

export function getTemplate(id: string): GraphTemplate | undefined {
  return GRAPH_TEMPLATES.find((t) => t.id === id);
}
