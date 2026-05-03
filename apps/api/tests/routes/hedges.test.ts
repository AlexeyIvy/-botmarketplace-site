import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock Prisma ───────────────────────────────────────────────────────────────

const mockHedgePositions: Record<string, unknown> = {};
const mockBotRuns: Record<string, unknown> = {};
const mockBotIntents: unknown[] = [];
const mockLegExecutions: unknown[] = [];
const mockWorkspaceMemberships: unknown[] = [];

// Bybit mocks — terminal.test.ts pattern. Reset between tests.
const mockBybitPlaceOrder = vi.fn();
const mockBybitGetOrderStatus = vi.fn();

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: {
    sql: vi.fn(),
    join: vi.fn(),
    JsonNull: "DbNull",
    InputJsonValue: {} as never,
  },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    hedgePosition: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `hedge-${Date.now()}`;
        const record = {
          id,
          ...data,
          fundingCollected: data.fundingCollected ?? 0,
          createdAt: new Date(),
          closedAt: null,
          legs: [],
        };
        mockHedgePositions[id] = record;
        return Promise.resolve(record);
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockHedgePositions[where.id] ?? null);
      }),
      findMany: vi.fn().mockImplementation(() => {
        return Promise.resolve(Object.values(mockHedgePositions));
      }),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const existing = mockHedgePositions[where.id] as Record<string, unknown> | undefined;
        if (existing) {
          Object.assign(existing, data);
        }
        return Promise.resolve(existing);
      }),
    },
    botRun: {
      findUnique: vi.fn().mockImplementation(({ where, select }: { where: { id: string }; select?: Record<string, unknown> }) => {
        const row = mockBotRuns[where.id];
        if (!row) return Promise.resolve(null);
        // The /execute and /exit handlers project bot.exchangeConnection via
        // a `select` clause; the legacy /entry and ownership-check paths do
        // not. The mock returns the full row regardless — Prisma's runtime
        // semantics where unselected fields are dropped don't matter here
        // because the consumer reads only what it asked for, and excess
        // fields are harmless.
        void select;
        return Promise.resolve(row);
      }),
    },
    botIntent: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const record = { id: `intent-${Date.now()}-${Math.random()}`, ...data, createdAt: new Date(), updatedAt: new Date() };
        mockBotIntents.push(record);
        return Promise.resolve(record);
      }),
    },
    legExecution: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const record = { id: `leg-${Date.now()}-${Math.random()}`, ...data, timestamp: new Date() };
        mockLegExecutions.push(record);
        return Promise.resolve(record);
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(() => {
        const membership = mockWorkspaceMemberships[0] as Record<string, unknown> | undefined;
        if (!membership) return Promise.resolve(null);
        return Promise.resolve({
          ...membership,
          workspace: { id: (membership as Record<string, unknown>).workspaceId, name: "Test Workspace" },
        });
      }),
    },
    $transaction: vi.fn().mockImplementation(async (ops: Promise<unknown>[]) => {
      const results = [];
      for (const op of ops) {
        results.push(await op);
      }
      return results;
    }),
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

vi.mock("../../src/lib/crypto.js", () => ({
  decryptWithFallback: vi.fn().mockReturnValue("plaintext-secret"),
}));

vi.mock("../../src/lib/bybitOrder.js", () => ({
  bybitPlaceOrder: (...args: unknown[]) => mockBybitPlaceOrder(...args),
  bybitGetOrderStatus: (...args: unknown[]) => mockBybitGetOrderStatus(...args),
  sanitizeBybitError: (err: unknown) => (err instanceof Error ? err.message : String(err)),
  // Unused by hedge routes, but other importers of this module may pull them
  // via the same mock factory if Vitest hoists shared modules. Provide stubs.
  mapBybitStatus: vi.fn(),
  getBybitBaseUrl: () => "https://api-demo.bybit.com",
  isBybitLive: () => false,
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Test setup ────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;

const TEST_WORKSPACE_ID = "ws-test-123";
const TEST_RUN_ID = "run-test-456";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: "test-user-id", email: "test@test.com" });
});

afterAll(async () => {
  await app.close();
});

