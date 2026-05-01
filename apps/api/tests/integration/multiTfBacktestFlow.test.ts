/**
 * 52-T6 — Multi-TF backtest integration tests.
 *
 * Three self-contained suites that prove the bundle-aware backtest path is
 * correct end-to-end at the engine level (no HTTP, no Prisma — those are
 * covered by the route tests in `tests/routes/lab.test.ts`).
 *
 * 1. **Look-ahead structural guard.** When a future HTF bar's close is
 *    perturbed, an MTF indicator resolved at an earlier primary bar MUST NOT
 *    change. This is the closed-bundle invariant from `docs/52-T4 §2`.
 *
 * 2. **Multi-TF backtest e2e via `runBacktestWithBundle`.** Hand-rolled M5+H1
 *    fixture flows through the same code path the lab routes use; reports
 *    are deterministic (same input ⇒ identical output) and the candle count
 *    matches the primary slice exactly.
 *
 * 3. **Backward-compat smoke.** A bundle that contains only the primary
 *    interval — i.e. the user opted in to the bundle API but did not provide
 *    HTF context — produces a report bit-for-bit identical to the legacy
 *    single-TF `runBacktest`.
 *
 * All fixtures are deterministic: no `Math.random`, no `Date.now`, all
 * timestamps anchored to UTC midnight 2026-01-01.
 */

import { describe, it, expect } from "vitest";
import {
  INTERVAL_MS,
  createClosedCandleBundle,
  type MtfCandle,
  type Interval,
} from "../../src/lib/mtf/intervalAlignment.js";
import {
  createMtfCache,
  resolveMtfIndicator,
} from "../../src/lib/mtf/mtfIndicatorResolver.js";
import { runBacktest, runBacktestWithBundle } from "../../src/lib/backtest.js";
import type { CandlesByInterval } from "../../src/lib/mtf/loadCandleBundle.js";
import type { CandleInterval } from "../../src/types/datasetBundle.js";
import type { MarketCandle } from "@prisma/client";

// ---------------------------------------------------------------------------
// Fixtures — deterministic candles
// ---------------------------------------------------------------------------

/** Anchor: 2026-01-01T00:00:00Z. */
const T0 = Date.UTC(2026, 0, 1, 0, 0, 0);

/**
 * 288 M5 candles = 1 day. Close prices follow an alternating up/down ramp
 * so RSI has non-trivial structure (avoids the all-flat / all-NaN trap).
 */
function makeM5Day(): MtfCandle[] {
  return Array.from({ length: 288 }, (_, i) => {
    const direction = i % 2 === 0 ? 1 : -1;
    const close = 100 + direction * (i % 10) * 0.5;
    return {
      openTime: T0 + i * INTERVAL_MS["5m"],
      open: 100,
      high: close + 1,
      low: close - 1,
      close,
      volume: 10,
    };
  });
}

/** 24 H1 candles aligned to the day. */
function makeH1Day(): MtfCandle[] {
  return Array.from({ length: 24 }, (_, i) => ({
    openTime: T0 + i * INTERVAL_MS["1h"],
    open: 1000,
    high: 1010 + i,
    low: 990 - i,
    close: 1000 + (i % 5) * 2,
    volume: 100,
  }));
}

/** Wrap an MtfCandle as a Prisma `MarketCandle` (the only fields the
 *  bundle path actually reads — open/high/low/close/volume + openTimeMs). */
