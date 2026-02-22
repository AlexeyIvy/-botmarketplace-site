-- CreateEnum
CREATE TYPE "TerminalOrderSide" AS ENUM ('BUY', 'SELL');

-- CreateEnum
CREATE TYPE "TerminalOrderType" AS ENUM ('MARKET', 'LIMIT');

-- CreateEnum
CREATE TYPE "TerminalOrderStatus" AS ENUM ('PENDING', 'SUBMITTED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'FAILED');

-- CreateTable
CREATE TABLE "TerminalOrder" (
    "id" TEXT NOT NULL,
    "workspaceId" TEXT NOT NULL,
    "exchangeConnectionId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" "TerminalOrderSide" NOT NULL,
    "type" "TerminalOrderType" NOT NULL,
    "qty" DECIMAL(18,8) NOT NULL,
    "price" DECIMAL(18,8),
    "status" "TerminalOrderStatus" NOT NULL DEFAULT 'PENDING',
    "exchangeOrderId" TEXT,
    "error" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "TerminalOrder_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "TerminalOrder" ADD CONSTRAINT "TerminalOrder_workspaceId_fkey"
    FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TerminalOrder" ADD CONSTRAINT "TerminalOrder_exchangeConnectionId_fkey"
    FOREIGN KEY ("exchangeConnectionId") REFERENCES "ExchangeConnection"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- Index
CREATE INDEX "TerminalOrder_workspaceId_idx" ON "TerminalOrder"("workspaceId");
CREATE INDEX "TerminalOrder_exchangeConnectionId_idx" ON "TerminalOrder"("exchangeConnectionId");
CREATE INDEX "TerminalOrder_workspaceId_createdAt_idx" ON "TerminalOrder"("workspaceId", "createdAt" DESC);
