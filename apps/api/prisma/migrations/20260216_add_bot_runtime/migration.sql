-- CreateEnum
CREATE TYPE "BotRunState" AS ENUM ('CREATED', 'QUEUED', 'STARTING', 'SYNCING', 'RUNNING', 'STOPPING', 'STOPPED', 'FAILED', 'TIMED_OUT');

-- CreateTable
CREATE TABLE "BotRun" (
    "id" TEXT NOT NULL,
    "workspaceId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "state" "BotRunState" NOT NULL DEFAULT 'CREATED',
    "leaseOwner" TEXT,
    "leaseUntil" TIMESTAMP(3),
    "startedAt" TIMESTAMP(3),
    "stoppedAt" TIMESTAMP(3),
    "errorCode" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "BotRun_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BotEvent" (
    "id" TEXT NOT NULL,
    "botRunId" TEXT NOT NULL,
    "ts" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "type" TEXT NOT NULL,
    "payloadJson" JSONB NOT NULL,

    CONSTRAINT "BotEvent_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "BotRun_workspaceId_idx" ON "BotRun"("workspaceId");

-- CreateIndex
CREATE INDEX "BotRun_workspaceId_symbol_idx" ON "BotRun"("workspaceId", "symbol");

-- CreateIndex
CREATE INDEX "BotRun_state_idx" ON "BotRun"("state");

-- CreateIndex (partial unique: one active run per workspace+symbol)
CREATE UNIQUE INDEX "BotRun_active_workspace_symbol_key"
    ON "BotRun" ("workspaceId", "symbol")
    WHERE "state" IN ('CREATED', 'QUEUED', 'STARTING', 'SYNCING', 'RUNNING');

-- CreateIndex
CREATE INDEX "BotEvent_botRunId_ts_idx" ON "BotEvent"("botRunId", "ts" DESC);

-- AddForeignKey
ALTER TABLE "BotRun" ADD CONSTRAINT "BotRun_workspaceId_fkey" FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BotEvent" ADD CONSTRAINT "BotEvent_botRunId_fkey" FOREIGN KEY ("botRunId") REFERENCES "BotRun"("id") ON DELETE CASCADE ON UPDATE CASCADE;
