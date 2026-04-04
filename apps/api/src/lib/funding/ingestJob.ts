/**
 * Funding ingestion job — fetches live data from Bybit and persists
 * FundingSnapshot + SpreadSnapshot records to the database.
 *
 * Designed to be called from a cron scheduler (every 8 hours).
 */

import type { PrismaClient } from "@prisma/client";
import { fetchFundingHistory, fetchLinearTickers, fetchSpotTickers } from "./fetcher.js";
import { parseFundingHistory, parseLinearTicker, buildSpreadFromTickers } from "./ingestion.js";
import { logger } from "../logger.js";

/** Default symbols to ingest funding history for. */
const DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"];

/**
 * Ingest historical funding rates for a list of symbols.
 * Fetches from Bybit, parses, and bulk-inserts into FundingSnapshot.
 */
export async function ingestFundingRates(
  prisma: PrismaClient,
  symbols: string[] = DEFAULT_SYMBOLS,
): Promise<number> {
  let totalInserted = 0;

  for (const symbol of symbols) {
    try {
      const rawItems = await fetchFundingHistory(symbol);
      const snapshots = parseFundingHistory(rawItems);

      if (snapshots.length === 0) continue;

      const result = await prisma.fundingSnapshot.createMany({
        data: snapshots.map((s) => ({
          symbol: s.symbol,
          fundingRate: s.fundingRate,
          nextFundingAt: new Date(s.nextFundingAt),
          timestamp: new Date(s.timestamp),
        })),
        skipDuplicates: true,
      });

      totalInserted += result.count;
      logger.info({ symbol, inserted: result.count }, "Funding rates ingested");
    } catch (err) {
      logger.error({ err, symbol }, "Failed to ingest funding rates");
    }
  }

  return totalInserted;
}

/**
 * Ingest current spread snapshots by matching linear and spot tickers.
 * Fetches all linear + spot tickers, matches by symbol, and bulk-inserts SpreadSnapshots.
 */
export async function ingestSpreads(prisma: PrismaClient): Promise<number> {
  const now = Date.now();

  const [linearTickers, spotTickers] = await Promise.all([
    fetchLinearTickers(),
    fetchSpotTickers(),
  ]);

  // Build a spot lookup: "BTCUSDT" → BybitSpotTicker
  const spotMap = new Map(spotTickers.map((t) => [t.symbol, t]));

  const spreads: Array<{
    symbol: string;
    spotPrice: number;
    perpPrice: number;
    basisBps: number;
    timestamp: Date;
  }> = [];

  for (const perpTicker of linearTickers) {
    // Bybit perp symbols end with "USDT", spot symbols are the same
    const spotTicker = spotMap.get(perpTicker.symbol);
    if (!spotTicker) continue;

    const spread = buildSpreadFromTickers(perpTicker, spotTicker, now);
    if (!spread) continue;

    spreads.push({
      symbol: spread.symbol,
      spotPrice: spread.spotPrice,
      perpPrice: spread.perpPrice,
      basisBps: spread.basisBps,
      timestamp: new Date(spread.timestamp),
    });
  }

  if (spreads.length === 0) return 0;

  const result = await prisma.spreadSnapshot.createMany({
    data: spreads,
    skipDuplicates: true,
  });

  logger.info({ inserted: result.count, total: spreads.length }, "Spread snapshots ingested");
  return result.count;
}

/**
 * Run the full ingestion pipeline: funding rates + spreads.
 * Call this from the cron scheduler.
 */
export async function runIngestion(prisma: PrismaClient): Promise<void> {
  const start = Date.now();
  logger.info("Starting funding ingestion job");

  try {
    const [fundingCount, spreadCount] = await Promise.all([
      ingestFundingRates(prisma),
      ingestSpreads(prisma),
    ]);

    const durationMs = Date.now() - start;
    logger.info(
      { fundingCount, spreadCount, durationMs },
      "Funding ingestion job completed",
    );
  } catch (err) {
    logger.error({ err }, "Funding ingestion job failed");
  }
}
