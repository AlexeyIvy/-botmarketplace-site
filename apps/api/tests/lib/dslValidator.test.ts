import { describe, it, expect } from "vitest";
import { validateDsl } from "../../src/lib/dslValidator.js";

/** Minimal valid DSL object that passes schema validation. */
function makeValidDsl(): Record<string, unknown> {
  return {
    id: "strat-001",
    name: "Test Strategy",
    dslVersion: 1,
    enabled: true,
    market: {
      exchange: "bybit",
      env: "demo",
      category: "linear",
      symbol: "BTCUSDT",
    },
    timeframes: ["M15"],
    entry: {
      side: "Buy",
      signal: { type: "crossover" },
      indicators: [],
    },
    risk: {
      maxPositionSizeUsd: 100,
      riskPerTradePct: 2,
      cooldownSeconds: 60,
    },
    execution: {
      orderType: "Market",
      clientOrderIdPrefix: "lab_",
      maxSlippageBps: 50,
    },
    guards: {
      maxOpenPositions: 1,
      maxOrdersPerMinute: 10,
      pauseOnError: true,
    },
  };
}

describe("dslValidator – validateDsl", () => {
  // ── Valid DSL ─────────────────────────────────────────────────────────

  it("returns null for a valid DSL object", () => {
    const result = validateDsl(makeValidDsl());
    expect(result).toBeNull();
  });

  it("accepts valid DSL with optional dailyLossLimitUsd", () => {
    const dsl = makeValidDsl();
    (dsl["risk"] as Record<string, unknown>)["dailyLossLimitUsd"] = 500;
    expect(validateDsl(dsl)).toBeNull();
  });

  // ── Null / undefined / non-object ─────────────────────────────────────

  it("rejects null input", () => {
    const errors = validateDsl(null);
    expect(errors).not.toBeNull();
    expect(errors!.length).toBeGreaterThan(0);
    expect(errors![0].message).toContain("required");
  });

  it("rejects undefined input", () => {
    const errors = validateDsl(undefined);
    expect(errors).not.toBeNull();
  });

  it("rejects array input", () => {
    const errors = validateDsl([]);
    expect(errors).not.toBeNull();
    expect(errors![0].message).toContain("JSON object");
  });

  it("rejects string input", () => {
    const errors = validateDsl("not an object");
    expect(errors).not.toBeNull();
  });

  // ── Missing required fields ───────────────────────────────────────────

  it("rejects DSL missing 'id'", () => {
    const dsl = makeValidDsl();
    delete dsl["id"];
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
    expect(errors!.some((e) => e.field === "id" || e.message.includes("id"))).toBe(true);
  });

  it("rejects DSL missing 'market'", () => {
    const dsl = makeValidDsl();
    delete dsl["market"];
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects DSL missing 'risk'", () => {
    const dsl = makeValidDsl();
    delete dsl["risk"];
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects DSL missing 'execution'", () => {
    const dsl = makeValidDsl();
    delete dsl["execution"];
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects DSL missing 'guards'", () => {
    const dsl = makeValidDsl();
    delete dsl["guards"];
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  // ── Field constraints ─────────────────────────────────────────────────

  it("rejects riskPerTradePct > 100", () => {
    const dsl = makeValidDsl();
    (dsl["risk"] as Record<string, unknown>)["riskPerTradePct"] = 150;
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects riskPerTradePct = 0", () => {
    const dsl = makeValidDsl();
    (dsl["risk"] as Record<string, unknown>)["riskPerTradePct"] = 0;
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects maxPositionSizeUsd = 0", () => {
    const dsl = makeValidDsl();
    (dsl["risk"] as Record<string, unknown>)["maxPositionSizeUsd"] = 0;
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects invalid orderType", () => {
    const dsl = makeValidDsl();
    (dsl["execution"] as Record<string, unknown>)["orderType"] = "StopLimit";
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects exchange other than bybit", () => {
    const dsl = makeValidDsl();
    (dsl["market"] as Record<string, unknown>)["exchange"] = "binance";
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects env other than demo", () => {
    const dsl = makeValidDsl();
    (dsl["market"] as Record<string, unknown>)["env"] = "live";
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  it("rejects additional properties at top level", () => {
    const dsl = makeValidDsl();
    (dsl as Record<string, unknown>)["extraField"] = "sneaky";
    const errors = validateDsl(dsl);
    expect(errors).not.toBeNull();
  });

  // ── Error format ──────────────────────────────────────────────────────

  it("error objects have field and message properties", () => {
    const errors = validateDsl({});
    expect(errors).not.toBeNull();
    for (const err of errors!) {
      expect(err).toHaveProperty("field");
      expect(err).toHaveProperty("message");
      expect(typeof err.field).toBe("string");
      expect(typeof err.message).toBe("string");
    }
  });
});
