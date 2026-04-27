import { describe, it, expect } from "vitest";
import { calcRSI } from "../../../src/lib/indicators/rsi.js";
import { makeUptrend, makeDowntrend, makeFlat } from "../../fixtures/candles.js";

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

describe("calcRSI", () => {
  it("returns null for warm-up bars (i < length) and value from index `length` onward", () => {
    const candles = candlesFromCloses([10, 11, 9, 12, 13, 11]);
    const result = calcRSI(candles, 3);

    expect(result).toHaveLength(6);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeNull();
    expect(result[3]).not.toBeNull();
  });

  it("returns all-null when n < length + 1", () => {
    // length=5 needs ≥ 6 candles (5 changes); 5 candles produce only 4 changes.
    const candles = candlesFromCloses([1, 2, 3, 4, 5]);
    const result = calcRSI(candles, 5);
    expect(result).toHaveLength(5);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("matches hand-calculated reference (length=2, closes=[10, 12, 11, 14])", () => {
    // Step-by-step:
    //   diffs:  +2 (gain), -1 (loss), +3 (gain)
    //   seed (i=1..2): gainSum=2, lossSum=1 → avgGain=1, avgLoss=0.5
    //   RSI[2] = 100 - 100/(1 + 1/0.5) = 100 - 100/3 = 66.6667
    //
    //   step i=3: gain=3, loss=0
    //     avgGain = (1*(2-1) + 3)/2 = 2
    //     avgLoss = (0.5*(2-1) + 0)/2 = 0.25
    //     RSI[3] = 100 - 100/(1 + 2/0.25) = 100 - 100/9 = 88.8889
    const candles = candlesFromCloses([10, 12, 11, 14]);
    const result = calcRSI(candles, 2);

    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeCloseTo(100 - 100 / 3, 8);
    expect(result[3]).toBeCloseTo(100 - 100 / 9, 8);
  });

  it("returns 100 for a monotonic uptrend (avgLoss = 0 branch)", () => {
    const candles = makeUptrend(30, 100, 1);
    const result = calcRSI(candles, 14);

    expect(result[13]).toBeNull();
    expect(result[14]).toBe(100);
    expect(result[result.length - 1]).toBe(100);
  });

  it("returns 0 for a monotonic downtrend (avgGain = 0 → RS = 0)", () => {
    const candles = makeDowntrend(30, 200, 1);
    const result = calcRSI(candles, 14);

    expect(result[13]).toBeNull();
    expect(result[14]).toBe(0);
    expect(result[result.length - 1]).toBe(0);
  });

  it("returns 100 for a flat series (both sums zero — avgLoss = 0 branch)", () => {
    const candles = makeFlat(20, 100);
    const result = calcRSI(candles, 14);

    expect(result[14]).toBe(100);
    expect(result[19]).toBe(100);
  });

  it("recovers from oversold towards mid-range as gains arrive", () => {
    // 14 down moves of -1, then 7 up moves of +1.
    // After the seed window: avgGain=0, avgLoss=1, RSI=0.
    // Subsequent up moves push RSI upward.
    const closes = [
      ...Array.from({ length: 15 }, (_, i) => 100 - i), // 100..86 (14 losses)
      ...Array.from({ length: 7 }, (_, i) => 86 + (i + 1)), // 87..93 (7 gains)
    ];
    const candles = candlesFromCloses(closes);
    const result = calcRSI(candles, 14);

    expect(result[14]).toBe(0);
    const last = result[result.length - 1];
    expect(last).not.toBeNull();
    expect(last as number).toBeGreaterThan(0);
    expect(last as number).toBeLessThan(100);
  });

  it("returns array of same length as input", () => {
    const candles = candlesFromCloses([1, 2, 3, 4, 5, 6, 7, 8]);
    expect(calcRSI(candles, 3)).toHaveLength(8);
  });

  it("handles empty array", () => {
    expect(calcRSI([], 14)).toEqual([]);
  });
});
