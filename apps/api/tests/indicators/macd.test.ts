import { describe, it, expect } from "vitest";
import { calcMACD } from "../../src/lib/indicators/macd.js";
import { makeUptrend, makeDowntrend } from "../fixtures/candles.js";
import { getIndicatorValues, createIndicatorCache } from "../../src/lib/dslEvaluator.js";

// ---------------------------------------------------------------------------
// calcMACD unit tests
// ---------------------------------------------------------------------------

describe("calcMACD", () => {
  it("returns all nulls for candles shorter than slowPeriod", () => {
    const candles = makeUptrend(10, 100, 1);
    const result = calcMACD(candles, 12, 26, 9);
    expect(result.macd.every((v) => v === null)).toBe(true);
    expect(result.signal.every((v) => v === null)).toBe(true);
    expect(result.histogram.every((v) => v === null)).toBe(true);
  });

  it("result arrays have same length as input", () => {
    const candles = makeUptrend(60, 100, 1);
    const result = calcMACD(candles);
    expect(result.macd.length).toBe(60);
    expect(result.signal.length).toBe(60);
    expect(result.histogram.length).toBe(60);
  });

  it("MACD line is non-null from slowPeriod-1 onward", () => {
    const candles = makeUptrend(60, 100, 1);
    const result = calcMACD(candles, 12, 26, 9);
    // First 25 bars should be null (slowPeriod - 1 = 25)
    for (let i = 0; i < 25; i++) {
      expect(result.macd[i]).toBeNull();
    }
    // From bar 25 onward, MACD should be a number
    for (let i = 25; i < 60; i++) {
      expect(result.macd[i]).toBeTypeOf("number");
    }
  });

  it("signal line starts after slowPeriod + signalPeriod - 2", () => {
    const candles = makeUptrend(60, 100, 1);
    const result = calcMACD(candles, 12, 26, 9);
    // Signal starts at bar 25 + 9 - 1 = 33
    expect(result.signal[33]).toBeTypeOf("number");
    expect(result.signal[32]).toBeNull();
  });

  it("histogram = macd - signal where both are non-null", () => {
    const candles = makeUptrend(60, 100, 1);
    const result = calcMACD(candles, 12, 26, 9);
    for (let i = 33; i < 60; i++) {
      expect(result.histogram[i]).toBeCloseTo(result.macd[i]! - result.signal[i]!, 10);
    }
  });

  it("uptrend MACD line is positive", () => {
    // Use steeper trend so fast EMA diverges from slow EMA
    const candles = makeUptrend(80, 100, 5);
    const result = calcMACD(candles, 12, 26, 9);
    // MACD line (fast - slow) should be positive in strong uptrend
    const lastMacd = result.macd[79];
    expect(lastMacd).toBeTypeOf("number");
    expect(lastMacd!).toBeGreaterThan(0);
  });

  it("downtrend MACD line is negative", () => {
    const candles = makeDowntrend(80, 500, 5);
    const result = calcMACD(candles, 12, 26, 9);
    const lastMacd = result.macd[79];
    expect(lastMacd).toBeTypeOf("number");
    expect(lastMacd!).toBeLessThan(0);
  });
});

// ---------------------------------------------------------------------------
// getIndicatorValues integration: macd, macd_signal, volume
// ---------------------------------------------------------------------------

describe("getIndicatorValues – macd and volume", () => {
  const candles = makeUptrend(60, 100, 1);
  const cache = createIndicatorCache();

  it("type 'macd' returns histogram series", () => {
    const vals = getIndicatorValues("macd", {}, candles, cache);
    expect(vals.length).toBe(60);
    // Should have non-null values after warm-up
    const nonNull = vals.filter((v) => v !== null);
    expect(nonNull.length).toBeGreaterThan(0);
  });

  it("type 'macd_signal' returns signal line", () => {
    const vals = getIndicatorValues("macd_signal", {}, candles, cache);
    expect(vals.length).toBe(60);
    const nonNull = vals.filter((v) => v !== null);
    expect(nonNull.length).toBeGreaterThan(0);
  });

  it("type 'macd_histogram' returns histogram", () => {
    const vals = getIndicatorValues("macd_histogram", {}, candles, cache);
    expect(vals.length).toBe(60);
    // Should match the "macd" type result
    const macdVals = getIndicatorValues("macd", {}, candles, cache);
    expect(vals).toEqual(macdVals);
  });

  it("custom MACD periods are respected", () => {
    const cache2 = createIndicatorCache();
    const vals = getIndicatorValues("macd", { fastPeriod: 8, slowPeriod: 17, signalPeriod: 5 }, candles, cache2);
    expect(vals.length).toBe(60);
    // With shorter slow period (17), warm-up is shorter — more non-null values
    const nonNull = vals.filter((v) => v !== null);
    expect(nonNull.length).toBeGreaterThan(30);
  });

  it("type 'volume' returns volume series with length === candles.length", () => {
    const vals = getIndicatorValues("volume", {}, candles, cache);
    expect(vals.length).toBe(candles.length);
    // All values should be non-null (volume is always present)
    expect(vals.every((v) => v !== null)).toBe(true);
  });

  it("volume values match candle volumes", () => {
    const vals = getIndicatorValues("volume", {}, candles, cache);
    for (let i = 0; i < candles.length; i++) {
      expect(vals[i]).toBe(candles[i].volume);
    }
  });
});
