-- CreateEnum
CREATE TYPE "ExchangeConnectionStatus" AS ENUM ('UNKNOWN', 'CONNECTED', 'FAILED');

-- CreateTable
CREATE TABLE "ExchangeConnection" (
    "id"              TEXT NOT NULL,
    "workspaceId"     TEXT NOT NULL,
    "exchange"        TEXT NOT NULL,
    "name"            TEXT NOT NULL,
    "apiKey"          TEXT NOT NULL,
    "encryptedSecret" TEXT NOT NULL,
    "status"          "ExchangeConnectionStatus" NOT NULL DEFAULT 'UNKNOWN',
    "createdAt"       TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"       TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ExchangeConnection_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ExchangeConnection_workspaceId_name_key" ON "ExchangeConnection"("workspaceId", "name");

-- CreateIndex
CREATE INDEX "ExchangeConnection_workspaceId_idx" ON "ExchangeConnection"("workspaceId");

-- AddForeignKey
ALTER TABLE "ExchangeConnection" ADD CONSTRAINT "ExchangeConnection_workspaceId_fkey"
    FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;
