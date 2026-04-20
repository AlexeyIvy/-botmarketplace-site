import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({
    $queryRaw: vi.fn().mockResolvedValue([]),
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
  },
}));

import { buildApp } from "../../src/app.js";
import {
  intentCreatedTotal,
  intentFilledTotal,
  intentFailedTotal,
  register,
} from "../../src/lib/metrics.js";

describe("GET /metrics", () => {
  beforeEach(() => {
    register.resetMetrics();
  });

  it("returns 200 with text/plain content-type", async () => {
    const app = await buildApp();
    const res = await app.inject({ method: "GET", url: "/metrics" });

    expect(res.statusCode).toBe(200);
    expect(res.headers["content-type"]).toMatch(/^text\/plain; version=0\.0\.4/);
    expect(res.payload).toContain("botmarket_intent_created_total");
    expect(res.payload).toContain("botmarket_http_request_duration_seconds");
    await app.close();
  });

  it("records HTTP request duration histogram", async () => {
    const app = await buildApp();
    // Make a request that will be observed
    await app.inject({ method: "GET", url: "/health" });

    const body = await register.metrics();
    expect(body).toMatch(
      /botmarket_http_request_duration_seconds_count\{[^}]*route="\/health"[^}]*\}\s+1/,
    );
    await app.close();
  });

  it("reflects intent counter increments", async () => {
    intentCreatedTotal.inc();
    intentCreatedTotal.inc();
    intentFilledTotal.inc();
    intentFailedTotal.inc();

    const app = await buildApp();
    const res = await app.inject({ method: "GET", url: "/metrics" });
    expect(res.payload).toMatch(/botmarket_intent_created_total(?:\{[^}]*\})?\s+2/);
    expect(res.payload).toMatch(/botmarket_intent_filled_total(?:\{[^}]*\})?\s+1/);
    expect(res.payload).toMatch(/botmarket_intent_failed_total(?:\{[^}]*\})?\s+1/);
    await app.close();
  });
});
