/**
 * Multi-Timeframe Interval Alignment (#134 — Slice 1)
 *
 * Pure functions for aligning candle data across multiple timeframes.
 *
 * Core problem: when evaluating a 1m candle, which 5m/15m/1h candle is
 * "current"? This module provides deterministic alignment primitives.
 *
 * Concepts:
 *   - Primary TF: the timeframe on which signals are evaluated (e.g., 1m)
 *   - Context TFs: higher timeframes providing confluence (e.g., 5m, 15m, 1h)
 *   - Alignment: mapping a primary-TF candle to the correct context-TF candle
 *
 * Design:
 *   - Pure functions, no I/O
 *   - All alignment is timestamp-based (candle openTime in epoch ms)
 *   - No assumptions about candle source (works with any OHLCV data)
 */

/**
 * Standard OHLCV candle (compatible with bybitCandles.Candle).
 *
 * Intentionally duplicated here to keep this module free of exchange imports.
 * TypeScript structural typing means bybitCandles.Candle satisfies MtfCandle
 * without explicit conversion. Unify if a shared types package is introduced.
 */
export interface MtfCandle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ---------------------------------------------------------------------------
// Interval definitions
// ---------------------------------------------------------------------------

export type Interval = "1m" | "5m" | "15m" | "1h" | "4h" | "1d";

/** Duration of each interval in milliseconds */
export const INTERVAL_MS: Record<Interval, number> = {
  "1m": 60_000,
  "5m": 300_000,
  "15m": 900_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1d": 86_400_000,
};

/** Map from DSL timeframe names to interval */
export const TIMEFRAME_TO_INTERVAL: Record<string, Interval> = {
  M1: "1m",
  M5: "5m",
  M15: "15m",
  H1: "1h",
  H4: "4h",
  D1: "1d",
};

/** Ordered from smallest to largest */
export const INTERVAL_ORDER: Interval[] = ["1m", "5m", "15m", "1h", "4h", "1d"];

// ---------------------------------------------------------------------------
// Alignment primitives
// ---------------------------------------------------------------------------

/**
 * Compute the open time of the higher-TF candle that contains a given timestamp.
 *
 * Example: for timestamp in the middle of a 5m candle,
 *   alignToInterval(ts, "5m") → start of that 5m period
 *
 * Uses floor division on UTC epoch — deterministic, no timezone ambiguity.
 * All intervals are anchored to the Unix epoch (1970-01-01 00:00:00 UTC).
 * This is correct for 24/7 crypto markets with no DST. 4h boundaries fall
 * at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC.
 */
export function alignToInterval(timestampMs: number, interval: Interval): number {
  const ms = INTERVAL_MS[interval];
  return Math.floor(timestampMs / ms) * ms;
}

/**
 * Find the index of the context-TF candle that corresponds to a primary-TF candle.
 *
 * Given a primary candle's openTime and a sorted array of context-TF candles,
 * returns the index of the context candle whose period contains the primary candle.
 *
 * Uses binary search for O(log n) performance.
 *
 * @returns Index into contextCandles, or -1 if not found
 */
export function findContextCandleIndex(
  primaryOpenTime: number,
  contextCandles: MtfCandle[],
  contextInterval: Interval,
): number {
  const alignedTime = alignToInterval(primaryOpenTime, contextInterval);

  // Binary search for the context candle with openTime === alignedTime
  let lo = 0;
  let hi = contextCandles.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >>> 1;
    const midTime = contextCandles[mid].openTime;
    if (midTime === alignedTime) return mid;
    if (midTime < alignedTime) lo = mid + 1;
    else hi = mid - 1;
  }

  return -1;
}

/**
 * Build a lookup table mapping each primary-TF candle index to the
 * corresponding context-TF candle index.
 *
 * The result array has the same length as primaryCandles.
 * result[i] = index into contextCandles, or -1 if no match.
 *
 * Optimized: walks both arrays in parallel (O(n+m) instead of O(n log m)).
 *
 * @precondition Both primaryCandles and contextCandles must be sorted by
 *               openTime ascending. Unsorted input produces undefined results.
 */
export function buildAlignmentMap(
  primaryCandles: MtfCandle[],
  contextCandles: MtfCandle[],
  contextInterval: Interval,
): number[] {
  const map = new Array<number>(primaryCandles.length).fill(-1);
  if (contextCandles.length === 0) return map;

  let ctxIdx = 0;

  for (let i = 0; i < primaryCandles.length; i++) {
    const aligned = alignToInterval(primaryCandles[i].openTime, contextInterval);

    // Advance context pointer to match or pass the aligned time
    while (ctxIdx < contextCandles.length && contextCandles[ctxIdx].openTime < aligned) {
      ctxIdx++;
    }

    // Check if we found an exact match
    if (ctxIdx < contextCandles.length && contextCandles[ctxIdx].openTime === aligned) {
      map[i] = ctxIdx;
    }
  }

  return map;
}