beforeEach(() => {
  // Reset mutable state
  Object.keys(mockHedgePositions).forEach((k) => delete mockHedgePositions[k]);
  Object.keys(mockBotRuns).forEach((k) => delete mockBotRuns[k]);
  mockBotIntents.length = 0;
  mockLegExecutions.length = 0;
  mockWorkspaceMemberships.length = 0;
  mockBybitPlaceOrder.mockReset();
  mockBybitGetOrderStatus.mockReset();
  // Disable real timers in the leg poll loop — tests rely on the mock
  // returning Filled on the first call, but defence-in-depth.
  process.env.HEDGE_LEG_POLL_DELAY_MS = "0";

  // Set up default workspace membership + run with linked exchange creds
  // (the /execute and /exit routes need bot.exchangeConnection populated;
  // tests for /entry / GET endpoints simply ignore the extra fields).
  mockWorkspaceMemberships.push({
    userId: "test-user-id",
    workspaceId: TEST_WORKSPACE_ID,
    role: "OWNER",
  });
  mockBotRuns[TEST_RUN_ID] = {
    id: TEST_RUN_ID,
    workspaceId: TEST_WORKSPACE_ID,
    status: "RUNNING",
    bot: {
      exchangeConnection: {
        apiKey: "linear-key",
        encryptedSecret: "iv:tag:cipher",
        spotApiKey: "spot-key",
        spotEncryptedSecret: "iv:tag:cipher2",
      },
    },
  };
});

function authHeaders() {
  return {
    authorization: `Bearer ${token}`,
    "x-workspace-id": TEST_WORKSPACE_ID,
  };
}

// ── POST /hedges/entry ───────────────────────────────────────────────────────

describe("POST /api/v1/hedges/entry", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/entry",
      payload: { symbol: "BTCUSDT", botRunId: TEST_RUN_ID },
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 if symbol is missing", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/entry",
      headers: authHeaders(),
      payload: { botRunId: TEST_RUN_ID },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 if botRunId is missing", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/entry",
      headers: authHeaders(),
      payload: { symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 if run not found", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/entry",
      headers: authHeaders(),
      payload: { symbol: "BTCUSDT", botRunId: "nonexistent" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("creates a PLANNED hedge position", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/entry",
      headers: authHeaders(),
      payload: { symbol: "BTCUSDT", botRunId: TEST_RUN_ID, entryBasisBps: 5 },
    });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.symbol).toBe("BTCUSDT");
    expect(body.status).toBe("PLANNED");
    expect(body.entryBasisBps).toBe(5);
    expect(body.botRunId).toBe(TEST_RUN_ID);
  });

  it("uppercases the symbol", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/entry",
      headers: authHeaders(),
      payload: { symbol: "ethusdt", botRunId: TEST_RUN_ID },
    });
    expect(res.statusCode).toBe(201);
    expect(res.json().symbol).toBe("ETHUSDT");
  });
});

// ── POST /hedges/:id/execute ─────────────────────────────────────────────────

function seedPlannedHedge(id: string, runId = TEST_RUN_ID, symbol = "BTCUSDT") {
  mockHedgePositions[id] = {
    id,
    botRunId: runId,
    symbol,
    status: "PLANNED",
    entryBasisBps: 5,
    fundingCollected: 0,
    createdAt: new Date(),
    closedAt: null,
    legs: [],
  };
}

function placedOk(orderId: string) {
  return Promise.resolve({ orderId, orderLinkId: `link-${orderId}` });
}

function statusFilled(orderId: string, qty: string, price: string) {
  return Promise.resolve({
    orderId,
    symbol: "BTCUSDT",
    side: "Buy",
    orderType: "Market",
    qty,
    price: "0",
    avgPrice: price,
    cumExecQty: qty,
    orderStatus: "Filled",
    createdTime: "0",
    updatedTime: "0",
  });
}

