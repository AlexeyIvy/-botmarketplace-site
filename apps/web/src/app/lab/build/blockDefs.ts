// ---------------------------------------------------------------------------
// Phase 3B — Block definitions for Strategy Graph MVP
// Source: docs/23-lab-v2-ide-spec.md §6.3, §9.1
// ---------------------------------------------------------------------------

// Port data types per §9.1
export type PortDataType =
  | "Series<OHLCV>"
  | "Series<number>"
  | "Series<boolean>"
  | "Signal"
  | "RiskParams"
  | "OrderModel";

// Port colors per §9.1
export const PORT_TYPE_COLOR: Record<PortDataType, string> = {
  "Series<OHLCV>": "#5B9BD5",     // Steel blue
  "Series<number>": "#D4A44C",    // Amber
  "Series<boolean>": "#9580C8",   // Violet
  Signal: "#52A97C",              // Emerald
  RiskParams: "#D46060",          // Coral
  OrderModel: "#6A849E",          // Slate
};

// Type abbreviations for edge labels
export const PORT_TYPE_ABBR: Record<PortDataType, string> = {
  "Series<OHLCV>": "OHLCV",
  "Series<number>": "ℝ",
  "Series<boolean>": "𝔹",
  Signal: "SIG",
  RiskParams: "RISK",
  OrderModel: "ORD",
};

// Block categories per §6.3
export type BlockCategory = "input" | "indicator" | "logic" | "execution" | "risk";

// Category accent colors (left-border on node card per §6.3.1)
export const CATEGORY_COLOR: Record<BlockCategory, string> = {
  input: "#5B9BD5",      // Steel blue
  indicator: "#D4A44C",  // Amber
  logic: "#9580C8",      // Violet
  execution: "#52A97C",  // Emerald
  risk: "#D46060",       // Coral
};

// Category display labels
export const CATEGORY_LABEL: Record<BlockCategory, string> = {
  input: "Input",
  indicator: "Indicator",
  logic: "Logic",
  execution: "Execution",
  risk: "Risk",
};

export interface PortDef {
  id: string;
  label: string;
  dataType: PortDataType;
  required: boolean;
}

export interface ParamDef {
  id: string;
  label: string;
  type: "number" | "select" | "string";
  defaultValue: unknown;
  options?: string[];         // for select type
  min?: number;
  max?: number;
}

export interface BlockDef {
  type: string;             // unique block type key
  label: string;            // display name
  category: BlockCategory;
  inputs: PortDef[];
  outputs: PortDef[];
  params: ParamDef[];
  description: string;
}

// ---------------------------------------------------------------------------
// Phase 3 MVP block library
// Source: docs/23-lab-v2-ide-spec.md §15 (Phase 3B task)
// Blocks: candles, SMA, EMA, RSI, compare, cross, enter_long, enter_short,
//         stop_loss, take_profit
// ---------------------------------------------------------------------------

