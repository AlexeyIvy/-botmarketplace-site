/**
 * Multi-Timeframe Interval Alignment Tests (#134 — Slice 1)
 *
 * Deterministic tests for interval alignment, candle bundle, and session primitives.
 */

import { describe, it, expect } from "vitest";
import {
  type MtfCandle,
  alignToInterval,
  findContextCandleIndex,
  buildAlignmentMap,
  createCandleBundle,
  getContextCandle,
  isInSession,
  getSessionStart,
  isSessionBoundary,
  INTERVAL_MS,
  SESSIONS,
  TIMEFRAME_TO_INTERVAL,
  type Interval,
} from "../../src/lib/mtf/intervalAlignment.js";

// ---------------------------------------------------------------------------
// Candle fixtures
// ---------------------------------------------------------------------------

// Use a start time aligned to all intervals (divisible by 86400000 = 1d)
const ALIGNED_START = 1700006400000; // 2023-11-15 00:00:00 UTC (aligned to day boundary)

function makeCandles(interval: Interval, count: number, startMs: number = ALIGNED_START): MtfCandle[] {
  const ms = INTERVAL_MS[interval];
  const candles: MtfCandle[] = [];
  for (let i = 0; i < count; i++) {
    const openTime = startMs + i * ms;
    candles.push({
      openTime,
      open: 100 + i,
      high: 101 + i,
      low: 99 + i,
      close: 100.5 + i,
      volume: 1000,
    });
  }
  return candles;
}

// ---------------------------------------------------------------------------
// alignToInterval
// ---------------------------------------------------------------------------

describe("alignToInterval", () => {
  it("aligns 1m timestamp to 5m boundary", () => {
    const base = ALIGNED_START; // on 5m boundary
    const ts = base + 3 * 60_000; // +3m
    expect(alignToInterval(ts, "5m")).toBe(base);
  });

  it("aligns to 15m boundary", () => {
    const base = ALIGNED_START;
    expect(alignToInterval(base + 7 * 60_000, "15m")).toBe(base);
    expect(alignToInterval(base + 16 * 60_000, "15m")).toBe(base + 15 * 60_000);
  });

  it("aligns to 1h boundary", () => {
    const base = ALIGNED_START;
    const aligned = alignToInterval(base + 30 * 60_000, "1h");
    expect(aligned).toBe(base);
  });

  it("exact boundary returns itself", () => {
    expect(alignToInterval(ALIGNED_START, "5m")).toBe(ALIGNED_START);
    expect(alignToInterval(ALIGNED_START, "15m")).toBe(ALIGNED_START);
    expect(alignToInterval(ALIGNED_START, "1h")).toBe(ALIGNED_START);
  });

  it("is deterministic", () => {
    const ts = ALIGNED_START + 123456;
    expect(alignToInterval(ts, "15m")).toBe(alignToInterval(ts, "15m"));
  });
});

// ---------------------------------------------------------------------------
// findContextCandleIndex
// ---------------------------------------------------------------------------

