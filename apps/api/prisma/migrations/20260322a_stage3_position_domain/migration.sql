-- Stage 3 (#127): Position domain — Position + PositionEvent models

-- CreateEnum
CREATE TYPE "PositionSide" AS ENUM ('LONG', 'SHORT');

-- CreateEnum
CREATE TYPE "PositionStatus" AS ENUM ('OPEN', 'CLOSED');

-- CreateEnum
CREATE TYPE "PositionEventType" AS ENUM ('OPEN', 'ADD', 'PARTIAL_CLOSE', 'CLOSE', 'SL_UPDATE', 'TP_UPDATE');

-- CreateTable
CREATE TABLE "Position" (
    "id" TEXT NOT NULL,
    "botId" TEXT NOT NULL,
    "botRunId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" "PositionSide" NOT NULL,
    "status" "PositionStatus" NOT NULL DEFAULT 'OPEN',
    "entryQty" DECIMAL(18,8) NOT NULL,
    "avgEntryPrice" DECIMAL(18,8) NOT NULL,
    "costBasis" DECIMAL(18,8) NOT NULL,
    "currentQty" DECIMAL(18,8) NOT NULL,
    "realisedPnl" DECIMAL(18,8) NOT NULL DEFAULT 0,
    "slPrice" DECIMAL(18,8),
    "tpPrice" DECIMAL(18,8),
    "openedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "closedAt" TIMESTAMP(3),
    "metaJson" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Position_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PositionEvent" (
    "id" TEXT NOT NULL,
    "positionId" TEXT NOT NULL,
    "type" "PositionEventType" NOT NULL,
    "qty" DECIMAL(18,8),
    "price" DECIMAL(18,8),
    "realisedPnl" DECIMAL(18,8),
    "snapshotJson" JSONB,
    "intentId" TEXT,
    "metaJson" JSONB,
    "ts" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PositionEvent_pkey" PRIMARY KEY ("id")
);

-- CreateIndex: Position
CREATE INDEX "Position_botId_idx" ON "Position"("botId");
CREATE INDEX "Position_botRunId_idx" ON "Position"("botRunId");
CREATE INDEX "Position_botRunId_status_idx" ON "Position"("botRunId", "status");
CREATE INDEX "Position_botId_status_idx" ON "Position"("botId", "status");
CREATE INDEX "Position_botId_symbol_status_idx" ON "Position"("botId", "symbol", "status");

-- CreateIndex: PositionEvent
CREATE INDEX "PositionEvent_positionId_ts_idx" ON "PositionEvent"("positionId", "ts" DESC);
CREATE INDEX "PositionEvent_positionId_type_idx" ON "PositionEvent"("positionId", "type");

-- AddForeignKey
ALTER TABLE "Position" ADD CONSTRAINT "Position_botId_fkey" FOREIGN KEY ("botId") REFERENCES "Bot"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "Position" ADD CONSTRAINT "Position_botRunId_fkey" FOREIGN KEY ("botRunId") REFERENCES "BotRun"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "PositionEvent" ADD CONSTRAINT "PositionEvent_positionId_fkey" FOREIGN KEY ("positionId") REFERENCES "Position"("id") ON DELETE CASCADE ON UPDATE CASCADE;
