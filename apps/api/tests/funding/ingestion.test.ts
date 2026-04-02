import { describe, it, expect } from "vitest";
import {
  parseFundingHistoryItem,
  parseFundingHistory,
  buildSpreadFromTickers,
} from "../../src/lib/funding/ingestion.js";
import type {
  BybitFundingHistoryItem,
  BybitLinearTicker,
  BybitSpotTicker,
} from "../../src/lib/funding/ingestion.js";

// ── parseFundingHistoryItem ─────────────────────────────────────────────────

describe("parseFundingHistoryItem", () => {
  it("parses a Bybit funding history item", () => {
    const item: BybitFundingHistoryItem = {
      symbol: "BTCUSDT",
      fundingRate: "0.0001",
      fundingRateTimestamp: "1700000000000",
    };
    const snap = parseFundingHistoryItem(item);
    expect(snap.symbol).toBe("BTCUSDT");
    expect(snap.fundingRate).toBe(0.0001);
    expect(snap.timestamp).toBe(1700000000000);
    expect(snap.nextFundingAt).toBe(1700000000000 + 8 * 3600 * 1000);
  });

  it("handles negative funding rate string", () => {
    const item: BybitFundingHistoryItem = {
      symbol: "ETHUSDT",
      fundingRate: "-0.00025",
      fundingRateTimestamp: "1700000000000",
    };
    const snap = parseFundingHistoryItem(item);
    expect(snap.fundingRate).toBe(-0.00025);
  });
});

// ── parseLinearTicker ───────────────────────────────────────────────────────

describe("parseLinearTicker", () => {
  it("parses ticker fields correctly with explicit timestamp", async () => {
    const { parseLinearTicker } = await import("../../src/lib/funding/ingestion.js");
    const ticker: BybitLinearTicker = {
      symbol: "ETHUSDT",
      fundingRate: "-0.00015",
      nextFundingTime: "1700028800000",
      lastPrice: "3500.50",
    };
    const snap = parseLinearTicker(ticker, 1700000000000);
    expect(snap.symbol).toBe("ETHUSDT");
    expect(snap.fundingRate).toBe(-0.00015);
    expect(snap.nextFundingAt).toBe(1700028800000);
    expect(snap.timestamp).toBe(1700000000000);
  });

  it("uses Date.now() when no timestamp provided", async () => {
    const { parseLinearTicker } = await import("../../src/lib/funding/ingestion.js");
    const ticker: BybitLinearTicker = {
      symbol: "BTCUSDT",
      fundingRate: "0.0001",
      nextFundingTime: "1700028800000",
      lastPrice: "67000",
    };
    const before = Date.now();
    const snap = parseLinearTicker(ticker);
    const after = Date.now();
    expect(snap.timestamp).toBeGreaterThanOrEqual(before);
    expect(snap.timestamp).toBeLessThanOrEqual(after);
  });
});

// ── parseFundingHistory ─────────────────────────────────────────────────────

describe("parseFundingHistory", () => {
  it("returns sorted snapshots by timestamp ascending", () => {
    const items: BybitFundingHistoryItem[] = [
      { symbol: "BTCUSDT", fundingRate: "0.0003", fundingRateTimestamp: "1700003000000" },
      { symbol: "BTCUSDT", fundingRate: "0.0001", fundingRateTimestamp: "1700001000000" },
      { symbol: "BTCUSDT", fundingRate: "0.0002", fundingRateTimestamp: "1700002000000" },
    ];
    const snaps = parseFundingHistory(items);
    expect(snaps).toHaveLength(3);
    expect(snaps[0].timestamp).toBe(1700001000000);
    expect(snaps[1].timestamp).toBe(1700002000000);
    expect(snaps[2].timestamp).toBe(1700003000000);
  });

  it("returns empty for empty input", () => {
    expect(parseFundingHistory([])).toEqual([]);
  });
});

// ── buildSpreadFromTickers ──────────────────────────────────────────────────

describe("buildSpreadFromTickers", () => {
  const perpTicker: BybitLinearTicker = {
    symbol: "BTCUSDT",
    fundingRate: "0.0001",
    nextFundingTime: "1700028800000",
    lastPrice: "67445.00",
  };

  const spotTicker: BybitSpotTicker = {
    symbol: "BTCUSDT",
    lastPrice: "67432.50",
  };

  it("builds a spread snapshot with correct basis", () => {
    const snap = buildSpreadFromTickers(perpTicker, spotTicker, 1700000000000);
    expect(snap).not.toBeNull();
    expect(snap!.symbol).toBe("BTCUSDT");
    expect(snap!.spotPrice).toBe(67432.5);
    expect(snap!.perpPrice).toBe(67445);
    expect(snap!.basisBps).toBeCloseTo(1.854, 2);
    expect(snap!.timestamp).toBe(1700000000000);
  });

  it("returns null for invalid spot price", () => {
    const badSpot: BybitSpotTicker = { symbol: "BTCUSDT", lastPrice: "0" };
    expect(buildSpreadFromTickers(perpTicker, badSpot, 1700000000000)).toBeNull();
  });

  it("returns null for NaN prices", () => {
    const badPerp: BybitLinearTicker = { ...perpTicker, lastPrice: "NaN" };
    expect(buildSpreadFromTickers(badPerp, spotTicker, 1700000000000)).toBeNull();
  });

  it("returns null for empty price strings", () => {
    const badSpot: BybitSpotTicker = { symbol: "BTCUSDT", lastPrice: "" };
    expect(buildSpreadFromTickers(perpTicker, badSpot, 1700000000000)).toBeNull();
  });
});
