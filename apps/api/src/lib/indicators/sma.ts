/**
 * Simple Moving Average (SMA).
 *
 * SMA[i] = average of the most recent `length` closes ending at bar i.
 *
 * Returns array of same length as input; first `length - 1` values are null
 * (warm-up). Pure, deterministic — no I/O, no side effects.
 */

import type { Candle } from "./types.js";

export function calcSMA(candles: Candle[], length: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < length) return result;

  let sum = 0;
  for (let i = 0; i < length; i++) sum += candles[i].close;
  result[length - 1] = sum / length;

  for (let i = length; i < n; i++) {
    sum += candles[i].close - candles[i - length].close;
    result[i] = sum / length;
  }
  return result;
}
