/**
 * Safety Circuit Breaker Tests (#141, slice 1)
 *
 * Validates the pure decision logic for two runtime circuit breakers:
 *
 *   1. Daily loss limit — stops a run when estimated daily loss exceeds threshold
 *   2. Pause on error — stops a run after consecutive failed intents
 *
 * All tests are deterministic: no DB, no network, no wall-clock dependence.
 * Tests exercise the pure functions in safetyGuards.ts which the botWorker
 * feeds with DB-queried state.
 *
 * Stage 8, issue #141 — first slice: circuit breaker safety tests.
 */

import { describe, it, expect } from "vitest";
import {
  parseDailyLossConfig,
  parseGuardsConfig,
  shouldTriggerDailyLossLimit,
  shouldPauseOnError,
  DEFAULT_ERROR_PAUSE_THRESHOLD,
  type DailyLossConfig,
} from "../../src/lib/safetyGuards.js";

// ---------------------------------------------------------------------------
// Helpers: minimal DSL fixtures
// ---------------------------------------------------------------------------

function makeDsl(overrides: {
  risk?: Record<string, unknown>;
  guards?: Record<string, unknown>;
} = {}): Record<string, unknown> {
  return {
    version: 2,
    enabled: true,
    risk: {
      riskPerTradePct: 1,
      maxPositionSizeUsd: 100,
      dailyLossLimitUsd: 50,
      cooldownSeconds: 0,
      ...overrides.risk,
    },
    guards: {
      maxOpenPositions: 1,
      maxOrdersPerMinute: 10,
      pauseOnError: true,
      ...overrides.guards,
    },
  };
}

// ===========================================================================
// 1. parseDailyLossConfig
// ===========================================================================

describe("parseDailyLossConfig", () => {
  it("extracts risk fields from valid DSL", () => {
    const config = parseDailyLossConfig(makeDsl());
    expect(config.dailyLossLimitUsd).toBe(50);
    expect(config.riskPerTradePct).toBe(1);
    expect(config.maxPositionSizeUsd).toBe(100);
  });

  it("returns defaults when risk section is missing", () => {
    const config = parseDailyLossConfig({ version: 2 });
    expect(config.dailyLossLimitUsd).toBeNull();
    expect(config.riskPerTradePct).toBe(1);
    expect(config.maxPositionSizeUsd).toBe(100);
  });

  it("returns null limit for non-positive dailyLossLimitUsd", () => {
    expect(parseDailyLossConfig(makeDsl({ risk: { dailyLossLimitUsd: 0 } })).dailyLossLimitUsd).toBeNull();
    expect(parseDailyLossConfig(makeDsl({ risk: { dailyLossLimitUsd: -10 } })).dailyLossLimitUsd).toBeNull();
  });

  it("returns null limit for non-number dailyLossLimitUsd", () => {
    expect(parseDailyLossConfig(makeDsl({ risk: { dailyLossLimitUsd: "50" } })).dailyLossLimitUsd).toBeNull();
    expect(parseDailyLossConfig(makeDsl({ risk: { dailyLossLimitUsd: null } })).dailyLossLimitUsd).toBeNull();
  });

  it("handles null/undefined DSL gracefully", () => {
    expect(parseDailyLossConfig(null).dailyLossLimitUsd).toBeNull();
    expect(parseDailyLossConfig(undefined).dailyLossLimitUsd).toBeNull();
  });
});

// ===========================================================================
// 2. parseGuardsConfig
// ===========================================================================

describe("parseGuardsConfig", () => {
  it("reads pauseOnError=true from DSL", () => {
    const guards = parseGuardsConfig(makeDsl());
    expect(guards.pauseOnError).toBe(true);
  });

  it("reads pauseOnError=false from DSL", () => {
    const guards = parseGuardsConfig(makeDsl({ guards: { pauseOnError: false } }));
    expect(guards.pauseOnError).toBe(false);
  });

  it("defaults to true when guards section is missing", () => {
    const guards = parseGuardsConfig({ version: 2 });
    expect(guards.pauseOnError).toBe(true);
  });

  it("defaults to true when pauseOnError field is missing", () => {
    const guards = parseGuardsConfig({ version: 2, guards: { maxOpenPositions: 1 } });
    expect(guards.pauseOnError).toBe(true);
  });

  it("defaults to true for null/undefined DSL", () => {
    expect(parseGuardsConfig(null).pauseOnError).toBe(true);
    expect(parseGuardsConfig(undefined).pauseOnError).toBe(true);
  });
});

