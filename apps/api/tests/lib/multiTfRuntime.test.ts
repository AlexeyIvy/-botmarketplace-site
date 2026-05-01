/**
 * Multi-TF runtime evaluator coverage (docs/52-T3).
 *
 * Pure-function tests around the new {@link RuntimeMtfContext} plumbing in
 * signalEngine + exitEngine + dslEvaluator. The botWorker integration
 * itself is covered indirectly: it composes these primitives and the
 * botWorker.test.ts harness already exercises the surrounding state
 * machine. This file pins the multi-TF semantics:
 *
 *   1. `resolveIndicatorRef` falls through to the single-TF path when the
 *      ref does not declare `sourceTimeframe`.
 *   2. `resolveIndicatorRef` reads from the bundle's context-TF candles
 *      (mapped via the alignment map) when `sourceTimeframe` is set.
 *   3. `resolveIndicatorRef` throws `MtfBundleRequiredError` when a ref
 *      asks for a context TF but no bundle is provided.
 *   4. `signalEngine.evaluateEntry` with a `sideCondition.indicator` carrying
 *      `sourceTimeframe` resolves it through the bundle.
 *   5. `exitEngine.evaluateExit` with `indicatorExit.indicator` carrying
 *      `sourceTimeframe` resolves it through the bundle.
 *   6. The "bundle missing" guard fires from inside `evaluateEntry` /
 *      `evaluateExit` — i.e. is genuinely invoked, not just defined.
 */

import { describe, it, expect } from "vitest";
import {
  resolveIndicatorRef,
  createIndicatorCache,
  MtfBundleRequiredError,
  type DslIndicatorRef,
  type RuntimeMtfContext,
} from "../../src/lib/dslEvaluator.js";
import {
  createCandleBundle,
  type MtfCandle,
  type Interval,
} from "../../src/lib/mtf/intervalAlignment.js";
import { createMtfCache } from "../../src/lib/mtf/mtfIndicatorResolver.js";
import { evaluateEntry } from "../../src/lib/signalEngine.js";
import { evaluateExit, createTrailingStopState } from "../../src/lib/exitEngine.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const M5_MS = 300_000;
const H1_MS = 3_600_000;

/** Build a 12-hour M5 series (144 bars) with a gentle uptrend on close. */
function makeM5(): MtfCandle[] {
  const out: MtfCandle[] = [];
  const t0 = Date.UTC(2026, 0, 1, 0, 0, 0);
  for (let i = 0; i < 144; i++) {
    const close = 100 + i * 0.1;
    out.push({
      openTime: t0 + i * M5_MS,
      open: close - 0.05,
      high: close + 0.1,
      low: close - 0.1,
      close,
      volume: 10,
    });
  }
  return out;
}

/** Build the matching 12 H1 bars; close steps in 1.0 increments per hour. */
function makeH1(): MtfCandle[] {
  const out: MtfCandle[] = [];
  const t0 = Date.UTC(2026, 0, 1, 0, 0, 0);
  for (let i = 0; i < 12; i++) {
    const close = 50 + i; // 50, 51, ..., 61
    out.push({
      openTime: t0 + i * H1_MS,
      open: close - 0.5,
      high: close + 0.5,
      low: close - 0.5,
      close,
      volume: 100,
    });
  }
  return out;
}

function makeRuntimeMtfContext(): RuntimeMtfContext {
  const bundle = createCandleBundle("5m" as Interval, {
    "5m": makeM5(),
    "1h": makeH1(),
  });
  return { bundle, mtfCache: createMtfCache() };
}

// ---------------------------------------------------------------------------
// 1. resolveIndicatorRef behavioural matrix
// ---------------------------------------------------------------------------

