/**
 * Strategy Preset seed (docs/51-T6 + docs/55-T4 funding-arb registration).
 *
 * Loads the 4 non-Funding flagship presets (Adaptive Regime, DCA Momentum,
 * MTF Scalper, SMC Liquidity Sweep) plus the funding-arb preset from JSON
 * fixtures next to this file and upserts them into the StrategyPreset table.
 *
 * - Inserts always start as `PRIVATE` so a partially-finished preset is
 *   never visible to end users. Promotion to `PUBLIC` (or `BETA` for
 *   funding-arb, once docs/55-T6 extends the visibility enum) is a
 *   separate admin step (docs/51 §Решение 3) — the `update` branch below
 *   is intentionally careful not to roll back a manual flip.
 * - The DSL inside each flagship fixture is a placeholder. Final
 *   flagship-grade DSL lands in docs/53 (Adaptive Regime golden fixture)
 *   and docs/54 (DCA / MTF / SMC). The placeholders are real enough to
 *   pass `validateDsl`.
 * - The funding-arb fixture's DSL is a placeholder too, but with
 *   `enabled: false` — funding-arb's real runtime path is
 *   `hedgeBotWorker.ts` (docs/55-T4), not the DSL evaluator, and the
 *   `enabled` flag keeps the standard bot worker from emitting intents
 *   on this preset before mode routing lands.
 */

import { promises as fs } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Prisma, PresetVisibility, type PrismaClient } from "@prisma/client";

const HERE = dirname(fileURLToPath(import.meta.url));

interface PresetFixture {
  name: string;
  description: string;
  dslJson: Record<string, unknown>;
  defaultBotConfigJson: Record<string, unknown>;
  datasetBundleHintJson?: Record<string, unknown> | null;
}

interface PresetSpec {
  slug: string;
  category: "trend" | "dca" | "scalping" | "smc" | "arb";
  file: string;
}

const PRESETS: PresetSpec[] = [
  { slug: "adaptive-regime",     category: "trend",    file: "presets/adaptive-regime.json" },
  { slug: "dca-momentum",        category: "dca",      file: "presets/dca-momentum.json" },
  { slug: "mtf-scalper",         category: "scalping", file: "presets/mtf-scalper.json" },
  { slug: "smc-liquidity-sweep", category: "smc",      file: "presets/smc-liquidity-sweep.json" },
  { slug: "funding-arb",         category: "arb",      file: "presets/funding-arb.json" },
];

async function loadFixture(file: string): Promise<PresetFixture> {
  const path = resolve(HERE, file);
  const raw = await fs.readFile(path, "utf8");
  return JSON.parse(raw) as PresetFixture;
}

export async function seedPresets(prisma: PrismaClient): Promise<{ slug: string; created: boolean }[]> {
  const out: { slug: string; created: boolean }[] = [];

  for (const spec of PRESETS) {
    const fixture = await loadFixture(spec.file);

    const datasetHint =
      fixture.datasetBundleHintJson === undefined || fixture.datasetBundleHintJson === null
        ? Prisma.JsonNull
        : (fixture.datasetBundleHintJson as Prisma.InputJsonValue);

    // The `update` branch deliberately omits `visibility` so an admin who
    // promoted a preset to PUBLIC is not silently rolled back to PRIVATE
    // by the next seed run.
    const result = await prisma.strategyPreset.upsert({
      where: { slug: spec.slug },
      create: {
        slug: spec.slug,
        category: spec.category,
        name: fixture.name,
        description: fixture.description,
        dslJson: fixture.dslJson as Prisma.InputJsonValue,
        defaultBotConfigJson: fixture.defaultBotConfigJson as Prisma.InputJsonValue,
        datasetBundleHintJson: datasetHint,
        visibility: PresetVisibility.PRIVATE,
      },
      update: {
        category: spec.category,
        name: fixture.name,
        description: fixture.description,
        dslJson: fixture.dslJson as Prisma.InputJsonValue,
        defaultBotConfigJson: fixture.defaultBotConfigJson as Prisma.InputJsonValue,
        datasetBundleHintJson: datasetHint,
      },
    });
    out.push({ slug: result.slug, created: result.createdAt.getTime() === result.updatedAt.getTime() });
  }

  return out;
}
