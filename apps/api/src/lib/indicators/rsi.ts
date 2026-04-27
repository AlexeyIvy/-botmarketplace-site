/**
 * Relative Strength Index (RSI) — Wilder's smoothed RSI.
 *
 * Formula:
 *   change[i]   = close[i] - close[i-1]
 *   gain[i]     = max(change[i], 0)
 *   loss[i]     = max(-change[i], 0)
 *   avgGain[length] = SMA of gains over the first `length` changes (seed)
 *   avgLoss[length] = SMA of losses over the first `length` changes (seed)
 *   avgGain[i]  = (avgGain[i-1] * (length - 1) + gain[i]) / length   (Wilder)
 *   avgLoss[i]  = (avgLoss[i-1] * (length - 1) + loss[i]) / length   (Wilder)
 *   RSI[i]      = 100 - 100 / (1 + avgGain[i] / avgLoss[i])
 *
 * Special case: when avgLoss === 0, RSI is defined as 100 (no downward
 * pressure observed in the smoothed window).
 *
 * Returns array of same length as input; first `length` values are null
 * (warm-up — RSI requires `length` price changes, i.e. `length + 1` candles).
 * Pure, deterministic — no I/O, no side effects.
 */

import type { Candle } from "./types.js";

export function calcRSI(candles: Candle[], length: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < length + 1) return result;

  let gainSum = 0;
  let lossSum = 0;
  for (let i = 1; i <= length; i++) {
    const change = candles[i].close - candles[i - 1].close;
    if (change > 0) gainSum += change;
    else lossSum += Math.abs(change);
  }

  let avgGain = gainSum / length;
  let avgLoss = lossSum / length;
  result[length] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = length + 1; i < n; i++) {
    const change = candles[i].close - candles[i - 1].close;
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;
    avgGain = (avgGain * (length - 1) + gain) / length;
    avgLoss = (avgLoss * (length - 1) + loss) / length;
    result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return result;
}
