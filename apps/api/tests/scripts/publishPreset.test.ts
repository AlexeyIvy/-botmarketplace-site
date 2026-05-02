/**
 * publishPreset CLI — unit coverage (docs/53-T4 / 54-T1..T3 closing).
 *
 * Drives `publishPreset()` directly with an in-memory mock prisma so
 * the visibility-flip logic is exercised without a database.
 *
 * Coverage:
 *   1. argv parsing: --slug / --visibility / --dry-run.
 *   2. Bad input: missing slug, missing visibility, invalid visibility.
 *   3. Not-found preset → kind "not_found", no update.
 *   4. Already-at-target → kind "noop", no update.
 *   5. PRIVATE → PUBLIC apply → kind "changed", update called.
 *   6. PRIVATE → PUBLIC dry-run → kind "changed" with dryRun=true, NO update.
 */

import { describe, it, expect, vi } from "vitest";
import {
  parseArgs,
  publishPreset,
  allowedVisibilities,
} from "../../scripts/publishPreset.js";

// ---------------------------------------------------------------------------
// Mock prisma — minimum surface required by publishPreset
// ---------------------------------------------------------------------------

interface FakePreset {
  slug: string;
  name: string;
  visibility: "PRIVATE" | "PUBLIC";
  updatedAt: Date;
}

function buildPrisma(seed: FakePreset[]) {
  const store = new Map<string, FakePreset>();
  for (const p of seed) store.set(p.slug, { ...p });

  const findUnique = vi.fn(async ({ where }: { where: { slug: string } }) => {
    // Return a copy — real prisma never hands back a live reference.
    const row = store.get(where.slug);
    return row ? { ...row } : null;
  });
  const update = vi.fn(async ({ where, data }: { where: { slug: string }; data: { visibility: "PRIVATE" | "PUBLIC" } }) => {
    const row = store.get(where.slug);
    if (!row) throw new Error("test fixture: preset not present");
    row.visibility = data.visibility;
    row.updatedAt = new Date();
    return row;
  });

  return {
    prisma: { strategyPreset: { findUnique, update } } as never,
    findUnique,
    update,
    store,
  };
}

function silentLog() {
  const lines: string[] = [];
  return { log: (l: string) => lines.push(l), lines };
}

// ---------------------------------------------------------------------------
// 1. argv parsing
// ---------------------------------------------------------------------------

describe("parseArgs", () => {
  it("reads --slug, --visibility, --dry-run", () => {
    const out = parseArgs(["--slug", "adaptive-regime", "--visibility", "PUBLIC", "--dry-run"]);
    expect(out).toEqual({ slug: "adaptive-regime", visibility: "PUBLIC", dryRun: true });
  });

  it("dryRun defaults to false", () => {
    const out = parseArgs(["--slug", "x", "--visibility", "PRIVATE"]);
    expect(out.dryRun).toBe(false);
  });

  it("missing fields stay undefined", () => {
    expect(parseArgs([])).toEqual({ dryRun: false });
  });
});

// ---------------------------------------------------------------------------
// 2. allowedVisibilities — sanity
// ---------------------------------------------------------------------------

describe("allowedVisibilities", () => {
  it("contains PRIVATE and PUBLIC at minimum", () => {
    const list = allowedVisibilities();
    expect(list).toContain("PRIVATE");
    expect(list).toContain("PUBLIC");
  });
});

// ---------------------------------------------------------------------------
// 3. Bad input
// ---------------------------------------------------------------------------

