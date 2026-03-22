-- Partial fill wiring: add PARTIALLY_FILLED to IntentState + fill tracking columns

-- AlterEnum
ALTER TYPE "IntentState" ADD VALUE 'PARTIALLY_FILLED';

-- AlterTable: add fill tracking columns to BotIntent
ALTER TABLE "BotIntent" ADD COLUMN "cumExecQty" DECIMAL(18, 8);
ALTER TABLE "BotIntent" ADD COLUMN "avgFillPrice" DECIMAL(18, 8);
