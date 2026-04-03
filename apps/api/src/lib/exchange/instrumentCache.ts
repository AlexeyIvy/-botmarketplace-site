/**
 * Instrument metadata cache for Bybit linear perpetuals.
 *
 * Fetches and caches instrument info (tick size, qty step, min order qty,
 * min notional, max leverage) from the Bybit V5 instruments-info endpoint.
 *
 * Cache strategy:
 * - In-memory Map keyed by symbol
 * - TTL-based expiry (default 15 minutes)
 * - Lazy refresh: stale entries are re-fetched on next access
 * - Bulk prefetch available for startup/warm-up
 *
 * Stage 3 — Issue #129
 */

import { logger } from "../logger.js";

const log = logger.child({ module: "instrumentCache" });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface InstrumentInfo {
  symbol: string;
  baseCoin: string;
  quoteCoin: string;
  /** Minimum price increment (e.g. 0.10 for BTCUSDT) */
  tickSize: number;
  /** Minimum qty increment (e.g. 0.001 for BTCUSDT) */
  qtyStep: number;
  /** Minimum order quantity */
  minOrderQty: number;
  /** Maximum order quantity */
  maxOrderQty: number;
  /** Minimum notional value (USD) for an order */
  minNotional: number;
  /** Maximum leverage allowed */
  maxLeverage: number;
  /** Status from exchange */
  status: string;
  /** When this entry was fetched (ms) */
  fetchedAt: number;
}

interface BybitInstrumentItem {
  symbol: string;
  baseCoin: string;
  quoteCoin: string;
  status: string;
  lotSizeFilter: {
    minOrderQty: string;
    maxOrderQty: string;
    qtyStep: string;
    minNotionalValue?: string;
  };
  priceFilter: {
    tickSize: string;
  };
  leverageFilter: {
    maxLeverage: string;
  };
}

interface BybitInstrumentsResponse {
  retCode: number;
  retMsg: string;
  result: {
    list: BybitInstrumentItem[];
    nextPageCursor?: string;
  };
}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/** Default TTL for cached entries (15 minutes). */
const DEFAULT_TTL_MS = 15 * 60 * 1000;

/** Base URL — overridable via BYBIT_BASE_URL env var for demo/live routing. */
function getBaseUrl(): string {
  return process.env.BYBIT_BASE_URL ?? "https://api.bybit.com";
}

// ---------------------------------------------------------------------------
// Cache storage
// ---------------------------------------------------------------------------

const cache = new Map<string, InstrumentInfo>();
let lastBulkFetchMs = 0;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Get instrument metadata for a symbol. Returns cached value if fresh,
 * otherwise fetches from Bybit.
 *
 * @throws if the symbol is not found on the exchange
 */
export async function getInstrument(
  symbol: string,
  ttlMs = DEFAULT_TTL_MS,
): Promise<InstrumentInfo> {
  const cached = cache.get(symbol);
  if (cached && Date.now() - cached.fetchedAt < ttlMs) {
    return cached;
  }

  // Fetch single instrument
  const base = getBaseUrl();
  const url = `${base}/v5/market/instruments-info?category=linear&symbol=${encodeURIComponent(symbol)}`;

  const res = await fetch(url, { headers: { "User-Agent": "botmarketplace/1" } });
  if (!res.ok) {
    throw new Error(`Bybit instruments request failed: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as BybitInstrumentsResponse;
  if (json.retCode !== 0) {
    throw new Error(`Bybit API error ${json.retCode}: ${json.retMsg}`);
  }

  const item = json.result?.list?.find((i) => i.symbol === symbol);
  if (!item) {
    throw new Error(`Instrument not found: ${symbol}`);
  }

  const info = parseInstrument(item);
  cache.set(symbol, info);
  return info;
}

/**
 * Prefetch all linear perpetual instruments into the cache.
 * Useful at startup to avoid per-order latency.
 */
export async function prefetchInstruments(ttlMs = DEFAULT_TTL_MS): Promise<number> {
  // Avoid hammering the endpoint if recently fetched
  if (Date.now() - lastBulkFetchMs < ttlMs) {
    return cache.size;
  }

  const base = getBaseUrl();
  const url = `${base}/v5/market/instruments-info?category=linear&status=Trading&limit=1000`;

  const res = await fetch(url, { headers: { "User-Agent": "botmarketplace/1" } });
  if (!res.ok) {
    throw new Error(`Bybit instruments bulk fetch failed: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as BybitInstrumentsResponse;
  if (json.retCode !== 0) {
    throw new Error(`Bybit API error ${json.retCode}: ${json.retMsg}`);
  }

  const now = Date.now();
  for (const item of json.result?.list ?? []) {
    cache.set(item.symbol, parseInstrument(item, now));
  }
  lastBulkFetchMs = now;

  log.info({ count: cache.size }, "instrument cache prefetched");
  return cache.size;
}

/**
 * Check whether a symbol exists in the cache (without fetching).
 * Returns undefined if not cached or stale.
 */
export function getCachedInstrument(symbol: string, ttlMs = DEFAULT_TTL_MS): InstrumentInfo | undefined {
  const cached = cache.get(symbol);
  if (cached && Date.now() - cached.fetchedAt < ttlMs) {
    return cached;
  }
  return undefined;
}

/** Clear the entire cache (useful for testing). */
export function clearCache(): void {
  cache.clear();
  lastBulkFetchMs = 0;
}

/**
 * Inject instrument info directly into cache (useful for testing).
 */
export function setInstrument(info: InstrumentInfo): void {
  cache.set(info.symbol, info);
}

// ---------------------------------------------------------------------------
// Internal
// ---------------------------------------------------------------------------

function parseInstrument(item: BybitInstrumentItem, now = Date.now()): InstrumentInfo {
  return {
    symbol: item.symbol,
    baseCoin: item.baseCoin,
    quoteCoin: item.quoteCoin,
    tickSize: Number(item.priceFilter.tickSize),
    qtyStep: Number(item.lotSizeFilter.qtyStep),
    minOrderQty: Number(item.lotSizeFilter.minOrderQty),
    maxOrderQty: Number(item.lotSizeFilter.maxOrderQty),
    minNotional: Number(item.lotSizeFilter.minNotionalValue ?? "0"),
    maxLeverage: Number(item.leverageFilter.maxLeverage),
    status: item.status,
    fetchedAt: now,
  };
}
