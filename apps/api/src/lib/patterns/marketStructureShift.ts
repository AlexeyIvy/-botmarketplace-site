/**
 * Market Structure Shift (MSS) detection.
 *
 * Detects Break of Structure (BOS) and Change of Character (CHoCH)
 * by tracking swing highs/lows and identifying when price breaks
 * a previous swing level.
 *
 * Logic:
 *
 * 1. Identify swing highs and swing lows using a lookback window
 *    (reuses findSwingPoints from liquiditySweep).
 *
 * 2. Determine the prevailing trend from the last two same-type swings:
 *    - If the latest swing high > previous swing high → uptrend
 *    - If the latest swing low < previous swing low → downtrend
 *
 * 3. For each candle after a swing point:
 *    - If candle.close breaks above a prior swing high:
 *      → BOS (bullish) if already in uptrend or trend is unestablished
 *      → CHoCH (bullish) if in downtrend
 *    - If candle.close breaks below a prior swing low:
 *      → BOS (bearish) if already in downtrend or trend is unestablished
 *      → CHoCH (bearish) if in uptrend
 *
 * When trend is "none" (insufficient swings to determine), breaks are
 * classified as BOS (establishing structure, not changing it).
 *
 * Each swing level is only broken once (first break wins).
 *
 * Pure function — no side effects, deterministic, no mutation of input.
 */

import type { Candle, MarketStructureShift, MssType } from "./types.js";
import { findSwingPoints } from "./liquiditySweep.js";

export interface DetectMssOptions {
  /**
   * Number of bars on each side required to confirm a swing point.
   * Default: 3.
   */
  swingLen?: number;
}

type Trend = "up" | "down" | "none";

/**
 * Detect market structure shifts (BOS and CHoCH) in a candle array.
 *
 * @param candles OHLCV array.
 * @param options Detection parameters.
 * @returns Array of detected structure shifts, ordered by index ascending.
 */
export function detectMarketStructureShifts(
  candles: Candle[],
  options: DetectMssOptions = {},
): MarketStructureShift[] {
  const { swingLen = 3 } = options;
  const n = candles.length;
  const results: MarketStructureShift[] = [];

  if (n < 2 * swingLen + 2) return results;

  const swings = findSwingPoints(candles, swingLen);
  if (swings.length < 2) return results;

  const swingHighs = swings.filter((s) => s.type === "high");
  const swingLows = swings.filter((s) => s.type === "low");

  // Pointer-based trend tracking: index of the last two confirmed
  // swing highs/lows before the current candle (avoids O(n*s) filter).
  let highPtr = -1; // index into swingHighs[] of last confirmed before candle i
  let lowPtr = -1;  // index into swingLows[] of last confirmed before candle i
  let trend: Trend = "none";

  const brokenSwings = new Set<number>();
  const firstSwingEnd = swings[0].index + swingLen;

  for (let i = firstSwingEnd + 1; i < n; i++) {
    const candle = candles[i];

    // Advance pointers to include all swings confirmed before candle i
    while (highPtr + 1 < swingHighs.length && swingHighs[highPtr + 1].index < i) {
      highPtr++;
    }
    while (lowPtr + 1 < swingLows.length && swingLows[lowPtr + 1].index < i) {
      lowPtr++;
    }

    // Derive trend from the last two confirmed swing highs/lows
    trend = deriveTrendFromPointers(swingHighs, swingLows, highPtr, lowPtr);

    // Check for breaks of prior swing highs (bullish break).
    // Only check the most recent unbroken swing high.
    for (let sh = swingHighs.length - 1; sh >= 0; sh--) {
      const swing = swingHighs[sh];
      if (swing.index >= i) continue;
      if (brokenSwings.has(swing.index)) continue;

      if (candle.close > swing.level) {
        // BOS if trend is already up or unestablished; CHoCH if trend is down
        const type: MssType = trend === "down" ? "CHoCH" : "BOS";
        results.push({
          index: i,
          type,
          direction: "bullish",
          brokenLevel: swing.level,
          timestamp: candle.openTime,
        });
        brokenSwings.add(swing.index);
      }
      break; // only check the most recent unbroken swing high
    }

    // Check for breaks of prior swing lows (bearish break).
    for (let sl = swingLows.length - 1; sl >= 0; sl--) {
      const swing = swingLows[sl];
      if (swing.index >= i) continue;
      if (brokenSwings.has(swing.index)) continue;

      if (candle.close < swing.level) {
        // BOS if trend is already down or unestablished; CHoCH if trend is up
        const type: MssType = trend === "up" ? "CHoCH" : "BOS";
        results.push({
          index: i,
          type,
          direction: "bearish",
          brokenLevel: swing.level,
          timestamp: candle.openTime,
        });
        brokenSwings.add(swing.index);
      }
      break;
    }
  }

  return results;
}

/**
 * Derive trend from pointer positions into pre-sorted swing arrays.
 * O(1) per call instead of O(s) filter.
 */
function deriveTrendFromPointers(
  swingHighs: { index: number; level: number }[],
  swingLows: { index: number; level: number }[],
  highPtr: number,
  lowPtr: number,
): Trend {
  if (highPtr < 1 || lowPtr < 1) return "none";

  const hh = swingHighs[highPtr].level > swingHighs[highPtr - 1].level;
  const hl = swingLows[lowPtr].level > swingLows[lowPtr - 1].level;
  const lh = swingHighs[highPtr].level < swingHighs[highPtr - 1].level;
  const ll = swingLows[lowPtr].level < swingLows[lowPtr - 1].level;

  if (hh && hl) return "up";
  if (lh && ll) return "down";
  return "none";
}