// ===========================================================================
// 3. shouldTriggerDailyLossLimit — core invariants
// ===========================================================================

describe("shouldTriggerDailyLossLimit", () => {
  const baseConfig: DailyLossConfig = {
    dailyLossLimitUsd: 50,
    riskPerTradePct: 1,
    maxPositionSizeUsd: 100,
  };
  // estimatedLossPerTrade = (1 / 100) * 100 = $1 per failed intent

  it("does not trigger when no failed intents", () => {
    const result = shouldTriggerDailyLossLimit(baseConfig, 0);
    expect(result.triggered).toBe(false);
    expect(result.estimatedLoss).toBe(0);
  });

  it("does not trigger when estimated loss is below limit", () => {
    const result = shouldTriggerDailyLossLimit(baseConfig, 49);
    expect(result.triggered).toBe(false);
    expect(result.estimatedLoss).toBe(49);
  });

  it("triggers when estimated loss equals limit exactly", () => {
    const result = shouldTriggerDailyLossLimit(baseConfig, 50);
    expect(result.triggered).toBe(true);
    expect(result.estimatedLoss).toBe(50);
  });

  it("triggers when estimated loss exceeds limit", () => {
    const result = shouldTriggerDailyLossLimit(baseConfig, 100);
    expect(result.triggered).toBe(true);
    expect(result.estimatedLoss).toBe(100);
  });

  it("does not trigger when dailyLossLimitUsd is null", () => {
    const config = { ...baseConfig, dailyLossLimitUsd: null };
    const result = shouldTriggerDailyLossLimit(config, 1000);
    expect(result.triggered).toBe(false);
    expect(result.reason).toContain("no daily loss limit");
  });

  it("does not trigger when dailyLossLimitUsd is zero", () => {
    const config = { ...baseConfig, dailyLossLimitUsd: 0 };
    const result = shouldTriggerDailyLossLimit(config, 1000);
    expect(result.triggered).toBe(false);
  });

  it("is deterministic — same inputs always produce same output", () => {
    const r1 = shouldTriggerDailyLossLimit(baseConfig, 50);
    const r2 = shouldTriggerDailyLossLimit(baseConfig, 50);
    expect(r1).toEqual(r2);
  });

  it("repeated evaluation after trigger remains triggered", () => {
    // Simulates: breaker already fired on tick N, re-evaluated on tick N+1
    // The function is stateless — it should still return triggered=true
    const result1 = shouldTriggerDailyLossLimit(baseConfig, 60);
    const result2 = shouldTriggerDailyLossLimit(baseConfig, 60);
    expect(result1.triggered).toBe(true);
    expect(result2.triggered).toBe(true);
    expect(result1).toEqual(result2);
  });

  describe("with different risk parameters", () => {
    it("higher riskPerTradePct triggers sooner", () => {
      const highRisk: DailyLossConfig = {
        dailyLossLimitUsd: 50,
        riskPerTradePct: 5, // 5% → $5/trade
        maxPositionSizeUsd: 100,
      };
      // 10 failures × $5 = $50 → triggers
      expect(shouldTriggerDailyLossLimit(highRisk, 10).triggered).toBe(true);
      // 9 failures × $5 = $45 → does not trigger
      expect(shouldTriggerDailyLossLimit(highRisk, 9).triggered).toBe(false);
    });

    it("larger position size triggers sooner", () => {
      const bigPosition: DailyLossConfig = {
        dailyLossLimitUsd: 50,
        riskPerTradePct: 1, // 1% of $5000 = $50/trade
        maxPositionSizeUsd: 5000,
      };
      // 1 failure × $50 = $50 → triggers
      expect(shouldTriggerDailyLossLimit(bigPosition, 1).triggered).toBe(true);
      // 0 failures → does not trigger
      expect(shouldTriggerDailyLossLimit(bigPosition, 0).triggered).toBe(false);
    });

    it("uses defaults correctly for missing risk fields", () => {
      const config = parseDailyLossConfig(makeDsl());
      const result = shouldTriggerDailyLossLimit(config, 50);
      expect(result.triggered).toBe(true);
      expect(result.estimatedLossPerTrade).toBe(1); // (1/100)*100
    });
  });

  describe("estimatedLoss calculation accuracy", () => {
    it("returns correct estimatedLoss and estimatedLossPerTrade", () => {
      const config: DailyLossConfig = {
        dailyLossLimitUsd: 100,
        riskPerTradePct: 2,
        maxPositionSizeUsd: 500,
      };
      // expectedLossPerTrade = (2/100) * 500 = $10
      const result = shouldTriggerDailyLossLimit(config, 7);
      expect(result.estimatedLossPerTrade).toBe(10);
      expect(result.estimatedLoss).toBe(70);
      expect(result.triggered).toBe(false);
    });
  });
});

