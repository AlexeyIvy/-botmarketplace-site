/**
 * Route tests: datasets.ts — Issue #227 (Roadmap V4, Batch 2, B1)
 *
 * Covers: GET /lab/datasets, GET /lab/datasets/:id, GET /lab/datasets/:id/preview
 * Note: POST /lab/datasets is NOT tested here (calls real exchange API).
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockDatasets: Record<string, Record<string, unknown>> = {};
const mockCandles: Array<Record<string, unknown>> = [];
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn(), JsonNull: "DbNull" },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    marketDataset: {
      findMany: vi.fn().mockImplementation(({ where }: { where: { workspaceId: string } }) => {
        return Promise.resolve(
          Object.values(mockDatasets)
            .filter((d) => d.workspaceId === where.workspaceId)
            .sort((a, b) => new Date(b.createdAt as string).getTime() - new Date(a.createdAt as string).getTime()),
        );
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { id: string } }) => {
        return Promise.resolve(mockDatasets[where.id] ?? null);
      }),
    },
    marketCandle: {
      findMany: vi.fn().mockImplementation(() => Promise.resolve(mockCandles)),
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

// Mock exchange fetcher (not used in GET routes, but imported at module level)
vi.mock("../../src/lib/bybitCandles.js", () => ({
  fetchCandles: vi.fn().mockResolvedValue([]),
}));

vi.mock("../../src/lib/datasetHash.js", () => ({
  computeDatasetHash: vi.fn().mockReturnValue("mock-hash"),
}));

vi.mock("../../src/lib/dataQuality.js", () => ({
  computeDataQuality: vi.fn().mockReturnValue({ qualityJson: {}, status: "GOOD" }),
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let token: string;
const WS_ID = "ws-ds-test";
const USER_ID = "user-ds-1";

beforeAll(async () => {
  app = await buildApp();
  token = app.jwt.sign({ sub: USER_ID, email: "ds@test.com" });
});

afterAll(async () => { await app.close(); });

beforeEach(() => {
  Object.keys(mockDatasets).forEach((k) => delete mockDatasets[k]);
  mockCandles.length = 0;
  mockWorkspaceMemberships.length = 0;

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
});

function headers() {
  return { authorization: `Bearer ${token}`, "x-workspace-id": WS_ID };
}

function seedDataset(id = "ds-1", overrides: Record<string, unknown> = {}) {
  const record = {
    id,
    workspaceId: WS_ID,
    exchange: "BYBIT",
    symbol: "BTCUSDT",
    interval: "M15",
    fromTsMs: BigInt(1700000000000),
    toTsMs: BigInt(1700086400000),
    candleCount: 100,
    datasetHash: "abc123",
    qualityJson: { gapCount: 0, totalExpected: 100, totalActual: 100 },
    engineVersion: "v1",
    status: "GOOD",
    name: "Test Dataset",
    fetchedAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
    ...overrides,
  };
  mockDatasets[id] = record;
  return record;
}

// ═══════════════════════════════════════════════════════════════════════════

describe("GET /api/v1/lab/datasets", () => {
  it("returns 200 with empty list", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([]);
  });

  it("returns datasets for the workspace", async () => {
    seedDataset("ds-1");
    seedDataset("ds-2");
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toHaveLength(2);
  });

  it("returns 401 without auth", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets" });
    expect(res.statusCode).toBe(401);
  });

  it("returns 403 for non-member workspace", async () => {
    mockWorkspaceMemberships.length = 0;
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets", headers: headers() });
    expect(res.statusCode).toBe(403);
  });
});

describe("GET /api/v1/lab/datasets/:id", () => {
  it("returns dataset metadata", async () => {
    seedDataset("ds-detail");
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets/ds-detail", headers: headers() });
    expect(res.statusCode).toBe(200);
    expect(res.json().datasetId).toBe("ds-detail");
    expect(res.json().symbol).toBe("BTCUSDT");
  });

  it("returns 404 for nonexistent dataset", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets/nope", headers: headers() });
    expect(res.statusCode).toBe(404);
  });

  it("returns 403 for dataset in another workspace", async () => {
    seedDataset("ds-other", { workspaceId: "ws-other" });
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets/ds-other", headers: headers() });
    expect(res.statusCode).toBe(403);
  });
});

describe("GET /api/v1/lab/datasets/:id/preview", () => {
  it("returns paginated candle rows", async () => {
    seedDataset("ds-preview");
    mockCandles.push(
      { openTimeMs: BigInt(1700000000000), open: "100", high: "102", low: "99", close: "101", volume: "1000" },
      { openTimeMs: BigInt(1700000900000), open: "101", high: "103", low: "100", close: "102", volume: "1100" },
    );
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets/ds-preview/preview", headers: headers() });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.rows).toHaveLength(2);
    expect(body.page).toBe(1);
    expect(body.totalCount).toBe(100);
  });

  it("returns 404 for nonexistent dataset", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets/nope/preview", headers: headers() });
    expect(res.statusCode).toBe(404);
  });

  it("returns 403 for dataset in another workspace", async () => {
    seedDataset("ds-prev-other", { workspaceId: "ws-other" });
    const res = await app.inject({ method: "GET", url: "/api/v1/lab/datasets/ds-prev-other/preview", headers: headers() });
    expect(res.statusCode).toBe(403);
  });
});
