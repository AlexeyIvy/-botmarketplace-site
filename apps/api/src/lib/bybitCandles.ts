/**
 * Fetch historical OHLCV candles from Bybit public API (market/kline).
 * Uses mainnet public endpoint — no auth required.
 */

const BYBIT_PUBLIC = "https://api.bybit.com";
/** Maximum candles per request (Bybit cap) */
const PAGE_LIMIT = 1000;

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
