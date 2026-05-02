-- BacktestResult dataset bundle column (docs/52 follow-up)
--
-- Adds a nullable JSONB column to BacktestResult so the bundle a
-- multi-TF backtest ran against is persisted alongside its report.
-- Existing rows are unaffected (NULL ⇒ legacy single-TF run driven by
-- `datasetId` alone). This unblocks accurate multi-TF replay from a
-- BacktestResult row — previously the bundle was consumed in-flight
-- and replays silently fell back to single-TF.
--
-- Mirrors 20260501000000_dataset_bundle on Bot/BacktestSweep/WalkForwardRun.

ALTER TABLE "BacktestResult" ADD COLUMN "datasetBundleJson" JSONB;
