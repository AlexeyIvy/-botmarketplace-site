-- Phase 4: StrategyGraph + StrategyGraphVersion
-- Authoring layer for graph-to-DSL compiler (docs/23-lab-v2-ide-spec.md §17)
-- Additive migration — no changes to existing tables.

-- StrategyGraph: mutable draft; updated on auto-save / compile
CREATE TABLE "StrategyGraph" (
    "id"                    TEXT NOT NULL,
    "workspaceId"           TEXT NOT NULL,
    "name"                  TEXT NOT NULL,
    "blockLibraryVersion"   TEXT NOT NULL DEFAULT '0.3.0',
    "dslVersionTarget"      INTEGER NOT NULL DEFAULT 1,
    "graphJson"             JSONB NOT NULL,
    "validationSummaryJson" JSONB,
    "createdAt"             TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"             TIMESTAMP(3) NOT NULL,

    CONSTRAINT "StrategyGraph_pkey" PRIMARY KEY ("id")
);

-- StrategyGraphVersion: immutable snapshot created on each compile
CREATE TABLE "StrategyGraphVersion" (
    "id"                  TEXT NOT NULL,
    "strategyGraphId"     TEXT NOT NULL,
    "version"             INTEGER NOT NULL,
    "blockLibraryVersion" TEXT NOT NULL,
    "graphSnapshotJson"   JSONB NOT NULL,
    "strategyVersionId"   TEXT NOT NULL,
    "createdAt"           TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "StrategyGraphVersion_pkey" PRIMARY KEY ("id")
);

-- Indexes
CREATE INDEX "StrategyGraph_workspaceId_idx" ON "StrategyGraph"("workspaceId");
CREATE UNIQUE INDEX "StrategyGraphVersion_strategyGraphId_version_key" ON "StrategyGraphVersion"("strategyGraphId", "version");
CREATE INDEX "StrategyGraphVersion_strategyGraphId_idx" ON "StrategyGraphVersion"("strategyGraphId");
CREATE INDEX "StrategyGraphVersion_strategyVersionId_idx" ON "StrategyGraphVersion"("strategyVersionId");

-- Foreign keys
ALTER TABLE "StrategyGraph" ADD CONSTRAINT "StrategyGraph_workspaceId_fkey"
    FOREIGN KEY ("workspaceId") REFERENCES "Workspace"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "StrategyGraphVersion" ADD CONSTRAINT "StrategyGraphVersion_strategyGraphId_fkey"
    FOREIGN KEY ("strategyGraphId") REFERENCES "StrategyGraph"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "StrategyGraphVersion" ADD CONSTRAINT "StrategyGraphVersion_strategyVersionId_fkey"
    FOREIGN KEY ("strategyVersionId") REFERENCES "StrategyVersion"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
