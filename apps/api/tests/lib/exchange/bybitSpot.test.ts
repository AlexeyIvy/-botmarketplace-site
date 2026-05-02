/**
 * Bybit Spot adapter — unit coverage (docs/55-T1).
 *
 * Mocks the global `fetch` to feed canned Bybit v5 responses through the
 * three public helpers and pin:
 *
 *   1. {@link fetchSpotCandles}      — newest-first input → ascending output;
 *      `limit` clamped to `[1, 1000]`; correct query string.
 *   2. {@link fetchSpotTicker}       — populated, plus 5s in-memory cache
 *      (second call within the window does NOT re-hit `fetch`).
 *   3. {@link getSpotInstrumentInfo} — populated, plus 24h in-memory cache.
 *   4. Error surface — HTTP non-2xx ⇒ `BybitSpotError {cause:'http'}`,
 *      `retCode!=0` ⇒ `{cause:'api'}`, missing-symbol ⇒ `{cause:'not_found'}`.
 *
 * Reset helpers are exported by the module so each test starts from a
 * clean cache, matching the behaviour of `instrumentCache.test.ts`.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  BybitSpotError,
  fetchSpotCandles,
  fetchSpotTicker,
  getSpotInstrumentInfo,
  _resetSpotInstrumentCache,
  _resetSpotTickerCache,
} from "../../../src/lib/exchange/bybitSpot.js";

// ---------------------------------------------------------------------------
// Test scaffolding
// ---------------------------------------------------------------------------

const realFetch = globalThis.fetch;

function mockFetch(impl: typeof fetch) {
  globalThis.fetch = impl as typeof fetch;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  _resetSpotTickerCache();
  _resetSpotInstrumentCache();
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

// ---------------------------------------------------------------------------
// 1. fetchSpotCandles
// ---------------------------------------------------------------------------

describe("fetchSpotCandles", () => {
  it("parses Bybit kline rows newest-first into ascending SpotCandle[]", async () => {
    // Bybit returns newest-first; the adapter must reverse to ascending.
    const klineList = [
      ["1730000600000", "100.4", "100.5", "100.3", "100.45", "10", "1004"],
      ["1730000300000", "100.1", "100.2", "100.0", "100.15", "20", "2003"],
      ["1730000000000", "99.9",  "100.0", "99.8",  "100.0",  "30", "3000"],
    ];
    const calls: string[] = [];
    mockFetch(vi.fn(async (input) => {
      calls.push(String(input));
      return jsonResponse({ retCode: 0, retMsg: "OK", result: { list: klineList } });
    }) as unknown as typeof fetch);

    const out = await fetchSpotCandles({ symbol: "BTCUSDT", interval: "M5", limit: 3 });

    expect(out).toHaveLength(3);
    expect(out[0].openTime).toBeLessThan(out[1].openTime);
    expect(out[2].openTime).toBe(1730000600000);
    expect(out[0]).toMatchObject({ open: 99.9, high: 100, low: 99.8, close: 100, volume: 30 });

    // Query-string sanity — category / symbol / interval / limit all set.
    expect(calls[0]).toContain("category=spot");
    expect(calls[0]).toContain("symbol=BTCUSDT");
    expect(calls[0]).toContain("interval=5");
    expect(calls[0]).toContain("limit=3");
  });

  it("clamps `limit` into [1, 1000]; defaults to 200 when absent", async () => {
    const calls: string[] = [];
    mockFetch(vi.fn(async (input) => {
      calls.push(String(input));
      return jsonResponse({ retCode: 0, retMsg: "OK", result: { list: [] } });
    }) as unknown as typeof fetch);

    await fetchSpotCandles({ symbol: "BTCUSDT", interval: "M5" });
    await fetchSpotCandles({ symbol: "BTCUSDT", interval: "M5", limit: 99999 });
    await fetchSpotCandles({ symbol: "BTCUSDT", interval: "M5", limit: 0 });

    expect(calls[0]).toContain("limit=200");
    expect(calls[1]).toContain("limit=1000");
    expect(calls[2]).toContain("limit=1");
  });

  it("maps every CandleInterval to the correct Bybit interval code", async () => {
    const captured: string[] = [];
    mockFetch(vi.fn(async (input) => {
      captured.push(String(input));
      return jsonResponse({ retCode: 0, retMsg: "OK", result: { list: [] } });
    }) as unknown as typeof fetch);

    const cases: Array<[Parameters<typeof fetchSpotCandles>[0]["interval"], string]> = [
      ["M1", "interval=1"],
      ["M5", "interval=5"],
      ["M15", "interval=15"],
      ["M30", "interval=30"],
      ["H1", "interval=60"],
      ["H4", "interval=240"],
      ["D1", "interval=D"],
    ];
    for (const [iv] of cases) {
      await fetchSpotCandles({ symbol: "BTCUSDT", interval: iv });
    }
    for (let i = 0; i < cases.length; i++) {
      expect(captured[i]).toContain(cases[i][1]);
    }
  });
});

// ---------------------------------------------------------------------------
// 2. fetchSpotTicker
// ---------------------------------------------------------------------------

describe("fetchSpotTicker", () => {
  function tickerResponse() {
    return jsonResponse({
      retCode: 0,
      retMsg: "OK",
      time: 1_730_000_000_000,
      result: {
        list: [{
          symbol: "BTCUSDT",
          lastPrice: "65000.5",
          bid1Price: "64999.5",
          ask1Price: "65001.5",
          bid1Size: "0.123",
          ask1Size: "0.456",
        }],
      },
    });
  }

  it("returns parsed numbers + a Date timestamp", async () => {
    mockFetch(vi.fn(async () => tickerResponse()) as unknown as typeof fetch);

    const t = await fetchSpotTicker("BTCUSDT");
    expect(t).toMatchObject({
      symbol: "BTCUSDT",
      lastPrice: 65000.5,
      bidPrice: 64999.5,
      askPrice: 65001.5,
      bidSize: 0.123,
      askSize: 0.456,
    });
    expect(t.timestamp).toBeInstanceOf(Date);
    expect(t.timestamp.getTime()).toBe(1_730_000_000_000);
  });

  it("caches subsequent calls within the 5s TTL (one HTTP request total)", async () => {
    const fetchMock = vi.fn(async () => tickerResponse());
    mockFetch(fetchMock as unknown as typeof fetch);

    const a = await fetchSpotTicker("BTCUSDT");
    const b = await fetchSpotTicker("BTCUSDT");
    expect(b).toEqual(a);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("re-fetches after the TTL expires (manual cache reset stand-in)", async () => {
    const fetchMock = vi.fn(async () => tickerResponse());
    mockFetch(fetchMock as unknown as typeof fetch);

    await fetchSpotTicker("BTCUSDT");
    _resetSpotTickerCache();
    await fetchSpotTicker("BTCUSDT");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("throws BybitSpotError(cause='not_found') when symbol is absent", async () => {
    mockFetch(vi.fn(async () =>
      jsonResponse({ retCode: 0, retMsg: "OK", result: { list: [] } }),
    ) as unknown as typeof fetch);

    await expect(fetchSpotTicker("NOPE")).rejects.toMatchObject({
      name: "BybitSpotError",
      cause: "not_found",
    });
  });
});

// ---------------------------------------------------------------------------
// 3. getSpotInstrumentInfo
// ---------------------------------------------------------------------------

describe("getSpotInstrumentInfo", () => {
  function instrumentResponse(extras: Record<string, string> = {}) {
    return jsonResponse({
      retCode: 0,
      retMsg: "OK",
      result: {
        list: [{
          symbol: "BTCUSDT",
          baseCoin: "BTC",
          quoteCoin: "USDT",
          status: "Trading",
          lotSizeFilter: {
            minOrderQty: "0.0001",
            basePrecision: "0.000001",
            minOrderAmt: "5",
            ...extras,
          },
          priceFilter: { tickSize: "0.01" },
        }],
      },
    });
  }

  it("returns parsed instrument metadata with numeric fields", async () => {
    mockFetch(vi.fn(async () => instrumentResponse()) as unknown as typeof fetch);

    const info = await getSpotInstrumentInfo("BTCUSDT");
    expect(info).toMatchObject({
      symbol: "BTCUSDT",
      baseAsset: "BTC",
      quoteAsset: "USDT",
      tickSize: 0.01,
      lotSize: 0.000001,
      minOrderSize: 0.0001,
      minOrderValue: 5,
    });
    expect(typeof info.fetchedAt).toBe("number");
  });

  it("falls back to minOrderQty for lotSize when basePrecision is omitted", async () => {
    mockFetch(vi.fn(async () => jsonResponse({
      retCode: 0,
      retMsg: "OK",
      result: {
        list: [{
          symbol: "BTCUSDT",
          baseCoin: "BTC",
          quoteCoin: "USDT",
          status: "Trading",
          lotSizeFilter: { minOrderQty: "0.0001" },
          priceFilter: { tickSize: "0.01" },
        }],
      },
    })) as unknown as typeof fetch);

    const info = await getSpotInstrumentInfo("BTCUSDT");
    expect(info.lotSize).toBe(0.0001);
    expect(info.minOrderValue).toBe(0); // exchange omitted minOrderAmt
  });

  it("caches subsequent calls (one HTTP request total)", async () => {
    const fetchMock = vi.fn(async () => instrumentResponse());
    mockFetch(fetchMock as unknown as typeof fetch);

    await getSpotInstrumentInfo("BTCUSDT");
    await getSpotInstrumentInfo("BTCUSDT");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws BybitSpotError(cause='not_found') when the symbol is absent", async () => {
    mockFetch(vi.fn(async () =>
      jsonResponse({ retCode: 0, retMsg: "OK", result: { list: [] } }),
    ) as unknown as typeof fetch);

    await expect(getSpotInstrumentInfo("ZZZ")).rejects.toMatchObject({
      name: "BybitSpotError",
      cause: "not_found",
    });
  });
});

// ---------------------------------------------------------------------------
// 4. Error surface — uniform across all three helpers
// ---------------------------------------------------------------------------

describe("BybitSpotError", () => {
  it("HTTP non-2xx maps to cause='http' with statusCode", async () => {
    mockFetch(vi.fn(async () =>
      new Response("rate limit", { status: 429, statusText: "Too Many Requests" }),
    ) as unknown as typeof fetch);

    await expect(fetchSpotTicker("BTCUSDT")).rejects.toMatchObject({
      name: "BybitSpotError",
      cause: "http",
      statusCode: 429,
    });
  });

  it("retCode != 0 maps to cause='api' with retCode", async () => {
    mockFetch(vi.fn(async () =>
      jsonResponse({ retCode: 10001, retMsg: "Invalid request", result: { list: [] } }),
    ) as unknown as typeof fetch);

    await expect(getSpotInstrumentInfo("BTCUSDT")).rejects.toMatchObject({
      name: "BybitSpotError",
      cause: "api",
      retCode: 10001,
    });
  });

  it("BybitSpotError is an instance of Error so existing handlers still catch it", async () => {
    mockFetch(vi.fn(async () =>
      new Response("bad", { status: 500, statusText: "Server Error" }),
    ) as unknown as typeof fetch);

    try {
      await fetchSpotCandles({ symbol: "BTCUSDT", interval: "M5" });
      expect.fail("expected throw");
    } catch (err) {
      expect(err).toBeInstanceOf(BybitSpotError);
      expect(err).toBeInstanceOf(Error);
    }
  });
});
