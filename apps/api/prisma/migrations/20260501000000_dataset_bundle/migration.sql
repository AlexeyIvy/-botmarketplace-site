-- Multi-Interval Dataset Bundle (docs/52-T1)
--
-- Adds a nullable JSONB column on Bot, BacktestSweep and WalkForwardRun
-- so callers can attach a `Partial<Record<CandleInterval, string | true>>`
-- bundle. Existing rows are unaffected (NULL ⇒ legacy single-TF behaviour).

ALTER TABLE "Bot"            ADD COLUMN "datasetBundleJson" JSONB;
ALTER TABLE "BacktestSweep"  ADD COLUMN "datasetBundleJson" JSONB;
ALTER TABLE "WalkForwardRun" ADD COLUMN "datasetBundleJson" JSONB;
