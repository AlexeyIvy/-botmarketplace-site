/**
 * POST /client-errors — error reporting endpoint tests (Task #23)
 */

import { describe, it, expect, vi } from "vitest";

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  })),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    $queryRaw: vi.fn().mockResolvedValue([{ "?column?": 1 }]),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
    botRun: { count: vi.fn().mockResolvedValue(0) },
  },
}));

vi.mock("../../src/lib/botWorker.js", () => ({
  lastPollTimestampMs: Date.now(),
  POLL_INTERVAL_MS: 4000,
  startBotWorker: vi.fn(),
}));

import { buildApp } from "../../src/app.js";

describe("POST /api/v1/client-errors", () => {
  it("returns 204 for valid error report", async () => {
    const app = await buildApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/client-errors",
      payload: {
        message: "Cannot read property 'foo' of undefined",
        stack: "TypeError: Cannot read...\n  at Component",
        url: "https://botmarketplace.store/terminal",
        timestamp: new Date().toISOString(),
      },
    });

    expect(res.statusCode).toBe(204);
    await app.close();
  });

  it("returns 400 for missing message", async () => {
    const app = await buildApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/client-errors",
      payload: { stack: "some stack" },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 400 for empty body", async () => {
    const app = await buildApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/client-errors",
      payload: {},
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("does not require authentication", async () => {
    const app = await buildApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/client-errors",
      payload: { message: "Error before login" },
    });

    // Should succeed without Bearer token
    expect(res.statusCode).toBe(204);
    await app.close();
  });

  it("accepts minimal payload (message only)", async () => {
    const app = await buildApp();

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/client-errors",
      payload: { message: "Something broke" },
    });

    expect(res.statusCode).toBe(204);
    await app.close();
  });

  it("rate-limits at 3 requests per minute", async () => {
    const app = await buildApp();

    // Send 4 requests — first 3 should succeed, 4th should be rate-limited
    const results: number[] = [];
    for (let i = 0; i < 4; i++) {
      const res = await app.inject({
        method: "POST",
        url: "/api/v1/client-errors",
        payload: { message: `Error ${i}` },
        remoteAddress: "10.0.0.99", // consistent source IP for rate limiting
      });
      results.push(res.statusCode);
    }

    // First 3: 204 (success)
    expect(results.slice(0, 3).every((c) => c === 204)).toBe(true);
    // 4th: 429 (rate limited)
    expect(results[3]).toBe(429);

    await app.close();
  });
});
