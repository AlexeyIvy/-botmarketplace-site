import { describe, it, expect } from "vitest";
import { calcSMA } from "../../../src/lib/indicators/sma.js";
import { makeUptrend, makeFlat } from "../../fixtures/candles.js";

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

describe("calcSMA", () => {
  it("returns null for warm-up bars (i < length - 1) and SMA from length-1 onward", () => {
    const candles = candlesFromCloses([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    const result = calcSMA(candles, 4);

    expect(result).toHaveLength(10);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeNull();
    expect(result[3]).toBeCloseTo((1 + 2 + 3 + 4) / 4, 10);
    expect(result[4]).toBeCloseTo((2 + 3 + 4 + 5) / 4, 10);
    expect(result[9]).toBeCloseTo((7 + 8 + 9 + 10) / 4, 10);
  });

  it("returns last value as the average of the most recent `length` closes", () => {
    const closes = [10, 12, 14, 16, 18, 20, 22, 24];
    const candles = candlesFromCloses(closes);
    const length = 5;
    const result = calcSMA(candles, length);
    const expected =
      closes.slice(closes.length - length).reduce((a, b) => a + b, 0) / length;
    expect(result[result.length - 1]).toBeCloseTo(expected, 10);
  });

  it("returns all-null when n < length", () => {
    const candles = candlesFromCloses([1, 2, 3]);
    const result = calcSMA(candles, 5);
    expect(result).toHaveLength(3);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("equals the constant price for a flat series", () => {
    const candles = makeFlat(20, 100);
    const result = calcSMA(candles, 5);
    expect(result[4]).toBeCloseTo(100, 10);
    expect(result[19]).toBeCloseTo(100, 10);
  });

  it("matches manual SMA on a steady uptrend", () => {
    const candles = makeUptrend(10, 100, 1);
    const result = calcSMA(candles, 3);
    // closes: 100,101,102,...,109 → SMA(3) at i=2 → (100+101+102)/3
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeCloseTo(101, 10);
    expect(result[9]).toBeCloseTo((107 + 108 + 109) / 3, 10);
  });

  it("handles empty array", () => {
    expect(calcSMA([], 5)).toEqual([]);
  });
});
