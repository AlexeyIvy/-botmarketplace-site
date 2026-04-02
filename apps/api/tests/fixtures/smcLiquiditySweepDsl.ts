/**
 * SMC Liquidity Sweep Flagship — DSL fixture.
 *
 * Strategy: Enter when a liquidity sweep coincides with a fair value gap.
 * - Entry signal: liquidity_sweep > 0 (bullish sweep detected)
 * - Side condition: fair_value_gap indicator (positive = bullish bias)
 * - Exit: 2% fixed SL, 4% fixed TP
 *
 * This is a DSL v2 strategy using adaptive side from the FVG indicator.
 */
export function makeSmcLiquiditySweepDsl(): Record<string, unknown> {
  return {
    id: "smc-liquidity-sweep-001",
    name: "SMC Liquidity Sweep",
    dslVersion: 2,
    enabled: true,
    market: {
      exchange: "bybit",
      env: "demo",
      category: "linear",
      symbol: "BTCUSDT",
    },
    timeframes: ["M15"],
    entry: {
      sideCondition: {
        indicator: { type: "liquidity_sweep", length: 2, period: 50 },
        source: "close",
        long: { op: "gt" },
        short: { op: "lt" },
      },
      signal: {
        type: "compare",
        op: ">",
        left: { blockType: "liquidity_sweep", length: 2, period: 50 },
        right: { blockType: "constant", length: 0 },
      },
      indicators: [
        { type: "liquidity_sweep", length: 2, period: 50 },
      ],
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 2.0 },
      takeProfit: { type: "fixed_pct", value: 4.0 },
    },
    risk: {
      maxPositionSizeUsd: 1000,
      riskPerTradePct: 2.0,
      cooldownSeconds: 0,
    },
    execution: {
      orderType: "Market",
      clientOrderIdPrefix: "smc_sweep_",
      maxSlippageBps: 50,
    },
    guards: {
      maxOpenPositions: 1,
      maxOrdersPerMinute: 10,
      pauseOnError: true,
    },
  };
}
