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

vi.mock("../../src/lib/logger.js", () => ({
  logger: {
    child: () => ({
      info: vi.fn(),
      warn: vi.fn(),
      error: vi.fn(),
      debug: vi.fn(),
    }),
  },
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

// ---------------------------------------------------------------------------
// Import the real functions (after mocks are set up)
// ---------------------------------------------------------------------------

import {
  _activateRun as activateRun,
  _timeoutExpiredRuns as timeoutExpiredRuns,
  _stopRun as stopRun,
} from "../../src/lib/botWorker.js";

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
    mockBotRunFindUnique.mockResolvedValueOnce({ id: runId, state: "STARTING", botId: "bot-1" });

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
