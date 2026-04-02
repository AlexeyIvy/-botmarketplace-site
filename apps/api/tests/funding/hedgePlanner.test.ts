import { describe, it, expect } from "vitest";
import {
  shouldEnterHedge,
  planHedge,
  applySpotFill,
  applyPerpFill,
  applyFundingPayment,
  shouldExitHedge,
  beginClose,
  finalizeClose,
  computeHedgePnl,
} from "../../src/lib/funding/hedgePlanner.js";
import type { FundingCandidate } from "../../src/lib/funding/types.js";
import type { LegExecution, HedgePosition } from "../../src/lib/funding/hedgeTypes.js";

// ── Helpers ─────────────────────────────────────────────────────────────────

const T0 = 1_700_000_000_000;

function makeCandidate(overrides: Partial<FundingCandidate> = {}): FundingCandidate {
  return {
    symbol: "BTCUSDT",
    currentRate: 0.0003,
    annualizedYieldPct: 32.85,
    basisBps: 5,
    streak: 5,
    avgRate: 0.0002,
    ...overrides,
  };
}

function makeLeg(side: LegExecution["side"], price: number, qty: number, fee = 0): LegExecution {
  return { side, price, quantity: qty, fee, timestamp: T0 };
}

function makeOpenPosition(): HedgePosition {
  const pos = planHedge("BTCUSDT", 5, T0);
  const withSpot = applySpotFill(pos, makeLeg("SPOT_BUY", 67000, 0.015));
  return applyPerpFill(withSpot, makeLeg("PERP_SHORT", 67005, 0.015));
}

// ── shouldEnterHedge ────────────────────────────────────────────────────────

describe("shouldEnterHedge", () => {
  it("returns true for a qualifying candidate", () => {
    expect(shouldEnterHedge(makeCandidate())).toBe(true);
  });

  it("rejects low yield", () => {
    expect(shouldEnterHedge(makeCandidate({ annualizedYieldPct: 5 }))).toBe(false);
  });

  it("rejects wide basis", () => {
    expect(shouldEnterHedge(makeCandidate({ basisBps: 50 }))).toBe(false);
  });

  it("rejects short streak", () => {
    expect(shouldEnterHedge(makeCandidate({ streak: 2 }))).toBe(false);
  });

  it("rejects negative yield (short-pay, only long-collect supported)", () => {
    expect(shouldEnterHedge(makeCandidate({ annualizedYieldPct: -20 }))).toBe(false);
  });

  it("respects custom thresholds", () => {
    const candidate = makeCandidate({ annualizedYieldPct: 6, basisBps: 2, streak: 3 });
    expect(shouldEnterHedge(candidate, { minEntryYieldPct: 5 })).toBe(true);
    expect(shouldEnterHedge(candidate, { minEntryYieldPct: 10 })).toBe(false);
  });
});

// ── State machine: plan → open → close ──────────────────────────────────────

describe("hedge state machine", () => {
  it("planHedge creates PLANNED position", () => {
    const pos = planHedge("BTCUSDT", 5, T0);
    expect(pos.status).toBe("PLANNED");
    expect(pos.symbol).toBe("BTCUSDT");
    expect(pos.entryBasisBps).toBe(5);
    expect(pos.spotLeg).toBeNull();
    expect(pos.perpLeg).toBeNull();
    expect(pos.fundingCollected).toBe(0);
  });

  it("applySpotFill transitions to OPENING", () => {
    const pos = planHedge("BTCUSDT", 5, T0);
    const filled = applySpotFill(pos, makeLeg("SPOT_BUY", 67000, 0.015));
    expect(filled.status).toBe("OPENING");
    expect(filled.spotLeg).not.toBeNull();
    expect(filled.spotLeg!.price).toBe(67000);
  });

  it("applyPerpFill after spotFill transitions to OPEN", () => {
    const pos = planHedge("BTCUSDT", 5, T0);
    const withSpot = applySpotFill(pos, makeLeg("SPOT_BUY", 67000, 0.015));
    const open = applyPerpFill(withSpot, makeLeg("PERP_SHORT", 67005, 0.015));
    expect(open.status).toBe("OPEN");
    expect(open.spotLeg).not.toBeNull();
    expect(open.perpLeg).not.toBeNull();
  });

  it("legs can be filled in either order", () => {
    const pos = planHedge("BTCUSDT", 5, T0);
    const withPerp = applyPerpFill(pos, makeLeg("PERP_SHORT", 67005, 0.015));
    expect(withPerp.status).toBe("OPENING");
    const open = applySpotFill(withPerp, makeLeg("SPOT_BUY", 67000, 0.015));
    expect(open.status).toBe("OPEN");
  });

  it("applyFundingPayment accumulates funding", () => {
    const open = makeOpenPosition();
    const after1 = applyFundingPayment(open, 1.5);
    expect(after1.fundingCollected).toBe(1.5);
    const after2 = applyFundingPayment(after1, 2.0);
    expect(after2.fundingCollected).toBe(3.5);
  });

  it("does not mutate the original position", () => {
    const open = makeOpenPosition();
    const after = applyFundingPayment(open, 5);
    expect(open.fundingCollected).toBe(0);
    expect(after.fundingCollected).toBe(5);
  });
});

// ── shouldExitHedge ─────────────────────────────────────────────────────────

