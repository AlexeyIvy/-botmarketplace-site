/**
 * Deterministic dataset hash (Stage 19a).
 *
 * Canonical string: candles sorted by openTimeMs ASC, one line per candle:
 *   openTimeMs|open|high|low|close|volume
 * where each DECIMAL field is formatted with .toFixed(8) (exactly 8 decimal places),
 * computed from DB-read Prisma.Decimal values (NOT from intermediate Number()).
 *
 * Lines joined with '\n', then sha256 hex.
 */

import { createHash } from "node:crypto";
import type { Prisma } from "@prisma/client";

export interface HashableCandle {
  openTimeMs: bigint;
  open: Prisma.Decimal;
  high: Prisma.Decimal;
  low: Prisma.Decimal;
  close: Prisma.Decimal;
  volume: Prisma.Decimal;
}

export function computeDatasetHash(candles: HashableCandle[]): string {
  const sorted = [...candles].sort((a, b) =>
    a.openTimeMs < b.openTimeMs ? -1 : a.openTimeMs > b.openTimeMs ? 1 : 0,
  );

  const lines = sorted.map(
    (c) =>
      `${c.openTimeMs}|${c.open.toFixed(8)}|${c.high.toFixed(8)}|${c.low.toFixed(8)}|${c.close.toFixed(8)}|${c.volume.toFixed(8)}`,
  );

  return createHash("sha256").update(lines.join("\n"), "utf8").digest("hex");
}
