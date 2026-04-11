/**
 * Route tests: intents.ts — Issue #227 (Roadmap V4, Batch 2, B1)
 *
 * Covers: POST /runs/:runId/intents, GET /runs/:runId/intents,
 *         PATCH /runs/:runId/intents/:intentId/state
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockBotRuns: Record<string, Record<string, unknown>> = {};
const mockBotIntents: Record<string, Record<string, unknown>> = {};
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];
let intentCounter = 0;

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull", InputJsonValue: {} as never },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    botRun: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockBotRuns[where.id] ?? null);
      }),
    },
    botIntent: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id?: string; botRunId_intentId?: { botRunId: string; intentId: string } } }) => {
        if (where.botRunId_intentId) {
          const key = `${where.botRunId_intentId.botRunId}:${where.botRunId_intentId.intentId}`;
          return Promise.resolve(mockBotIntents[key] ?? null);
        }
        if (where.id) {
          return Promise.resolve(Object.values(mockBotIntents).find((i) => i.id === where.id) ?? null);
        }
        return Promise.resolve(null);
      }),
      findMany: vi.fn().mockImplementation(({ where }: { where: { botRunId: string } }) => {
        return Promise.resolve(
          Object.values(mockBotIntents).filter((i) => i.botRunId === where.botRunId),
        );
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `intent-${++intentCounter}`;
        const record = { id, ...data, createdAt: new Date(), updatedAt: new Date() };
        const key = `${data.botRunId}:${data.intentId}`;
        mockBotIntents[key] = record;
        return Promise.resolve(record);
      }),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const intent = Object.values(mockBotIntents).find((i) => i.id === where.id) as Record<string, unknown> | undefined;
        if (intent) Object.assign(intent, data, { updatedAt: new Date() });
        return Promise.resolve(intent);
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
const WS_ID = "ws-intent-test";
const USER_ID = "user-intent-1";
const RUN_ID = "run-intent-1";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: USER_ID, email: "intent@test.com" });
});

afterAll(async () => { await app.close(); });

beforeEach(() => {
  Object.keys(mockBotRuns).forEach((k) => delete mockBotRuns[k]);
  Object.keys(mockBotIntents).forEach((k) => delete mockBotIntents[k]);
  mockWorkspaceMemberships.length = 0;
  intentCounter = 0;

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
  mockBotRuns[RUN_ID] = { id: RUN_ID, workspaceId: WS_ID, botId: "bot-1", state: "RUNNING" };
});

function headers() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

// ═══════════════════════════════════════════════════════════════════════════

describe("POST /api/v1/runs/:runId/intents", () => {
  it("creates an intent (201)", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "my-intent-1", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(201);
    expect(res.json().intentId).toBe("my-intent-1");
    expect(res.json().state).toBe("PENDING");
  });

  it("returns existing intent for duplicate intentId (idempotent, 200)", async () => {
    // Create first
    await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "idem-1", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    // Duplicate
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "idem-1", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(200);
  });

  it("returns 400 for missing intentId", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for missing type", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "x", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for non-positive qty", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "x", type: "ENTRY", side: "BUY", qty: -1 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 for nonexistent run", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/runs/nope/intents",
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "x", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { "content-type": "application/json" },
      payload: { intentId: "x", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 403 for non-member workspace", async () => {
    mockWorkspaceMemberships.length = 0;
    const res = await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "x", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    expect(res.statusCode).toBe(403);
  });
});

describe("GET /api/v1/runs/:runId/intents", () => {
  it("returns empty list", async () => {
    const res = await app.inject({ method: "GET", url: `/api/v1/runs/${RUN_ID}/intents`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([]);
  });

  it("returns intents for the run", async () => {
    // Create an intent
    await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "list-1", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    const res = await app.inject({ method: "GET", url: `/api/v1/runs/${RUN_ID}/intents`, headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toHaveLength(1);
  });

  it("returns 404 for nonexistent run", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/runs/nope/intents", headers: headers() });
    expect(res.statusCode).toBe(404);
  });
});

describe("PATCH /api/v1/runs/:runId/intents/:intentId/state", () => {
  it("advances intent state", async () => {
    // Create intent first
    await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "state-1", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/runs/${RUN_ID}/intents/state-1/state`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { state: "PLACED", orderId: "exch-order-123" },
    });
    expect(res.statusCode).toBe(200);
  });

  it("returns 409 for terminal intent state", async () => {
    // Create and set to FILLED
    await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "terminal-1", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    // Manually set to terminal state
    const key = `${RUN_ID}:terminal-1`;
    (mockBotIntents[key] as Record<string, unknown>).state = "FILLED";

    const res = await app.inject({
      method: "PATCH", url: `/api/v1/runs/${RUN_ID}/intents/terminal-1/state`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { state: "CANCELLED" },
    });
    expect(res.statusCode).toBe(409);
  });

  it("returns 404 for nonexistent intent", async () => {
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/runs/${RUN_ID}/intents/nope/state`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { state: "PLACED" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 400 for missing state in body", async () => {
    await app.inject({
      method: "POST", url: `/api/v1/runs/${RUN_ID}/intents`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: { intentId: "bad-state", type: "ENTRY", side: "BUY", qty: 0.01 },
    });
    const res = await app.inject({
      method: "PATCH", url: `/api/v1/runs/${RUN_ID}/intents/bad-state/state`,
      headers: { ...headers(), "content-type": "application/json" },
      payload: {},
    });
    expect(res.statusCode).toBe(400);
  });
});
