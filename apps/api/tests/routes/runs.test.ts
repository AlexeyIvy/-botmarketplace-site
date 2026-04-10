/**
 * Route tests: runs.ts — Issue #224 (Roadmap V4, Batch 1, A2)
 *
 * Covers: POST /bots/:botId/runs, GET /bots/:botId/runs/:runId, GET /runs/:runId,
 *         POST /bots/:botId/runs/:runId/stop, POST /runs/stop-all,
 *         PATCH /runs/:runId/state, POST /runs/:runId/heartbeat,
 *         GET /runs/:runId/events, POST /runs/:runId/signal, POST /runs/reconcile
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockBots: Record<string, Record<string, unknown>> = {};
const mockBotRuns: Record<string, Record<string, unknown>> = {};
const mockBotEvents: Array<Record<string, unknown>> = [];
const mockBotIntents: Record<string, Record<string, unknown>> = {};
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];
let runIdCounter = 0;

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull", InputJsonValue: {} as never },
  BotRunState: {},
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    bot: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockBots[where.id] ?? null);
      }),
    },
    botRun: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockBotRuns[where.id] ?? null);
      }),
      findFirst: vi.fn().mockImplementation(({ where }: { where: { botId: string; state?: unknown } }) => {
        const match = Object.values(mockBotRuns).find(
          (r) => r.botId === where.botId && !["STOPPED", "FAILED", "TIMED_OUT"].includes(r.state as string),
        );
        return Promise.resolve(match ?? null);
      }),
      findMany: vi.fn().mockImplementation(({ where }: { where: { workspaceId?: string; botId?: string } }) => {
        let results = Object.values(mockBotRuns);
        if (where.workspaceId) results = results.filter((r) => r.workspaceId === where.workspaceId);
        if (where.botId) results = results.filter((r) => r.botId === where.botId);
        return Promise.resolve(results);
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `run-${++runIdCounter}`;
        const record = { id, ...data, version: 0, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
        mockBotRuns[id] = record;
        return Promise.resolve(record);
      }),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const run = mockBotRuns[where.id];
        if (run) Object.assign(run, data, { updatedAt: new Date().toISOString() });
        return Promise.resolve(run);
      }),
    },
    botEvent: {
      findMany: vi.fn().mockImplementation(() => Promise.resolve(mockBotEvents)),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const record = { id: `evt-${Date.now()}`, ...data, ts: new Date() };
        mockBotEvents.push(record);
        return Promise.resolve(record);
      }),
    },
    botIntent: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { botRunId_intentId?: { botRunId: string; intentId: string } } }) => {
        if (where.botRunId_intentId) {
          const key = `${where.botRunId_intentId.botRunId}:${where.botRunId_intentId.intentId}`;
          return Promise.resolve(mockBotIntents[key] ?? null);
        }
        return Promise.resolve(null);
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const record = { id: `intent-${Date.now()}`, ...data, createdAt: new Date(), updatedAt: new Date() };
        const key = `${data.botRunId}:${data.intentId}`;
        mockBotIntents[key] = record;
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
    $transaction: vi.fn().mockImplementation(async (fn: (tx: unknown) => Promise<unknown>) => {
      // Simulate transaction by passing the prisma mock itself
      const { prisma } = await import("../../src/lib/prisma.js");
      return fn(prisma);
    }),
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

// Mock state machine
const mockTransition = vi.fn().mockImplementation(async (runId: string, toState: string) => {
  const run = mockBotRuns[runId];
  if (run) {
    run.state = toState;
    if (toState === "STOPPED") run.stoppedAt = new Date().toISOString();
  }
  return run;
});

vi.mock("../../src/lib/stateMachine.js", () => ({
  transition: (...args: unknown[]) => mockTransition(...args),
  isTerminalState: vi.fn().mockImplementation((state: string) => ["STOPPED", "FAILED", "TIMED_OUT"].includes(state)),
  isValidTransition: vi.fn().mockReturnValue(true),
  InvalidTransitionError: class extends Error { constructor(m: string) { super(m); this.name = "InvalidTransitionError"; } },
  RunNotFoundError: class extends Error { constructor(m: string) { super(m); this.name = "RunNotFoundError"; } },
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;
const WS_ID = "ws-run-test";
const USER_ID = "user-run-1";
const BOT_ID = "bot-run-1";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: USER_ID, email: "run@test.com" });
});

afterAll(async () => {
  await app.close();
});

beforeEach(() => {
  Object.keys(mockBots).forEach((k) => delete mockBots[k]);
  Object.keys(mockBotRuns).forEach((k) => delete mockBotRuns[k]);
  Object.keys(mockBotIntents).forEach((k) => delete mockBotIntents[k]);
  mockBotEvents.length = 0;
  mockWorkspaceMemberships.length = 0;
  runIdCounter = 0;
  mockTransition.mockClear();

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
  mockBots[BOT_ID] = { id: BOT_ID, workspaceId: WS_ID, name: "TestBot", symbol: "BTCUSDT" };
});

function headers() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

function seedRun(state = "RUNNING", botId = BOT_ID) {
  const id = `run-${++runIdCounter}`;
  const record = { id, botId, workspaceId: WS_ID, symbol: "BTCUSDT", state, version: 0, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
  mockBotRuns[id] = record;
  return record;
}

// ═══════════════════════════════════════════════════════════════════════════

describe("POST /api/v1/bots/:botId/runs (start run)", () => {
  it("creates a run (201)", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(201);
  });

  it("returns 404 for nonexistent bot", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/bots/nonexistent/runs",
      headers: { ...headers(), "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 409 when active run already exists", async () => {
    seedRun("RUNNING");
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(409);
  });

  it("accepts optional durationMinutes", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { durationMinutes: 60 },
    });
    expect(res.statusCode).toBe(201);
  });

  it("returns 400 for invalid durationMinutes", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { durationMinutes: 9999 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs`,
      headers: { "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(401);
  });
});

describe("GET /api/v1/bots/:botId/runs/:runId", () => {
  it("returns a specific run", async () => {
    const run = seedRun("RUNNING");
    const res = await app.inject({ method: "GET", url: `/api/v1/bots/${BOT_ID}/runs/${run.id}`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().id).toBe(run.id);
  });

  it("returns 404 for nonexistent run", async () => {
    const res = await app.inject({ method: "GET", url: `/api/v1/bots/${BOT_ID}/runs/nope`, headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("GET /api/v1/runs/:runId", () => {
  it("returns run by ID within workspace", async () => {
    const run = seedRun("QUEUED");
    const res = await app.inject({ method: "GET", url: `/api/v1/runs/${run.id}`, headers: headers() });
    expect(res.statusCode).toBe(200);
  });

  it("returns 404 for run in another workspace", async () => {
    const id = `run-${++runIdCounter}`;
    mockBotRuns[id] = { id, botId: BOT_ID, workspaceId: "ws-other", state: "RUNNING" };
    const res = await app.inject({ method: "GET", url: `/api/v1/runs/${id}`, headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("POST /api/v1/bots/:botId/runs/:runId/stop", () => {
  it("stops a running run", async () => {
    const run = seedRun("RUNNING");
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs/${run.id}/stop`,
      headers: headers(),
    });
    expect(res.statusCode).toBe(200);
  });

  it("returns 404 for nonexistent run", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs/nope/stop`,
      headers: headers(),
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 409 for already stopped run", async () => {
    const run = seedRun("STOPPED");
    const res = await app.inject({
      method: "POST", url: `/api/v1/bots/${BOT_ID}/runs/${run.id}/stop`,
      headers: headers(),
    });
    expect(res.statusCode).toBe(409);
  });
});

describe("POST /api/v1/runs/stop-all", () => {
  it("stops all active runs in workspace", async () => {
    seedRun("RUNNING");
    seedRun("QUEUED");
    const res = await app.inject({ method: "POST", url: "/api/v1/runs/stop-all", headers: headers() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.total).toBe(2);
  });

  it("returns empty when no active runs", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/runs/stop-all", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().total).toBe(0);
  });
});

describe("PATCH /api/v1/runs/:runId/state", () => {
  it("advances run state", async () => {
    const run = seedRun("QUEUED");
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/runs/${run.id}/state`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { state: "RUNNING", message: "Worker acquired" },
    });
    expect(res.statusCode).toBe(200);
  });

  it("returns 404 for nonexistent run", async () => {
    const res = await app.inject({
      method: "PATCH", url: "/api/v1/runs/nope/state",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { state: "RUNNING" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 400 for missing state in body", async () => {
    const run = seedRun("QUEUED");
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/runs/${run.id}/state`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(400);
  });
});

describe("POST /api/v1/runs/:runId/heartbeat", () => {
  it("renews lease for a running run", async () => {
    const run = seedRun("RUNNING");
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/heartbeat`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { workerId: "worker-1" },
    });
    expect(res.statusCode).toBe(200);
  });

  it("returns 409 for terminal run", async () => {
    const run = seedRun("STOPPED");
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/heartbeat`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { workerId: "worker-1" },
    });
    expect(res.statusCode).toBe(409);
  });
});

describe("GET /api/v1/runs/:runId/events", () => {
  it("returns events list", async () => {
    const run = seedRun("RUNNING");
    mockBotEvents.push({ id: "e1", botRunId: run.id, type: "signal", ts: new Date(), payloadJson: {} });
    const res = await app.inject({ method: "GET", url: `/api/v1/runs/${run.id}/events`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toHaveLength(1);
  });

  it("returns 404 for nonexistent run", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/runs/nope/events", headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("POST /api/v1/runs/:runId/signal", () => {
  it("creates a signal intent (201)", async () => {
    const run = seedRun("RUNNING");
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/signal`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(201);
  });

  it("returns 409 for non-RUNNING run", async () => {
    const run = seedRun("QUEUED");
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/signal`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(409);
  });

  it("returns 400 for invalid side", async () => {
    const run = seedRun("RUNNING");
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/signal`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { side: "INVALID", qty: 0.01 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for non-positive qty", async () => {
    const run = seedRun("RUNNING");
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/signal`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { side: "BUY", qty: -1 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("idempotent: returns existing intent for same intentId", async () => {
    const run = seedRun("RUNNING");
    // First call
    const res1 = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/signal`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { side: "BUY", qty: 0.01, intentId: "idem-1" },
    });
    expect(res1.statusCode).toBe(201);

    // Second call with same intentId
    const res2 = await app.inject({
      method: "POST", url: `/api/v1/runs/${run.id}/signal`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { side: "BUY", qty: 0.01, intentId: "idem-1" },
    });
    expect(res2.statusCode).toBe(200);
  });
});

describe("POST /api/v1/runs/reconcile", () => {
  it("reconciles stale runs", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/runs/reconcile", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().at).toBeDefined();
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/runs/reconcile" });
    expect(res.statusCode).toBe(401);
  });
});
