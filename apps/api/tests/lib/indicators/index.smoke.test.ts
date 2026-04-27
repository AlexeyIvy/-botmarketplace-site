import { describe, it, expect } from "vitest";
import {
  calcSMA,
  calcEMA,
  calcRSI,
  calcBollingerBands,
  calcATR,
  trueRange,
  calcVWAP,
  calcADX,
  calcSuperTrend,
  calcMACD,
  type Candle,
  type BollingerBandsResult,
  type ADXResult,
  type SuperTrendResult,
  type MACDResult,
} from "../../../src/lib/indicators/index.js";

describe("indicators public API (45-T4 smoke)", () => {
  it("re-exports all base indicator functions through indicators/index.ts", () => {
    expect(typeof calcSMA).toBe("function");
    expect(typeof calcEMA).toBe("function");
    expect(typeof calcRSI).toBe("function");
    expect(typeof calcBollingerBands).toBe("function");
    expect(typeof calcATR).toBe("function");
    expect(typeof trueRange).toBe("function");
    expect(typeof calcVWAP).toBe("function");
    expect(typeof calcADX).toBe("function");
    expect(typeof calcSuperTrend).toBe("function");
    expect(typeof calcMACD).toBe("function");
  });

  it("re-exports all base indicator types through indicators/index.ts", () => {
    // Compile-time check — types must resolve. Construct values to exercise them.
    const candle: Candle = {
      openTime: 1_700_000_000_000,
      open: 100,
      high: 101,
      low: 99,
      close: 100,
      volume: 1000,
    };
    const bb: BollingerBandsResult = { upper: [], middle: [], lower: [] };
    const adx: ADXResult = { adx: [], plusDI: [], minusDI: [] };
    const st: SuperTrendResult = { supertrend: [], direction: [] };
    const macd: MACDResult = { macd: [], signal: [], histogram: [] };

    expect(candle.close).toBe(100);
    expect(bb.upper).toEqual([]);
    expect(adx.adx).toEqual([]);
    expect(st.supertrend).toEqual([]);
    expect(macd.macd).toEqual([]);
  });

  it("indicator functions return same-length arrays from a shared candle input", () => {
    const candles: Candle[] = Array.from({ length: 30 }, (_, i) => ({
      openTime: 1_700_000_000_000 + i * 60_000,
      open: 100 + i,
      high: 101 + i,
      low: 99 + i,
      close: 100 + i,
      volume: 1000,
    }));

    expect(calcSMA(candles, 14)).toHaveLength(30);
    expect(calcEMA(candles, 14)).toHaveLength(30);
    expect(calcRSI(candles, 14)).toHaveLength(30);
    expect(calcATR(candles, 14)).toHaveLength(30);
    expect(calcVWAP(candles)).toHaveLength(30);
    expect(trueRange(candles)).toHaveLength(30);

    const bb = calcBollingerBands(candles, 20, 2);
    expect(bb.upper).toHaveLength(30);
    expect(bb.middle).toHaveLength(30);
    expect(bb.lower).toHaveLength(30);

    const adx = calcADX(candles, 14);
    expect(adx.adx).toHaveLength(30);

    const st = calcSuperTrend(candles, 10, 3);
    expect(st.supertrend).toHaveLength(30);

    const macd = calcMACD(candles, 12, 26, 9);
    expect(macd.macd).toHaveLength(30);
  });
});
