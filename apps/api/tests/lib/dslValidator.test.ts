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

  // ── DSL v2 ─────────────────────────────────────────────────────────────

  describe("v2 – exit section", () => {
    function makeValidV2Dsl(): Record<string, unknown> {
      return {
        id: "strat-v2-001",
        name: "Test V2 Strategy",
        dslVersion: 2,
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
        exit: {
          stopLoss: { type: "fixed_pct", value: 2.0 },
          takeProfit: { type: "fixed_pct", value: 4.0 },
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

    it("accepts a valid v2 DSL with exit section", () => {
      expect(validateDsl(makeValidV2Dsl())).toBeNull();
    });

    it("accepts v2 with trailing stop", () => {
      const dsl = makeValidV2Dsl();
      (dsl.exit as Record<string, unknown>).trailingStop = {
        type: "trailing_pct",
        activationPct: 1.5,
        callbackPct: 0.5,
      };
      expect(validateDsl(dsl)).toBeNull();
    });

    it("accepts v2 with indicator exit", () => {
      const dsl = makeValidV2Dsl();
      (dsl.exit as Record<string, unknown>).indicatorExit = {
        indicator: { type: "RSI", length: 14 },
        condition: { op: "gt", value: 70 },
        appliesTo: "long",
      };
      expect(validateDsl(dsl)).toBeNull();
    });

    it("accepts v2 with time exit", () => {
      const dsl = makeValidV2Dsl();
      (dsl.exit as Record<string, unknown>).timeExit = { maxBarsInPosition: 50 };
      expect(validateDsl(dsl)).toBeNull();
    });

    it("accepts v2 with atr_multiple stop-loss", () => {
      const dsl = makeValidV2Dsl();
      (dsl.exit as Record<string, unknown>).stopLoss = {
        type: "atr_multiple",
        value: 2.0,
        atrPeriod: 14,
      };
      expect(validateDsl(dsl)).toBeNull();
    });

    it("rejects v2 without exit section", () => {
      const dsl = makeValidV2Dsl();
      delete dsl.exit;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.field === "exit")).toBe(true);
    });

    it("rejects v1 with exit section", () => {
      const dsl = makeValidV2Dsl();
      dsl.dslVersion = 1;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.message.includes("dslVersion >= 2"))).toBe(true);
    });
  });

  describe("v2 – sideCondition", () => {
    function makeV2WithSideCondition(): Record<string, unknown> {
      return {
        id: "strat-v2-sc",
        name: "Side Condition Strategy",
        dslVersion: 2,
        enabled: true,
        market: {
          exchange: "bybit",
          env: "demo",
          category: "linear",
          symbol: "ETHUSDT",
        },
        timeframes: ["H1"],
        entry: {
          sideCondition: {
            indicator: { type: "EMA", length: 200 },
            source: "close",
            long: { op: "gt" },
            short: { op: "lt" },
          },
          signal: { type: "crossover" },
          indicators: [],
        },
        exit: {
          stopLoss: { type: "fixed_pct", value: 1.5 },
          takeProfit: { type: "fixed_pct", value: 3.0 },
        },
        risk: {
          maxPositionSizeUsd: 200,
          riskPerTradePct: 1,
          cooldownSeconds: 120,
        },
        execution: {
          orderType: "Market",
          clientOrderIdPrefix: "lab_",
          maxSlippageBps: 30,
        },
        guards: {
          maxOpenPositions: 1,
          maxOrdersPerMinute: 10,
          pauseOnError: true,
        },
      };
    }

    it("accepts v2 with sideCondition (no side)", () => {
      expect(validateDsl(makeV2WithSideCondition())).toBeNull();
    });

    it("rejects side + sideCondition together", () => {
      const dsl = makeV2WithSideCondition();
      (dsl.entry as Record<string, unknown>).side = "Buy";
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.message.includes("mutually exclusive"))).toBe(true);
    });

    it("rejects sideCondition in v1", () => {
      const dsl = makeV2WithSideCondition();
      dsl.dslVersion = 1;
      delete (dsl as Record<string, unknown>).exit;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.message.includes("dslVersion >= 2"))).toBe(true);
    });

    it("rejects entry without side or sideCondition", () => {
      const dsl = makeV2WithSideCondition();
      delete (dsl.entry as Record<string, unknown>).sideCondition;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.message.includes("side") && e.message.includes("sideCondition"))).toBe(true);
    });
  });

  describe("v2 – DCA config (#131)", () => {
    function makeV2WithDca(): Record<string, unknown> {
      return {
        id: "strat-v2-dca",
        name: "DCA Strategy",
        dslVersion: 2,
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
        exit: {
          stopLoss: { type: "fixed_pct", value: 10 },
          takeProfit: { type: "fixed_pct", value: 5 },
        },
        risk: {
          maxPositionSizeUsd: 1000,
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
        dca: {
          baseOrderSizeUsd: 100,
          maxSafetyOrders: 3,
          priceStepPct: 1.0,
          stepScale: 1.0,
          volumeScale: 1.5,
          takeProfitPct: 1.5,
        },
      };
    }

    it("accepts valid v2 DSL with DCA config", () => {
      expect(validateDsl(makeV2WithDca())).toBeNull();
    });

    it("rejects DCA in v1", () => {
      const dsl = makeV2WithDca();
      dsl.dslVersion = 1;
      delete dsl.exit;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.field === "dca")).toBe(true);
    });

    it("rejects DCA when total exposure exceeds maxPositionSizeUsd", () => {
      const dsl = makeV2WithDca();
      // base=100 + SO1=150 + SO2=225 + SO3=337.5 = 812.5 > 500
      (dsl.risk as Record<string, unknown>).maxPositionSizeUsd = 500;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.message.includes("exposure"))).toBe(true);
    });

    it("accepts DCA when exposure fits within maxPositionSizeUsd", () => {
      const dsl = makeV2WithDca();
      (dsl.risk as Record<string, unknown>).maxPositionSizeUsd = 1000;
      expect(validateDsl(dsl)).toBeNull();
    });

    it("rejects DCA with missing required fields", () => {
      const dsl = makeV2WithDca();
      dsl.dca = { baseOrderSizeUsd: 100 }; // missing other fields
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
    });

    it("rejects DCA with invalid field values", () => {
      const dsl = makeV2WithDca();
      (dsl.dca as Record<string, unknown>).maxSafetyOrders = 0; // minimum is 1
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
    });

    it("rejects DCA with stepScale < 1", () => {
      const dsl = makeV2WithDca();
      (dsl.dca as Record<string, unknown>).stepScale = 0.5;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
    });

    it("rejects DCA with volumeScale < 1", () => {
      const dsl = makeV2WithDca();
      (dsl.dca as Record<string, unknown>).volumeScale = 0.9;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
    });

    it("accepts v2 without DCA (optional)", () => {
      const dsl = makeV2WithDca();
      delete dsl.dca;
      expect(validateDsl(dsl)).toBeNull();
    });

    it("rejects DCA without risk.maxPositionSizeUsd", () => {
      const dsl = makeV2WithDca();
      delete (dsl.risk as Record<string, unknown>).maxPositionSizeUsd;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.field === "risk.maxPositionSizeUsd")).toBe(true);
      expect(errors!.some((e) => e.message.includes("required"))).toBe(true);
    });

    it("rejects DCA config that would produce non-positive trigger prices", () => {
      const dsl = makeV2WithDca();
      // 50 SOs at 5% step → 250% deviation → negative trigger prices
      (dsl.dca as Record<string, unknown>).maxSafetyOrders = 50;
      (dsl.dca as Record<string, unknown>).priceStepPct = 5.0;
      (dsl.risk as Record<string, unknown>).maxPositionSizeUsd = 999999;
      const errors = validateDsl(dsl);
      expect(errors).not.toBeNull();
      expect(errors!.some((e) => e.message.includes("deviation"))).toBe(true);
    });

    it("accepts DCA config where deviation is safely under 100%", () => {
      const dsl = makeV2WithDca();
      // 3 SOs at 1% step → 3% deviation → fine
      expect(validateDsl(dsl)).toBeNull();
    });
  });
});
