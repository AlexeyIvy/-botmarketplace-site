/**
 * Average True Range (ATR) — Wilder's smoothed ATR.
 *
 * Formula:
 *   TR = max(high - low, |high - prevClose|, |low - prevClose|)
 *   ATR[period-1] = SMA of first `period` TR values (seed)
 *   ATR[i] = ATR[i-1] * (period - 1) / period + TR[i] / period   (Wilder smoothing)
 *
 * Returns array of same length as input; first `period` - 1 values are null (warm-up).
 * For the very first candle (i = 0) TR is defined as high - low (no previous close).
 */

import type { Candle } from "./types.js";

/**
 * Compute True Range for each candle.
 * Result length === candles.length. Index 0 uses high - low only.
 */
export function trueRange(candles: Candle[]): number[] {
  const n = candles.length;
  const tr = new Array<number>(n);
  for (let i = 0; i < n; i++) {
    const { high, low } = candles[i];
    if (i === 0) {
      tr[i] = high - low;
    } else {
      const prevClose = candles[i - 1].close;
      tr[i] = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
    }
  }
  return tr;
}

/**
 * Wilder-smoothed ATR.
 * @param candles OHLCV array
 * @param period  ATR period (default 14)
 * @returns Array of (number | null), same length as input
 */
export function calcATR(candles: Candle[], period = 14): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < period) return result;

  const tr = trueRange(candles);

  // Seed: SMA of first `period` TR values
  let sum = 0;
  for (let i = 0; i < period; i++) sum += tr[i];
  let atr = sum / period;
  result[period - 1] = atr;

  // Wilder smoothing
  for (let i = period; i < n; i++) {
    atr = (atr * (period - 1) + tr[i]) / period;
    result[i] = atr;
  }

  return result;
}
