-- Task #20: Add optimistic lock version to BotRun
-- Additive migration — no data loss, default 0 for existing rows
ALTER TABLE "BotRun" ADD COLUMN "version" INTEGER NOT NULL DEFAULT 0;
