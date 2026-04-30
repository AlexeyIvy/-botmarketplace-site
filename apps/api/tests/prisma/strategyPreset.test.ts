/**
 * 51-T1 + 51-T4 — Prisma type sanity for the new StrategyPreset model and
 * the additive Bot/Strategy.templateSlug columns.
 *
 * This is a type-level smoke test: it asserts that `prisma generate` produced
 * the expected types after the migration. The actual DB-level behaviour
 * (CREATE TABLE, default visibility, unique slug) is verified by Prisma at
 * `prisma migrate deploy` time and is out of scope here.
 */

import { describe, it, expect } from "vitest";
import {
  PresetVisibility,
  type Bot,
  type Strategy,
  type StrategyPreset,
} from "@prisma/client";

describe("StrategyPreset (51-T1) — generated types", () => {
  it("StrategyPreset row matches declared schema", () => {
    const row: StrategyPreset = {
      slug: "test-preset",
      name: "Test Preset",
      description: "A preset",
      category: "trend",
      dslJson: { ok: true },
      defaultBotConfigJson: { symbol: "BTCUSDT", timeframe: "M15" },
      datasetBundleHintJson: null,
      visibility: PresetVisibility.PRIVATE,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    expect(row.slug).toBe("test-preset");
    expect(row.visibility).toBe(PresetVisibility.PRIVATE);
  });

  it("PresetVisibility enum exposes both members", () => {
    expect(PresetVisibility.PRIVATE).toBe("PRIVATE");
    expect(PresetVisibility.PUBLIC).toBe("PUBLIC");
  });
});

describe("Bot.templateSlug + Strategy.templateSlug (51-T4)", () => {
  it("Bot exposes nullable templateSlug column", () => {
    const slot: Pick<Bot, "templateSlug"> = { templateSlug: null };
    expect(slot.templateSlug).toBeNull();

    const tagged: Pick<Bot, "templateSlug"> = { templateSlug: "adaptive-regime" };
    expect(tagged.templateSlug).toBe("adaptive-regime");
  });

  it("Strategy exposes nullable templateSlug column", () => {
    const slot: Pick<Strategy, "templateSlug"> = { templateSlug: null };
    expect(slot.templateSlug).toBeNull();

    const tagged: Pick<Strategy, "templateSlug"> = { templateSlug: "dca-momentum" };
    expect(tagged.templateSlug).toBe("dca-momentum");
  });
});
