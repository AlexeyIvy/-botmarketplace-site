/**
 * 51-T6 — seedPresets sanity.
 *
 * Verifies that:
 *  1. each fixture under prisma/seed/presets/ has a real DSL that passes
 *     `validateDsl`,
 *  2. seedPresets() upserts all 4 presets, defaulting `visibility` to PRIVATE,
 *  3. it is idempotent (a second run re-uses the same upsert path), and
 *  4. the `update` branch does not roll back a manual PUBLIC promotion.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { promises as fs } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { validateDsl } from "../../src/lib/dslValidator.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const SEED_DIR = resolve(HERE, "../../prisma/seed/presets");

const SLUGS = [
  "adaptive-regime",
  "dca-momentum",
  "mtf-scalper",
  "smc-liquidity-sweep",
  "funding-arb",
] as const;

// ---------------------------------------------------------------------------
// Fixture-level DSL validation (no Prisma involved)
// ---------------------------------------------------------------------------

describe("seed/presets/*.json fixtures", () => {
  for (const slug of SLUGS) {
    it(`${slug}.json passes validateDsl`, async () => {
      const path = resolve(SEED_DIR, `${slug}.json`);
      const raw = await fs.readFile(path, "utf8");
      const parsed = JSON.parse(raw) as { dslJson: unknown };
      const errors = validateDsl(parsed.dslJson);
      expect(errors).toBeNull();
    });
  }
});

// ---------------------------------------------------------------------------
// seedPresets() behaviour (Prisma mocked)
// ---------------------------------------------------------------------------

const mockPresets: Record<string, Record<string, unknown>> = {};

vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn(),
  Prisma: { JsonNull: "DbNull", InputJsonValue: {} as never },
  PresetVisibility: { PRIVATE: "PRIVATE", PUBLIC: "PUBLIC" },
}));

const mockPrisma = {
  strategyPreset: {
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
  },
};

import { seedPresets } from "../../prisma/seed/seedPresets.js";

beforeEach(() => {
  Object.keys(mockPresets).forEach((k) => delete mockPresets[k]);
  mockPrisma.strategyPreset.upsert.mockClear();
});

describe("seedPresets()", () => {
  it("upserts all 4 presets with visibility=PRIVATE", async () => {
    const results = await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    expect(results.map((r) => r.slug).sort()).toEqual([...SLUGS].sort());
    expect(Object.keys(mockPresets).sort()).toEqual([...SLUGS].sort());
    for (const slug of SLUGS) {
      expect(mockPresets[slug].visibility).toBe("PRIVATE");
      expect(mockPresets[slug].slug).toBe(slug);
    }
  });

  it("is idempotent — second run produces no creates", async () => {
    await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    expect(Object.keys(mockPresets)).toHaveLength(SLUGS.length);
    expect(mockPrisma.strategyPreset.upsert).toHaveBeenCalledTimes(SLUGS.length * 2);
  });

  it("does not roll back a manual PUBLIC promotion on re-seed", async () => {
    await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    // Simulate an admin flipping one preset to PUBLIC out-of-band.
    mockPresets["adaptive-regime"].visibility = "PUBLIC";
    await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    expect(mockPresets["adaptive-regime"].visibility).toBe("PUBLIC");
    // Other presets remain PRIVATE.
    expect(mockPresets["dca-momentum"].visibility).toBe("PRIVATE");
  });

  it("each preset carries the documented category", async () => {
    await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    expect(mockPresets["adaptive-regime"].category).toBe("trend");
    expect(mockPresets["dca-momentum"].category).toBe("dca");
    expect(mockPresets["mtf-scalper"].category).toBe("scalping");
    expect(mockPresets["smc-liquidity-sweep"].category).toBe("smc");
    expect(mockPresets["funding-arb"].category).toBe("arb");
  });

  it("funding-arb seeds with enabled=false so the DSL evaluator emits no intents", async () => {
    // Mode-based routing (docs/55-T4) is not yet wired; until it is,
    // instantiating this preset would put the bot on the regular DSL
    // path. The placeholder DSL must short-circuit at the
    // `enabled: false` gate (botWorker.ts stage 12) so we never emit
    // accidental orders on a preset whose real runtime is hedgeBotWorker.
    await seedPresets(mockPrisma as unknown as import("@prisma/client").PrismaClient);
    const dsl = mockPresets["funding-arb"].dslJson as Record<string, unknown>;
    expect(dsl.enabled).toBe(false);
  });
});
