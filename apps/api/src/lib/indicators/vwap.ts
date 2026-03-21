/**
 * Volume Weighted Average Price (VWAP).
 *
 * Intraday VWAP accumulates from the first candle in the dataset (or from each
 * session reset). Typical price = (high + low + close) / 3.
 *
 * Formula:
 *   cumTPV += typicalPrice * volume
 *   cumVol += volume
 *   VWAP = cumTPV / cumVol
 *
 * Anchoring: by default the accumulation starts at index 0 and runs continuously
 * (anchored VWAP). For intraday session resets, pass `anchorFn` that returns true
 * on bars where the accumulation should restart.
 *
 * Returns null for bars where cumulative volume is zero (no trading).
 */

import type { Candle } from "./types.js";

/**
 * Compute anchored VWAP over candle array.
 *
 * @param candles  OHLCV array
 * @param anchorFn Optional function that returns true on bars where VWAP resets.
 *                 Defaults to anchoring at index 0 only (session-continuous VWAP).
 * @returns Array of (number | null), same length as input
 */
export function calcVWAP(
  candles: Candle[],
  anchorFn?: (candle: Candle, index: number) => boolean,
): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);

  let cumTPV = 0;
  let cumVol = 0;

  for (let i = 0; i < n; i++) {
    const c = candles[i];

    // Reset accumulation at anchor points
    if (i === 0 || (anchorFn && anchorFn(c, i))) {
      cumTPV = 0;
      cumVol = 0;
    }

    const tp = (c.high + c.low + c.close) / 3;
    cumTPV += tp * c.volume;
    cumVol += c.volume;

    result[i] = cumVol > 0 ? cumTPV / cumVol : null;
  }

  return result;
}
