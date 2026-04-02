/**
 * Fair Value Gap (FVG) detection.
 *
 * An FVG is a 3-candle imbalance pattern used in Smart Money Concepts:
 *
 *   Bullish FVG: candle[i-2].high < candle[i].low
 *     → Gap zone: [candle[i-2].high, candle[i].low]
 *     → Indicates aggressive buying; price may retrace to fill the gap.
 *
 *   Bearish FVG: candle[i-2].low > candle[i].high
 *     → Gap zone: [candle[i].high, candle[i-2].low]
 *     → Indicates aggressive selling; price may retrace to fill the gap.
 *
 * The detector scans candles left-to-right and emits one FairValueGap per
 * qualifying 3-candle window. The middle candle (index i-1) is the impulse
 * candle, and its index is stored in the result.
 *
 * Pure function — no side effects, deterministic, no mutation of input.
 */

import type { Candle, FairValueGap } from "./types.js";

export interface DetectFvgOptions {
  /**
   * Minimum gap size as a fraction of the middle candle's body.
   * 0 = accept any gap. Default: 0 (no minimum).
   */
  minGapRatio?: number;
}

/**
 * Detect all Fair Value Gaps in a candle array.
 *
 * @param candles  OHLCV candle array (minimum 3 candles for any detection).
 * @param options  Optional detection parameters.
 * @returns Array of detected FVGs, ordered by index ascending.
 */
export function detectFairValueGaps(
  candles: Candle[],
  options: DetectFvgOptions = {},
): FairValueGap[] {
  const { minGapRatio = 0 } = options;
  const results: FairValueGap[] = [];
  const n = candles.length;

  if (n < 3) return results;

  for (let i = 2; i < n; i++) {
    const first = candles[i - 2];
    const middle = candles[i - 1];
    const third = candles[i];

    // Bullish FVG: first candle's high < third candle's low
    if (first.high < third.low) {
      const gapSize = third.low - first.high;
      const bodySize = Math.abs(middle.close - middle.open);

      if (minGapRatio === 0 || bodySize === 0 || gapSize / bodySize >= minGapRatio) {
        results.push({
          index: i - 1,
          direction: "bullish",
          high: third.low,
          low: first.high,
          timestamp: middle.openTime,
        });
      }
    }

    // Bearish FVG: first candle's low > third candle's high
    if (first.low > third.high) {
      const gapSize = first.low - third.high;
      const bodySize = Math.abs(middle.close - middle.open);

      if (minGapRatio === 0 || bodySize === 0 || gapSize / bodySize >= minGapRatio) {
        results.push({
          index: i - 1,
          direction: "bearish",
          high: first.low,
          low: third.high,
          timestamp: middle.openTime,
        });
      }
    }
  }

  return results;
}

/**
 * Check whether a given FVG has been "filled" (price has retraced into the gap).
 *
 * A bullish FVG is filled when any candle after the FVG has a low ≤ fvg.low.
 * A bearish FVG is filled when any candle after the FVG has a high ≥ fvg.high.
 *
 * @param fvg     The FVG to check.
 * @param candles The full candle array (same array used for detection).
 * @returns Index of the first candle that fills the FVG, or -1 if unfilled.
 */
export function findFvgFillIndex(fvg: FairValueGap, candles: Candle[]): number {
  // Start scanning from the candle after the 3-candle window (fvg.index + 2)
  const startIdx = fvg.index + 2;

  for (let i = startIdx; i < candles.length; i++) {
    if (fvg.direction === "bullish" && candles[i].low <= fvg.low) {
      return i;
    }
    if (fvg.direction === "bearish" && candles[i].high >= fvg.high) {
      return i;
    }
  }

  return -1;
}
