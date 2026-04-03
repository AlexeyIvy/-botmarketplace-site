-- CreateEnum
CREATE TYPE "HedgeStatus" AS ENUM ('PLANNED', 'OPENING', 'OPEN', 'CLOSING', 'CLOSED', 'FAILED');

-- CreateTable
CREATE TABLE "FundingSnapshot" (
    "id" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "fundingRate" DOUBLE PRECISION NOT NULL,
    "nextFundingAt" TIMESTAMP(3) NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "FundingSnapshot_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SpreadSnapshot" (
    "id" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "spotPrice" DOUBLE PRECISION NOT NULL,
    "perpPrice" DOUBLE PRECISION NOT NULL,
    "basisBps" DOUBLE PRECISION NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SpreadSnapshot_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "HedgePosition" (
    "id" TEXT NOT NULL,
    "botRunId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "status" "HedgeStatus" NOT NULL DEFAULT 'PLANNED',
    "entryBasisBps" DOUBLE PRECISION NOT NULL,
    "fundingCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "closedAt" TIMESTAMP(3),

    CONSTRAINT "HedgePosition_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LegExecution" (
    "id" TEXT NOT NULL,
    "hedgeId" TEXT NOT NULL,
    "side" TEXT NOT NULL,
    "price" DOUBLE PRECISION NOT NULL,
    "quantity" DOUBLE PRECISION NOT NULL,
    "fee" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "LegExecution_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "FundingSnapshot_symbol_timestamp_idx" ON "FundingSnapshot"("symbol", "timestamp");

-- CreateIndex
CREATE INDEX "SpreadSnapshot_symbol_timestamp_idx" ON "SpreadSnapshot"("symbol", "timestamp");

-- CreateIndex
CREATE INDEX "HedgePosition_botRunId_idx" ON "HedgePosition"("botRunId");

-- CreateIndex
CREATE INDEX "HedgePosition_symbol_status_idx" ON "HedgePosition"("symbol", "status");

-- CreateIndex
CREATE INDEX "LegExecution_hedgeId_idx" ON "LegExecution"("hedgeId");

-- AddForeignKey
ALTER TABLE "LegExecution" ADD CONSTRAINT "LegExecution_hedgeId_fkey" FOREIGN KEY ("hedgeId") REFERENCES "HedgePosition"("id") ON DELETE CASCADE ON UPDATE CASCADE;
