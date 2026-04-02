/**
 * Liquidity Sweep detection.
 *
 * A liquidity sweep is when price briefly breaks beyond a swing high or
 * swing low (where stop-loss orders cluster) then reverses, indicating
 * that smart money has "swept" the liquidity at that level.
 *
 * Detection logic:
 *
 * 1. Identify swing highs/lows using a lookback window.
 *    - Swing high: a candle whose high is the highest in [i - swingLen, i + swingLen].
 *    - Swing low:  a candle whose low  is the lowest  in [i - swingLen, i + swingLen].
 *
 * 2. For each subsequent candle, check if it sweeps a prior swing level:
 *    - Bullish sweep: candle's low < swing low's low, but candle closes above the swing low.
 *    - Bearish sweep: candle's high > swing high's high, but candle closes below the swing high.
 *
 * Pure function — no side effects, deterministic, no mutation of input.
 */

import type { Candle, LiquiditySweep } from "./types.js";

export interface DetectSweepOptions {
  /**
   * Number of bars on each side required to confirm a swing point.
   * Higher values = fewer, stronger swings. Default: 3.
   */
  swingLen?: number;
  /**
   * Maximum number of bars after a swing point within which a sweep is valid.
   * Default: 50.
   */
  maxAge?: number;
}

interface SwingPoint {
  index: number;
  level: number;
  type: "high" | "low";
}

/**
 * Identify swing highs and lows in a candle array.
 *
 * A swing high at index i means candles[i].high is the maximum high
 * in the window [i - swingLen, i + swingLen].
 * A swing low at index i means candles[i].low is the minimum low
 * in the window [i - swingLen, i + swingLen].
 *
 * @param candles  OHLCV array.
 * @param swingLen Number of bars on each side.
 * @returns Array of swing points, ordered by index ascending.
 */
export function findSwingPoints(candles: Candle[], swingLen: number): SwingPoint[] {
  const n = candles.length;
  const swings: SwingPoint[] = [];

  for (let i = swingLen; i < n - swingLen; i++) {
    let isSwingHigh = true;
    let isSwingLow = true;

    for (let j = 1; j <= swingLen; j++) {
      if (candles[i].high <= candles[i - j].high || candles[i].high <= candles[i + j].high) {
        isSwingHigh = false;
      }
      if (candles[i].low >= candles[i - j].low || candles[i].low >= candles[i + j].low) {
        isSwingLow = false;
      }
      if (!isSwingHigh && !isSwingLow) break;
    }

    if (isSwingHigh) {
      swings.push({ index: i, level: candles[i].high, type: "high" });
    }
    if (isSwingLow) {
      swings.push({ index: i, level: candles[i].low, type: "low" });
    }
  }

  return swings;
}

/**
 * Detect liquidity sweeps in a candle array.
 *
 * @param candles OHLCV array (minimum 2 * swingLen + 2 for any detection).
 * @param options Detection parameters.
 * @returns Array of detected sweeps, ordered by index ascending.
 */
export function detectLiquiditySweeps(
  candles: Candle[],
  options: DetectSweepOptions = {},
): LiquiditySweep[] {
  const { swingLen = 3, maxAge = 50 } = options;
  const results: LiquiditySweep[] = [];
  const n = candles.length;

  if (n < 2 * swingLen + 2) return results;

  const swings = findSwingPoints(candles, swingLen);

  // For each candle after the first possible swing, check for sweeps
  for (let i = swingLen + 1; i < n; i++) {
    const candle = candles[i];

    for (const swing of swings) {
      // Swing must be before the current candle
      if (swing.index >= i) break;
      // Swing must not be too old
      if (i - swing.index > maxAge) continue;

      if (swing.type === "low") {
        // Bullish sweep: wick below swing low, close above it
        if (candle.low < swing.level && candle.close > swing.level) {
          results.push({
            index: i,
            direction: "bullish",
            level: swing.level,
            penetration: swing.level - candle.low,
            timestamp: candle.openTime,
          });
        }
      } else {
        // Bearish sweep: wick above swing high, close below it
        if (candle.high > swing.level && candle.close < swing.level) {
          results.push({
            index: i,
            direction: "bearish",
            level: swing.level,
            penetration: candle.high - swing.level,
            timestamp: candle.openTime,
          });
        }
      }
    }
  }

  return results;
}