describe("shouldExitHedge", () => {
  it("returns null for non-OPEN position", () => {
    const planned = planHedge("BTCUSDT", 5, T0);
    expect(shouldExitHedge(planned, 0.0003, 67000, 67005, T0)).toBeNull();
  });

  it("returns null when conditions are healthy", () => {
    const open = makeOpenPosition();
    // Good yield (0.0003 → ~32.85%), tight basis, within hold time
    expect(shouldExitHedge(open, 0.0003, 67000, 67005, T0 + 1000)).toBeNull();
  });

  it("returns funding_deteriorated when yield drops", () => {
    const open = makeOpenPosition();
    // Very low rate → yield below floor
    expect(shouldExitHedge(open, 0.000001, 67000, 67005, T0 + 1000)).toBe("funding_deteriorated");
  });

  it("returns basis_widened when spread is too large", () => {
    const open = makeOpenPosition();
    // Huge basis: perp at 67700 vs spot 67000 → ~104 bps > 100 ceiling
    expect(shouldExitHedge(open, 0.0003, 67000, 67700, T0 + 1000)).toBe("basis_widened");
  });

  it("returns max_hold_exceeded when position is too old", () => {
    const open = makeOpenPosition();
    const eightDaysLater = T0 + 8 * 24 * 60 * 60 * 1000;
    expect(shouldExitHedge(open, 0.0003, 67000, 67005, eightDaysLater)).toBe("max_hold_exceeded");
  });

  it("respects custom config", () => {
    const open = makeOpenPosition();
    // Default would exit on low yield, but custom floor is 0
    expect(shouldExitHedge(open, 0.000001, 67000, 67005, T0 + 1000, { exitYieldFloorPct: 0 })).toBeNull();
  });

  it("checks exit conditions in priority order: funding → basis → time", () => {
    const open = makeOpenPosition();
    const eightDaysLater = T0 + 8 * 24 * 60 * 60 * 1000;
    // Both funding deteriorated AND max hold exceeded → funding wins (checked first)
    expect(shouldExitHedge(open, 0.000001, 67000, 67005, eightDaysLater)).toBe("funding_deteriorated");
  });
});

// ── Close lifecycle ─────────────────────────────────────────────────────────

describe("close lifecycle", () => {
  it("beginClose transitions to CLOSING", () => {
    const open = makeOpenPosition();
    const closing = beginClose(open, "funding_deteriorated");
    expect(closing.status).toBe("CLOSING");
  });

  it("finalizeClose transitions to CLOSED with all legs", () => {
    const open = makeOpenPosition();
    const closing = beginClose(open, "funding_deteriorated");
    const closed = finalizeClose(
      closing,
      makeLeg("SPOT_SELL", 67100, 0.015),
      makeLeg("PERP_CLOSE", 67095, 0.015),
      T0 + 86400000,
    );
    expect(closed.status).toBe("CLOSED");
    expect(closed.spotCloseLeg).not.toBeNull();
    expect(closed.perpCloseLeg).not.toBeNull();
    expect(closed.closedAt).toBe(T0 + 86400000);
  });
});

// ── computeHedgePnl ─────────────────────────────────────────────────────────

describe("computeHedgePnl", () => {
  it("returns 0 for non-CLOSED position", () => {
    expect(computeHedgePnl(makeOpenPosition())).toBe(0);
  });

  it("computes correct P&L for a profitable hedge", () => {
    // Buy spot at 67000, short perp at 67005
    // Sell spot at 67100, close perp at 67095
    // Spot P&L = (67100 - 67000) * 0.015 = 1.50
    // Perp P&L = (67005 - 67095) * 0.015 = -1.35
    // Funding collected = 5.00
    // Total fees = 4 * 0.10 = 0.40
    // Net = 5.00 + 1.50 - 1.35 - 0.40 = 4.75
    let pos = planHedge("BTCUSDT", 5, T0);
    pos = applySpotFill(pos, makeLeg("SPOT_BUY", 67000, 0.015, 0.10));
    pos = applyPerpFill(pos, makeLeg("PERP_SHORT", 67005, 0.015, 0.10));
    pos = applyFundingPayment(pos, 5.0);
    pos = beginClose(pos, "manual");
    pos = finalizeClose(
      pos,
      makeLeg("SPOT_SELL", 67100, 0.015, 0.10),
      makeLeg("PERP_CLOSE", 67095, 0.015, 0.10),
      T0 + 86400000,
    );

    const pnl = computeHedgePnl(pos);
    expect(pnl).toBeCloseTo(4.75, 2);
  });

  it("computes negative P&L when funding doesn't cover losses", () => {
    let pos = planHedge("BTCUSDT", 5, T0);
    pos = applySpotFill(pos, makeLeg("SPOT_BUY", 67000, 0.015, 0.50));
    pos = applyPerpFill(pos, makeLeg("PERP_SHORT", 67005, 0.015, 0.50));
    pos = applyFundingPayment(pos, 0.5); // minimal funding
    pos = beginClose(pos, "basis_widened");
    // Price moved against us: spot dropped, perp dropped more
    pos = finalizeClose(
      pos,
      makeLeg("SPOT_SELL", 66000, 0.015, 0.50),
      makeLeg("PERP_CLOSE", 67100, 0.015, 0.50),
      T0 + 86400000,
    );

    const pnl = computeHedgePnl(pos);
    expect(pnl).toBeLessThan(0);
  });

  it("is deterministic", () => {
    let pos = planHedge("BTCUSDT", 5, T0);
    pos = applySpotFill(pos, makeLeg("SPOT_BUY", 67000, 0.015));
    pos = applyPerpFill(pos, makeLeg("PERP_SHORT", 67005, 0.015));
    pos = applyFundingPayment(pos, 3.0);
    pos = finalizeClose(pos, makeLeg("SPOT_SELL", 67050, 0.015), makeLeg("PERP_CLOSE", 67040, 0.015), T0 + 1000);
    const a = computeHedgePnl(pos);
    const b = computeHedgePnl(pos);
    expect(a).toBe(b);
  });
});
