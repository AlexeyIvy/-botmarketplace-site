/**
 * Bollinger Bands.
 *
 * For each bar i ≥ period - 1:
 *   middle[i] = SMA(close, period) over the most recent `period` closes
 *   stdDev[i] = sqrt( Σ (close[j] - middle[i])² / period )   (population stdDev)
 *   upper[i]  = middle[i] + stdDevMult * stdDev[i]
 *   lower[i]  = middle[i] - stdDevMult * stdDev[i]
 *
 * Returns three parallel arrays of the same length as input; the first
 * `period - 1` values in each array are null (warm-up). When all closes in
 * the window are equal, stdDev is 0 and upper === middle === lower.
 *
 * Pure, deterministic — no I/O, no side effects.
 */

import type { Candle } from "./types.js";

export interface BollingerBandsResult {
  upper: (number | null)[];
  middle: (number | null)[];
  lower: (number | null)[];
}

export function calcBollingerBands(
  candles: Candle[],
  period: number,
  stdDevMult: number,
): BollingerBandsResult {
  const n = candles.length;
  const upper: (number | null)[] = new Array(n).fill(null);
  const middle: (number | null)[] = new Array(n).fill(null);
  const lower: (number | null)[] = new Array(n).fill(null);
  if (n < period) return { upper, middle, lower };

  for (let i = period - 1; i < n; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += candles[j].close;
    const mean = sum / period;

    let sqSum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const diff = candles[j].close - mean;
      sqSum += diff * diff;
    }
    const stdDev = Math.sqrt(sqSum / period);

    middle[i] = mean;
    upper[i] = mean + stdDevMult * stdDev;
    lower[i] = mean - stdDevMult * stdDev;
  }

  return { upper, middle, lower };
}
