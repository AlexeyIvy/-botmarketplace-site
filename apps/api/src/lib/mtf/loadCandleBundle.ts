/**
 * Multi-Interval Candle Loader (docs/52-T2).
 *
 * Single entry point that turns a `DatasetBundle` into a
 * `Map<CandleInterval, MarketCandle[]>`.
 *
 * Used by:
 *  - `botWorker` runtime (52-T3) — `mode: "runtime"`, may carry `true`
 *    placeholders meaning "any candles for this `(symbol, interval)`".
 *  - `runBacktest` and lab routes (52-T4) — `mode: "backtest"`, every value
 *    must be a concrete `MarketDataset.id`, results are bounded by `until`.
 *
 * Design notes:
 *  - Per-interval queries are issued in parallel via `Promise.all`.
 *  - An in-memory LRU caches results so several bots on the same symbol do
 *    not hammer Postgres on every tick. Runtime entries TTL out after 30s;
 *    backtest entries are pinned (the cache key encodes `until`, so a frozen
 *    historical slice is safely shareable).
 *  - On miss, `findMany` is called with `orderBy: openTimeMs desc` + `take:
 *    lookbackBars`, then reversed to ascending — that is the cheapest way to
 *    get the freshest N candles when the table has billions of older rows.
 */

import type { CandleInterval as PrismaCandleInterval, MarketCandle, PrismaClient } from "@prisma/client";
import type { Logger } from "pino";
import { prisma as defaultPrisma } from "../prisma.js";
import {
  bundleIntervals,
  type BundleMode,
  type CandleInterval,
  type DatasetBundle,
} from "../../types/datasetBundle.js";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export type CandlesByInterval = Map<CandleInterval, MarketCandle[]>;

export interface LoadCandleBundleArgs {
  symbol: string;
  bundle: DatasetBundle;
  /** How many candles per interval to load (latest N, returned in ASC order). */
  lookbackBars: number;
  mode: BundleMode;
  /** Backtest upper bound (inclusive). For runtime, leave undefined ⇒ now(). */
  until?: Date;
  /** Defaults to the shared singleton; overrideable for tests. */
  prismaClient?: PrismaClient;
  /** Optional logger; falls back to no-op when omitted. */
  logger?: Pick<Logger, "debug">;
}

export class CandleBundleLoadError extends Error {
  readonly field?: string;
  constructor(message: string, field?: string) {
    super(message);
    this.field = field;
    this.name = "CandleBundleLoadError";
  }
}

// ---------------------------------------------------------------------------
// LRU cache (module-scoped, deliberately small)
// ---------------------------------------------------------------------------

const RUNTIME_TTL_MS = 30_000;
const CACHE_MAX_ENTRIES = 64;

interface CacheEntry {
  candles: MarketCandle[];
  /** Absolute expiry time; Infinity for backtest pins. */
  expiresAt: number;
}

const cache = new Map<string, CacheEntry>();

function cacheKey(args: {
  mode: BundleMode;
  symbol: string;
  interval: CandleInterval;
  value: string | true;
  lookbackBars: number;
  until?: Date;
}): string {
  const valuePart = args.value === true ? "*" : `ds:${args.value}`;
  const untilPart = args.until ? `u:${args.until.getTime()}` : "u:live";
  return `${args.mode}|${args.symbol}|${args.interval}|${valuePart}|n:${args.lookbackBars}|${untilPart}`;
}

function cacheGet(key: string): MarketCandle[] | null {
  const entry = cache.get(key);
  if (!entry) return null;
  if (entry.expiresAt < Date.now()) {
    cache.delete(key);
    return null;
  }
  // LRU touch — re-insert moves the key to the most-recently-used end.
  cache.delete(key);
  cache.set(key, entry);
  return entry.candles;
}

function cacheSet(key: string, candles: MarketCandle[], mode: BundleMode): void {
  if (cache.size >= CACHE_MAX_ENTRIES) {
    // Drop the oldest entry — Map iteration order is insertion order.
    const oldest = cache.keys().next().value;
    if (oldest !== undefined) cache.delete(oldest);
  }
  const expiresAt = mode === "runtime" ? Date.now() + RUNTIME_TTL_MS : Number.POSITIVE_INFINITY;
  cache.set(key, { candles, expiresAt });
}

/** Test helper — exported so suites can reset between cases. */
export function _resetCandleBundleCache(): void {
  cache.clear();
}

// ---------------------------------------------------------------------------
// Loader
// ---------------------------------------------------------------------------

