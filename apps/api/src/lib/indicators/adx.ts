/**
 * Average Directional Index (ADX) — Wilder's method.
 *
 * Measures trend strength on a 0–100 scale regardless of direction.
 *
 * Internal steps:
 *   1. +DM / -DM (directional movement per bar)
 *   2. Wilder-smooth +DM, -DM, and TR over `period` bars
 *   3. +DI = smoothed(+DM) / smoothed(TR) * 100
 *      -DI = smoothed(-DM) / smoothed(TR) * 100
 *   4. DX = |+DI - -DI| / (+DI + -DI) * 100
 *   5. ADX = Wilder-smoothed DX over `period` bars
 *
 * Warm-up: ADX is null for the first (2 * period - 1) bars.
 *
 * Implementation choice: classic Wilder with SMA seed for the first smoothed values.
 * This matches TradingView's "ADX" built-in indicator.
 */

import type { Candle } from "./types.js";

export interface ADXResult {
  adx: (number | null)[];
  plusDI: (number | null)[];
  minusDI: (number | null)[];
}

/**
 * Compute ADX, +DI, -DI.
 * @param candles OHLCV array
 * @param period  ADX period (default 14)
 */
export function calcADX(candles: Candle[], period = 14): ADXResult {
  const n = candles.length;
  const adx: (number | null)[] = new Array(n).fill(null);
  const plusDI: (number | null)[] = new Array(n).fill(null);
  const minusDI: (number | null)[] = new Array(n).fill(null);

  if (n < 2) return { adx, plusDI, minusDI };

  // Step 1: Raw directional movement and true range
  const rawPlusDM = new Array<number>(n).fill(0);
  const rawMinusDM = new Array<number>(n).fill(0);
  const rawTR = new Array<number>(n).fill(0);

  for (let i = 1; i < n; i++) {
    const { high, low } = candles[i];
    const prevHigh = candles[i - 1].high;
    const prevLow = candles[i - 1].low;
    const prevClose = candles[i - 1].close;

    // True Range
    rawTR[i] = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));

    // Directional Movement
    const upMove = high - prevHigh;
    const downMove = prevLow - low;

    rawPlusDM[i] = upMove > downMove && upMove > 0 ? upMove : 0;
    rawMinusDM[i] = downMove > upMove && downMove > 0 ? downMove : 0;
  }

  // Need at least period + 1 bars for first smoothed values (index 1..period)
  if (n < period + 1) return { adx, plusDI, minusDI };

  // Step 2: Wilder smoothing — seed with SMA of first `period` raw values (indices 1..period)
  let smoothPlusDM = 0;
  let smoothMinusDM = 0;
  let smoothTR = 0;

  for (let i = 1; i <= period; i++) {
    smoothPlusDM += rawPlusDM[i];
    smoothMinusDM += rawMinusDM[i];
    smoothTR += rawTR[i];
  }

  // DX values for later ADX smoothing
  const dxValues: number[] = [];

  // First DI values at index = period
  const computeDI = (idx: number): void => {
    const pdi = smoothTR > 0 ? (smoothPlusDM / smoothTR) * 100 : 0;
    const mdi = smoothTR > 0 ? (smoothMinusDM / smoothTR) * 100 : 0;
    plusDI[idx] = pdi;
    minusDI[idx] = mdi;

    const diSum = pdi + mdi;
    const dx = diSum > 0 ? (Math.abs(pdi - mdi) / diSum) * 100 : 0;
    dxValues.push(dx);
  };

  computeDI(period);

  // Continue Wilder smoothing for subsequent bars
  for (let i = period + 1; i < n; i++) {
    smoothPlusDM = smoothPlusDM - smoothPlusDM / period + rawPlusDM[i];
    smoothMinusDM = smoothMinusDM - smoothMinusDM / period + rawMinusDM[i];
    smoothTR = smoothTR - smoothTR / period + rawTR[i];

    computeDI(i);
  }

  // Step 5: ADX = Wilder-smoothed DX
  // Need `period` DX values before first ADX (seed with SMA)
  if (dxValues.length < period) return { adx, plusDI, minusDI };

  let adxVal = 0;
  for (let i = 0; i < period; i++) adxVal += dxValues[i];
  adxVal /= period;

  // First ADX at index = 2 * period - 1
  const adxStartIdx = 2 * period - 1;
  if (adxStartIdx < n) adx[adxStartIdx] = adxVal;

  // Smooth subsequent ADX values
  for (let i = period; i < dxValues.length; i++) {
    adxVal = (adxVal * (period - 1) + dxValues[i]) / period;
    const candleIdx = period + i; // offset: dxValues[0] corresponds to candle index `period`
    if (candleIdx < n) adx[candleIdx] = adxVal;
  }

  return { adx, plusDI, minusDI };
}
