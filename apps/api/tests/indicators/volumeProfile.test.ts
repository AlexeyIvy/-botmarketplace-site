import { describe, it, expect } from "vitest";
import { calcVolumeProfile, type VolumeProfileCandle } from "../../src/lib/indicators/volumeProfile.js";

function makeCandles(n: number, basePrice = 100, spread = 2): VolumeProfileCandle[] {
  return Array.from({ length: n }, (_, i) => ({
    high: basePrice + spread / 2 + (i % 3) * 0.5,
    low: basePrice - spread / 2 - (i % 3) * 0.5,
    close: basePrice + (i % 2 === 0 ? 0.5 : -0.5),
    volume: 1000 + i * 10,
  }));
}

describe("calcVolumeProfile", () => {
  it("returns null arrays for insufficient data", () => {
    const candles = makeCandles(5);
    const result = calcVolumeProfile(candles, 20);
    expect(result.poc.every(v => v === null)).toBe(true);
    expect(result.vah.every(v => v === null)).toBe(true);
    expect(result.val.every(v => v === null)).toBe(true);
  });

  it("computes POC, VAH, VAL after warm-up period", () => {
    const candles = makeCandles(30);
    const result = calcVolumeProfile(candles, 20);

    // First 19 bars are null (warm-up)
    for (let i = 0; i < 19; i++) {
      expect(result.poc[i]).toBeNull();
    }
    // Bar 19+ should have values
    expect(result.poc[19]).not.toBeNull();
    expect(result.vah[19]).not.toBeNull();
    expect(result.val[19]).not.toBeNull();
  });

  it("POC is within the price range", () => {
    const candles = makeCandles(30, 100, 4);
    const result = calcVolumeProfile(candles, 20);

    for (let i = 19; i < 30; i++) {
      expect(result.poc[i]).toBeGreaterThanOrEqual(96);
      expect(result.poc[i]).toBeLessThanOrEqual(104);
    }
  });

  it("VAL <= POC <= VAH", () => {
    const candles = makeCandles(30, 100, 4);
    const result = calcVolumeProfile(candles, 20);

    for (let i = 19; i < 30; i++) {
      expect(result.val[i]!).toBeLessThanOrEqual(result.poc[i]!);
      expect(result.poc[i]!).toBeLessThanOrEqual(result.vah[i]!);
    }
  });

  it("VAH >= VAL (value area has positive width)", () => {
    const candles = makeCandles(30, 100, 4);
    const result = calcVolumeProfile(candles, 20);

    for (let i = 19; i < 30; i++) {
      expect(result.vah[i]!).toBeGreaterThanOrEqual(result.val[i]!);
    }
  });

  it("handles flat market (all same price)", () => {
    const candles: VolumeProfileCandle[] = Array.from({ length: 25 }, () => ({
      high: 100, low: 100, close: 100, volume: 1000,
    }));
    const result = calcVolumeProfile(candles, 20);
    // Flat → POC = VAH = VAL = close
    expect(result.poc[19]).toBe(100);
    expect(result.vah[19]).toBe(100);
    expect(result.val[19]).toBe(100);
  });

  it("is deterministic", () => {
    const candles = makeCandles(30);
    const a = calcVolumeProfile(candles, 20);
    const b = calcVolumeProfile(candles, 20);
    expect(a.poc).toEqual(b.poc);
    expect(a.vah).toEqual(b.vah);
    expect(a.val).toEqual(b.val);
  });

  it("higher volume at specific price pushes POC there", () => {
    // Create candles where most volume is at high prices
    const candles: VolumeProfileCandle[] = Array.from({ length: 25 }, (_, i) => ({
      high: i < 20 ? 105 : 110,
      low: i < 20 ? 100 : 108,
      close: i < 20 ? 102 : 109,
      volume: i < 20 ? 100 : 10000, // huge volume at high prices for last 5 bars
    }));
    const result = calcVolumeProfile(candles, 25, 24);
    // POC should be pulled toward the high-volume zone
    expect(result.poc[24]).not.toBeNull();
    expect(result.poc[24]!).toBeGreaterThan(105);
  });
});
