import { describe, it, expect } from "vitest";
import {
  annualizeFundingRate,
  averageFundingRate,
  fundingStreak,
  buildCandidate,
  scanFundingCandidates,
} from "../../src/lib/funding/scanner.js";
import type { FundingSnapshot, SpreadSnapshot } from "../../src/lib/funding/types.js";

// ── Helpers ─────────────────────────────────────────────────────────────────

const T0 = 1_700_000_000_000;
const H8 = 8 * 60 * 60 * 1000; // 8 hours

function makeSnapshots(rates: number[], symbol = "BTCUSDT"): FundingSnapshot[] {
  return rates.map((rate, i) => ({
    symbol,
    fundingRate: rate,
    nextFundingAt: T0 + (i + 1) * H8,
    timestamp: T0 + i * H8,
  }));
}

function makeSpread(symbol: string, spotPrice: number, perpPrice: number): SpreadSnapshot {
  return {
    symbol,
    spotPrice,
    perpPrice,
    basisBps: ((perpPrice - spotPrice) / spotPrice) * 10_000,
    timestamp: T0,
  };
}

// ── annualizeFundingRate ────────────────────────────────────────────────────

describe("annualizeFundingRate", () => {
  it("annualizes a 0.01% rate (Bybit 8h settlement)", () => {
    // 0.0001 * 365 * 3 * 100 = 10.95%
    expect(annualizeFundingRate(0.0001)).toBeCloseTo(10.95, 1);
  });

  it("returns 0 for zero rate", () => {
    expect(annualizeFundingRate(0)).toBe(0);
  });

  it("handles negative rates", () => {
    expect(annualizeFundingRate(-0.0001)).toBeCloseTo(-10.95, 1);
  });

  it("is deterministic", () => {
    expect(annualizeFundingRate(0.0005)).toBe(annualizeFundingRate(0.0005));
  });
});

// ── averageFundingRate ──────────────────────────────────────────────────────

describe("averageFundingRate", () => {
  it("returns 0 for empty array", () => {
    expect(averageFundingRate([])).toBe(0);
  });

  it("computes mean of funding rates", () => {
    const snaps = makeSnapshots([0.0001, 0.0002, 0.0003]);
    expect(averageFundingRate(snaps)).toBeCloseTo(0.0002, 6);
  });

  it("handles mixed positive and negative", () => {
    const snaps = makeSnapshots([0.0001, -0.0001]);
    expect(averageFundingRate(snaps)).toBeCloseTo(0, 10);
  });
});

// ── fundingStreak ───────────────────────────────────────────────────────────

describe("fundingStreak", () => {
  it("returns 0 for empty array", () => {
    expect(fundingStreak([])).toBe(0);
  });

  it("returns 1 for a single snapshot", () => {
    expect(fundingStreak(makeSnapshots([0.0001]))).toBe(1);
  });

  it("counts consecutive positive rates from the end", () => {
    // [neg, neg, pos, pos, pos] → streak = 3
    const snaps = makeSnapshots([-0.0001, -0.0002, 0.0001, 0.0002, 0.0003]);
    expect(fundingStreak(snaps)).toBe(3);
  });

  it("counts consecutive negative rates from the end", () => {
    // [pos, neg, neg] → streak = 2
    const snaps = makeSnapshots([0.0001, -0.0001, -0.0002]);
    expect(fundingStreak(snaps)).toBe(2);
  });

  it("breaks streak on sign change", () => {
    // [pos, neg, pos] → streak = 1
    const snaps = makeSnapshots([0.0001, -0.0001, 0.0002]);
    expect(fundingStreak(snaps)).toBe(1);
  });

  it("returns 1 for zero rate", () => {
    const snaps = makeSnapshots([0.0001, 0]);
    expect(fundingStreak(snaps)).toBe(1);
  });

  it("all same sign → streak = length", () => {
    const snaps = makeSnapshots([0.0001, 0.0002, 0.0003, 0.0004, 0.0005]);
    expect(fundingStreak(snaps)).toBe(5);
  });

  it("all-zero rates → streak = 1 (zero is non-directional)", () => {
    const snaps = makeSnapshots([0, 0, 0]);
    expect(fundingStreak(snaps)).toBe(1);
  });
});

// ── buildCandidate ──────────────────────────────────────────────────────────

describe("buildCandidate", () => {
  it("builds candidate from snapshots and spread", () => {
    const snaps = makeSnapshots([0.0001, 0.0002, 0.0003]);
    const spread = makeSpread("BTCUSDT", 67000, 67010);
    const c = buildCandidate("BTCUSDT", snaps, spread);

    expect(c.symbol).toBe("BTCUSDT");
    expect(c.currentRate).toBe(0.0003);
    expect(c.annualizedYieldPct).toBeCloseTo(32.85, 1); // 0.0003 * 1095 * 100
    expect(c.basisBps).toBeCloseTo(1.49, 1);
    expect(c.streak).toBe(3);
    expect(c.avgRate).toBeCloseTo(0.0002, 6);
  });

  it("handles null spread", () => {
    const snaps = makeSnapshots([0.0001]);
    const c = buildCandidate("ETHUSDT", snaps, null);
    expect(c.basisBps).toBe(0);
  });

  it("handles empty snapshots", () => {
    const c = buildCandidate("SOLUSDT", [], null);
    expect(c.currentRate).toBe(0);
    expect(c.annualizedYieldPct).toBe(0);
    expect(c.streak).toBe(0);
  });

  it("handles negative funding rates (short-pay)", () => {
    const snaps = makeSnapshots([-0.0002, -0.0003, -0.0004]);
    const c = buildCandidate("ETHUSDT", snaps, null);
    expect(c.currentRate).toBe(-0.0004);
    expect(c.annualizedYieldPct).toBeLessThan(0);
    expect(c.streak).toBe(3);
  });
});

