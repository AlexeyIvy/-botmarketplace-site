-- Stage 19a: Market candle layer + dataset freeze + deterministic hash + quality
-- Adds: CandleInterval enum, DatasetStatus enum, MarketCandle (shared), MarketDataset (workspace-scoped)

CREATE TYPE "CandleInterval" AS ENUM ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1');
CREATE TYPE "DatasetStatus"  AS ENUM ('READY', 'PARTIAL', 'FAILED');

-- Shared market candle storage (no workspaceId — exchange/symbol/interval/time is global)
CREATE TABLE "MarketCandle" (
  "id"         TEXT          NOT NULL,
  "exchange"   TEXT          NOT NULL,
  "symbol"     TEXT          NOT NULL,
  "interval"   "CandleInterval" NOT NULL,
  "openTimeMs" BIGINT        NOT NULL,
  "open"       DECIMAL(18,8) NOT NULL,
  "high"       DECIMAL(18,8) NOT NULL,
  "low"        DECIMAL(18,8) NOT NULL,
  "close"      DECIMAL(18,8) NOT NULL,
  "volume"     DECIMAL(18,8) NOT NULL,
  "createdAt"  TIMESTAMP(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "MarketCandle_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "MarketCandle_exchange_symbol_interval_openTimeMs_key"
  ON "MarketCandle"("exchange", "symbol", "interval", "openTimeMs");

CREATE INDEX "MarketCandle_exchange_symbol_interval_openTimeMs_idx"
  ON "MarketCandle"("exchange", "symbol", "interval", "openTimeMs" DESC);

-- Workspace-scoped dataset snapshot (frozen range + deterministic hash)
CREATE TABLE "MarketDataset" (
  "id"            TEXT             NOT NULL,
  "workspaceId"   TEXT             NOT NULL,
  "exchange"      TEXT             NOT NULL,
  "symbol"        TEXT             NOT NULL,
  "interval"      "CandleInterval" NOT NULL,
  "fromTsMs"      BIGINT           NOT NULL,
  "toTsMs"        BIGINT           NOT NULL,
  "fetchedAt"     TIMESTAMP(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "datasetHash"   TEXT             NOT NULL,
  "candleCount"   INTEGER          NOT NULL,
  "qualityJson"   JSONB            NOT NULL,
  "engineVersion" TEXT             NOT NULL,
  "status"        "DatasetStatus"  NOT NULL,
  "createdAt"     TIMESTAMP(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "MarketDataset_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "MarketDataset"
  ADD CONSTRAINT "MarketDataset_workspaceId_fkey"
  FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

CREATE UNIQUE INDEX "MarketDataset_workspaceId_exchange_symbol_interval_fromTsMs_toTsMs_key"
  ON "MarketDataset"("workspaceId", "exchange", "symbol", "interval", "fromTsMs", "toTsMs");

CREATE INDEX "MarketDataset_workspaceId_createdAt_idx"
  ON "MarketDataset"("workspaceId", "createdAt" DESC);
