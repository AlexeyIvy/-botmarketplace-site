import { describe, it, expect } from "vitest";
import { computeSizing, extractRiskParams } from "../../src/lib/riskManager.js";

// ---------------------------------------------------------------------------
// DSL fixture
// ---------------------------------------------------------------------------

function makeRiskDsl(overrides: Record<string, unknown> = {}) {
  return {
    id: "test-risk",
    name: "Risk Test",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      side: "Buy",
      signal: { type: "crossover", fast: { blockType: "SMA", length: 5 }, slow: { blockType: "SMA", length: 20 } },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 2 },
      takeProfit: { type: "fixed_pct", value: 4 },
    },
    risk: {
      maxPositionSizeUsd: 100,
      riskPerTradePct: 2,
      cooldownSeconds: 0,
      ...overrides,
    },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

// ---------------------------------------------------------------------------
// Eligibility guards
// ---------------------------------------------------------------------------

describe("riskManager – eligibility", () => {
  it("returns ineligible when already in position", () => {
    const result = computeSizing({
      dslJson: makeRiskDsl(),
      currentPrice: 50_000,
      hasOpenPosition: true,
      lastTradeCloseTime: 0,
      now: Date.now(),
    });

    expect(result.eligible).toBe(false);
    expect(result.qty).toBe(0);
    expect(result.notionalUsd).toBe(0);
    expect(result.reason).toBe("already in position");
  });

  it("returns eligible when no open position and no cooldown", () => {
    const result = computeSizing({
      dslJson: makeRiskDsl(),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: 0,
      now: Date.now(),
    });

    expect(result.eligible).toBe(true);
    expect(result.qty).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Cooldown behavior
// ---------------------------------------------------------------------------

describe("riskManager – cooldown", () => {
  it("blocks entry during active cooldown", () => {
    const now = 1_700_000_100_000;
    const result = computeSizing({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: now - 30_000, // 30s ago, cooldown is 60s
      now,
    });

    expect(result.eligible).toBe(false);
    expect(result.reason).toContain("cooldown");
    expect(result.reason).toContain("30s remaining");
  });

  it("allows entry after cooldown expires", () => {
    const now = 1_700_000_100_000;
    const result = computeSizing({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: now - 61_000, // 61s ago, cooldown is 60s
      now,
    });

    expect(result.eligible).toBe(true);
  });

  it("allows entry exactly at cooldown boundary", () => {
    const now = 1_700_000_100_000;
    const result = computeSizing({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: now - 60_000, // exactly 60s ago
      now,
    });

    expect(result.eligible).toBe(true);
  });

  it("skips cooldown when cooldownSeconds is 0", () => {
    const now = 1_700_000_100_000;
    const result = computeSizing({
      dslJson: makeRiskDsl({ cooldownSeconds: 0 }),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: now - 1_000, // 1s ago
      now,
    });

    expect(result.eligible).toBe(true);
  });

  it("skips cooldown when lastTradeCloseTime is 0 (no prior trade)", () => {
    const result = computeSizing({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: 0,
      now: Date.now(),
    });

    expect(result.eligible).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Sizing calculation
// ---------------------------------------------------------------------------

describe("riskManager – sizing", () => {
  it("computes qty = maxPositionSizeUsd / currentPrice", () => {
    const result = computeSizing({
      dslJson: makeRiskDsl({ maxPositionSizeUsd: 200 }),
      currentPrice: 50_000,
      hasOpenPosition: false,
      lastTradeCloseTime: 0,
      now: Date.now(),
    });

    expect(result.eligible).toBe(true);
    expect(result.notionalUsd).toBe(200);
    expect(result.qty).toBeCloseTo(200 / 50_000, 10);
  });

  it("defaults maxPositionSizeUsd to 100 when not specified", () => {
    const dsl = makeRiskDsl();
    delete (dsl.risk as Record<string, unknown>).maxPositionSizeUsd;

    const result = computeSizing({
      dslJson: dsl,
      currentPrice: 40_000,
      hasOpenPosition: false,
      lastTradeCloseTime: 0,
      now: Date.now(),
    });

    expect(result.eligible).toBe(true);
    expect(result.notionalUsd).toBe(100);
    expect(result.qty).toBeCloseTo(100 / 40_000, 10);
  });

  it("produces Infinity qty when currentPrice is 0", () => {
    // Edge case: division by zero produces Infinity, not a crash.
    // Callers should validate price > 0 before calling.
    const result = computeSizing({
      dslJson: makeRiskDsl(),
      currentPrice: 0,
      hasOpenPosition: false,
      lastTradeCloseTime: 0,
      now: Date.now(),
    });

    expect(result.eligible).toBe(true);
    expect(result.qty).toBe(Infinity);
  });
});

// ---------------------------------------------------------------------------
// extractRiskParams
// ---------------------------------------------------------------------------

describe("riskManager – extractRiskParams", () => {
  it("returns risk params from DSL", () => {
    const params = extractRiskParams(
      makeRiskDsl({ maxPositionSizeUsd: 500, cooldownSeconds: 120 }),
    );

    expect(params.riskPerTradePct).toBe(2);
    expect(params.maxPositionSizeUsd).toBe(500);
    expect(params.cooldownSeconds).toBe(120);
  });

  it("returns defaults when optional fields missing", () => {
    const dsl = makeRiskDsl();
    delete (dsl.risk as Record<string, unknown>).maxPositionSizeUsd;
    delete (dsl.risk as Record<string, unknown>).cooldownSeconds;

    const params = extractRiskParams(dsl);
    expect(params.maxPositionSizeUsd).toBe(100);
    expect(params.cooldownSeconds).toBe(0);
  });
});
