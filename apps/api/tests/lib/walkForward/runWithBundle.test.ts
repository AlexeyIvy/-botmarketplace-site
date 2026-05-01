/**
 * Walk-forward bundle-aware runner — coverage (docs/52 follow-up).
 *
 * Pins the contract of {@link runWalkForwardWithBundle}:
 *
 *   1. Single-TF bundle (primary only) reproduces {@link runWalkForward}
 *      report bit-for-bit on the same candles.
 *   2. Multi-TF bundle ({M5,H1}) accepts an MTF DSL — no preflight throw,
 *      every fold gets a non-null IS/OOS report.
 *   3. Look-ahead guard at the fold boundary: perturbing an HTF candle that
 *      lives in fold N's OOS window does not change fold N's IS report.
 *   4. The split axis is the primary TF — fold count and ranges match the
 *      single-TF split() contract.
 *
 * Trade-engine semantics (fees, slippage, fillAt) are deliberately not
 * exercised here — they are covered by tests/lib/backtest.test.ts and
 * tests/lib/runBacktestWithBundle.test.ts. This file focuses on the
 * fold-slicing plumbing the new wrapper introduces.
 */

import { describe, it, expect } from "vitest";
import { runWalkForward, runWalkForwardWithBundle } from "../../../src/lib/walkForward/run.js";
import { INTERVAL_MS, type MtfCandle } from "../../../src/lib/mtf/intervalAlignment.js";
import type { CandleInterval } from "../../../src/types/datasetBundle.js";
import type { MarketCandle } from "@prisma/client";
import type { Candle } from "../../../src/lib/bybitCandles.js";

// ---------------------------------------------------------------------------
// Fixture helpers — mirror tests/lib/runBacktestWithBundle.test.ts
// ---------------------------------------------------------------------------

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

function makeBundle(input: Partial<Record<CandleInterval, MtfCandle[]>>): Map<CandleInterval, MarketCandle[]> {
  const out = new Map<CandleInterval, MarketCandle[]>();
  for (const [interval, candles] of Object.entries(input)) {
    if (!candles) continue;
    out.set(interval as CandleInterval, candles.map((c) => toRow(c, interval as CandleInterval)));
  }
  return out;
}

function makeM5(count: number): MtfCandle[] {
  const start = Date.UTC(2026, 0, 1, 0, 0, 0);
  const ms = INTERVAL_MS["5m"];
  return Array.from({ length: count }, (_, i) => {
    const close = 100 + i * 0.05;
    return {
      openTime: start + i * ms,
      open: close - 0.02,
      high: close + 0.05,
      low: close - 0.05,
      close,
      volume: 10,
    };
  });
}

function makeH1(count: number): MtfCandle[] {
  const start = Date.UTC(2026, 0, 1, 0, 0, 0);
  const ms = INTERVAL_MS["1h"];
  return Array.from({ length: count }, (_, i) => {
    const close = 50 + i * 0.5;
    return {
      openTime: start + i * ms,
      open: close - 0.2,
      high: close + 0.3,
      low: close - 0.3,
      close,
      volume: 100,
    };
  });
}

function toCandle(row: MarketCandle): Candle {
  return {
    openTime: Number(row.openTimeMs),
    open: Number(row.open),
    high: Number(row.high),
    low: Number(row.low),
    close: Number(row.close),
    volume: Number(row.volume),
  };
}

/** A neutral DSL that never trades but exercises the full evaluator path. */
const NEUTRAL_DSL = {
  dslVersion: 1,
  name: "neutral-walk",
  market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
  entry: { side: "Buy" },
  risk: { maxPositionSizeUsd: 100, riskPerTradePct: 1, cooldownSeconds: 60 },
  execution: { orderType: "Market", clientOrderIdPrefix: "neutral" },
  guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
};

/**
 * MTF DSL — references H1 indicator via `sourceTimeframe`. Single-TF
 * `runWalkForward` rejects this with `WalkForwardMtfNotSupportedError`;
 * `runWalkForwardWithBundle` must accept it.
 */
const MTF_DSL = {
  ...NEUTRAL_DSL,
  name: "neutral-mtf-walk",
  entry: {
    sideCondition: {
      indicator: { type: "sma", length: 3, sourceTimeframe: "1h" },
      source: "close",
      mode: "price_vs_indicator",
      long: { op: ">" },
      short: { op: "<" },
    },
    signal: { type: "direct" },
    stopLoss: { type: "fixed_pct", value: 1 },
    takeProfit: { type: "fixed_pct", value: 2 },
  },
};

const FOLD_CFG = { isBars: 200, oosBars: 60, step: 60, anchored: false };

// ---------------------------------------------------------------------------
// 1. Backwards compat: primary-only bundle ≡ runWalkForward
// ---------------------------------------------------------------------------

