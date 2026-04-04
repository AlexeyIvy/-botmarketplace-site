import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ingestFundingRates, ingestSpreads } from "../../src/lib/funding/ingestJob.js";

// ── Mock fetcher module ───────────────────────────────────────────────────────

vi.mock("../../src/lib/funding/fetcher.js", () => ({
  fetchFundingHistory: vi.fn(),
  fetchLinearTickers: vi.fn(),
  fetchSpotTickers: vi.fn(),
}));

import { fetchFundingHistory, fetchLinearTickers, fetchSpotTickers } from "../../src/lib/funding/fetcher.js";

const mockFetchFundingHistory = vi.mocked(fetchFundingHistory);
const mockFetchLinearTickers = vi.mocked(fetchLinearTickers);
const mockFetchSpotTickers = vi.mocked(fetchSpotTickers);

// ── Mock Prisma client ────────────────────────────────────────────────────────

function makeMockPrisma() {
  return {
    fundingSnapshot: {
      createMany: vi.fn().mockResolvedValue({ count: 0 }),
    },
    spreadSnapshot: {
      createMany: vi.fn().mockResolvedValue({ count: 0 }),
    },
  } as any;
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ── ingestFundingRates ────────────────────────────────────────────────────────

describe("ingestFundingRates", () => {
  it("fetches, parses, and inserts funding snapshots", async () => {
    const rawItems = [
      { symbol: "BTCUSDT", fundingRate: "0.0001", fundingRateTimestamp: "1700000000000" },
      { symbol: "BTCUSDT", fundingRate: "0.0002", fundingRateTimestamp: "1700028800000" },
    ];
    mockFetchFundingHistory.mockResolvedValue(rawItems);

    const prisma = makeMockPrisma();
    prisma.fundingSnapshot.createMany.mockResolvedValue({ count: 2 });

    const count = await ingestFundingRates(prisma, ["BTCUSDT"]);

    expect(count).toBe(2);
    expect(mockFetchFundingHistory).toHaveBeenCalledWith("BTCUSDT");
    expect(prisma.fundingSnapshot.createMany).toHaveBeenCalledOnce();

    // Verify data shape passed to createMany
    const callArgs = prisma.fundingSnapshot.createMany.mock.calls[0][0];
    expect(callArgs.data).toHaveLength(2);
    expect(callArgs.data[0].symbol).toBe("BTCUSDT");
    expect(callArgs.data[0].fundingRate).toBe(0.0001);
    expect(callArgs.data[0].timestamp).toBeInstanceOf(Date);
    expect(callArgs.data[0].nextFundingAt).toBeInstanceOf(Date);
    expect(callArgs.skipDuplicates).toBe(true);
  });

  it("skips symbol when fetch returns empty", async () => {
    mockFetchFundingHistory.mockResolvedValue([]);

    const prisma = makeMockPrisma();
    const count = await ingestFundingRates(prisma, ["BTCUSDT"]);

    expect(count).toBe(0);
    expect(prisma.fundingSnapshot.createMany).not.toHaveBeenCalled();
  });

  it("continues other symbols when one fails", async () => {
    mockFetchFundingHistory
      .mockRejectedValueOnce(new Error("timeout"))
      .mockResolvedValueOnce([
        { symbol: "ETHUSDT", fundingRate: "0.0003", fundingRateTimestamp: "1700000000000" },
      ]);

    const prisma = makeMockPrisma();
    prisma.fundingSnapshot.createMany.mockResolvedValue({ count: 1 });

    const count = await ingestFundingRates(prisma, ["BTCUSDT", "ETHUSDT"]);

    expect(count).toBe(1);
    expect(prisma.fundingSnapshot.createMany).toHaveBeenCalledOnce();
  });
});

// ── ingestSpreads ─────────────────────────────────────────────────────────────

describe("ingestSpreads", () => {
  it("matches linear and spot tickers to produce spread snapshots", async () => {
    mockFetchLinearTickers.mockResolvedValue([
      { symbol: "BTCUSDT", fundingRate: "0.0001", nextFundingTime: "1700028800000", lastPrice: "42100" },
      { symbol: "ETHUSDT", fundingRate: "0.0002", nextFundingTime: "1700028800000", lastPrice: "2210" },
    ]);
    mockFetchSpotTickers.mockResolvedValue([
      { symbol: "BTCUSDT", lastPrice: "42000" },
      // ETHUSDT missing from spot → should be skipped
    ]);

    const prisma = makeMockPrisma();
    prisma.spreadSnapshot.createMany.mockResolvedValue({ count: 1 });

    const count = await ingestSpreads(prisma);

    expect(count).toBe(1);
    expect(prisma.spreadSnapshot.createMany).toHaveBeenCalledOnce();

    const callArgs = prisma.spreadSnapshot.createMany.mock.calls[0][0];
    expect(callArgs.data).toHaveLength(1);
    expect(callArgs.data[0].symbol).toBe("BTCUSDT");
    expect(callArgs.data[0].spotPrice).toBe(42000);
    expect(callArgs.data[0].perpPrice).toBe(42100);
    expect(typeof callArgs.data[0].basisBps).toBe("number");
    expect(callArgs.data[0].timestamp).toBeInstanceOf(Date);
  });

  it("returns 0 when no tickers match", async () => {
    mockFetchLinearTickers.mockResolvedValue([
      { symbol: "XYZUSDT", fundingRate: "0.0001", nextFundingTime: "1700028800000", lastPrice: "10" },
    ]);
    mockFetchSpotTickers.mockResolvedValue([
      { symbol: "ABCUSDT", lastPrice: "5" },
    ]);

    const prisma = makeMockPrisma();
    const count = await ingestSpreads(prisma);

    expect(count).toBe(0);
    expect(prisma.spreadSnapshot.createMany).not.toHaveBeenCalled();
  });
});
