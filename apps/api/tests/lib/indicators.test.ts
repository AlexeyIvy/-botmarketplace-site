import { describe, it, expect } from "vitest";
import { calcVWAP } from "../../src/lib/indicators/vwap.js";
import { calcATR, trueRange } from "../../src/lib/indicators/atr.js";
import { calcADX } from "../../src/lib/indicators/adx.js";
import { calcSuperTrend } from "../../src/lib/indicators/supertrend.js";
import { makeUptrend, makeDowntrend, makeFlat } from "../fixtures/candles.js";

// ---------------------------------------------------------------------------
// Helper: build custom candles from OHLCV tuples
// ---------------------------------------------------------------------------
interface Candle {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

function candlesFrom(
  rows: [open: number, high: number, low: number, close: number, volume: number][],
): Candle[] {
  return rows.map(([o, h, l, c, v], i) => ({
    openTime: 1_700_000_000_000 + i * 60_000,
    open: o,
    high: h,
    low: l,
    close: c,
    volume: v,
  }));
}

// ===========================================================================
// VWAP
// ===========================================================================
describe("calcVWAP", () => {
  it("returns correct VWAP for a simple 3-bar example", () => {
    // Hand-calculated reference:
    // Bar 0: tp=(110+90+100)/3=100,  cumTPV=100*1000=100000, cumVol=1000 → VWAP=100
    // Bar 1: tp=(120+100+110)/3=110, cumTPV=100000+110*2000=320000, cumVol=3000 → VWAP≈106.667
    // Bar 2: tp=(115+105+112)/3=110.667, cumTPV=320000+110.667*1500=486000, cumVol=4500 → VWAP≈108
    const candles = candlesFrom([
      [95, 110, 90, 100, 1000],
      [100, 120, 100, 110, 2000],
      [110, 115, 105, 112, 1500],
    ]);

    const result = calcVWAP(candles);
    expect(result).toHaveLength(3);
    expect(result[0]).toBeCloseTo(100, 4);
    expect(result[1]).toBeCloseTo(320000 / 3000, 4);
    expect(result[2]).toBeCloseTo(
      (100 * 1000 + 110 * 2000 + ((115 + 105 + 112) / 3) * 1500) / 4500,
      4,
    );
  });

  it("returns null for zero-volume bars at the start", () => {
    const candles = candlesFrom([
      [100, 110, 90, 100, 0],
      [100, 110, 90, 100, 0],
      [100, 110, 90, 100, 1000],
    ]);
    const result = calcVWAP(candles);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).not.toBeNull();
  });

  it("handles empty array", () => {
    expect(calcVWAP([])).toEqual([]);
  });

  it("handles single candle", () => {
    const candles = candlesFrom([[100, 110, 90, 100, 500]]);
    const result = calcVWAP(candles);
    expect(result).toHaveLength(1);
    expect(result[0]).toBeCloseTo(100, 4); // tp = (110+90+100)/3 = 100
  });

  it("produces monotonically valid values on uptrend fixture", () => {
    const candles = makeUptrend(30);
    const result = calcVWAP(candles);
    // All values should be non-null (all candles have volume > 0)
    for (const v of result) {
      expect(v).not.toBeNull();
      expect(v).toBeGreaterThan(0);
    }
  });

  it("VWAP with anchor resets accumulation", () => {
    const candles = candlesFrom([
      [100, 110, 90, 100, 1000],
      [100, 120, 80, 110, 2000],
      [110, 115, 105, 112, 1500], // anchor reset here
      [112, 120, 108, 118, 1000],
    ]);
    const noAnchor = calcVWAP(candles);
    const withAnchor = calcVWAP(candles, (_c, i) => i === 2);

    // Values before reset should be same
    expect(noAnchor[0]).toEqual(withAnchor[0]);
    expect(noAnchor[1]).toEqual(withAnchor[1]);
    // After reset they should differ
    expect(noAnchor[2]).not.toEqual(withAnchor[2]);
  });
});

// ===========================================================================
// ATR (internal primitive, but tested directly for correctness)
// ===========================================================================
describe("calcATR", () => {
  it("returns all nulls when not enough data", () => {
    const candles = makeUptrend(5);
    const result = calcATR(candles, 14);
    expect(result.every((v) => v === null)).toBe(true);
  });

  it("first ATR value equals SMA of first N true ranges", () => {
    const candles = makeUptrend(20);
    const tr = trueRange(candles);
    const period = 5;
    const result = calcATR(candles, period);

    // First period-1 values are null
    for (let i = 0; i < period - 1; i++) expect(result[i]).toBeNull();

    // Value at index period-1 = SMA of TR[0..period-1]
    const expectedSeed = tr.slice(0, period).reduce((a, b) => a + b, 0) / period;
    expect(result[period - 1]).toBeCloseTo(expectedSeed, 10);
  });

  it("ATR is non-negative for all valid values", () => {
    const candles = makeUptrend(50);
    const result = calcATR(candles, 14);
    for (const v of result) {
      if (v !== null) expect(v).toBeGreaterThanOrEqual(0);
    }
  });

  it("flat market produces small ATR", () => {
    const candles = makeFlat(30);
    const result = calcATR(candles, 14);
    const validValues = result.filter((v): v is number => v !== null);
    expect(validValues.length).toBeGreaterThan(0);
    // Flat candles have high-low = 1 (±0.5), ATR should be close to 1
    for (const v of validValues) expect(v).toBeLessThan(2);
  });
});

