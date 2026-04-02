/**
 * MTF Indicator Resolver Tests (#134 — Slice 2)
 *
 * Deterministic tests for multi-timeframe indicator resolution.
 */

import { describe, it, expect } from "vitest";
import type { Candle } from "../../src/lib/bybitCandles.js";
import type { DslIndicatorRef } from "../../src/lib/dslEvaluator.js";
import {
  resolveMtfIndicator,
  resolveMtfIndicatorAt,
  createMtfCache,
} from "../../src/lib/mtf/mtfIndicatorResolver.js";
import {
  createCandleBundle,
  INTERVAL_MS,
  type Interval,
} from "../../src/lib/mtf/intervalAlignment.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const ALIGNED_START = 1700006400000; // UTC midnight, aligned to all intervals

function makeCandles(interval: Interval, count: number, startPrice = 100, step = 1): Candle[] {
  const ms = INTERVAL_MS[interval];
  const candles: Candle[] = [];
  for (let i = 0; i < count; i++) {
    const close = startPrice + i * step;
    candles.push({
      openTime: ALIGNED_START + i * ms,
      open: close - step * 0.3,
      high: close + step * 0.5,
      low: close - step * 0.5,
      close,
      volume: 1000 + i,
    });
  }
  return candles;
}

function makeSmaRef(length: number, sourceTimeframe?: string): DslIndicatorRef {
  return { type: "SMA", length, ...(sourceTimeframe ? { sourceTimeframe } : {}) };
}

// ---------------------------------------------------------------------------
// resolveMtfIndicator — no MTF (fallback to primary)
// ---------------------------------------------------------------------------

