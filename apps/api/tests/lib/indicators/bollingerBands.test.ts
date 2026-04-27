import { describe, it, expect } from "vitest";
import { calcBollingerBands } from "../../../src/lib/indicators/bollingerBands.js";
import { makeFlat, makeUptrend } from "../../fixtures/candles.js";

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

describe("calcBollingerBands", () => {
  it("returns null for warm-up bars (i < period - 1) on all three series", () => {
    const candles = candlesFromCloses([1, 2, 3, 4, 5, 6]);
    const { upper, middle, lower } = calcBollingerBands(candles, 4, 2);

    expect(upper).toHaveLength(6);
    expect(middle).toHaveLength(6);
    expect(lower).toHaveLength(6);
    for (let i = 0; i < 3; i++) {
      expect(upper[i]).toBeNull();
      expect(middle[i]).toBeNull();
      expect(lower[i]).toBeNull();
    }
    expect(middle[3]).not.toBeNull();
  });

  it("returns all-null arrays when n < period", () => {
    const candles = candlesFromCloses([1, 2, 3]);
    const result = calcBollingerBands(candles, 5, 2);
    expect(result.upper).toHaveLength(3);
    expect(result.upper.every((v) => v === null)).toBe(true);
    expect(result.middle.every((v) => v === null)).toBe(true);
    expect(result.lower.every((v) => v === null)).toBe(true);
  });

  it("matches hand-calculated reference (period=2, mult=1, closes=[1, 3])", () => {
    // Window at i=1: [1, 3]; mean = 2;
    //   sqDiffs = [(1-2)², (3-2)²] = [1, 1]; sqSum = 2;
    //   stdDev = sqrt(2/2) = 1;
    //   upper = 2 + 1*1 = 3; lower = 2 - 1*1 = 1.
    const candles = candlesFromCloses([1, 3]);
    const { upper, middle, lower } = calcBollingerBands(candles, 2, 1);

    expect(middle[1]).toBeCloseTo(2, 10);
    expect(upper[1]).toBeCloseTo(3, 10);
    expect(lower[1]).toBeCloseTo(1, 10);
  });

  it("matches hand-calculated reference (period=4, mult=2, closes=[10, 12, 11, 13, 15])", () => {
    // i=3: window=[10,12,11,13]; mean=11.5;
    //   sqDiffs = [2.25, 0.25, 0.25, 2.25]; sqSum=5; stdDev=sqrt(5/4)=sqrt(1.25);
    //   upper=11.5+2*sqrt(1.25); lower=11.5-2*sqrt(1.25).
    // i=4: window=[12,11,13,15]; mean=12.75;
    //   sqDiffs=[0.5625, 3.0625, 0.0625, 5.0625]; sqSum=8.75; stdDev=sqrt(8.75/4)=sqrt(2.1875);
    //   upper=12.75+2*sqrt(2.1875); lower=12.75-2*sqrt(2.1875).
    const candles = candlesFromCloses([10, 12, 11, 13, 15]);
    const { upper, middle, lower } = calcBollingerBands(candles, 4, 2);

    const sd1 = Math.sqrt(1.25);
    expect(middle[3]).toBeCloseTo(11.5, 10);
    expect(upper[3]).toBeCloseTo(11.5 + 2 * sd1, 10);
    expect(lower[3]).toBeCloseTo(11.5 - 2 * sd1, 10);

    const sd2 = Math.sqrt(2.1875);
    expect(middle[4]).toBeCloseTo(12.75, 10);
    expect(upper[4]).toBeCloseTo(12.75 + 2 * sd2, 10);
    expect(lower[4]).toBeCloseTo(12.75 - 2 * sd2, 10);
  });

  it("collapses bands to middle on a flat series (stdDev = 0)", () => {
    const candles = makeFlat(20, 100);
    const { upper, middle, lower } = calcBollingerBands(candles, 5, 2);

    for (let i = 4; i < 20; i++) {
      expect(middle[i]).toBeCloseTo(100, 10);
      expect(upper[i]).toBeCloseTo(100, 10);
      expect(lower[i]).toBeCloseTo(100, 10);
    }
  });

  it("middle equals the SMA of the most recent `period` closes", () => {
    const closes = [5, 10, 15, 20, 25, 30, 35];
    const candles = candlesFromCloses(closes);
    const period = 3;
    const { middle } = calcBollingerBands(candles, period, 2);

    for (let i = period - 1; i < closes.length; i++) {
      const expected =
        closes.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
      expect(middle[i]).toBeCloseTo(expected, 10);
    }
  });

  it("keeps upper > middle > lower whenever stdDev > 0", () => {
    const candles = makeUptrend(20, 100, 1);
    const { upper, middle, lower } = calcBollingerBands(candles, 5, 2);

    for (let i = 4; i < 20; i++) {
      expect(upper[i]).not.toBeNull();
      expect(middle[i]).not.toBeNull();
      expect(lower[i]).not.toBeNull();
      expect(upper[i] as number).toBeGreaterThan(middle[i] as number);
      expect(middle[i] as number).toBeGreaterThan(lower[i] as number);
    }
  });

  it("upper / lower are symmetric around middle (mult * stdDev each side)", () => {
    const candles = candlesFromCloses([10, 15, 12, 18, 14, 20, 13, 17]);
    const { upper, middle, lower } = calcBollingerBands(candles, 4, 2.5);

    for (let i = 3; i < candles.length; i++) {
      const m = middle[i] as number;
      const u = upper[i] as number;
      const l = lower[i] as number;
      expect(u - m).toBeCloseTo(m - l, 10);
    }
  });

  it("handles empty array", () => {
    const result = calcBollingerBands([], 5, 2);
    expect(result.upper).toEqual([]);
    expect(result.middle).toEqual([]);
    expect(result.lower).toEqual([]);
  });
});
