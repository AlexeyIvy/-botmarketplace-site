/**
 * Pattern Engine — converts SMC pattern detections to indicator-compatible
 * number series for use in the DSL evaluator and backtest pipeline.
 *
 * Each pattern detector returns structured results (FairValueGap[], etc.).
 * The evaluator needs `(number | null)[]` series of the same length as
 * the candle array. This module bridges the two representations.
 *
 * Encoding convention:
 *   +1 = bullish signal at this bar
 *   -1 = bearish signal at this bar
 *   +2 = bullish CHoCH (MSS only)
 *   -2 = bearish CHoCH (MSS only)
 *    0 = no signal
 *  null = insufficient data (warm-up period)
 *
 * Pure functions — deterministic, no side effects.
 */

import type { Candle } from "../indicators/types.js";
import { detectFairValueGaps } from "../patterns/fairValueGap.js";
import type { DetectFvgOptions } from "../patterns/fairValueGap.js";
import { detectLiquiditySweeps } from "../patterns/liquiditySweep.js";
import type { DetectSweepOptions } from "../patterns/liquiditySweep.js";
import { detectOrderBlocks } from "../patterns/orderBlock.js";
import type { DetectObOptions } from "../patterns/orderBlock.js";
import { detectMarketStructureShifts } from "../patterns/marketStructureShift.js";
import type { DetectMssOptions } from "../patterns/marketStructureShift.js";

/**
 * Convert Fair Value Gap detections to a number series.
 * +1 at the middle candle of a bullish FVG, -1 for bearish, 0 otherwise.
 */
export function fvgSeries(
  candles: Candle[],
  options?: DetectFvgOptions,
): (number | null)[] {
  const n = candles.length;
  const result: (number | null)[] = new Array(n).fill(0);
  if (n < 3) return new Array(n).fill(null);

  // Mark first 2 bars as null (warm-up: need 3 candles minimum)
  result[0] = null;
  result[1] = null;

  const fvgs = detectFairValueGaps(candles, options);
  for (const fvg of fvgs) {
    result[fvg.index] = fvg.direction === "bullish" ? 1 : -1;
  }
  return result;
}

/**
 * Convert Liquidity Sweep detections to a number series.
 * +1 at a bullish sweep candle, -1 for bearish, 0 otherwise.
 */
export function sweepSeries(
  candles: Candle[],
  options?: DetectSweepOptions,
): (number | null)[] {
  const swingLen = options?.swingLen ?? 3;
  const n = candles.length;
  const minBars = 2 * swingLen + 2;
  if (n < minBars) return new Array(n).fill(null);

  const result: (number | null)[] = new Array(n).fill(0);
  // Mark warm-up bars as null
  for (let i = 0; i < swingLen; i++) result[i] = null;

  const sweeps = detectLiquiditySweeps(candles, options);
  for (const sweep of sweeps) {
    // If multiple sweeps on same bar, last one wins (rare edge case)
    result[sweep.index] = sweep.direction === "bullish" ? 1 : -1;
  }
  return result;
}

/**
 * Convert Order Block detections to a number series.
 * +1 at a bullish OB candle, -1 for bearish, 0 otherwise.
 */
export function orderBlockSeries(
  candles: Candle[],
  options?: DetectObOptions,
): (number | null)[] {
  const atrPeriod = options?.atrPeriod ?? 14;
  const n = candles.length;
  if (n < atrPeriod + 1) return new Array(n).fill(null);

  const result: (number | null)[] = new Array(n).fill(0);
  // Mark ATR warm-up as null
  for (let i = 0; i < atrPeriod; i++) result[i] = null;

  const obs = detectOrderBlocks(candles, options);
  for (const ob of obs) {
    result[ob.index] = ob.direction === "bullish" ? 1 : -1;
  }
  return result;
}

/**
 * Convert Market Structure Shift detections to a number series.
 * +1 = bullish BOS, -1 = bearish BOS, +2 = bullish CHoCH, -2 = bearish CHoCH.
 */
export function mssSeries(
  candles: Candle[],
  options?: DetectMssOptions,
): (number | null)[] {
  const swingLen = options?.swingLen ?? 3;
  const n = candles.length;
  const minBars = 2 * swingLen + 2;
  if (n < minBars) return new Array(n).fill(null);

  const result: (number | null)[] = new Array(n).fill(0);
  for (let i = 0; i < swingLen; i++) result[i] = null;

  const shifts = detectMarketStructureShifts(candles, options);
  for (const shift of shifts) {
    if (shift.type === "BOS") {
      result[shift.index] = shift.direction === "bullish" ? 1 : -1;
    } else {
      result[shift.index] = shift.direction === "bullish" ? 2 : -2;
    }
  }
  return result;
}
