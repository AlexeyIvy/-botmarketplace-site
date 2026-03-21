/**
 * SuperTrend indicator.
 *
 * Combines ATR-based bands with trend direction tracking.
 *
 * Formula:
 *   basicUpper = hl2 + multiplier * ATR
 *   basicLower = hl2 - multiplier * ATR
 *
 *   finalUpper[i] = basicUpper[i] < finalUpper[i-1] || close[i-1] > finalUpper[i-1]
 *                   ? basicUpper[i] : finalUpper[i-1]
 *   finalLower[i] = basicLower[i] > finalLower[i-1] || close[i-1] < finalLower[i-1]
 *                   ? basicLower[i] : finalLower[i-1]
 *
 *   direction[i] = close[i] > finalUpper[i-1] ? 1 (up/bullish)
 *                : close[i] < finalLower[i-1] ? -1 (down/bearish)
 *                : direction[i-1]
 *
 *   supertrend[i] = direction[i] === 1 ? finalLower[i] : finalUpper[i]
 *
 * Implementation matches TradingView's SuperTrend built-in.
 *
 * Warm-up: null for first `atrPeriod - 1` bars (ATR warm-up).
 */

import type { Candle } from "./types.js";
import { calcATR } from "./atr.js";

export interface SuperTrendResult {
  /** SuperTrend line value */
  supertrend: (number | null)[];
  /** Trend direction: 1 = bullish (price above), -1 = bearish (price below), null = warm-up */
  direction: (1 | -1 | null)[];
}

/**
 * Compute SuperTrend.
 * @param candles    OHLCV array
 * @param atrPeriod  ATR period (default 10)
 * @param multiplier ATR multiplier (default 3)
 */
export function calcSuperTrend(
  candles: Candle[],
  atrPeriod = 10,
  multiplier = 3,
): SuperTrendResult {
  const n = candles.length;
  const supertrend: (number | null)[] = new Array(n).fill(null);
  const direction: (1 | -1 | null)[] = new Array(n).fill(null);

  const atr = calcATR(candles, atrPeriod);

  // Track final upper/lower bands
  const finalUpper = new Array<number>(n).fill(0);
  const finalLower = new Array<number>(n).fill(0);

  for (let i = 0; i < n; i++) {
    const atrVal = atr[i];
    if (atrVal === null) continue;

    const hl2 = (candles[i].high + candles[i].low) / 2;
    const basicUpper = hl2 + multiplier * atrVal;
    const basicLower = hl2 - multiplier * atrVal;

    if (i === atrPeriod - 1) {
      // First valid ATR bar — initialize bands and direction
      finalUpper[i] = basicUpper;
      finalLower[i] = basicLower;
      // Initial direction based on close vs bands
      direction[i] = candles[i].close <= basicUpper ? 1 : -1;
    } else {
      // Final Upper Band: tighten (lower) only if previous close was below it
      finalUpper[i] =
        basicUpper < finalUpper[i - 1] || candles[i - 1].close > finalUpper[i - 1]
          ? basicUpper
          : finalUpper[i - 1];

      // Final Lower Band: tighten (raise) only if previous close was above it
      finalLower[i] =
        basicLower > finalLower[i - 1] || candles[i - 1].close < finalLower[i - 1]
          ? basicLower
          : finalLower[i - 1];

      // Direction
      const prevDir = direction[i - 1]!;
      if (prevDir === 1 && candles[i].close < finalLower[i]) {
        direction[i] = -1;
      } else if (prevDir === -1 && candles[i].close > finalUpper[i]) {
        direction[i] = 1;
      } else {
        direction[i] = prevDir;
      }
    }

    // SuperTrend value = lower band when bullish, upper band when bearish
    supertrend[i] = direction[i] === 1 ? finalLower[i] : finalUpper[i];
  }

  return { supertrend, direction };
}
