/**
 * Route tests: bots.ts — Issue #223 (Roadmap V4, Batch 1, A1)
 *
 * Covers: GET /bots, POST /bots, PATCH /bots/:id, GET /bots/:id,
 *         GET /bots/:id/runs, GET /bots/:id/positions, POST /bots/:id/kill
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockBots: Record<string, Record<string, unknown>> = {};
const mockStrategyVersions: Record<string, Record<string, unknown>> = {};
const mockExchangeConns: Record<string, Record<string, unknown>> = {};
const mockBotRuns: Record<string, Record<string, unknown>> = {};
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];
let botIdCounter = 0;

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull", InputJsonValue: {} as never },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    bot: {
      findMany: vi.fn().mockImplementation(({ where }: { where: { workspaceId: string } }) => {
        return Promise.resolve(Object.values(mockBots).filter((b) => b.workspaceId === where.workspaceId));
      }),
      findUnique: vi.fn().mockImplementation(({ where, include }: { where: { id?: string; workspaceId_name?: { workspaceId: string; name: string } }; include?: unknown }) => {
        if (where.id) {
          const bot = mockBots[where.id] ?? null;
          if (bot && include) {
            return Promise.resolve({
              ...bot,
              strategyVersion: mockStrategyVersions[bot.strategyVersionId as string] ?? null,
              runs: [],
            });
          }
          return Promise.resolve(bot);
        }
        if (where.workspaceId_name) {
          const match = Object.values(mockBots).find(
            (b) => b.workspaceId === where.workspaceId_name!.workspaceId && b.name === where.workspaceId_name!.name,
          );
          return Promise.resolve(match ?? null);
        }
        return Promise.resolve(null);
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `bot-${++botIdCounter}`;
        const record = { id, ...data, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
        mockBots[id] = record;
        return Promise.resolve(record);
      }),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const bot = mockBots[where.id];
        if (bot) Object.assign(bot, data, { updatedAt: new Date().toISOString() });
        return Promise.resolve(bot);
      }),
    },
    strategyVersion: {
      findUnique: vi.fn().mockImplementation(({ where, include }: { where: { id: string }; include?: unknown }) => {
        const sv = mockStrategyVersions[where.id] ?? null;
        if (sv && include) {
          return Promise.resolve({ ...sv, strategy: { workspaceId: sv.workspaceId } });
        }
        return Promise.resolve(sv);
      }),
    },
    exchangeConnection: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockExchangeConns[where.id] ?? null);
      }),
    },
    botRun: {
      findMany: vi.fn().mockImplementation(({ where }: { where: { botId: string } }) => {
        return Promise.resolve(
          Object.values(mockBotRuns)
            .filter((r) => r.botId === where.botId)
            .sort((a, b) => new Date(b.createdAt as string).getTime() - new Date(a.createdAt as string).getTime()),
        );
      }),
    },
    position: {
      findUnique: vi.fn().mockResolvedValue(null),
    },
    botIntent: {
      updateMany: vi.fn().mockResolvedValue({ count: 0 }),
    },
    botEvent: {
      create: vi.fn().mockResolvedValue({}),
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

// Mock position manager (imports Prisma directly)
vi.mock("../../src/lib/positionManager.js", () => ({
  listBotPositions: vi.fn().mockResolvedValue([]),
  getActiveBotPosition: vi.fn().mockResolvedValue(null),
  getPositionEvents: vi.fn().mockResolvedValue([]),
  calcUnrealisedPnl: vi.fn().mockReturnValue(0),
}));

// Mock DCA bridge
vi.mock("../../src/lib/runtime/dcaBridge.js", () => ({
  recoverDcaState: vi.fn().mockReturnValue(null),
}));

// Mock state machine for kill endpoint
vi.mock("../../src/lib/stateMachine.js", () => ({
  transition: vi.fn().mockResolvedValue({}),
  isValidTransition: vi.fn().mockReturnValue(true),
  isTerminalState: vi.fn().mockReturnValue(false),
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;
const WS_ID = "ws-bot-test";
const USER_ID = "user-bot-1";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: USER_ID, email: "bot@test.com" });
});

afterAll(async () => {
  await app.close();
});

beforeEach(() => {
  Object.keys(mockBots).forEach((k) => delete mockBots[k]);
  Object.keys(mockStrategyVersions).forEach((k) => delete mockStrategyVersions[k]);
  Object.keys(mockExchangeConns).forEach((k) => delete mockExchangeConns[k]);
  Object.keys(mockBotRuns).forEach((k) => delete mockBotRuns[k]);
  mockWorkspaceMemberships.length = 0;
  botIdCounter = 0;

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });

  // Seed a strategy version
  mockStrategyVersions["sv-1"] = {
    id: "sv-1", strategyId: "strat-1", version: 1,
    workspaceId: WS_ID, strategy: { workspaceId: WS_ID },
    dslJson: {}, executionPlanJson: {},
  };

  // Seed an exchange connection
  mockExchangeConns["conn-1"] = { id: "conn-1", workspaceId: WS_ID };
});

function headers() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

function seedBot(name = "TestBot", overrides: Record<string, unknown> = {}) {
  const id = `bot-${++botIdCounter}`;
  const record = {
    id, workspaceId: WS_ID, name, symbol: "BTCUSDT", timeframe: "M15",
    status: "DRAFT", strategyVersionId: "sv-1", exchangeConnectionId: null,
    createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    ...overrides,
  };
  mockBots[id] = record;
  return record;
}

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

describe("GET /api/v1/bots", () => {
  it("returns 200 with empty list", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/bots", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([]);
  });

  it("returns bots for the workspace", async () => {
    seedBot("Bot A");
    seedBot("Bot B");
    const res = await app.inject({ method: "GET", url: "/api/v1/bots", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toHaveLength(2);
  });

  it("returns 401 without token", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/bots" });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 without X-Workspace-Id", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/bots", headers: { authorization: `Bearer ${token}` } });
    expect(res.statusCode).toBe(400);
  });

  it("returns 403 for non-member workspace", async () => {
    mockWorkspaceMemberships.length = 0;
    const res = await app.inject({ method: "GET", url: "/api/v1/bots", headers: headers() });
    expect(res.statusCode).toBe(403);
  });
});

describe("POST /api/v1/bots", () => {
  it("creates a bot (201)", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "NewBot", strategyVersionId: "sv-1", symbol: "ETHUSDT", timeframe: "H1" },
    });
    expect(res.statusCode).toBe(201);
    expect(res.json().name).toBe("NewBot");
    expect(res.json().status).toBe("DRAFT");
  });

  it("returns 400 for missing required fields", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "X" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for invalid timeframe", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "X", strategyVersionId: "sv-1", symbol: "BTC", timeframe: "BAD" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for nonexistent strategyVersionId", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "X", strategyVersionId: "nonexistent", symbol: "BTC", timeframe: "M15" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 409 for duplicate name", async () => {
    seedBot("DupeBot");
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "DupeBot", strategyVersionId: "sv-1", symbol: "BTC", timeframe: "M15" },
    });
    expect(res.statusCode).toBe(409);
  });

  it("accepts optional exchangeConnectionId", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "ConnBot", strategyVersionId: "sv-1", symbol: "BTC", timeframe: "M15", exchangeConnectionId: "conn-1" },
    });
    expect(res.statusCode).toBe(201);
  });

  it("returns 400 for nonexistent exchangeConnectionId", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "Bad", strategyVersionId: "sv-1", symbol: "BTC", timeframe: "M15", exchangeConnectionId: "bad" },
    });
    expect(res.statusCode).toBe(400);
  });
});

describe("GET /api/v1/bots/:id", () => {
  it("returns bot with details", async () => {
    const bot = seedBot("DetailBot");
    const res = await app.inject({ method: "GET", url: `/api/v1/bots/${bot.id}`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().name).toBe("DetailBot");
  });

  it("returns 404 for nonexistent id", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/bots/nope", headers: headers() });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 for bot in another workspace", async () => {
    const id = `bot-${++botIdCounter}`;
    mockBots[id] = { id, workspaceId: "ws-other", name: "Secret", status: "DRAFT" };
    const res = await app.inject({ method: "GET", url: `/api/v1/bots/${id}`, headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("PATCH /api/v1/bots/:id", () => {
  it("updates bot name", async () => {
    const bot = seedBot("OldName");
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/bots/${bot.id}`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "NewName" },
    });
    expect(res.statusCode).toBe(200);
  });

  it("returns 404 for nonexistent bot", async () => {
    const res = await app.inject({
      method: "PATCH", url: "/api/v1/bots/nope",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "X" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 409 for duplicate name on update", async () => {
    seedBot("Existing");
    const bot = seedBot("Rename");
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/bots/${bot.id}`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { name: "Existing" },
    });
    expect(res.statusCode).toBe(409);
  });

  it("returns 400 for empty body", async () => {
    const bot = seedBot("NoChange");
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/bots/${bot.id}`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(400);
  });
});

describe("GET /api/v1/bots/:id/runs", () => {
  it("returns runs for a bot", async () => {
    const bot = seedBot("RunBot");
    mockBotRuns["run-1"] = { id: "run-1", botId: bot.id, state: "STOPPED", createdAt: new Date().toISOString() };
    const res = await app.inject({ method: "GET", url: `/api/v1/bots/${bot.id}/runs`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toHaveLength(1);
  });

  it("returns 404 for nonexistent bot", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/bots/nope/runs", headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("GET /api/v1/bots/:id/positions", () => {
  it("returns 200 with positions array", async () => {
    const bot = seedBot("PosBot");
    const res = await app.inject({ method: "GET", url: `/api/v1/bots/${bot.id}/positions`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([]);
  });

  it("returns 404 for nonexistent bot", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/bots/nope/positions", headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("POST /api/v1/bots/:id/kill", () => {
  it("kills a bot with active runs", async () => {
    const bot = seedBot("KillBot");
    mockBotRuns["run-kill"] = { id: "run-kill", botId: bot.id, state: "RUNNING" };
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${bot.id}/kill`,
      headers: headers(),
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().killed).toBe(true);
  });

  it("returns 404 for nonexistent bot", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/bots/nope/kill", headers: headers() });
    expect(res.statusCode).toBe(404);
  });

  it("is safe to kill a bot with no active runs", async () => {
    const bot = seedBot("IdleBot");
    const res = await app.inject({ method: "POST", url: `/api/v1/bots/${bot.id}/kill`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().killed).toBe(true);
    expect(res.json().stoppedRuns).toEqual([]);
  });
});
