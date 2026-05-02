/**
 * Bybit Spot adapter — public market-data only (docs/55-T1).
 *
 * Three read-only helpers used by the funding-arbitrage runtime to size
 * and price the spot leg of a hedge:
 *
 *   - {@link fetchSpotCandles}      — kline series (for diagnostics / UI).
 *   - {@link fetchSpotTicker}       — last + bid/ask (for spread cost).
 *   - {@link getSpotInstrumentInfo} — tick / lot / min order size.
 *
 * Trading itself goes through the existing `bybitOrder.ts` with
 * `category: "spot"`. This file is intentionally market-data only — no
 * private endpoints, no order placement.
 *
 * Design notes:
 *  - Uses `fetch` + the Bybit v5 public surface, mirroring
 *    `bybitCandles.ts` and `exchange/instrumentCache.ts`.
 *  - Public market data does not require auth, so a single base URL
 *    (`BYBIT_PUBLIC_URL`, default `https://api.bybit.com`) covers both
 *    demo and live runtimes.
 *  - In-memory caches with TTLs from the docs/55-T1 spec:
 *      • instrument info — 24h (instruments rarely change),
 *      • ticker          — 5s  (cuts request volume during a hedge tick).
 *  - Caches are module-scoped and exported `_reset*ForTests` helpers let
 *    suites reset between cases.
 *  - All HTTP error paths funnel through {@link BybitSpotError} so callers
 *    can branch on `cause` (`http` / `api` / `parse`) instead of inspecting
 *    free-form messages.
 */

import { logger } from "../logger.js";
import type { CandleInterval } from "../../types/datasetBundle.js";

const log = logger.child({ module: "bybitSpot" });

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/** Public market data always lives on the main endpoint — no auth, no
 *  routing differences between demo and live. Mirrors bybitCandles.ts. */
function getBaseUrl(): string {
  return process.env.BYBIT_PUBLIC_URL ?? "https://api.bybit.com";
}

const USER_AGENT = "botmarketplace-spot/1";

