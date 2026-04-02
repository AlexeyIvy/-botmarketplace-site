/**
 * Order Block (OB) detection.
 *
 * An order block is the last opposing candle before a strong impulsive move.
 * It represents an area of institutional accumulation or distribution.
 *
 * Detection logic:
 *
 * 1. Scan for impulse candles — candles with body size ≥ minImpulseMultiple × ATR.
 * 2. Look back to find the last opposing candle before the impulse:
 *    - Bullish OB: last bearish candle (close < open) before a bullish impulse.
 *    - Bearish OB: last bullish candle (close > open) before a bearish impulse.
 * 3. The OB zone is [candle.low, candle.high] of that opposing candle.
 *
 * Uses a simple rolling ATR approximation (mean true range over `atrPeriod` bars)
 * to normalize impulse strength across different price levels.
 *
 * Pure function — no side effects, deterministic, no mutation of input.
 */

import type { Candle, OrderBlock } from "./types.js";

export interface DetectObOptions {
  /**
   * ATR period for normalizing impulse strength. Default: 14.
   */
  atrPeriod?: number;
  /**
   * Minimum impulse body size as a multiple of ATR. Default: 1.5.
   */
  minImpulseMultiple?: number;
  /**
   * Maximum lookback from the impulse candle to find the opposing candle.
   * Default: 5.
   */
  maxLookback?: number;
}

/**
 * Compute simple true range values for each candle.
 */
function trueRanges(candles: Candle[]): number[] {
  const n = candles.length;
  const tr = new Array<number>(n);
  for (let i = 0; i < n; i++) {
    const { high, low } = candles[i];
    if (i === 0) {
      tr[i] = high - low;
    } else {
      const pc = candles[i - 1].close;
      tr[i] = Math.max(high - low, Math.abs(high - pc), Math.abs(low - pc));
    }
  }
  return tr;
}

/**
 * Detect order blocks in a candle array.
 *
 * @param candles OHLCV array.
 * @param options Detection parameters.
 * @returns Array of detected order blocks, ordered by index ascending.
 */
export function detectOrderBlocks(
  candles: Candle[],
  options: DetectObOptions = {},
): OrderBlock[] {
  const { atrPeriod = 14, minImpulseMultiple = 1.5, maxLookback = 5 } = options;
  const n = candles.length;
  const results: OrderBlock[] = [];

  if (n < atrPeriod + 1) return results;

  const tr = trueRanges(candles);

  // Rolling ATR (simple moving average of TR)
  let trSum = 0;
  for (let i = 0; i < atrPeriod; i++) trSum += tr[i];

  for (let i = atrPeriod; i < n; i++) {
    // Update rolling ATR
    trSum += tr[i] - tr[i - atrPeriod];
    const atr = trSum / atrPeriod;

    if (atr === 0) continue;

    const candle = candles[i];
    const body = candle.close - candle.open; // positive = bullish, negative = bearish
    const absBody = Math.abs(body);

    // Check if this is an impulse candle
    if (absBody < minImpulseMultiple * atr) continue;

    const isBullishImpulse = body > 0;

    // Look back for the last opposing candle
    const lookbackEnd = Math.max(0, i - maxLookback);
    for (let j = i - 1; j >= lookbackEnd; j--) {
      const prev = candles[j];
      const prevBody = prev.close - prev.open;

      if (isBullishImpulse && prevBody < 0) {
        // Found a bearish candle before bullish impulse → bullish OB
        results.push({
          index: j,
          direction: "bullish",
          high: prev.high,
          low: prev.low,
          impulseStrength: absBody,
          timestamp: prev.openTime,
        });
        break;
      }

      if (!isBullishImpulse && prevBody > 0) {
        // Found a bullish candle before bearish impulse → bearish OB
        results.push({
          index: j,
          direction: "bearish",
          high: prev.high,
          low: prev.low,
          impulseStrength: absBody,
          timestamp: prev.openTime,
        });
        break;
      }
    }
  }

  return results;
}
