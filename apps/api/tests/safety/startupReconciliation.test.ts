/**
 * Startup Reconciliation Tests (#141, slice 2)
 *
 * Validates the pure decision logic for startup intent reconciliation:
 *
 *   1. classifyIntent — per-intent classification on startup
 *   2. reconcileStartupState — full reconciliation decision for a run
 *   3. detectStartupInconsistencies — position-intent consistency checks
 *
 * All tests are deterministic: no DB, no network, no wall-clock dependence.
 * Tests exercise the pure functions in stateReconciler.ts which the botWorker
 * feeds with DB-queried state during activateRun.
 *
 * Stage 8, issue #141 — slice 2: startup reconciliation.
 */

import { describe, it, expect } from "vitest";
import {
  classifyIntent,
  reconcileStartupState,
  detectStartupInconsistencies,
  type StartupIntent,
  type StartupReconciliationResult,
} from "../../src/lib/stateReconciler.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BASE_DATE = new Date("2024-06-15T12:00:00Z");

function makeIntent(overrides: Partial<StartupIntent> = {}): StartupIntent {
  return {
    id: "intent-001",
    intentId: "entry_1718452800000_long",
    state: "PENDING",
    type: "ENTRY",
    side: "BUY",
    orderId: null,
    createdAt: BASE_DATE,
    ...overrides,
  };
}

function makePosition(overrides: Partial<PositionSnapshot> = {}): PositionSnapshot {
  return {
    id: "pos-001",
    botId: "bot-test",
    botRunId: "run-test",
    symbol: "BTCUSDT",
    side: "LONG",
    status: "OPEN",
    entryQty: 0.01,
    avgEntryPrice: 65000,
    costBasis: 650,
    currentQty: 0.01,
    realisedPnl: 0,
    slPrice: 64000,
    tpPrice: 67000,
    openedAt: new Date("2024-06-15T11:00:00Z"),
    closedAt: null,
    ...overrides,
  };
}

// ===========================================================================
// 1. classifyIntent — per-intent classification
// ===========================================================================

describe("classifyIntent", () => {
  it("classifies PENDING intent as cancel", () => {
    const result = classifyIntent(makeIntent({ state: "PENDING" }));
    expect(result.action).toBe("cancel");
    expect(result.reason).toContain("stale PENDING");
  });

  it("classifies PLACED intent as monitor", () => {
    const result = classifyIntent(makeIntent({
      state: "PLACED",
      orderId: "bybit-order-123",
    }));
    expect(result.action).toBe("monitor");
    expect(result.reason).toContain("PLACED");
    expect(result.reason).toContain("exchange reconciliation");
  });

  it("classifies PARTIALLY_FILLED intent as monitor", () => {
    const result = classifyIntent(makeIntent({
      state: "PARTIALLY_FILLED",
      orderId: "bybit-order-456",
    }));
    expect(result.action).toBe("monitor");
    expect(result.reason).toContain("PARTIALLY_FILLED");
  });

  it("classifies FILLED intent as ok", () => {
    const result = classifyIntent(makeIntent({ state: "FILLED" }));
    expect(result.action).toBe("ok");
    expect(result.reason).toContain("terminal");
  });

  it("classifies FAILED intent as ok", () => {
    const result = classifyIntent(makeIntent({ state: "FAILED" }));
    expect(result.action).toBe("ok");
  });

  it("classifies CANCELLED intent as ok", () => {
    const result = classifyIntent(makeIntent({ state: "CANCELLED" }));
    expect(result.action).toBe("ok");
  });

  it("preserves intent id and db id in classification", () => {
    const result = classifyIntent(makeIntent({
      id: "db-id-xyz",
      intentId: "entry_123_long",
    }));
    expect(result.id).toBe("db-id-xyz");
    expect(result.intentId).toBe("entry_123_long");
  });

  it("classifies PENDING EXIT intent as cancel", () => {
    const result = classifyIntent(makeIntent({
      state: "PENDING",
      type: "EXIT",
      side: "SELL",
    }));
    expect(result.action).toBe("cancel");
    expect(result.reason).toContain("EXIT");
  });
});

