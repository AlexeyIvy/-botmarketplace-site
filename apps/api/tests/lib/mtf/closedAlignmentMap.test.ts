/**
 * 52-T4 — `buildClosedAlignmentMap` & `createClosedCandleBundle` (look-ahead guard).
 *
 * Anchor: at primary bar `i`, the resolved HTF candle MUST satisfy
 *
 *   htf.openTime + INTERVAL_MS[contextInterval] ≤ primary[i].openTime
 *
 * i.e. the HTF candle has fully closed by the time the primary bar opens.
 * The standard {@link buildAlignmentMap} returns the *containing* HTF candle
 * (not yet closed) and is therefore not safe for backtest usage.
 */

import { describe, it, expect } from "vitest";
import {
  buildAlignmentMap,
  buildClosedAlignmentMap,
  createCandleBundle,
  createClosedCandleBundle,
  INTERVAL_MS,
  type MtfCandle,
} from "../../../src/lib/mtf/intervalAlignment.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/** 1 hour of M5 candles starting at 12:00 UTC (12 candles). */
function makeM5Candles(): MtfCandle[] {
  const start = Date.UTC(2026, 0, 1, 12, 0, 0);
  return Array.from({ length: 12 }, (_, i) => ({
    openTime: start + i * INTERVAL_MS["5m"],
    open: 100 + i,
    high: 101 + i,
    low: 99 + i,
    close: 100.5 + i,
    volume: 1,
  }));
}

/** 3 hours of H1 candles starting at 11:00 UTC (so H1[0]=11:00, H1[1]=12:00, H1[2]=13:00). */
function makeH1Candles(): MtfCandle[] {
  const start = Date.UTC(2026, 0, 1, 11, 0, 0);
  return Array.from({ length: 3 }, (_, i) => ({
    openTime: start + i * INTERVAL_MS["1h"],
    open: 1000 + i,
    high: 1001 + i,
    low: 999 + i,
    close: 1000.5 + i,
    volume: 100,
  }));
}

// ---------------------------------------------------------------------------
// buildClosedAlignmentMap
// ---------------------------------------------------------------------------

describe("buildClosedAlignmentMap", () => {
  it("at primary M5_12:05, the closed-safe H1 is the previous one (H1_11:00)", () => {
    const m5 = makeM5Candles();
    const h1 = makeH1Candles(); // 11:00, 12:00, 13:00
    const closed = buildClosedAlignmentMap(m5, h1, "1h");

    // Every M5 in [12:00, 13:00) must map to H1_11:00 (idx 0): H1_12:00 has
    // not yet closed (closes at 13:00).
    for (let i = 0; i < 12; i++) {
      expect(closed[i]).toBe(0);
    }
  });

  it("standard buildAlignmentMap maps to the containing (open) H1 — proves the difference", () => {
    const m5 = makeM5Candles();
    const h1 = makeH1Candles();
    const open = buildAlignmentMap(m5, h1, "1h");
    // Standard alignment maps every M5 in [12:00, 13:00) to H1_12:00 (idx 1).
    for (let i = 0; i < 12; i++) {
      expect(open[i]).toBe(1);
    }
  });

  it("first primary bars get -1 when no closed HTF is available yet", () => {
    const m5 = makeM5Candles();
    // Only one H1 candle, opening at 12:00 — closes at 13:00, never closed
    // before any of the M5 bars (which all live in [12:00, 13:00)).
    const h1: MtfCandle[] = [
      { openTime: Date.UTC(2026, 0, 1, 12, 0, 0), open: 1, high: 1, low: 1, close: 1, volume: 0 },
    ];
    const closed = buildClosedAlignmentMap(m5, h1, "1h");
    for (let i = 0; i < 12; i++) {
      expect(closed[i]).toBe(-1);
    }
  });

  it("advances to the next closed HTF as primary crosses the boundary", () => {
    // Build M5 candles spanning 12:00 .. 14:55 (35 bars, two H1 boundaries).
    const m5: MtfCandle[] = Array.from({ length: 36 }, (_, i) => ({
      openTime: Date.UTC(2026, 0, 1, 12, 0, 0) + i * INTERVAL_MS["5m"],
      open: i, high: i, low: i, close: i, volume: 1,
    }));
    const h1 = makeH1Candles(); // 11:00, 12:00, 13:00
    const closed = buildClosedAlignmentMap(m5, h1, "1h");

    // [12:00, 13:00) → H1_11:00 (idx 0).
    for (let i = 0; i < 12; i++) expect(closed[i]).toBe(0);
    // [13:00, 14:00) → H1_12:00 (idx 1, just closed at 13:00).
    for (let i = 12; i < 24; i++) expect(closed[i]).toBe(1);
    // [14:00, 14:55] → H1_13:00 (idx 2, just closed at 14:00).
    for (let i = 24; i < 36; i++) expect(closed[i]).toBe(2);
  });

  it("returns -1 for every primary bar when context is empty", () => {
    const m5 = makeM5Candles();
    const closed = buildClosedAlignmentMap(m5, [], "1h");
    expect(closed).toHaveLength(12);
    expect(closed.every((v) => v === -1)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// createClosedCandleBundle
// ---------------------------------------------------------------------------

describe("createClosedCandleBundle", () => {
  it("alignmentMaps use look-ahead-safe semantics; createCandleBundle does not", () => {
    const m5 = makeM5Candles();
    const h1 = makeH1Candles();

    const closed = createClosedCandleBundle("5m", { "5m": m5, "1h": h1 });
    const standard = createCandleBundle("5m", { "5m": m5, "1h": h1 });

    expect(closed.alignmentMaps["1h"]).toEqual(new Array(12).fill(0));
    expect(standard.alignmentMaps["1h"]).toEqual(new Array(12).fill(1));
  });

  it("throws when the primary interval is missing", () => {
    expect(() => createClosedCandleBundle("5m", { "1h": [] })).toThrow(
      /Primary interval "5m" not found/,
    );
  });

  it("ignores unknown interval keys silently", () => {
    const m5 = makeM5Candles();
    const bundle = createClosedCandleBundle("5m", { "5m": m5, "3m": [] });
    expect(bundle.alignmentMaps["3m"]).toBeUndefined();
  });
});
