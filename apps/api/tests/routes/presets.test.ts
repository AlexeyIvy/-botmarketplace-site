/**
 * Route tests: presets.ts (docs/51-T2 + 51-T3)
 *
 * Covers POST /presets, GET /presets, GET /presets/:slug — visibility scoping,
 * slug regex, DSL validation, admin token gating, 404-not-403 leakage rule —
 * and POST /presets/:slug/instantiate — workspace gating, override merging,
 * transactional Strategy + StrategyVersion + Bot create, and rollback when
 * the Bot.create step fails.
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockPresets: Record<string, Record<string, unknown>> = {};
const mockStrategies: Record<string, Record<string, unknown>> = {};
const mockStrategyVersions: Record<string, Record<string, unknown>> = {};
const mockBots: Record<string, Record<string, unknown>> = {};
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];

let strategyIdCounter = 0;
let strategyVersionIdCounter = 0;
let botIdCounter = 0;

// Test-time hook: the next Bot.create raises this error (one-shot).
let botCreateError: Error | null = null;

// ── Mock Prisma ─────────────────────────────────────────────────────────────

vi.mock("@prisma/client", () => {
  class PrismaClientKnownRequestError extends Error {
    code: string;
    constructor(message: string, opts: { code: string }) {
      super(message);
      this.code = opts.code;
    }
  }
  return {
    PrismaClient: vi.fn().mockImplementation(() => ({})),
    Prisma: {
      sql: vi.fn(),
      join: vi.fn(),
      JsonNull: "DbNull",
      InputJsonValue: {} as never,
      PrismaClientKnownRequestError,
    },
    PresetVisibility: { PRIVATE: "PRIVATE", BETA: "BETA", PUBLIC: "PUBLIC" },
    BotMode: { DSL: "DSL", FUNDING_ARB: "FUNDING_ARB" },
  };
});

vi.mock("../../src/lib/prisma.js", () => {
  // Build a "tx" client whose create methods write to a per-transaction
  // staging buffer. On commit, staging is flushed to the global mocks; on
  // throw, staging is discarded — emulating Prisma rollback semantics.
  function buildTx(staging: {
    strategies: Record<string, Record<string, unknown>>;
    versions: Record<string, Record<string, unknown>>;
    bots: Record<string, Record<string, unknown>>;
  }) {
    return {
      strategy: {
        create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
          const id = `strat-${++strategyIdCounter}`;
          const row = { id, ...data, createdAt: new Date(), updatedAt: new Date() };
          staging.strategies[id] = row;
          return Promise.resolve(row);
        }),
      },
      strategyVersion: {
        create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
          const id = `sv-${++strategyVersionIdCounter}`;
          const row = { id, ...data, createdAt: new Date() };
          staging.versions[id] = row;
          return Promise.resolve(row);
        }),
      },
      bot: {
        create: vi.fn().mockImplementation(({ data }: { data: Record<string, unknown> }) => {
          if (botCreateError) {
            const err = botCreateError;
            botCreateError = null;
            return Promise.reject(err);
          }
          const id = `bot-${++botIdCounter}`;
          const row = { id, ...data, createdAt: new Date(), updatedAt: new Date() };
          staging.bots[id] = row;
          return Promise.resolve(row);
        }),
      },
    };
  }

  const prisma = {
    strategyPreset: {
      create: vi.fn().mockImplementation(async ({ data }: { data: Record<string, unknown> }) => {
        const slug = data.slug as string;
        if (mockPresets[slug]) {
          const { Prisma } = await import("@prisma/client");
          throw new Prisma.PrismaClientKnownRequestError("Unique constraint failed", { code: "P2002" } as never);
        }
        const row = { ...data, createdAt: new Date(), updatedAt: new Date() };
        mockPresets[slug] = row;
        return row;
      }),
      findMany: vi.fn().mockImplementation(({ where, select }: { where: Record<string, unknown>; select?: Record<string, boolean> }) => {
        const visibility = where?.visibility;
        const category = where?.category;
        // Visibility filter supports `value` (eq) and `{ in: [...] }` (Prisma's
        // OR-set), the two shapes the route uses for three-tier scoping.
        const visibilityIn =
          visibility && typeof visibility === "object" && "in" in (visibility as object)
            ? ((visibility as { in: unknown[] }).in)
            : null;
        const matched = Object.values(mockPresets).filter((p) => {
          if (visibilityIn != null) {
            if (!visibilityIn.includes(p.visibility)) return false;
          } else if (visibility !== undefined && p.visibility !== visibility) {
            return false;
          }
          if (category !== undefined && p.category !== category) return false;
          return true;
        });
        const projected = select
          ? matched.map((row) => {
              const out: Record<string, unknown> = {};
              for (const [k, v] of Object.entries(select)) {
                if (v) out[k] = (row as Record<string, unknown>)[k];
              }
              return out;
            })
          : matched;
        return Promise.resolve(projected);
      }),
      findUnique: vi.fn().mockImplementation(({ where }: { where: { slug: string } }) => {
        return Promise.resolve(mockPresets[where.slug] ?? null);
      }),
    },
    workspaceMember: {
      findUnique: vi.fn().mockImplementation(({ where }: { where: { workspaceId_userId: { workspaceId: string; userId: string } } }) => {
        const m = mockWorkspaceMemberships.find(
          (r) =>
            r.workspaceId === where.workspaceId_userId.workspaceId &&
            r.userId === where.workspaceId_userId.userId,
        );
        if (!m) return Promise.resolve(null);
        return Promise.resolve({ ...m, workspace: { id: m.workspaceId, name: "Test WS" } });
      }),
    },
    $transaction: vi.fn().mockImplementation(async (cb: (tx: ReturnType<typeof buildTx>) => Promise<unknown>) => {
      const staging = {
        strategies: {} as Record<string, Record<string, unknown>>,
        versions: {} as Record<string, Record<string, unknown>>,
        bots: {} as Record<string, Record<string, unknown>>,
      };
      const tx = buildTx(staging);
      const result = await cb(tx); // throws → staging is dropped (rollback)
      // Commit: flush staging into the global mocks.
      Object.assign(mockStrategies, staging.strategies);
      Object.assign(mockStrategyVersions, staging.versions);
      Object.assign(mockBots, staging.bots);
      return result;
    }),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  };
  return { prisma };
});

// Validate-DSL stub: accept any object that has `dslVersion` set, reject otherwise.
// This is intentionally narrower than the real validator — we just need a way
// to assert the route calls it before persisting.
vi.mock("../../src/lib/dslValidator.js", () => ({
  validateDsl: vi.fn().mockImplementation((dsl: unknown) => {
    if (!dsl || typeof dsl !== "object") return [{ field: "dslJson", message: "must be object" }];
    if ((dsl as Record<string, unknown>).dslVersion === undefined) {
      return [{ field: "dslVersion", message: "missing" }];
    }
    return null;
  }),
}));

import { buildApp } from "../../src/app.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let userToken: string;
const ADMIN_TOKEN = "test-admin-token-very-secret";
const WS_ID = "ws-preset-test";
const USER_ID = "user-preset-1";

beforeAll(async () => {
  process.env.ADMIN_API_TOKEN = ADMIN_TOKEN;
  app = await buildApp();
  userToken = app.jwt.sign({ sub: USER_ID, email: "preset@test.com" });
});

afterAll(async () => {
  delete process.env.ADMIN_API_TOKEN;
  await app.close();
});

beforeEach(() => {
  Object.keys(mockPresets).forEach((k) => delete mockPresets[k]);
  Object.keys(mockStrategies).forEach((k) => delete mockStrategies[k]);
  Object.keys(mockStrategyVersions).forEach((k) => delete mockStrategyVersions[k]);
  Object.keys(mockBots).forEach((k) => delete mockBots[k]);
  mockWorkspaceMemberships.length = 0;
  strategyIdCounter = 0;
  strategyVersionIdCounter = 0;
  botIdCounter = 0;
  botCreateError = null;

  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
});

// ── Helpers ─────────────────────────────────────────────────────────────────

function adminHeaders() {
  return { "x-admin-token": ADMIN_TOKEN, "content-type": "application/json" };
}

const VALID_DSL = { dslVersion: 1, name: "x" };

const VALID_BODY = {
  slug: "trend-test",
  name: "Trend Test",
  description: "A test preset",
  category: "trend" as const,
  dslJson: VALID_DSL,
  defaultBotConfigJson: {
    symbol: "BTCUSDT",
    timeframe: "M15" as const,
    quoteAmount: 100,
    maxOpenPositions: 1,
  },
};

async function seedPreset(
  slug: string,
  visibility: "PRIVATE" | "BETA" | "PUBLIC",
  category = "trend",
  configOverrides: Record<string, unknown> = {},
) {
  mockPresets[slug] = {
    slug,
    name: `Preset ${slug}`,
    description: `Description ${slug}`,
    category,
    dslJson: VALID_DSL,
    defaultBotConfigJson: {
      symbol: "BTCUSDT",
      timeframe: "M15",
      quoteAmount: 100,
      maxOpenPositions: 1,
      ...configOverrides,
    },
    datasetBundleHintJson: null,
    visibility,
    createdAt: new Date(),
    updatedAt: new Date(),
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// POST /api/v1/presets
// ═══════════════════════════════════════════════════════════════════════════

describe("POST /api/v1/presets", () => {
  it("returns 401 without admin token", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: { "content-type": "application/json" },
      payload: VALID_BODY,
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 401 with wrong admin token", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: { "x-admin-token": "wrong", "content-type": "application/json" },
      payload: VALID_BODY,
    });
    expect(res.statusCode).toBe(401);
  });

  it("rejects uppercase slug (400)", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: { ...VALID_BODY, slug: "Bad-SLUG" },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().errors.some((e: { field: string }) => e.field === "slug")).toBe(true);
  });

  it("rejects invalid category (400)", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: { ...VALID_BODY, category: "bogus" },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().errors.some((e: { field: string }) => e.field === "category")).toBe(true);
  });

  it("rejects DSL that fails validateDsl (400)", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: { ...VALID_BODY, dslJson: { malformed: true } },
    });
    expect(res.statusCode).toBe(400);
    expect(res.json().detail).toMatch(/DSL/);
  });

  it("creates preset (201) and persists with default PRIVATE visibility", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: VALID_BODY,
    });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.slug).toBe(VALID_BODY.slug);
    expect(body.visibility).toBe("PRIVATE");
    expect(mockPresets[VALID_BODY.slug]).toBeDefined();
  });

  it("returns 409 on duplicate slug", async () => {
    const r1 = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: VALID_BODY,
    });
    expect(r1.statusCode).toBe(201);
    const r2 = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: VALID_BODY,
    });
    expect(r2.statusCode).toBe(409);
  });

  it("rejects defaultBotConfigJson with bad timeframe (400)", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets",
      headers: adminHeaders(),
      payload: {
        ...VALID_BODY,
        defaultBotConfigJson: { ...VALID_BODY.defaultBotConfigJson, timeframe: "M30" },
      },
    });
    expect(res.statusCode).toBe(400);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/v1/presets
// ═══════════════════════════════════════════════════════════════════════════

describe("GET /api/v1/presets", () => {
  it("returns only PUBLIC presets without admin token", async () => {
    await seedPreset("public-a", "PUBLIC");
    await seedPreset("public-b", "PUBLIC", "dca");
    await seedPreset("private-a", "PRIVATE");

    const res = await app.inject({ method: "GET", url: "/api/v1/presets" });
    expect(res.statusCode).toBe(200);
    const slugs = (res.json() as Array<{ slug: string }>).map((p) => p.slug).sort();
    expect(slugs).toEqual(["public-a", "public-b"]);
  });

  it("returns all presets with admin token", async () => {
    await seedPreset("public-a", "PUBLIC");
    await seedPreset("private-a", "PRIVATE");

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/presets",
      headers: { "x-admin-token": ADMIN_TOKEN },
    });
    expect(res.statusCode).toBe(200);
    expect((res.json() as unknown[]).length).toBe(2);
  });

  it("filters by category", async () => {
    await seedPreset("trend-a", "PUBLIC", "trend");
    await seedPreset("dca-a", "PUBLIC", "dca");

    const res = await app.inject({ method: "GET", url: "/api/v1/presets?category=dca" });
    expect(res.statusCode).toBe(200);
    const rows = res.json() as Array<{ slug: string }>;
    expect(rows.map((r) => r.slug)).toEqual(["dca-a"]);
  });

  it("does not include dslJson in list response", async () => {
    await seedPreset("public-a", "PUBLIC");
    const res = await app.inject({ method: "GET", url: "/api/v1/presets" });
    const rows = res.json() as Array<Record<string, unknown>>;
    expect(rows[0]).not.toHaveProperty("dslJson");
    expect(rows[0]).toHaveProperty("defaultBotConfigJson");
  });

  // ── BETA visibility tier (docs/55-T6 §A4) ─────────────────────────────────

  it("anonymous list excludes BETA presets", async () => {
    await seedPreset("public-a", "PUBLIC");
    await seedPreset("beta-a", "BETA", "arb");

    const res = await app.inject({ method: "GET", url: "/api/v1/presets" });
    const slugs = (res.json() as Array<{ slug: string }>).map((p) => p.slug);
    expect(slugs).toEqual(["public-a"]);
  });

  it("authenticated list includes both PUBLIC and BETA presets", async () => {
    await seedPreset("public-a", "PUBLIC");
    await seedPreset("beta-a", "BETA", "arb");
    await seedPreset("private-a", "PRIVATE");

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/presets",
      headers: { authorization: `Bearer ${userToken}` },
    });
    expect(res.statusCode).toBe(200);
    const slugs = (res.json() as Array<{ slug: string }>).map((p) => p.slug).sort();
    expect(slugs).toEqual(["beta-a", "public-a"]);
  });

  it("admin can filter by ?visibility=BETA", async () => {
    await seedPreset("public-a", "PUBLIC");
    await seedPreset("beta-a", "BETA", "arb");
    await seedPreset("private-a", "PRIVATE");

    const res = await app.inject({
      method: "GET",
      url: "/api/v1/presets?visibility=BETA",
      headers: { "x-admin-token": ADMIN_TOKEN },
    });
    const slugs = (res.json() as Array<{ slug: string }>).map((p) => p.slug);
    expect(slugs).toEqual(["beta-a"]);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// GET /api/v1/presets/:slug
// ═══════════════════════════════════════════════════════════════════════════

describe("GET /api/v1/presets/:slug", () => {
  it("returns 404 for unknown slug", async () => {
    const res = await app.inject({ method: "GET", url: "/api/v1/presets/does-not-exist" });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 (not 403) for PRIVATE preset without admin", async () => {
    await seedPreset("secret", "PRIVATE");
    const res = await app.inject({ method: "GET", url: "/api/v1/presets/secret" });
    expect(res.statusCode).toBe(404);
  });

  it("returns 200 with dslJson for PUBLIC preset (anonymous)", async () => {
    await seedPreset("public-a", "PUBLIC");
    const res = await app.inject({ method: "GET", url: "/api/v1/presets/public-a" });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.slug).toBe("public-a");
    expect(body.dslJson).toBeDefined();
    expect(body.visibility).toBe("PUBLIC");
  });

  it("returns 200 for PRIVATE preset with admin token", async () => {
    await seedPreset("secret", "PRIVATE");
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/presets/secret",
      headers: { "x-admin-token": ADMIN_TOKEN },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().slug).toBe("secret");
  });

  // ── BETA visibility tier (docs/55-T6 §A4) ─────────────────────────────────

  it("returns 404 for BETA preset without authentication", async () => {
    await seedPreset("beta-arb", "BETA", "arb");
    const res = await app.inject({ method: "GET", url: "/api/v1/presets/beta-arb" });
    expect(res.statusCode).toBe(404);
  });

  it("returns 200 for BETA preset with a valid Bearer token", async () => {
    await seedPreset("beta-arb", "BETA", "arb");
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/presets/beta-arb",
      headers: { authorization: `Bearer ${userToken}` },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().visibility).toBe("BETA");
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// adminGuard fail-closed
// ═══════════════════════════════════════════════════════════════════════════

describe("adminGuard — fail-closed when env is unset", () => {
  it("rejects POST when ADMIN_API_TOKEN is unset, even with header", async () => {
    const previous = process.env.ADMIN_API_TOKEN;
    delete process.env.ADMIN_API_TOKEN;
    try {
      const res = await app.inject({
        method: "POST",
        url: "/api/v1/presets",
        headers: { "x-admin-token": "anything", "content-type": "application/json" },
        payload: VALID_BODY,
      });
      expect(res.statusCode).toBe(401);
    } finally {
      process.env.ADMIN_API_TOKEN = previous;
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// POST /api/v1/presets/:slug/instantiate
// ═══════════════════════════════════════════════════════════════════════════

function userHeaders() {
  return {
    authorization: `Bearer ${userToken}`,
    "x-workspace-id": WS_ID,
    "content-type": "application/json",
  };
}

describe("POST /api/v1/presets/:slug/instantiate", () => {
  it("returns 401 without auth", async () => {
    await seedPreset("public-a", "PUBLIC");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      payload: {},
    });
    expect(res.statusCode).toBe(401);
  });

  it("returns 403 for non-member workspace", async () => {
    await seedPreset("public-a", "PUBLIC");
    mockWorkspaceMemberships.length = 0;
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(403);
  });

  it("returns 404 for unknown slug", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/does-not-exist/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(404);
  });

  it("returns 404 (not 403) for PRIVATE preset without admin token", async () => {
    await seedPreset("secret", "PRIVATE");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/secret/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(404);
  });

  it("instantiates PRIVATE preset when admin token is provided", async () => {
    await seedPreset("secret", "PRIVATE");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/secret/instantiate",
      headers: { ...userHeaders(), "x-admin-token": ADMIN_TOKEN },
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.botId).toBeDefined();
    expect(body.strategyId).toBeDefined();
    expect(body.strategyVersionId).toBeDefined();
  });

  it("instantiates BETA preset for an authenticated non-admin user (docs/55-T6)", async () => {
    await seedPreset("beta-arb", "BETA", "arb");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/beta-arb/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    expect(res.json().botId).toBeDefined();
  });

  it("creates exactly one Strategy + Version + Bot, all tagged with templateSlug", async () => {
    await seedPreset("public-a", "PUBLIC");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    expect(Object.keys(mockStrategies)).toHaveLength(1);
    expect(Object.keys(mockStrategyVersions)).toHaveLength(1);
    expect(Object.keys(mockBots)).toHaveLength(1);

    const strategy = Object.values(mockStrategies)[0];
    const version = Object.values(mockStrategyVersions)[0];
    const bot = Object.values(mockBots)[0];

    expect(strategy.templateSlug).toBe("public-a");
    expect(strategy.workspaceId).toBe(WS_ID);
    expect(bot.templateSlug).toBe("public-a");
    expect(bot.workspaceId).toBe(WS_ID);
    expect(bot.status).toBe("DRAFT");
    expect(bot.mode).toBe("DSL"); // 55-T4: defaults to DSL when preset has no mode
    expect(bot.strategyVersionId).toBe(version.id);
    expect(version.strategyId).toBe(strategy.id);
    expect(version.dslJson).toEqual(VALID_DSL);
  });

  it("honours overrides.symbol", async () => {
    await seedPreset("public-a", "PUBLIC");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: { overrides: { symbol: "ETHUSDT" } },
    });
    expect(res.statusCode).toBe(201);
    const bot = Object.values(mockBots)[0];
    expect(bot.symbol).toBe("ETHUSDT");
  });

  it("rejects unsupported timeframe in overrides (400)", async () => {
    await seedPreset("public-a", "PUBLIC");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: { overrides: { timeframe: "M30" } },
    });
    expect(res.statusCode).toBe(400);
  });

  it("rolls back Strategy + StrategyVersion when Bot.create fails", async () => {
    await seedPreset("public-a", "PUBLIC");
    botCreateError = new Error("simulated bot.create failure");
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(500);
    // Nothing committed — staging was discarded.
    expect(Object.keys(mockStrategies)).toHaveLength(0);
    expect(Object.keys(mockStrategyVersions)).toHaveLength(0);
    expect(Object.keys(mockBots)).toHaveLength(0);
  });

  it("two consecutive instantiate calls produce two independent triples", async () => {
    await seedPreset("public-a", "PUBLIC");
    const r1 = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    const r2 = await app.inject({
      method: "POST",
      url: "/api/v1/presets/public-a/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(r1.statusCode).toBe(201);
    expect(r2.statusCode).toBe(201);
    expect(r1.json().botId).not.toBe(r2.json().botId);
    expect(Object.keys(mockBots)).toHaveLength(2);
    expect(Object.keys(mockStrategies)).toHaveLength(2);
  });

  // ── Bot.mode propagation (docs/55-T4) ─────────────────────────────────────

  it("persists Bot.mode = FUNDING_ARB when preset's defaultBotConfigJson sets it", async () => {
    await seedPreset("funding-arb-test", "BETA", "arb", { mode: "FUNDING_ARB" });
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/funding-arb-test/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    const bot = Object.values(mockBots)[0];
    expect(bot.mode).toBe("FUNDING_ARB");
  });

  it("rejects an unknown mode value with 400 + clear error", async () => {
    await seedPreset("bad-mode", "PUBLIC", "trend", { mode: "TURBO_CRYPTO" });
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/bad-mode/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(400);
    const body = res.json() as { errors: Array<{ field: string; message: string }> };
    expect(body.errors.some((e) => e.field === "mode" && /must be one of/.test(e.message))).toBe(true);
  });
});
