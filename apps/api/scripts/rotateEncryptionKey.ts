#!/usr/bin/env tsx
/**
 * Re-encrypt all secrets after rotating SECRET_ENCRYPTION_KEY (§5.7).
 *
 * Prerequisites:
 *   1. New key generated:  openssl rand -hex 32
 *   2. .env updated BEFORE running this script:
 *        SECRET_ENCRYPTION_KEY=<new 64-hex key>
 *        SECRET_ENCRYPTION_KEY_OLD=<previous 64-hex key>
 *   3. Services restarted so the API can decrypt existing records with the
 *      old key while placing new encryptions with the new key.
 *   4. A DB backup taken (see RUNBOOK §7).
 *
 * This script walks every row containing encrypted secrets
 * (ExchangeConnection.encryptedSecret, WorkspaceNotification
 * notifyJson.telegram.botToken), decrypts with whichever key works,
 * and re-encrypts with the current (new) key.
 *
 * Idempotent: re-running on already-rotated rows is a no-op because the
 * current key decrypts and re-encrypts to the same ciphertext family.
 *
 * Usage:
 *   pnpm --filter @botmarketplace/api exec tsx scripts/rotateEncryptionKey.ts
 *   pnpm --filter @botmarketplace/api exec tsx scripts/rotateEncryptionKey.ts --dry-run
 */

import { PrismaClient } from "@prisma/client";
import {
  decryptWithFallback,
  encrypt,
  getEncryptionKeyRaw,
} from "../src/lib/crypto.js";

const DRY_RUN = process.argv.includes("--dry-run");

async function main() {
  const prisma = new PrismaClient();
  const newKey = getEncryptionKeyRaw();

  console.log(`[rotateEncryptionKey] mode=${DRY_RUN ? "dry-run" : "apply"}`);

  // 1. ExchangeConnection.encryptedSecret
  const conns = await prisma.exchangeConnection.findMany({
    select: { id: true, encryptedSecret: true },
  });
  console.log(`[exchangeConnection] found ${conns.length} rows`);

  let ecRotated = 0;
  let ecSkipped = 0;
  let ecFailed = 0;
  for (const conn of conns) {
    try {
      const plain = decryptWithFallback(conn.encryptedSecret);
      const recrypted = encrypt(plain, newKey);
      if (recrypted === conn.encryptedSecret) {
        ecSkipped++;
        continue; // extremely unlikely (random IV) but keep for safety
      }
      if (!DRY_RUN) {
        await prisma.exchangeConnection.update({
          where: { id: conn.id },
          data: { encryptedSecret: recrypted },
        });
      }
      ecRotated++;
    } catch (err) {
      ecFailed++;
      console.error(`[exchangeConnection] ${conn.id} failed:`, (err as Error).message);
    }
  }
  console.log(`[exchangeConnection] rotated=${ecRotated} skipped=${ecSkipped} failed=${ecFailed}`);

  // 2. WorkspaceNotification — Telegram bot token (optionally encrypted)
  const notifs = await prisma.workspaceNotification.findMany({
    select: { id: true, notifyJson: true },
  });
  console.log(`[workspaceNotification] found ${notifs.length} rows`);

  let wnRotated = 0;
  let wnFailed = 0;
  let wnUnencrypted = 0;
  for (const row of notifs) {
    const config = (row.notifyJson ?? {}) as Record<string, unknown>;
    const tg = config.telegram as Record<string, unknown> | undefined;
    if (!tg || !tg._tokenEncrypted || typeof tg.botToken !== "string") {
      wnUnencrypted++;
      continue;
    }
    try {
      const plain = decryptWithFallback(tg.botToken);
      const recrypted = encrypt(plain, newKey);
      tg.botToken = recrypted;
      if (!DRY_RUN) {
        await prisma.workspaceNotification.update({
          where: { id: row.id },
          data: { notifyJson: config as object },
        });
      }
      wnRotated++;
    } catch (err) {
      wnFailed++;
      console.error(`[workspaceNotification] ${row.id} failed:`, (err as Error).message);
    }
  }
  console.log(
    `[workspaceNotification] rotated=${wnRotated} unencrypted=${wnUnencrypted} failed=${wnFailed}`,
  );

  const anyFailed = ecFailed + wnFailed;
  if (anyFailed > 0) {
    console.error(`[rotateEncryptionKey] ${anyFailed} rows failed — investigate before removing SECRET_ENCRYPTION_KEY_OLD`);
    process.exit(1);
  }

  if (DRY_RUN) {
    console.log("[rotateEncryptionKey] dry-run complete — no DB writes.");
  } else {
    console.log(
      "[rotateEncryptionKey] done. Verify app health, then remove SECRET_ENCRYPTION_KEY_OLD from .env and restart services.",
    );
  }

  await prisma.$disconnect();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
