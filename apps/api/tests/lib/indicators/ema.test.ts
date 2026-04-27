import { describe, it, expect } from "vitest";
import { calcEMA } from "../../../src/lib/indicators/ema.js";
import { makeFlat } from "../../fixtures/candles.js";

interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

function candlesFromCloses(closes: number[]): Candle[] {
  return closes.map((c, i) => ({
    openTime: 1_700_000_000_000 + i * 60_000,
    open: c,
    high: c,
    low: c,
    close: c,
    volume: 1000,
  }));
}

describe("calcEMA", () => {
  it("returns null for warm-up bars (i < length - 1)", () => {
    const candles = candlesFromCloses([1, 2, 3, 4, 5, 6, 7, 8]);
    const result = calcEMA(candles, 4);

    expect(result).toHaveLength(8);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeNull();
    expect(result[3]).not.toBeNull();
  });

  it("seeds the first value with SMA of the first `length` closes", () => {
    const closes = [10, 20, 30, 40, 50, 60];
    const candles = candlesFromCloses(closes);
    const length = 4;
    const result = calcEMA(candles, length);
    const seedSma = (10 + 20 + 30 + 40) / length;
    expect(result[length - 1]).toBeCloseTo(seedSma, 10);
  });

  it("applies smoothing factor k = 2 / (length + 1) on subsequent bars", () => {
    const closes = [10, 20, 30, 40, 50, 60];
    const candles = candlesFromCloses(closes);
    const length = 4;
    const result = calcEMA(candles, length);

    const seed = (10 + 20 + 30 + 40) / length;
    const k = 2 / (length + 1);
    const expectedAt4 = closes[4] * k + seed * (1 - k);
    const expectedAt5 = closes[5] * k + expectedAt4 * (1 - k);

    expect(result[4]).toBeCloseTo(expectedAt4, 10);
    expect(result[5]).toBeCloseTo(expectedAt5, 10);
  });

  it("returns all-null when n < length", () => {
    const candles = candlesFromCloses([1, 2, 3]);
    const result = calcEMA(candles, 5);
    expect(result).toHaveLength(3);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("equals the constant price for a flat series (no movement to converge to)", () => {
    const candles = makeFlat(20, 100);
    const result = calcEMA(candles, 5);
    expect(result[4]).toBeCloseTo(100, 10);
    expect(result[19]).toBeCloseTo(100, 10);
  });

  it("converges towards a new price level after a step change", () => {
    // First 10 bars at 100, then 90 bars at 200 — EMA should approach 200.
    const closes = [
      ...Array.from({ length: 10 }, () => 100),
      ...Array.from({ length: 90 }, () => 200),
    ];
    const candles = candlesFromCloses(closes);
    const result = calcEMA(candles, 5);
    const last = result[result.length - 1];
    expect(last).not.toBeNull();
    expect(last as number).toBeGreaterThan(199);
    expect(last as number).toBeLessThanOrEqual(200);
  });

  it("returns array of same length as input", () => {
    const candles = candlesFromCloses([1, 2, 3, 4, 5, 6, 7]);
    expect(calcEMA(candles, 3)).toHaveLength(7);
  });
});
