/**
 * Route tests: strategies.ts — Issue #225 (Roadmap V4, Batch 1, A3)
 *
 * Covers: GET/POST /strategies, GET /strategies/:id,
 *         POST /strategies/:id/versions, POST /strategies/validate
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockStrategies: Record<string, Record<string, unknown>> = {};
const mockVersions: Record<string, Record<string, unknown>> = {};
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];
let strategyIdCounter = 0;
let versionIdCounter = 0;

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull" },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    strategy: {
      findMany: vi.fn().mockImplementation(({ where }: { where: { workspaceId: string } }) => {
        const results = Object.values(mockStrategies).filter(
          (s) => s.workspaceId === where.workspaceId,
        );
        return Promise.resolve(results.sort((a, b) =>
          new Date(b.createdAt as string).getTime() - new Date(a.createdAt as string).getTime(),
        ));
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id?: string; workspaceId_name?: { workspaceId: string; name: string } } }) => {
        if (where.id) {
          return Promise.resolve(mockStrategies[where.id] ?? null);
        }
        if (where.workspaceId_name) {
          const match = Object.values(mockStrategies).find(
            (s) => s.workspaceId === where.workspaceId_name!.workspaceId && s.name === where.workspaceId_name!.name,
          );
          return Promise.resolve(match ?? null);
        }
        return Promise.resolve(null);
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `strat-${++strategyIdCounter}`;
        const record = { id, ...data, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
        mockStrategies[id] = record;
        return Promise.resolve(record);
      }),
    },
    strategyVersion: {
      findFirst: vi.fn().mockImplementation(({ where }: { where: { strategyId: string } }) => {
        const versions = Object.values(mockVersions).filter(
          (v) => v.strategyId === where.strategyId,
        );
        if (versions.length === 0) return Promise.resolve(null);
        return Promise.resolve(versions.sort((a, b) => (b.version as number) - (a.version as number))[0]);
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `ver-${++versionIdCounter}`;
        const record = { id, ...data, createdAt: new Date().toISOString() };
        mockVersions[id] = record;
        return Promise.resolve(record);
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(() => {
        const m = mockWorkspaceMemberships[0];
        if (!m) return Promise.resolve(null);
        return Promise.resolve({ ...m, workspace: { id: m.workspaceId, name: "Test WS" } });
      }),
    },
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;
const WS_ID = "ws-strat-test";
const USER_ID = "user-strat-1";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: USER_ID, email: "strat@test.com" });
});

afterAll(async () => {
  await app.close();
});

beforeEach(() => {
  Object.keys(mockStrategies).forEach((k) => delete mockStrategies[k]);
  Object.keys(mockVersions).forEach((k) => delete mockVersions[k]);
  mockWorkspaceMemberships.length = 0;
  strategyIdCounter = 0;
  versionIdCounter = 0;

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
});

function headers() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function seedStrategy(name = "Test Strategy", symbol = "BTCUSDT", timeframe = "M15") {
  const id = `strat-${++strategyIdCounter}`;
  const record = { id, workspaceId: WS_ID, name, symbol, timeframe, status: "DRAFT", createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
  mockStrategies[id] = record;
  return record;
}

// Minimal valid DSL v2 for testing
const VALID_DSL = {
  id: "test-1", name: "Test", dslVersion: 2, enabled: true,
  market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
  timeframes: ["M15"],
  entry: {
    side: "Buy",
    signal: { type: "crossover", fast: { blockType: "SMA", length: 10 }, slow: { blockType: "SMA", length: 20 } },
    indicators: [{ type: "SMA", length: 10 }, { type: "SMA", length: 20 }],
  },
  exit: {
    stopLoss: { type: "fixed_pct", value: 2.0 },
    takeProfit: { type: "fixed_pct", value: 4.0 },
  },
  risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2.0, cooldownSeconds: 60 },
  execution: { orderType: "Market", clientOrderIdPrefix: "test_", maxSlippageBps: 50 },
  guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
};

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

describe("GET /api/v1/strategies", () => {
  it("returns 200 with empty list", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([]);
  });

  it("returns strategies for the workspace", async () => {
    seedStrategy("Alpha");
    seedStrategy("Beta");
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies", headers: headers() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body).toHaveLength(2);
  });

  it("returns 401 without token", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies" });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 without X-Workspace-Id", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies", headers: { authorization: `Bearer ${token}` } });
    expect(res.statusCode).toBe(400);
  });

  it("returns 403 for non-member workspace", async () => {
    mockWorkspaceMemberships.length = 0;
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies", headers: headers() });
    expect(res.statusCode).toBe(403);
  });
});

describe("POST /api/v1/strategies", () => {
  it("creates a strategy (201)", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "My Strat", symbol: "ETHUSDT", timeframe: "H1" },
    });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.name).toBe("My Strat");
    expect(body.symbol).toBe("ETHUSDT");
    expect(body.status).toBe("DRAFT");
  });

  it("returns 400 for missing fields", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "X" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for invalid timeframe", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "X", symbol: "BTCUSDT", timeframe: "INVALID" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 409 for duplicate name in workspace", async () => {
    seedStrategy("Dupe");
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "Dupe", symbol: "BTCUSDT", timeframe: "M15" },
    });
    expect(res.statusCode).toBe(409);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies",
      headers: { "content-type": "application/json" },
      payload: { name: "X", symbol: "BTCUSDT", timeframe: "M15" },
    });
    expect(res.statusCode).toBe(401);
  });
});

describe("GET /api/v1/strategies/:id", () => {
  it("returns strategy with versions", async () => {
    const strat = seedStrategy("Lookup");
    const res = await app.inject({ method: "GET", url: `/api/v1/strategies/${strat.id}`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().name).toBe("Lookup");
  });

  it("returns 404 for nonexistent id", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies/nonexistent", headers: headers() });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 for strategy in another workspace", async () => {
    const id = `strat-${++strategyIdCounter}`;
    mockStrategies[id] = { id, workspaceId: "ws-other", name: "Secret", symbol: "BTC", timeframe: "M15", status: "DRAFT", createdAt: new Date().toISOString() };
    const res = await app.inject({ method: "GET", url: `/api/v1/strategies/${id}`, headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("POST /api/v1/strategies/:id/versions", () => {
  it("creates a version with valid DSL (201)", async () => {
    const strat = seedStrategy("Versioned");
    const res = await app.inject({
      method: "POST", url: `/api/v1/strategies/${strat.id}/versions`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { dslJson: VALID_DSL },
    });
    expect(res.statusCode).toBe(201);
    expect(res.json().strategyId).toBe(strat.id);
    expect(res.json().version).toBe(1);
  });

  it("returns 400 for invalid DSL", async () => {
    const strat = seedStrategy("BadDSL");
    const res = await app.inject({
      method: "POST", url: `/api/v1/strategies/${strat.id}/versions`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { dslJson: { invalid: true } },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 for nonexistent strategy", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies/nonexistent/versions",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { dslJson: VALID_DSL },
    });
    expect(res.statusCode).toBe(404);
  });
});

describe("POST /api/v1/strategies/validate", () => {
  it("returns ok for valid DSL", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies/validate",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { dslJson: VALID_DSL },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().ok).toBe(true);
  });

  it("returns 400 for invalid DSL", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies/validate",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { dslJson: {} },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/strategies/validate",
      headers: { "content-type": "application/json" },
      payload: { dslJson: VALID_DSL },
    });
    expect(res.statusCode).toBe(401);
  });
});
