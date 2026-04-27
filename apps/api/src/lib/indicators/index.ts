/**
 * Indicator engine — reusable calculation primitives.
 *
 * Each indicator is a pure function: (candles, params) → result array.
 * All results are same-length as input with null for warm-up bars.
 */

export type { Candle } from "./types.js";
export { calcSMA } from "./sma.js";
export { calcEMA } from "./ema.js";
export { calcATR, trueRange } from "./atr.js";
export { calcVWAP } from "./vwap.js";
export { calcADX } from "./adx.js";
export type { ADXResult } from "./adx.js";
export { calcSuperTrend } from "./supertrend.js";
export type { SuperTrendResult } from "./supertrend.js";
export { calcMACD } from "./macd.js";
export type { MACDResult } from "./macd.js";
