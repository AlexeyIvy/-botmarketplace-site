-- Task #22: Add retry counter to BotIntent for dead-letter queue
-- Additive migration — default 0 for existing rows
ALTER TABLE "BotIntent" ADD COLUMN "retryCount" INTEGER NOT NULL DEFAULT 0;
