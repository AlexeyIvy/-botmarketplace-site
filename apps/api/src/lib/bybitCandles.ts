/**
 * Bybit public market-data helpers (read-only, no auth required).
 * Used by: lab routes (candles for backtest), terminal routes (ticker + candles).
 */

const BYBIT_PUBLIC = "https://api.bybit.com";
/** Maximum candles per request (Bybit cap) */
const PAGE_LIMIT = 1000;

// ---------------------------------------------------------------------------
// Ticker
// ---------------------------------------------------------------------------

export interface Ticker {
  symbol: string;
  lastPrice: number;
  bidPrice: number;
  askPrice: number;
  prevPrice24h: number;
  price24hPcnt: number;
  highPrice24h: number;
  lowPrice24h: number;
  volume24h: number;
  turnover24h: number;
}

interface BybitTickerResponse {
  retCode: number;
  retMsg: string;
  result: {
    list: Array<{
      symbol: string;
      lastPrice: string;
      bid1Price: string;
      ask1Price: string;
      prevPrice24h: string;
      price24hPcnt: string;
      highPrice24h: string;
      lowPrice24h: string;
      volume24h: string;
      turnover24h: string;
    }>;
  };
}

/**
 * Fetch current ticker for a linear perpetual symbol (e.g. "BTCUSDT").
 * Throws if the symbol is not found or Bybit returns an error.
 */
export async function fetchTicker(symbol: string): Promise<Ticker> {
  const url =
    `${BYBIT_PUBLIC}/v5/market/tickers` +
    `?category=linear&symbol=${encodeURIComponent(symbol)}`;

  const res = await fetch(url, { headers: { "User-Agent": "botmarketplace-terminal/1" } });
  if (!res.ok) {
    throw new Error(`Bybit ticker request failed: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as BybitTickerResponse;
  if (json.retCode !== 0) {
    throw new Error(`Bybit API error ${json.retCode}: ${json.retMsg}`);
  }

  const item = json.result?.list?.[0];
  if (!item) {
    throw new Error(`Symbol not found: ${symbol}`);
  }

  return {
    symbol: item.symbol,
    lastPrice: Number(item.lastPrice),
    bidPrice: Number(item.bid1Price),
    askPrice: Number(item.ask1Price),
    prevPrice24h: Number(item.prevPrice24h),
    price24hPcnt: Number(item.price24hPcnt),
    highPrice24h: Number(item.highPrice24h),
    lowPrice24h: Number(item.lowPrice24h),
    volume24h: Number(item.volume24h),
    turnover24h: Number(item.turnover24h),
  };
}

export interface Candle {
  openTime: number; // ms
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface BybitKlineResponse {
  retCode: number;
  retMsg: string;
  result: {
    list: string[][];
  };
}

/**
 * Fetch up to maxCandles candles for the given symbol/interval between fromMs and toMs.
 * Bybit returns candles in descending order; we reverse to ascending.
 *
 * @param symbol  e.g. "BTCUSDT"
 * @param interval  "1" | "5" | "15" | "60"
 * @param fromMs  start timestamp in milliseconds (inclusive)
 * @param toMs    end timestamp in milliseconds (inclusive)
 * @param maxCandles  cap to avoid runaway fetches (default 2000)
 */
export async function fetchCandles(
  symbol: string,
  interval: string,
  fromMs: number,
  toMs: number,
  maxCandles = 2000,
): Promise<Candle[]> {
  const all: Candle[] = [];
  let cursor = toMs;

  while (all.length < maxCandles) {
    const url =
      `${BYBIT_PUBLIC}/v5/market/kline` +
      `?category=linear&symbol=${encodeURIComponent(symbol)}` +
      `&interval=${interval}&start=${fromMs}&end=${cursor}&limit=${PAGE_LIMIT}`;

    const res = await fetch(url, { headers: { "User-Agent": "botmarketplace-backtest/1" } });
    if (!res.ok) {
      throw new Error(`Bybit kline request failed: ${res.status} ${res.statusText}`);
    }

    const json = (await res.json()) as BybitKlineResponse;
    if (json.retCode !== 0) {
      throw new Error(`Bybit API error ${json.retCode}: ${json.retMsg}`);
    }

    const raw = json.result?.list ?? [];
    if (raw.length === 0) break;

    // Each item: [openTime, open, high, low, close, volume, turnover]
    const page: Candle[] = raw.map((row) => ({
      openTime: Number(row[0]),
      open:     Number(row[1]),
      high:     Number(row[2]),
      low:      Number(row[3]),
      close:    Number(row[4]),
      volume:   Number(row[5]),
    }));

    // Bybit returns newest-first; collect them in reverse
    for (let i = page.length - 1; i >= 0; i--) {
      if (page[i].openTime >= fromMs && page[i].openTime <= toMs) {
        all.push(page[i]);
      }
    }

    const oldest = Math.min(...page.map((c) => c.openTime));
    if (oldest <= fromMs || page.length < PAGE_LIMIT) break;
    cursor = oldest - 1;
  }

  // Sort ascending by openTime (deduplicate just in case)
  all.sort((a, b) => a.openTime - b.openTime);
  const unique = all.filter((c, i) => i === 0 || c.openTime !== all[i - 1].openTime);
  return unique.slice(0, maxCandles);
}
