-- 55-T4: BotMode enum + Bot.mode column.
--
-- Additive only. Existing rows backfill to DSL via the column default
-- so DSL bots remain on the DSL evaluator path with no behavioural
-- change. FUNDING_ARB is the routing seam for funding-arb bots; the
-- DSL evaluator (botWorker.evaluateStrategies) early-skips them and
-- hedgeBotWorker owns intent emission via HedgePosition advancement.

CREATE TYPE "BotMode" AS ENUM ('DSL', 'FUNDING_ARB');

ALTER TABLE "Bot" ADD COLUMN "mode" "BotMode" NOT NULL DEFAULT 'DSL';
