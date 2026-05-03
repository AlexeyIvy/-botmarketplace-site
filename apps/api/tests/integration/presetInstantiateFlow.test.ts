/**
 * 51-T7 — End-to-end preset instantiate flow.
 *
 * Exercises the seed → list-filter → instantiate path in one suite, asserting
 * the runtime invariant from `docs/50 §Решение 1`: bots created from a
 * preset look identical to bots created via the standard Lab → Build path,
 * so `botWorker.ts` never branches on `templateSlug`.
 *
 * Steps (mirrors docs/51 §51-T7):
 *   1. Run the real `seedPresets()` against an in-memory Prisma mock —
 *      the 4 flagship presets land as PRIVATE.
 *   2. Promote `adaptive-regime` to PUBLIC out-of-band (the mock store edit
 *      stands in for the documented "direct SQL" step).
 *   3. `GET /presets` without auth returns only `adaptive-regime`.
 *   4. `GET /presets/adaptive-regime` returns the full record with `dslJson`
 *      deep-equal to the on-disk seed fixture.
 *   5. `POST /presets/adaptive-regime/instantiate` (workspace user, no admin
 *      header) → 201 with `{ botId, strategyId, strategyVersionId }`.
 *   6. The persisted Bot is DRAFT, has `templateSlug=adaptive-regime`, and
 *      its `StrategyVersion.dslJson` deep-equals the seed fixture.
 *   7. `validateDsl(StrategyVersion.dslJson)` returns null — proving the
 *      runtime invariant: the saved DSL is consumable by the standard
 *      runtime (botWorker / signalEngine / exitEngine) without any
 *      preset-specific glue.
 *
 * Implementation notes:
 *  - `dslValidator` is intentionally NOT mocked here (unlike
 *    `tests/routes/presets.test.ts`); we want the real validator to vet the
 *    seed fixtures, since that is what makes step 7 a meaningful check.
 *  - The Prisma mock follows the same in-memory pattern as the unit tests
 *    in `tests/routes/presets.test.ts` and `tests/prisma/seedPresets.test.ts`.
 *    A real Postgres-backed integration harness does not yet exist in this
 *    repo (see docs/51-T7 §"Implementation notes" — fall back to detailed
 *    in-memory transactions).
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";
import { promises as fs } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// ── Mock state ──────────────────────────────────────────────────────────────

const mockPresets: Record<string, Record<string, unknown>> = {};
const mockStrategies: Record<string, Record<string, unknown>> = {};
const mockStrategyVersions: Record<string, Record<string, unknown>> = {};
const mockBots: Record<string, Record<string, unknown>> = {};
const mockWorkspaceMemberships: Array<Record<string, unknown>> = [];

let strategyIdCounter = 0;
let strategyVersionIdCounter = 0;
let botIdCounter = 0;

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
      // upsert path — used by seedPresets()
      upsert: vi.fn().mockImplementation(async ({
        where,
        create,
        update,
      }: {
        where: { slug: string };
        create: Record<string, unknown>;
        update: Record<string, unknown>;
      }) => {
        const existing = mockPresets[where.slug];
        if (existing) {
          const merged = { ...existing, ...update, updatedAt: new Date() };
          mockPresets[where.slug] = merged;
          return merged;
        }
        const now = new Date();
        const fresh = { ...create, createdAt: now, updatedAt: now };
        mockPresets[where.slug] = fresh;
        return fresh;
      }),
      findMany: vi.fn().mockImplementation(({ where, select }: { where: Record<string, unknown>; select?: Record<string, boolean> }) => {
        const visibility = where?.visibility;
        const category = where?.category;
        const matched = Object.values(mockPresets).filter((p) => {
          if (visibility !== undefined && p.visibility !== visibility) return false;
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
      const result = await cb(tx);
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

// NB: deliberately NOT mocking dslValidator — the whole point of step 7
// (see file header) is that the real validator vets the seed DSL.

import { buildApp } from "../../src/app.js";
import { seedPresets } from "../../prisma/seed/seedPresets.js";
import { validateDsl } from "../../src/lib/dslValidator.js";
import { prisma as mockedPrisma } from "../../src/lib/prisma.js";
import type { FastifyInstance } from "fastify";

// ── Setup ───────────────────────────────────────────────────────────────────

let app: FastifyInstance;
let userToken: string;
const ADMIN_TOKEN = "test-admin-integration-secret";
const WS_ID = "ws-preset-integration";
const USER_ID = "user-preset-integration";

const HERE = dirname(fileURLToPath(import.meta.url));
const SEED_DIR = resolve(HERE, "../../prisma/seed/presets");

async function readSeedFixture(slug: string): Promise<{
  name: string;
  description: string;
  dslJson: Record<string, unknown>;
  defaultBotConfigJson: Record<string, unknown>;
}> {
  const raw = await fs.readFile(resolve(SEED_DIR, `${slug}.json`), "utf8");
  return JSON.parse(raw);
}

beforeAll(async () => {
  process.env.ADMIN_API_TOKEN = ADMIN_TOKEN;
  app = await buildApp();
  userToken = app.jwt.sign({ sub: USER_ID, email: "preset-integration@test.com" });
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
  mockWorkspaceMemberships.push({ userId: USER_ID, workspaceId: WS_ID, role: "OWNER" });
});

// ── Helpers ─────────────────────────────────────────────────────────────────

function userHeaders() {
  return {
    authorization: `Bearer ${userToken}`,
    "x-workspace-id": WS_ID,
    "content-type": "application/json",
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Full flow: seed → list-filter → instantiate → invariant check
// ═══════════════════════════════════════════════════════════════════════════

describe("preset instantiate flow (e2e, mocked Prisma)", () => {
  it("seed populates all flagship presets in PRIVATE state", async () => {
    const results = await seedPresets(
      mockedPrisma as unknown as import("@prisma/client").PrismaClient,
    );
    expect(results.map((r) => r.slug).sort()).toEqual(
      ["adaptive-regime", "dca-momentum", "funding-arb", "mtf-scalper", "smc-liquidity-sweep"],
    );
    for (const slug of Object.keys(mockPresets)) {
      expect(mockPresets[slug].visibility).toBe("PRIVATE");
    }
  });

  it("after promoting adaptive-regime to PUBLIC, anonymous list returns only that slug", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);
    // Stand-in for `UPDATE strategy_preset SET visibility=PUBLIC WHERE slug=...`
    mockPresets["adaptive-regime"].visibility = "PUBLIC";

    const res = await app.inject({ method: "GET", url: "/api/v1/presets" });
    expect(res.statusCode).toBe(200);
    const slugs = (res.json() as Array<{ slug: string }>).map((p) => p.slug);
    expect(slugs).toEqual(["adaptive-regime"]);
  });

  it("anonymous GET /presets/adaptive-regime returns dslJson matching the seed fixture", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);
    mockPresets["adaptive-regime"].visibility = "PUBLIC";

    const fixture = await readSeedFixture("adaptive-regime");
    const res = await app.inject({ method: "GET", url: "/api/v1/presets/adaptive-regime" });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.slug).toBe("adaptive-regime");
    expect(body.visibility).toBe("PUBLIC");
    expect(body.dslJson).toEqual(fixture.dslJson);
  });

  it("POST /presets/adaptive-regime/instantiate creates DRAFT bot tagged with templateSlug", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);
    mockPresets["adaptive-regime"].visibility = "PUBLIC";

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/adaptive-regime/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    const { botId, strategyId, strategyVersionId } = res.json();
    expect(botId).toBeDefined();
    expect(strategyId).toBeDefined();
    expect(strategyVersionId).toBeDefined();

    // Bot record asserts — DRAFT, workspace-scoped, templateSlug present.
    const bot = mockBots[botId as string];
    expect(bot).toBeDefined();
    expect(bot.status).toBe("DRAFT");
    expect(bot.workspaceId).toBe(WS_ID);
    expect(bot.templateSlug).toBe("adaptive-regime");
    expect(bot.strategyVersionId).toBe(strategyVersionId);

    // Strategy carries the slug too (so analytics can join across both tables).
    const strategy = mockStrategies[strategyId as string];
    expect(strategy).toBeDefined();
    expect(strategy.templateSlug).toBe("adaptive-regime");
    expect(strategy.workspaceId).toBe(WS_ID);

    // StrategyVersion DSL = the on-disk seed fixture (deep equal).
    const fixture = await readSeedFixture("adaptive-regime");
    const version = mockStrategyVersions[strategyVersionId as string];
    expect(version).toBeDefined();
    expect(version.strategyId).toBe(strategyId);
    expect(version.dslJson).toEqual(fixture.dslJson);
  });

  it("PRIVATE preset cannot be instantiated without admin token (404)", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);
    // dca-momentum stays PRIVATE (default seed state).

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/dca-momentum/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(404);
    expect(Object.keys(mockBots)).toHaveLength(0);
  });

  it("admin override unlocks PRIVATE instantiate without flipping visibility", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/mtf-scalper/instantiate",
      headers: { ...userHeaders(), "x-admin-token": ADMIN_TOKEN },
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    expect(Object.keys(mockBots)).toHaveLength(1);
    // The preset itself must still be PRIVATE — admin instantiate is not a
    // promotion mechanism.
    expect(mockPresets["mtf-scalper"].visibility).toBe("PRIVATE");
  });

  // Runtime invariant: the saved StrategyVersion DSL is acceptable to the
  // real validator that `botWorker → dslEvaluator` will use. If a future
  // change introduces preset-specific DSL shape, this test fails — proving
  // we have not silently coupled the runtime to the preset system.
  it("StrategyVersion.dslJson passes the real validateDsl (botWorker invariant)", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);
    mockPresets["adaptive-regime"].visibility = "PUBLIC";

    const res = await app.inject({
      method: "POST",
      url: "/api/v1/presets/adaptive-regime/instantiate",
      headers: userHeaders(),
      payload: {},
    });
    expect(res.statusCode).toBe(201);
    const { strategyVersionId } = res.json();
    const version = mockStrategyVersions[strategyVersionId as string];
    expect(version).toBeDefined();
    expect(validateDsl(version.dslJson)).toBeNull();
  });

  it("all 4 seeded fixtures pass the real validateDsl", async () => {
    await seedPresets(mockedPrisma as unknown as import("@prisma/client").PrismaClient);
    for (const slug of Object.keys(mockPresets)) {
      const fixture = await readSeedFixture(slug);
      expect(validateDsl(fixture.dslJson)).toBeNull();
    }
  });
});
