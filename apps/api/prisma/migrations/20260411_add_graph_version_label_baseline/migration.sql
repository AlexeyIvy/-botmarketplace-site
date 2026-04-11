-- Task 26: Governance / Provenance — version labels + baseline designation
-- Additive migration — no data loss, nullable label + default false baseline

ALTER TABLE "StrategyGraphVersion" ADD COLUMN "label" TEXT;
ALTER TABLE "StrategyGraphVersion" ADD COLUMN "isBaseline" BOOLEAN NOT NULL DEFAULT false;
