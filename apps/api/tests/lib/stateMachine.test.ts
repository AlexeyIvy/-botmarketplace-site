/**
 * stateMachine.ts — optimistic locking tests (Roadmap V3, Task #20)
 *
 * Tests that transition() uses version-based optimistic locking
 * to prevent race conditions on concurrent state transitions.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockFindUnique = vi.fn();
const mockUpdateMany = vi.fn();
const mockFindUniqueOrThrow = vi.fn();
const mockEventCreate = vi.fn();
const mockTransaction = vi.fn();

vi.mock("@prisma/client", () => ({
  Prisma: {
    sql: vi.fn(),
    join: vi.fn(),
  },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    botRun: {
      findUnique: (...args: unknown[]) => mockFindUnique(...args),
    },
    $transaction: (fn: (tx: unknown) => Promise<unknown>) => {
      const tx = {
        botRun: {
          updateMany: (...args: unknown[]) => mockUpdateMany(...args),
          findUniqueOrThrow: (...args: unknown[]) => mockFindUniqueOrThrow(...args),
        },
        botEvent: {
          create: (...args: unknown[]) => mockEventCreate(...args),
        },
      };
      return fn(tx);
    },
  },
}));

import {
  transition,
  isValidTransition,
  isTerminalState,
  InvalidTransitionError,
  RunNotFoundError,
  StaleStateError,
  TERMINAL_STATES,
} from "../../src/lib/stateMachine.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeRun(overrides: Record<string, unknown> = {}) {
  return {
    id: "run-1",
    botId: "bot-1",
    workspaceId: "ws-1",
    symbol: "BTCUSDT",
    state: "QUEUED",
    version: 0,
    leaseOwner: null,
    leaseUntil: null,
    startedAt: null,
    stoppedAt: null,
    errorCode: null,
    durationMinutes: null,
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Pure function tests (no Prisma needed)
// ---------------------------------------------------------------------------

describe("isValidTransition", () => {
  it("allows QUEUED → STARTING", () => {
    expect(isValidTransition("QUEUED", "STARTING")).toBe(true);
  });

  it("allows RUNNING → FAILED", () => {
    expect(isValidTransition("RUNNING", "FAILED")).toBe(true);
  });

  it("rejects FAILED → RUNNING (terminal state)", () => {
    expect(isValidTransition("FAILED", "RUNNING")).toBe(false);
  });

  it("rejects STOPPED → anything", () => {
    expect(isValidTransition("STOPPED", "RUNNING")).toBe(false);
    expect(isValidTransition("STOPPED", "FAILED")).toBe(false);
  });
});

describe("isTerminalState", () => {
  it("STOPPED is terminal", () => expect(isTerminalState("STOPPED")).toBe(true));
  it("FAILED is terminal", () => expect(isTerminalState("FAILED")).toBe(true));
  it("TIMED_OUT is terminal", () => expect(isTerminalState("TIMED_OUT")).toBe(true));
  it("RUNNING is not terminal", () => expect(isTerminalState("RUNNING")).toBe(false));
  it("QUEUED is not terminal", () => expect(isTerminalState("QUEUED")).toBe(false));
});

describe("TERMINAL_STATES", () => {
  it("contains exactly 3 states", () => {
    expect(TERMINAL_STATES.size).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// Transition with optimistic locking
// ---------------------------------------------------------------------------

describe("transition() — optimistic locking", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockEventCreate.mockResolvedValue(undefined);
  });

  it("increments version on successful transition", async () => {
    const run = makeRun({ state: "QUEUED", version: 3 });
    mockFindUnique.mockResolvedValue(run);
    mockUpdateMany.mockResolvedValue({ count: 1 });
    mockFindUniqueOrThrow.mockResolvedValue({
      ...run,
      state: "STARTING",
      version: 4,
      updatedAt: new Date(),
    });

    const result = await transition("run-1", "STARTING", {
      eventType: "RUN_STARTING",
    });

    expect(result.state).toBe("STARTING");
    expect(result.version).toBe(4);

    // Verify updateMany was called with version guard
    expect(mockUpdateMany).toHaveBeenCalledWith({
      where: { id: "run-1", version: 3 },
      data: expect.objectContaining({
        state: "STARTING",
        version: 4,
      }),
    });
  });

  it("throws StaleStateError when version conflicts (race condition)", async () => {
    const run = makeRun({ state: "QUEUED", version: 5 });
    mockFindUnique.mockResolvedValue(run);
    // Another worker already modified this row — updateMany matches 0 rows
    mockUpdateMany.mockResolvedValue({ count: 0 });

    await expect(transition("run-1", "STARTING")).rejects.toThrow(StaleStateError);
    await expect(transition("run-1", "STARTING")).rejects.toThrow(
      "Optimistic lock conflict",
    );
  });

  it("throws RunNotFoundError for non-existent run", async () => {
    mockFindUnique.mockResolvedValue(null);

    await expect(transition("nonexistent", "STARTING")).rejects.toThrow(
      RunNotFoundError,
    );
  });

  it("throws InvalidTransitionError for illegal transition", async () => {
    const run = makeRun({ state: "FAILED", version: 2 });
    mockFindUnique.mockResolvedValue(run);

    await expect(transition("run-1", "RUNNING")).rejects.toThrow(
      InvalidTransitionError,
    );

    // updateMany should NOT be called — we reject before hitting DB
    expect(mockUpdateMany).not.toHaveBeenCalled();
  });

  it("sets startedAt when transitioning to RUNNING", async () => {
    const run = makeRun({ state: "SYNCING", version: 2 });
    mockFindUnique.mockResolvedValue(run);
    mockUpdateMany.mockResolvedValue({ count: 1 });
    mockFindUniqueOrThrow.mockResolvedValue({
      ...run,
      state: "RUNNING",
      version: 3,
      startedAt: new Date(),
    });

    const startedAt = new Date("2026-04-06T12:00:00Z");
    await transition("run-1", "RUNNING", { startedAt });

    expect(mockUpdateMany).toHaveBeenCalledWith({
      where: { id: "run-1", version: 2 },
      data: expect.objectContaining({
        state: "RUNNING",
        version: 3,
        startedAt,
      }),
    });
  });

  it("sets stoppedAt and errorCode on terminal transitions", async () => {
    const run = makeRun({ state: "RUNNING", version: 7 });
    mockFindUnique.mockResolvedValue(run);
    mockUpdateMany.mockResolvedValue({ count: 1 });
    mockFindUniqueOrThrow.mockResolvedValue({
      ...run,
      state: "FAILED",
      version: 8,
      errorCode: "ACTIVATE_CRASH",
    });

    await transition("run-1", "FAILED", {
      errorCode: "ACTIVATE_CRASH",
      message: "crashed",
    });

    expect(mockUpdateMany).toHaveBeenCalledWith({
      where: { id: "run-1", version: 7 },
      data: expect.objectContaining({
        state: "FAILED",
        version: 8,
        stoppedAt: expect.any(Date),
        errorCode: "ACTIVATE_CRASH",
      }),
    });
  });

  it("creates BotEvent with correct payload", async () => {
    const run = makeRun({ state: "QUEUED", version: 0 });
    mockFindUnique.mockResolvedValue(run);
    mockUpdateMany.mockResolvedValue({ count: 1 });
    mockFindUniqueOrThrow.mockResolvedValue({
      ...run,
      state: "STARTING",
      version: 1,
    });

    await transition("run-1", "STARTING", {
      eventType: "RUN_STARTING",
      message: "Worker picked up run",
    });

    expect(mockEventCreate).toHaveBeenCalledWith({
      data: {
        botRunId: "run-1",
        type: "RUN_STARTING",
        payloadJson: expect.objectContaining({
          from: "QUEUED",
          to: "STARTING",
          message: "Worker picked up run",
        }),
      },
    });
  });

  it("works starting from version 0 (new run)", async () => {
    const run = makeRun({ state: "CREATED", version: 0 });
    mockFindUnique.mockResolvedValue(run);
    mockUpdateMany.mockResolvedValue({ count: 1 });
    mockFindUniqueOrThrow.mockResolvedValue({
      ...run,
      state: "QUEUED",
      version: 1,
    });

    const result = await transition("run-1", "QUEUED");
    expect(result.version).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Error classes
// ---------------------------------------------------------------------------

describe("error classes", () => {
  it("StaleStateError has correct properties", () => {
    const err = new StaleStateError("run-x", 5);
    expect(err.name).toBe("StaleStateError");
    expect(err.runId).toBe("run-x");
    expect(err.expectedVersion).toBe(5);
    expect(err.message).toContain("run-x");
    expect(err.message).toContain("5");
    expect(err instanceof Error).toBe(true);
  });

  it("InvalidTransitionError has from/to", () => {
    const err = new InvalidTransitionError("FAILED", "RUNNING");
    expect(err.from).toBe("FAILED");
    expect(err.to).toBe("RUNNING");
    expect(err.message).toContain("FAILED");
  });

  it("RunNotFoundError has runId", () => {
    const err = new RunNotFoundError("run-y");
    expect(err.runId).toBe("run-y");
  });
});
