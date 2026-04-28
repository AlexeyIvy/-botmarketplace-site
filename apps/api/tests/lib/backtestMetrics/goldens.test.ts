/**
 * 49-T4: backtestMetrics golden table.
 *
 * Locks (sharpe, profitFactor, expectancy) for the five reference
 * fixtures in `_fixtures.ts`. The numbers below are the engine's
 * authoritative output as of 49-T1..T3 — any change to a utility's
 * formula or rounding will surface here. Pair updates with the PR
 * that intentionally shifts the contract and record the reason in
 * the commit message.
 */

import { describe, it, expect } from "vitest";
import {
  sharpeRatio,
  profitFactor,
  expectancy,
} from "../../../src/lib/backtestMetrics/index.js";
import {
  EMPTY,
  SINGLE_WIN,
  MIXED_BALANCED,
  ALL_WINS,
  ALL_LOSSES,
  ALL_FIXTURES,
} from "./_fixtures.js";
import { legacyComputeSharpe } from "./_legacySharpe.js";

interface GoldenRow {
  name: string;
  sharpe: number | null;
  profitFactor: number | null;
  expectancy: number | null;
}

const GOLDEN: GoldenRow[] = [
  { name: "EMPTY",          sharpe: null, profitFactor: null,                       expectancy: null },
  { name: "SINGLE_WIN",     sharpe: null, profitFactor: Number.POSITIVE_INFINITY,   expectancy: 3.5  },
  { name: "MIXED_BALANCED", sharpe: 4.59, profitFactor: 2,                          expectancy: 0.6  },
  { name: "ALL_WINS",       sharpe: 27.71, profitFactor: Number.POSITIVE_INFINITY,  expectancy: 1.33 },
  { name: "ALL_LOSSES",     sharpe: -24.25, profitFactor: 0,                        expectancy: -1.17 },
];

describe("49-T4: backtestMetrics golden table", () => {
  it("matches locked (sharpe, profitFactor, expectancy) for every fixture", () => {
    const observed: GoldenRow[] = (Object.keys(ALL_FIXTURES) as (keyof typeof ALL_FIXTURES)[])
      .map((name) => {
        const fx = ALL_FIXTURES[name];
        return {
          name,
          sharpe: sharpeRatio(fx),
          profitFactor: profitFactor(fx),
          expectancy: expectancy(fx),
        };
      });
    expect(observed).toEqual(GOLDEN);
  });

  // ---------------------------------------------------------------------
  // Bit-for-bit regression vs the archived legacy implementation.
  // ---------------------------------------------------------------------

  it("sharpeRatio is bit-for-bit identical to legacyComputeSharpe on every fixture", () => {
    for (const fx of [EMPTY, SINGLE_WIN, MIXED_BALANCED, ALL_WINS, ALL_LOSSES]) {
      expect(sharpeRatio(fx)).toBe(legacyComputeSharpe(fx));
    }
  });

  // ---------------------------------------------------------------------
  // Per-utility hand-calc anchors (independent of the table for clearer
  // diagnosis when a single utility regresses).
  // ---------------------------------------------------------------------

  it("MIXED_BALANCED hand-calc anchor", () => {
    // sharpe: mean=0.6, var=4.3, stdDev≈2.0736, mean/stdDev≈0.28934,
    //         *sqrt(252)≈4.5933 → round 2dp → 4.59
    expect(sharpeRatio(MIXED_BALANCED)).toBe(4.59);
    // profitFactor: gross=6 / loss=3 = 2
    expect(profitFactor(MIXED_BALANCED)).toBe(2);
    // expectancy: 0.6*2 - 0.4*1.5 = 0.6
    expect(expectancy(MIXED_BALANCED)).toBe(0.6);
  });

  it("SINGLE_WIN edge anchor: sharpe null, pf +Infinity, expectancy preserved", () => {
    expect(sharpeRatio(SINGLE_WIN)).toBeNull();
    expect(profitFactor(SINGLE_WIN)).toBe(Number.POSITIVE_INFINITY);
    expect(expectancy(SINGLE_WIN)).toBe(3.5);
  });
});