// ---------------------------------------------------------------------------
// Multi-TF candle bundle
// ---------------------------------------------------------------------------

/** A bundle of candle arrays, one per timeframe */
export interface CandleBundle {
  /** The primary evaluation timeframe */
  primaryInterval: Interval;
  /** Candle data keyed by interval */
  candles: Record<string, MtfCandle[]>;
  /** Pre-computed alignment maps: alignmentMaps[contextInterval][primaryIdx] = contextIdx */
  alignmentMaps: Record<string, number[]>;
}

/**
 * Create a CandleBundle from a set of candle arrays.
 *
 * Pre-computes alignment maps for all context intervals relative to the primary.
 *
 * @param primaryInterval  The primary evaluation interval
 * @param candlesByInterval  Map of interval → candle array (must include primary)
 */
export function createCandleBundle(
  primaryInterval: Interval,
  candlesByInterval: Record<string, MtfCandle[]>,
): CandleBundle {
  const primary = candlesByInterval[primaryInterval];
  if (!primary) {
    throw new Error(`Primary interval "${primaryInterval}" not found in candle data`);
  }

  const alignmentMaps: Record<string, number[]> = {};
  for (const [interval, candles] of Object.entries(candlesByInterval)) {
    if (interval === primaryInterval) continue;
    if (!INTERVAL_MS[interval as Interval]) continue;
    alignmentMaps[interval] = buildAlignmentMap(primary, candles, interval as Interval);
  }

  return {
    primaryInterval,
    candles: candlesByInterval,
    alignmentMaps,
  };
}

/**
 * Look up the context-TF candle value at a given primary-TF bar index.
 *
 * @returns The context candle, or null if not aligned (gap in data)
 */
export function getContextCandle(
  bundle: CandleBundle,
  contextInterval: string,
  primaryBarIndex: number,
): MtfCandle | null {
  const map = bundle.alignmentMaps[contextInterval];
  if (!map) return null;

  const ctxIdx = map[primaryBarIndex];
  if (ctxIdx < 0) return null;

  return bundle.candles[contextInterval]?.[ctxIdx] ?? null;
}

// ---------------------------------------------------------------------------
// Session boundaries
// ---------------------------------------------------------------------------

/** Known trading session definitions (UTC hours) */
export interface SessionWindow {
  name: string;
  /** UTC hour when session opens (0-23) */
  openHourUtc: number;
  /** UTC hour when session closes (0-23) */
  closeHourUtc: number;
}

export const SESSIONS: Record<string, SessionWindow> = {
  london: { name: "London", openHourUtc: 8, closeHourUtc: 16 },
  new_york: { name: "New York", openHourUtc: 13, closeHourUtc: 21 },
  asia: { name: "Asia", openHourUtc: 0, closeHourUtc: 8 },
  utc_day: { name: "UTC Day", openHourUtc: 0, closeHourUtc: 0 }, // 24h, resets at midnight
};

/**
 * Check if a timestamp falls within a trading session.
 *
 * For utc_day, always returns true (full 24h session).
 */
export function isInSession(timestampMs: number, session: SessionWindow): boolean {
  if (session.openHourUtc === session.closeHourUtc) return true; // 24h session

  const date = new Date(timestampMs);
  const hour = date.getUTCHours();

  if (session.openHourUtc < session.closeHourUtc) {
    return hour >= session.openHourUtc && hour < session.closeHourUtc;
  }
  // Wraps midnight (e.g., 22:00 → 06:00)
  return hour >= session.openHourUtc || hour < session.closeHourUtc;
}

/**
 * Compute the start of the current session period for a given timestamp.
 *
 * Used for session-anchored VWAP resets: when the session starts,
 * VWAP accumulation restarts from zero.
 */
export function getSessionStart(timestampMs: number, session: SessionWindow): number {
  const date = new Date(timestampMs);
  const hour = date.getUTCHours();

  const sessionDate = new Date(date);
  sessionDate.setUTCMinutes(0, 0, 0);
  sessionDate.setUTCHours(session.openHourUtc);

  // If current hour is before session open, session started yesterday
  if (session.openHourUtc <= session.closeHourUtc) {
    if (hour < session.openHourUtc) {
      sessionDate.setUTCDate(sessionDate.getUTCDate() - 1);
    }
  } else {
    // Wrap case: if we're in the early-morning portion (after midnight)
    if (hour < session.openHourUtc && hour < session.closeHourUtc) {
      sessionDate.setUTCDate(sessionDate.getUTCDate() - 1);
    }
  }

  return sessionDate.getTime();
}

/**
 * Check if a candle is the first bar of a new session.
 *
 * Compares the session start of the current candle vs the previous candle.
 * If they differ, it's a new session → triggers VWAP/profile reset.
 */
export function isSessionBoundary(
  currentOpenTime: number,
  previousOpenTime: number,
  session: SessionWindow,
): boolean {
  return getSessionStart(currentOpenTime, session) !== getSessionStart(previousOpenTime, session);
}
