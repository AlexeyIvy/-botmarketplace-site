/**
 * Shared types for SMC (Smart Money Concepts) pattern detection.
 *
 * All pattern detectors consume Candle[] and return typed detection results.
 * Re-exports Candle from the indicator engine so consumers have a single import.
 */

export type { Candle } from "../indicators/types.js";

/** Direction of an SMC pattern. */
export type SmcDirection = "bullish" | "bearish";

/**
 * A detected Fair Value Gap (FVG).
 *
 * An FVG is a 3-candle imbalance where the wick of candle 1 does not overlap
 * with the wick of candle 3, leaving a "gap" that price may return to fill.
 *
 * - Bullish FVG: candle[i-2].high < candle[i].low  (gap up)
 * - Bearish FVG: candle[i-2].low  > candle[i].high (gap down)
 */
export interface FairValueGap {
  /** Index of the middle candle (the impulse candle). */
  index: number;
  /** Bullish = gap up, bearish = gap down. */
  direction: SmcDirection;
  /** Upper edge of the gap zone. */
  high: number;
  /** Lower edge of the gap zone. */
  low: number;
  /** openTime of the middle candle (for time-based lookups). */
  timestamp: number;
}