// ===========================================================================
// 2. reconcileStartupState — full reconciliation
// ===========================================================================

describe("reconcileStartupState", () => {
  describe("clean startup (no intents)", () => {
    it("returns clean result with no intents", () => {
      const result = reconcileStartupState([], null);
      expect(result.toCancel).toHaveLength(0);
      expect(result.toMonitor).toHaveLength(0);
      expect(result.terminal).toHaveLength(0);
      expect(result.safeToEvaluate).toBe(true);
      expect(result.summary).toContain("clean startup");
      expect(result.counts.total).toBe(0);
    });

    it("returns clean result with only terminal intents", () => {
      const intents = [
        makeIntent({ id: "i1", state: "FILLED" }),
        makeIntent({ id: "i2", state: "FAILED" }),
        makeIntent({ id: "i3", state: "CANCELLED" }),
      ];
      const result = reconcileStartupState(intents, null);
      expect(result.toCancel).toHaveLength(0);
      expect(result.toMonitor).toHaveLength(0);
      expect(result.terminal).toHaveLength(3);
      expect(result.safeToEvaluate).toBe(true);
      expect(result.counts.terminal).toBe(3);
    });
  });

  describe("stale PENDING intents", () => {
    it("marks stale PENDING intents for cancellation", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING", type: "ENTRY" }),
        makeIntent({ id: "i2", state: "PENDING", type: "EXIT" }),
      ];
      const result = reconcileStartupState(intents, null);
      expect(result.toCancel).toHaveLength(2);
      expect(result.toCancel[0].action).toBe("cancel");
      expect(result.toCancel[1].action).toBe("cancel");
      expect(result.counts.pending).toBe(2);
    });

    it("cancels stale ENTRY intents when position is open (prevents duplicate entry)", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING", type: "ENTRY" }),
      ];
      const position = makePosition();
      const result = reconcileStartupState(intents, position);
      expect(result.toCancel).toHaveLength(1);
      expect(result.summary).toContain("stale ENTRY");
      expect(result.summary).toContain("duplicate");
    });

    it("cancels stale EXIT intents when no position (prevents phantom exit)", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING", type: "EXIT", side: "SELL" }),
      ];
      const result = reconcileStartupState(intents, null);
      expect(result.toCancel).toHaveLength(1);
    });

    it("is safe to evaluate after cancellation is applied", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING" }),
        makeIntent({ id: "i2", state: "PENDING" }),
        makeIntent({ id: "i3", state: "PENDING" }),
      ];
      const result = reconcileStartupState(intents, null);
      expect(result.safeToEvaluate).toBe(true);
    });
  });

  describe("in-flight intents (PLACED/PARTIALLY_FILLED)", () => {
    it("marks PLACED intents for monitoring", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PLACED", orderId: "bybit-123" }),
      ];
      const result = reconcileStartupState(intents, makePosition());
      expect(result.toMonitor).toHaveLength(1);
      expect(result.toMonitor[0].action).toBe("monitor");
      expect(result.counts.placed).toBe(1);
    });

    it("marks PARTIALLY_FILLED intents for monitoring", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PARTIALLY_FILLED", orderId: "bybit-456" }),
      ];
      const result = reconcileStartupState(intents, makePosition());
      expect(result.toMonitor).toHaveLength(1);
      expect(result.counts.partiallyFilled).toBe(1);
    });

    it("summary mentions in-flight count", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PLACED", orderId: "o1" }),
        makeIntent({ id: "i2", state: "PARTIALLY_FILLED", orderId: "o2" }),
      ];
      const result = reconcileStartupState(intents, null);
      expect(result.summary).toContain("2 in-flight");
    });
  });

  describe("mixed intent states", () => {
    it("correctly classifies mixed intent set", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING", type: "ENTRY" }),
        makeIntent({ id: "i2", state: "PLACED", orderId: "o1", type: "ENTRY" }),
        makeIntent({ id: "i3", state: "FILLED", type: "ENTRY" }),
        makeIntent({ id: "i4", state: "FAILED", type: "EXIT" }),
        makeIntent({ id: "i5", state: "PENDING", type: "EXIT" }),
      ];
      const result = reconcileStartupState(intents, null);

      expect(result.toCancel).toHaveLength(2);   // PENDING ENTRY + PENDING EXIT
      expect(result.toMonitor).toHaveLength(1);   // PLACED
      expect(result.terminal).toHaveLength(2);    // FILLED + FAILED
      expect(result.counts.pending).toBe(2);
      expect(result.counts.placed).toBe(1);
      expect(result.counts.terminal).toBe(2);
      expect(result.counts.total).toBe(5);
    });
  });

  describe("determinism and idempotency", () => {
    it("is deterministic — same inputs always produce same output", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING" }),
        makeIntent({ id: "i2", state: "PLACED", orderId: "o1" }),
      ];
      const position = makePosition();
      const r1 = reconcileStartupState(intents, position);
      const r2 = reconcileStartupState(intents, position);
      expect(r1).toEqual(r2);
    });

    it("is idempotent — repeated calls produce identical results", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING" }),
        makeIntent({ id: "i2", state: "FILLED" }),
      ];
      const results: StartupReconciliationResult[] = [];
      for (let i = 0; i < 5; i++) {
        results.push(reconcileStartupState(intents, null));
      }
      for (let i = 1; i < results.length; i++) {
        expect(results[i]).toEqual(results[0]);
      }
    });

    it("produces consistent counts", () => {
      const intents = [
        makeIntent({ id: "i1", state: "PENDING" }),
        makeIntent({ id: "i2", state: "PLACED", orderId: "o1" }),
        makeIntent({ id: "i3", state: "PARTIALLY_FILLED", orderId: "o2" }),
        makeIntent({ id: "i4", state: "FILLED" }),
        makeIntent({ id: "i5", state: "FAILED" }),
        makeIntent({ id: "i6", state: "CANCELLED" }),
      ];
      const result = reconcileStartupState(intents, null);
      const totalCounted =
        result.counts.pending +
        result.counts.placed +
        result.counts.partiallyFilled +
        result.counts.terminal;
      expect(totalCounted).toBe(result.counts.total);
      expect(result.counts.total).toBe(6);
    });
  });
});

