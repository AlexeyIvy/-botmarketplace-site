-- Stage 18a: AI Action Plan + Audit tables
-- Adds AiPlan (stores generated plans with TTL) and AiActionAudit (execution log).

CREATE TYPE "AiActionStatus" AS ENUM ('PROPOSED', 'EXECUTED', 'FAILED', 'CANCELLED');

CREATE TABLE "AiPlan" (
  "id"          TEXT NOT NULL,
  "workspaceId" TEXT NOT NULL,
  "userId"      TEXT NOT NULL,
  "expiresAt"   TIMESTAMP(3) NOT NULL,
  "planJson"    JSONB NOT NULL,
  "requestId"   TEXT,
  "createdAt"   TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AiPlan_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "AiActionAudit" (
  "id"          TEXT NOT NULL,
  "planId"      TEXT NOT NULL,
  "workspaceId" TEXT NOT NULL,
  "userId"      TEXT NOT NULL,
  "actionId"    TEXT NOT NULL,
  "actionType"  TEXT NOT NULL,
  "status"      "AiActionStatus" NOT NULL DEFAULT 'PROPOSED',
  "inputJson"   JSONB NOT NULL,
  "resultJson"  JSONB,
  "requestId"   TEXT,
  "createdAt"   TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "executedAt"  TIMESTAMP(3),
  CONSTRAINT "AiActionAudit_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "AiPlan"
  ADD CONSTRAINT "AiPlan_workspaceId_fkey"
  FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "AiActionAudit"
  ADD CONSTRAINT "AiActionAudit_planId_fkey"
  FOREIGN KEY ("planId") REFERENCES "AiPlan"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "AiActionAudit"
  ADD CONSTRAINT "AiActionAudit_workspaceId_fkey"
  FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

CREATE INDEX "AiPlan_workspaceId_createdAt_idx" ON "AiPlan"("workspaceId", "createdAt" DESC);
CREATE INDEX "AiActionAudit_planId_idx" ON "AiActionAudit"("planId");
CREATE INDEX "AiActionAudit_workspaceId_createdAt_idx" ON "AiActionAudit"("workspaceId", "createdAt" DESC);