describe("resolveIndicatorRef (52-T3)", () => {
  it("uses the primary candle path when no sourceTimeframe is set", () => {
    const candles = makeM5();
    const cache = createIndicatorCache();
    const ref: DslIndicatorRef = { type: "sma", length: 14 };

    const values = resolveIndicatorRef(ref, candles, cache);
    expect(values).toHaveLength(candles.length);
    // First (length - 1) entries are null while the SMA window is filling.
    expect(values[0]).toBeNull();
    expect(values[12]).toBeNull();
    expect(values[13]).not.toBeNull();
  });

  it("resolves through the bundle's context TF when sourceTimeframe is set", () => {
    const ctx = makeRuntimeMtfContext();
    const ref: DslIndicatorRef = { type: "sma", length: 3, sourceTimeframe: "1h" };
    const cache = createIndicatorCache();

    const values = resolveIndicatorRef(ref, ctx.bundle.candles["5m"], cache, ctx);
    expect(values).toHaveLength(ctx.bundle.candles["5m"].length);

    // The H1 SMA(3) at primary bar i = 35 (M5 02:55Z, contained in H1 02:00Z)
    // should equal the H1 SMA(3) at H1 idx 2: avg(50, 51, 52) = 51.
    expect(values[35]).toBeCloseTo(51, 5);
  });

  it("throws MtfBundleRequiredError when sourceTimeframe is set but no bundle", () => {
    const ref: DslIndicatorRef = { type: "rsi", length: 14, sourceTimeframe: "H1" };
    const candles = makeM5();
    const cache = createIndicatorCache();

    expect(() => resolveIndicatorRef(ref, candles, cache)).toThrow(MtfBundleRequiredError);
    expect(() => resolveIndicatorRef(ref, candles, cache, null)).toThrow(MtfBundleRequiredError);
  });

  it("MtfBundleRequiredError carries the offending ref metadata", () => {
    const ref: DslIndicatorRef = { type: "rsi", length: 14, sourceTimeframe: "H1" };
    const candles = makeM5();
    const cache = createIndicatorCache();

    try {
      resolveIndicatorRef(ref, candles, cache);
      expect.fail("expected MtfBundleRequiredError");
    } catch (err) {
      expect(err).toBeInstanceOf(MtfBundleRequiredError);
      const e = err as MtfBundleRequiredError;
      expect(e.indicatorType).toBe("rsi");
      expect(e.sourceTimeframe).toBe("H1");
    }
  });
});

// ---------------------------------------------------------------------------
// 2. signalEngine.evaluateEntry with a context-TF sideCondition
// ---------------------------------------------------------------------------

describe("signalEngine.evaluateEntry — multi-TF sideCondition (52-T3)", () => {
  /** A DSL with a `sideCondition` whose indicator lives on H1. */
  function mtfSideConditionDsl() {
    return {
      id: "mtf-side",
      name: "MTF side condition",
      dslVersion: 2,
      enabled: true,
      market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
      entry: {
        sideCondition: {
          indicator: { type: "sma", length: 3, sourceTimeframe: "1h" },
          source: "close",
          mode: "price_vs_indicator",
          long: { op: ">" },
          short: { op: "<" },
        },
        signal: {
          // A trivially-true compare so the side decides the outcome.
          type: "compare",
          left: { blockType: "sma", length: 3 },
          right: { blockType: "sma", length: 3 },
          op: ">=",
        },
        stopLoss: { type: "fixed_pct", value: 1 },
        takeProfit: { type: "fixed_pct", value: 2 },
      },
      risk: { maxPositionSizeUsd: 100, riskPerTradePct: 1, cooldownSeconds: 0 },
      execution: { orderType: "Market", clientOrderIdPrefix: "t_" },
      guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
    };
  }

  it("resolves the H1 indicator via bundle and produces a long signal", () => {
    const ctx = makeRuntimeMtfContext();
    // Primary close at the latest M5 bar is ~114.3, H1 SMA(3) ≈ 60 — so
    // close > SMA => long.
    const signal = evaluateEntry({
      candles: ctx.bundle.candles["5m"],
      dslJson: mtfSideConditionDsl(),
      position: null,
      mtfContext: ctx,
    });
    expect(signal).not.toBeNull();
    expect(signal!.side).toBe("long");
  });

  it("throws MtfBundleRequiredError when the bundle is missing", () => {
    const m5 = makeM5();
    expect(() => evaluateEntry({
      candles: m5,
      dslJson: mtfSideConditionDsl(),
      position: null,
    })).toThrow(MtfBundleRequiredError);
  });

  it("falls back cleanly when sourceTimeframe is removed", () => {
    const dsl = mtfSideConditionDsl();
    // Strip sourceTimeframe — pure single-TF behaviour, no bundle needed.
    (dsl.entry.sideCondition.indicator as { sourceTimeframe?: string }).sourceTimeframe = undefined;
    const m5 = makeM5();
    const signal = evaluateEntry({
      candles: m5,
      dslJson: dsl,
      position: null,
    });
    // close (~114) > M5 SMA(3) (~114 - small) → long.
    expect(signal?.side).toBe("long");
  });
});