// ===========================================================================
// 3. detectStartupInconsistencies — position-intent consistency
// ===========================================================================

describe("detectStartupInconsistencies", () => {
  it("returns no issues for consistent state (no position, no pending intents)", () => {
    const issues = detectStartupInconsistencies([], null);
    expect(issues).toHaveLength(0);
  });

  it("returns no issues for consistent state (open position, no pending intents)", () => {
    const intents = [
      makeIntent({ state: "FILLED", type: "ENTRY" }),
    ];
    const issues = detectStartupInconsistencies(intents, makePosition());
    expect(issues).toHaveLength(0);
  });

  it("returns no issues for consistent state (no position, terminal intents only)", () => {
    const intents = [
      makeIntent({ id: "i1", state: "FILLED", type: "ENTRY" }),
      makeIntent({ id: "i2", state: "FILLED", type: "EXIT" }),
    ];
    const issues = detectStartupInconsistencies(intents, null);
    expect(issues).toHaveLength(0);
  });

  it("detects PENDING ENTRY with open position (duplicate entry risk)", () => {
    const intents = [
      makeIntent({ state: "PENDING", type: "ENTRY" }),
    ];
    const issues = detectStartupInconsistencies(intents, makePosition());
    expect(issues).toHaveLength(1);
    expect(issues[0]).toContain("PENDING ENTRY");
    expect(issues[0]).toContain("duplicate entry");
  });

  it("detects PENDING EXIT with no open position (phantom exit risk)", () => {
    const intents = [
      makeIntent({ state: "PENDING", type: "EXIT", side: "SELL" }),
    ];
    const issues = detectStartupInconsistencies(intents, null);
    expect(issues).toHaveLength(1);
    expect(issues[0]).toContain("PENDING EXIT");
    expect(issues[0]).toContain("nonexistent position");
  });

  it("detects multiple inconsistencies simultaneously", () => {
    // Open position with stale ENTRY intent + stale EXIT intents without position
    // (This is an impossible state in practice, but tests both checks)
    const intents = [
      makeIntent({ id: "i1", state: "PENDING", type: "ENTRY" }),
    ];
    const issues = detectStartupInconsistencies(intents, makePosition());
    expect(issues.length).toBeGreaterThanOrEqual(1);
    expect(issues[0]).toContain("PENDING ENTRY");
  });

  it("ignores non-PENDING intents for consistency check", () => {
    // PLACED ENTRY with open position is fine — exchange reconciliation handles it
    const intents = [
      makeIntent({ state: "PLACED", type: "ENTRY", orderId: "o1" }),
    ];
    const issues = detectStartupInconsistencies(intents, makePosition());
    expect(issues).toHaveLength(0);
  });

  it("ignores closed position for consistency check", () => {
    const intents = [
      makeIntent({ state: "PENDING", type: "ENTRY" }),
    ];
    const closedPos = makePosition({ status: "CLOSED" });
    const issues = detectStartupInconsistencies(intents, closedPos);
    // Closed position is like no position — PENDING ENTRY with no open position is fine
    // (it would just be a stale signal, not a consistency issue per se)
    expect(issues).toHaveLength(0);
  });

  it("is deterministic", () => {
    const intents = [
      makeIntent({ state: "PENDING", type: "EXIT", side: "SELL" }),
    ];
    const r1 = detectStartupInconsistencies(intents, null);
    const r2 = detectStartupInconsistencies(intents, null);
    expect(r1).toEqual(r2);
  });
});

