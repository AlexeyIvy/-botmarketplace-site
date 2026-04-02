/**
 * DCA Momentum Bot — Strategy DSL Fixtures (#133)
 *
 * Hand-authored DSL v2 for the DCA Momentum Bot flagship strategy.
 * Entry: SMA(5) crossover SMA(20) → long entry (deterministic signal
 *        for test fixtures; production variant uses RSI(14) < 40 + EMA(21) filter)
 * DCA: 3 safety orders, 1% step, 1.5x volume scale, 1.5% TP from avg
 * Exit: 10% SL from avg entry, 1.5% TP from avg entry (DCA-managed)
 */

/**
 * Standard DCA Momentum Bot DSL (conservative variant).
 *
 * Designed for deterministic candle fixtures:
 *   - SMA(5)/SMA(20) crossover fires on transition from flat to up
 *   - Price dips trigger safety orders
 *   - Recovery triggers TP at avg entry + 1.5%
 */
export function makeDcaMomentumBotDsl() {
  return {
    id: "dca-momentum-bot",
    name: "DCA Momentum Bot",
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
        type: "crossover",
        fast: { blockType: "SMA", length: 5 },
        slow: { blockType: "SMA", length: 20 },
      },
      indicators: [
        { type: "RSI", length: 14 },
        { type: "EMA", length: 21 },
      ],
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 10 },
      takeProfit: { type: "fixed_pct", value: 5 },
    },
    risk: {
      maxPositionSizeUsd: 1000,
      riskPerTradePct: 2,
      cooldownSeconds: 0,
    },
    execution: {
      orderType: "Market",
      clientOrderIdPrefix: "dca_mom_",
    },
    guards: {
      maxOpenPositions: 1,
      maxOrdersPerMinute: 10,
      pauseOnError: true,
    },
    dca: {
      baseOrderSizeUsd: 100,
      maxSafetyOrders: 3,
      priceStepPct: 1.0,
      stepScale: 1.0,
      volumeScale: 1.5,
      takeProfitPct: 1.5,
    },
  };
}

/**
 * Aggressive DCA variant — more SOs, tighter step.
 */
export function makeDcaMomentumBotAggressiveDsl() {
  return {
    ...makeDcaMomentumBotDsl(),
    id: "dca-momentum-aggressive",
    name: "DCA Momentum Bot (Aggressive)",
    risk: {
      maxPositionSizeUsd: 3000,
      riskPerTradePct: 2,
      cooldownSeconds: 0,
    },
    dca: {
      baseOrderSizeUsd: 100,
      maxSafetyOrders: 5,
      priceStepPct: 0.8,
      stepScale: 1.05,
      volumeScale: 1.5,
      takeProfitPct: 2.0,
    },
  };
}
