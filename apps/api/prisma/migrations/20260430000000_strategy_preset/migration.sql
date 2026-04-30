-- 51-T1 + 51-T4: StrategyPreset model + Bot/Strategy.templateSlug.
-- Additive migration only — no ALTER on existing data, no backfill.
--
-- StrategyPreset is an immutable JSON template that acts as a factory for
-- StrategyVersion. Bot.templateSlug / Strategy.templateSlug carry the
-- preset slug as a plain string (no FK), so deleting a preset does not
-- cascade to existing bots.

-- ── PresetVisibility enum ───────────────────────────────────────────────────
CREATE TYPE "PresetVisibility" AS ENUM ('PRIVATE', 'PUBLIC');

-- ── StrategyPreset table ────────────────────────────────────────────────────
CREATE TABLE "StrategyPreset" (
    "slug"                  TEXT NOT NULL,
    "name"                  TEXT NOT NULL,
    "description"           TEXT NOT NULL,
    "category"              TEXT NOT NULL,
    "dslJson"               JSONB NOT NULL,
    "defaultBotConfigJson"  JSONB NOT NULL,
    "datasetBundleHintJson" JSONB,
    "visibility"            "PresetVisibility" NOT NULL DEFAULT 'PRIVATE',
    "createdAt"             TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"             TIMESTAMP(3) NOT NULL,

    CONSTRAINT "StrategyPreset_pkey" PRIMARY KEY ("slug")
);

CREATE INDEX "StrategyPreset_visibility_idx" ON "StrategyPreset"("visibility");
CREATE INDEX "StrategyPreset_category_idx"   ON "StrategyPreset"("category");

-- ── Strategy.templateSlug (51-T4) ───────────────────────────────────────────
ALTER TABLE "Strategy" ADD COLUMN "templateSlug" TEXT;
CREATE INDEX "Strategy_templateSlug_idx" ON "Strategy"("templateSlug");

-- ── Bot.templateSlug (51-T4) ────────────────────────────────────────────────
ALTER TABLE "Bot" ADD COLUMN "templateSlug" TEXT;
CREATE INDEX "Bot_templateSlug_idx" ON "Bot"("templateSlug");