// ===========================================================================
// 4. shouldPauseOnError — core invariants
// ===========================================================================

describe("shouldPauseOnError", () => {
  it("does not trigger when pauseOnError is false", () => {
    const result = shouldPauseOnError(false, 100);
    expect(result.triggered).toBe(false);
    expect(result.reason).toContain("disabled");
  });

  it("does not trigger when fewer failures than threshold", () => {
    const result = shouldPauseOnError(true, 2);
    expect(result.triggered).toBe(false);
    expect(result.consecutiveFailures).toBe(2);
  });

  it("triggers when failures equal threshold", () => {
    const result = shouldPauseOnError(true, DEFAULT_ERROR_PAUSE_THRESHOLD);
    expect(result.triggered).toBe(true);
    expect(result.consecutiveFailures).toBe(DEFAULT_ERROR_PAUSE_THRESHOLD);
  });

  it("triggers when failures exceed threshold", () => {
    const result = shouldPauseOnError(true, DEFAULT_ERROR_PAUSE_THRESHOLD + 5);
    expect(result.triggered).toBe(true);
  });

  it("does not trigger with zero failures", () => {
    const result = shouldPauseOnError(true, 0);
    expect(result.triggered).toBe(false);
  });

  it("is deterministic — same inputs always produce same output", () => {
    const r1 = shouldPauseOnError(true, 3);
    const r2 = shouldPauseOnError(true, 3);
    expect(r1).toEqual(r2);
  });

  it("repeated evaluation after trigger remains triggered", () => {
    const result1 = shouldPauseOnError(true, 5);
    const result2 = shouldPauseOnError(true, 5);
    expect(result1.triggered).toBe(true);
    expect(result2.triggered).toBe(true);
    expect(result1).toEqual(result2);
  });

  describe("custom threshold", () => {
    it("respects custom threshold of 1", () => {
      expect(shouldPauseOnError(true, 1, 1).triggered).toBe(true);
      expect(shouldPauseOnError(true, 0, 1).triggered).toBe(false);
    });

    it("respects custom threshold of 5", () => {
      expect(shouldPauseOnError(true, 4, 5).triggered).toBe(false);
      expect(shouldPauseOnError(true, 5, 5).triggered).toBe(true);
    });
  });

  it("default threshold is 3", () => {
    expect(DEFAULT_ERROR_PAUSE_THRESHOLD).toBe(3);
    expect(shouldPauseOnError(true, 3).triggered).toBe(true);
    expect(shouldPauseOnError(true, 2).triggered).toBe(false);
  });
});

// ===========================================================================
// 5. Config parsing + decision integration
// ===========================================================================

