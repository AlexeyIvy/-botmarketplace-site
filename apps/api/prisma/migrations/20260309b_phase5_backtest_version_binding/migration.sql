-- Phase 5: Bind BacktestResult to explicit StrategyVersion
-- docs/23-lab-v2-ide-spec.md §16 Phase 5 — reproducibility binding
-- Additive change — nullable FK, no breaking changes.

ALTER TABLE "BacktestResult"
  ADD COLUMN "strategyVersionId" TEXT;

-- FK to StrategyVersion; SetNull on delete to preserve backtest history
ALTER TABLE "BacktestResult"
  ADD CONSTRAINT "BacktestResult_strategyVersionId_fkey"
  FOREIGN KEY ("strategyVersionId")
  REFERENCES "StrategyVersion"("id")
  ON DELETE SET NULL
  ON UPDATE CASCADE;

CREATE INDEX "BacktestResult_strategyVersionId_idx"
  ON "BacktestResult"("strategyVersionId");
