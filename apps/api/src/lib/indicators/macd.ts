/**
 * MACD (Moving Average Convergence Divergence) indicator.
 *
 * Pure function: (candles, fast, slow, signal) → MACDResult
 * All result arrays are same-length as input with null for warm-up bars.
 */

import type { Candle } from "./types.js";

export interface MACDResult {
  macd: (number | null)[];
  signal: (number | null)[];
  histogram: (number | null)[];
}

/**
 * Calculate MACD from candle close prices.
 * @param candles - OHLCV candle data
 * @param fastPeriod - Fast EMA period (default 12)
 * @param slowPeriod - Slow EMA period (default 26)
 * @param signalPeriod - Signal line EMA period (default 9)
 */
export function calcMACD(
  candles: Candle[],
  fastPeriod = 12,
  slowPeriod = 26,
  signalPeriod = 9,
): MACDResult {
  const n = candles.length;
  const macd: (number | null)[] = new Array(n).fill(null);
  const signal: (number | null)[] = new Array(n).fill(null);
  const histogram: (number | null)[] = new Array(n).fill(null);

  if (n < slowPeriod) return { macd, signal, histogram };

  // Calculate fast and slow EMAs
  const fastEMA = emaFromClose(candles, fastPeriod);
  const slowEMA = emaFromClose(candles, slowPeriod);

  // MACD line = fast EMA - slow EMA
  for (let i = slowPeriod - 1; i < n; i++) {
    if (fastEMA[i] !== null && slowEMA[i] !== null) {
      macd[i] = fastEMA[i]! - slowEMA[i]!;
    }
  }

  // Signal line = EMA of MACD line
  const macdStart = slowPeriod - 1;
  const signalStart = macdStart + signalPeriod - 1;

  if (n > signalStart) {
    // Seed signal with SMA of first signalPeriod MACD values
    let sum = 0;
    for (let i = macdStart; i < macdStart + signalPeriod; i++) {
      sum += macd[i]!;
    }
    let signalEma = sum / signalPeriod;
    signal[signalStart] = signalEma;
    histogram[signalStart] = macd[signalStart]! - signalEma;

    const k = 2 / (signalPeriod + 1);
    for (let i = signalStart + 1; i < n; i++) {
      if (macd[i] !== null) {
        signalEma = macd[i]! * k + signalEma * (1 - k);
        signal[i] = signalEma;
        histogram[i] = macd[i]! - signalEma;
      }
    }
  }

  return { macd, signal, histogram };
}

/** Helper: compute EMA from candle close prices */
function emaFromClose(candles: Candle[], period: number): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n < period) return result;

  let sum = 0;
  for (let i = 0; i < period; i++) sum += candles[i].close;
  let ema = sum / period;
  result[period - 1] = ema;

  const k = 2 / (period + 1);
  for (let i = period; i < n; i++) {
    ema = candles[i].close * k + ema * (1 - k);
    result[i] = ema;
  }
  return result;
}
