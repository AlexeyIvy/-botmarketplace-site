/**
 * 52-T2 — `loadCandleBundle` unit tests.
 *
 * Mocks Prisma's `marketCandle.findMany` and `marketDataset.findUnique` so
 * the loader can be exercised without a database. Covers:
 *
 *  - runtime-mode bundles with `true` placeholders (no dataset lookup);
 *  - runtime-mode bundles with concrete datasetIds (dataset is resolved,
 *    then candles are scoped by `(exchange, symbol, interval, range)`);
 *  - backtest-mode bundles (concrete only; `true` is rejected with a clear
 *    error);
 *  - parallelism — N intervals incur a single round-trip latency, not N;
 *  - the LRU + TTL cache short-circuits a second identical call within the
 *    runtime TTL window;
 *  - the cache key encodes `until` so backtest pins do not collide with
 *    sliding-window runtime queries.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  loadCandleBundle,
  CandleBundleLoadError,
  _resetCandleBundleCache,
} from "../../../src/lib/mtf/loadCandleBundle.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface FakeCandle {
  id: string;
  exchange: string;
  symbol: string;
  interval: "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1";
  openTimeMs: bigint;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  createdAt: Date;
}

function makeCandle(overrides: Partial<FakeCandle>): FakeCandle {
  return {
    id: "c-1",
    exchange: "bybit",
    symbol: "BTCUSDT",
    interval: "M5",
    openTimeMs: 0n,
    open: 100,
    high: 101,
    low: 99,
    close: 100.5,
    volume: 10,
    createdAt: new Date(),
    ...overrides,
  };
}

interface MockPrisma {
  marketCandle: {
    findMany: ReturnType<typeof vi.fn>;
  };
  marketDataset: {
    findUnique: ReturnType<typeof vi.fn>;
  };
}

function makePrisma(): MockPrisma {
  return {
    marketCandle: { findMany: vi.fn() },
    marketDataset: { findUnique: vi.fn() },
  };
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  _resetCandleBundleCache();
});

// ═══════════════════════════════════════════════════════════════════════════
// Runtime mode — `true` placeholders
// ═══════════════════════════════════════════════════════════════════════════

describe("loadCandleBundle / runtime mode", () => {
  it("loads candles for each interval and returns them ASC", async () => {
    const prisma = makePrisma();
    const m5 = [
      makeCandle({ id: "m5-2", openTimeMs: 200n }),
      makeCandle({ id: "m5-1", openTimeMs: 100n }),
    ]; // returned DESC by findMany
    const h1 = [
      makeCandle({ id: "h1-2", interval: "H1", openTimeMs: 7200_000n }),
      makeCandle({ id: "h1-1", interval: "H1", openTimeMs: 3600_000n }),
    ];
    prisma.marketCandle.findMany
      .mockResolvedValueOnce(m5)
      .mockResolvedValueOnce(h1);

    const result = await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: true, H1: true },
      lookbackBars: 100,
      mode: "runtime",
      prismaClient: prisma as never,
    });

    expect(result.size).toBe(2);
    expect(result.get("M5")?.map((c) => c.id)).toEqual(["m5-1", "m5-2"]);
    expect(result.get("H1")?.map((c) => c.id)).toEqual(["h1-1", "h1-2"]);

    // Both queries scoped by (symbol, interval), no datasetId involvement.
    const calls = prisma.marketCandle.findMany.mock.calls;
    expect(calls).toHaveLength(2);
    expect(calls[0][0].where).toMatchObject({ symbol: "BTCUSDT", interval: "M5" });
    expect(calls[0][0].take).toBe(100);
    expect(calls[1][0].where).toMatchObject({ symbol: "BTCUSDT", interval: "H1" });
    expect(prisma.marketDataset.findUnique).not.toHaveBeenCalled();
  });

  it("issues per-interval queries in parallel", async () => {
    const prisma = makePrisma();
    let resolveOne!: () => void;
    let resolveTwo!: () => void;
    const oneStarted = new Promise<void>((r) => (resolveOne = r));
    const twoStarted = new Promise<void>((r) => (resolveTwo = r));

    prisma.marketCandle.findMany.mockImplementationOnce(async () => {
      resolveOne();
      // Wait for the second query to also start before returning — proves
      // the loader did not serialise.
      await twoStarted;
      return [];
    });
    prisma.marketCandle.findMany.mockImplementationOnce(async () => {
      resolveTwo();
      await oneStarted;
      return [];
    });

    await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: true, H1: true },
      lookbackBars: 50,
      mode: "runtime",
      prismaClient: prisma as never,
    });

    expect(prisma.marketCandle.findMany).toHaveBeenCalledTimes(2);
  });

  it("respects `until` upper bound in runtime + true mode", async () => {
    const prisma = makePrisma();
    prisma.marketCandle.findMany.mockResolvedValue([]);

    const until = new Date(1_700_000_000_000);
    await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: true },
      lookbackBars: 25,
      mode: "runtime",
      until,
      prismaClient: prisma as never,
    });

    const where = prisma.marketCandle.findMany.mock.calls[0][0].where;
    expect(where.openTimeMs).toEqual({ lte: BigInt(until.getTime()) });
  });

  it("returns empty arrays without throwing when an interval has no candles", async () => {
    const prisma = makePrisma();
    prisma.marketCandle.findMany.mockResolvedValueOnce([]).mockResolvedValueOnce([]);

    const result = await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: true, H1: true },
      lookbackBars: 25,
      mode: "runtime",
      prismaClient: prisma as never,
    });

    expect(result.get("M5")).toEqual([]);
    expect(result.get("H1")).toEqual([]);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Backtest mode
// ═══════════════════════════════════════════════════════════════════════════

describe("loadCandleBundle / backtest mode", () => {
  it("rejects `true` placeholders", async () => {
    const prisma = makePrisma();
    await expect(
      loadCandleBundle({
        symbol: "BTCUSDT",
        bundle: { M5: true },
        lookbackBars: 100,
        mode: "backtest",
        prismaClient: prisma as never,
      }),
    ).rejects.toBeInstanceOf(CandleBundleLoadError);
    expect(prisma.marketCandle.findMany).not.toHaveBeenCalled();
  });

  it("scopes the candle query to the dataset's range", async () => {
    const prisma = makePrisma();
    prisma.marketDataset.findUnique.mockResolvedValueOnce({
      symbol: "BTCUSDT",
      interval: "M5",
      exchange: "bybit",
      fromTsMs: 1_000n,
      toTsMs: 9_000n,
    });
    prisma.marketCandle.findMany.mockResolvedValueOnce([
      makeCandle({ id: "c2", openTimeMs: 2_000n }),
      makeCandle({ id: "c1", openTimeMs: 1_500n }),
    ]);

    const until = new Date(5_000);
    const result = await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: "ds-1" },
      lookbackBars: 100,
      mode: "backtest",
      until,
      prismaClient: prisma as never,
    });

    expect(prisma.marketDataset.findUnique).toHaveBeenCalledWith({
      where: { id: "ds-1" },
      select: expect.any(Object),
    });
    const where = prisma.marketCandle.findMany.mock.calls[0][0].where;
    expect(where.exchange).toBe("bybit");
    expect(where.symbol).toBe("BTCUSDT");
    expect(where.interval).toBe("M5");
    // until (5_000) < dataset.toTsMs (9_000) ⇒ uses until.
    expect(where.openTimeMs).toEqual({ gte: 1_000n, lte: 5_000n });
    expect(result.get("M5")?.map((c) => c.id)).toEqual(["c1", "c2"]);
  });

  it("falls back to dataset.toTsMs when `until` is not provided", async () => {
    const prisma = makePrisma();
    prisma.marketDataset.findUnique.mockResolvedValueOnce({
      symbol: "BTCUSDT",
      interval: "M5",
      exchange: "bybit",
      fromTsMs: 1_000n,
      toTsMs: 9_000n,
    });
    prisma.marketCandle.findMany.mockResolvedValueOnce([]);

    await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: "ds-1" },
      lookbackBars: 50,
      mode: "backtest",
      prismaClient: prisma as never,
    });

    const where = prisma.marketCandle.findMany.mock.calls[0][0].where;
    expect(where.openTimeMs).toEqual({ gte: 1_000n, lte: 9_000n });
  });

  it("throws when the dataset is missing", async () => {
    const prisma = makePrisma();
    prisma.marketDataset.findUnique.mockResolvedValueOnce(null);

    await expect(
      loadCandleBundle({
        symbol: "BTCUSDT",
        bundle: { M5: "missing" },
        lookbackBars: 25,
        mode: "backtest",
        prismaClient: prisma as never,
      }),
    ).rejects.toThrow(/dataset "missing" not found/);
  });

  it("throws when the dataset symbol/interval mismatches the bundle entry", async () => {
    const prisma = makePrisma();
    prisma.marketDataset.findUnique.mockResolvedValueOnce({
      symbol: "ETHUSDT",
      interval: "M5",
      exchange: "bybit",
      fromTsMs: 0n,
      toTsMs: 0n,
    });

    await expect(
      loadCandleBundle({
        symbol: "BTCUSDT",
        bundle: { M5: "ds-mismatch" },
        lookbackBars: 25,
        mode: "backtest",
        prismaClient: prisma as never,
      }),
    ).rejects.toThrow(/symbol ETHUSDT does not match bundle symbol BTCUSDT/);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Cache
// ═══════════════════════════════════════════════════════════════════════════

describe("loadCandleBundle / cache", () => {
  it("re-uses results across two identical runtime calls", async () => {
    const prisma = makePrisma();
    prisma.marketCandle.findMany.mockResolvedValue([
      makeCandle({ id: "c1", openTimeMs: 100n }),
    ]);

    const args = {
      symbol: "BTCUSDT" as const,
      bundle: { M5: true } as const,
      lookbackBars: 25,
      mode: "runtime" as const,
      prismaClient: prisma as never,
    };
    await loadCandleBundle(args);
    await loadCandleBundle(args);

    expect(prisma.marketCandle.findMany).toHaveBeenCalledTimes(1);
  });

  it("treats different `until` values as distinct cache keys (backtest)", async () => {
    const prisma = makePrisma();
    prisma.marketDataset.findUnique.mockResolvedValue({
      symbol: "BTCUSDT",
      interval: "M5",
      exchange: "bybit",
      fromTsMs: 0n,
      toTsMs: 100_000n,
    });
    prisma.marketCandle.findMany.mockResolvedValue([]);

    await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: "ds-1" },
      lookbackBars: 25,
      mode: "backtest",
      until: new Date(50_000),
      prismaClient: prisma as never,
    });
    await loadCandleBundle({
      symbol: "BTCUSDT",
      bundle: { M5: "ds-1" },
      lookbackBars: 25,
      mode: "backtest",
      until: new Date(60_000),
      prismaClient: prisma as never,
    });

    expect(prisma.marketCandle.findMany).toHaveBeenCalledTimes(2);
  });

  it("re-uses backtest pins on identical args (no TTL)", async () => {
    const prisma = makePrisma();
    prisma.marketDataset.findUnique.mockResolvedValue({
      symbol: "BTCUSDT",
      interval: "M5",
      exchange: "bybit",
      fromTsMs: 0n,
      toTsMs: 100_000n,
    });
    prisma.marketCandle.findMany.mockResolvedValue([]);

    const args = {
      symbol: "BTCUSDT" as const,
      bundle: { M5: "ds-1" } as const,
      lookbackBars: 25,
      mode: "backtest" as const,
      until: new Date(50_000),
      prismaClient: prisma as never,
    };
    await loadCandleBundle(args);
    await loadCandleBundle(args);

    expect(prisma.marketCandle.findMany).toHaveBeenCalledTimes(1);
    expect(prisma.marketDataset.findUnique).toHaveBeenCalledTimes(1);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════════════════

describe("loadCandleBundle / validation", () => {
  it("rejects an empty bundle", async () => {
    const prisma = makePrisma();
    await expect(
      loadCandleBundle({
        symbol: "BTCUSDT",
        bundle: {},
        lookbackBars: 25,
        mode: "runtime",
        prismaClient: prisma as never,
      }),
    ).rejects.toThrow(/bundle is empty/);
  });

  it("rejects non-positive lookbackBars", async () => {
    const prisma = makePrisma();
    await expect(
      loadCandleBundle({
        symbol: "BTCUSDT",
        bundle: { M5: true },
        lookbackBars: 0,
        mode: "runtime",
        prismaClient: prisma as never,
      }),
    ).rejects.toThrow(/lookbackBars/);
  });
});
