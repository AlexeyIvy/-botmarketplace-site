-- 46-T4: persist fillAt per sweep so each run replays with the same
-- execution model. Additive migration — existing rows default to "CLOSE",
-- which matches their actual pre-46 behavior.

ALTER TABLE "BacktestSweep" ADD COLUMN "fillAt" TEXT NOT NULL DEFAULT 'CLOSE';
