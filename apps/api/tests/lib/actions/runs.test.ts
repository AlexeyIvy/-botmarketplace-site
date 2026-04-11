/**
 * actions/runs.ts — unit tests
 * Tests startRun/stopRun validation, workspace scoping, single-active-run invariant,
 * and state machine integration.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockBotFindUnique = vi.fn();
const mockBotRunFindFirst = vi.fn();
const mockBotRunFindUnique = vi.fn();
const mockBotRunCreate = vi.fn();
const mockBotEventCreate = vi.fn();
const mockTransaction = vi.fn();
const mockTransition = vi.fn();
const mockIsTerminalState = vi.fn();
const mockIsValidTransition = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../../src/lib/prisma.js", () => ({
  prisma: {
    bot: {
      findUnique: (...args: unknown[]) => mockBotFindUnique(...args),
    },
    botRun: {
      findFirst: (...args: unknown[]) => mockBotRunFindFirst(...args),
      findUnique: (...args: unknown[]) => mockBotRunFindUnique(...args),
      create: (...args: unknown[]) => mockBotRunCreate(...args),
    },
    botEvent: {
      create: (...args: unknown[]) => mockBotEventCreate(...args),
    },
    $transaction: (fn: (tx: unknown) => Promise<unknown>) => {
      const tx = {
        botRun: {
          create: (...args: unknown[]) => mockBotRunCreate(...args),
        },
        botEvent: {
          create: (...args: unknown[]) => mockBotEventCreate(...args),
        },
      };
      return fn(tx);
    },
  },
}));

vi.mock("../../../src/lib/stateMachine.js", () => {
  class InvalidTransitionError extends Error {
    from: string;
    to: string;
    constructor(from: string, to: string) {
      super(`Invalid state transition: ${from} → ${to}`);
      this.name = "InvalidTransitionError";
      this.from = from;
      this.to = to;
    }
  }
  return {
    transition: (...args: unknown[]) => mockTransition(...args),
    isTerminalState: (...args: unknown[]) => mockIsTerminalState(...args),
    isValidTransition: (...args: unknown[]) => mockIsValidTransition(...args),
    InvalidTransitionError,
  };
});

import { startRun, stopRun, ActionValidationError, ActionConflictError, ActionNotFoundError } from "../../../src/lib/actions/runs.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WS = "ws-test-1";
const OTHER_WS = "ws-other";
const BOT_ID = "bot-1";
const RUN_ID = "run-1";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// startRun tests
// ---------------------------------------------------------------------------

describe("startRun", () => {
  // ── Input validation ──────────────────────────────────────────────────

  it("throws ActionValidationError when botId is missing", async () => {
    await expect(startRun(WS, {}))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when botId is not a string", async () => {
    await expect(startRun(WS, { botId: 123 }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError for invalid durationMinutes (float)", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    await expect(startRun(WS, { botId: BOT_ID, durationMinutes: 5.5 }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError for durationMinutes < 1", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    await expect(startRun(WS, { botId: BOT_ID, durationMinutes: 0 }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError for durationMinutes > 1440", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    await expect(startRun(WS, { botId: BOT_ID, durationMinutes: 1441 }))
      .rejects.toThrow(ActionValidationError);
  });

  // ── Cross-workspace ───────────────────────────────────────────────────

  it("throws ActionNotFoundError when bot not found", async () => {
    mockBotFindUnique.mockResolvedValue(null);
    await expect(startRun(WS, { botId: BOT_ID }))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when bot belongs to another workspace", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: OTHER_WS });
    await expect(startRun(WS, { botId: BOT_ID }))
      .rejects.toThrow(ActionNotFoundError);
  });

  // ── Single-active-run invariant ───────────────────────────────────────

  it("throws ActionConflictError when an active run exists", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    mockBotRunFindFirst.mockResolvedValue({ id: "run-active", state: "RUNNING" });
    await expect(startRun(WS, { botId: BOT_ID }))
      .rejects.toThrow(ActionConflictError);
  });

  // ── Happy path ────────────────────────────────────────────────────────

  it("creates run in CREATED state, transitions to QUEUED, returns result", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    mockBotRunFindFirst.mockResolvedValue(null);
    mockBotRunCreate.mockResolvedValue({
      id: RUN_ID,
      botId: BOT_ID,
      workspaceId: WS,
      symbol: "BTCUSDT",
      state: "CREATED",
    });
    mockBotEventCreate.mockResolvedValue({});
    mockTransition.mockResolvedValue({ id: RUN_ID, state: "QUEUED" });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, state: "QUEUED" });

    const result = await startRun(WS, { botId: BOT_ID });
    expect(result).toEqual({ runId: RUN_ID, state: "QUEUED" });
    expect(mockTransition).toHaveBeenCalledWith(
      RUN_ID,
      "QUEUED",
      expect.objectContaining({ eventType: "RUN_QUEUED" }),
    );
  });

  it("passes durationMinutes to created run when provided", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    mockBotRunFindFirst.mockResolvedValue(null);
    mockBotRunCreate.mockResolvedValue({
      id: RUN_ID,
      state: "CREATED",
    });
    mockBotEventCreate.mockResolvedValue({});
    mockTransition.mockResolvedValue({ id: RUN_ID, state: "QUEUED" });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, state: "QUEUED" });

    await startRun(WS, { botId: BOT_ID, durationMinutes: 60 });

    expect(mockBotRunCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ durationMinutes: 60 }),
      }),
    );
  });

  it("allows null durationMinutes", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS, symbol: "BTCUSDT" });
    mockBotRunFindFirst.mockResolvedValue(null);
    mockBotRunCreate.mockResolvedValue({
      id: RUN_ID,
      state: "CREATED",
    });
    mockBotEventCreate.mockResolvedValue({});
    mockTransition.mockResolvedValue({ id: RUN_ID, state: "QUEUED" });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, state: "QUEUED" });

    await startRun(WS, { botId: BOT_ID, durationMinutes: null });

    expect(mockBotRunCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ durationMinutes: null }),
      }),
    );
  });
});

// ---------------------------------------------------------------------------
// stopRun tests
// ---------------------------------------------------------------------------

describe("stopRun", () => {
  // ── Input validation ──────────────────────────────────────────────────

  it("throws ActionValidationError when botId is missing", async () => {
    await expect(stopRun(WS, { runId: RUN_ID }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when runId is missing", async () => {
    await expect(stopRun(WS, { botId: BOT_ID }))
      .rejects.toThrow(ActionValidationError);
  });

  // ── Cross-workspace ───────────────────────────────────────────────────

  it("throws ActionNotFoundError when bot not found", async () => {
    mockBotFindUnique.mockResolvedValue(null);
    await expect(stopRun(WS, { botId: BOT_ID, runId: RUN_ID }))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when bot belongs to another workspace", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: OTHER_WS });
    await expect(stopRun(WS, { botId: BOT_ID, runId: RUN_ID }))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when run not found", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS });
    mockBotRunFindUnique.mockResolvedValue(null);
    await expect(stopRun(WS, { botId: BOT_ID, runId: RUN_ID }))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when run belongs to another bot", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, botId: "bot-other" });
    await expect(stopRun(WS, { botId: BOT_ID, runId: RUN_ID }))
      .rejects.toThrow(ActionNotFoundError);
  });

  // ── Terminal state ────────────────────────────────────────────────────

  it("throws ActionConflictError when run is in terminal state", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, botId: BOT_ID, state: "STOPPED" });
    mockIsTerminalState.mockReturnValue(true);
    await expect(stopRun(WS, { botId: BOT_ID, runId: RUN_ID }))
      .rejects.toThrow(ActionConflictError);
  });

  // ── Happy path: via STOPPING ──────────────────────────────────────────

  it("transitions through STOPPING then STOPPED when valid", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, botId: BOT_ID, state: "RUNNING" });
    mockIsTerminalState.mockReturnValue(false);
    mockIsValidTransition.mockReturnValue(true);
    mockTransition
      .mockResolvedValueOnce({ id: RUN_ID, state: "STOPPING" })
      .mockResolvedValueOnce({ id: RUN_ID, state: "STOPPED" });

    const result = await stopRun(WS, { botId: BOT_ID, runId: RUN_ID });
    expect(result).toEqual({ runId: RUN_ID, state: "STOPPED" });
    expect(mockTransition).toHaveBeenCalledTimes(2);
  });

  // ── Happy path: direct STOPPED ────────────────────────────────────────

  it("transitions directly to STOPPED when STOPPING is not valid", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, botId: BOT_ID, state: "CREATED" });
    mockIsTerminalState.mockReturnValue(false);
    mockIsValidTransition.mockReturnValue(false);
    mockTransition.mockResolvedValue({ id: RUN_ID, state: "STOPPED" });

    const result = await stopRun(WS, { botId: BOT_ID, runId: RUN_ID });
    expect(result).toEqual({ runId: RUN_ID, state: "STOPPED" });
    expect(mockTransition).toHaveBeenCalledTimes(1);
  });

  // ── InvalidTransitionError wrapping ───────────────────────────────────

  it("wraps InvalidTransitionError as ActionConflictError", async () => {
    mockBotFindUnique.mockResolvedValue({ id: BOT_ID, workspaceId: WS });
    mockBotRunFindUnique.mockResolvedValue({ id: RUN_ID, botId: BOT_ID, state: "RUNNING" });
    mockIsTerminalState.mockReturnValue(false);
    mockIsValidTransition.mockReturnValue(true);

    // Import the mocked InvalidTransitionError
    const { InvalidTransitionError } = await import("../../../src/lib/stateMachine.js");
    mockTransition.mockRejectedValue(new InvalidTransitionError("RUNNING" as never, "STOPPING" as never));

    await expect(stopRun(WS, { botId: BOT_ID, runId: RUN_ID }))
      .rejects.toThrow(ActionConflictError);
  });
});
