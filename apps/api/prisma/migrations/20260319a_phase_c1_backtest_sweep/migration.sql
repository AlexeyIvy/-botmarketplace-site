-- CreateEnum
CREATE TYPE "SweepStatus" AS ENUM ('PENDING', 'RUNNING', 'DONE', 'FAILED');

-- CreateTable
CREATE TABLE "BacktestSweep" (
    "id" TEXT NOT NULL,
    "workspaceId" TEXT NOT NULL,
    "strategyVersionId" TEXT NOT NULL,
    "datasetId" TEXT NOT NULL,
    "sweepParamJson" JSONB NOT NULL,
    "feeBps" INTEGER NOT NULL,
    "slippageBps" INTEGER NOT NULL,
    "status" "SweepStatus" NOT NULL DEFAULT 'PENDING',
    "progress" INTEGER NOT NULL DEFAULT 0,
    "runCount" INTEGER NOT NULL,
    "resultsJson" JSONB,
    "bestParamValue" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "BacktestSweep_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "BacktestSweep_workspaceId_idx" ON "BacktestSweep"("workspaceId");

-- CreateIndex
CREATE INDEX "BacktestSweep_workspaceId_createdAt_idx" ON "BacktestSweep"("workspaceId", "createdAt" DESC);

-- AddForeignKey
ALTER TABLE "BacktestSweep" ADD CONSTRAINT "BacktestSweep_workspaceId_fkey" FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;
