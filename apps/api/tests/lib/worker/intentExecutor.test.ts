/**
 * worker/intentExecutor.ts — unit tests (#230)
 * Tests demo mode, live mode, retry logic, dead-letter behaviour.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockUpdateMany = vi.fn();
const mockUpdate = vi.fn();
const mockEventCreate = vi.fn();
const mockBybitPlaceOrder = vi.fn();
const mockGetInstrument = vi.fn();
const mockNormalizeOrder = vi.fn();
const mockDecrypt = vi.fn();
const mockGetEncryptionKeyRaw = vi.fn();
const mockClassifyError = vi.fn();

vi.mock("@prisma/client", () => ({
  Prisma: {
    sql: vi.fn(),
    join: vi.fn(),
    InputJsonValue: {} as never,
  },
}));

vi.mock("../../../src/lib/prisma.js", () => ({
  prisma: {
    botIntent: {
      updateMany: (...args: unknown[]) => mockUpdateMany(...args),
      update: (...args: unknown[]) => mockUpdate(...args),
    },
    botEvent: {
      create: (...args: unknown[]) => mockEventCreate(...args),
    },
  },
}));

vi.mock("../../../src/lib/crypto.js", () => ({
  decrypt: (...args: unknown[]) => mockDecrypt(...args),
  getEncryptionKeyRaw: (...args: unknown[]) => mockGetEncryptionKeyRaw(...args),
}));

vi.mock("../../../src/lib/bybitOrder.js", () => ({
  bybitPlaceOrder: (...args: unknown[]) => mockBybitPlaceOrder(...args),
  getBybitBaseUrl: vi.fn().mockReturnValue("https://api-demo.bybit.com"),
  isBybitLive: vi.fn().mockReturnValue(false),
}));

vi.mock("../../../src/lib/exchange/instrumentCache.js", () => ({
  getInstrument: (...args: unknown[]) => mockGetInstrument(...args),
}));

vi.mock("../../../src/lib/exchange/normalizer.js", () => ({
  normalizeOrder: (...args: unknown[]) => mockNormalizeOrder(...args),
}));

vi.mock("../../../src/lib/errorClassifier.js", () => ({
  classifyExecutionError: (...args: unknown[]) => mockClassifyError(...args),
}));

import { executeIntent, MAX_INTENT_RETRIES } from "../../../src/lib/worker/intentExecutor.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockLog = {
  child: vi.fn().mockReturnThis(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
  debug: vi.fn(),
} as unknown as import("pino").Logger;

function makeIntent(overrides: Record<string, unknown> = {}) {
  return {
    id: "intent-1",
    intentId: "entry_123_long",
    orderLinkId: "lab_abc_123",
    side: "BUY",
    qty: { toString: () => "0.01" },
    price: null,
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
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUpdateMany.mockResolvedValue({ count: 1 });
  mockUpdate.mockResolvedValue({});
  mockEventCreate.mockResolvedValue({});
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("executeIntent", () => {
  it("skips if another worker already claimed the intent", async () => {
    mockUpdateMany.mockResolvedValue({ count: 0 });
    await executeIntent(makeIntent() as never, mockLog);
    expect(mockUpdate).not.toHaveBeenCalled();
  });

  it("simulates fill in demo mode (no exchange connection)", async () => {
    await executeIntent(makeIntent() as never, mockLog);

    expect(mockUpdateMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1", state: "PENDING" },
        data: { state: "PLACED" },
      }),
    );
    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: "intent-1" },
        data: expect.objectContaining({ state: "FILLED" }),
      }),
    );
    expect(mockEventCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ type: "intent_simulated" }),
      }),
    );
  });

  it("places order via Bybit in live mode", async () => {
    mockGetEncryptionKeyRaw.mockReturnValue(Buffer.alloc(32));
    mockDecrypt.mockReturnValue("plain-secret");
    mockGetInstrument.mockResolvedValue({ lotSizeFilter: {}, priceFilter: {} });
    mockNormalizeOrder.mockReturnValue({
      valid: true,
      order: { qty: "0.01", price: undefined, diagnostics: {} },
    });
    mockBybitPlaceOrder.mockResolvedValue({
      orderId: "bybit-order-1",
      orderLinkId: "lab_abc_123",
    });

    const intent = makeIntent({
      botRun: {
        id: "run-1",
        bot: {
          id: "bot-1",
          symbol: "BTCUSDT",
          exchangeConnectionId: "ec-1",
          exchangeConnection: { apiKey: "key", encryptedSecret: "enc" },
          strategyVersion: { dslJson: { enabled: true, execution: { orderType: "Market" } } },
        },
      },
    });

    await executeIntent(intent as never, mockLog);

    expect(mockBybitPlaceOrder).toHaveBeenCalledOnce();
    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ orderId: "bybit-order-1" }),
      }),
    );
  });

  it("retries on transient error when retry count < max", async () => {
    mockGetEncryptionKeyRaw.mockReturnValue(Buffer.alloc(32));
    mockDecrypt.mockReturnValue("secret");
    mockGetInstrument.mockRejectedValue(new Error("timeout"));
    mockClassifyError.mockReturnValue({
      retryable: true,
      errorClass: "network_timeout",
      reason: "timeout",
    });

    const intent = makeIntent({
      retryCount: 0,
      botRun: {
        id: "run-1",
        bot: {
          id: "bot-1",
          symbol: "BTCUSDT",
          exchangeConnectionId: "ec-1",
          exchangeConnection: { apiKey: "key", encryptedSecret: "enc" },
          strategyVersion: { dslJson: {} },
        },
      },
    });

    await executeIntent(intent as never, mockLog);

    // Should set back to PENDING with incremented retryCount
    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          state: "PENDING",
          retryCount: 1,
        }),
      }),
    );
  });

  it("dead-letters on permanent error", async () => {
    mockGetEncryptionKeyRaw.mockReturnValue(Buffer.alloc(32));
    mockDecrypt.mockReturnValue("secret");
    mockGetInstrument.mockRejectedValue(new Error("invalid symbol"));
    mockClassifyError.mockReturnValue({
      retryable: false,
      errorClass: "invalid_request",
      reason: "invalid symbol",
    });

    const intent = makeIntent({
      retryCount: 0,
      botRun: {
        id: "run-1",
        bot: {
          id: "bot-1",
          symbol: "BTCUSDT",
          exchangeConnectionId: "ec-1",
          exchangeConnection: { apiKey: "key", encryptedSecret: "enc" },
          strategyVersion: { dslJson: {} },
        },
      },
    });

    await executeIntent(intent as never, mockLog);

    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ state: "FAILED" }),
      }),
    );
  });

  it("dead-letters when max retries exceeded", async () => {
    mockGetEncryptionKeyRaw.mockReturnValue(Buffer.alloc(32));
    mockDecrypt.mockReturnValue("secret");
    mockGetInstrument.mockRejectedValue(new Error("timeout"));
    mockClassifyError.mockReturnValue({
      retryable: true,
      errorClass: "network_timeout",
      reason: "timeout",
    });

    const intent = makeIntent({
      retryCount: MAX_INTENT_RETRIES, // already at max
      botRun: {
        id: "run-1",
        bot: {
          id: "bot-1",
          symbol: "BTCUSDT",
          exchangeConnectionId: "ec-1",
          exchangeConnection: { apiKey: "key", encryptedSecret: "enc" },
          strategyVersion: { dslJson: {} },
        },
      },
    });

    await executeIntent(intent as never, mockLog);

    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ state: "FAILED" }),
      }),
    );
  });
});
