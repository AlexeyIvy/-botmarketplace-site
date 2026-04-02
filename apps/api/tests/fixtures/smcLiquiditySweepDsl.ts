/**
 * SMC Liquidity Sweep Flagship — DSL fixture.
 *
 * Strategy: Enter long when a bullish liquidity sweep is detected.
 * - Entry signal: liquidity_sweep > 0 (bullish sweep fires the signal)
 * - Side: fixed Buy (long only — the signal already filters for bullish sweeps)
 * - Exit: 2% fixed SL, 4% fixed TP
 *
 * Note: sideCondition (DSL v2) compares price vs indicator value, which is
 * designed for continuous indicators (e.g., close > SMA). For discrete SMC
 * signals (+1/-1), use fixed side + directional compare signal instead.
 * Future enhancement: "direct" sideCondition mode for discrete signals.
 *
 * DSL v2 for exit section support.
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
      side: "Buy",
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
