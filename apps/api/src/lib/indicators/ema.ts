/**
 * Exponential Moving Average (EMA).
 *
 * Seeded with the SMA of the first `length` closes; subsequent bars apply
 * the standard exponential smoothing factor k = 2 / (length + 1):
 *   EMA[i] = close[i] * k + EMA[i-1] * (1 - k)
 *
 * Returns array of same length as input; first `length - 1` values are null
 * (warm-up). Pure, deterministic — no I/O, no side effects.
 */

import type { Candle } from "./types.js";

export function calcEMA(candles: Candle[], length: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < length) return result;

  // Seed with SMA
  let sum = 0;
  for (let i = 0; i < length; i++) sum += candles[i].close;
  let ema = sum / length;
  result[length - 1] = ema;

  const k = 2 / (length + 1);
  for (let i = length; i < n; i++) {
    ema = candles[i].close * k + ema * (1 - k);
    result[i] = ema;
  }
  return result;
}
