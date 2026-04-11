/**
 * Workspace isolation tests — Issue #229 (Roadmap V4, Batch 2, B3)
 *
 * Verifies that multi-tenant isolation via resolveWorkspace() prevents
 * cross-workspace data access across all protected routes.
 *
 * Pattern: Two users in separate workspaces. User A should never see
 * or modify resources belonging to User B's workspace.
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];
const mockBots: Record<string, Record<string, unknown>> = {};
const mockStrategies: Record<string, Record<string, unknown>> = {};
const mockBotRuns: Record<string, Record<string, unknown>> = {};

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
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id?: string; workspaceId_name?: unknown } }) => {
        if (where.id) return Promise.resolve(mockBots[where.id] ?? null);
        return Promise.resolve(null);
      }),
    },
    strategy: {
      findMany: vi.fn().mockImplementation(({ where }: { where: { workspaceId: string } }) => {
        return Promise.resolve(Object.values(mockStrategies).filter((s) => s.workspaceId === where.workspaceId));
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id?: string; workspaceId_name?: unknown } }) => {
        if (where.id) return Promise.resolve(mockStrategies[where.id] ?? null);
        return Promise.resolve(null);
      }),
    },
    botRun: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockBotRuns[where.id] ?? null);
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { workspaceId_userId: { workspaceId: string; userId: string } } }) => {
        const { workspaceId, userId } = where.workspaceId_userId;
        const m = mockWorkspaceMemberships.find(
          (m) => m.workspaceId === workspaceId && m.userId === userId,
        );
        if (!m) return Promise.resolve(null);
        return Promise.resolve({ ...m, workspace: { id: m.workspaceId, name: "WS" } });
      }),
    },
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

vi.mock("../../src/lib/positionManager.js", () => ({
  listBotPositions: vi.fn().mockResolvedValue([]),
  getActiveBotPosition: vi.fn().mockResolvedValue(null),
  getPositionEvents: vi.fn().mockResolvedValue([]),
  calcUnrealisedPnl: vi.fn().mockReturnValue(0),
}));

vi.mock("../../src/lib/runtime/dcaBridge.js", () => ({
  recoverDcaState: vi.fn().mockReturnValue(null),
}));

vi.mock("../../src/lib/stateMachine.js", () => ({
  transition: vi.fn().mockResolvedValue({}),
  isValidTransition: vi.fn().mockReturnValue(true),
  isTerminalState: vi.fn().mockReturnValue(false),
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;

const WS_A = "ws-a-111";
const WS_B = "ws-b-222";
const USER_A = "user-a";
const USER_B = "user-b";

let tokenA: string;
let tokenB: string;

beforeAll(async () => {
  app = await buildApp();
  tokenA = app.jwt.sign({ sub: USER_A, email: "a@test.com" });
  tokenB = app.jwt.sign({ sub: USER_B, email: "b@test.com" });
});

afterAll(async () => { await app.close(); });

beforeEach(() => {
  Object.keys(mockBots).forEach((k) => delete mockBots[k]);
  Object.keys(mockStrategies).forEach((k) => delete mockStrategies[k]);
  Object.keys(mockBotRuns).forEach((k) => delete mockBotRuns[k]);
  mockWorkspaceMemberships.length = 0;

  // User A is member of WS_A only
  mockWorkspaceMemberships.push({ userId: USER_A, workspaceId: WS_A, role: "OWNER" });
  // User B is member of WS_B only
  mockWorkspaceMemberships.push({ userId: USER_B, workspaceId: WS_B, role: "OWNER" });

  // Seed data: bot in WS_A, strategy in WS_B
  mockBots["bot-ws-a"] = { id: "bot-ws-a", workspaceId: WS_A, name: "A's Bot", symbol: "BTC", status: "DRAFT", strategyVersionId: "sv1" };
  mockBots["bot-ws-b"] = { id: "bot-ws-b", workspaceId: WS_B, name: "B's Bot", symbol: "ETH", status: "DRAFT", strategyVersionId: "sv2" };
  mockStrategies["strat-ws-a"] = { id: "strat-ws-a", workspaceId: WS_A, name: "A's Strat", status: "DRAFT" };
  mockStrategies["strat-ws-b"] = { id: "strat-ws-b", workspaceId: WS_B, name: "B's Strat", status: "DRAFT" };
  mockBotRuns["run-ws-a"] = { id: "run-ws-a", botId: "bot-ws-a", workspaceId: WS_A, state: "RUNNING" };
  mockBotRuns["run-ws-b"] = { id: "run-ws-b", botId: "bot-ws-b", workspaceId: WS_B, state: "RUNNING" };
});

function headersA() {
  return { authorization: `Bearer ${tokenA}`, "x-workspace-id": WS_A };
}
function headersB() {
  return { authorization: `Bearer ${tokenB}`, "x-workspace-id": WS_B };
}

// ═══════════════════════════════════════════════════════════════════════════

describe("resolveWorkspace gate", () => {
  it("returns 400 when X-Workspace-Id header is missing", async () => {
    const res = await app.inject({
      method: "GET", url: "/api/v1/bots",
      headers: { authorization: `Bearer ${tokenA}` },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 403 when user is not a member of requested workspace", async () => {
    // User A tries to access WS_B
    const res = await app.inject({
      method: "GET", url: "/api/v1/bots",
      headers: { authorization: `Bearer ${tokenA}`, "x-workspace-id": WS_B },
    });
    expect(res.statusCode).toBe(403);
  });
});

describe("Bot isolation: user A cannot access user B's bots", () => {
  it("GET /bots lists only own workspace bots", async () => {
    const resA = await app.inject({ method: "GET", url: "/api/v1/bots", headers: headersA() });
    const resB = await app.inject({ method: "GET", url: "/api/v1/bots", headers: headersB() });
    expect(resA.json().length).toBe(1);
    expect(resA.json()[0].name).toBe("A's Bot");
    expect(resB.json().length).toBe(1);
    expect(resB.json()[0].name).toBe("B's Bot");
  });

  it("GET /bots/:id returns 404 for bot in another workspace", async () => {
    // User A tries to get User B's bot
    const res = await app.inject({ method: "GET", url: "/api/v1/bots/bot-ws-b", headers: headersA() });
    expect(res.statusCode).toBe(404);
  });

  it("PATCH /bots/:id returns 404 for bot in another workspace", async () => {
    const res = await app.inject({
      method: "PATCH", url: "/api/v1/bots/bot-ws-b",
      headers: { ...headersA(), "content-type": "application/json" },
      payload: { name: "Stolen" },
    });
    expect(res.statusCode).toBe(404);
  });
});

describe("Strategy isolation: user A cannot access user B's strategies", () => {
  it("GET /strategies lists only own workspace strategies", async () => {
    const resA = await app.inject({ method: "GET", url: "/api/v1/strategies", headers: headersA() });
    const resB = await app.inject({ method: "GET", url: "/api/v1/strategies", headers: headersB() });
    expect(resA.json().length).toBe(1);
    expect(resA.json()[0].name).toBe("A's Strat");
    expect(resB.json().length).toBe(1);
    expect(resB.json()[0].name).toBe("B's Strat");
  });

  it("GET /strategies/:id returns 404 for strategy in another workspace", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/strategies/strat-ws-b", headers: headersA() });
    expect(res.statusCode).toBe(404);
  });
});

describe("Run isolation: user A cannot access user B's runs", () => {
  it("GET /runs/:runId returns 404 for run in another workspace", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/runs/run-ws-b", headers: headersA() });
    expect(res.statusCode).toBe(404);
  });
});

describe("Cross-workspace header spoofing", () => {
  it("User A cannot spoof WS_B header (membership check blocks)", async () => {
    // User A sends X-Workspace-Id: WS_B but is not a member
    const res = await app.inject({
      method: "GET", url: "/api/v1/bots",
      headers: { authorization: `Bearer ${tokenA}`, "x-workspace-id": WS_B },
    });
    expect(res.statusCode).toBe(403);
  });

  it("User B cannot spoof WS_A header", async () => {
    const res = await app.inject({
      method: "GET", url: "/api/v1/strategies",
      headers: { authorization: `Bearer ${tokenB}`, "x-workspace-id": WS_A },
    });
    expect(res.statusCode).toBe(403);
  });
});