// ---------------------------------------------------------------------------
// 3. exitEngine.evaluateExit with a context-TF indicatorExit
// ---------------------------------------------------------------------------

describe("exitEngine.evaluateExit — multi-TF indicatorExit (52-T3)", () => {
  function mtfIndicatorExitDsl() {
    return {
      id: "mtf-exit",
      name: "MTF indicator exit",
      dslVersion: 2,
      enabled: true,
      market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
      entry: {
        side: "Buy",
        signal: { type: "direct" },
        stopLoss: { type: "fixed_pct", value: 99 },
        takeProfit: { type: "fixed_pct", value: 99 },
      },
      exit: {
        stopLoss: { type: "fixed_pct", value: 99 },
        takeProfit: { type: "fixed_pct", value: 99 },
        indicatorExit: {
          indicator: { type: "sma", length: 3, sourceTimeframe: "1h" },
          condition: { op: ">", value: 55 },
          appliesTo: "both",
        },
      },
      risk: { maxPositionSizeUsd: 100, riskPerTradePct: 1, cooldownSeconds: 0 },
      execution: { orderType: "Market", clientOrderIdPrefix: "t_" },
      guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
    };
  }

  function fakeOpenLongPosition(entryPrice: number): PositionSnapshot {
    return {
      id: "pos_1",
      botRunId: "run_1",
      symbol: "BTCUSDT",
      side: "LONG",
      currentQty: 1,
      avgEntryPrice: entryPrice,
      slPrice: entryPrice * 0.5,
      tpPrice: entryPrice * 2,
      status: "OPEN",
      openedAt: new Date(0),
    } as unknown as PositionSnapshot;
  }

  it("fires the indicator exit when the H1 SMA(3) tail is above the threshold", () => {
    const ctx = makeRuntimeMtfContext();
    // Last M5 maps to the last fully-formed H1 (idx 11 — close 61), SMA(3)
    // tail = avg(59, 60, 61) = 60 > 55 → exit fires.
    const m5 = ctx.bundle.candles["5m"];
    const close = evaluateExit({
      candles: m5,
      dslJson: mtfIndicatorExitDsl(),
      position: fakeOpenLongPosition(110),
      barsHeld: 5,
      trailingState: createTrailingStopState(110),
      mtfContext: ctx,
    });
    expect(close).not.toBeNull();
    expect(close!.reason).toBe("indicator_exit");
  });

  it("throws MtfBundleRequiredError when the bundle is missing", () => {
    const m5 = makeM5();
    expect(() => evaluateExit({
      candles: m5,
      dslJson: mtfIndicatorExitDsl(),
      position: fakeOpenLongPosition(110),
      barsHeld: 5,
      trailingState: createTrailingStopState(110),
    })).toThrow(MtfBundleRequiredError);
  });
});
