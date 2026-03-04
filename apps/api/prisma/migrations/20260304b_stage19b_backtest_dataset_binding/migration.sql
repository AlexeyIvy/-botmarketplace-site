-- Stage 19b: BacktestResult → MarketDataset reproducibility binding
-- Adds dataset FK + execution params + engineVersion to BacktestResult.
-- All new columns are nullable or have defaults → deploy-safe (no table lock, no data loss).

-- Add reproducibility columns to BacktestResult
ALTER TABLE "BacktestResult"
  ADD COLUMN IF NOT EXISTS "datasetId"     TEXT,
  ADD COLUMN IF NOT EXISTS "datasetHash"   TEXT,
  ADD COLUMN IF NOT EXISTS "feeBps"        INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS "slippageBps"   INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS "fillAt"        TEXT    NOT NULL DEFAULT 'CLOSE',
  ADD COLUMN IF NOT EXISTS "engineVersion" TEXT    NOT NULL DEFAULT 'unknown';

-- FK: BacktestResult.datasetId → MarketDataset.id (SET NULL on dataset delete)
ALTER TABLE "BacktestResult"
  ADD CONSTRAINT "BacktestResult_datasetId_fkey"
    FOREIGN KEY ("datasetId")
    REFERENCES "MarketDataset"("id")
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- Index for dataset-based queries
CREATE INDEX IF NOT EXISTS "BacktestResult_datasetId_idx"
  ON "BacktestResult"("datasetId");
