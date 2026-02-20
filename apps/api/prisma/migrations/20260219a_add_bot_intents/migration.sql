-- CreateEnum
CREATE TYPE "IntentType" AS ENUM ('ENTRY', 'EXIT', 'SL', 'TP', 'CANCEL');

-- CreateEnum
CREATE TYPE "IntentState" AS ENUM ('PENDING', 'PLACED', 'FILLED', 'CANCELLED', 'FAILED');

-- CreateEnum
CREATE TYPE "OrderSide" AS ENUM ('BUY', 'SELL');

-- CreateTable
CREATE TABLE "BotIntent" (
    "id" TEXT NOT NULL,
    "botRunId" TEXT NOT NULL,
    "intentId" TEXT NOT NULL,
    "orderLinkId" TEXT NOT NULL,
    "type" "IntentType" NOT NULL,
    "state" "IntentState" NOT NULL DEFAULT 'PENDING',
    "side" "OrderSide" NOT NULL,
    "qty" DECIMAL(18,8) NOT NULL,
    "price" DECIMAL(18,8),
    "orderId" TEXT,
    "metaJson" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "BotIntent_pkey" PRIMARY KEY ("id")
);

-- CreateIndex (intentId unique per run — client idempotency key)
CREATE UNIQUE INDEX "BotIntent_botRunId_intentId_key" ON "BotIntent"("botRunId", "intentId");

-- CreateIndex (orderLinkId unique globally — sent to exchange as clientOrderId)
CREATE UNIQUE INDEX "BotIntent_orderLinkId_key" ON "BotIntent"("orderLinkId");

-- CreateIndex
CREATE INDEX "BotIntent_botRunId_idx" ON "BotIntent"("botRunId");

-- CreateIndex
CREATE INDEX "BotIntent_orderLinkId_idx" ON "BotIntent"("orderLinkId");

-- CreateIndex
CREATE INDEX "BotIntent_botRunId_state_idx" ON "BotIntent"("botRunId", "state");

-- AddForeignKey
ALTER TABLE "BotIntent"
    ADD CONSTRAINT "BotIntent_botRunId_fkey"
    FOREIGN KEY ("botRunId") REFERENCES "BotRun"("id") ON DELETE CASCADE ON UPDATE CASCADE;