// ── scanFundingCandidates ───────────────────────────────────────────────────

describe("scanFundingCandidates", () => {
  function makeSymbolData() {
    const data = new Map<string, { snapshots: FundingSnapshot[]; spread: SpreadSnapshot | null }>();

    // High yield, low basis, long streak → should qualify
    data.set("BTCUSDT", {
      snapshots: makeSnapshots([0.0001, 0.0002, 0.0003, 0.0004, 0.0005], "BTCUSDT"),
      spread: makeSpread("BTCUSDT", 67000, 67005),
    });

    // Very high yield → should rank first
    data.set("ETHUSDT", {
      snapshots: makeSnapshots([0.001, 0.001, 0.001, 0.001], "ETHUSDT"),
      spread: makeSpread("ETHUSDT", 3500, 3501),
    });

    // Too low yield → filtered out
    data.set("SOLUSDT", {
      snapshots: makeSnapshots([0.000001, 0.000001, 0.000001, 0.000001], "SOLUSDT"),
      spread: makeSpread("SOLUSDT", 150, 150.01),
    });

    // High basis (too risky) → filtered out
    data.set("DOGEUSDT", {
      snapshots: makeSnapshots([0.001, 0.001, 0.001, 0.001], "DOGEUSDT"),
      spread: makeSpread("DOGEUSDT", 0.10, 0.11), // 1000 bps basis
    });

    // Short streak → filtered out
    data.set("XRPUSDT", {
      snapshots: makeSnapshots([0.001, -0.001, 0.001], "XRPUSDT"),
      spread: makeSpread("XRPUSDT", 0.50, 0.5001),
    });

    return data;
  }

  it("returns candidates ranked by absolute yield descending", () => {
    const results = scanFundingCandidates(makeSymbolData());
    expect(results.length).toBe(2); // BTC + ETH qualify
    expect(results[0].symbol).toBe("ETHUSDT"); // higher yield
    expect(results[1].symbol).toBe("BTCUSDT");
  });

  it("filters by minAnnualizedYieldPct", () => {
    const results = scanFundingCandidates(makeSymbolData(), { minAnnualizedYieldPct: 100 });
    expect(results.every((c) => Math.abs(c.annualizedYieldPct) >= 100)).toBe(true);
  });

  it("filters by maxBasisBps", () => {
    // Allow high basis → DOGE should now qualify
    const results = scanFundingCandidates(makeSymbolData(), { maxBasisBps: 2000, minStreak: 3 });
    expect(results.some((c) => c.symbol === "DOGEUSDT")).toBe(true);
  });

  it("filters by minStreak", () => {
    // XRP has streak of 1 (alternating signs)
    const results = scanFundingCandidates(makeSymbolData(), { minStreak: 1, minAnnualizedYieldPct: 0 });
    expect(results.some((c) => c.symbol === "XRPUSDT")).toBe(true);
  });

  it("respects topN limit", () => {
    const results = scanFundingCandidates(makeSymbolData(), { topN: 1 });
    expect(results.length).toBe(1);
  });

  it("returns empty for no qualifying candidates", () => {
    const results = scanFundingCandidates(makeSymbolData(), { minAnnualizedYieldPct: 999 });
    expect(results).toEqual([]);
  });

  it("returns empty for empty input", () => {
    const results = scanFundingCandidates(new Map());
    expect(results).toEqual([]);
  });

  it("ranks all-negative funding candidates by absolute yield", () => {
    const data = new Map<string, { snapshots: FundingSnapshot[]; spread: SpreadSnapshot | null }>();
    data.set("BTCUSDT", {
      snapshots: makeSnapshots([-0.0005, -0.0005, -0.0005, -0.0005], "BTCUSDT"),
      spread: makeSpread("BTCUSDT", 67000, 66990),
    });
    data.set("ETHUSDT", {
      snapshots: makeSnapshots([-0.001, -0.001, -0.001, -0.001], "ETHUSDT"),
      spread: makeSpread("ETHUSDT", 3500, 3499),
    });
    const results = scanFundingCandidates(data, { minAnnualizedYieldPct: 5, minStreak: 3, maxBasisBps: 50 });
    expect(results.length).toBe(2);
    expect(results[0].symbol).toBe("ETHUSDT"); // higher abs yield
    expect(results[0].annualizedYieldPct).toBeLessThan(0);
  });

  it("is deterministic", () => {
    const data = makeSymbolData();
    const a = scanFundingCandidates(data);
    const b = scanFundingCandidates(data);
    expect(a).toEqual(b);
  });
});