const TICKER_TTL_MS = 5_000;
const INSTRUMENT_TTL_MS = 24 * 60 * 60 * 1000;

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface SpotCandle {
  /** Open time in ms since the Unix epoch. */
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SpotTicker {
  symbol: string;
  lastPrice: number;
  bidPrice: number;
  askPrice: number;
  bidSize: number;
  askSize: number;
  /** Server timestamp at the moment of the snapshot. */
  timestamp: Date;
}

export interface SpotInstrumentInfo {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  /** Minimum price increment. */
  tickSize: number;
  /** Minimum quantity increment. */
  lotSize: number;
  /** Minimum order quantity (base units). */
  minOrderSize: number;
  /** Minimum order notional (quote units, e.g. USDT). 0 if exchange omits it. */
  minOrderValue: number;
  /** When this entry was fetched (ms epoch). */
  fetchedAt: number;
}

/** Typed error so callers can branch on `cause` rather than parsing strings. */
export class BybitSpotError extends Error {
  readonly cause: "http" | "api" | "parse" | "not_found";
  readonly statusCode?: number;
  readonly retCode?: number;
  constructor(
    message: string,
    cause: BybitSpotError["cause"],
    extras: { statusCode?: number; retCode?: number } = {},
  ) {
    super(message);
    this.name = "BybitSpotError";
    this.cause = cause;
    this.statusCode = extras.statusCode;
    this.retCode = extras.retCode;
  }
}

// ---------------------------------------------------------------------------
// Bybit response shapes (only the fields we read)
// ---------------------------------------------------------------------------

interface BybitKlineResponse {
  retCode: number;
  retMsg: string;
  result: { list: string[][] };
}

interface BybitTickerResponse {
  retCode: number;
  retMsg: string;
  time?: number;
  result: {
    list: Array<{
      symbol: string;
      lastPrice: string;
      bid1Price: string;
      ask1Price: string;
      bid1Size?: string;
      ask1Size?: string;
    }>;
  };
}

interface BybitInstrumentItem {
  symbol: string;
  baseCoin: string;
  quoteCoin: string;
  status: string;
  lotSizeFilter: {
    minOrderQty: string;
    basePrecision?: string;
    quotePrecision?: string;
    minOrderAmt?: string;
  };
  priceFilter: { tickSize: string };
}

interface BybitInstrumentsResponse {
  retCode: number;
  retMsg: string;
  result: { list: BybitInstrumentItem[] };
}

// ---------------------------------------------------------------------------
// Caches
// ---------------------------------------------------------------------------

interface CacheEntry<T> { value: T; expiresAt: number }

const tickerCache = new Map<string, CacheEntry<SpotTicker>>();
const instrumentCache = new Map<string, SpotInstrumentInfo>();

/** Test helpers — exported so suites can reset state between cases. */
export function _resetSpotTickerCache(): void { tickerCache.clear(); }
export function _resetSpotInstrumentCache(): void { instrumentCache.clear(); }

// ---------------------------------------------------------------------------
// HTTP helper
// ---------------------------------------------------------------------------

/**
 * Issue a single GET to the Bybit v5 public surface and surface either a
 * typed `BybitSpotError` or the parsed JSON body. Centralised so HTTP /
 * API / parse error branches are uniform across the three public helpers.
 */
async function getJson<T extends { retCode: number; retMsg: string }>(
  path: string,
  query: Record<string, string | number>,
): Promise<T> {
  const url = new URL(getBaseUrl() + path);
  for (const [k, v] of Object.entries(query)) url.searchParams.set(k, String(v));

  log.debug({ msg: "[bybit-spot] GET", path, query });

  const res = await fetch(url.toString(), { headers: { "User-Agent": USER_AGENT } });
  if (!res.ok) {
    throw new BybitSpotError(
      `Bybit spot HTTP ${res.status} ${res.statusText} for ${path}`,
      "http",
      { statusCode: res.status },
    );
  }

  let json: T;
  try {
    json = (await res.json()) as T;
  } catch (err) {
    throw new BybitSpotError(
      `Bybit spot response parse error for ${path}: ${(err as Error).message}`,
      "parse",
    );
  }
  if (json.retCode !== 0) {
    throw new BybitSpotError(
      `Bybit spot API error ${json.retCode}: ${json.retMsg}`,
      "api",
      { retCode: json.retCode },
    );
  }
  return json;
}

// ---------------------------------------------------------------------------
// Candles
// ---------------------------------------------------------------------------

/** Map a {@link CandleInterval} (uppercase enum) to Bybit's kline-interval
 *  string ("1", "5", ..., "D"). Mirrors the helper in routes/lab.ts —
 *  duplicated locally to keep the adapter free of route-layer imports. */
function bybitIntervalCode(interval: CandleInterval): string {
  switch (interval) {
    case "M1":  return "1";
    case "M5":  return "5";
    case "M15": return "15";
    case "M30": return "30";
    case "H1":  return "60";
    case "H4":  return "240";
    case "D1":  return "D";
  }
}

const MAX_CANDLE_LIMIT = 1000;
const DEFAULT_CANDLE_LIMIT = 200;

/**
 * Fetch the latest N spot candles for `symbol` at `interval`.
 *
 * Returned candles are sorted ascending by `openTime` (Bybit returns
 * newest-first; we reverse).
 *
 * @throws {@link BybitSpotError} on HTTP / API failure.
 */
export async function fetchSpotCandles(args: {
  symbol: string;
  interval: CandleInterval;
  limit?: number;
}): Promise<SpotCandle[]> {
  const limit = clampLimit(args.limit, DEFAULT_CANDLE_LIMIT, MAX_CANDLE_LIMIT);
  const json = await getJson<BybitKlineResponse>("/v5/market/kline", {
    category: "spot",
    symbol: args.symbol,
    interval: bybitIntervalCode(args.interval),
    limit,
  });

  const raw = json.result?.list ?? [];
  const candles: SpotCandle[] = raw.map((row) => ({
    openTime: Number(row[0]),
    open:     Number(row[1]),
    high:     Number(row[2]),
    low:      Number(row[3]),
    close:    Number(row[4]),
    volume:   Number(row[5]),
  }));
  // Bybit returns newest-first; sort ascending so callers can append directly.
  candles.sort((a, b) => a.openTime - b.openTime);
  return candles;
}

function clampLimit(raw: number | undefined, fallback: number, max: number): number {
  if (!Number.isFinite(raw) || raw === undefined) return fallback;
  if (raw < 1) return 1;
  if (raw > max) return max;
  return Math.floor(raw);
}

// ---------------------------------------------------------------------------
// Ticker
// ---------------------------------------------------------------------------

/**
 * Fetch the current spot ticker for `symbol`. Cached for 5s — hedge ticks
 * may pull the same ticker multiple times per second; the cache cuts
 * outbound load without hiding meaningful price changes.
 */
export async function fetchSpotTicker(symbol: string): Promise<SpotTicker> {
  const now = Date.now();
  const hit = tickerCache.get(symbol);
  if (hit && hit.expiresAt > now) return hit.value;

  const json = await getJson<BybitTickerResponse>("/v5/market/tickers", {
    category: "spot",
    symbol,
  });
  const item = json.result?.list?.[0];
  if (!item) {
    throw new BybitSpotError(`Spot symbol not found: ${symbol}`, "not_found");
  }

  const ticker: SpotTicker = {
    symbol: item.symbol,
    lastPrice: Number(item.lastPrice),
    bidPrice: Number(item.bid1Price),
    askPrice: Number(item.ask1Price),
    bidSize: Number(item.bid1Size ?? "0"),
    askSize: Number(item.ask1Size ?? "0"),
    timestamp: new Date(typeof json.time === "number" ? json.time : now),
  };
  tickerCache.set(symbol, { value: ticker, expiresAt: now + TICKER_TTL_MS });
  return ticker;
}

// ---------------------------------------------------------------------------
// Instrument info
// ---------------------------------------------------------------------------

/**
 * Fetch spot instrument metadata (tick / lot / min sizes). Cached for 24h —
 * Bybit instrument parameters change rarely and a stale entry never makes
 * order rounding silently wrong (it would just produce a rejected order).
 */
export async function getSpotInstrumentInfo(symbol: string): Promise<SpotInstrumentInfo> {
  const now = Date.now();
  const cached = instrumentCache.get(symbol);
  if (cached && now - cached.fetchedAt < INSTRUMENT_TTL_MS) return cached;

  const json = await getJson<BybitInstrumentsResponse>("/v5/market/instruments-info", {
    category: "spot",
    symbol,
  });
  const item = json.result?.list?.find((i) => i.symbol === symbol);
  if (!item) {
    throw new BybitSpotError(`Spot instrument not found: ${symbol}`, "not_found");
  }

  const info: SpotInstrumentInfo = {
    symbol: item.symbol,
    baseAsset: item.baseCoin,
    quoteAsset: item.quoteCoin,
    tickSize: Number(item.priceFilter.tickSize),
    // Spot uses `basePrecision` (string like "0.000001") as the smallest
    // tradable unit; fall back to `minOrderQty` if absent.
    lotSize: Number(item.lotSizeFilter.basePrecision ?? item.lotSizeFilter.minOrderQty),
    minOrderSize: Number(item.lotSizeFilter.minOrderQty),
    minOrderValue: Number(item.lotSizeFilter.minOrderAmt ?? "0"),
    fetchedAt: now,
  };
  instrumentCache.set(symbol, info);
  return info;
}
