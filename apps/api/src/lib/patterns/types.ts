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
 * A detected Liquidity Sweep.
 *
 * A liquidity sweep occurs when price breaks beyond a swing high/low
 * (sweeping stop-loss orders) then reverses, signaling smart money
 * activity.
 *
 * - Bullish sweep: price dips below a swing low then closes back above it.
 *   Suggests short-side liquidity was taken; reversal to the upside likely.
 * - Bearish sweep: price spikes above a swing high then closes back below it.
 *   Suggests long-side liquidity was taken; reversal to the downside likely.
 */
export interface LiquiditySweep {
  /** Index of the sweep candle. */
  index: number;
  /** Direction of the expected move after the sweep. */
  direction: SmcDirection;
  /** The swing level that was swept. */
  level: number;
  /** How far price penetrated beyond the swing level. */
  penetration: number;
  /** openTime of the sweep candle. */
  timestamp: number;
}

/**
 * A detected Order Block (OB).
 *
 * An order block is the last opposing candle before a strong impulsive move,
 * representing an area where institutional orders were placed.
 *
 * - Bullish OB: the last bearish candle before a strong bullish move.
 *   Zone: [candle.low, candle.high]. Price may retrace here for a long entry.
 * - Bearish OB: the last bullish candle before a strong bearish move.
 *   Zone: [candle.low, candle.high]. Price may retrace here for a short entry.
 */
export interface OrderBlock {
  /** Index of the order block candle. */
  index: number;
  /** Direction of the expected continuation after a retest. */
  direction: SmcDirection;
  /** Upper edge of the OB zone (candle high). */
  high: number;
  /** Lower edge of the OB zone (candle low). */
  low: number;
  /** Body size of the impulse candle(s) that confirmed the OB. */
  impulseStrength: number;
  /** openTime of the OB candle. */
  timestamp: number;
}

/**
 * Type of market structure shift.
 *
 * - BOS (Break of Structure): price breaks a swing point in the direction
 *   of the existing trend, confirming continuation.
 * - CHoCH (Change of Character): price breaks a swing point against the
 *   prevailing trend, signaling a potential reversal.
 */
export type MssType = "BOS" | "CHoCH";

/**
 * A detected Market Structure Shift (MSS).
 *
 * Market structure is defined by swing highs and swing lows:
 * - Uptrend: higher highs and higher lows
 * - Downtrend: lower highs and lower lows
 *
 * A BOS confirms the current trend; a CHoCH signals a trend change.
 */
export interface MarketStructureShift {
  /** Index of the candle that caused the break. */
  index: number;
  /** Type: BOS (trend continuation) or CHoCH (trend reversal). */
  type: MssType;
  /** Direction of the expected move after the shift. */
  direction: SmcDirection;
  /** The swing level that was broken. */
  brokenLevel: number;
  /** openTime of the breaking candle. */
  timestamp: number;
}

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
