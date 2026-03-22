import { describe, it, expect } from "vitest";
import { computeSizing, extractRiskParams, type RiskContext } from "../../src/lib/riskManager.js";

// ---------------------------------------------------------------------------
// DSL fixture
// ---------------------------------------------------------------------------

function makeRiskDsl(overrides: Record<string, unknown> = {}) {
  return {
    id: "test-risk",
    name: "Test Risk",
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
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0, ...overrides },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

function makeCtx(overrides: Partial<RiskContext> = {}): RiskContext {
  return {
    dslJson: makeRiskDsl(),
    currentPrice: 50_000,
    hasOpenPosition: false,
    lastTradeCloseTime: 0,
    now: 1_700_000_000_000,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Eligibility guards
// ---------------------------------------------------------------------------

describe("riskManager – eligibility", () => {
  it("is eligible when no position and no cooldown", () => {
    const result = computeSizing(makeCtx());
    expect(result.eligible).toBe(true);
    expect(result.qty).toBeGreaterThan(0);
    expect(result.notionalUsd).toBe(100);
  });

  it("rejects when already in position", () => {
    const result = computeSizing(makeCtx({ hasOpenPosition: true }));
    expect(result.eligible).toBe(false);
    expect(result.qty).toBe(0);
    expect(result.notionalUsd).toBe(0);
    expect(result.reason).toBe("already in position");
  });
});

// ---------------------------------------------------------------------------
// Cooldown behavior
// ---------------------------------------------------------------------------

describe("riskManager – cooldown", () => {
  it("rejects entry during cooldown period", () => {
    const result = computeSizing(makeCtx({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      lastTradeCloseTime: 1_700_000_000_000 - 30_000, // 30s ago
      now: 1_700_000_000_000,
    }));
    expect(result.eligible).toBe(false);
    expect(result.reason).toContain("cooldown");
    expect(result.reason).toContain("30s remaining");
  });

  it("allows entry after cooldown has elapsed", () => {
    const result = computeSizing(makeCtx({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      lastTradeCloseTime: 1_700_000_000_000 - 120_000, // 120s ago (>60s)
      now: 1_700_000_000_000,
    }));
    expect(result.eligible).toBe(true);
  });

  it("allows entry exactly at cooldown boundary", () => {
    const result = computeSizing(makeCtx({
      dslJson: makeRiskDsl({ cooldownSeconds: 60 }),
      lastTradeCloseTime: 1_700_000_000_000 - 60_000, // exactly 60s ago
      now: 1_700_000_000_000,
    }));
    expect(result.eligible).toBe(true);
  });

  it("ignores cooldown when lastTradeCloseTime is 0 (no prior trade)", () => {
    const result = computeSizing(makeCtx({
      dslJson: makeRiskDsl({ cooldownSeconds: 300 }),
      lastTradeCloseTime: 0,
    }));
    expect(result.eligible).toBe(true);
  });

  it("ignores cooldown when cooldownSeconds is 0", () => {
    const result = computeSizing(makeCtx({
      dslJson: makeRiskDsl({ cooldownSeconds: 0 }),
      lastTradeCloseTime: 1_700_000_000_000 - 1_000, // 1s ago
      now: 1_700_000_000_000,
    }));
    expect(result.eligible).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Sizing calculation
// ---------------------------------------------------------------------------

describe("riskManager – sizing", () => {
  it("computes qty = maxPositionSizeUsd / currentPrice", () => {
    const result = computeSizing(makeCtx({ currentPrice: 50_000 }));
    expect(result.qty).toBeCloseTo(100 / 50_000, 10);
    expect(result.notionalUsd).toBe(100);
  });

  it("uses custom maxPositionSizeUsd from DSL", () => {
    const result = computeSizing(makeCtx({
      dslJson: makeRiskDsl({ maxPositionSizeUsd: 500 }),
      currentPrice: 250,
    }));
    expect(result.qty).toBeCloseTo(2, 10);
    expect(result.notionalUsd).toBe(500);
  });

  it("defaults maxPositionSizeUsd to 100 when omitted", () => {
    const dsl = makeRiskDsl();
    delete (dsl.risk as Record<string, unknown>).maxPositionSizeUsd;
    const result = computeSizing(makeCtx({ dslJson: dsl, currentPrice: 100 }));
    expect(result.notionalUsd).toBe(100);
    expect(result.qty).toBeCloseTo(1, 10);
  });

  it("handles very high price (small qty)", () => {
    const result = computeSizing(makeCtx({ currentPrice: 1_000_000 }));
    expect(result.qty).toBeCloseTo(100 / 1_000_000, 12);
    expect(result.eligible).toBe(true);
  });

  it("handles very low price (large qty)", () => {
    const result = computeSizing(makeCtx({ currentPrice: 0.001 }));
    expect(result.qty).toBeCloseTo(100 / 0.001, 5);
    expect(result.eligible).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// extractRiskParams
// ---------------------------------------------------------------------------

describe("riskManager – extractRiskParams", () => {
  it("extracts risk params from DSL", () => {
    const params = extractRiskParams(makeRiskDsl({ maxPositionSizeUsd: 250, cooldownSeconds: 30 }));
    expect(params.riskPerTradePct).toBe(2);
    expect(params.maxPositionSizeUsd).toBe(250);
    expect(params.cooldownSeconds).toBe(30);
  });

  it("uses defaults for missing optional fields", () => {
    const dsl = makeRiskDsl();
    delete (dsl.risk as Record<string, unknown>).maxPositionSizeUsd;
    delete (dsl.risk as Record<string, unknown>).cooldownSeconds;
    const params = extractRiskParams(dsl);
    expect(params.maxPositionSizeUsd).toBe(100);
    expect(params.cooldownSeconds).toBe(0);
  });
});