function toRow(c: MtfCandle, interval: CandleInterval): MarketCandle {
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

function makeBundle(input: Partial<Record<CandleInterval, MtfCandle[]>>): CandlesByInterval {
  const out: CandlesByInterval = new Map();
  for (const [interval, candles] of Object.entries(input)) {
    if (!candles) continue;
    out.set(interval as CandleInterval, candles.map((c) => toRow(c, interval as CandleInterval)));
  }
  return out;
}

/** A neutral DSL that never trades — the engine still walks every bar so we
 *  get a meaningful `candles` field and the bundle path is exercised. */
const NEUTRAL_DSL = {
  dslVersion: 1,
  name: "neutral-mtf",
  market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
  entry: { side: "Buy" },
  risk: { maxPositionSizeUsd: 100, riskPerTradePct: 1, cooldownSeconds: 60 },
  execution: { orderType: "Market", clientOrderIdPrefix: "neutral" },
  guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
};

// ═══════════════════════════════════════════════════════════════════════════
// 1. Look-ahead structural guard
// ═══════════════════════════════════════════════════════════════════════════

describe("look-ahead structural guard (closed-bundle invariant)", () => {
  it("perturbing a future HTF bar leaves an earlier MTF indicator value unchanged", () => {
    const m5 = makeM5Day();
    const h1Base = makeH1Day();

    // Pick a primary bar early in the day — say M5_3:30 (i = 42 ⇒ openTime
    // T0 + 42*5min = 3:30Z). At that moment, only H1[0..2] (00:00, 01:00,
    // 02:00) have fully closed; H1[3] (03:00) is still open.
    const primaryIdx = 42;
    const indicatorRef = {
      type: "rsi",
      length: 14,
      sourceTimeframe: "H1" as const,
    };

    // Baseline: resolve via a closed-safe bundle.
    const baseBundle = createClosedCandleBundle("5m" as Interval, {
      "5m": m5,
      "1h": h1Base,
    });
    const baseValues = resolveMtfIndicator(indicatorRef, m5, createMtfCache(), baseBundle);
    const baseValue = baseValues[primaryIdx];

    // Perturb a *future* H1 bar (index 12 — opens at 12:00Z, well after the
    // primary @ 03:30Z). If alignment leaks, the indicator value at the
    // earlier primary bar would change too.
    const h1Perturbed = h1Base.map((c, i) => (i === 12 ? { ...c, close: c.close + 50 } : c));
    const perturbedBundle = createClosedCandleBundle("5m" as Interval, {
      "5m": m5,
      "1h": h1Perturbed,
    });
    const perturbedValues = resolveMtfIndicator(indicatorRef, m5, createMtfCache(), perturbedBundle);

    // Hard equality — the resolution at primaryIdx must be identical.
    expect(perturbedValues[primaryIdx]).toBe(baseValue);
  });

  it("perturbing the *currently open* (containing) HTF bar also leaves earlier values unchanged", () => {
    const m5 = makeM5Day();
    const h1Base = makeH1Day();

    // M5_03:30 sits inside H1_03:00 (idx 3) — that H1 has not closed by
    // 03:30. The closed-safe alignment must therefore use H1_02:00 (idx 2)
    // and changing H1_03:00 must not move the resolved indicator.
    const primaryIdx = 42;
    const ref = { type: "rsi", length: 14, sourceTimeframe: "H1" as const };

    const baseBundle = createClosedCandleBundle("5m" as Interval, { "5m": m5, "1h": h1Base });
    const baseValue = resolveMtfIndicator(ref, m5, createMtfCache(), baseBundle)[primaryIdx];

    const h1Perturbed = h1Base.map((c, i) => (i === 3 ? { ...c, close: c.close - 99 } : c));
    const perturbedBundle = createClosedCandleBundle("5m" as Interval, {
      "5m": m5,
      "1h": h1Perturbed,
    });
    const perturbedValue = resolveMtfIndicator(ref, m5, createMtfCache(), perturbedBundle)[primaryIdx];

    expect(perturbedValue).toBe(baseValue);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 2. Multi-TF backtest e2e via runBacktestWithBundle
// ═══════════════════════════════════════════════════════════════════════════

describe("multi-TF backtest via runBacktestWithBundle", () => {
  it("processes every primary bar and returns a deterministic report", () => {
    const bundle = makeBundle({ M5: makeM5Day(), H1: makeH1Day() });

    const r1 = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    const r2 = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });

    // Determinism — same input ⇒ byte-equal output.
    expect(r1).toEqual(r2);
    expect(r1.candles).toBe(288);
    expect(r1.trades).toBe(0); // neutral DSL never trades
    expect(r1.tradeLog).toEqual([]);
  });

  it("ignores HTF intervals that have no alignment mapping (e.g. M30) without throwing", () => {
    const bundle = makeBundle({
      M5: makeM5Day(),
      H1: makeH1Day(),
      M30: makeM5Day().slice(0, 48), // M30 has no entry in TIMEFRAME_TO_INTERVAL
    });
    const report = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    expect(report.candles).toBe(288);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// 3. Backward-compat with single-TF runBacktest
// ═══════════════════════════════════════════════════════════════════════════

describe("backward-compat with legacy runBacktest", () => {
  it("primary-only bundle reproduces single-TF runBacktest report bit-for-bit", () => {
    const m5 = makeM5Day();
    const bundle = makeBundle({ M5: m5 });

    const fromBundle = runBacktestWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    const fromLegacy = runBacktest(
      m5 as unknown as Parameters<typeof runBacktest>[0],
      NEUTRAL_DSL,
    );

    expect(fromBundle).toEqual(fromLegacy);
  });

  it("DSL without sourceTimeframe behaves identically with or without HTF context", () => {
    // The DSL is single-TF; adding an H1 entry to the bundle must not
    // affect the engine output.
    const m5 = makeM5Day();
    const withHtf = makeBundle({ M5: m5, H1: makeH1Day() });
    const withoutHtf = makeBundle({ M5: m5 });

    const a = runBacktestWithBundle({
      bundle: withHtf,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    const b = runBacktestWithBundle({
      bundle: withoutHtf,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
    });
    expect(a).toEqual(b);
  });
});