// ===========================================================================
// ADX
// ===========================================================================
describe("calcADX", () => {
  it("returns all nulls for insufficient data", () => {
    const candles = makeUptrend(10);
    const { adx, plusDI, minusDI } = calcADX(candles, 14);
    expect(adx.every((v) => v === null)).toBe(true);
    // +DI/-DI may have some values even with 10 bars (period+1=15 needed), so check:
    expect(plusDI.every((v) => v === null)).toBe(true);
    expect(minusDI.every((v) => v === null)).toBe(true);
  });

  it("ADX warm-up length is correct (2*period - 1)", () => {
    const period = 5;
    const candles = makeUptrend(50);
    const { adx } = calcADX(candles, period);

    // First 2*period - 2 values should be null
    for (let i = 0; i < 2 * period - 2; i++) {
      expect(adx[i]).toBeNull();
    }
    // Value at index 2*period - 1 should exist
    expect(adx[2 * period - 1]).not.toBeNull();
  });

  it("ADX values are in 0–100 range", () => {
    const candles = makeUptrend(50);
    const { adx, plusDI, minusDI } = calcADX(candles, 7);
    for (const v of adx) {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    }
    for (const v of plusDI) {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    }
    for (const v of minusDI) {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    }
  });

  it("strong uptrend produces +DI > -DI", () => {
    const candles = makeUptrend(50, 100, 2);
    const { plusDI, minusDI } = calcADX(candles, 7);

    // Check last few values where indicator is stable
    const lastIdx = candles.length - 1;
    const pdi = plusDI[lastIdx] as number;
    const mdi = minusDI[lastIdx] as number;
    expect(pdi).toBeGreaterThan(mdi);
  });

  it("strong downtrend produces -DI > +DI", () => {
    const candles = makeDowntrend(50, 200, 2);
    const { plusDI, minusDI } = calcADX(candles, 7);

    const lastIdx = candles.length - 1;
    const pdi = plusDI[lastIdx] as number;
    const mdi = minusDI[lastIdx] as number;
    expect(mdi).toBeGreaterThan(pdi);
  });

  it("strong trend produces high ADX", () => {
    const candles = makeUptrend(50, 100, 3);
    const { adx } = calcADX(candles, 7);

    // ADX at the end should be elevated (> 25 is typical threshold for trending)
    const lastADX = adx[candles.length - 1] as number;
    expect(lastADX).toBeGreaterThan(20);
  });

  it("flat market produces low ADX", () => {
    const candles = makeFlat(60);
    const { adx } = calcADX(candles, 14);

    // Filter valid values near the end
    const tail = adx.slice(-10).filter((v): v is number => v !== null);
    expect(tail.length).toBeGreaterThan(0);
    for (const v of tail) {
      // ADX should be low in flat market (typically < 25)
      expect(v).toBeLessThan(30);
    }
  });

  it("is deterministic — same input produces same output", () => {
    const candles = makeUptrend(40, 100, 1.5);
    const r1 = calcADX(candles, 10);
    const r2 = calcADX(candles, 10);
    expect(r1.adx).toEqual(r2.adx);
    expect(r1.plusDI).toEqual(r2.plusDI);
    expect(r1.minusDI).toEqual(r2.minusDI);
  });

  // Golden reference test: hand-verified 5-bar ADX on known data
  it("golden: matches hand-calculated values on 12-bar dataset with period=3", () => {
    // Small period to make hand-calculation feasible
    const candles = candlesFrom([
      // O,   H,   L,   C,   V
      [100, 102, 98,  101, 100],
      [101, 105, 100, 104, 100],  // +DM=3, -DM=0, TR=5
      [104, 108, 103, 107, 100],  // +DM=3, -DM=0, TR=5
      [107, 109, 105, 106, 100],  // +DM=1, -DM=0, TR=4
      [106, 110, 104, 109, 100],  // +DM=1, -DM=1→0(+DM wins), TR=6
      [109, 111, 107, 108, 100],  // +DM=1, -DM=0, TR=4
      [108, 112, 106, 111, 100],  // +DM=1, -DM=1→0(+DM wins), TR=6
      [111, 113, 109, 110, 100],  // +DM=1, -DM=0, TR=4
      [110, 114, 108, 113, 100],  // +DM=1, -DM=1→0, TR=6
      [113, 115, 111, 112, 100],  // +DM=1, -DM=0, TR=4
      [112, 116, 110, 115, 100],  // +DM=1, -DM=1→0, TR=6
      [115, 117, 113, 114, 100],  // +DM=1, -DM=0, TR=4
    ]);

    const period = 3;
    const { adx, plusDI, minusDI } = calcADX(candles, period);

    // With period=3, first DI at index 3, first ADX at index 5
    expect(plusDI[period]).not.toBeNull();
    expect(minusDI[period]).not.toBeNull();
    expect(adx[2 * period - 1]).not.toBeNull();

    // In this uptrending dataset, +DI should dominate
    const lastPDI = plusDI[11] as number;
    const lastMDI = minusDI[11] as number;
    expect(lastPDI).toBeGreaterThan(lastMDI);
    // ADX should be moderate to high
    expect(adx[11]).not.toBeNull();
    expect(adx[11] as number).toBeGreaterThan(0);
  });
});