describe("publishPreset — bad input", () => {
  it("rejects missing slug", async () => {
    const { prisma } = buildPrisma([]);
    const out = await publishPreset({ visibility: "PUBLIC", prisma, log: () => {} });
    expect(out).toMatchObject({ kind: "bad_input" });
  });

  it("rejects missing visibility", async () => {
    const { prisma } = buildPrisma([]);
    const out = await publishPreset({ slug: "x", prisma, log: () => {} });
    expect(out).toMatchObject({ kind: "bad_input" });
  });

  it("rejects unknown visibility value", async () => {
    const { prisma } = buildPrisma([]);
    const out = await publishPreset({ slug: "x", visibility: "EXPERIMENTAL", prisma, log: () => {} });
    expect(out).toMatchObject({ kind: "bad_input" });
    if (out.kind === "bad_input") {
      expect(out.reason).toMatch(/invalid visibility/);
    }
  });
});

// ---------------------------------------------------------------------------
// 4. Not-found preset
// ---------------------------------------------------------------------------

describe("publishPreset — not found", () => {
  it("returns { kind: 'not_found' } when slug doesn't match", async () => {
    const { prisma, update } = buildPrisma([]);
    const out = await publishPreset({ slug: "ghost", visibility: "PUBLIC", prisma, log: () => {} });
    expect(out).toEqual({ kind: "not_found", slug: "ghost" });
    expect(update).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 5. Already-at-target — noop
// ---------------------------------------------------------------------------

describe("publishPreset — noop", () => {
  it("returns { kind: 'noop' } and skips update when visibility already matches", async () => {
    const { prisma, update } = buildPrisma([{
      slug: "adaptive-regime",
      name: "Adaptive Regime",
      visibility: "PUBLIC",
      updatedAt: new Date("2026-04-01T00:00:00Z"),
    }]);
    const sink = silentLog();

    const out = await publishPreset({ slug: "adaptive-regime", visibility: "PUBLIC", prisma, log: sink.log });

    expect(out).toEqual({ kind: "noop", slug: "adaptive-regime", visibility: "PUBLIC" });
    expect(update).not.toHaveBeenCalled();
    expect(sink.lines.join(" ")).toMatch(/already at PUBLIC/);
  });
});

// ---------------------------------------------------------------------------
// 6. Apply path
// ---------------------------------------------------------------------------

describe("publishPreset — apply", () => {
  it("PRIVATE → PUBLIC writes the update and returns { kind: 'changed', dryRun: false }", async () => {
    const { prisma, update, store } = buildPrisma([{
      slug: "dca-momentum",
      name: "DCA Momentum",
      visibility: "PRIVATE",
      updatedAt: new Date("2026-04-01T00:00:00Z"),
    }]);
    const sink = silentLog();

    const out = await publishPreset({
      slug: "dca-momentum", visibility: "PUBLIC", dryRun: false, prisma, log: sink.log,
    });

    expect(out).toMatchObject({
      kind: "changed",
      slug: "dca-momentum",
      from: "PRIVATE",
      to: "PUBLIC",
      dryRun: false,
    });
    expect(update).toHaveBeenCalledOnce();
    expect(store.get("dca-momentum")?.visibility).toBe("PUBLIC");
  });
});

// ---------------------------------------------------------------------------
// 7. Dry-run path
// ---------------------------------------------------------------------------

describe("publishPreset — dry-run", () => {
  it("PRIVATE → PUBLIC with --dry-run does NOT call update; returns dryRun: true", async () => {
    const { prisma, update, store } = buildPrisma([{
      slug: "smc-liquidity-sweep",
      name: "SMC Liquidity Sweep",
      visibility: "PRIVATE",
      updatedAt: new Date("2026-04-01T00:00:00Z"),
    }]);
    const sink = silentLog();

    const out = await publishPreset({
      slug: "smc-liquidity-sweep", visibility: "PUBLIC", dryRun: true, prisma, log: sink.log,
    });

    expect(out).toMatchObject({ kind: "changed", dryRun: true });
    expect(update).not.toHaveBeenCalled();
    // Store unchanged — dry-run.
    expect(store.get("smc-liquidity-sweep")?.visibility).toBe("PRIVATE");
    expect(sink.lines.join(" ")).toMatch(/dry-run/);
  });
});
