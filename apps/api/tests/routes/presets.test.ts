/**
 * Route tests: presets.ts (docs/51-T2)
 *
 * Covers POST /presets, GET /presets, GET /presets/:slug — visibility scoping,
 * slug regex, DSL validation, admin token gating, and 404-not-403 leakage rule
 * for PRIVATE presets.
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockPresets: Record<string, Record<string, unknown>> = {};

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
    PresetVisibility: { PRIVATE: "PRIVATE", PUBLIC: "PUBLIC" },
  };
});

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    strategyPreset: {
      create: vi.fn().mockImplementation(async ({ data }: { data: Record<string, unknown> }) => {
        const slug = data.slug as string;
        if (mockPresets[slug]) {
          // emulate Prisma unique-constraint violation
          const { Prisma } = await import("@prisma/client");
          throw new Prisma.PrismaClientKnownRequestError("Unique constraint failed", { code: "P2002" } as never);
        }
        const row = {
          ...data,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        mockPresets[slug] = row;
        return row;
      }),
      findMany: vi.fn().mockImplementation(({ where, select }: { where: Record<string, unknown>; select?: Record<string, boolean> }) => {
        const visibility = where?.visibility;
        const category = where?.category;
        const matched = Object.values(mockPresets).filter((p) => {
          if (visibility !== undefined && p.visibility !== visibility) return false;
          if (category !== undefined && p.category !== category) return false;
          return true;
        });
        // Honour `select`: include only keys with truthy value (mirrors Prisma).
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
  },
}));

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
const ADMIN_TOKEN = "test-admin-token-very-secret";

beforeAll(async () => {
  process.env.ADMIN_API_TOKEN = ADMIN_TOKEN;
  app = await buildApp();
});

afterAll(async () => {
  delete process.env.ADMIN_API_TOKEN;
  await app.close();
});

beforeEach(() => {
  Object.keys(mockPresets).forEach((k) => delete mockPresets[k]);
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

async function seedPreset(slug: string, visibility: "PRIVATE" | "PUBLIC", category = "trend") {
  mockPresets[slug] = {
    slug,
    name: `Preset ${slug}`,
    description: `Description ${slug}`,
    category,
    dslJson: VALID_DSL,
    defaultBotConfigJson: { symbol: "BTCUSDT", timeframe: "M15", quoteAmount: 100, maxOpenPositions: 1 },
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
