/**
 * /readyz — extended health check tests (Roadmap V3, Task #18)
 *
 * Tests worker health, encryption key, stuck runs checks.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  })),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

const mockQueryRaw = vi.fn();
const mockBotRunCount = vi.fn();

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    $queryRaw: (...args: unknown[]) => mockQueryRaw(...args),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
    botRun: {
      count: (...args: unknown[]) => mockBotRunCount(...args),
    },
  },
}));

// Mock botWorker exports — we'll override lastPollTimestampMs per test
let mockLastPollTimestampMs = 0;
vi.mock("../../src/lib/botWorker.js", () => ({
  get lastPollTimestampMs() {
    return mockLastPollTimestampMs;
  },
  POLL_INTERVAL_MS: 4_000,
  startBotWorker: vi.fn(),
}));

import { buildApp } from "../../src/app.js";

async function getApp() {
  const app = await buildApp();
  return app;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("GET /readyz", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockQueryRaw.mockResolvedValue([{ "?column?": 1 }]);
    mockBotRunCount.mockResolvedValue(0);
    mockLastPollTimestampMs = Date.now() - 1000; // 1s ago — healthy
    process.env.SECRET_ENCRYPTION_KEY = "a".repeat(64);
  });

  it("returns 200 with status ok when all checks pass", async () => {
    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("ok");
    expect(body.checks.database.ok).toBe(true);
    expect(body.checks.worker.ok).toBe(true);
    expect(body.checks.encryptionKey.ok).toBe(true);
    expect(body.checks.stuckRuns.ok).toBe(true);

    await app.close();
  });

  it("returns 503 when database is down", async () => {
    mockQueryRaw.mockRejectedValue(new Error("connection refused"));

    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(503);
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("unavailable");
    expect(body.checks.database.ok).toBe(false);

    await app.close();
  });

  it("returns 503 when worker is stale", async () => {
    // Last poll 60 seconds ago — way beyond 3×4s = 12s threshold
    mockLastPollTimestampMs = Date.now() - 60_000;

    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(503);
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("unavailable");
    expect(body.checks.worker.ok).toBe(false);
    expect(body.checks.worker.detail).toContain("stale");

    await app.close();
  });

  it("returns 200 (ok) when worker hasn't polled yet (starting)", async () => {
    mockLastPollTimestampMs = 0;

    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.checks.worker.ok).toBe(true);
    expect(body.checks.worker.detail).toContain("starting");

    await app.close();
  });

  it("returns degraded when encryption key is missing", async () => {
    delete process.env.SECRET_ENCRYPTION_KEY;

    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(200); // not critical — degraded, not 503
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("degraded");
    expect(body.checks.encryptionKey.ok).toBe(false);

    await app.close();
  });

  it("returns degraded when encryption key has wrong length", async () => {
    process.env.SECRET_ENCRYPTION_KEY = "short";

    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("degraded");
    expect(body.checks.encryptionKey.ok).toBe(false);
    expect(body.checks.encryptionKey.detail).toContain("wrong length");

    await app.close();
  });

  it("returns degraded when stuck runs exist", async () => {
    mockBotRunCount.mockResolvedValue(2);

    const app = await getApp();
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("degraded");
    expect(body.checks.stuckRuns.ok).toBe(false);
    expect(body.checks.stuckRuns.detail).toContain("2 run(s) stuck");

    await app.close();
  });

  it("does not require authentication", async () => {
    const app = await getApp();
    // readyz should be accessible without Bearer token
    const res = await app.inject({ method: "GET", url: "/api/v1/readyz" });
    expect(res.statusCode).toBe(200);
    await app.close();
  });
});
