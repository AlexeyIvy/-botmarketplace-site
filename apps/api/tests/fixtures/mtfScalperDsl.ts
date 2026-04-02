/**
 * MTF Confluence Scalper — Strategy DSL Fixtures (#136)
 *
 * Hand-authored DSL v2 for the MTF Confluence Scalper flagship strategy.
 * Uses SMA crossover on 1m for entry signal with EMA sideCondition
 * from 5m context timeframe for MTF confluence.
 *
 * Production variant uses VWAP + VolumeProfile + RSI(3) confluence,
 * but deterministic fixtures use SMA/EMA for reliable crossover timing.
 */

/**
 * MTF Confluence Scalper DSL — 1m primary, 5m context for side.
 */
export function makeMtfScalperDsl() {
  return {
    id: "mtf-confluence-scalper",
    name: "MTF Confluence Scalper",
    dslVersion: 2,
    enabled: true,
    market: {
      exchange: "bybit",
      env: "demo",
      category: "linear",
      symbol: "BTCUSDT",
    },
    timeframes: ["1m", "5m"],
    entry: {
      sideCondition: {
        indicator: { type: "EMA", length: 20, sourceTimeframe: "5m" },
        long: { op: "gt" },
        short: { op: "lt" },
      },
      signal: {
        type: "crossover",
        fast: { blockType: "SMA", length: 5 },
        slow: { blockType: "SMA", length: 10 },
      },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 1.0 },
      takeProfit: { type: "fixed_pct", value: 2.0 },
    },
    risk: {
      maxPositionSizeUsd: 500,
      riskPerTradePct: 1,
      cooldownSeconds: 0,
    },
    execution: {
      orderType: "Market",
      clientOrderIdPrefix: "mtf_scalp_",
    },
    guards: {
      maxOpenPositions: 1,
      maxOrdersPerMinute: 30,
      pauseOnError: true,
    },
  };
}
