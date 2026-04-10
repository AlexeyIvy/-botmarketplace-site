/**
 * botWorker — real function tests (Roadmap V3, Task #15)
 *
 * Tests the actual activateRun, timeoutExpiredRuns, stopRun functions
 * with mocked prisma + transition. Replaces placebo tests.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks — must be declared before imports
// ---------------------------------------------------------------------------

const mockTransition = vi.fn();
const mockIsValidTransition = vi.fn().mockReturnValue(true);

vi.mock("../../src/lib/stateMachine.js", () => ({
  transition: (...args: unknown[]) => mockTransition(...args),
  isValidTransition: (...args: unknown[]) => mockIsValidTransition(...args),
}));

const mockBotRunFindUnique = vi.fn();
const mockBotRunFindMany = vi.fn().mockResolvedValue([]);
const mockBotRunCount = vi.fn().mockResolvedValue(0);
const mockBotRunUpdate = vi.fn();
const mockBotRunUpdateMany = vi.fn();
const mockBotUpdate = vi.fn();
const mockBotIntentFindMany = vi.fn().mockResolvedValue([]);
const mockBotIntentUpdateMany = vi.fn();
const mockBotIntentUpdate = vi.fn();
const mockBotEventCreate = vi.fn();
const mockPositionEventFindFirst = vi.fn().mockResolvedValue(null);
const mockPositionFindUnique = vi.fn().mockResolvedValue(null);

vi.mock("@prisma/client", () => ({
  Prisma: {
    sql: vi.fn(),
    join: vi.fn(),
  },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    botRun: {
      findUnique: (...args: unknown[]) => mockBotRunFindUnique(...args),
      findMany: (...args: unknown[]) => mockBotRunFindMany(...args),
      count: (...args: unknown[]) => mockBotRunCount(...args),
      update: (...args: unknown[]) => mockBotRunUpdate(...args),
      updateMany: (...args: unknown[]) => mockBotRunUpdateMany(...args),
    },
    bot: {
      update: (...args: unknown[]) => mockBotUpdate(...args),
    },
    botIntent: {
      findMany: (...args: unknown[]) => mockBotIntentFindMany(...args),
      update: (...args: unknown[]) => mockBotIntentUpdate(...args),
      updateMany: (...args: unknown[]) => mockBotIntentUpdateMany(...args),
    },
    botEvent: {
      create: (...args: unknown[]) => mockBotEventCreate(...args),
    },
    positionEvent: {
      findFirst: (...args: unknown[]) => mockPositionEventFindFirst(...args),
    },
    position: {
      findUnique: (...args: unknown[]) => mockPositionFindUnique(...args),
    },
  },
}));

function createMockLogger(): Record<string, unknown> {
  const mock: Record<string, unknown> = {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
    child: () => createMockLogger(),
  };
  return mock;
}

vi.mock("../../src/lib/logger.js", () => ({
  logger: createMockLogger(),
}));

vi.mock("../../src/lib/bybitOrder.js", () => ({
  bybitPlaceOrder: vi.fn(),
  bybitGetOrderStatus: vi.fn(),
  mapBybitStatus: vi.fn(),
  getBybitBaseUrl: vi.fn().mockReturnValue("https://api-demo.bybit.com"),
  isBybitLive: vi.fn().mockReturnValue(false),
}));

vi.mock("../../src/lib/crypto.js", () => ({
  decrypt: vi.fn().mockReturnValue("decrypted-secret"),
  getEncryptionKeyRaw: vi.fn().mockReturnValue(Buffer.alloc(32)),
}));

vi.mock("../../src/lib/positionManager.js", () => ({
  getActivePosition: vi.fn().mockResolvedValue(null),
  openPosition: vi.fn(),
  applyPartialFill: vi.fn(),
  closePosition: vi.fn(),
  updateSLTP: vi.fn(),
}));

vi.mock("../../src/lib/signalEngine.js", () => ({
  evaluateEntry: vi.fn(),
}));

vi.mock("../../src/lib/exitEngine.js", () => ({
  evaluateExit: vi.fn(),
  createTrailingStopState: vi.fn(),
}));

vi.mock("../../src/lib/riskManager.js", () => ({
  computeSizing: vi.fn(),
}));

vi.mock("../../src/lib/exchange/instrumentCache.js", () => ({
  getInstrument: vi.fn(),
}));

vi.mock("../../src/lib/exchange/normalizer.js", () => ({
  normalizeOrder: vi.fn(),
}));

vi.mock("../../src/lib/runtime/positionSizer.js", () => ({
  sizeOrder: vi.fn(),
}));

vi.mock("../../src/lib/runtime/dcaBridge.js", () => ({
  extractDcaConfig: vi.fn(),
  extractSlPct: vi.fn(),
  initializeDcaLadder: vi.fn(),
  handleDcaBaseFill: vi.fn(),
  handleDcaSoFill: vi.fn(),
  finalizeDcaLadder: vi.fn(),
  recoverDcaState: vi.fn().mockReturnValue(null),
  checkAndTriggerSOs: vi.fn(),
}));

vi.mock("../../src/lib/runtime/dcaEngine.js", () => ({
  serializeDcaState: vi.fn(),
}));

vi.mock("../../src/lib/recoveryManager.js", () => ({
  reconstructRunState: vi.fn().mockReturnValue({
    trailingStopState: null,
    lastTradeCloseTime: 0,
  }),
}));

vi.mock("../../src/lib/stateReconciler.js", () => ({
  reconcileStartupState: vi.fn().mockReturnValue({
    toCancel: [],
    toMonitor: [],
    summary: "clean",
    counts: { pending: 0, placed: 0, cancelled: 0, failed: 0, filled: 0 },
  }),
  detectStartupInconsistencies: vi.fn().mockReturnValue([]),
}));

vi.mock("../../src/lib/errorClassifier.js", () => ({
  classifyExecutionError: vi.fn().mockReturnValue({ category: "UNKNOWN", retryable: false }),
}));

vi.mock("../../src/lib/safetyGuards.js", () => ({
  parseDailyLossConfig: vi.fn(),
  parseGuardsConfig: vi.fn(),
  shouldTriggerDailyLossLimit: vi.fn().mockReturnValue(false),
  shouldPauseOnError: vi.fn().mockReturnValue(false),
  DEFAULT_ERROR_PAUSE_THRESHOLD: 3,
}));

vi.mock("../../src/lib/notify.js", () => ({
  notifyRunEvent: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Import the real functions (after mocks are set up)
// ---------------------------------------------------------------------------

import {
  _activateRun as activateRun,
  _timeoutExpiredRuns as timeoutExpiredRuns,
  _stopRun as stopRun,
  _processIntents as processIntents,
  _executeIntent as executeIntent,
  _reconcilePlacedIntents as reconcilePlacedIntents,
} from "../../src/lib/botWorker.js";

import { bybitPlaceOrder, bybitGetOrderStatus, mapBybitStatus } from "../../src/lib/bybitOrder.js";
import { classifyExecutionError } from "../../src/lib/errorClassifier.js";
import { getInstrument } from "../../src/lib/exchange/instrumentCache.js";
import { normalizeOrder } from "../../src/lib/exchange/normalizer.js";
import { getActivePosition } from "../../src/lib/positionManager.js";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("activateRun (real function)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTransition.mockResolvedValue(undefined);
    mockBotRunUpdate.mockResolvedValue(undefined);
    mockBotUpdate.mockResolvedValue(undefined);
    mockBotRunCount.mockResolvedValue(0);
    mockBotEventCreate.mockResolvedValue(undefined);
  });

  it("transitions through STARTING → SYNCING → RUNNING on success", async () => {
    const runId = "run-001";
    // After STARTING transition, findUnique returns STARTING state
    mockBotRunFindUnique
      .mockResolvedValueOnce({ id: runId, state: "STARTING", botId: "bot-1" })
      // After SYNCING transition, findUnique returns SYNCING state with bot
      .mockResolvedValueOnce({
        id: runId,
        state: "SYNCING",
        botId: "bot-1",
        bot: { id: "bot-1", symbol: "BTCUSDT" },
      });

    await activateRun(runId);

    // Verify all three transitions were called
    expect(mockTransition).toHaveBeenCalledTimes(3);
    expect(mockTransition).toHaveBeenNthCalledWith(1, runId, "STARTING", expect.objectContaining({
      eventType: "RUN_STARTING",
    }));
    expect(mockTransition).toHaveBeenNthCalledWith(2, runId, "SYNCING", expect.objectContaining({
      eventType: "RUN_SYNCING",
    }));
    expect(mockTransition).toHaveBeenNthCalledWith(3, runId, "RUNNING", expect.objectContaining({
      eventType: "RUN_RUNNING",
    }));
  });

  it("transitions to FAILED when an error occurs during activation", async () => {
    const runId = "run-002";
    // First transition (STARTING) succeeds, second one throws
    mockTransition
      .mockResolvedValueOnce(undefined) // STARTING
      .mockRejectedValueOnce(new Error("DB connection lost")) // SYNCING fails
      .mockResolvedValueOnce(undefined); // FAILED transition in catch

    // findUnique after STARTING returns STARTING state
    mockBotRunFindUnique
      .mockResolvedValueOnce({ id: runId, state: "STARTING", botId: "bot-1" })
      // catch block queries for workspaceId/symbol for notification
      .mockResolvedValueOnce({ id: runId, workspaceId: "ws-1", symbol: "BTCUSDT" });

    await activateRun(runId);

    // The catch block should transition to FAILED
    const failedCall = mockTransition.mock.calls.find((c) => c[1] === "FAILED");
    expect(failedCall).toBeDefined();
    expect(failedCall![2]).toMatchObject({
      eventType: "RUN_FAILED",
      errorCode: "ACTIVATE_CRASH",
    });
    expect(failedCall![2].message).toContain("DB connection lost");
  });

  it("aborts if run state changed during STARTING (e.g. user stopped)", async () => {
    const runId = "run-003";
    mockTransition.mockResolvedValue(undefined);
    // After STARTING, findUnique shows STOPPING (user stopped it)
    mockBotRunFindUnique.mockResolvedValueOnce({
      id: runId,
      state: "STOPPING",
      botId: "bot-1",
    });

    await activateRun(runId);

    // Should only have one transition (STARTING), then abort
    expect(mockTransition).toHaveBeenCalledTimes(1);
    expect(mockTransition).toHaveBeenCalledWith(runId, "STARTING", expect.anything());
  });

  it("aborts if run state changed during SYNCING (e.g. user stopped)", async () => {
    const runId = "run-004";
    mockTransition.mockResolvedValue(undefined);
    // STARTING → ok
    mockBotRunFindUnique
      .mockResolvedValueOnce({ id: runId, state: "STARTING", botId: "bot-1" })
      // After SYNCING, state is STOPPING
      .mockResolvedValueOnce({
        id: runId,
        state: "STOPPING",
        botId: "bot-1",
        bot: { id: "bot-1", symbol: "BTCUSDT" },
      });

    await activateRun(runId);

    // Should have STARTING + SYNCING transitions, then abort (no RUNNING)
    expect(mockTransition).toHaveBeenCalledTimes(2);
  });

  it("handles transition to FAILED also failing (double fault)", async () => {
    const runId = "run-005";
    // First transition throws → catch block → transition to FAILED also throws
    mockTransition
      .mockRejectedValueOnce(new Error("Initial crash"))
      .mockRejectedValueOnce(new Error("Cannot transition"));

    // catch block queries for workspaceId/symbol for notification
    mockBotRunFindUnique.mockResolvedValueOnce({ id: runId, workspaceId: "ws-1", symbol: "BTCUSDT" });

    // Should not throw — double fault is logged but swallowed
    await expect(activateRun(runId)).resolves.toBeUndefined();
  });
});

describe("timeoutExpiredRuns (real function)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTransition.mockResolvedValue(undefined);
    mockBotRunCount.mockResolvedValue(0);
    mockBotUpdate.mockResolvedValue(undefined);
  });

  it("marks stuck STARTING runs as FAILED (ephemeral timeout)", async () => {
    const stuckRun = {
      id: "run-stuck-starting",
      botId: "bot-1",
      state: "STARTING",
      updatedAt: new Date(Date.now() - 10 * 60 * 1000), // 10 min ago
    };

    mockBotRunFindMany
      .mockResolvedValueOnce([stuckRun]) // ephemeral query
      .mockResolvedValueOnce([]); // RUNNING query

    await timeoutExpiredRuns();

    expect(mockTransition).toHaveBeenCalledWith(
      "run-stuck-starting",
      "FAILED",
      expect.objectContaining({
        errorCode: "EPHEMERAL_STATE_TIMEOUT",
        message: expect.stringContaining("stuck in STARTING"),
      }),
    );
  });

  it("marks stuck SYNCING runs as FAILED", async () => {
    const stuckRun = {
      id: "run-stuck-syncing",
      botId: "bot-2",
      state: "SYNCING",
      updatedAt: new Date(Date.now() - 8 * 60 * 1000),
    };

    mockBotRunFindMany
      .mockResolvedValueOnce([stuckRun])
      .mockResolvedValueOnce([]);

    await timeoutExpiredRuns();

    expect(mockTransition).toHaveBeenCalledWith(
      "run-stuck-syncing",
      "FAILED",
      expect.objectContaining({
        errorCode: "EPHEMERAL_STATE_TIMEOUT",
      }),
    );
  });

  it("times out RUNNING runs that exceeded max duration", async () => {
    const oldRun = {
      id: "run-old-running",
      botId: "bot-3",
      startedAt: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
      durationMinutes: null,
    };

    mockBotRunFindMany
      .mockResolvedValueOnce([]) // no ephemeral
      .mockResolvedValueOnce([oldRun]); // RUNNING query

    await timeoutExpiredRuns();

    expect(mockTransition).toHaveBeenCalledWith(
      "run-old-running",
      "TIMED_OUT",
      expect.objectContaining({
        eventType: "RUN_TIMED_OUT",
      }),
    );
  });

  it("respects per-run durationMinutes", async () => {
    const recentRun = {
      id: "run-short-running",
      botId: "bot-4",
      startedAt: new Date(Date.now() - 20 * 60 * 1000), // 20 min ago
      durationMinutes: 15, // Custom: 15 min
    };

    mockBotRunFindMany
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([recentRun]);

    await timeoutExpiredRuns();

    // 20 min > 15 min custom duration → should timeout
    expect(mockTransition).toHaveBeenCalledWith(
      "run-short-running",
      "TIMED_OUT",
      expect.anything(),
    );
  });

  it("does NOT timeout a RUNNING run within its duration", async () => {
    const freshRun = {
      id: "run-fresh",
      botId: "bot-5",
      startedAt: new Date(Date.now() - 30 * 60 * 1000), // 30 min ago
      durationMinutes: null, // default 4 hours
    };

    mockBotRunFindMany
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([freshRun]);

    await timeoutExpiredRuns();

    // 30 min < 4 hours → no transition
    expect(mockTransition).not.toHaveBeenCalled();
  });

  it("handles transition errors gracefully", async () => {
    const stuckRun = {
      id: "run-stuck",
      botId: "bot-6",
      state: "STARTING",
      updatedAt: new Date(Date.now() - 10 * 60 * 1000),
    };

    mockBotRunFindMany
      .mockResolvedValueOnce([stuckRun])
      .mockResolvedValueOnce([]);

    mockTransition.mockRejectedValueOnce(new Error("Already transitioned"));

    // Should not throw
    await expect(timeoutExpiredRuns()).resolves.toBeUndefined();
  });
});

describe("stopRun (real function)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTransition.mockResolvedValue(undefined);
    mockBotRunCount.mockResolvedValue(0);
    mockBotUpdate.mockResolvedValue(undefined);
  });

  it("transitions STOPPING → STOPPED", async () => {
    mockBotRunFindUnique.mockResolvedValueOnce({
      id: "run-stop",
      state: "STOPPING",
      botId: "bot-1",
    });

    await stopRun("run-stop");

    expect(mockTransition).toHaveBeenCalledWith(
      "run-stop",
      "STOPPED",
      expect.objectContaining({
        eventType: "RUN_STOPPED",
      }),
    );
  });

  it("does nothing if run is not in STOPPING state", async () => {
    mockBotRunFindUnique.mockResolvedValueOnce({
      id: "run-running",
      state: "RUNNING",
      botId: "bot-2",
    });

    await stopRun("run-running");

    expect(mockTransition).not.toHaveBeenCalled();
  });

  it("does nothing if run not found", async () => {
    mockBotRunFindUnique.mockResolvedValueOnce(null);

    await stopRun("run-nonexistent");

    expect(mockTransition).not.toHaveBeenCalled();
  });

  it("handles errors gracefully", async () => {
    mockBotRunFindUnique.mockRejectedValueOnce(new Error("DB error"));

    await expect(stopRun("run-err")).resolves.toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// executeIntent tests (B3, issue #216)
// ---------------------------------------------------------------------------

describe("executeIntent (real function)", () => {
  const demoIntent = {
    id: "intent-1",
    intentId: "int-uuid-1",
    orderLinkId: "link-1",
    side: "BUY",
    qty: { toString: () => "0.01" },
    price: { toString: () => "50000" },
    retryCount: 0,
    metaJson: {},
    botRun: {
      id: "run-1",
      bot: {
        id: "bot-1",
        symbol: "BTCUSDT",
        exchangeConnectionId: null,
        exchangeConnection: null,
        strategyVersion: { dslJson: { enabled: true } },
      },
    },
  };

  const liveIntent = {
    ...demoIntent,
    botRun: {
      id: "run-1",
      bot: {
        id: "bot-1",
        symbol: "BTCUSDT",
        exchangeConnectionId: "exc-1",
        exchangeConnection: {
          apiKey: "test-api-key",
          encryptedSecret: "encrypted-secret",
        },
        strategyVersion: { dslJson: { enabled: true } },
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockBotIntentUpdateMany.mockResolvedValue({ count: 1 });
    mockBotIntentUpdate.mockResolvedValue(undefined);
    mockBotEventCreate.mockResolvedValue(undefined);
  });

  it("simulates fill in demo mode (no exchangeConnection)", async () => {
    await executeIntent(demoIntent);

    // Should claim intent atomically (PENDING → PLACED)
    expect(mockBotIntentUpdateMany).toHaveBeenCalledWith({
      where: { id: "intent-1", state: "PENDING" },
      data: { state: "PLACED" },
    });

    // Should mark as FILLED with simulated meta
    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1" },
        data: expect.objectContaining({
          state: "FILLED",
          metaJson: expect.objectContaining({ simulated: true }),
        }),
      }),
    );

    // Should create intent_simulated event
    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          botRunId: "run-1",
          type: "intent_simulated",
        }),
      }),
    );
  });

  it("skips silently when another worker claimed the intent", async () => {
    mockBotIntentUpdateMany.mockResolvedValue({ count: 0 });

    await executeIntent(demoIntent);

    expect(mockBotIntentUpdate).not.toHaveBeenCalled();
    expect(mockBotEventCreate).not.toHaveBeenCalled();
  });

  it("places order on Bybit in live mode", async () => {
    vi.mocked(getInstrument).mockResolvedValue({} as never);
    vi.mocked(normalizeOrder).mockReturnValue({
      valid: true,
      order: { qty: "0.01", price: "50000", diagnostics: {} },
    } as never);
    vi.mocked(bybitPlaceOrder).mockResolvedValue({
      orderId: "bybit-order-123",
      orderLinkId: "link-1",
    });

    await executeIntent(liveIntent);

    expect(vi.mocked(bybitPlaceOrder)).toHaveBeenCalledWith(
      "test-api-key",
      "decrypted-secret",
      expect.objectContaining({
        symbol: "BTCUSDT",
        side: "Buy",
        orderType: "Market",
        qty: "0.01",
      }),
    );

    // Should save orderId in intent
    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1" },
        data: expect.objectContaining({
          orderId: "bybit-order-123",
        }),
      }),
    );

    // Should create intent_placed event
    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: "intent_placed",
          payloadJson: expect.objectContaining({
            orderId: "bybit-order-123",
          }),
        }),
      }),
    );
  });

  it("retries on transient error when retryCount < MAX", async () => {
    vi.mocked(getInstrument).mockResolvedValue({} as never);
    vi.mocked(normalizeOrder).mockReturnValue({
      valid: true,
      order: { qty: "0.01", diagnostics: {} },
    } as never);
    vi.mocked(bybitPlaceOrder).mockRejectedValue(new Error("rate limit hit"));
    vi.mocked(classifyExecutionError).mockReturnValue({
      retryable: true,
      errorClass: "RATE_LIMIT",
      reason: "rate limited",
      category: "TRANSIENT",
    } as never);

    const retryIntent = { ...liveIntent, retryCount: 1 };
    await executeIntent(retryIntent);

    // Should put back to PENDING with incremented retryCount
    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1" },
        data: expect.objectContaining({
          state: "PENDING",
          retryCount: 2,
        }),
      }),
    );

    // Should create intent_retry event
    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: "intent_retry",
          payloadJson: expect.objectContaining({
            retryAttempt: 2,
          }),
        }),
      }),
    );
  });

  it("dead-letters when max retries exhausted", async () => {
    vi.mocked(getInstrument).mockResolvedValue({} as never);
    vi.mocked(normalizeOrder).mockReturnValue({
      valid: true,
      order: { qty: "0.01", diagnostics: {} },
    } as never);
    vi.mocked(bybitPlaceOrder).mockRejectedValue(new Error("timeout"));
    vi.mocked(classifyExecutionError).mockReturnValue({
      retryable: true,
      errorClass: "TIMEOUT",
      reason: "request timeout",
      category: "TRANSIENT",
    } as never);

    // MAX_INTENT_RETRIES defaults to 3; retryCount=3 means exhausted
    const exhaustedIntent = { ...liveIntent, retryCount: 3 };
    await executeIntent(exhaustedIntent);

    // Should set to FAILED (dead-letter)
    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1" },
        data: expect.objectContaining({
          state: "FAILED",
          metaJson: expect.objectContaining({
            deadLetterReason: expect.stringContaining("max retries exhausted"),
          }),
        }),
      }),
    );

    // Should create intent_dead_lettered event
    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: "intent_dead_lettered",
        }),
      }),
    );
  });

  it("fails immediately on permanent error", async () => {
    vi.mocked(getInstrument).mockResolvedValue({} as never);
    vi.mocked(normalizeOrder).mockReturnValue({
      valid: true,
      order: { qty: "0.01", diagnostics: {} },
    } as never);
    vi.mocked(bybitPlaceOrder).mockRejectedValue(new Error("insufficient balance"));
    vi.mocked(classifyExecutionError).mockReturnValue({
      retryable: false,
      errorClass: "INSUFFICIENT_BALANCE",
      reason: "not enough funds",
      category: "PERMANENT",
    } as never);

    await executeIntent(liveIntent);

    // Should set to FAILED immediately
    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1" },
        data: expect.objectContaining({
          state: "FAILED",
          metaJson: expect.objectContaining({
            retryable: false,
            errorClass: "INSUFFICIENT_BALANCE",
          }),
        }),
      }),
    );

    // Should create intent_failed event (not dead_lettered)
    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: "intent_failed",
        }),
      }),
    );
  });
});

// ---------------------------------------------------------------------------
// processIntents tests (B3, issue #216)
// ---------------------------------------------------------------------------

describe("processIntents (real function)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBotIntentFindMany.mockResolvedValue([]);
    mockBotIntentUpdateMany.mockResolvedValue({ count: 1 });
    mockBotIntentUpdate.mockResolvedValue(undefined);
    mockBotEventCreate.mockResolvedValue(undefined);
  });

  it("cancels intents when strategy has enabled: false", async () => {
    mockBotIntentFindMany.mockResolvedValue([
      {
        id: "intent-disabled-1",
        intentId: "uuid-dis-1",
        orderLinkId: "link-dis-1",
        side: "BUY",
        qty: { toString: () => "0.01" },
        price: { toString: () => "50000" },
        retryCount: 0,
        metaJson: {},
        state: "PENDING",
        botRun: {
          id: "run-1",
          state: "RUNNING",
          bot: {
            id: "bot-1",
            symbol: "BTCUSDT",
            exchangeConnectionId: null,
            exchangeConnection: null,
            strategyVersion: { dslJson: { enabled: false } },
          },
        },
      },
    ]);

    await processIntents();

    // Should cancel the intent
    expect(mockBotIntentUpdateMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-disabled-1", state: "PENDING" },
        data: expect.objectContaining({
          state: "CANCELLED",
          metaJson: expect.objectContaining({ reason: "strategy_disabled" }),
        }),
      }),
    );

    // Should create intent_cancelled event
    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          botRunId: "run-1",
          type: "intent_cancelled",
          payloadJson: expect.objectContaining({
            reason: expect.stringContaining("strategy disabled"),
          }),
        }),
      }),
    );
  });

  it("executes enabled intents (demo mode path)", async () => {
    mockBotIntentFindMany.mockResolvedValue([
      {
        id: "intent-active-1",
        intentId: "uuid-act-1",
        orderLinkId: "link-act-1",
        side: "SELL",
        qty: { toString: () => "0.5" },
        price: null,
        retryCount: 0,
        metaJson: {},
        state: "PENDING",
        botRun: {
          id: "run-2",
          state: "RUNNING",
          bot: {
            id: "bot-2",
            symbol: "ETHUSDT",
            exchangeConnectionId: null,
            exchangeConnection: null,
            strategyVersion: { dslJson: { enabled: true } },
          },
        },
      },
    ]);

    await processIntents();

    // Should claim intent (atomic lock from executeIntent)
    expect(mockBotIntentUpdateMany).toHaveBeenCalledWith({
      where: { id: "intent-active-1", state: "PENDING" },
      data: { state: "PLACED" },
    });

    // Should mark as FILLED (demo mode simulated)
    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ state: "FILLED" }),
      }),
    );
  });

  it("handles empty result (no pending intents) without errors", async () => {
    mockBotIntentFindMany.mockResolvedValue([]);

    await processIntents();

    expect(mockBotIntentUpdateMany).not.toHaveBeenCalled();
    expect(mockBotIntentUpdate).not.toHaveBeenCalled();
    expect(mockBotEventCreate).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// reconcilePlacedIntents tests (B3, issue #216)
// ---------------------------------------------------------------------------

describe("reconcilePlacedIntents (real function)", () => {
  const makePlacedIntent = (overrides: Record<string, unknown> = {}) => ({
    id: "intent-placed-1",
    intentId: "uuid-placed-1",
    orderLinkId: "link-placed-1",
    orderId: "bybit-order-1",
    side: "BUY",
    type: "ENTRY",
    state: "PLACED",
    qty: { toString: () => "1.0", toNumber: () => 1.0 },
    price: { toString: () => "50000", toNumber: () => 50000 },
    cumExecQty: null,
    retryCount: 0,
    metaJson: {},
    botRun: {
      id: "run-1",
      state: "RUNNING",
      bot: {
        id: "bot-1",
        symbol: "BTCUSDT",
        exchangeConnectionId: "exc-1",
        exchangeConnection: {
          apiKey: "test-api-key",
          encryptedSecret: "encrypted-secret",
        },
      },
    },
    ...overrides,
  });

  beforeEach(() => {
    vi.clearAllMocks();
    mockBotIntentFindMany.mockResolvedValue([]);
    mockBotIntentUpdate.mockResolvedValue(undefined);
    mockBotEventCreate.mockResolvedValue(undefined);
    vi.mocked(getActivePosition).mockResolvedValue(null);
  });

  it("updates intent to FILLED on full fill", async () => {
    mockBotIntentFindMany.mockResolvedValue([makePlacedIntent()]);
    vi.mocked(bybitGetOrderStatus).mockResolvedValue({
      orderId: "bybit-order-1",
      symbol: "BTCUSDT",
      side: "Buy",
      orderType: "Market",
      qty: "1.0",
      price: "50000",
      avgPrice: "50100",
      cumExecQty: "1.0",
      orderStatus: "Filled",
      createdTime: "1700000000000",
      updatedTime: "1700000001000",
    });
    vi.mocked(mapBybitStatus).mockReturnValue("FILLED");

    await reconcilePlacedIntents();

    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-placed-1" },
        data: expect.objectContaining({
          state: "FILLED",
          cumExecQty: 1.0,
          avgFillPrice: 50100,
        }),
      }),
    );

    expect(mockBotEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: "intent_reconciled",
          payloadJson: expect.objectContaining({
            newState: "FILLED",
            fillDelta: 1.0,
          }),
        }),
      }),
    );
  });

  it("updates intent to PARTIALLY_FILLED on partial fill", async () => {
    mockBotIntentFindMany.mockResolvedValue([makePlacedIntent()]);
    vi.mocked(bybitGetOrderStatus).mockResolvedValue({
      orderId: "bybit-order-1",
      symbol: "BTCUSDT",
      side: "Buy",
      orderType: "Market",
      qty: "1.0",
      price: "50000",
      avgPrice: "50050",
      cumExecQty: "0.5",
      orderStatus: "PartiallyFilled",
      createdTime: "1700000000000",
      updatedTime: "1700000001000",
    });
    vi.mocked(mapBybitStatus).mockReturnValue("PARTIALLY_FILLED");

    await reconcilePlacedIntents();

    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-placed-1" },
        data: expect.objectContaining({
          state: "PARTIALLY_FILLED",
          cumExecQty: 0.5,
          avgFillPrice: 50050,
        }),
      }),
    );
  });

  it("cancels intent when exchange order is CANCELLED", async () => {
    mockBotIntentFindMany.mockResolvedValue([makePlacedIntent()]);
    vi.mocked(bybitGetOrderStatus).mockResolvedValue({
      orderId: "bybit-order-1",
      symbol: "BTCUSDT",
      side: "Buy",
      orderType: "Limit",
      qty: "1.0",
      price: "50000",
      avgPrice: "0",
      cumExecQty: "0",
      orderStatus: "Cancelled",
      createdTime: "1700000000000",
      updatedTime: "1700000001000",
    });
    vi.mocked(mapBybitStatus).mockReturnValue("CANCELLED");

    await reconcilePlacedIntents();

    expect(mockBotIntentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-placed-1" },
        data: expect.objectContaining({
          state: "CANCELLED",
        }),
      }),
    );
  });

  it("skips intents without exchange connection", async () => {
    mockBotIntentFindMany.mockResolvedValue([
      makePlacedIntent({
        botRun: {
          id: "run-1",
          state: "RUNNING",
          bot: {
            id: "bot-1",
            symbol: "BTCUSDT",
            exchangeConnectionId: null,
            exchangeConnection: null,
          },
        },
      }),
    ]);

    await reconcilePlacedIntents();

    expect(vi.mocked(bybitGetOrderStatus)).not.toHaveBeenCalled();
    expect(mockBotIntentUpdate).not.toHaveBeenCalled();
  });

  it("handles exchange API errors gracefully (non-fatal)", async () => {
    mockBotIntentFindMany.mockResolvedValue([makePlacedIntent()]);
    vi.mocked(bybitGetOrderStatus).mockRejectedValue(new Error("network timeout"));

    await reconcilePlacedIntents();

    // Should not throw, should not update intent
    expect(mockBotIntentUpdate).not.toHaveBeenCalled();
  });
});
