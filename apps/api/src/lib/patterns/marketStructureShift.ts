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
 *      → BOS (bullish) if already in uptrend, CHoCH (bullish) if in downtrend
 *    - If candle.close breaks below a prior swing low:
 *      → BOS (bearish) if already in downtrend, CHoCH (bearish) if in uptrend
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

  // Track the most recent unbroken swing high and swing low
  const swingHighs = swings.filter((s) => s.type === "high");
  const swingLows = swings.filter((s) => s.type === "low");

  // Determine initial trend from swing sequence
  let trend: Trend = "none";

  // Set of swing indices already broken (each level breaks only once)
  const brokenSwings = new Set<number>();

  // Process candles after the first swing is confirmed
  const firstSwingEnd = swings[0].index + swingLen;

  for (let i = firstSwingEnd + 1; i < n; i++) {
    const candle = candles[i];

    // Update trend from confirmed swings before this candle
    trend = deriveTrend(swingHighs, swingLows, i);

    // Check for breaks of prior swing highs (bullish break)
    for (let sh = swingHighs.length - 1; sh >= 0; sh--) {
      const swing = swingHighs[sh];
      if (swing.index >= i) continue;
      if (brokenSwings.has(swing.index)) continue;

      if (candle.close > swing.level) {
        const type: MssType = trend === "up" ? "BOS" : "CHoCH";
        results.push({
          index: i,
          type,
          direction: "bullish",
          brokenLevel: swing.level,
          timestamp: candle.openTime,
        });
        brokenSwings.add(swing.index);
        break; // only break the most recent unbroken swing
      }
      break; // only check the most recent unbroken swing high
    }

    // Check for breaks of prior swing lows (bearish break)
    for (let sl = swingLows.length - 1; sl >= 0; sl--) {
      const swing = swingLows[sl];
      if (swing.index >= i) continue;
      if (brokenSwings.has(swing.index)) continue;

      if (candle.close < swing.level) {
        const type: MssType = trend === "down" ? "BOS" : "CHoCH";
        results.push({
          index: i,
          type,
          direction: "bearish",
          brokenLevel: swing.level,
          timestamp: candle.openTime,
        });
        brokenSwings.add(swing.index);
        break;
      }
      break;
    }
  }

  return results;
}

/**
 * Derive the prevailing trend from swing points confirmed before `beforeIndex`.
 */
function deriveTrend(
  swingHighs: { index: number; level: number }[],
  swingLows: { index: number; level: number }[],
  beforeIndex: number,
): Trend {
  // Get the last two swing highs before this index
  const recentHighs = swingHighs.filter((s) => s.index < beforeIndex);
  const recentLows = swingLows.filter((s) => s.index < beforeIndex);

  if (recentHighs.length >= 2 && recentLows.length >= 2) {
    const hh = recentHighs[recentHighs.length - 1].level > recentHighs[recentHighs.length - 2].level;
    const hl = recentLows[recentLows.length - 1].level > recentLows[recentLows.length - 2].level;
    const lh = recentHighs[recentHighs.length - 1].level < recentHighs[recentHighs.length - 2].level;
    const ll = recentLows[recentLows.length - 1].level < recentLows[recentLows.length - 2].level;

    if (hh && hl) return "up";
    if (lh && ll) return "down";
  }

  return "none";
}
