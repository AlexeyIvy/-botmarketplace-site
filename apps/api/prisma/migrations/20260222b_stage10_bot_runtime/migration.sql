-- Stage 10: Bot Runtime Hardening
-- 1. Add exchangeConnectionId (nullable) to Bot — links bot to trading credentials
-- 2. Add durationMinutes (nullable) to BotRun — configurable run timeout

ALTER TABLE "Bot"
  ADD COLUMN IF NOT EXISTS "exchangeConnectionId" TEXT;

ALTER TABLE "BotRun"
  ADD COLUMN IF NOT EXISTS "durationMinutes" INTEGER;

-- FK: Bot.exchangeConnectionId → ExchangeConnection.id (RESTRICT so we can't delete a connection in use)
ALTER TABLE "Bot"
  ADD CONSTRAINT "Bot_exchangeConnectionId_fkey"
  FOREIGN KEY ("exchangeConnectionId")
  REFERENCES "ExchangeConnection"("id")
  ON DELETE SET NULL
  ON UPDATE CASCADE;
