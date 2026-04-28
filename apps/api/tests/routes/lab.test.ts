/**
 * lab.ts — route tests (#235)
 * Tests graph CRUD, backtest trigger, sweep endpoints.
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock stores ─────────────────────────────────────────────────────────────

const mockGraphs: Record<string, unknown> = {};
const mockBacktests: Record<string, unknown> = {};
const mockSweeps: Record<string, unknown> = {};
const mockStrategyVersions: Record<string, unknown> = {};
const mockStrategies: Record<string, unknown> = {};
const mockDatasets: Record<string, unknown> = {};
const mockJournalEntries: Record<string, unknown> = {};
const mockGraphVersions: Record<string, unknown> = {};
const mockWorkspaceMemberships: unknown[] = [];
let graphIdCounter = 0;
let gvIdCounter = 0;

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull", InputJsonValue: {} as never },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    strategyGraph: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `graph-${++graphIdCounter}`;
        const record = { id, ...data, blockLibraryVersion: 1, dslVersionTarget: 2, validationSummaryJson: null, createdAt: new Date(), updatedAt: new Date() };
        mockGraphs[id] = record;
        return Promise.resolve(record);
      }),
      findMany: vi.fn().mockImplementation(() => Promise.resolve(Object.values(mockGraphs))),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockGraphs[where.id] ?? null);
      }),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const existing = mockGraphs[where.id] as Record<string, unknown> | undefined;
        if (existing) Object.assign(existing, data, { updatedAt: new Date() });
        return Promise.resolve(existing);
      }),
    },
    strategyVersion: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockStrategyVersions[where.id] ?? null);
      }),
      findMany: vi.fn().mockResolvedValue([]),
      findFirst: vi.fn().mockResolvedValue(null),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `sv-${Date.now()}`;
        const record = { id, ...data, createdAt: new Date() };
        mockStrategyVersions[id] = record;
        return Promise.resolve(record);
      }),
    },
    strategyGraphVersion: {
      count: vi.fn().mockResolvedValue(0),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `gv-${++gvIdCounter}`;
        const record = { id, ...data, label: null, isBaseline: false, createdAt: new Date() };
        mockGraphVersions[id] = record;
        return Promise.resolve(record);
      }),
      findUnique: vi.fn().mockImplementation(({ where, include }: { where: { id: string }; include?: unknown }) => {
        const gv = mockGraphVersions[where.id] as Record<string, unknown> | undefined;
        if (!gv) return Promise.resolve(null);
        const result: Record<string, unknown> = { ...gv };
        if (include) {
          const inc = include as Record<string, unknown>;
          if (inc.strategyGraph) {
            const graph = mockGraphs[gv.strategyGraphId as string] as Record<string, unknown> | undefined;
            result.strategyGraph = graph ? { workspaceId: graph.workspaceId, name: graph.name } : null;
          }
          if (inc.strategyVersion) {
            const sv = mockStrategyVersions[gv.strategyVersionId as string] as Record<string, unknown> | undefined;
            result.strategyVersion = sv ? { strategyId: sv.strategyId } : null;
          }
        }
        return Promise.resolve(result);
      }),
      findFirst: vi.fn().mockImplementation(({ where }: { where: Record<string, unknown> }) => {
        const svId = where.strategyVersionId as string | undefined;
        if (svId) {
          const found = Object.values(mockGraphVersions).find((gv) => (gv as Record<string, unknown>).strategyVersionId === svId);
          if (found) {
            const gv = found as Record<string, unknown>;
            const graph = mockGraphs[gv.strategyGraphId as string] as Record<string, unknown> | undefined;
            return Promise.resolve({ ...gv, strategyGraph: graph ? { name: graph.name } : null });
          }
        }
        return Promise.resolve(null);
      }),
      findMany: vi.fn().mockImplementation(({ where }: { where?: Record<string, unknown> } = {}) => {
        let items = Object.values(mockGraphVersions) as Record<string, unknown>[];
        if (where?.strategyGraphId) items = items.filter((v) => v.strategyGraphId === where.strategyGraphId);
        if (where?.isBaseline) items = items.filter((v) => v.isBaseline === true);
        if (where?.strategyVersion) {
          const sv = where.strategyVersion as Record<string, unknown>;
          if (sv.strategyId) {
            items = items.filter((v) => {
              const svRecord = mockStrategyVersions[v.strategyVersionId as string] as Record<string, unknown> | undefined;
              return svRecord?.strategyId === sv.strategyId;
            });
          }
        }
        return Promise.resolve(items);
      }),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const existing = mockGraphVersions[where.id] as Record<string, unknown> | undefined;
        if (existing) Object.assign(existing, data);
        return Promise.resolve(existing);
      }),
    },
    strategy: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id?: string; workspaceId_name?: unknown } }) => {
        if (where.id) return Promise.resolve(mockStrategies[where.id] ?? null);
        return Promise.resolve(null);
      }),
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `strat-${Date.now()}`;
        const record = { id, ...data };
        mockStrategies[id] = record;
        return Promise.resolve(record);
      }),
    },
    backtestResult: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `bt-${Date.now()}`;
        const record = { id, ...data, createdAt: new Date(), updatedAt: new Date(), reportJson: null, errorMessage: null };
        mockBacktests[id] = record;
        return Promise.resolve(record);
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockBacktests[where.id] ?? null);
      }),
      findMany: vi.fn().mockImplementation(() => Promise.resolve(Object.values(mockBacktests))),
      update: vi.fn().mockResolvedValue({}),
    },
    backtestSweep: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `sweep-${Date.now()}`;
        const record = { id, ...data, progress: 0, resultsJson: null, bestParamValue: null, createdAt: new Date(), updatedAt: new Date() };
        mockSweeps[id] = record;
        return Promise.resolve(record);
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockSweeps[where.id] ?? null);
      }),
      findMany: vi.fn().mockImplementation(() => Promise.resolve(Object.values(mockSweeps))),
      count: vi.fn().mockResolvedValue(0),
      update: vi.fn().mockResolvedValue({}),
    },
    marketDataset: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockDatasets[where.id] ?? null);
      }),
    },
    marketCandle: {
      findMany: vi.fn().mockResolvedValue([]),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(() => {
        const m = mockWorkspaceMemberships[0] as Record<string, unknown> | undefined;
        if (!m) return Promise.resolve(null);
        return Promise.resolve({ ...m, workspace: { id: m.workspaceId, name: "Test" } });
      }),
    },
    labJournalEntry: {
      create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
        const id = `je-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
        const record = { id, ...data, createdAt: new Date(), updatedAt: new Date() };
        mockJournalEntries[id] = record;
        return Promise.resolve(record);
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockJournalEntries[where.id] ?? null);
      }),
      findMany: vi.fn().mockImplementation(() => Promise.resolve(Object.values(mockJournalEntries))),
      update: vi.fn().mockImplementation(({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const existing = mockJournalEntries[where.id] as Record<string, unknown> | undefined;
        if (!existing) return Promise.resolve(null);
        const updated = { ...existing, ...data, updatedAt: new Date() };
        mockJournalEntries[where.id] = updated;
        return Promise.resolve(updated);
      }),
      delete: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        delete mockJournalEntries[where.id];
        return Promise.resolve({});
      }),
    },
    $queryRaw: vi.fn().mockResolvedValue([]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
}));

vi.mock("../../src/lib/graphCompiler.js", () => ({
  compileGraph: vi.fn().mockReturnValue({
    ok: true,
    compiledDsl: { id: "test", name: "test", dslVersion: 2 },
    validationIssues: [],
  }),
}));

vi.mock("../../src/lib/backtest.js", () => ({
  runBacktest: vi.fn().mockReturnValue({ trades: 0, totalPnlPct: 0 }),
}));

vi.mock("../../src/lib/dslValidator.js", () => ({
  validateDsl: vi.fn().mockReturnValue(null),
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ────────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;

const WS_ID = "ws-test-123";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: "test-user-id", email: "test@test.com" });
});

afterAll(async () => {
  await app.close();
});

beforeEach(() => {
  Object.keys(mockGraphs).forEach((k) => delete mockGraphs[k]);
  Object.keys(mockBacktests).forEach((k) => delete mockBacktests[k]);
  Object.keys(mockSweeps).forEach((k) => delete mockSweeps[k]);
  Object.keys(mockStrategyVersions).forEach((k) => delete mockStrategyVersions[k]);
  Object.keys(mockStrategies).forEach((k) => delete mockStrategies[k]);
  Object.keys(mockDatasets).forEach((k) => delete mockDatasets[k]);
  Object.keys(mockGraphVersions).forEach((k) => delete mockGraphVersions[k]);
  Object.keys(mockJournalEntries).forEach((k) => delete mockJournalEntries[k]);
  mockWorkspaceMemberships.length = 0;
  mockWorkspaceMemberships.push({ workspaceId: WS_ID, userId: "test-user-id", role: "OWNER" });
  graphIdCounter = 0;
  gvIdCounter = 0;
});

function authHeaders() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

// ── POST /lab/graphs ────────────────────────────────────────────────────────

describe("POST /api/v1/lab/graphs", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graphs", payload: { name: "x", graphJson: {} } });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 when name is missing", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graphs", headers: authHeaders(), payload: { graphJson: {} } });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when graphJson is missing", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graphs", headers: authHeaders(), payload: { name: "Test" } });
    expect(res.statusCode).toBe(400);
  });

  it("creates graph with 201", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/graphs",
      headers: authHeaders(),
      payload: { name: "My Graph", graphJson: { nodes: [], edges: [] } },
    });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.name).toBe("My Graph");
    expect(body.id).toBeDefined();
  });
});

// ── GET /lab/graphs ─────────────────────────────────────────────────────────

describe("GET /api/v1/lab/graphs", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graphs" });
    expect(res.statusCode).toBe(401);
  });

  it("returns list of graphs", async () => {
    mockGraphs["g-1"] = { id: "g-1", workspaceId: WS_ID, name: "Graph 1", graphJson: {} };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graphs", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toBeInstanceOf(Array);
  });
});

// ── GET /lab/graphs/:id ─────────────────────────────────────────────────────

describe("GET /api/v1/lab/graphs/:id", () => {
  it("returns 404 for nonexistent graph", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graphs/nonexistent", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("returns graph when found", async () => {
    mockGraphs["g-1"] = { id: "g-1", workspaceId: WS_ID, name: "Graph 1", graphJson: {} };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graphs/g-1", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json().name).toBe("Graph 1");
  });

  it("returns 404 for graph in another workspace", async () => {
    mockGraphs["g-other"] = { id: "g-other", workspaceId: "ws-other", name: "Other" };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graphs/g-other", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });
});

// ── PATCH /lab/graphs/:id ───────────────────────────────────────────────────

describe("PATCH /api/v1/lab/graphs/:id", () => {
  it("returns 404 when graph not found", async () => {
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graphs/missing", headers: authHeaders(), payload: { name: "X" } });
    expect(res.statusCode).toBe(404);
  });

  it("returns 400 when no fields provided", async () => {
    mockGraphs["g-1"] = { id: "g-1", workspaceId: WS_ID, name: "Graph 1" };
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graphs/g-1", headers: authHeaders(), payload: {} });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when graphJson is not an object", async () => {
    mockGraphs["g-1"] = { id: "g-1", workspaceId: WS_ID, name: "Graph 1" };
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graphs/g-1", headers: authHeaders(), payload: { graphJson: "not-obj" } });
    expect(res.statusCode).toBe(400);
  });

  it("updates graph name", async () => {
    mockGraphs["g-1"] = { id: "g-1", workspaceId: WS_ID, name: "Old", graphJson: {} };
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graphs/g-1", headers: authHeaders(), payload: { name: "New Name" } });
    expect(res.statusCode).toBe(200);
  });
});

// ── POST /lab/backtest ──────────────────────────────────────────────────────

describe("POST /api/v1/lab/backtest", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/backtest", payload: {} });
    expect(res.statusCode).toBe(401);
  });

  it("returns 202 with valid inputs", async () => {
    mockStrategyVersions["sv-1"] = { id: "sv-1", strategyId: "strat-1", strategy: { workspaceId: WS_ID }, dslJson: {} };
    mockDatasets["ds-1"] = { id: "ds-1", workspaceId: WS_ID, exchange: "bybit", symbol: "BTCUSDT", interval: "M15", fromTsMs: BigInt(1704067200000), toTsMs: BigInt(1706745600000), datasetHash: "abc" };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: authHeaders(),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1" },
    });
    expect(res.statusCode).toBe(202);
    const body = res.json();
    expect(body.status).toBe("PENDING");
  });

  it("returns 400 when strategyVersionId is missing", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: authHeaders(),
      payload: { datasetId: "ds-1" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when datasetId is missing", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: authHeaders(),
      payload: { strategyVersionId: "sv-1" },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 for invalid feeBps", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: authHeaders(),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1", feeBps: -1 },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 when strategyVersion not found", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: authHeaders(),
      payload: { strategyVersionId: "sv-missing", datasetId: "ds-1" },
    });
    expect(res.statusCode).toBe(404);
  });

  // 46-T4: fillAt now accepts OPEN | CLOSE | NEXT_OPEN. Each test uses a
  // distinct X-Forwarded-For so the per-route rate-limit (5 req/min/ip) is
  // not exhausted by the existing six tests above.
  const fillAtHeaders = (ip: string) => ({ ...authHeaders(), "x-forwarded-for": ip });

  it("46-T4: accepts fillAt=OPEN and persists it", async () => {
    mockStrategyVersions["sv-1"] = { id: "sv-1", strategyId: "strat-1", strategy: { workspaceId: WS_ID }, dslJson: {} };
    mockDatasets["ds-1"] = { id: "ds-1", workspaceId: WS_ID, exchange: "bybit", symbol: "BTCUSDT", interval: "M15", fromTsMs: BigInt(1704067200000), toTsMs: BigInt(1706745600000), datasetHash: "abc" };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: fillAtHeaders("10.46.4.1"),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1", fillAt: "OPEN" },
    });
    expect(res.statusCode).toBe(202);
    expect(res.json().fillAt).toBe("OPEN");
  });

  it("46-T4: accepts fillAt=NEXT_OPEN and persists it", async () => {
    mockStrategyVersions["sv-1"] = { id: "sv-1", strategyId: "strat-1", strategy: { workspaceId: WS_ID }, dslJson: {} };
    mockDatasets["ds-1"] = { id: "ds-1", workspaceId: WS_ID, exchange: "bybit", symbol: "BTCUSDT", interval: "M15", fromTsMs: BigInt(1704067200000), toTsMs: BigInt(1706745600000), datasetHash: "abc" };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: fillAtHeaders("10.46.4.2"),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1", fillAt: "NEXT_OPEN" },
    });
    expect(res.statusCode).toBe(202);
    expect(res.json().fillAt).toBe("NEXT_OPEN");
  });

  it("46-T4: rejects unknown fillAt with 400", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: fillAtHeaders("10.46.4.3"),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1", fillAt: "BOGUS" },
    });
    expect(res.statusCode).toBe(400);
    const body = res.json();
    expect(JSON.stringify(body)).toContain("fillAt");
  });

  it("46-T4: defaults fillAt to CLOSE when omitted", async () => {
    mockStrategyVersions["sv-1"] = { id: "sv-1", strategyId: "strat-1", strategy: { workspaceId: WS_ID }, dslJson: {} };
    mockDatasets["ds-1"] = { id: "ds-1", workspaceId: WS_ID, exchange: "bybit", symbol: "BTCUSDT", interval: "M15", fromTsMs: BigInt(1704067200000), toTsMs: BigInt(1706745600000), datasetHash: "abc" };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: fillAtHeaders("10.46.4.4"),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1" },
    });
    expect(res.statusCode).toBe(202);
    expect(res.json().fillAt).toBe("CLOSE");
  });

  it("46-T4: takerFeeBps overrides legacy feeBps in persisted feeBps column", async () => {
    mockStrategyVersions["sv-1"] = { id: "sv-1", strategyId: "strat-1", strategy: { workspaceId: WS_ID }, dslJson: {} };
    mockDatasets["ds-1"] = { id: "ds-1", workspaceId: WS_ID, exchange: "bybit", symbol: "BTCUSDT", interval: "M15", fromTsMs: BigInt(1704067200000), toTsMs: BigInt(1706745600000), datasetHash: "abc" };

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest",
      headers: fillAtHeaders("10.46.4.5"),
      payload: { strategyVersionId: "sv-1", datasetId: "ds-1", feeBps: 10, takerFeeBps: 30 },
    });
    expect(res.statusCode).toBe(202);
    // The canonical taker fee wins over the deprecated alias.
    expect(res.json().feeBps).toBe(30);
  });
});

// ── GET /lab/backtest/:id ───────────────────────────────────────────────────

describe("GET /api/v1/lab/backtest/:id", () => {
  it("returns 404 for nonexistent backtest", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtest/missing", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("returns backtest when found", async () => {
    mockBacktests["bt-1"] = { id: "bt-1", workspaceId: WS_ID, status: "DONE" };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtest/bt-1", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
  });
});

// ── GET /lab/backtests ──────────────────────────────────────────────────────

describe("GET /api/v1/lab/backtests", () => {
  it("returns list", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toBeInstanceOf(Array);
  });
});

// ── POST /lab/backtest/sweep ────────────────────────────────────────────────

describe("POST /api/v1/lab/backtest/sweep", () => {
  it("returns 400 when required fields missing", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/backtest/sweep", headers: authHeaders(), payload: {} });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when sweepParam fields invalid", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest/sweep",
      headers: authHeaders(),
      payload: {
        datasetId: "ds-1",
        strategyVersionId: "sv-1",
        sweepParam: { blockId: "b1", paramName: "p1", from: "bad", to: 10, step: 1 },
      },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when from >= to", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest/sweep",
      headers: authHeaders(),
      payload: {
        datasetId: "ds-1",
        strategyVersionId: "sv-1",
        sweepParam: { blockId: "b1", paramName: "p1", from: 10, to: 5, step: 1 },
      },
    });
    expect(res.statusCode).toBe(400);
  });

  it("returns 422 when sweep exceeds 20 runs", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest/sweep",
      headers: authHeaders(),
      payload: {
        datasetId: "ds-1",
        strategyVersionId: "sv-1",
        sweepParam: { blockId: "b1", paramName: "p1", from: 1, to: 100, step: 1 },
      },
    });
    expect(res.statusCode).toBe(422);
  });

  // 46-T4: sweep accepts and persists fillAt.
  it("46-T4: rejects unknown fillAt with 400", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/lab/backtest/sweep",
      headers: authHeaders(),
      payload: {
        datasetId: "ds-1",
        strategyVersionId: "sv-1",
        sweepParam: { blockId: "b1", paramName: "p1", from: 1, to: 5, step: 1 },
        fillAt: "BOGUS",
      },
    });
    expect(res.statusCode).toBe(400);
  });
});

// ── GET /lab/backtest/sweep/:id ─────────────────────────────────────────────

describe("GET /api/v1/lab/backtest/sweep/:id", () => {
  it("returns 404 when not found", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtest/sweep/missing", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("returns sweep when found", async () => {
    mockSweeps["sw-1"] = { id: "sw-1", workspaceId: WS_ID, status: "DONE", progress: 5, runCount: 5, resultsJson: [], createdAt: new Date(), updatedAt: new Date() };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtest/sweep/sw-1", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json().status).toBe("done");
  });
});

// ── GET /lab/backtest/sweeps ────────────────────────────────────────────────

describe("GET /api/v1/lab/backtest/sweeps", () => {
  it("returns list", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtest/sweeps", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toBeInstanceOf(Array);
  });
});

// ── GET /lab/backtests/compare ──────────────────────────────────────────────

describe("GET /api/v1/lab/backtests/compare", () => {
  it("returns 400 when query params missing", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare", headers: authHeaders() });
    expect(res.statusCode).toBe(400);
  });

  it("returns 400 when comparing run with itself", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=bt-1&b=bt-1", headers: authHeaders() });
    expect(res.statusCode).toBe(400);
  });

  it("returns 404 when run A not found", async () => {
    mockBacktests["bt-2"] = { id: "bt-2", workspaceId: WS_ID, status: "DONE", reportJson: { totalPnlPct: 5, winrate: 60, maxDrawdownPct: 3, trades: 10 } };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=missing&b=bt-2", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 when run B not found", async () => {
    mockBacktests["bt-1"] = { id: "bt-1", workspaceId: WS_ID, status: "DONE", reportJson: { totalPnlPct: 10, winrate: 55, maxDrawdownPct: 5, trades: 20 } };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=bt-1&b=missing", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 for cross-workspace access", async () => {
    mockBacktests["bt-1"] = { id: "bt-1", workspaceId: WS_ID, status: "DONE", reportJson: {} };
    mockBacktests["bt-other"] = { id: "bt-other", workspaceId: "ws-other", status: "DONE", reportJson: {} };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=bt-1&b=bt-other", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("returns comparison with delta on success", async () => {
    mockBacktests["bt-a"] = { id: "bt-a", workspaceId: WS_ID, status: "DONE", reportJson: { totalPnlPct: 15.5, winrate: 62, maxDrawdownPct: 5.2, trades: 50, sharpe: 1.24 }, feeBps: 10, slippageBps: 5, engineVersion: "abc123" };
    mockBacktests["bt-b"] = { id: "bt-b", workspaceId: WS_ID, status: "DONE", reportJson: { totalPnlPct: 12.3, winrate: 58.5, maxDrawdownPct: 7.1, trades: 48, sharpe: 0.98 }, feeBps: 10, slippageBps: 5, engineVersion: "abc123" };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=bt-a&b=bt-b", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.a.id).toBe("bt-a");
    expect(body.b.id).toBe("bt-b");
    expect(body.delta.pnlDelta).toBeCloseTo(3.2, 1);
    expect(body.delta.winrateDelta).toBeCloseTo(3.5, 1);
    expect(body.delta.tradeDelta).toBe(2);
    expect(body.delta.sharpeDelta).toBeCloseTo(0.26, 2);
  });

  it("returns null deltas when reports missing fields", async () => {
    mockBacktests["bt-x"] = { id: "bt-x", workspaceId: WS_ID, status: "DONE", reportJson: {} };
    mockBacktests["bt-y"] = { id: "bt-y", workspaceId: WS_ID, status: "DONE", reportJson: null };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=bt-x&b=bt-y", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.delta.pnlDelta).toBeNull();
    expect(body.delta.winrateDelta).toBeNull();
  });

  it("includes lineage data in compare response", async () => {
    mockGraphs["g-lin"] = { id: "g-lin", workspaceId: WS_ID, name: "My Strategy", graphJson: {} };
    mockStrategyVersions["sv-lin"] = { id: "sv-lin", strategyId: "strat-lin" };
    mockGraphVersions["gv-lin"] = { id: "gv-lin", strategyGraphId: "g-lin", strategyVersionId: "sv-lin", version: 1, label: "baseline-run", isBaseline: true };
    mockBacktests["bt-l1"] = { id: "bt-l1", workspaceId: WS_ID, strategyVersionId: "sv-lin", status: "DONE", reportJson: { totalPnlPct: 10 } };
    mockBacktests["bt-l2"] = { id: "bt-l2", workspaceId: WS_ID, strategyVersionId: null, status: "DONE", reportJson: { totalPnlPct: 5 } };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/backtests/compare?a=bt-l1&b=bt-l2", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.a.lineage).toBeTruthy();
    expect(body.a.lineage.label).toBe("baseline-run");
    expect(body.a.lineage.isBaseline).toBe(true);
    expect(body.a.lineage.graphName).toBe("My Strategy");
    expect(body.b.lineage).toBeNull();
  });
});

// ── PATCH /lab/graph-versions/:id (Task 26) ───────────────────────────────

describe("PATCH /api/v1/lab/graph-versions/:id", () => {
  function seedGraphVersion() {
    mockGraphs["g-1"] = { id: "g-1", workspaceId: WS_ID, name: "Test Graph", graphJson: {} };
    mockStrategyVersions["sv-1"] = { id: "sv-1", strategyId: "strat-1" };
    mockGraphVersions["gv-1"] = { id: "gv-1", strategyGraphId: "g-1", strategyVersionId: "sv-1", version: 1, label: null, isBaseline: false, createdAt: new Date() };
  }

  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graph-versions/gv-1", payload: { label: "test" } });
    expect(res.statusCode).toBe(401);
  });

  it("returns 404 for missing graph version", async () => {
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graph-versions/missing", headers: authHeaders(), payload: { label: "test" } });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 for cross-workspace access", async () => {
    mockGraphs["g-other"] = { id: "g-other", workspaceId: "ws-other", name: "Other", graphJson: {} };
    mockGraphVersions["gv-other"] = { id: "gv-other", strategyGraphId: "g-other", strategyVersionId: "sv-x", version: 1, label: null, isBaseline: false, createdAt: new Date() };
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graph-versions/gv-other", headers: authHeaders(), payload: { label: "test" } });
    expect(res.statusCode).toBe(404);
  });

  it("updates label successfully", async () => {
    seedGraphVersion();
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graph-versions/gv-1", headers: authHeaders(), payload: { label: "v2-tighter-stop" } });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.label).toBe("v2-tighter-stop");
    expect(body.id).toBe("gv-1");
  });

  it("clears label with null", async () => {
    seedGraphVersion();
    (mockGraphVersions["gv-1"] as Record<string, unknown>).label = "old-label";
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graph-versions/gv-1", headers: authHeaders(), payload: { label: null } });
    expect(res.statusCode).toBe(200);
    expect(res.json().label).toBeNull();
  });

  it("returns 400 for label over 100 chars", async () => {
    seedGraphVersion();
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/graph-versions/gv-1", headers: authHeaders(), payload: { label: "x".repeat(101) } });
    expect(res.statusCode).toBe(400);
  });
});

// ── POST /lab/graph-versions/:id/baseline (Task 26) ───────────────────────

describe("POST /api/v1/lab/graph-versions/:id/baseline", () => {
  function seedForBaseline() {
    mockGraphs["g-b"] = { id: "g-b", workspaceId: WS_ID, name: "Baseline Graph", graphJson: {} };
    mockStrategies["strat-b"] = { id: "strat-b", workspaceId: WS_ID, name: "Baseline Strategy" };
    mockStrategyVersions["sv-b1"] = { id: "sv-b1", strategyId: "strat-b" };
    mockStrategyVersions["sv-b2"] = { id: "sv-b2", strategyId: "strat-b" };
    mockGraphVersions["gv-b1"] = { id: "gv-b1", strategyGraphId: "g-b", strategyVersionId: "sv-b1", version: 1, label: null, isBaseline: false, createdAt: new Date() };
    mockGraphVersions["gv-b2"] = { id: "gv-b2", strategyGraphId: "g-b", strategyVersionId: "sv-b2", version: 2, label: null, isBaseline: false, createdAt: new Date() };
  }

  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graph-versions/gv-b1/baseline" });
    expect(res.statusCode).toBe(401);
  });

  it("returns 404 for missing graph version", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graph-versions/missing/baseline", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("sets baseline on first call", async () => {
    seedForBaseline();
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graph-versions/gv-b1/baseline", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json().isBaseline).toBe(true);
  });

  it("toggles off when already baseline", async () => {
    seedForBaseline();
    (mockGraphVersions["gv-b1"] as Record<string, unknown>).isBaseline = true;
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graph-versions/gv-b1/baseline", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json().isBaseline).toBe(false);
  });

  it("clears previous baseline when setting new one", async () => {
    seedForBaseline();
    (mockGraphVersions["gv-b1"] as Record<string, unknown>).isBaseline = true;
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graph-versions/gv-b2/baseline", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json().isBaseline).toBe(true);
    // Previous baseline should be cleared
    expect((mockGraphVersions["gv-b1"] as Record<string, unknown>).isBaseline).toBe(false);
  });

  it("returns 404 for cross-workspace access", async () => {
    mockGraphs["g-other2"] = { id: "g-other2", workspaceId: "ws-other", name: "Other", graphJson: {} };
    mockGraphVersions["gv-other2"] = { id: "gv-other2", strategyGraphId: "g-other2", strategyVersionId: "sv-x", version: 1, label: null, isBaseline: false, createdAt: new Date() };
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/graph-versions/gv-other2/baseline", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });
});

// ── GET /lab/graph-versions (Task 26) ─────────────────────────────────────

describe("GET /api/v1/lab/graph-versions", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graph-versions?graphId=g-1" });
    expect(res.statusCode).toBe(401);
  });

  it("returns 400 without strategyId or graphId", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graph-versions", headers: authHeaders() });
    expect(res.statusCode).toBe(400);
  });

  it("returns versions for a graph", async () => {
    mockGraphs["g-list"] = { id: "g-list", workspaceId: WS_ID, name: "List Graph", graphJson: {} };
    mockGraphVersions["gv-l1"] = { id: "gv-l1", strategyGraphId: "g-list", strategyVersionId: "sv-l1", version: 1, label: "first", isBaseline: true, blockLibraryVersion: "0.3.0", createdAt: new Date() };
    mockGraphVersions["gv-l2"] = { id: "gv-l2", strategyGraphId: "g-list", strategyVersionId: "sv-l2", version: 2, label: null, isBaseline: false, blockLibraryVersion: "0.3.0", createdAt: new Date() };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graph-versions?graphId=g-list", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body).toBeInstanceOf(Array);
    expect(body.length).toBe(2);
  });

  it("returns 404 for cross-workspace graph", async () => {
    mockGraphs["g-other3"] = { id: "g-other3", workspaceId: "ws-other", name: "Other", graphJson: {} };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/graph-versions?graphId=g-other3", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });
});

// ── Research Journal CRUD (Task 28) ─────────────────────────────────────────

describe("POST /api/v1/lab/journal", () => {
  it("returns 400 when missing required fields", async () => {
    const res = await app.inject({ method: "POST", url: "/api/v1/lab/journal", headers: authHeaders(), payload: {} });
    expect(res.statusCode).toBe(400);
  });

  it("creates entry with required fields", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/journal", headers: authHeaders(),
      payload: {
        strategyGraphVersionId: "gv-1",
        hypothesis: "Increasing SMA length will reduce noise",
        whatChanged: "SMA length 14 → 20",
        expectedResult: "Fewer false signals, higher winrate",
      },
    });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.hypothesis).toBe("Increasing SMA length will reduce noise");
    expect(body.status).toBe("KEEP_TESTING");
    expect(body.id).toBeTruthy();
  });

  it("returns 400 for invalid status", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/journal", headers: authHeaders(),
      payload: {
        strategyGraphVersionId: "gv-1",
        hypothesis: "test", whatChanged: "test", expectedResult: "test",
        status: "INVALID_STATUS",
      },
    });
    expect(res.statusCode).toBe(400);
  });
});

describe("GET /api/v1/lab/journal", () => {
  it("returns empty array when no entries", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/journal", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([]);
  });

  it("returns entries filtered by graphVersionId", async () => {
    mockJournalEntries["je-1"] = { id: "je-1", workspaceId: WS_ID, strategyGraphVersionId: "gv-1", hypothesis: "H1", whatChanged: "W1", expectedResult: "E1", status: "KEEP_TESTING", createdAt: new Date(), updatedAt: new Date() };
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/journal?graphVersionId=gv-1", headers: authHeaders() });
    expect(res.statusCode).toBe(200);
  });
});

describe("PATCH /api/v1/lab/journal/:id", () => {
  it("returns 404 for non-existent entry", async () => {
    const res = await app.inject({ method: "PATCH", url: "/api/v1/lab/journal/missing", headers: authHeaders(), payload: { hypothesis: "updated" } });
    expect(res.statusCode).toBe(404);
  });

  it("updates existing entry", async () => {
    mockJournalEntries["je-2"] = { id: "je-2", workspaceId: WS_ID, strategyGraphVersionId: "gv-1", hypothesis: "Old", whatChanged: "W", expectedResult: "E", status: "KEEP_TESTING", createdAt: new Date(), updatedAt: new Date() };
    const res = await app.inject({
      method: "PATCH", url: "/api/v1/lab/journal/je-2", headers: authHeaders(),
      payload: { hypothesis: "Updated hypothesis", status: "PROMOTE" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().hypothesis).toBe("Updated hypothesis");
  });
});

describe("DELETE /api/v1/lab/journal/:id", () => {
  it("returns 404 for non-existent entry", async () => {
    const res = await app.inject({ method: "DELETE", url: "/api/v1/lab/journal/missing", headers: authHeaders() });
    expect(res.statusCode).toBe(404);
  });

  it("deletes existing entry", async () => {
    mockJournalEntries["je-3"] = { id: "je-3", workspaceId: WS_ID, strategyGraphVersionId: "gv-1", hypothesis: "H", whatChanged: "W", expectedResult: "E", status: "KEEP_TESTING", createdAt: new Date(), updatedAt: new Date() };
    const res = await app.inject({ method: "DELETE", url: "/api/v1/lab/journal/je-3", headers: authHeaders() });
    expect(res.statusCode).toBe(204);
  });
});

// ── POST /lab/preview ── DSL dry-run preview ─────────────────────────────────

import { prisma as previewPrisma } from "../../src/lib/prisma.js";
import { runBacktest as previewRunBacktest } from "../../src/lib/backtest.js";
import { validateDsl as previewValidateDsl } from "../../src/lib/dslValidator.js";

describe("POST /api/v1/lab/preview", () => {
  const prismaMock = previewPrisma as unknown as {
    marketCandle: { findMany: ReturnType<typeof vi.fn> };
  };
  const backtestMock = previewRunBacktest as unknown as ReturnType<typeof vi.fn>;
  const validatorMock = previewValidateDsl as unknown as ReturnType<typeof vi.fn>;

  const dummyDsl = { market: { exchange: "bybit", symbol: "BTCUSDT" } };
  let ipCounter = 0;

  function makeCandles(n: number) {
    const nowMs = Date.now();
    return Array.from({ length: n }, (_, i) => ({
      openTimeMs: BigInt(nowMs - (n - i) * 15 * 60_000),
      open: 100, high: 101, low: 99, close: 100.5, volume: 10,
    }));
  }

  // Each test gets a unique client IP so the per-route rate-limit bucket is fresh
  // (app.ts sets trustProxy="127.0.0.1" → X-Forwarded-For is honored in tests).
  function previewHeaders() {
    ipCounter += 1;
    const oct = 10 + (ipCounter % 240);
    return { ...authHeaders(), "x-forwarded-for": `10.0.0.${oct}` };
  }

  beforeEach(() => {
    validatorMock.mockReset().mockReturnValue(null);
    backtestMock.mockReset().mockReturnValue({
      trades: 3, wins: 2, winrate: 0.667,
      totalPnlPct: 1.23, maxDrawdownPct: 0.5, candles: 96, tradeLog: [],
    });
    prismaMock.marketCandle.findMany.mockReset().mockResolvedValue(makeCandles(96));
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: { "x-forwarded-for": "10.0.1.1" },
      payload: { dslJson: dummyDsl, symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 200 with report + meta for valid DSL and sufficient candles", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: dummyDsl, symbol: "BTCUSDT", hours: 24 },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.report).toMatchObject({ trades: 3, winrate: 0.667, totalPnlPct: 1.23 });
    expect(body.meta).toMatchObject({ symbol: "BTCUSDT", exchange: "bybit", interval: "M15", hours: 24, candleCount: 96 });
    expect(typeof body.meta.dataAgeMs).toBe("number");
  });

  it("returns 400 when DSL validation fails", async () => {
    validatorMock.mockReturnValueOnce([{ field: "entry", message: "missing" }]);
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: {}, symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().errors).toEqual([{ field: "entry", message: "missing" }]);
  });

  it("returns 400 when symbol is missing", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: dummyDsl },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().errors[0].field).toBe("symbol");
  });

  it("returns 400 when hours exceeds the cap", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: dummyDsl, symbol: "BTCUSDT", hours: 9999 },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().errors[0].field).toBe("hours");
  });

  it("returns 409 when candles < 2", async () => {
    prismaMock.marketCandle.findMany.mockResolvedValueOnce([]);
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: dummyDsl, symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(409);
    expect(res.json().title).toBe("Insufficient Data");
  });

  it("returns 422 when backtest engine throws", async () => {
    backtestMock.mockImplementationOnce(() => { throw new Error("bad indicator"); });
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: dummyDsl, symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(422);
    expect(res.json().detail).toContain("bad indicator");
  });

  it("applies rate limit after 5 requests/minute from the same IP", async () => {
    const headers = { ...authHeaders(), "x-forwarded-for": "10.9.9.9" };
    const payload = { dslJson: dummyDsl, symbol: "BTCUSDT" };
    const results: number[] = [];
    for (let i = 0; i < 6; i++) {
      const res = await app.inject({
        method: "POST", url: "/api/v1/lab/preview",
        headers, payload,
      });
      results.push(res.statusCode);
    }
    expect(results.filter((s) => s === 200).length).toBeLessThanOrEqual(5);
    expect(results).toContain(429);
  });

  // ── strategyVersionId path (Test-tab flow) ────────────────────────────────

  it("resolves DSL from strategyVersionId and uses strategy.symbol by default", async () => {
    mockStrategyVersions["sv-preview-1"] = {
      id: "sv-preview-1",
      strategyId: "strat-preview-1",
      dslJson: dummyDsl,
      strategy: { workspaceId: WS_ID, symbol: "ETHUSDT" },
    };

    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { strategyVersionId: "sv-preview-1" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().meta.symbol).toBe("ETHUSDT");
  });

  it("allows overriding the strategy's symbol via body", async () => {
    mockStrategyVersions["sv-preview-2"] = {
      id: "sv-preview-2",
      strategyId: "strat-preview-2",
      dslJson: dummyDsl,
      strategy: { workspaceId: WS_ID, symbol: "ETHUSDT" },
    };

    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { strategyVersionId: "sv-preview-2", symbol: "SOLUSDT" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().meta.symbol).toBe("SOLUSDT");
  });

  it("returns 404 when strategyVersion belongs to another workspace", async () => {
    mockStrategyVersions["sv-other"] = {
      id: "sv-other",
      strategyId: "strat-other",
      dslJson: dummyDsl,
      strategy: { workspaceId: "ws-different", symbol: "BTCUSDT" },
    };

    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { strategyVersionId: "sv-other" },
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 400 when neither dslJson nor strategyVersionId provided", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().detail).toContain("dslJson or strategyVersionId");
  });

  it("returns 400 when both dslJson and strategyVersionId provided", async () => {
    const res = await app.inject({
      method: "POST", url: "/api/v1/lab/preview",
      headers: previewHeaders(),
      payload: { dslJson: dummyDsl, strategyVersionId: "sv-xyz", symbol: "BTCUSDT" },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().errors[0].message).toContain("mutually exclusive");
  });
});
