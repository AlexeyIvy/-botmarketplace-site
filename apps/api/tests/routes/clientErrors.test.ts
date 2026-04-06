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

  it("rate-limits at 10 requests per minute", async () => {
    const app = await buildApp();

    // Send 11 requests — first 10 should succeed, 11th should be rate-limited
    const results: number[] = [];
    for (let i = 0; i < 11; i++) {
      const res = await app.inject({
        method: "POST",
        url: "/api/v1/client-errors",
        payload: { message: `Error ${i}` },
        remoteAddress: "10.0.0.99", // consistent source IP for rate limiting
      });
      results.push(res.statusCode);
    }

    // First 10: 204 (success)
    expect(results.slice(0, 10).every((c) => c === 204)).toBe(true);
    // 11th: 429 (rate limited)
    expect(results[10]).toBe(429);

    await app.close();
  });
});
