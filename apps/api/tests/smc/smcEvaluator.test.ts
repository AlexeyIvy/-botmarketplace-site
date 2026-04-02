/**
 * SMC Evaluator Integration Tests
 *
 * Verifies that SMC pattern blocks resolve correctly through the DSL evaluator
 * (getIndicatorValues → patternEngine → pattern detectors).
 */
import { describe, it, expect } from "vitest";
import {
  getIndicatorValues,
  createIndicatorCache,
} from "../../src/lib/dslEvaluator.js";
import { bullishFvgFixture, bullishSweepFixture, makeBullishObFixture, makeBosBullishFixture } from "./smcFixtures.js";

describe("getIndicatorValues — SMC patterns", () => {
  it("resolves fair_value_gap through the evaluator", () => {
    const cache = createIndicatorCache();
    const values = getIndicatorValues("fair_value_gap", { multiplier: 0 }, bullishFvgFixture, cache);
    expect(values.length).toBe(bullishFvgFixture.length);
    expect(values[1]).toBe(1); // bullish FVG at bar 1
  });

  it("resolves liquidity_sweep through the evaluator", () => {
    const cache = createIndicatorCache();
    const values = getIndicatorValues("liquidity_sweep", { length: 2, period: 50 }, bullishSweepFixture, cache);
    expect(values.length).toBe(bullishSweepFixture.length);
    expect(values[5]).toBe(1); // bullish sweep at bar 5
  });

  it("resolves order_block through the evaluator", () => {
    const candles = makeBullishObFixture();
    const cache = createIndicatorCache();
    const values = getIndicatorValues("order_block", { period: 14, multiplier: 1.5, length: 5 }, candles, cache);
    expect(values.length).toBe(candles.length);
    // Should have at least one bullish OB (+1)
    expect(values.some((v) => v === 1)).toBe(true);
  });

  it("resolves market_structure_shift through the evaluator", () => {
    const candles = makeBosBullishFixture();
    const cache = createIndicatorCache();
    const values = getIndicatorValues("market_structure_shift", { length: 2 }, candles, cache);
    expect(values.length).toBe(candles.length);
    expect(values[14]).toBe(1); // bullish BOS at bar 14
  });

  it("caches SMC pattern results on second call", () => {
    const cache = createIndicatorCache();
    const a = getIndicatorValues("fair_value_gap", { multiplier: 0 }, bullishFvgFixture, cache);
    const b = getIndicatorValues("fair_value_gap", { multiplier: 0 }, bullishFvgFixture, cache);
    // Same reference from cache
    expect(a).toBe(b);
  });

  it("different params produce different cache entries", () => {
    const cache = createIndicatorCache();
    const a = getIndicatorValues("fair_value_gap", { multiplier: 0 }, bullishFvgFixture, cache);
    const b = getIndicatorValues("fair_value_gap", { multiplier: 0.5 }, bullishFvgFixture, cache);
    // Different references (different params)
    expect(a).not.toBe(b);
  });
});