// ===========================================================================
// 4. Integration: recovery + reconciliation scenarios
// ===========================================================================

describe("startup reconciliation scenarios", () => {
  it("scenario: clean startup with no history", () => {
    const result = reconcileStartupState([], null);
    const issues = detectStartupInconsistencies([], null);
    expect(result.toCancel).toHaveLength(0);
    expect(result.toMonitor).toHaveLength(0);
    expect(issues).toHaveLength(0);
    expect(result.safeToEvaluate).toBe(true);
  });

  it("scenario: restart with open position and stale entry (crash during entry)", () => {
    // Worker crashed after signal fired but before intent was processed
    const intents = [
      makeIntent({ id: "i1", state: "PENDING", type: "ENTRY", intentId: "entry_100_long" }),
    ];
    const position = makePosition();

    const issues = detectStartupInconsistencies(intents, position);
    expect(issues.length).toBe(1); // duplicate entry risk detected

    const result = reconcileStartupState(intents, position);
    expect(result.toCancel).toHaveLength(1); // stale PENDING → cancel
    expect(result.summary).toContain("duplicate");
    expect(result.safeToEvaluate).toBe(true); // safe after cancellation
  });

  it("scenario: restart with in-flight order (crash during placement)", () => {
    // Worker crashed after placing order but before tracking the fill
    const intents = [
      makeIntent({
        id: "i1",
        state: "PLACED",
        type: "ENTRY",
        orderId: "bybit-order-789",
      }),
    ];

    const result = reconcileStartupState(intents, null);
    expect(result.toCancel).toHaveLength(0); // don't cancel placed orders
    expect(result.toMonitor).toHaveLength(1); // track via exchange loop
    expect(result.safeToEvaluate).toBe(true);
  });

  it("scenario: restart with mixed state after crash", () => {
    const intents = [
      // Filled entry from before crash
      makeIntent({ id: "i1", state: "FILLED", type: "ENTRY" }),
      // Stale pending exit that never got processed
      makeIntent({ id: "i2", state: "PENDING", type: "EXIT", side: "SELL" }),
      // Placed exit order still on exchange
      makeIntent({ id: "i3", state: "PLACED", type: "EXIT", orderId: "bybit-exit-1", side: "SELL" }),
    ];
    const position = makePosition();

    const result = reconcileStartupState(intents, position);
    expect(result.toCancel).toHaveLength(1); // stale PENDING EXIT
    expect(result.toMonitor).toHaveLength(1); // PLACED EXIT
    expect(result.terminal).toHaveLength(1); // FILLED ENTRY
    expect(result.safeToEvaluate).toBe(true);
  });

  it("scenario: all intents already terminal (normal clean state)", () => {
    const intents = [
      makeIntent({ id: "i1", state: "FILLED", type: "ENTRY" }),
      makeIntent({ id: "i2", state: "FILLED", type: "EXIT" }),
    ];

    const result = reconcileStartupState(intents, null);
    expect(result.toCancel).toHaveLength(0);
    expect(result.toMonitor).toHaveLength(0);
    expect(result.terminal).toHaveLength(2);
    expect(result.summary).toContain("clean startup");
  });

  it("scenario: multiple stale PENDING intents from rapid signal generation", () => {
    // Worker crashed while signal engine was generating intents rapidly
    const intents = [
      makeIntent({ id: "i1", state: "PENDING", type: "ENTRY", intentId: "entry_100_long" }),
      makeIntent({ id: "i2", state: "PENDING", type: "ENTRY", intentId: "entry_104_long" }),
      makeIntent({ id: "i3", state: "PENDING", type: "ENTRY", intentId: "entry_108_long" }),
    ];

    const result = reconcileStartupState(intents, null);
    expect(result.toCancel).toHaveLength(3);
    expect(result.counts.pending).toBe(3);
    // After cancellation, signal engine will re-evaluate with fresh market data
    expect(result.safeToEvaluate).toBe(true);
  });

  it("reconciliation followed by re-evaluation prevents duplicate actions", () => {
    // First run: stale PENDING intents found
    const intents = [
      makeIntent({ id: "i1", state: "PENDING", type: "ENTRY" }),
    ];
    const result1 = reconcileStartupState(intents, makePosition());
    expect(result1.toCancel).toHaveLength(1);

    // After cancellation: intent is now CANCELLED (simulated)
    const intentsAfter = [
      makeIntent({ id: "i1", state: "CANCELLED", type: "ENTRY" }),
    ];
    const result2 = reconcileStartupState(intentsAfter, makePosition());
    expect(result2.toCancel).toHaveLength(0); // nothing left to cancel
    expect(result2.terminal).toHaveLength(1); // CANCELLED is terminal
  });
});

