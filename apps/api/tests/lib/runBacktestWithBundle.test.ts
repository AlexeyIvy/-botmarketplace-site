/**
 * 52-T4 — `runBacktestWithBundle` smoke tests.
 *
 * Drives the new bundle-aware entry point with deterministic, hand-rolled
 * fixtures. The runtime evaluator already supports MTF via `MtfBacktestContext`
 * (#134); this test focuses on the conversion + look-ahead-safe alignment
 * the new wrapper introduces. Trade-engine semantics (fees, slippage, fillAt)
 * are covered exhaustively by `tests/lib/backtest.test.ts` — we deliberately
 * keep the DSL minimal here so the bundle plumbing is the only signal.
 */

import { describe, it, expect } from "vitest";
import {
  runBacktestWithBundle,
  type BacktestReport,
} from "../../src/lib/backtest.js";
import { INTERVAL_MS, type MtfCandle } from "../../src/lib/mtf/intervalAlignment.js";
import type { CandleInterval } from "../../src/types/datasetBundle.js";
import type { MarketCandle } from "@prisma/client";

// ---------------------------------------------------------------------------
// Fixture helpers
// ---------------------------------------------------------------------------

function toRow(c: MtfCandle, interval: CandleInterval): MarketCandle {
  // The wrapper only reads the numeric / BigInt fields — populate the rest
  // with shape-correct defaults so it satisfies the Prisma type.
  return {
    id: `c-${interval}-${c.openTime}`,
    exchange: "bybit",
    symbol: "BTCUSDT",
    interval,
    openTimeMs: BigInt(c.openTime),
    open: c.open as unknown as MarketCandle["open"],
    high: c.high as unknown as MarketCandle["high"],
    low: c.low as unknown as MarketCandle["low"],
    close: c.close as unknown as MarketCandle["close"],
    volume: c.volume as unknown as MarketCandle["volume"],
    createdAt: new Date(c.openTime),
  };
}

function makeBundle(input: Partial<Record<CandleInterval, MtfCandle[]>>): Map<CandleInterval, MarketCandle[]> {
  const out = new Map<CandleInterval, MarketCandle[]>();
  for (const [interval, candles] of Object.entries(input)) {
    if (!candles) continue;
    out.set(interval as CandleInterval, candles.map((c) => toRow(c, interval as CandleInterval)));
  }
  return out;
}

/** A no-op DSL — never enters, never exits. Just exercises the bundle path. */
const NEUTRAL_DSL = {
  dslVersion: 1,
  name: "neutral",
  market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
  entry: { side: "Buy" },
  risk: { maxPositionSizeUsd: 100, riskPerTradePct: 1, cooldownSeconds: 60 },
  execution: { orderType: "Market", clientOrderIdPrefix: "neutral" },
  guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
};

function makeFlat(interval: CandleInterval, count: number): MtfCandle[] {
  const ms = (() => {
    switch (interval) {
      case "M5": return INTERVAL_MS["5m"];
      case "M15": return INTERVAL_MS["15m"];
      case "M1": return INTERVAL_MS["1m"];
      case "H1": return INTERVAL_MS["1h"];
      case "H4": return INTERVAL_MS["4h"];
      case "D1": return INTERVAL_MS["1d"];
      default: throw new Error(`No alignment mapping for ${interval}`);
    }
  })();
  const start = Date.UTC(2026, 0, 1, 0, 0, 0);
  return Array.from({ length: count }, (_, i) => ({
    openTime: start + i * ms,
    open: 100, high: 101, low: 99, close: 100, volume: 1,
  }));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("runBacktestWithBundle", () => {
  it("runs against a single-TF bundle and reports the candle count", () => {
    const bundle = makeBundle({ M5: makeFlat("M5", 50) });
    const report = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    expect(report.candles).toBe(50);
    expect(report.trades).toBe(0);
  });

  it("matches single-TF runBacktest output for the same primary candles", async () => {
    // When the bundle has one interval (= primary), the wrapper should
    // delegate to runBacktest with no MTF context and produce identical
    // results bit-for-bit.
    const m5 = makeFlat("M5", 30);
    const bundle = makeBundle({ M5: m5 });

    const fromWrapper = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });

    // Hand-call runBacktest with the equivalent Candle[] directly.
    const { runBacktest } = await import("../../src/lib/backtest.js");
    const fromDirect = runBacktest(
      m5 as unknown as Parameters<typeof runBacktest>[0],
      NEUTRAL_DSL,
    );

    expect(fromWrapper).toEqual(fromDirect);
  });

  it("accepts a multi-interval bundle and produces a deterministic report", () => {
    const bundle = makeBundle({
      M5: makeFlat("M5", 24),
      H1: makeFlat("H1", 5),
    });
    const reportA = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    const reportB = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    // Determinism: same input ⇒ same output.
    expect(reportA).toEqual(reportB);
    expect(reportA.candles).toBe(24);
  });

  it("returns an empty report when primary interval has no candles", () => {
    const bundle = makeBundle({ M5: [] });
    const report: BacktestReport = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    expect(report.trades).toBe(0);
    expect(report.candles).toBe(0);
    expect(report.tradeLog).toEqual([]);
  });

  it("throws when the primary interval is absent from the bundle", () => {
    const bundle = makeBundle({ M5: makeFlat("M5", 10) });
    expect(() =>
      runBacktestWithBundle({
        bundle,
        primaryInterval: "H1",
        dslJson: NEUTRAL_DSL,
      }),
    ).toThrow(/primary interval "H1" missing/);
  });

  it("rejects intervals with no alignment mapping (M30 — no '30m' in helper)", () => {
    // The wrapper's primary-interval translation goes through TIMEFRAME_TO_INTERVAL
    // which has no entry for M30; calling with M30 as primary must throw.
    const bundle = makeBundle({ M30: makeFlat("M5", 10).map((c) => ({ ...c })) });
    expect(() =>
      runBacktestWithBundle({
        bundle,
        primaryInterval: "M30",
        dslJson: NEUTRAL_DSL,
      }),
    ).toThrow(/unsupported interval "M30"/);
  });
});
