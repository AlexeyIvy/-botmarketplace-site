-- CreateEnum
CREATE TYPE "BotStatus" AS ENUM ('DRAFT', 'ACTIVE', 'DISABLED');

-- CreateTable
CREATE TABLE "Bot" (
    "id" TEXT NOT NULL,
    "workspaceId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "strategyVersionId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "timeframe" "Timeframe" NOT NULL,
    "status" "BotStatus" NOT NULL DEFAULT 'DRAFT',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Bot_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Bot_workspaceId_name_key" ON "Bot"("workspaceId", "name");

-- CreateIndex
CREATE INDEX "Bot_workspaceId_idx" ON "Bot"("workspaceId");

-- CreateIndex
CREATE INDEX "Bot_strategyVersionId_idx" ON "Bot"("strategyVersionId");

-- CreateIndex
CREATE INDEX "Bot_workspaceId_symbol_idx" ON "Bot"("workspaceId", "symbol");

-- AddForeignKey (Workspace cascade)
ALTER TABLE "Bot" ADD CONSTRAINT "Bot_workspaceId_fkey" FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey (StrategyVersion restrict — prevent deleting a version used by a bot)
ALTER TABLE "Bot" ADD CONSTRAINT "Bot_strategyVersionId_fkey" FOREIGN KEY ("strategyVersionId") REFERENCES "StrategyVersion"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AlterTable: add botId to BotRun (required — no existing rows in MVP)
ALTER TABLE "BotRun" ADD COLUMN "botId" TEXT NOT NULL;

-- CreateIndex
CREATE INDEX "BotRun_botId_idx" ON "BotRun"("botId");

-- AddForeignKey (Bot cascade — deleting bot removes its runs)
ALTER TABLE "BotRun" ADD CONSTRAINT "BotRun_botId_fkey" FOREIGN KEY ("botId") REFERENCES "Bot"("id") ON DELETE CASCADE ON UPDATE CASCADE;