export async function loadCandleBundle(args: LoadCandleBundleArgs): Promise<CandlesByInterval> {
  const prisma = args.prismaClient ?? defaultPrisma;
  const intervals = bundleIntervals(args.bundle);
  if (intervals.length === 0) {
    throw new CandleBundleLoadError("bundle is empty", "datasetBundleJson");
  }
  if (!Number.isInteger(args.lookbackBars) || args.lookbackBars < 1) {
    throw new CandleBundleLoadError("lookbackBars must be a positive integer", "lookbackBars");
  }

  // Backtest mode: forbid the `true` placeholder — a backtest needs frozen data.
  if (args.mode === "backtest") {
    for (const interval of intervals) {
      if (args.bundle[interval] === true) {
        throw new CandleBundleLoadError(
          `backtest mode requires concrete datasetId for interval ${interval}`,
          `datasetBundleJson.${interval}`,
        );
      }
    }
  }

  const fetched = await Promise.all(
    intervals.map(async (interval) => {
      const value = args.bundle[interval];
      if (value === undefined) {
        // Should be impossible after bundleIntervals(), but narrow for TS.
        return [interval, [] as MarketCandle[]] as const;
      }
      const key = cacheKey({
        mode: args.mode,
        symbol: args.symbol,
        interval,
        value,
        lookbackBars: args.lookbackBars,
        until: args.until,
      });
      const cached = cacheGet(key);
      if (cached) return [interval, cached] as const;

      const candles = await fetchCandlesForInterval(prisma, args, interval, value);
      cacheSet(key, candles, args.mode);
      return [interval, candles] as const;
    }),
  );

  const out: CandlesByInterval = new Map();
  let total = 0;
  for (const [interval, candles] of fetched) {
    out.set(interval, candles);
    total += candles.length;
  }

  args.logger?.debug({
    msg: "loadCandleBundle",
    symbol: args.symbol,
    intervals,
    totalCandles: total,
    mode: args.mode,
  });

  return out;
}

// ---------------------------------------------------------------------------
// Per-interval fetch — encapsulates the runtime / backtest split
// ---------------------------------------------------------------------------

async function fetchCandlesForInterval(
  prisma: PrismaClient,
  args: LoadCandleBundleArgs,
  interval: CandleInterval,
  value: string | true,
): Promise<MarketCandle[]> {
  // Runtime + literal `true` ⇒ "any candles for symbol+interval", optionally
  // capped at `until` if the caller supplied one.
  if (value === true) {
    const upper = args.until ? BigInt(args.until.getTime()) : undefined;
    const rows = await prisma.marketCandle.findMany({
      where: {
        symbol: args.symbol,
        interval: interval as PrismaCandleInterval,
        ...(upper !== undefined ? { openTimeMs: { lte: upper } } : {}),
      },
      orderBy: { openTimeMs: "desc" },
      take: args.lookbackBars,
    });
    return rows.reverse();
  }

  // value is a concrete MarketDataset.id — load the dataset row to learn its
  // (exchange, symbol, interval, fromTsMs, toTsMs) and constrain the candle
  // scan to that range.
  const dataset = await prisma.marketDataset.findUnique({
    where: { id: value },
    select: {
      symbol: true,
      interval: true,
      exchange: true,
      fromTsMs: true,
      toTsMs: true,
    },
  });
  if (!dataset) {
    throw new CandleBundleLoadError(
      `dataset "${value}" not found for interval ${interval}`,
      `datasetBundleJson.${interval}`,
    );
  }
  if (dataset.symbol !== args.symbol) {
    throw new CandleBundleLoadError(
      `dataset "${value}" symbol ${dataset.symbol} does not match bundle symbol ${args.symbol}`,
      `datasetBundleJson.${interval}`,
    );
  }
  if (dataset.interval !== interval) {
    throw new CandleBundleLoadError(
      `dataset "${value}" interval ${dataset.interval} does not match bundle interval ${interval}`,
      `datasetBundleJson.${interval}`,
    );
  }

  const upper =
    args.until !== undefined
      ? bigIntMin(BigInt(args.until.getTime()), dataset.toTsMs)
      : dataset.toTsMs;

  const rows = await prisma.marketCandle.findMany({
    where: {
      exchange: dataset.exchange,
      symbol: dataset.symbol,
      interval: dataset.interval,
      openTimeMs: { gte: dataset.fromTsMs, lte: upper },
    },
    orderBy: { openTimeMs: "desc" },
    take: args.lookbackBars,
  });
  return rows.reverse();
}

function bigIntMin(a: bigint, b: bigint): bigint {
  return a < b ? a : b;
}
