/**
 * actions/lab.ts — unit tests
 * Tests runBacktestAction: input validation, workspace scoping,
 * date validation, interval mapping, async fire-and-forget.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockStrategyFindUnique = vi.fn();
const mockBacktestCreate = vi.fn();
const mockBacktestUpdate = vi.fn();
const mockBacktestFindUnique = vi.fn();
const mockFetchCandles = vi.fn();
const mockRunBacktest = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../../src/lib/prisma.js", () => ({
  prisma: {
    strategy: {
      findUnique: (...args: unknown[]) => mockStrategyFindUnique(...args),
    },
    backtestResult: {
      create: (...args: unknown[]) => mockBacktestCreate(...args),
      update: (...args: unknown[]) => mockBacktestUpdate(...args),
      findUnique: (...args: unknown[]) => mockBacktestFindUnique(...args),
    },
  },
}));

vi.mock("../../../src/lib/bybitCandles.js", () => ({
  fetchCandles: (...args: unknown[]) => mockFetchCandles(...args),
}));

vi.mock("../../../src/lib/backtest.js", () => ({
  runBacktest: (...args: unknown[]) => mockRunBacktest(...args),
}));

import { runBacktestAction, ActionValidationError, ActionNotFoundError } from "../../../src/lib/actions/lab.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WS = "ws-test-1";
const OTHER_WS = "ws-other";

const validInput = {
  strategyId: "s-1",
  fromTs: "2025-01-01T00:00:00Z",
  toTs: "2025-01-31T00:00:00Z",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  mockBacktestCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
    Promise.resolve({ id: "bt-new", ...data }),
  );
  // The async runner runs fire-and-forget, mock to avoid unhandled rejections
  mockBacktestUpdate.mockResolvedValue({});
  mockBacktestFindUnique.mockResolvedValue({
    id: "bt-new",
    strategyId: "s-1",
  });
  mockFetchCandles.mockResolvedValue([]);
  mockRunBacktest.mockReturnValue({ trades: [], pnl: 0 });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("runBacktestAction", () => {
  // ── Input validation ──────────────────────────────────────────────────

  it("throws ActionValidationError when strategyId is missing", async () => {
    await expect(runBacktestAction(WS, { fromTs: "2025-01-01", toTs: "2025-01-31" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when strategyId is not a string", async () => {
    await expect(runBacktestAction(WS, { ...validInput, strategyId: 123 }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when fromTs is missing", async () => {
    await expect(runBacktestAction(WS, { strategyId: "s-1", toTs: "2025-01-31" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when toTs is missing", async () => {
    await expect(runBacktestAction(WS, { strategyId: "s-1", fromTs: "2025-01-01" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError for invalid interval", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS, symbol: "BTCUSDT", timeframe: "M15" });
    await expect(runBacktestAction(WS, { ...validInput, interval: "30" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when fromTs is not a valid date", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS, symbol: "BTCUSDT", timeframe: "M15" });
    await expect(runBacktestAction(WS, { ...validInput, fromTs: "not-a-date" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when toTs is not a valid date", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS, symbol: "BTCUSDT", timeframe: "M15" });
    await expect(runBacktestAction(WS, { ...validInput, toTs: "not-a-date" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when fromTs >= toTs", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS, symbol: "BTCUSDT", timeframe: "M15" });
    await expect(runBacktestAction(WS, {
      ...validInput,
      fromTs: "2025-02-01T00:00:00Z",
      toTs: "2025-01-01T00:00:00Z",
    })).rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when fromTs equals toTs", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS, symbol: "BTCUSDT", timeframe: "M15" });
    await expect(runBacktestAction(WS, {
      ...validInput,
      fromTs: "2025-01-15T00:00:00Z",
      toTs: "2025-01-15T00:00:00Z",
    })).rejects.toThrow(ActionValidationError);
  });

  // ── Cross-workspace ───────────────────────────────────────────────────

  it("throws ActionNotFoundError when strategy not found", async () => {
    mockStrategyFindUnique.mockResolvedValue(null);
    await expect(runBacktestAction(WS, validInput))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when strategy belongs to another workspace", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: OTHER_WS });
    await expect(runBacktestAction(WS, validInput))
      .rejects.toThrow(ActionNotFoundError);
  });

  // ── Happy path ────────────────────────────────────────────────────────

  it("creates backtest with PENDING status and returns result", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "BTCUSDT",
      timeframe: "M15",
    });

    const result = await runBacktestAction(WS, validInput);

    expect(result).toEqual({
      backtestId: "bt-new",
      status: "PENDING",
    });
    expect(mockBacktestCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        workspaceId: WS,
        strategyId: "s-1",
        symbol: "BTCUSDT",
        interval: "15",
        status: "PENDING",
      }),
    });
  });

  it("uses strategy symbol when body symbol not provided", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "ETHUSDT",
      timeframe: "H1",
    });

    await runBacktestAction(WS, validInput);

    expect(mockBacktestCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        symbol: "ETHUSDT",
        interval: "60",
      }),
    });
  });

  it("uses body symbol when explicitly provided", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "ETHUSDT",
      timeframe: "M15",
    });

    await runBacktestAction(WS, { ...validInput, symbol: "SOLUSDT" });

    expect(mockBacktestCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        symbol: "SOLUSDT",
      }),
    });
  });

  it("uses body interval when explicitly provided", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "BTCUSDT",
      timeframe: "M15",
    });

    await runBacktestAction(WS, { ...validInput, interval: "60" });

    expect(mockBacktestCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        interval: "60",
      }),
    });
  });

  it("maps timeframe M1 to interval 1", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "BTCUSDT",
      timeframe: "M1",
    });

    await runBacktestAction(WS, validInput);

    expect(mockBacktestCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({ interval: "1" }),
    });
  });

  it("maps timeframe M5 to interval 5", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "BTCUSDT",
      timeframe: "M5",
    });

    await runBacktestAction(WS, validInput);

    expect(mockBacktestCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({ interval: "5" }),
    });
  });

  it("accepts all valid intervals", async () => {
    mockStrategyFindUnique.mockResolvedValue({
      id: "s-1",
      workspaceId: WS,
      symbol: "BTCUSDT",
      timeframe: "M15",
    });

    for (const interval of ["1", "5", "15", "60"]) {
      vi.clearAllMocks();
      mockStrategyFindUnique.mockResolvedValue({
        id: "s-1",
        workspaceId: WS,
        symbol: "BTCUSDT",
        timeframe: "M15",
      });
      mockBacktestCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
        Promise.resolve({ id: "bt-new", ...data }),
      );
      mockBacktestUpdate.mockResolvedValue({});
      mockBacktestFindUnique.mockResolvedValue({ id: "bt-new", strategyId: "s-1" });
      mockFetchCandles.mockResolvedValue([]);
      mockRunBacktest.mockReturnValue({ trades: [], pnl: 0 });

      const result = await runBacktestAction(WS, { ...validInput, interval });
      expect(result.status).toBe("PENDING");
    }
  });
});
