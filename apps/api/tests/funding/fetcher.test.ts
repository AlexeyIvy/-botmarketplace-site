import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchFundingHistory, fetchLinearTickers, fetchSpotTickers } from "../../src/lib/funding/fetcher.js";

// ── Mock global fetch ─────────────────────────────────────────────────────────

function mockFetchOk(result: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ retCode: 0, retMsg: "OK", result }),
  });
}

function mockFetchFail() {
  return vi.fn().mockRejectedValue(new Error("network error"));
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetchOk({ list: [] }));
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ── fetchFundingHistory ───────────────────────────────────────────────────────

describe("fetchFundingHistory", () => {
  it("returns parsed list from Bybit response", async () => {
    const items = [
      { symbol: "BTCUSDT", fundingRate: "0.0001", fundingRateTimestamp: "1700000000000" },
    ];
    vi.stubGlobal("fetch", mockFetchOk({ list: items }));

    const result = await fetchFundingHistory("BTCUSDT");
    expect(result).toEqual(items);
    expect(fetch).toHaveBeenCalledOnce();
  });

  it("retries once on network failure then throws", async () => {
    vi.stubGlobal("fetch", mockFetchFail());

    await expect(fetchFundingHistory("BTCUSDT")).rejects.toThrow("network error");
    expect(fetch).toHaveBeenCalledTimes(2); // original + 1 retry
  });

  it("throws on non-zero retCode", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ retCode: 10001, retMsg: "Invalid symbol", result: null }),
    }));

    await expect(fetchFundingHistory("BAD")).rejects.toThrow("Bybit API error");
  });
});

// ── fetchLinearTickers ────────────────────────────────────────────────────────

describe("fetchLinearTickers", () => {
  it("returns linear ticker list", async () => {
    const tickers = [
      { symbol: "BTCUSDT", fundingRate: "0.0001", nextFundingTime: "1700000000000", lastPrice: "42000" },
    ];
    vi.stubGlobal("fetch", mockFetchOk({ list: tickers }));

    const result = await fetchLinearTickers();
    expect(result).toEqual(tickers);
  });
});

// ── fetchSpotTickers ──────────────────────────────────────────────────────────

describe("fetchSpotTickers", () => {
  it("returns spot ticker list", async () => {
    const tickers = [{ symbol: "BTCUSDT", lastPrice: "41950" }];
    vi.stubGlobal("fetch", mockFetchOk({ list: tickers }));

    const result = await fetchSpotTickers();
    expect(result).toEqual(tickers);
  });
});