describe("resolveMtfIndicator — single TF (no bundle)", () => {
  it("computes SMA on primary candles when no sourceTimeframe", () => {
    const candles = makeCandles("1m", 20, 100, 1);
    const cache = createMtfCache();

    const result = resolveMtfIndicator(
      makeSmaRef(5),
      candles,
      cache,
      null, // no bundle
    );

    expect(result).toHaveLength(20);
    // SMA(5) needs 5 bars warm-up → first 4 are null
    for (let i = 0; i < 4; i++) expect(result[i]).toBeNull();
    expect(result[4]).not.toBeNull();
    // SMA(5) at bar 4: avg of bars 0-4 = (100+101+102+103+104)/5 = 102
    expect(result[4]).toBeCloseTo(102, 2);
  });

  it("falls back to primary when sourceTimeframe set but bundle is null", () => {
    const candles = makeCandles("1m", 20, 100, 1);
    const cache = createMtfCache();

    const result = resolveMtfIndicator(
      makeSmaRef(5, "5m"),
      candles,
      cache,
      null,
    );

    // Should compute on primary since bundle is null
    expect(result).toHaveLength(20);
    expect(result[4]).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// resolveMtfIndicator — with CandleBundle
// ---------------------------------------------------------------------------

describe("resolveMtfIndicator — MTF resolution via CandleBundle", () => {
  function makeTestBundle() {
    // Primary: 1m candles (30 bars, price 100→129)
    // Context: 5m candles (6 bars, price 100→105 each bar = avg of 5 1m bars)
    const c1m = makeCandles("1m", 30, 100, 1);
    // For 5m: each bar represents the average of 5 1m bars
    // 5m bar 0: close = 102 (avg of 100-104), bar 1: close = 107, etc.
    const c5m = makeCandles("5m", 6, 102, 5);

    return createCandleBundle("1m", { "1m": c1m, "5m": c5m });
  }

  it("resolves indicator from context TF when sourceTimeframe is set", () => {
    const bundle = makeTestBundle();
    const cache = createMtfCache();

    const result = resolveMtfIndicator(
      makeSmaRef(3, "5m"), // SMA(3) on 5m candles
      bundle.candles["1m"] as Candle[],
      cache,
      bundle,
    );

    expect(result).toHaveLength(30);

    // SMA(3) on 5m needs 3 bars → first 2 5m bars have null
    // 1m bars 0-9 map to 5m bars 0-1 → SMA still warming up → null
    for (let i = 0; i < 10; i++) {
      expect(result[i]).toBeNull();
    }

    // 1m bars 10-14 map to 5m bar 2 → SMA(3) ready
    // SMA(3) at 5m bar 2 = (102 + 107 + 112) / 3 = 107
    expect(result[10]).not.toBeNull();
    expect(result[10]).toBeCloseTo(107, 0);

    // All 1m bars within same 5m period get same value
    expect(result[10]).toBe(result[11]);
    expect(result[11]).toBe(result[12]);
    expect(result[12]).toBe(result[13]);
    expect(result[13]).toBe(result[14]);
  });

  it("context TF values step-change at 5m boundaries", () => {
    const bundle = makeTestBundle();
    const cache = createMtfCache();

    const result = resolveMtfIndicator(
      makeSmaRef(3, "5m"),
      bundle.candles["1m"] as Candle[],
      cache,
      bundle,
    );

    // 5m bar 2 value vs 5m bar 3 value should differ
    const val_5mBar2 = result[10]; // maps to 5m[2]
    const val_5mBar3 = result[15]; // maps to 5m[3]
    if (val_5mBar2 !== null && val_5mBar3 !== null) {
      expect(val_5mBar3).not.toBe(val_5mBar2);
    }
  });

  it("falls back to primary when context TF not in bundle", () => {
    const bundle = makeTestBundle();
    const cache = createMtfCache();

    const result = resolveMtfIndicator(
      makeSmaRef(5, "15m"), // 15m not in bundle
      bundle.candles["1m"] as Candle[],
      cache,
      bundle,
    );

    // Falls back to computing on primary (1m)
    expect(result).toHaveLength(30);
    expect(result[4]).not.toBeNull(); // SMA(5) ready at bar 4
  });

  it("uses separate caches per TF (no cross-pollution)", () => {
    const bundle = makeTestBundle();
    const cache = createMtfCache();

    // Compute SMA(5) on primary
    const primarySma = resolveMtfIndicator(
      makeSmaRef(5),
      bundle.candles["1m"] as Candle[],
      cache,
      bundle,
    );

    // Compute SMA(3) on 5m
    const contextSma = resolveMtfIndicator(
      makeSmaRef(3, "5m"),
      bundle.candles["1m"] as Candle[],
      cache,
      bundle,
    );

    // Both should have different values (different source data)
    if (primarySma[10] !== null && contextSma[10] !== null) {
      expect(primarySma[10]).not.toBe(contextSma[10]);
    }

    // Primary cache should have SMA entries, context cache should have separate entries
    expect(cache.primary.sma.size).toBeGreaterThan(0);
    expect(cache.context.size).toBeGreaterThan(0);
  });

  it("is deterministic — same inputs, same results", () => {
    const bundle = makeTestBundle();

    const a = resolveMtfIndicator(
      makeSmaRef(3, "5m"),
      bundle.candles["1m"] as Candle[],
      createMtfCache(),
      bundle,
    );

    const b = resolveMtfIndicator(
      makeSmaRef(3, "5m"),
      bundle.candles["1m"] as Candle[],
      createMtfCache(),
      bundle,
    );

    expect(a).toEqual(b);
  });
});

// ---------------------------------------------------------------------------
// resolveMtfIndicatorAt
// ---------------------------------------------------------------------------

describe("resolveMtfIndicatorAt", () => {
  it("returns value at specific bar", () => {
    const candles = makeCandles("1m", 20, 100, 1);
    const cache = createMtfCache();

    const val = resolveMtfIndicatorAt(makeSmaRef(5), 4, candles, cache, null);
    expect(val).toBeCloseTo(102, 2);
  });

  it("returns null for bar before warm-up", () => {
    const candles = makeCandles("1m", 20, 100, 1);
    const cache = createMtfCache();

    const val = resolveMtfIndicatorAt(makeSmaRef(5), 2, candles, cache, null);
    expect(val).toBeNull();
  });

  it("returns null for out-of-range bar", () => {
    const candles = makeCandles("1m", 10, 100, 1);
    const cache = createMtfCache();

    const val = resolveMtfIndicatorAt(makeSmaRef(5), 99, candles, cache, null);
    expect(val).toBeNull();
  });
});
