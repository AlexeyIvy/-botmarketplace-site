/**
 * actions/bots.ts — unit tests
 * Tests createBot validation, workspace scoping, and duplicate detection.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockStrategyVersionFindUnique = vi.fn();
const mockExchangeConnectionFindUnique = vi.fn();
const mockBotFindUnique = vi.fn();
const mockBotCreate = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../../src/lib/prisma.js", () => ({
  prisma: {
    strategyVersion: {
      findUnique: (...args: unknown[]) => mockStrategyVersionFindUnique(...args),
    },
    exchangeConnection: {
      findUnique: (...args: unknown[]) => mockExchangeConnectionFindUnique(...args),
    },
    bot: {
      findUnique: (...args: unknown[]) => mockBotFindUnique(...args),
      create: (...args: unknown[]) => mockBotCreate(...args),
    },
  },
}));

import { createBot, ActionValidationError, ActionConflictError, ActionNotFoundError } from "../../../src/lib/actions/bots.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WS = "ws-test-1";
const OTHER_WS = "ws-other";

const validInput = {
  name: "TestBot",
  strategyVersionId: "sv-1",
  symbol: "BTCUSDT",
  timeframe: "M5",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupHappyPath() {
  mockStrategyVersionFindUnique.mockResolvedValue({
    id: "sv-1",
    strategy: { workspaceId: WS },
  });
  mockBotFindUnique.mockResolvedValue(null);
  mockBotCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
    Promise.resolve({ id: "bot-new", ...data }),
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
});

describe("createBot", () => {
  // ── Input validation ────────────────────────────────────────────────────

  it("throws ActionValidationError when name is missing", async () => {
    await expect(createBot(WS, { ...validInput, name: "" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when name is not a string", async () => {
    await expect(createBot(WS, { ...validInput, name: 123 }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when strategyVersionId is missing", async () => {
    await expect(createBot(WS, { ...validInput, strategyVersionId: "" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when symbol is missing", async () => {
    await expect(createBot(WS, { ...validInput, symbol: "" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError for invalid timeframe", async () => {
    await expect(createBot(WS, { ...validInput, timeframe: "H4" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when timeframe is missing", async () => {
    await expect(createBot(WS, { ...validInput, timeframe: undefined }))
      .rejects.toThrow(ActionValidationError);
  });

  // ── Cross-workspace checks ──────────────────────────────────────────────

  it("throws ActionNotFoundError when strategyVersion not in workspace", async () => {
    mockStrategyVersionFindUnique.mockResolvedValue({
      id: "sv-1",
      strategy: { workspaceId: OTHER_WS },
    });
    await expect(createBot(WS, validInput))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when strategyVersion does not exist", async () => {
    mockStrategyVersionFindUnique.mockResolvedValue(null);
    await expect(createBot(WS, validInput))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when exchangeConnectionId belongs to another workspace", async () => {
    mockStrategyVersionFindUnique.mockResolvedValue({
      id: "sv-1",
      strategy: { workspaceId: WS },
    });
    mockExchangeConnectionFindUnique.mockResolvedValue({
      id: "ec-1",
      workspaceId: OTHER_WS,
    });
    await expect(createBot(WS, { ...validInput, exchangeConnectionId: "ec-1" }))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when exchangeConnectionId does not exist", async () => {
    mockStrategyVersionFindUnique.mockResolvedValue({
      id: "sv-1",
      strategy: { workspaceId: WS },
    });
    mockExchangeConnectionFindUnique.mockResolvedValue(null);
    await expect(createBot(WS, { ...validInput, exchangeConnectionId: "ec-missing" }))
      .rejects.toThrow(ActionNotFoundError);
  });

  // ── Duplicate name ──────────────────────────────────────────────────────

  it("throws ActionConflictError when bot name already exists in workspace", async () => {
    mockStrategyVersionFindUnique.mockResolvedValue({
      id: "sv-1",
      strategy: { workspaceId: WS },
    });
    mockBotFindUnique.mockResolvedValue({ id: "bot-existing", name: "TestBot" });
    await expect(createBot(WS, validInput))
      .rejects.toThrow(ActionConflictError);
  });

  // ── Happy path ──────────────────────────────────────────────────────────

  it("creates bot with status DRAFT and returns result", async () => {
    setupHappyPath();
    const result = await createBot(WS, validInput);

    expect(result).toEqual({
      botId: "bot-new",
      name: "TestBot",
      status: "DRAFT",
    });
    expect(mockBotCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        workspaceId: WS,
        name: "TestBot",
        symbol: "BTCUSDT",
        timeframe: "M5",
        status: "DRAFT",
        strategyVersionId: "sv-1",
        exchangeConnectionId: null,
      }),
    });
  });

  it("creates bot with exchangeConnectionId when provided", async () => {
    setupHappyPath();
    mockExchangeConnectionFindUnique.mockResolvedValue({
      id: "ec-1",
      workspaceId: WS,
    });
    const result = await createBot(WS, { ...validInput, exchangeConnectionId: "ec-1" });

    expect(result.botId).toBe("bot-new");
    expect(mockBotCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        exchangeConnectionId: "ec-1",
      }),
    });
  });

  it("accepts all valid timeframes", async () => {
    for (const tf of ["M1", "M5", "M15", "H1"]) {
      setupHappyPath();
      vi.clearAllMocks();
      setupHappyPath();
      const result = await createBot(WS, { ...validInput, timeframe: tf });
      expect(result.status).toBe("DRAFT");
    }
  });
});
