import { describe, it, expect, vi } from "vitest";

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

describe("API security headers (§5.8)", () => {
  it("sets strict CSP + hardening headers on every response", async () => {
    const app = await buildApp();
    const res = await app.inject({ method: "GET", url: "/health" });

    expect(res.headers["content-security-policy"]).toBe(
      "default-src 'none'; frame-ancestors 'none'",
    );
    expect(res.headers["x-content-type-options"]).toBe("nosniff");
    expect(res.headers["x-frame-options"]).toBe("DENY");
    expect(res.headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
    expect(res.headers["x-request-id"]).toBeTruthy();

    await app.close();
  });

  it("keeps the strict CSP on /metrics too (API is single source of truth)", async () => {
    const app = await buildApp();
    const res = await app.inject({ method: "GET", url: "/metrics" });
    expect(res.headers["content-security-policy"]).toBe(
      "default-src 'none'; frame-ancestors 'none'",
    );
    await app.close();
  });
});
