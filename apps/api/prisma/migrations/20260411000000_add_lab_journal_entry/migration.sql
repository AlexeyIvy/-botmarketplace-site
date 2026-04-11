-- CreateEnum
CREATE TYPE "JournalEntryStatus" AS ENUM ('BASELINE', 'PROMOTE', 'DISCARD', 'KEEP_TESTING');

-- CreateTable
CREATE TABLE "LabJournalEntry" (
    "id" TEXT NOT NULL,
    "workspaceId" TEXT NOT NULL,
    "strategyGraphVersionId" TEXT NOT NULL,
    "backtestResultId" TEXT,
    "hypothesis" TEXT NOT NULL,
    "whatChanged" TEXT NOT NULL,
    "expectedResult" TEXT NOT NULL,
    "actualResult" TEXT,
    "nextStep" TEXT,
    "status" "JournalEntryStatus" NOT NULL DEFAULT 'KEEP_TESTING',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "LabJournalEntry_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "LabJournalEntry_workspaceId_idx" ON "LabJournalEntry"("workspaceId");

-- CreateIndex
CREATE INDEX "LabJournalEntry_strategyGraphVersionId_idx" ON "LabJournalEntry"("strategyGraphVersionId");

-- CreateIndex
CREATE INDEX "LabJournalEntry_workspaceId_createdAt_idx" ON "LabJournalEntry"("workspaceId", "createdAt" DESC);

-- AddForeignKey
ALTER TABLE "LabJournalEntry" ADD CONSTRAINT "LabJournalEntry_workspaceId_fkey" FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;
