/**
 * actions/strategies.ts — unit tests
 * Tests createStrategy, validateDslAction, createStrategyVersion:
 * input validation, workspace scoping, DSL validation, version auto-increment.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockStrategyFindUnique = vi.fn();
const mockStrategyCreate = vi.fn();
const mockVersionFindFirst = vi.fn();
const mockVersionCreate = vi.fn();
const mockValidateDsl = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../../src/lib/prisma.js", () => ({
  prisma: {
    strategy: {
      findUnique: (...args: unknown[]) => mockStrategyFindUnique(...args),
      create: (...args: unknown[]) => mockStrategyCreate(...args),
    },
    strategyVersion: {
      findFirst: (...args: unknown[]) => mockVersionFindFirst(...args),
      create: (...args: unknown[]) => mockVersionCreate(...args),
    },
  },
}));

vi.mock("../../../src/lib/dslValidator.js", () => ({
  validateDsl: (...args: unknown[]) => mockValidateDsl(...args),
}));

import {
  createStrategy,
  validateDslAction,
  createStrategyVersion,
  ActionValidationError,
  ActionConflictError,
  ActionNotFoundError,
} from "../../../src/lib/actions/strategies.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WS = "ws-test-1";
const OTHER_WS = "ws-other";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  mockValidateDsl.mockReturnValue(null); // valid by default
});

// ---------------------------------------------------------------------------
// createStrategy
// ---------------------------------------------------------------------------

describe("createStrategy", () => {
  const validInput = { name: "MyStrat", symbol: "BTCUSDT", timeframe: "M15" };

  it("throws ActionValidationError when name is missing", async () => {
    await expect(createStrategy(WS, { ...validInput, name: "" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when name is not a string", async () => {
    await expect(createStrategy(WS, { ...validInput, name: 42 }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when symbol is missing", async () => {
    await expect(createStrategy(WS, { ...validInput, symbol: "" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError for invalid timeframe", async () => {
    await expect(createStrategy(WS, { ...validInput, timeframe: "D1" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionConflictError when name already exists in workspace", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", name: "MyStrat" });
    await expect(createStrategy(WS, validInput))
      .rejects.toThrow(ActionConflictError);
  });

  it("creates strategy with status DRAFT and returns result", async () => {
    mockStrategyFindUnique.mockResolvedValue(null);
    mockStrategyCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
      Promise.resolve({ id: "s-new", ...data }),
    );

    const result = await createStrategy(WS, validInput);
    expect(result).toEqual({
      strategyId: "s-new",
      name: "MyStrat",
      status: "DRAFT",
    });
    expect(mockStrategyCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        workspaceId: WS,
        name: "MyStrat",
        symbol: "BTCUSDT",
        timeframe: "M15",
        status: "DRAFT",
      }),
    });
  });

  it("accepts all valid timeframes", async () => {
    mockStrategyFindUnique.mockResolvedValue(null);
    mockStrategyCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
      Promise.resolve({ id: "s-new", ...data }),
    );

    for (const tf of ["M1", "M5", "M15", "H1"]) {
      const result = await createStrategy(WS, { ...validInput, timeframe: tf });
      expect(result.status).toBe("DRAFT");
    }
  });
});

// ---------------------------------------------------------------------------
// validateDslAction
// ---------------------------------------------------------------------------

describe("validateDslAction", () => {
  it("throws ActionValidationError when dslJson is missing", async () => {
    await expect(validateDslAction(WS, {}))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when dslJson is the placeholder value", async () => {
    await expect(validateDslAction(WS, { dslJson: "__USER_MUST_PROVIDE__" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("returns ok:false when DSL validation fails", async () => {
    mockValidateDsl.mockReturnValue([{ field: "entry", message: "missing" }]);
    const result = await validateDslAction(WS, { dslJson: { invalid: true } });
    expect(result.ok).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors![0].field).toBe("entry");
  });

  it("returns ok:true when DSL is valid", async () => {
    mockValidateDsl.mockReturnValue(null);
    const result = await validateDslAction(WS, { dslJson: { valid: true } });
    expect(result).toEqual({ ok: true });
  });
});

// ---------------------------------------------------------------------------
// createStrategyVersion
// ---------------------------------------------------------------------------

describe("createStrategyVersion", () => {
  const validInput = { strategyId: "s-1", dslJson: { id: "test" } };

  it("throws ActionValidationError when strategyId is missing", async () => {
    await expect(createStrategyVersion(WS, { dslJson: {} }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when dslJson is missing", async () => {
    await expect(createStrategyVersion(WS, { strategyId: "s-1" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionValidationError when dslJson is placeholder", async () => {
    await expect(createStrategyVersion(WS, { strategyId: "s-1", dslJson: "__USER_MUST_PROVIDE__" }))
      .rejects.toThrow(ActionValidationError);
  });

  it("throws ActionNotFoundError when strategy not found", async () => {
    mockStrategyFindUnique.mockResolvedValue(null);
    await expect(createStrategyVersion(WS, validInput))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionNotFoundError when strategy belongs to another workspace", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: OTHER_WS });
    await expect(createStrategyVersion(WS, validInput))
      .rejects.toThrow(ActionNotFoundError);
  });

  it("throws ActionValidationError when DSL validation fails", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS });
    mockValidateDsl.mockReturnValue([{ field: "entry", message: "bad" }]);
    await expect(createStrategyVersion(WS, validInput))
      .rejects.toThrow(ActionValidationError);
  });

  it("creates version with auto-incremented number from latest", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS });
    mockValidateDsl.mockReturnValue(null);
    mockVersionFindFirst.mockResolvedValue({ version: 3 });
    mockVersionCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
      Promise.resolve({ id: "sv-new", ...data }),
    );

    const result = await createStrategyVersion(WS, validInput);
    expect(result).toEqual({ versionId: "sv-new", version: 4 });
    expect(mockVersionCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        strategyId: "s-1",
        version: 4,
        dslJson: validInput.dslJson,
      }),
    });
  });

  it("starts at version 1 when no prior versions exist", async () => {
    mockStrategyFindUnique.mockResolvedValue({ id: "s-1", workspaceId: WS });
    mockValidateDsl.mockReturnValue(null);
    mockVersionFindFirst.mockResolvedValue(null);
    mockVersionCreate.mockImplementation(({ data }: { data: Record<string, unknown> }) =>
      Promise.resolve({ id: "sv-new", ...data }),
    );

    const result = await createStrategyVersion(WS, validInput);
    expect(result.version).toBe(1);
  });
});
