import { describe, it, expect } from "vitest";
import { applyDslSweepParam } from "../../src/lib/dslSweepParam.js";

describe("applyDslSweepParam", () => {
  it("patches the matching nodeId block with the new param value", () => {
    const dsl = {
      entry: {
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", nodeId: "n2", length: 10 },
          slow: { blockType: "SMA", nodeId: "n3", length: 20 },
        },
        indicators: [
          { type: "SMA", nodeId: "n2", length: 10 },
          { type: "SMA", nodeId: "n3", length: 20 },
        ],
      },
    };

    const result = applyDslSweepParam(dsl, "n2", "length", 15);

    // Both occurrences of nodeId "n2" should be patched
    const entry = result.entry as Record<string, unknown>;
    const signal = entry.signal as Record<string, unknown>;
    const fast = signal.fast as Record<string, unknown>;
    expect(fast.length).toBe(15);
    expect(fast.nodeId).toBe("n2");

    const indicators = entry.indicators as Record<string, unknown>[];
    expect(indicators[0].length).toBe(15);

    // nodeId "n3" should remain unchanged
    const slow = signal.slow as Record<string, unknown>;
    expect(slow.length).toBe(20);
    expect(indicators[1].length).toBe(20);
  });

  it("does not mutate the original DSL object", () => {
    const dsl = {
      entry: {
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", nodeId: "n2", length: 10 },
        },
      },
    };

    applyDslSweepParam(dsl, "n2", "length", 99);

    // Original should be untouched
    expect(dsl.entry.signal.fast.length).toBe(10);
  });

  it("returns unmodified clone when blockId does not match", () => {
    const dsl = {
      entry: {
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", nodeId: "n2", length: 10 },
        },
      },
    };

    const result = applyDslSweepParam(dsl, "nonexistent", "length", 99);

    const entry = result.entry as Record<string, unknown>;
    const signal = entry.signal as Record<string, unknown>;
    const fast = signal.fast as Record<string, unknown>;
    expect(fast.length).toBe(10);
  });

  it("patches nested exit block parameters", () => {
    const dsl = {
      entry: { side: "Buy" },
      exit: {
        stopLoss: { type: "atr_multiple", value: 2, atrPeriod: 14, nodeId: "n5" },
        takeProfit: { type: "fixed_pct", value: 4, nodeId: "n6" },
      },
    };

    const result = applyDslSweepParam(dsl, "n5", "value", 3);

    const exit = result.exit as Record<string, unknown>;
    const sl = exit.stopLoss as Record<string, unknown>;
    expect(sl.value).toBe(3);

    const tp = exit.takeProfit as Record<string, unknown>;
    expect(tp.value).toBe(4); // unchanged
  });

  it("works with different param names (period, multiplier)", () => {
    const dsl = {
      entry: {
        indicators: [
          { type: "supertrend", nodeId: "n7", atrPeriod: 10, multiplier: 3 },
        ],
      },
    };

    const result = applyDslSweepParam(dsl, "n7", "multiplier", 2.5);

    const entry = result.entry as Record<string, unknown>;
    const indicators = entry.indicators as Record<string, unknown>[];
    expect(indicators[0].multiplier).toBe(2.5);
    expect(indicators[0].atrPeriod).toBe(10); // unchanged
  });
});