describe("findContextCandleIndex", () => {
  it("finds correct 5m candle for a 1m timestamp", () => {
    const ctx5m = makeCandles("5m", 10);
    // A 1m candle 2 minutes into the 3rd 5m period
    const primaryTime = ctx5m[2].openTime + 2 * 60_000;
    expect(findContextCandleIndex(primaryTime, ctx5m, "5m")).toBe(2);
  });

  it("returns -1 when context data doesn't cover the timestamp", () => {
    const ctx5m = makeCandles("5m", 5);
    // Way after the last candle
    const farFuture = ctx5m[4].openTime + 100 * 300_000;
    expect(findContextCandleIndex(farFuture, ctx5m, "5m")).toBe(-1);
  });

  it("returns 0 for timestamp within first context candle", () => {
    const ctx5m = makeCandles("5m", 5);
    expect(findContextCandleIndex(ctx5m[0].openTime + 60_000, ctx5m, "5m")).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// buildAlignmentMap
// ---------------------------------------------------------------------------

describe("buildAlignmentMap", () => {
  it("maps every 1m candle to the correct 5m candle", () => {
    const start = ALIGNED_START;
    const primary1m = makeCandles("1m", 15, start);
    const context5m = makeCandles("5m", 3, start);

    const map = buildAlignmentMap(primary1m, context5m, "5m");
    expect(map).toHaveLength(15);

    // First 5 candles (0-4) should map to context[0]
    for (let i = 0; i < 5; i++) expect(map[i]).toBe(0);
    // Next 5 (5-9) should map to context[1]
    for (let i = 5; i < 10; i++) expect(map[i]).toBe(1);
    // Last 5 (10-14) should map to context[2]
    for (let i = 10; i < 15; i++) expect(map[i]).toBe(2);
  });

  it("maps 1m to 15m correctly", () => {
    const start = ALIGNED_START;
    const primary1m = makeCandles("1m", 30, start);
    const context15m = makeCandles("15m", 2, start);

    const map = buildAlignmentMap(primary1m, context15m, "15m");
    // First 15 candles → context[0], next 15 → context[1]
    for (let i = 0; i < 15; i++) expect(map[i]).toBe(0);
    for (let i = 15; i < 30; i++) expect(map[i]).toBe(1);
  });

  it("returns -1 for gaps in context data", () => {
    const start = ALIGNED_START;
    const primary1m = makeCandles("1m", 10, start);
    // Context starts at 5m offset (skip first 5m candle)
    const context5m = makeCandles("5m", 2, start + 300_000);

    const map = buildAlignmentMap(primary1m, context5m, "5m");
    // First 5 1m candles have no matching 5m candle
    for (let i = 0; i < 5; i++) expect(map[i]).toBe(-1);
    // Next 5 should map to context[0]
    for (let i = 5; i < 10; i++) expect(map[i]).toBe(0);
  });

  it("handles empty context array", () => {
    const primary = makeCandles("1m", 5);
    const map = buildAlignmentMap(primary, [], "5m");
    expect(map).toEqual([-1, -1, -1, -1, -1]);
  });
});

// ---------------------------------------------------------------------------
// CandleBundle
// ---------------------------------------------------------------------------

describe("createCandleBundle + getContextCandle", () => {
  it("creates bundle with alignment maps", () => {
    const start = ALIGNED_START;
    const bundle = createCandleBundle("1m", {
      "1m": makeCandles("1m", 30, start),
      "5m": makeCandles("5m", 6, start),
      "15m": makeCandles("15m", 2, start),
    });

    expect(bundle.primaryInterval).toBe("1m");
    expect(bundle.alignmentMaps["5m"]).toHaveLength(30);
    expect(bundle.alignmentMaps["15m"]).toHaveLength(30);
    expect(bundle.alignmentMaps["1m"]).toBeUndefined(); // primary not in maps
  });

  it("getContextCandle returns correct higher-TF candle", () => {
    const start = ALIGNED_START;
    const bundle = createCandleBundle("1m", {
      "1m": makeCandles("1m", 15, start),
      "5m": makeCandles("5m", 3, start),
    });

    // 1m bar 7 is in the 2nd 5m period
    const ctx = getContextCandle(bundle, "5m", 7);
    expect(ctx).not.toBeNull();
    expect(ctx!.openTime).toBe(start + 300_000); // 2nd 5m candle
  });

  it("returns null for unaligned bars", () => {
    const start = ALIGNED_START;
    const bundle = createCandleBundle("1m", {
      "1m": makeCandles("1m", 10, start),
      "5m": makeCandles("5m", 1, start + 300_000), // starts late
    });

    expect(getContextCandle(bundle, "5m", 0)).toBeNull(); // no match
    expect(getContextCandle(bundle, "5m", 5)).not.toBeNull(); // match
  });

  it("returns null for non-existent context interval", () => {
    const bundle = createCandleBundle("1m", { "1m": makeCandles("1m", 5) });
    expect(getContextCandle(bundle, "5m", 0)).toBeNull();
  });

  it("throws when primary interval is missing", () => {
    expect(() => createCandleBundle("1m", { "5m": makeCandles("5m", 5) })).toThrow("Primary interval");
  });
});

// ---------------------------------------------------------------------------
// Session helpers
// ---------------------------------------------------------------------------

describe("isInSession", () => {
  it("London session: 08:00-16:00 UTC", () => {
    const london = SESSIONS.london;
    // 10:00 UTC → in session
    const inSession = Date.UTC(2024, 0, 15, 10, 0, 0);
    expect(isInSession(inSession, london)).toBe(true);

    // 07:59 UTC → before session
    const before = Date.UTC(2024, 0, 15, 7, 59, 0);
    expect(isInSession(before, london)).toBe(false);

    // 16:00 UTC → session closed (exclusive)
    const atClose = Date.UTC(2024, 0, 15, 16, 0, 0);
    expect(isInSession(atClose, london)).toBe(false);
  });

  it("New York session: 13:00-21:00 UTC", () => {
    const ny = SESSIONS.new_york;
    expect(isInSession(Date.UTC(2024, 0, 15, 14, 30, 0), ny)).toBe(true);
    expect(isInSession(Date.UTC(2024, 0, 15, 12, 0, 0), ny)).toBe(false);
  });

  it("UTC day: always in session", () => {
    const utc = SESSIONS.utc_day;
    expect(isInSession(Date.UTC(2024, 0, 15, 3, 0, 0), utc)).toBe(true);
    expect(isInSession(Date.UTC(2024, 0, 15, 23, 59, 0), utc)).toBe(true);
  });
});

describe("getSessionStart", () => {
  it("returns London session start for mid-session timestamp", () => {
    const london = SESSIONS.london;
    const midSession = Date.UTC(2024, 0, 15, 12, 30, 0); // 12:30 UTC
    const start = getSessionStart(midSession, london);
    expect(start).toBe(Date.UTC(2024, 0, 15, 8, 0, 0)); // 08:00 UTC
  });

  it("returns previous day's session start for pre-session timestamp", () => {
    const london = SESSIONS.london;
    const beforeSession = Date.UTC(2024, 0, 15, 6, 0, 0); // 06:00 UTC
    const start = getSessionStart(beforeSession, london);
    expect(start).toBe(Date.UTC(2024, 0, 14, 8, 0, 0)); // previous day 08:00
  });
});

describe("isSessionBoundary", () => {
  it("detects new London session", () => {
    const london = SESSIONS.london;
    const prevDay = Date.UTC(2024, 0, 14, 15, 59, 0); // end of prev session
    const newDay = Date.UTC(2024, 0, 15, 8, 0, 0);   // start of new session
    expect(isSessionBoundary(newDay, prevDay, london)).toBe(true);
  });

  it("same session → no boundary", () => {
    const london = SESSIONS.london;
    const t1 = Date.UTC(2024, 0, 15, 10, 0, 0);
    const t2 = Date.UTC(2024, 0, 15, 10, 1, 0);
    expect(isSessionBoundary(t2, t1, london)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe("constants", () => {
  it("TIMEFRAME_TO_INTERVAL maps all DSL timeframes", () => {
    expect(TIMEFRAME_TO_INTERVAL["M1"]).toBe("1m");
    expect(TIMEFRAME_TO_INTERVAL["M5"]).toBe("5m");
    expect(TIMEFRAME_TO_INTERVAL["M15"]).toBe("15m");
    expect(TIMEFRAME_TO_INTERVAL["H1"]).toBe("1h");
    expect(TIMEFRAME_TO_INTERVAL["D1"]).toBe("1d");
  });

  it("INTERVAL_MS has correct millisecond values", () => {
    expect(INTERVAL_MS["1m"]).toBe(60_000);
    expect(INTERVAL_MS["5m"]).toBe(5 * 60_000);
    expect(INTERVAL_MS["15m"]).toBe(15 * 60_000);
    expect(INTERVAL_MS["1h"]).toBe(60 * 60_000);
    expect(INTERVAL_MS["1d"]).toBe(24 * 60 * 60_000);
  });
});
