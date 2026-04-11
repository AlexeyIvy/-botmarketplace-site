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

  // ── B2 Indicators ────────────────────────────────────────────────────────
  {
    type: "macd",
    label: "MACD",
    category: "indicator",
    inputs: [
      { id: "price", label: "price", dataType: "Series<number>", required: true },
    ],
    outputs: [
      { id: "macd", label: "macd", dataType: "Series<number>", required: false },
      { id: "signal", label: "signal", dataType: "Series<number>", required: false },
      { id: "histogram", label: "histogram", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "fastPeriod", label: "Fast Period", type: "number", defaultValue: 12, min: 1, max: 200 },
      { id: "slowPeriod", label: "Slow Period", type: "number", defaultValue: 26, min: 1, max: 500 },
      { id: "signalPeriod", label: "Signal Period", type: "number", defaultValue: 9, min: 1, max: 100 },
    ],
    description: "Moving Average Convergence Divergence.",
  },
  {
    type: "bollinger",
    label: "Bollinger Bands",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "upper", label: "upper", dataType: "Series<number>", required: false },
      { id: "middle", label: "middle", dataType: "Series<number>", required: false },
      { id: "lower", label: "lower", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "period", label: "Period", type: "number", defaultValue: 20, min: 2, max: 500 },
      { id: "stdDevMult", label: "Std Dev ×", type: "number", defaultValue: 2.0, min: 0.1, max: 10 },
    ],
    description: "Bollinger Bands — upper, middle (SMA), and lower bands.",
  },
  {
    type: "atr",
    label: "ATR",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "atr", label: "atr", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "period", label: "Period", type: "number", defaultValue: 14, min: 1, max: 500 },
    ],
    description: "Average True Range — volatility indicator.",
  },
  {
    type: "volume",
    label: "Volume",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "volume", label: "volume", dataType: "Series<number>", required: false },
    ],
    params: [],
    description: "Extracts the volume series from OHLCV candles.",
  },

  // ── Stage 2 Indicators (#125) ──────────────────────────────────────────────
  {
    type: "vwap",
    label: "VWAP",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "vwap", label: "vwap", dataType: "Series<number>", required: false },
    ],
    params: [],
    description: "Volume-Weighted Average Price — anchored from session start.",
  },
  {
    type: "adx",
    label: "ADX",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "adx", label: "adx", dataType: "Series<number>", required: false },
      { id: "plusDI", label: "+DI", dataType: "Series<number>", required: false },
      { id: "minusDI", label: "−DI", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "period", label: "Period", type: "number", defaultValue: 14, min: 2, max: 500 },
    ],
    description: "Average Directional Index — trend strength (0–100).",
  },
  {
    type: "supertrend",
    label: "SuperTrend",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "supertrend", label: "supertrend", dataType: "Series<number>", required: false },
      { id: "direction", label: "direction", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "atrPeriod", label: "ATR Period", type: "number", defaultValue: 10, min: 1, max: 500 },
      { id: "multiplier", label: "Multiplier", type: "number", defaultValue: 3, min: 0.1, max: 20 },
    ],
    description: "SuperTrend — ATR-based trend-following indicator with direction.",
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
  {
    type: "and_gate",
    label: "AND",
    category: "logic",
    inputs: [
      { id: "a", label: "a", dataType: "Series<boolean>", required: true },
      { id: "b", label: "b", dataType: "Series<boolean>", required: true },
    ],
    outputs: [
      { id: "out", label: "out", dataType: "Series<boolean>", required: false },
    ],
    params: [],
    description: "True only when all inputs are true on the same bar.",
  },
  {
    type: "or_gate",
    label: "OR",
    category: "logic",
    inputs: [
      { id: "a", label: "a", dataType: "Series<boolean>", required: true },
      { id: "b", label: "b", dataType: "Series<boolean>", required: true },
    ],
    outputs: [
      { id: "out", label: "out", dataType: "Series<boolean>", required: false },
    ],
    params: [],
    description: "True when any input is true on the same bar.",
  },
  {
    type: "confirm_n_bars",
    label: "Confirm N Bars",
    category: "logic",
    inputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: true },
    ],
    outputs: [
      { id: "confirmed", label: "confirmed", dataType: "Series<boolean>", required: false },
    ],
    params: [
      { id: "bars", label: "Confirm Bars", type: "number", defaultValue: 3, min: 1, max: 50 },
    ],
    description: "Requires signal to be true for N consecutive bars before firing.",
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
  {
    type: "enter_adaptive",
    label: "Enter Adaptive",
    category: "execution",
    inputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: true },
      { id: "risk", label: "risk", dataType: "RiskParams", required: true },
      { id: "sideIndicator", label: "side indicator", dataType: "Series<number>", required: true },
    ],
    outputs: [],
    params: [
      { id: "source", label: "Source", type: "select", defaultValue: "close", options: ["open", "high", "low", "close"] },
      { id: "longOp", label: "Long Op", type: "select", defaultValue: "gt", options: ["gt", "gte", "lt", "lte"] },
      { id: "shortOp", label: "Short Op", type: "select", defaultValue: "lt", options: ["gt", "gte", "lt", "lte"] },
    ],
    description: "Adaptive entry with dynamic long/short side determined by a side-condition indicator (DSL v2).",
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

  // ── DCA ───────────────────────────────────────────────────────────────────
  {
    type: "dca_config",
    label: "DCA Config",
    category: "risk",
    inputs: [],
    outputs: [
      { id: "risk", label: "dca", dataType: "RiskParams", required: false },
    ],
    params: [
      { id: "baseOrderSizeUsd", label: "Base Order (USD)", type: "number", defaultValue: 100, min: 1, max: 100000 },
      { id: "maxSafetyOrders", label: "Max Safety Orders", type: "number", defaultValue: 3, min: 1, max: 50 },
      { id: "priceStepPct", label: "Price Step %", type: "number", defaultValue: 1.0, min: 0.1, max: 50 },
      { id: "stepScale", label: "Step Scale", type: "number", defaultValue: 1.0, min: 1.0, max: 10 },
      { id: "volumeScale", label: "Volume Scale", type: "number", defaultValue: 1.5, min: 1.0, max: 10 },
      { id: "takeProfitPct", label: "TP from Avg %", type: "number", defaultValue: 1.5, min: 0.1, max: 100 },
    ],
    description: "Configures DCA ladder: base order, safety orders with step/volume scaling, and TP recalculation from averaged entry.",
  },

  // ── Trailing Stop (#Phase6) ────────────────────────────────────────────────
  {
    type: "trailing_stop",
    label: "Trailing Stop",
    category: "risk",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "risk", label: "risk", dataType: "RiskParams", required: false },
    ],
    params: [
      { id: "activationPct", label: "Activation %", type: "number", defaultValue: 1.0, min: 0.01, max: 50 },
      { id: "callbackPct", label: "Callback %", type: "number", defaultValue: 0.5, min: 0.01, max: 50 },
    ],
    description: "Trailing stop loss — activates after price moves favourably by activation %, then trails at callback % from high-water mark.",
  },

  // ── Close Position (#Phase6) ──────────────────────────────────────────────
  {
    type: "close_position",
    label: "Close Position",
    category: "execution",
    inputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: true },
    ],
    outputs: [],
    params: [
      {
        id: "reason",
        label: "Reason",
        type: "select",
        defaultValue: "signal",
        options: ["signal", "time_exit", "manual"],
      },
    ],
    description: "Explicitly closes any open position when the signal fires. Use for custom exit conditions beyond SL/TP.",
  },

  // ── MTF Confluence Indicators (#135) ──────────────────────────────────────
  {
    type: "volume_profile",
    label: "Volume Profile",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "poc", label: "POC", dataType: "Series<number>", required: false },
      { id: "vah", label: "VAH", dataType: "Series<number>", required: false },
      { id: "val", label: "VAL", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "period", label: "Period", type: "number", defaultValue: 20, min: 5, max: 200 },
      { id: "bins", label: "Bins", type: "number", defaultValue: 24, min: 6, max: 100 },
    ],
    description: "Volume distribution profile: POC (highest volume price), VAH/VAL (value area bounds).",
  },
  {
    type: "proximity_filter",
    label: "Proximity Filter",
    category: "logic",
    inputs: [
      { id: "price", label: "price", dataType: "Series<number>", required: true },
      { id: "level", label: "level", dataType: "Series<number>", required: true },
    ],
    outputs: [
      { id: "near", label: "near", dataType: "Series<boolean>", required: false },
    ],
    params: [
      { id: "threshold", label: "Threshold", type: "number", defaultValue: 1.0, min: 0.01, max: 50 },
      {
        id: "mode",
        label: "Mode",
        type: "select",
        defaultValue: "percentage",
        options: ["percentage", "absolute"],
      },
    ],
    description: "Gates signals by proximity to a reference level (e.g., near POC/VAH/VAL).",
  },

  // ── Private Data Blocks (Phase 6, 23b3) ────────────────────────────────────
  {
    type: "orders_history",
    label: "Orders History",
    category: "input",
    inputs: [],
    outputs: [
      { id: "buyCount", label: "buy count", dataType: "Series<number>", required: false },
      { id: "sellCount", label: "sell count", dataType: "Series<number>", required: false },
      { id: "totalVolume", label: "total vol", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "lookbackBars", label: "Lookback (bars)", type: "number", defaultValue: 50, min: 1, max: 500 },
    ],
    description: "Historical order data from connected exchange. Requires an active ExchangeConnection.",
  },
  {
    type: "executions_history",
    label: "Executions History",
    category: "input",
    inputs: [],
    outputs: [
      { id: "execCount", label: "exec count", dataType: "Series<number>", required: false },
      { id: "avgFillPrice", label: "avg fill", dataType: "Series<number>", required: false },
      { id: "totalQty", label: "total qty", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "lookbackBars", label: "Lookback (bars)", type: "number", defaultValue: 50, min: 1, max: 500 },
    ],
    description: "Historical execution/fill data from connected exchange. Requires an active ExchangeConnection.",
  },

  // ── SMC Pattern Primitives (#137) ──────────────────────────────────────────
  {
    type: "liquidity_sweep",
    label: "Liquidity Sweep",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "sweep", label: "sweep", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "swingLen", label: "Swing Length", type: "number", defaultValue: 3, min: 1, max: 20 },
      { id: "maxAge", label: "Max Age (bars)", type: "number", defaultValue: 50, min: 5, max: 200 },
    ],
    description: "Detects liquidity sweeps at swing highs/lows. Output: +1 bullish sweep, -1 bearish sweep, 0 no sweep.",
  },
  {
    type: "fair_value_gap",
    label: "Fair Value Gap",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "fvg", label: "fvg", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "minGapRatio", label: "Min Gap Ratio", type: "number", defaultValue: 0, min: 0, max: 5 },
    ],
    description: "Detects fair value gaps (3-candle imbalances). Output: +1 bullish FVG, -1 bearish FVG, 0 none.",
  },
  {
    type: "order_block",
    label: "Order Block",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "ob", label: "ob", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "atrPeriod", label: "ATR Period", type: "number", defaultValue: 14, min: 2, max: 50 },
      { id: "minImpulseMultiple", label: "Min Impulse (×ATR)", type: "number", defaultValue: 1.5, min: 0.5, max: 10 },
      { id: "maxLookback", label: "Max Lookback", type: "number", defaultValue: 5, min: 1, max: 20 },
    ],
    description: "Detects order blocks (last opposing candle before impulse). Output: +1 bullish OB, -1 bearish OB, 0 none.",
  },
  {
    type: "market_structure_shift",
    label: "Market Structure",
    category: "indicator",
    inputs: [
      { id: "candles", label: "candles", dataType: "Series<OHLCV>", required: true },
    ],
    outputs: [
      { id: "mss", label: "mss", dataType: "Series<number>", required: false },
    ],
    params: [
      { id: "swingLen", label: "Swing Length", type: "number", defaultValue: 3, min: 1, max: 20 },
    ],
    description: "Detects market structure shifts (BOS/CHoCH). Output: +1 bullish BOS, -1 bearish BOS, +2 bullish CHoCH, -2 bearish CHoCH, 0 none.",
  },

  // ── Annotate Event (Phase 6, 23b4) ─────────────────────────────────────────
  {
    type: "annotate_event",
    label: "Annotate Event",
    category: "logic",
    inputs: [
      { id: "signal", label: "signal", dataType: "Series<boolean>", required: true },
      { id: "price", label: "price", dataType: "Series<number>", required: false },
    ],
    outputs: [],
    params: [
      { id: "label", label: "Label", type: "string", defaultValue: "Event" },
      {
        id: "color",
        label: "Color",
        type: "select",
        defaultValue: "blue",
        options: ["blue", "green", "red", "yellow", "purple", "white"],
      },
      {
        id: "shape",
        label: "Shape",
        type: "select",
        defaultValue: "circle",
        options: ["circle", "diamond", "triangle", "square"],
      },
    ],
    description: "Marks events on the backtest equity curve when the signal fires. Useful for annotating key moments (entries, regime changes, etc.).",
  },
];

// ---------------------------------------------------------------------------
// MTF (#27): inject sourceTimeframe selector into all indicator blocks
// "auto" means use the strategy's primary timeframe (no MTF).
// ---------------------------------------------------------------------------

const TIMEFRAME_PARAM: ParamDef = {
  id: "sourceTimeframe",
  label: "Timeframe",
  type: "select",
  defaultValue: "auto",
  options: ["auto", "1m", "5m", "15m", "1h", "4h", "1d"],
};

for (const def of BLOCK_DEFS) {
  if (def.category === "indicator") {
    def.params.push(TIMEFRAME_PARAM);
  }
}

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
