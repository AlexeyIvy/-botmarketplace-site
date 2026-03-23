/**
 * Adaptive Regime Bot — hand-authored DSL fixtures.
 *
 * These represent the target DSL output for the Adaptive Regime Bot strategy.
 * They exercise DSL v2 features (sideCondition, top-level exit) that the
 * runtime already supports but the compiler does not yet emit.
 *
 * Strategy logic:
 *   Trend mode (ADX > 25):
 *     Entry signal: ADX(14) > 25 (strong trend detected)
 *     Side:         EMA(50) determines direction (close > EMA → long, close < EMA → short)
 *     Exit:         Fixed SL 2%, TP 4%
 *
 *   Range mode (ADX < 20):
 *     Entry signal: RSI(14) < 30 (oversold → long) or RSI(14) > 70 (overbought → short)
 *     Confirmation: price near BB lower/upper band
 *     Exit:         Fixed SL 1.5%, TP 3%
 *
 *   Neutral zone (20 <= ADX <= 25):
 *     No new entries.
 */

import type { AdaptiveStrategyConfig } from "../../src/lib/adaptiveStrategy.js";

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

/**
 * Range-mode entry config: RSI(14) < 40 mean-reversion long signal.
 *
 * Strategy: in low-ADX (range-bound) markets, buy when RSI shows weakness.
 * Uses RSI < 40 rather than the classic RSI < 30 because in a true range
 * market (ADX < 20), sharp drops that push RSI below 30 also temporarily
 * raise ADX above the range threshold. RSI < 40 fires during milder
 * pullbacks where ADX stays low — a more realistic mean-reversion signal.
 *
 * Side is fixed to "Buy" (long) — mean-reversion long on weakness.
 *
 * BB confirmation is implicit: in a range market with low ADX, price
 * oscillates near Bollinger Bands. A future slice can add explicit
 * BB band proximity checks.
 */
export function makeRangeModeEntry() {
  return {
    side: "Buy" as const,
    signal: {
      type: "compare" as const,
      op: "<" as const,
      left: { blockType: "rsi", length: 14 },
      right: { blockType: "constant", length: 40 },
    },
    indicators: [
      { type: "RSI", length: 14 },
      { type: "bollinger", length: 20, stdDevMult: 2 },
    ],
  };
}

/**
 * Range-mode entry config: RSI(14) > 60 mean-reversion short signal.
 *
 * Mirror of long entry: sell when RSI shows strength in range market.
 */
export function makeRangeModeShortEntry() {
  return {
    side: "Sell" as const,
    signal: {
      type: "compare" as const,
      op: ">" as const,
      left: { blockType: "rsi", length: 14 },
      right: { blockType: "constant", length: 60 },
    },
    indicators: [
      { type: "RSI", length: 14 },
      { type: "bollinger", length: 20, stdDevMult: 2 },
    ],
  };
}

/**
 * Full adaptive strategy config: trend + range entries with regime thresholds.
 *
 * Regime detection:
 *   ADX(14) > 25 → trend mode (EMA crossover direction + ADX strength entry)
 *   ADX(14) < 20 → range mode (RSI mean-reversion entry)
 *   20 <= ADX <= 25 → neutral (no entries)
 *
 * Trend entry: same as makeAdaptiveRegimeTrendDsl().entry
 * Range entry: RSI < 30 → long (mean-reversion)
 * Shared exit: SL 2%, TP 4%
 */
export function makeAdaptiveStrategyConfig(): AdaptiveStrategyConfig {
  return {
    regime: {
      adxPeriod: 14,
      trendThreshold: 25,
      rangeThreshold: 20,
    },
    trendEntry: {
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
    rangeEntry: {
      side: "Buy",
      signal: {
        type: "compare",
        op: "<",
        left: { blockType: "rsi", length: 14 },
        right: { blockType: "constant", length: 40 },
      },
      indicators: [
        { type: "RSI", length: 14 },
        { type: "bollinger", length: 20, stdDevMult: 2 },
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
  };
}
