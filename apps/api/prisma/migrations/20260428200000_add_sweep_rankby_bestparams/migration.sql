-- 47-T4: server-side rankBy for sweep best-row selection.
-- Additive: two new columns on BacktestSweep, both with safe defaults
-- so existing rows interpret as the legacy "rank by pnlPct" behavior.

-- Audit / replay echo for which metric chose the best row.
ALTER TABLE "BacktestSweep" ADD COLUMN "rankBy" TEXT NOT NULL DEFAULT 'pnlPct';

-- Multi-param best-row values: Record<`${blockId}.${paramName}`, number>.
ALTER TABLE "BacktestSweep" ADD COLUMN "bestParamValuesJson" JSONB;
