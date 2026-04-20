/**
 * Route tests: DLQ / operator UI endpoints on intents.ts (§5.6).
 *
 * Covers: GET /intents  (workspace-scoped list, filterable by state, paginated)
 *         POST /intents/:id/retry  (manual retry of a FAILED intent)
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

interface MockIntent {
  id: string;
  intentId: string;
  orderLinkId: string;
  state: "PENDING" | "PLACED" | "FILLED" | "FAILED" | "CANCELLED";
  type: "ENTRY" | "EXIT";
  side: "BUY" | "SELL";
  qty: number;
  price: number | null;
  retryCount: number;
  metaJson: Record<string, unknown> | null;
  orderId: string | null;
  cumExecQty: number | null;
  avgFillPrice: number | null;
  createdAt: Date;
  updatedAt: Date;
  botRunId: string;
}

const mockIntents: MockIntent[] = [];
const mockBotRuns: Record<string, { id: string; workspaceId: string; symbol: string; state: string; botId: string }> = {};
const mockBotEvents: Array<Record<string, unknown>> = [];
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull", InputJsonValue: {} as never },
}));

function includeBotRun(intent: MockIntent) {
  const run = mockBotRuns[intent.botRunId];
  return {
    ...intent,
    botRun: run
      ? {
          id: run.id,
          symbol: run.symbol,
          state: run.state,
          bot: { id: run.botId, name: `bot-${run.botId}`, symbol: run.symbol },
        }
      : null,
  };
}

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    botRun: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) =>
        Promise.resolve(mockBotRuns[where.id] ?? null),
      ),
    },
    botIntent: {
      findUnique: vi.fn().mockImplementation(({ where, include }: {
        where: { id?: string };
        include?: { botRun?: unknown };
      }) => {
        if (!where.id) return Promise.resolve(null);
        const intent = mockIntents.find((i) => i.id === where.id);
        if (!intent) return Promise.resolve(null);
        if (include?.botRun) {
          const run = mockBotRuns[intent.botRunId];
          return Promise.resolve({
            ...intent,
            botRun: run
              ? { id: run.id, workspaceId: run.workspaceId }
              : { id: intent.botRunId, workspaceId: "" },
          });
        }
        return Promise.resolve(intent);
      }),
      findMany: vi.fn().mockImplementation(({ where, take, skip }: {
        where: { botRun?: { workspaceId?: string }; state?: string };
        take?: number;
        skip?: number;
      }) => {
        let items = [...mockIntents];
        if (where.botRun?.workspaceId) {
          items = items.filter((i) => mockBotRuns[i.botRunId]?.workspaceId === where.botRun!.workspaceId);
        }
        if (where.state) {
          items = items.filter((i) => i.state === where.state);
        }
        items.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
        const sliced = items.slice(skip ?? 0, (skip ?? 0) + (take ?? items.length));
        return Promise.resolve(sliced.map(includeBotRun));
      }),
      count: vi.fn().mockImplementation(({ where }: { where: { botRun?: { workspaceId?: string }; state?: string } }) => {
        let items = [...mockIntents];
        if (where.botRun?.workspaceId) {
          items = items.filter((i) => mockBotRuns[i.botRunId]?.workspaceId === where.botRun!.workspaceId);
        }
        if (where.state) items = items.filter((i) => i.state === where.state);
        return Promise.resolve(items.length);
      }),
      update: vi.fn().mockImplementation(({ where, data, include }: {
        where: { id: string };
        data: Partial<MockIntent>;
        include?: { botRun?: unknown };
      }) => {
        const intent = mockIntents.find((i) => i.id === where.id);
        if (!intent) return Promise.resolve(null);
        Object.assign(intent, data, { updatedAt: new Date() });
        return Promise.resolve(include?.botRun ? includeBotRun(intent) : intent);
      }),
    },
    botEvent: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        mockBotEvents.push(data);
        return Promise.resolve({ id: `event-${mockBotEvents.length}`, ...data });
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(({ where }: {
        where: { workspaceId_userId?: { userId: string; workspaceId: string } };
      }) => {
        const filter = where.workspaceId_userId;
        if (!filter) return Promise.resolve(null);
        const m = mockWorkspaceMemberships.find(
          (x) => x.userId === filter.userId && x.workspaceId === filter.workspaceId,
        );
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
let otherToken: string;
const WS_ID = "ws-dlq-test";
const OTHER_WS_ID = "ws-dlq-other";
const USER_ID = "user-dlq-1";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: USER_ID, email: "dlq@test.com" });
  otherToken = app.jwt.sign({ sub: "user-other", email: "other@test.com" });
});

afterAll(async () => { await app.close(); });

function mkIntent(overrides: Partial<MockIntent> = {}): MockIntent {
  const id = overrides.id ?? `i-${mockIntents.length + 1}`;
  return {
    id,
    intentId: overrides.intentId ?? `intent-${id}`,
    orderLinkId: overrides.orderLinkId ?? `link-${id}`,
    state: overrides.state ?? "FAILED",
    type: overrides.type ?? "ENTRY",
    side: overrides.side ?? "BUY",
    qty: overrides.qty ?? 0.01,
    price: overrides.price ?? null,
    retryCount: overrides.retryCount ?? 1,
    metaJson: overrides.metaJson ?? { error: "HTTP 500", errorClass: "transient" },
    orderId: overrides.orderId ?? null,
    cumExecQty: overrides.cumExecQty ?? null,
    avgFillPrice: overrides.avgFillPrice ?? null,
    createdAt: overrides.createdAt ?? new Date(),
    updatedAt: overrides.updatedAt ?? new Date(),
    botRunId: overrides.botRunId ?? "run-1",
  };
}

beforeEach(() => {
  mockIntents.length = 0;
  mockBotEvents.length = 0;
  mockWorkspaceMemberships.length = 0;
  Object.keys(mockBotRuns).forEach((k) => delete mockBotRuns[k]);

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
  mockBotRuns["run-1"]  = { id: "run-1",  workspaceId: WS_ID,       symbol: "BTCUSDT", state: "RUNNING", botId: "bot-a" };
  mockBotRuns["run-2"]  = { id: "run-2",  workspaceId: OTHER_WS_ID, symbol: "ETHUSDT", state: "RUNNING", botId: "bot-b" };
});

function headers(wsId = WS_ID) {
  return { authorization: `Bearer ${token}`, "x-workspace-id": wsId };
}

// ═══════════════════════════════════════════════════════════════════════════

describe("GET /api/v1/intents (workspace-scoped list, §5.6)", () => {
  it("returns items + total for the current workspace only", async () => {
    mockIntents.push(mkIntent({ id: "i-ws", botRunId: "run-1" }));
    mockIntents.push(mkIntent({ id: "i-other", botRunId: "run-2" }));

    const res = await app.inject({ method: "GET", url: "/api/v1/intents", headers: headers() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.total).toBe(1);
    expect(body.items).toHaveLength(1);
    expect(body.items[0].id).toBe("i-ws");
    expect(body.items[0].botRun.bot.id).toBe("bot-a");
  });

  it("filters by state=FAILED", async () => {
    mockIntents.push(mkIntent({ id: "i-failed", state: "FAILED",   botRunId: "run-1" }));
    mockIntents.push(mkIntent({ id: "i-filled", state: "FILLED",   botRunId: "run-1" }));
    mockIntents.push(mkIntent({ id: "i-pend",   state: "PENDING",  botRunId: "run-1" }));

    const res = await app.inject({ method: "GET", url: "/api/v1/intents?state=FAILED", headers: headers() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.total).toBe(1);
    expect(body.items[0].id).toBe("i-failed");
  });

  it("respects limit + offset pagination", async () => {
    for (let i = 0; i < 5; i++) {
      const createdAt = new Date(Date.now() + i * 1000);
      mockIntents.push(mkIntent({ id: `i-${i}`, botRunId: "run-1", createdAt }));
    }
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/intents?limit=2&offset=1",
      headers: headers(),
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.total).toBe(5);
    expect(body.items).toHaveLength(2);
    expect(body.limit).toBe(2);
    expect(body.offset).toBe(1);
  });

  it("caps limit at 200 to prevent runaway queries", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/intents?limit=10000",
      headers: headers(),
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().limit).toBe(200);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/intents" });
    expect(res.statusCode).toBe(401);
  });

  it("returns empty list when user does not belong to the requested workspace", async () => {
    mockIntents.push(mkIntent({ id: "i-other", botRunId: "run-2" }));
    mockWorkspaceMemberships.length = 0;
    mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/intents",
      headers: { authorization: `Bearer ${otherToken}`, "x-workspace-id": WS_ID },
    });
    expect([401, 403, 404]).toContain(res.statusCode);
  });
});

// ═══════════════════════════════════════════════════════════════════════════

describe("POST /api/v1/intents/:id/retry (§5.6)", () => {
  it("resets a FAILED intent to PENDING and emits a BotEvent", async () => {
    mockIntents.push(mkIntent({ id: "i-retry", state: "FAILED", botRunId: "run-1" }));

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/intents/i-retry/retry",
      headers: headers(),
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.state).toBe("PENDING");
    expect(body.metaJson.manualRetryAt).toBeTruthy();
    expect(body.metaJson.previousState).toBe("FAILED");

    expect(mockBotEvents).toHaveLength(1);
    expect((mockBotEvents[0] as { type: string }).type).toBe("intent_manually_retried");
  });

  it("rejects retry on a non-FAILED intent (409)", async () => {
    mockIntents.push(mkIntent({ id: "i-pend", state: "PENDING", botRunId: "run-1" }));

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/intents/i-pend/retry",
      headers: headers(),
    });
    expect(res.statusCode).toBe(409);
    expect(mockBotEvents).toHaveLength(0);
  });

  it("returns 404 for an intent in a different workspace", async () => {
    mockIntents.push(mkIntent({ id: "i-other", state: "FAILED", botRunId: "run-2" }));

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/intents/i-other/retry",
      headers: headers(),
    });
    expect(res.statusCode).toBe(404);
    expect(mockBotEvents).toHaveLength(0);
  });

  it("returns 404 for a nonexistent intent id", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/intents/does-not-exist/retry",
      headers: headers(),
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/intents/x/retry" });
    expect(res.statusCode).toBe(401);
  });
});
