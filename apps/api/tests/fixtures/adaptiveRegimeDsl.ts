/**
 * Adaptive Regime Bot — hand-authored DSL v2 fixtures.
 *
 * These represent the target DSL output for the Adaptive Regime Bot strategy.
 * They exercise DSL v2 features (sideCondition, top-level exit) that the
 * runtime already supports but the compiler does not yet emit.
 *
 * Strategy logic (trend mode):
 *   Entry signal: ADX(14) > 25 (strong trend detected)
 *   Side:         EMA(50) determines direction (close > EMA → long, close < EMA → short)
 *   Exit:         Fixed SL 2%, TP 4%
 *
 * This is the trend-mode slice of the full Adaptive Regime Bot.
 * Range mode (BB + RSI when ADX < 20) is out of scope for this slice.
 */

/**
 * Trend-mode DSL: dynamic long/short via EMA(50) sideCondition + ADX(14) > 25 entry signal.
 */
export function makeAdaptiveRegimeTrendDsl() {
  return {
    id: "adaptive-regime-trend",
    name: "Adaptive Regime Bot — Trend Mode",
    dslVersion: 2,
    enabled: true,
    market: {
      exchange: "bybit",
      env: "demo",
      category: "linear",
      symbol: "BTCUSDT",
    },
    timeframes: ["5m"],
    entry: {
      sideCondition: {
        indicator: { type: "EMA", length: 50 },
        source: "close",
        long: { op: "gt" },
        short: { op: "lt" },
      },
      signal: {
        type: "compare",
        op: ">",
        left: { blockType: "adx", length: 14 },
        right: { blockType: "constant", length: 25 },
      },
      indicators: [
        { type: "ADX", length: 14 },
        { type: "EMA", length: 50 },
      ],
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 2.0 },
      takeProfit: { type: "fixed_pct", value: 4.0 },
    },
    risk: {
      riskPerTradePct: 2.0,
      maxPositionSizeUsd: 100,
      cooldownSeconds: 60,
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
  };
}

/**
 * Trend-mode DSL with fixed long side for simpler testing.
 * Entry: ADX(14) > 25, side: always long, SL 2%, TP 4%.
 */
export function makeAdaptiveRegimeLongOnlyDsl() {
  return {
    id: "adaptive-regime-long",
    name: "Adaptive Regime Bot — Long Only",
    dslVersion: 1,
    enabled: true,
    market: {
      exchange: "bybit",
      env: "demo",
      category: "linear",
      symbol: "BTCUSDT",
    },
    timeframes: ["5m"],
    entry: {
      side: "Buy",
      signal: {
        type: "compare",
        op: ">",
        left: { blockType: "adx", length: 14 },
        right: { blockType: "constant", length: 25 },
      },
      stopLoss: { type: "fixed_pct", value: 2.0 },
      takeProfit: { type: "fixed_pct", value: 4.0 },
      indicators: [{ type: "ADX", length: 14 }],
    },
    risk: {
      riskPerTradePct: 2.0,
      maxPositionSizeUsd: 100,
      cooldownSeconds: 60,
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
  };
}
