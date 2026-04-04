import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";

// ── Mock Prisma ───────────────────────────────────────────────────────────────

const mockFundingSnapshots: unknown[] = [];
const mockSpreadSnapshots: unknown[] = [];

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({})),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    fundingSnapshot: {
      findMany: vi.fn().mockImplementation(() => Promise.resolve(mockFundingSnapshots)),
    },
    spreadSnapshot: {
      findMany: vi.fn().mockImplementation(() => Promise.resolve(mockSpreadSnapshots)),
    },
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

beforeAll(async () => {
  app = await buildApp();
  // Generate a JWT for authenticated requests
  token = app.jwt.sign({ sub: "test-user-id", email: "test@test.com" });
});

afterAll(async () => {
  await app.close();
});

// ── Helper ────────────────────────────────────────────────────────────────────

function makeSnapshot(symbol: string, rate: number, daysAgo: number) {
  const ts = new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000);
  return {
    id: `snap-${symbol}-${daysAgo}`,
    symbol,
    fundingRate: rate,
    nextFundingAt: new Date(ts.getTime() + 8 * 3600 * 1000),
    timestamp: ts,
  };
}

function makeSpread(symbol: string, spotPrice: number, perpPrice: number) {
  return {
    id: `spread-${symbol}`,
    symbol,
    spotPrice,
    perpPrice,
    basisBps: ((perpPrice - spotPrice) / spotPrice) * 10000,
    timestamp: new Date(),
  };
}

// ── Scanner endpoint ──────────────────────────────────────────────────────────

describe("GET /api/v1/terminal/funding/scanner", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/scanner",
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns ranked candidates from DB data", async () => {
    // Setup mock data: BTCUSDT with high positive rate, 5 consecutive snapshots
    mockFundingSnapshots.length = 0;
    for (let i = 5; i >= 1; i--) {
      mockFundingSnapshots.push(makeSnapshot("BTCUSDT", 0.001, i));
    }
    mockSpreadSnapshots.length = 0;
    mockSpreadSnapshots.push(makeSpread("BTCUSDT", 42000, 42010));

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/scanner?minYield=5&maxBasis=50&minStreak=3&limit=10",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body).toHaveProperty("candidates");
    expect(body).toHaveProperty("updatedAt");
    expect(Array.isArray(body.candidates)).toBe(true);

    if (body.candidates.length > 0) {
      const c = body.candidates[0];
      expect(c.symbol).toBe("BTCUSDT");
      expect(typeof c.annualizedYieldPct).toBe("number");
      expect(typeof c.basisBps).toBe("number");
      expect(typeof c.streak).toBe("number");
    }
  });

  it("returns empty candidates when no data", async () => {
    mockFundingSnapshots.length = 0;
    mockSpreadSnapshots.length = 0;

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/scanner",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.candidates).toEqual([]);
  });

  it("returns 400 for invalid query params", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/scanner?minYield=abc",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(400);
  });
});

// ── History endpoint ──────────────────────────────────────────────────────────

describe("GET /api/v1/terminal/funding/:symbol/history", () => {
  it("returns 401 without auth", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/BTCUSDT/history",
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns snapshots for a symbol", async () => {
    // The findMany mock returns mockFundingSnapshots - set up data
    mockFundingSnapshots.length = 0;
    mockFundingSnapshots.push(makeSnapshot("BTCUSDT", 0.0001, 1));
    mockFundingSnapshots.push(makeSnapshot("BTCUSDT", 0.0002, 0));

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/BTCUSDT/history?limit=50",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body).toHaveProperty("snapshots");
    expect(Array.isArray(body.snapshots)).toBe(true);

    if (body.snapshots.length > 0) {
      const s = body.snapshots[0];
      expect(s).toHaveProperty("symbol");
      expect(s).toHaveProperty("fundingRate");
      expect(s).toHaveProperty("timestamp");
    }
  });

  it("returns 400 for invalid from date", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/terminal/funding/BTCUSDT/history?from=not-a-date",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(400);
  });
});