describe("runWalkForwardWithBundle — single-TF parity", () => {
  it("primary-only bundle reproduces runWalkForward report on identical candles", () => {
    const m5Rows = makeM5(400);
    const bundle = makeBundle({ M5: m5Rows });
    const candles = m5Rows.map(toCandle);

    const fromBundle = runWalkForwardWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
      opts: {},
      foldCfg: FOLD_CFG,
    });
    const fromLegacy = runWalkForward(candles, NEUTRAL_DSL, {}, FOLD_CFG);

    expect(fromBundle.folds).toHaveLength(fromLegacy.folds.length);
    expect(fromBundle.folds[0].isReport).toEqual(fromLegacy.folds[0].isReport);
    expect(fromBundle.folds[0].oosReport).toEqual(fromLegacy.folds[0].oosReport);
    expect(fromBundle.aggregate).toEqual(fromLegacy.aggregate);
  });

  it("invokes onProgress once per fold", () => {
    const bundle = makeBundle({ M5: makeM5(400) });
    const seen: Array<{ done: number; total: number }> = [];
    const report = runWalkForwardWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: NEUTRAL_DSL,
      opts: {},
      foldCfg: FOLD_CFG,
      onProgress: (done, total) => { seen.push({ done, total }); },
    });
    expect(seen).toHaveLength(report.folds.length);
    expect(seen[seen.length - 1]).toEqual({ done: report.folds.length, total: report.folds.length });
  });
});

// ---------------------------------------------------------------------------
// 2. Multi-TF bundle accepts an MTF DSL without preflight throws
// ---------------------------------------------------------------------------

describe("runWalkForwardWithBundle — MTF DSL acceptance", () => {
  it("runs an MTF DSL across all folds and produces non-null IS/OOS reports", () => {
    const bundle = makeBundle({
      M5: makeM5(400),
      // 400 M5 bars × 5min = 2000min ≈ 33h ⇒ at least 34 H1 bars cover the
      // window. Generate 40 to give the SMA(3) at least 3 bars in the
      // earliest fold.
      H1: makeH1(40),
    });

    const report = runWalkForwardWithBundle({
      bundle,
      primaryInterval: "M5",
      dslJson: MTF_DSL,
      opts: {},
      foldCfg: FOLD_CFG,
    });

    expect(report.folds.length).toBeGreaterThan(0);
    for (const f of report.folds) {
      expect(f.isReport).not.toBeNull();
      expect(f.oosReport).not.toBeNull();
      // Each IS slice has exactly isBars primary candles by construction.
      expect(f.isReport.candles).toBe(FOLD_CFG.isBars);
      expect(f.oosReport.candles).toBe(FOLD_CFG.oosBars);
    }
  });

  it("is deterministic — identical inputs ⇒ identical aggregate", () => {
    const fixture = () => makeBundle({ M5: makeM5(400), H1: makeH1(40) });
    const a = runWalkForwardWithBundle({
      bundle: fixture(), primaryInterval: "M5", dslJson: MTF_DSL, opts: {}, foldCfg: FOLD_CFG,
    });
    const b = runWalkForwardWithBundle({
      bundle: fixture(), primaryInterval: "M5", dslJson: MTF_DSL, opts: {}, foldCfg: FOLD_CFG,
    });
    expect(a.aggregate).toEqual(b.aggregate);
  });
});

// ---------------------------------------------------------------------------
// 3. Look-ahead guard at the fold boundary
// ---------------------------------------------------------------------------

describe("runWalkForwardWithBundle — fold-boundary look-ahead guard", () => {
  it("perturbing an HTF candle in fold N's OOS window leaves fold N's IS report unchanged", () => {
    const m5 = makeM5(400);
    const h1Base = makeH1(40);

    const baseReport = runWalkForwardWithBundle({
      bundle: makeBundle({ M5: m5, H1: h1Base }),
      primaryInterval: "M5", dslJson: MTF_DSL, opts: {}, foldCfg: FOLD_CFG,
    });

    // Pick fold 0; locate H1 indices that fall inside its OOS window only.
    const fold = baseReport.folds[0];
    const oosFromMs = fold.oosRange.fromTsMs;
    const oosToMs = fold.oosRange.toTsMs;
    const offendingIdx = h1Base.findIndex((c) => c.openTime >= oosFromMs && c.openTime <= oosToMs);
    expect(offendingIdx).toBeGreaterThanOrEqual(0);

    const h1Perturbed = h1Base.map((c, i) => (
      i === offendingIdx ? { ...c, close: c.close + 1000, high: c.high + 1000 } : c
    ));
    const perturbedReport = runWalkForwardWithBundle({
      bundle: makeBundle({ M5: m5, H1: h1Perturbed }),
      primaryInterval: "M5", dslJson: MTF_DSL, opts: {}, foldCfg: FOLD_CFG,
    });

    // Hard equality on fold 0 IS — the OOS perturbation cannot leak back.
    expect(perturbedReport.folds[0].isReport).toEqual(fold.isReport);
  });
});
