/**
 * Indicator engine — reusable calculation primitives.
 *
 * Each indicator is a pure function: (candles, params) → result array.
 * All results are same-length as input with null for warm-up bars.
 *
 * Public API:
 *   - Moving averages:  calcSMA, calcEMA
 *   - Momentum:         calcRSI, calcMACD (+ MACDResult)
 *   - Volatility:       calcATR (+ trueRange), calcBollingerBands (+ BollingerBandsResult)
 *   - Trend:            calcADX (+ ADXResult), calcSuperTrend (+ SuperTrendResult)
 *   - Volume-weighted:  calcVWAP
 *   - Shared types:     Candle
 *
 * SMC primitives (fvgSeries, sweepSeries, orderBlockSeries, mssSeries) remain
 * in `runtime/patternEngine.ts` — extraction deferred to the next refactoring
 * wave (no public consumer exists outside dslEvaluator / runtime layer).
 */

export type { Candle } from "./types.js";
export { calcSMA } from "./sma.js";
export { calcEMA } from "./ema.js";
export { calcRSI } from "./rsi.js";
export { calcBollingerBands } from "./bollingerBands.js";
export type { BollingerBandsResult } from "./bollingerBands.js";
export { calcATR, trueRange } from "./atr.js";
export { calcVWAP } from "./vwap.js";
export { calcADX } from "./adx.js";
export type { ADXResult } from "./adx.js";
export { calcSuperTrend } from "./supertrend.js";
export type { SuperTrendResult } from "./supertrend.js";
export { calcMACD } from "./macd.js";
export type { MACDResult } from "./macd.js";
