-- 48-T4: walk-forward validation persistence layer.
-- Additive only: one new enum, one new table, three indexes, one FK.
-- Mirrors BacktestSweep structurally (workspace cascade, no inverse
-- relations on strategyVersionId / datasetId).

-- CreateEnum
CREATE TYPE "WalkForwardStatus" AS ENUM ('PENDING', 'RUNNING', 'DONE', 'FAILED');

-- CreateTable
CREATE TABLE "WalkForwardRun" (
    "id" TEXT NOT NULL,
    "workspaceId" TEXT NOT NULL,
    "strategyVersionId" TEXT NOT NULL,
    "datasetId" TEXT NOT NULL,
    "status" "WalkForwardStatus" NOT NULL DEFAULT 'PENDING',
    "foldConfigJson" JSONB NOT NULL,
    "foldCount" INTEGER NOT NULL DEFAULT 0,
    "progress" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "foldsJson" JSONB,
    "aggregateJson" JSONB,
    "error" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "WalkForwardRun_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "WalkForwardRun_workspaceId_idx" ON "WalkForwardRun"("workspaceId");

-- CreateIndex
CREATE INDEX "WalkForwardRun_workspaceId_createdAt_idx" ON "WalkForwardRun"("workspaceId", "createdAt" DESC);

-- CreateIndex
CREATE INDEX "WalkForwardRun_strategyVersionId_idx" ON "WalkForwardRun"("strategyVersionId");

-- AddForeignKey
ALTER TABLE "WalkForwardRun" ADD CONSTRAINT "WalkForwardRun_workspaceId_fkey" FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;