export const BLOCK_DEFS: BlockDef[] = [
  // ── Input ─────────────────────────────────────────────────────────────────
  {
    type: "candles",
    label: "Candles",
    category: "input",
    inputs: [],
    outputs: [
      { id: "candles_out", label: "candles out", dataType: "Series<OHLCV>", required: false },
    ],
    params: [],
    description: "Raw market candle stream bound to the active MarketDataset.",
  },

  // A2-6: Constant — emits a fixed numeric value
  {
    type: "constant",
    label: "Constant",
    category: "input",
    inputs: [],
    outputs: [
      { id: "value", label: "value", dataType: "Series<number>", required: false },
    ],
    params: [
      {
        id: "value",
        label: "Value",
        type: "number",
        defaultValue: 0,
        min: -1_000_000,
        max: 1_000_000,
      },
    ],
    description: "Emits a fixed numeric value as a constant series.",
  },

  // ── Indicators ────────────────────────────────────────────────────────────
  {
    type: "SMA",
    label: "SMA",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "sma", label: "sma", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "length", label: "Length", type: "number", defaultValue: 14, min: 1, max: 500 },
    ],
    description: "Simple Moving Average over the close price.",
  },
  {
    type: "EMA",
    label: "EMA",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "ema", label: "ema", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "length", label: "Length", type: "number", defaultValue: 14, min: 1, max: 500 },
    ],
    description: "Exponential Moving Average over the close price.",
  },
  {
    type: "RSI",
    label: "RSI",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "rsi", label: "rsi", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "length", label: "Length", type: "number", defaultValue: 14, min: 2, max: 500 },
    ],
    description: "Relative Strength Index (0–100 oscillator).",
  },

  // ── Logic ─────────────────────────────────────────────────────────────────
  {
    type: "compare",
    label: "Compare",
    category: "logic",
    inputs: [
      { id: "a", label: "a", dataType: "Series<number>", required: true },
      { id: "b", label: "b", dataType: "Series<number>", required: true },
    ],
    outputs: [
      { id: "result", label: "result", dataType: "Series<boolean>", required: false },
    ],
    params: [
      {
        id: "op",
        label: "Operator",
        type: "select",
        defaultValue: ">",
        options: [">", "<", "==", ">=", "<="],
      },
    ],
    description: "Element-wise comparison of two numeric series.",
  },
  {
    type: "cross",
    label: "Cross",
    category: "logic",
    inputs: [
      { id: "a", label: "a", dataType: "Series<number>", required: true },
      { id: "b", label: "b", dataType: "Series<number>", required: true },
    ],
    outputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: false },
    ],
    params: [
      {
        id: "mode",
        label: "Mode",
        type: "select",
        defaultValue: "crossover",
        options: ["crossover", "crossunder", "both"],
      },
    ],
    description: "Detects crossover / crossunder events between two series.",
  },

  // ── Execution ─────────────────────────────────────────────────────────────
  {
    type: "enter_long",
    label: "Enter Long",
    category: "execution",
    inputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: true },
      { id: "risk", label: "risk", dataType: "RiskParams", required: true },
    ],
    outputs: [],
    params: [],
    description: "Opens a long position when the signal fires, applying the provided risk params.",
  },
  {
    type: "enter_short",
    label: "Enter Short",
    category: "execution",
    inputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: true },
      { id: "risk", label: "risk", dataType: "RiskParams", required: true },
    ],
    outputs: [],
    params: [],
    description: "Opens a short position when the signal fires, applying the provided risk params.",
  },

  // ── Risk ──────────────────────────────────────────────────────────────────
  {
    type: "stop_loss",
    label: "Stop Loss",
    category: "risk",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "risk", label: "risk", dataType: "RiskParams", required: false },
    ],
    params: [
      {
        id: "type",
        label: "Type",
        type: "select",
        defaultValue: "fixed",
        options: ["fixed", "atr-multiple"],
      },
      { id: "value", label: "Value", type: "number", defaultValue: 1.0, min: 0.01, max: 100 },
    ],
    description: "Computes stop-loss risk parameters (fixed % or ATR-multiple).",
  },
  {
    type: "take_profit",
    label: "Take Profit",
    category: "risk",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "risk", label: "risk", dataType: "RiskParams", required: false },
    ],
    params: [
      {
        id: "type",
        label: "Type",
        type: "select",
        defaultValue: "fixed",
        options: ["fixed", "r-multiple"],
      },
      { id: "value", label: "Value", type: "number", defaultValue: 2.0, min: 0.01, max: 100 },
    ],
    description: "Computes take-profit risk parameters (fixed % or R-multiple).",
  },
];

// ---------------------------------------------------------------------------
// Node data shape stored in React Flow node.data
// ---------------------------------------------------------------------------

export interface LabNodeData extends Record<string, unknown> {
  blockType: string;
  params: Record<string, unknown>;
  isStale?: boolean;
}

// Lookup map for fast access
export const BLOCK_DEF_MAP: Record<string, BlockDef> = Object.fromEntries(
  BLOCK_DEFS.map((b) => [b.type, b])
);

// Type compatibility: which output types can connect to which input types.
// Per §9.1: strict — no implicit coercions.
export function isPortTypeCompatible(
  outputType: PortDataType,
  inputType: PortDataType
): boolean {
  return outputType === inputType;
}