describe("end-to-end: DSL config → decision", () => {
  it("full path: DSL with daily loss limit → trigger on enough failures", () => {
    const dsl = makeDsl({ risk: { dailyLossLimitUsd: 10, riskPerTradePct: 2, maxPositionSizeUsd: 100 } });
    const config = parseDailyLossConfig(dsl);
    // $2/trade → 5 failures = $10 → triggers
    expect(shouldTriggerDailyLossLimit(config, 5).triggered).toBe(true);
    expect(shouldTriggerDailyLossLimit(config, 4).triggered).toBe(false);
  });

  it("full path: DSL with pauseOnError=true → trigger on consecutive failures", () => {
    const dsl = makeDsl({ guards: { pauseOnError: true } });
    const guards = parseGuardsConfig(dsl);
    expect(shouldPauseOnError(guards.pauseOnError, 3).triggered).toBe(true);
    expect(shouldPauseOnError(guards.pauseOnError, 2).triggered).toBe(false);
  });

  it("full path: DSL with pauseOnError=false → never trigger", () => {
    const dsl = makeDsl({ guards: { pauseOnError: false } });
    const guards = parseGuardsConfig(dsl);
    expect(shouldPauseOnError(guards.pauseOnError, 100).triggered).toBe(false);
  });

  it("both guards can fire independently on the same DSL", () => {
    const dsl = makeDsl({
      risk: { dailyLossLimitUsd: 10, riskPerTradePct: 2, maxPositionSizeUsd: 100 },
      guards: { pauseOnError: true },
    });

    const lossConfig = parseDailyLossConfig(dsl);
    const guardsConfig = parseGuardsConfig(dsl);

    // Daily loss triggers at 5 failed (5 × $2 = $10)
    const lossResult = shouldTriggerDailyLossLimit(lossConfig, 5);
    expect(lossResult.triggered).toBe(true);

    // pauseOnError triggers at 3 consecutive
    const pauseResult = shouldPauseOnError(guardsConfig.pauseOnError, 3);
    expect(pauseResult.triggered).toBe(true);
  });

  it("daily loss guard tolerates when no risk section at all", () => {
    const dsl = { version: 2, enabled: true };
    const config = parseDailyLossConfig(dsl);
    // Should not blow up, and should not trigger
    const result = shouldTriggerDailyLossLimit(config, 1000);
    expect(result.triggered).toBe(false);
  });

  it("pauseOnError guard tolerates when no guards section at all", () => {
    const dsl = { version: 2, enabled: true };
    const guards = parseGuardsConfig(dsl);
    // Default is true, so it should be able to trigger
    expect(guards.pauseOnError).toBe(true);
    expect(shouldPauseOnError(guards.pauseOnError, 3).triggered).toBe(true);
  });
});

// ===========================================================================
// 6. Edge cases and robustness
// ===========================================================================

describe("edge cases", () => {
  it("very large failedIntentCount does not overflow", () => {
    const config: DailyLossConfig = {
      dailyLossLimitUsd: 1000,
      riskPerTradePct: 0.01,
      maxPositionSizeUsd: 100,
    };
    const result = shouldTriggerDailyLossLimit(config, 1_000_000);
    expect(result.triggered).toBe(true);
    expect(Number.isFinite(result.estimatedLoss)).toBe(true);
  });

  it("very small riskPerTradePct requires many failures to trigger", () => {
    const config: DailyLossConfig = {
      dailyLossLimitUsd: 100,
      riskPerTradePct: 0.001, // 0.001% → $0.001/trade
      maxPositionSizeUsd: 100,
    };
    // Need 100,000 failures to reach $100
    expect(shouldTriggerDailyLossLimit(config, 99_999).triggered).toBe(false);
    expect(shouldTriggerDailyLossLimit(config, 100_000).triggered).toBe(true);
  });

  it("pauseOnError: exactly at boundary values", () => {
    // At threshold-1: no trigger
    expect(shouldPauseOnError(true, DEFAULT_ERROR_PAUSE_THRESHOLD - 1).triggered).toBe(false);
    // At threshold: trigger
    expect(shouldPauseOnError(true, DEFAULT_ERROR_PAUSE_THRESHOLD).triggered).toBe(true);
    // At threshold+1: trigger
    expect(shouldPauseOnError(true, DEFAULT_ERROR_PAUSE_THRESHOLD + 1).triggered).toBe(true);
  });

  it("result.reason is always a non-empty string", () => {
    const cases = [
      shouldTriggerDailyLossLimit({ dailyLossLimitUsd: null, riskPerTradePct: 1, maxPositionSizeUsd: 100 }, 0),
      shouldTriggerDailyLossLimit({ dailyLossLimitUsd: 50, riskPerTradePct: 1, maxPositionSizeUsd: 100 }, 0),
      shouldTriggerDailyLossLimit({ dailyLossLimitUsd: 50, riskPerTradePct: 1, maxPositionSizeUsd: 100 }, 50),
      shouldPauseOnError(true, 0),
      shouldPauseOnError(true, 3),
      shouldPauseOnError(false, 100),
    ];
    for (const result of cases) {
      expect(typeof result.reason).toBe("string");
      expect(result.reason.length).toBeGreaterThan(0);
    }
  });
});