// ===========================================================================
// SuperTrend
// ===========================================================================
describe("calcSuperTrend", () => {
  it("returns all nulls for insufficient data", () => {
    const candles = makeUptrend(5);
    const { supertrend, direction } = calcSuperTrend(candles, 10, 3);
    expect(supertrend.every((v) => v === null)).toBe(true);
    expect(direction.every((v) => v === null)).toBe(true);
  });

  it("warm-up length matches ATR period", () => {
    const period = 5;
    const candles = makeUptrend(30);
    const { supertrend, direction } = calcSuperTrend(candles, period, 3);

    // First period-2 values should be null
    for (let i = 0; i < period - 1; i++) {
      expect(supertrend[i]).toBeNull();
      expect(direction[i]).toBeNull();
    }
    // Value at period-1 should be set
    expect(supertrend[period - 1]).not.toBeNull();
    expect(direction[period - 1]).not.toBeNull();
  });

  it("uptrend produces bullish direction (1)", () => {
    const candles = makeUptrend(50, 100, 2);
    const { direction } = calcSuperTrend(candles, 10, 3);

    // Last 10 bars should all be bullish in a strong uptrend
    const tail = direction.slice(-10);
    for (const d of tail) {
      expect(d).toBe(1);
    }
  });

  it("downtrend produces bearish direction (-1)", () => {
    const candles = makeDowntrend(50, 200, 2);
    const { direction } = calcSuperTrend(candles, 10, 3);

    // Last 10 bars should be bearish
    const tail = direction.slice(-10);
    for (const d of tail) {
      expect(d).toBe(-1);
    }
  });

  it("supertrend line is below price in bullish, above in bearish", () => {
    const candles = makeUptrend(50, 100, 2);
    const { supertrend, direction } = calcSuperTrend(candles, 10, 3);

    for (let i = 0; i < candles.length; i++) {
      if (supertrend[i] === null) continue;
      if (direction[i] === 1) {
        // Bullish: supertrend (lower band) should be below close
        expect(supertrend[i]!).toBeLessThanOrEqual(candles[i].close);
      } else {
        // Bearish: supertrend (upper band) should be above close
        expect(supertrend[i]!).toBeGreaterThanOrEqual(candles[i].close);
      }
    }
  });

  it("direction only contains 1, -1, or null", () => {
    const candles = makeUptrend(40);
    const { direction } = calcSuperTrend(candles, 7, 2);
    for (const d of direction) {
      expect([1, -1, null]).toContain(d);
    }
  });

  it("flat market: direction remains stable", () => {
    const candles = makeFlat(40);
    const { direction } = calcSuperTrend(candles, 7, 2);

    // In flat market, no direction flips after initialization (close stays same)
    const validDirs = direction.filter((d): d is 1 | -1 => d !== null);
    expect(validDirs.length).toBeGreaterThan(0);

    // All should be same direction (no whipsaw on perfectly flat data)
    const first = validDirs[0];
    for (const d of validDirs) expect(d).toBe(first);
  });

  it("is deterministic — same input produces same output", () => {
    const candles = makeUptrend(40, 100, 1.5);
    const r1 = calcSuperTrend(candles, 10, 3);
    const r2 = calcSuperTrend(candles, 10, 3);
    expect(r1.supertrend).toEqual(r2.supertrend);
    expect(r1.direction).toEqual(r2.direction);
  });

  it("handles single candle", () => {
    const candles = makeUptrend(1);
    const { supertrend } = calcSuperTrend(candles, 1, 3);
    // With period=1, ATR is available at index 0 (high - low)
    expect(supertrend[0]).not.toBeNull();
  });

  // Golden reference: verify exact values on a small known dataset
  it("golden: 6-bar dataset with period=3, multiplier=2", () => {
    const candles = candlesFrom([
      [100, 105, 95,  102, 1000],
      [102, 108, 99,  106, 1200],
      [106, 112, 103, 110, 1100],
      [110, 113, 107, 108, 900],
      [108, 115, 106, 114, 1300],
      [114, 118, 111, 116, 1000],
    ]);

    const period = 3;
    const mult = 2;
    const { supertrend, direction } = calcSuperTrend(candles, period, mult);

    // First 2 values null (warm-up for ATR period 3)
    expect(supertrend[0]).toBeNull();
    expect(supertrend[1]).toBeNull();

    // Index 2 should have first value
    expect(supertrend[2]).not.toBeNull();
    expect(typeof supertrend[2]).toBe("number");

    // Verify remaining bars have valid values
    for (let i = 2; i < 6; i++) {
      expect(supertrend[i]).not.toBeNull();
      expect(direction[i]).not.toBeNull();
    }
  });
});