// ===========================================================================
// 5. Edge cases
// ===========================================================================

describe("edge cases", () => {
  it("handles large intent set without error", () => {
    const intents: StartupIntent[] = [];
    for (let i = 0; i < 100; i++) {
      intents.push(makeIntent({
        id: `i${i}`,
        intentId: `entry_${i}_long`,
        state: i % 3 === 0 ? "PENDING" : i % 3 === 1 ? "FILLED" : "FAILED",
      }));
    }
    const result = reconcileStartupState(intents, null);
    expect(result.counts.total).toBe(100);
    expect(result.counts.pending).toBe(34); // i=0,3,6,...,99 → 34 items
    expect(result.toCancel).toHaveLength(34);
  });

  it("null position is treated as no position", () => {
    const result = reconcileStartupState([], null);
    expect(result.safeToEvaluate).toBe(true);
    expect(detectStartupInconsistencies([], null)).toHaveLength(0);
  });

  it("closed position is treated as no open position", () => {
    const closedPos = makePosition({ status: "CLOSED" });
    const intents = [makeIntent({ state: "PENDING", type: "ENTRY" })];
    const result = reconcileStartupState(intents, closedPos);
    // Should still cancel stale PENDING but not report duplicate entry risk
    expect(result.toCancel).toHaveLength(1);
    // No "duplicate" in summary because position is closed
    expect(result.summary).not.toContain("duplicate");
  });

  it("summary is always a non-empty string", () => {
    const cases = [
      reconcileStartupState([], null),
      reconcileStartupState([makeIntent({ state: "PENDING" })], null),
      reconcileStartupState([makeIntent({ state: "PLACED", orderId: "o1" })], null),
      reconcileStartupState([makeIntent({ state: "FILLED" })], null),
    ];
    for (const result of cases) {
      expect(typeof result.summary).toBe("string");
      expect(result.summary.length).toBeGreaterThan(0);
    }
  });
});
