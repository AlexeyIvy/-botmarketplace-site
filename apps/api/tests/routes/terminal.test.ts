/**
 * Terminal order routes — integration tests via app.inject (Roadmap V3, Task #16)
 *
 * Tests POST /terminal/orders, GET /terminal/orders/:id, GET /terminal/orders
 * through the real Fastify app with mocked Prisma + Bybit.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  })),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

const mockExchangeFindUnique = vi.fn();
const mockExchangeUpdate = vi.fn();
const mockOrderCreate = vi.fn();
const mockOrderUpdate = vi.fn();
const mockOrderFindUnique = vi.fn();
const mockOrderFindMany = vi.fn();

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    exchangeConnection: {
      findUnique: (...args: unknown[]) => mockExchangeFindUnique(...args),
      findMany: vi.fn().mockResolvedValue([]),
      create: vi.fn(),
      update: (...args: unknown[]) => mockExchangeUpdate(...args),
      delete: vi.fn(),
    },
    terminalOrder: {
      create: (...args: unknown[]) => mockOrderCreate(...args),
      update: (...args: unknown[]) => mockOrderUpdate(...args),
      findUnique: (...args: unknown[]) => mockOrderFindUnique(...args),
      findMany: (...args: unknown[]) => mockOrderFindMany(...args),
    },
    botRun: { findMany: vi.fn().mockResolvedValue([]) },
    $connect: vi.fn(),
    $disconnect: vi.fn(),
    $queryRaw: vi.fn().mockResolvedValue([{ "?column?": 1 }]),
  },
}));

vi.mock("../../src/lib/workspace.js", () => ({
  resolveWorkspace: vi.fn().mockResolvedValue({ id: "ws-1", name: "test" }),
}));

vi.mock("../../src/lib/crypto.js", () => ({
  getEncryptionKey: vi.fn().mockReturnValue(Buffer.alloc(32)),
  encrypt: vi.fn().mockReturnValue("iv:tag:cipher"),
  decrypt: vi.fn().mockReturnValue("decrypted-secret"),
  decryptWithFallback: vi.fn().mockReturnValue("decrypted-secret"),
}));

const mockBybitPlaceOrder = vi.fn();
const mockBybitGetOrderStatus = vi.fn();

vi.mock("../../src/lib/bybitOrder.js", () => ({
  bybitPlaceOrder: (...args: unknown[]) => mockBybitPlaceOrder(...args),
  bybitGetOrderStatus: (...args: unknown[]) => mockBybitGetOrderStatus(...args),
  mapBybitStatus: vi.fn().mockReturnValue("FILLED"),
  sanitizeBybitError: vi.fn().mockImplementation((err: unknown) => {
    return err instanceof Error ? err.message : String(err);
  }),
}));

vi.mock("../../src/lib/exchange/instrumentCache.js", () => ({
  getInstrument: vi.fn().mockRejectedValue(new Error("no cache")),
}));

vi.mock("../../src/lib/exchange/normalizer.js", () => ({
  normalizeOrder: vi.fn(),
}));

vi.mock("../../src/lib/bybitCandles.js", () => ({
  fetchTicker: vi.fn(),
  fetchCandles: vi.fn(),
}));

import { buildApp } from "../../src/app.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function getApp() {
  const app = await buildApp();
  const token = app.jwt.sign({ sub: "user-1", workspaceId: "ws-1" });
  return { app, token };
}

const CONN = {
  id: "conn-1",
  workspaceId: "ws-1",
  exchange: "BYBIT",
  name: "My Bybit",
  apiKey: "test-api-key",
  encryptedSecret: "iv:tag:cipher",
  status: "CONNECTED",
  createdAt: new Date(),
  updatedAt: new Date(),
};

const ORDER_RECORD = {
  id: "order-1",
  workspaceId: "ws-1",
  exchangeConnectionId: "conn-1",
  symbol: "BTCUSDT",
  side: "BUY",
  type: "MARKET",
  qty: "0.001",
  price: null,
  status: "SUBMITTED",
  exchangeOrderId: "bybit-ord-123",
  error: null,
  createdAt: new Date(),
  updatedAt: new Date(),
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("POST /api/v1/terminal/orders", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExchangeFindUnique.mockResolvedValue(CONN);
    mockExchangeUpdate.mockResolvedValue(CONN);
  });

  it("returns 401 without auth token", async () => {
    const { app } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      payload: {},
    });

    expect(res.statusCode).toBe(401);
    await app.close();
  });

  it("returns 400 for missing required fields", async () => {
    const { app, token } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {},
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.title).toBe("Validation Error");
    await app.close();
  });

  it("returns 400 for invalid side", async () => {
    const { app, token } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "INVALID",
        type: "MARKET",
        qty: 0.001,
      },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 400 for invalid type", async () => {
    const { app, token } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "STOP",
        qty: 0.001,
      },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 400 for negative qty", async () => {
    const { app, token } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "MARKET",
        qty: -1,
      },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 400 for LIMIT order without price", async () => {
    const { app, token } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "LIMIT",
        qty: 0.001,
      },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 400 for MARKET order with price", async () => {
    const { app, token } = await getApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "MARKET",
        qty: 0.001,
        price: 50000,
      },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("price must not be set for MARKET orders");
    await app.close();
  });

  it("returns 404 when exchange connection not found", async () => {
    const { app, token } = await getApp();
    mockExchangeFindUnique.mockResolvedValue(null);

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-nonexistent",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "MARKET",
        qty: 0.001,
      },
    });

    expect(res.statusCode).toBe(404);
    await app.close();
  });

  it("creates order and returns 201 on success", async () => {
    const { app, token } = await getApp();

    const createdOrder = { ...ORDER_RECORD, status: "PENDING", exchangeOrderId: null };
    const updatedOrder = { ...ORDER_RECORD };

    mockOrderCreate.mockResolvedValue(createdOrder);
    mockOrderUpdate.mockResolvedValue(updatedOrder);
    mockBybitPlaceOrder.mockResolvedValue({ orderId: "bybit-ord-123", orderLinkId: "link-1" });

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "MARKET",
        qty: 0.001,
      },
    });

    expect(res.statusCode).toBe(201);
    const body = JSON.parse(res.payload);
    expect(body.symbol).toBe("BTCUSDT");
    expect(body.status).toBe("SUBMITTED");
    expect(body.exchangeOrderId).toBe("bybit-ord-123");
    // Ensure no secrets leaked
    expect(body.encryptedSecret).toBeUndefined();
    expect(body.apiKey).toBeUndefined();
    await app.close();
  });

  it("returns error when Bybit rejects the order", async () => {
    const { app, token } = await getApp();

    const createdOrder = { ...ORDER_RECORD, status: "PENDING", exchangeOrderId: null };
    mockOrderCreate.mockResolvedValue(createdOrder);
    mockOrderUpdate.mockResolvedValue({ ...createdOrder, status: "FAILED", error: "insufficient balance" });
    mockBybitPlaceOrder.mockRejectedValue(new Error("Bybit API error 10001: insufficient balance"));

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
      payload: {
        exchangeConnectionId: "conn-1",
        symbol: "BTCUSDT",
        side: "BUY",
        type: "MARKET",
        qty: 0.001,
      },
    });

    // Insufficient balance → 422
    expect(res.statusCode).toBe(422);
    await app.close();
  });
});

describe("GET /api/v1/terminal/orders", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 401 without auth", async () => {
    const { app } = await getApp();

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/orders",
    });

    expect(res.statusCode).toBe(401);
    await app.close();
  });

  it("returns order list", async () => {
    const { app, token } = await getApp();
    mockOrderFindMany.mockResolvedValue([ORDER_RECORD]);

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/orders",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(Array.isArray(body)).toBe(true);
    expect(body.length).toBe(1);
    expect(body[0].id).toBe("order-1");
    await app.close();
  });
});

describe("GET /api/v1/terminal/orders/:id", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 404 for non-existent order", async () => {
    const { app, token } = await getApp();
    mockOrderFindUnique.mockResolvedValue(null);

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/orders/nonexistent",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    await app.close();
  });

  it("returns order detail", async () => {
    const { app, token } = await getApp();
    // Order in terminal state (FILLED) — no live sync needed
    mockOrderFindUnique.mockResolvedValue({ ...ORDER_RECORD, status: "FILLED" });

    const res = await app.inject({
      method: "GET",
      url: `/api/v1/terminal/orders/${ORDER_RECORD.id}`,
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.id).toBe("order-1");
    expect(body.status).toBe("FILLED");
    await app.close();
  });
});
