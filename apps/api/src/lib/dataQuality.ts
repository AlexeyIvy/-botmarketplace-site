/**
 * Data quality analysis for market candle datasets (Stage 19a).
 *
 * qualityJson schema (7 fixed fields):
 *   intervalMs        — expected interval between candles in ms
 *   candleCount       — number of candles in DB range
 *   dupeAttempts      — candles that were already in DB (skipped on insert)
 *   gapsCount         — number of gaps > intervalMs between consecutive candles
 *   maxGapMs          — largest gap found (0 if no gaps)
 *   sanityIssuesCount — candles failing OHLCV sanity checks
 *   sanityDetails     — per-candle issue list
 *
 * Status rules:
 *   FAILED  — sanityIssuesCount > 0 OR maxGapMs > 5 * intervalMs
 *   PARTIAL — sanityIssuesCount == 0 AND gapsCount > 0
 *   READY   — sanityIssuesCount == 0 AND gapsCount == 0
 */

import type { Prisma } from "@prisma/client";

export interface QualityJson {
  intervalMs: number;
  candleCount: number;
  dupeAttempts: number;
  gapsCount: number;
  maxGapMs: number;
  sanityIssuesCount: number;
  sanityDetails: Array<{ openTimeMs: number; issue: string }>;
}

export type DatasetStatus = "READY" | "PARTIAL" | "FAILED";

export interface QualityResult {
  qualityJson: QualityJson;
  status: DatasetStatus;
}

export interface QualityCandle {
  openTimeMs: bigint;
  open: Prisma.Decimal;
  high: Prisma.Decimal;
  low: Prisma.Decimal;
  close: Prisma.Decimal;
  volume: Prisma.Decimal;
}

export function computeDataQuality(
  candles: QualityCandle[],
  intervalMs: number,
  dupeAttempts: number,
): QualityResult {
  const sorted = [...candles].sort((a, b) =>
    a.openTimeMs < b.openTimeMs ? -1 : a.openTimeMs > b.openTimeMs ? 1 : 0,
  );

  let gapsCount = 0;
  let maxGapMs = 0;
  const sanityDetails: Array<{ openTimeMs: number; issue: string }> = [];

  // Gap detection
  for (let i = 1; i < sorted.length; i++) {
    const gap = Number(sorted[i].openTimeMs - sorted[i - 1].openTimeMs);
    if (gap > intervalMs) {
      gapsCount++;
      if (gap > maxGapMs) maxGapMs = gap;
    }
  }

  // Sanity checks per candle: high >= open/close, low <= open/close, volume >= 0
  for (const c of sorted) {
    const o = c.open.toNumber();
    const h = c.high.toNumber();
    const l = c.low.toNumber();
    const cl = c.close.toNumber();
    const v = c.volume.toNumber();
    const ts = Number(c.openTimeMs);

    if (!Number.isFinite(o) || !Number.isFinite(h) || !Number.isFinite(l) || !Number.isFinite(cl)) {
      sanityDetails.push({ openTimeMs: ts, issue: "non_finite_price" });
    } else if (h < o || h < cl) {
      sanityDetails.push({ openTimeMs: ts, issue: "high_below_open_or_close" });
    } else if (l > o || l > cl) {
      sanityDetails.push({ openTimeMs: ts, issue: "low_above_open_or_close" });
    } else if (v < 0) {
      sanityDetails.push({ openTimeMs: ts, issue: "negative_volume" });
    }
  }

  const qualityJson: QualityJson = {
    intervalMs,
    candleCount: sorted.length,
    dupeAttempts,
    gapsCount,
    maxGapMs,
    sanityIssuesCount: sanityDetails.length,
    sanityDetails,
  };

  let status: DatasetStatus;
  if (sanityDetails.length > 0 || maxGapMs > 5 * intervalMs) {
    status = "FAILED";
  } else if (gapsCount > 0) {
    status = "PARTIAL";
  } else {
    status = "READY";
  }

  return { qualityJson, status };
}
