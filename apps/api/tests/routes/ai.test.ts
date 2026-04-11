/**
 * ai.ts — route tests (#235)
 * Tests /ai/status, /ai/chat, /ai/plan, /ai/execute endpoints.
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock stores ─────────────────────────────────────────────────────────────

let mockAiPlans: Record<string, unknown> = {};
let mockAiAudits: Record<string, unknown> = {};
const mockWorkspaceMemberships: unknown[] = [];

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull", InputJsonValue: {} as never },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    aiPlan: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `plan-${Date.now()}`;
        const record = { id, ...data, createdAt: new Date() };
        mockAiPlans[id] = record;
        return Promise.resolve(record);
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockAiPlans[where.id] ?? null);
      }),
    },
    aiActionAudit: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `audit-${Date.now()}`;
        const record = { id, ...data, status: "PROPOSED", createdAt: new Date() };
        mockAiAudits[id] = record;
        return Promise.resolve(record);
      }),
      findFirst: vi.fn().mockResolvedValue(null),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const existing = mockAiAudits[where.id] as Record<string, unknown> | undefined;
        if (existing) Object.assign(existing, data);
        return Promise.resolve(existing);
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(() => {
        const m = mockWorkspaceMemberships[0] as Record<string, unknown> | undefined;
        if (!m) return Promise.resolve(null);
        return Promise.resolve({ ...m, workspace: { id: m.workspaceId, name: "Test" } });
      }),
    },
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

// Mock AI provider
const mockChat = vi.fn();
vi.mock("../../src/lib/ai/provider.js", () => ({
  createProvider: vi.fn().mockImplementation(() => ({
    chat: (...args: unknown[]) => mockChat(...args),
  })),
  getConfiguredModel: vi.fn().mockReturnValue("gpt-4-test"),
  ProviderError: class extends Error {
    providerStatus: number;
    constructor(msg: string, status: number) {
      super(msg);
      this.providerStatus = status;
    }
  },
}));

// Mock AI context builders
vi.mock("../../src/lib/ai/context.js", () => ({
  buildContext: vi.fn().mockResolvedValue({ bots: [], strategies: [] }),
  serializeContext: vi.fn().mockReturnValue("context"),
}));

vi.mock("../../src/lib/ai/prompt.js", () => ({
  buildSystemPrompt: vi.fn().mockReturnValue("system prompt"),
}));

vi.mock("../../src/lib/ai/planContext.js", () => ({
  buildPlanContext: vi.fn().mockResolvedValue({}),
  serializePlanContext: vi.fn().mockReturnValue("plan context"),
}));

vi.mock("../../src/lib/ai/planPrompt.js", () => ({
  buildPlanSystemPrompt: vi.fn().mockReturnValue("plan system prompt"),
}));

vi.mock("../../src/lib/ai/planParser.js", () => ({
  parsePlanResponse: vi.fn().mockReturnValue({
    ok: true,
    actions: [{ actionId: "a1", type: "CREATE_STRATEGY", title: "Create", input: { name: "Test", symbol: "BTCUSDT", timeframe: "M15" } }],
    note: "test plan",
  }),
  buildActionPlan: vi.fn().mockImplementation((planId: string, actions: unknown[], note: unknown) => ({
    planId,
    actions,
    note,
  })),
}));

// Mock action modules
vi.mock("../../src/lib/actions/strategies.js", () => {
  class ActionValidationError extends Error {
    detail: string;
    constructor(detail: string) { super(detail); this.name = "ActionValidationError"; this.detail = detail; }
  }
  class ActionConflictError extends Error {
    detail: string;
    constructor(detail: string) { super(detail); this.name = "ActionConflictError"; this.detail = detail; }
  }
  class ActionNotFoundError extends Error {
    detail: string;
    constructor(detail: string) { super(detail); this.name = "ActionNotFoundError"; this.detail = detail; }
  }
  return {
    createStrategy: vi.fn().mockResolvedValue({ strategyId: "s-1", name: "Test", status: "DRAFT" }),
    validateDslAction: vi.fn().mockResolvedValue({ ok: true }),
    createStrategyVersion: vi.fn().mockResolvedValue({ versionId: "sv-1", version: 1 }),
    ActionValidationError,
    ActionConflictError,
    ActionNotFoundError,
  };
});

vi.mock("../../src/lib/actions/lab.js", () => ({
  runBacktestAction: vi.fn().mockResolvedValue({ backtestId: "bt-1", status: "PENDING" }),
}));

vi.mock("../../src/lib/actions/bots.js", () => ({
  createBot: vi.fn().mockResolvedValue({ botId: "bot-1", name: "Test", status: "DRAFT" }),
}));

vi.mock("../../src/lib/actions/runs.js", () => ({
  startRun: vi.fn().mockResolvedValue({ runId: "run-1", state: "QUEUED" }),
  stopRun: vi.fn().mockResolvedValue({ runId: "run-1", state: "STOPPED" }),
}));

// Mock AI sanitizer
vi.mock("../../src/lib/aiSanitizer.js", () => ({
  sanitizePrompt: vi.fn().mockImplementation((input: string) => ({ safe: true, cleaned: input })),
  sanitizeMessages: vi.fn().mockImplementation((msgs: unknown[]) => ({ messages: msgs, rejection: undefined })),
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ────────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;

const WS_ID = "ws-test-123";

beforeAll(async () => {
  process.env.AI_API_KEY = "test-key";
  process.env.AI_PROVIDER = "openai";
  app = await buildApp();
  token = app.jwt.sign({ sub: "test-user-id", email: "test@test.com" });
});

afterAll(async () => {
  delete process.env.AI_API_KEY;
  delete process.env.AI_PROVIDER;
  await app.close();
});

beforeEach(() => {
  mockAiPlans = {};
  mockAiAudits = {};
  mockWorkspaceMemberships.length = 0;
  mockWorkspaceMemberships.push({ workspaceId: WS_ID, userId: "test-user-id", role: "OWNER" });
  mockChat.mockReset();
});

function authHeaders() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

// ── GET /ai/status ──────────────────────────────────────────────────────────

describe("GET /api/v1/ai/status", () => {
  it("returns available: true when AI_API_KEY is set", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/ai/status" });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.available).toBe(true);
    expect(body.provider).toBeDefined();
    expect(body.model).toBeDefined();
  });
});

// ── POST /ai/chat ───────────────────────────────────────────────────────────

describe("POST /api/v1/ai/chat", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      payload: { messages: [{ role: "user", content: "hi" }] },
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 when messages is empty", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      headers: authHeaders(),
      payload: { messages: [] },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when message role is invalid", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      headers: authHeaders(),
      payload: { messages: [{ role: "system", content: "hi" }] },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when message content is empty", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      headers: authHeaders(),
      payload: { messages: [{ role: "user", content: "" }] },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when content exceeds 4096 chars", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      headers: authHeaders(),
      payload: { messages: [{ role: "user", content: "a".repeat(4097) }] },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when last message is not from user", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      headers: authHeaders(),
      payload: { messages: [{ role: "user", content: "hi" }, { role: "assistant", content: "bye" }] },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns AI reply on success", async () => {
    mockChat.mockResolvedValue("Hello! I can help with your strategy.");

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/chat",
      headers: authHeaders(),
      payload: { messages: [{ role: "user", content: "Help me create a strategy" }] },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.reply).toBe("Hello! I can help with your strategy.");
    expect(body.requestId).toBeDefined();
  });
});

// ── POST /ai/plan ───────────────────────────────────────────────────────────

describe("POST /api/v1/ai/plan", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/ai/plan", payload: { message: "test" } });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 when message is empty", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/plan",
      headers: authHeaders(),
      payload: { message: "" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when message exceeds 2000 chars", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/plan",
      headers: authHeaders(),
      payload: { message: "a".repeat(2001) },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns plan on success", async () => {
    mockChat.mockResolvedValue('{"actions": []}');

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/plan",
      headers: authHeaders(),
      payload: { message: "Create a BTC scalping strategy" },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.planId).toBeDefined();
    expect(body.actions).toBeInstanceOf(Array);
  });
});

// ── POST /ai/execute ────────────────────────────────────────────────────────

describe("POST /api/v1/ai/execute", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      payload: { planId: "p1", actionId: "a1" },
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 when planId is missing", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { actionId: "a1" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when actionId is missing", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "p1" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 when plan not found", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "missing", actionId: "a1" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 403 when plan belongs to another workspace", async () => {
    mockAiPlans["plan-other"] = {
      id: "plan-other",
      workspaceId: "ws-other",
      expiresAt: new Date(Date.now() + 60000),
      planJson: { actions: [] },
    };
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "plan-other", actionId: "a1" },
    });
    expect(res.statusCode).toBe(403);
  });

  it("returns 410 when plan has expired", async () => {
    mockAiPlans["plan-expired"] = {
      id: "plan-expired",
      workspaceId: WS_ID,
      expiresAt: new Date(Date.now() - 60000),
      planJson: { actions: [] },
    };
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "plan-expired", actionId: "a1" },
    });
    expect(res.statusCode).toBe(410);
  });

  it("returns 404 when action not found in plan", async () => {
    mockAiPlans["plan-1"] = {
      id: "plan-1",
      workspaceId: WS_ID,
      expiresAt: new Date(Date.now() + 60000),
      planJson: { actions: [{ actionId: "a1", type: "CREATE_STRATEGY", title: "Test", input: {} }] },
    };
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "plan-1", actionId: "nonexistent" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 400 for unsupported action type", async () => {
    mockAiPlans["plan-bad"] = {
      id: "plan-bad",
      workspaceId: WS_ID,
      expiresAt: new Date(Date.now() + 60000),
      planJson: { actions: [{ actionId: "a1", type: "DELETE_ALL", title: "Bad", input: {} }] },
    };
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "plan-bad", actionId: "a1" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("executes action successfully", async () => {
    mockAiPlans["plan-exec"] = {
      id: "plan-exec",
      workspaceId: WS_ID,
      expiresAt: new Date(Date.now() + 60000),
      planJson: {
        actions: [{ actionId: "a1", type: "CREATE_STRATEGY", title: "Create", input: { name: "Test", symbol: "BTCUSDT", timeframe: "M15" } }],
      },
    };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/ai/execute",
      headers: authHeaders(),
      payload: { planId: "plan-exec", actionId: "a1" },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.status).toBe("EXECUTED");
    expect(body.actionId).toBe("a1");
    expect(body.result).toBeDefined();
  });
});
