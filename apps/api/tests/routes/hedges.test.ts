import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock Prisma ───────────────────────────────────────────────────────────────

const mockHedgePositions: Record<string, unknown> = {};
const mockBotRuns: Record<string, unknown> = {};
const mockBotIntents: unknown[] = [];
const mockWorkspaceMemberships: unknown[] = [];

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
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockBotRuns[where.id] ?? null);
      }),
    },
    botIntent: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const record = { id: `intent-${Date.now()}-${Math.random()}`, ...data, createdAt: new Date(), updatedAt: new Date() };
        mockBotIntents.push(record);
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
  mockWorkspaceMemberships.length = 0;

  // Set up default workspace membership + run
  mockWorkspaceMemberships.push({
    userId: "test-user-id",
    workspaceId: TEST_WORKSPACE_ID,
    role: "OWNER",
  });
  mockBotRuns[TEST_RUN_ID] = {
    id: TEST_RUN_ID,
    workspaceId: TEST_WORKSPACE_ID,
    status: "RUNNING",
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
    const hedgeId = "hedge-already-open";
    mockHedgePositions[hedgeId] = {
      id: hedgeId,
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
      url: `/api/v1/hedges/${hedgeId}/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });
    expect(res.statusCode).toBe(409);
  });

  it("creates intents and transitions to OPENING", async () => {
    const hedgeId = "hedge-planned";
    mockHedgePositions[hedgeId] = {
      id: hedgeId,
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "PLANNED",
      entryBasisBps: 5,
      fundingCollected: 0,
      createdAt: new Date(),
      closedAt: null,
      legs: [],
    };

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/${hedgeId}/execute`,
      headers: authHeaders(),
      payload: { quantity: 0.01 },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.status).toBe("OPENING");
    expect(body.intents.spot).toBeDefined();
    expect(body.intents.perp).toBeDefined();
  });
});

// ── POST /hedges/:id/exit ────────────────────────────────────────────────────

describe("POST /api/v1/hedges/:id/exit", () => {
  it("returns 409 if hedge is not OPEN", async () => {
    const hedgeId = "hedge-planned-exit";
    mockHedgePositions[hedgeId] = {
      id: hedgeId,
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "PLANNED",
      entryBasisBps: 5,
      fundingCollected: 0,
      createdAt: new Date(),
      closedAt: null,
      legs: [],
    };

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/${hedgeId}/exit`,
      headers: authHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(409);
  });

  it("creates exit intents and transitions to CLOSING", async () => {
    const hedgeId = "hedge-open-exit";
    mockHedgePositions[hedgeId] = {
      id: hedgeId,
      botRunId: TEST_RUN_ID,
      symbol: "BTCUSDT",
      status: "OPEN",
      entryBasisBps: 5,
      fundingCollected: 10,
      createdAt: new Date(),
      closedAt: null,
      legs: [
        { side: "SPOT_BUY", price: 67000, quantity: 0.015, fee: 0.5, timestamp: new Date() },
        { side: "PERP_SHORT", price: 67005, quantity: 0.015, fee: 0.5, timestamp: new Date() },
      ],
    };

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/hedges/${hedgeId}/exit`,
      headers: authHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.status).toBe("CLOSING");
    expect(body.intents.spot).toBeDefined();
    expect(body.intents.perp).toBeDefined();
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