describe("POST /api/v1/hedges/:id/execute", () => {
  it("returns 404 for nonexistent hedge", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/hedges/nonexistent/execute",
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 409 if hedge is not PLANNED", async () => {
    mockHedgePositions["hedge-already-open"] = {
      id: "hedge-already-open",
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "OPEN",
      entryBasisBps: 5,
      fundingCollected: 0,
      createdAt: new Date(),
      closedAt: null,
      legs: [],
    };

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/hedge-already-open/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });
    expect(res.statusCode).toBe(409);
  });

  it("returns 400 when quantity is missing or non-positive", async () => {
    seedPlannedHedge("h-bad-qty");
    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-bad-qty/execute`,
      headers: authHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(400);
  });

  it("places spot Buy + perp Sell sequentially → status OPEN with 2 LegExecutions", async () => {
    seedPlannedHedge("h-ok");
    // Spot first, then perp — sequencing assertion below pins this.
    mockBybitPlaceOrder
      .mockImplementationOnce(() => placedOk("spot-1"))
      .mockImplementationOnce(() => placedOk("perp-1"));
    mockBybitGetOrderStatus
      .mockImplementationOnce(() => statusFilled("spot-1", "0.01", "67000"))
      .mockImplementationOnce(() => statusFilled("perp-1", "0.01", "67005"));

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-ok/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.status).toBe("OPEN");
    expect(body.outcome).toBe("FILLED");
    expect(body.legs).toHaveLength(2);

    // Spot leg recorded with the spot category fill, perp leg with the perp fill.
    const spotLeg = body.legs.find((l: { side: string }) => l.side === "SPOT_BUY");
    const perpLeg = body.legs.find((l: { side: string }) => l.side === "PERP_SHORT");
    expect(spotLeg).toMatchObject({ price: 67000, quantity: 0.01, orderId: "spot-1" });
    expect(perpLeg).toMatchObject({ price: 67005, quantity: 0.01, orderId: "perp-1" });

    // Sequencing: first call MUST be category=spot (spot leads).
    expect(mockBybitPlaceOrder).toHaveBeenCalledTimes(2);
    const firstCallArgs = mockBybitPlaceOrder.mock.calls[0];
    expect((firstCallArgs?.[2] as { category: string }).category).toBe("spot");
    expect((firstCallArgs?.[2] as { side: string }).side).toBe("Buy");
    const secondCallArgs = mockBybitPlaceOrder.mock.calls[1];
    expect((secondCallArgs?.[2] as { category: string }).category).toBe("linear");
    expect((secondCallArgs?.[2] as { side: string }).side).toBe("Sell");

    // Persisted state: status OPEN, 2 LegExecution rows.
    expect((mockHedgePositions["h-ok"] as { status: string }).status).toBe("OPEN");
    expect(mockLegExecutions.filter(
      (l) => (l as { hedgeId: string }).hedgeId === "h-ok",
    )).toHaveLength(2);
  });

  it("spot leg failure → no perp call, status FAILED, no LegExecution rows", async () => {
    seedPlannedHedge("h-spot-fail");
    mockBybitPlaceOrder.mockRejectedValueOnce(new Error("spot rejected"));

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-spot-fail/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });

    expect(res.statusCode).toBe(422);
    const body = res.json();
    expect(body.status).toBe("FAILED");
    expect(body.outcome).toBe("FAILED");
    expect(body.legs).toEqual([]);
    expect(body.reason).toMatch(/spot leg failed/);

    // Perp leg was never attempted.
    expect(mockBybitPlaceOrder).toHaveBeenCalledTimes(1);
    expect((mockHedgePositions["h-spot-fail"] as { status: string }).status).toBe("FAILED");
    expect(mockLegExecutions.filter(
      (l) => (l as { hedgeId: string }).hedgeId === "h-spot-fail",
    )).toHaveLength(0);
  });

  it("spot ok + perp fail → compensating spot Sell attempted, status FAILED", async () => {
    seedPlannedHedge("h-perp-fail");
    // Call 1: spot Buy (placed)        ; status poll Filled.
    // Call 2: perp Sell (rejected)     ; no status poll.
    // Call 3: compensating spot Sell   ; status poll Filled (succeeds).
    mockBybitPlaceOrder
      .mockImplementationOnce(() => placedOk("spot-buy-1"))
      .mockImplementationOnce(() => Promise.reject(new Error("perp rejected")))
      .mockImplementationOnce(() => placedOk("spot-sell-comp"));
    mockBybitGetOrderStatus
      .mockImplementationOnce(() => statusFilled("spot-buy-1", "0.01", "67000"))
      .mockImplementationOnce(() => statusFilled("spot-sell-comp", "0.01", "66990"));

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-perp-fail/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });

    expect(res.statusCode).toBe(422);
    const body = res.json();
    expect(body.status).toBe("FAILED");
    expect(body.outcome).toBe("PARTIAL_ERROR");
    expect(body.compensatingUnwind).toEqual({ attempted: true, succeeded: true });
    expect(body.reason).toMatch(/perp leg failed/);

    // The route reports only the original spot fill on the partial-error
    // path — the compensating sell is best-effort and not recorded in the
    // LegExecution audit (status=FAILED is the operator alert).
    expect(body.legs).toHaveLength(1);
    expect(body.legs[0].side).toBe("SPOT_BUY");

    expect(mockBybitPlaceOrder).toHaveBeenCalledTimes(3);
    const thirdCallArgs = mockBybitPlaceOrder.mock.calls[2];
    expect((thirdCallArgs?.[2] as { category: string; side: string }).category).toBe("spot");
    expect((thirdCallArgs?.[2] as { category: string; side: string }).side).toBe("Sell");
  });

  it("idempotency — repeated execute on already-OPEN hedge returns 409", async () => {
    seedPlannedHedge("h-idem");
    mockBybitPlaceOrder
      .mockImplementationOnce(() => placedOk("s-1"))
      .mockImplementationOnce(() => placedOk("p-1"));
    mockBybitGetOrderStatus
      .mockImplementationOnce(() => statusFilled("s-1", "0.01", "67000"))
      .mockImplementationOnce(() => statusFilled("p-1", "0.01", "67005"));

    const first = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-idem/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });
    expect(first.statusCode).toBe(200);

    // Second attempt on the now-OPEN hedge.
    const second = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-idem/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });
    expect(second.statusCode).toBe(409);
    // No additional Bybit calls — guard kicks in before executor is invoked.
    expect(mockBybitPlaceOrder).toHaveBeenCalledTimes(2);
  });
});

// ── POST /hedges/:id/exit ────────────────────────────────────────────────────

function seedOpenHedge(id: string, qty = 0.015) {
  mockHedgePositions[id] = {
    id,
    botRunId: TEST_RUN_ID,
    symbol: "BTCUSDT",
    status: "OPEN",
    entryBasisBps: 5,
    fundingCollected: 10,
    createdAt: new Date(),
    closedAt: null,
    legs: [
      { side: "SPOT_BUY", price: 67000, quantity: qty, fee: 0.5, timestamp: new Date() },
      { side: "PERP_SHORT", price: 67005, quantity: qty, fee: 0.5, timestamp: new Date() },
    ],
  };
}

describe("POST /api/v1/hedges/:id/exit", () => {
  it("returns 409 if hedge is not OPEN", async () => {
    seedPlannedHedge("hedge-planned-exit");
    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/hedge-planned-exit/exit`,
      headers: authHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(409);
  });

  it("places spot Sell + perp Buy sequentially → status CLOSED with 2 LegExecutions", async () => {
    seedOpenHedge("h-exit-ok", 0.015);
    mockBybitPlaceOrder
      .mockImplementationOnce(() => placedOk("spot-sell-1"))
      .mockImplementationOnce(() => placedOk("perp-buy-1"));
    mockBybitGetOrderStatus
      .mockImplementationOnce(() => statusFilled("spot-sell-1", "0.015", "67100"))
      .mockImplementationOnce(() => statusFilled("perp-buy-1", "0.015", "67095"));

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-exit-ok/exit`,
      headers: authHeaders(),
      payload: {},
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.status).toBe("CLOSED");
    expect(body.outcome).toBe("FILLED");
    expect(body.legs).toHaveLength(2);
    expect(body.legs.find((l: { side: string }) => l.side === "SPOT_SELL"))
      .toMatchObject({ price: 67100, quantity: 0.015, orderId: "spot-sell-1" });
    expect(body.legs.find((l: { side: string }) => l.side === "PERP_CLOSE"))
      .toMatchObject({ price: 67095, quantity: 0.015, orderId: "perp-buy-1" });

    // Sequencing — spot Sell first.
    const firstCall = mockBybitPlaceOrder.mock.calls[0]?.[2] as { category: string; side: string };
    expect(firstCall.category).toBe("spot");
    expect(firstCall.side).toBe("Sell");

    expect((mockHedgePositions["h-exit-ok"] as { status: string }).status).toBe("CLOSED");
    expect((mockHedgePositions["h-exit-ok"] as { closedAt: Date | null }).closedAt).toBeInstanceOf(Date);
  });

  it("perp close fail after spot sell → PARTIAL_ERROR (manual unwind, no auto-rebuy)", async () => {
    seedOpenHedge("h-exit-perp-fail", 0.015);
    mockBybitPlaceOrder
      .mockImplementationOnce(() => placedOk("spot-sell-2"))
      .mockImplementationOnce(() => Promise.reject(new Error("perp close rejected")));
    mockBybitGetOrderStatus.mockImplementationOnce(() =>
      statusFilled("spot-sell-2", "0.015", "67100"),
    );

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/h-exit-perp-fail/exit`,
      headers: authHeaders(),
      payload: {},
    });

    expect(res.statusCode).toBe(422);
    const body = res.json();
    expect(body.status).toBe("FAILED");
    expect(body.outcome).toBe("PARTIAL_ERROR");
    expect(body.legs).toHaveLength(1);
    expect(body.legs[0].side).toBe("SPOT_SELL");
    expect(body.reason).toMatch(/perp close leg failed/);
    // No compensatingUnwind block on exit path — re-buying spot would
    // contradict the operator's intent to exit.
    expect(body.compensatingUnwind).toBeUndefined();
    // Exactly 2 place calls: spot sell + failed perp close. No auto-rebuy.
    expect(mockBybitPlaceOrder).toHaveBeenCalledTimes(2);
  });
});

