-- Stage 12: Research Lab Results & Reproducibility
-- Adds strategyVersionId (for reproducibility pinning) and engineVersion to BacktestResult.

-- strategyVersionId: nullable FK so existing rows are not broken (SET NULL on cascade).
ALTER TABLE "BacktestResult"
    ADD COLUMN "strategyVersionId" TEXT,
    ADD COLUMN "engineVersion" TEXT NOT NULL DEFAULT '1';

CREATE INDEX "BacktestResult_strategyVersionId_idx"
    ON "BacktestResult"("strategyVersionId");

ALTER TABLE "BacktestResult"
    ADD CONSTRAINT "BacktestResult_strategyVersionId_fkey"
    FOREIGN KEY ("strategyVersionId") REFERENCES "StrategyVersion"("id")
    ON DELETE SET NULL ON UPDATE CASCADE;
