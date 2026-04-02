import { describe, it, expect } from "vitest";
import {
  fvgSeries,
  sweepSeries,
  orderBlockSeries,
  mssSeries,
} from "../../src/lib/runtime/patternEngine.js";
import {
  bullishFvgFixture,
  bearishFvgFixture,
  noFvgFixture,
  flatMarketFixture,
  bullishSweepFixture,
  bearishSweepFixture,
  makeBullishObFixture,
  makeBearishObFixture,
  makeBosBullishFixture,
  makeChochBearishFixture,
} from "./smcFixtures.js";

// ── FVG Series ──────────────────────────────────────────────────────────────

describe("fvgSeries", () => {
  it("returns all null for insufficient data", () => {
    const result = fvgSeries([]);
    expect(result).toEqual([]);
  });

  it("marks bullish FVG at the impulse candle index", () => {
    const result = fvgSeries(bullishFvgFixture);
    expect(result[0]).toBeNull(); // warm-up
    expect(result[1]).toBe(1);    // bullish FVG at index 1
    expect(result[2]).toBe(0);
    expect(result[3]).toBe(0);
  });

  it("marks bearish FVG at the impulse candle index", () => {
    const result = fvgSeries(bearishFvgFixture);
    expect(result[1]).toBe(-1); // bearish FVG at index 1
  });

  it("returns all zeros (no null) for data with no FVGs", () => {
    const result = fvgSeries(noFvgFixture);
    // First 2 are null (warm-up), rest are 0
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBe(0);
    expect(result[3]).toBe(0);
  });

  it("same length as input candles", () => {
    expect(fvgSeries(bullishFvgFixture).length).toBe(bullishFvgFixture.length);
  });
});

// ── Sweep Series ────────────────────────────────────────────────────────────

describe("sweepSeries", () => {
  it("returns all null for insufficient data", () => {
    const result = sweepSeries(flatMarketFixture, { swingLen: 2 });
    // 5 candles, needs 2*2+2=6 → all null
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("marks bullish sweep", () => {
    const result = sweepSeries(bullishSweepFixture, { swingLen: 2 });
    expect(result[5]).toBe(1); // bullish sweep at bar 5
  });

  it("marks bearish sweep", () => {
    const result = sweepSeries(bearishSweepFixture, { swingLen: 2 });
    expect(result[5]).toBe(-1); // bearish sweep at bar 5
  });

  it("same length as input candles", () => {
    expect(sweepSeries(bullishSweepFixture, { swingLen: 2 }).length).toBe(bullishSweepFixture.length);
  });
});

// ── Order Block Series ──────────────────────────────────────────────────────

describe("orderBlockSeries", () => {
  it("returns all null for insufficient data", () => {
    const result = orderBlockSeries(flatMarketFixture);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("marks bullish order block", () => {
    const candles = makeBullishObFixture();
    const result = orderBlockSeries(candles);
    // OB should be at bar 15 (the bearish candle before impulse)
    const obBars = result.map((v, i) => [i, v]).filter(([, v]) => v === 1);
    expect(obBars.length).toBeGreaterThanOrEqual(1);
    expect(obBars.some(([i]) => i === 15)).toBe(true);
  });

  it("marks bearish order block", () => {
    const candles = makeBearishObFixture();
    const result = orderBlockSeries(candles);
    const obBars = result.map((v, i) => [i, v]).filter(([, v]) => v === -1);
    expect(obBars.length).toBeGreaterThanOrEqual(1);
    expect(obBars.some(([i]) => i === 15)).toBe(true);
  });

  it("same length as input candles", () => {
    expect(orderBlockSeries(makeBullishObFixture()).length).toBe(makeBullishObFixture().length);
  });
});

// ── MSS Series ──────────────────────────────────────────────────────────────

describe("mssSeries", () => {
  it("returns all null for insufficient data", () => {
    const result = mssSeries(flatMarketFixture, { swingLen: 2 });
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("marks bullish BOS as +1", () => {
    const candles = makeBosBullishFixture();
    const result = mssSeries(candles, { swingLen: 2 });
    // Bar 14 should be BOS bullish → +1
    expect(result[14]).toBe(1);
  });

  it("marks bearish CHoCH as -2", () => {
    const candles = makeChochBearishFixture();
    const result = mssSeries(candles, { swingLen: 2 });
    // Bar 14 should be CHoCH bearish → -2
    expect(result[14]).toBe(-2);
  });

  it("same length as input candles", () => {
    expect(mssSeries(makeBosBullishFixture(), { swingLen: 2 }).length).toBe(makeBosBullishFixture().length);
  });
});

// ── Cross-cutting ───────────────────────────────────────────────────────────

describe("determinism", () => {
  it("all series functions are deterministic", () => {
    expect(fvgSeries(bullishFvgFixture)).toEqual(fvgSeries(bullishFvgFixture));
    expect(sweepSeries(bullishSweepFixture, { swingLen: 2 })).toEqual(sweepSeries(bullishSweepFixture, { swingLen: 2 }));
    expect(orderBlockSeries(makeBullishObFixture())).toEqual(orderBlockSeries(makeBullishObFixture()));
    expect(mssSeries(makeBosBullishFixture(), { swingLen: 2 })).toEqual(mssSeries(makeBosBullishFixture(), { swingLen: 2 }));
  });
});