// ── GET /hedges ──────────────────────────────────────────────────────────────

describe("GET /api/v1/hedges", () => {
  it("returns 400 without botRunId", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/hedges",
      headers: authHeaders(),
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 for unknown run", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/hedges?botRunId=nonexistent",
      headers: authHeaders(),
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns list of hedge positions", async () => {
    mockHedgePositions["h1"] = {
      id: "h1",
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "OPEN",
      entryBasisBps: 5,
      fundingCollected: 0,
      createdAt: new Date(),
      closedAt: null,
      legs: [],
    };

    const res = await app.inject({
      method: "GET",
      url: `/api/v1/hedges?botRunId=${TEST_RUN_ID}`,
      headers: authHeaders(),
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(Array.isArray(body)).toBe(true);
  });
});

// ── GET /hedges/:id ──────────────────────────────────────────────────────────

describe("GET /api/v1/hedges/:id", () => {
  it("returns 404 for nonexistent hedge", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/hedges/nonexistent",
      headers: authHeaders(),
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns hedge details with P&L for closed position", async () => {
    const hedgeId = "hedge-closed-detail";
    const now = new Date();
    mockHedgePositions[hedgeId] = {
      id: hedgeId,
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "CLOSED",
      entryBasisBps: 5,
      fundingCollected: 15,
      createdAt: now,
      closedAt: now,
      legs: [
        { side: "SPOT_BUY", price: 67000, quantity: 0.015, fee: 0.5, timestamp: now },
        { side: "PERP_SHORT", price: 67005, quantity: 0.015, fee: 0.5, timestamp: now },
        { side: "SPOT_SELL", price: 67100, quantity: 0.015, fee: 0.5, timestamp: now },
        { side: "PERP_CLOSE", price: 67095, quantity: 0.015, fee: 0.5, timestamp: now },
      ],
    };

    const res = await app.inject({
      method: "GET",
      url: `/api/v1/hedges/${hedgeId}`,
      headers: authHeaders(),
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.id).toBe(hedgeId);
    expect(body.pnl).toBeDefined();
    expect(typeof body.pnl).toBe("number");
  });

  it("returns hedge details with P&L for open position", async () => {
    const hedgeId = "hedge-open-detail";
    mockHedgePositions[hedgeId] = {
      id: hedgeId,
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "OPEN",
      entryBasisBps: 5,
      fundingCollected: 5,
      createdAt: new Date(),
      closedAt: null,
      legs: [
        { side: "SPOT_BUY", price: 67000, quantity: 0.015, fee: 0.5, timestamp: new Date() },
        { side: "PERP_SHORT", price: 67005, quantity: 0.015, fee: 0.5, timestamp: new Date() },
      ],
    };

    const res = await app.inject({
      method: "GET",
      url: `/api/v1/hedges/${hedgeId}`,
      headers: authHeaders(),
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.status).toBe("OPEN");
    expect(body.pnl).toBeDefined();
  });
});
