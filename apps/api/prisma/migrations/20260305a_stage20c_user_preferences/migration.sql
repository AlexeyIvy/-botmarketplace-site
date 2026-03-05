-- Stage 20c: User Preferences Sync
-- Adds per-user preferences table (not workspace-scoped).

CREATE TABLE "UserPreference" (
    "id"           TEXT         NOT NULL,
    "userId"       TEXT         NOT NULL,
    "terminalJson" JSONB        NOT NULL DEFAULT '{}',
    "createdAt"    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"    TIMESTAMP(3) NOT NULL,

    CONSTRAINT "UserPreference_pkey" PRIMARY KEY ("id")
);

-- One preferences row per user
CREATE UNIQUE INDEX "UserPreference_userId_key" ON "UserPreference"("userId");

-- FK → User
ALTER TABLE "UserPreference"
    ADD CONSTRAINT "UserPreference_userId_fkey"
    FOREIGN KEY ("userId")
    REFERENCES "User"("id")
    ON DELETE CASCADE
    ON UPDATE CASCADE;
