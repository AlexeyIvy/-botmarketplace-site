import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

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

const captureException = vi.fn();
const withScope = vi.fn((cb: (s: { setTag: ReturnType<typeof vi.fn>; setContext: ReturnType<typeof vi.fn> }) => void) =>
  cb({ setTag: vi.fn(), setContext: vi.fn() }),
);
const init = vi.fn();

vi.mock("@sentry/node", () => ({
  init,
  captureException,
  withScope,
}));

describe("Sentry integration", () => {
  beforeEach(() => {
    vi.resetModules();
    captureException.mockClear();
    withScope.mockClear();
    init.mockClear();
    delete process.env.SENTRY_DSN;
  });

  afterEach(() => {
    delete process.env.SENTRY_DSN;
  });

  it("initSentry is a no-op when SENTRY_DSN is unset", async () => {
    const { initSentry, isSentryEnabled } = await import("../../src/lib/sentry.js");
    initSentry();
    expect(init).not.toHaveBeenCalled();
    expect(isSentryEnabled()).toBe(false);
  });

  it("initSentry calls Sentry.init when SENTRY_DSN is set", async () => {
    process.env.SENTRY_DSN = "https://public@sentry.example.com/1";
    const { initSentry, isSentryEnabled } = await import("../../src/lib/sentry.js");
    initSentry();
    expect(init).toHaveBeenCalledTimes(1);
    expect(isSentryEnabled()).toBe(true);
  });

  it("app starts and serves /health without SENTRY_DSN", async () => {
    const { buildApp } = await import("../../src/app.js");
    const app = await buildApp();
    const res = await app.inject({ method: "GET", url: "/health" });
    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("captures exceptions to Sentry when a route throws a 5xx error", async () => {
    process.env.SENTRY_DSN = "https://public@sentry.example.com/1";
    const { initSentry } = await import("../../src/lib/sentry.js");
    initSentry();

    const { buildApp } = await import("../../src/app.js");
    const app = await buildApp();
    app.get("/boom", async () => {
      throw new Error("kaboom");
    });

    const res = await app.inject({ method: "GET", url: "/boom" });
    expect(res.statusCode).toBe(500);
    expect(captureException).toHaveBeenCalledTimes(1);
    expect(withScope).toHaveBeenCalledTimes(1);
    await app.close();
  });
});
