import { describe, it, expect, vi } from "vitest";
import {
  runWalkForward,
  WalkForwardMtfNotSupportedError,
} from "../../../src/lib/walkForward/run.js";
import { runBacktest } from "../../../src/lib/backtest.js";
import { makeFlatThenUp } from "../../fixtures/candles.js";

function makeSmaLongDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    id: "wf-test-sma",
    name: "Walk-forward SMA Long",
    dslVersion: 1,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      side: "Buy",
      signal: {
        type: "crossover",
        fast: { blockType: "SMA", length: fastLen },
        slow: { blockType: "SMA", length: slowLen },
      },
      stopLoss: { type: "fixed_pct", value: slPct },
      takeProfit: { type: "fixed_pct", value: tpPct },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: slPct, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

describe("walkForward.runWalkForward", () => {
  it("smoke: 100 candles + isBars=50/oosBars=10/step=10 → 5 folds with non-empty reports", () => {
    const candles = makeFlatThenUp(100, 25, 100, 2);
    const report = runWalkForward(
      candles,
      makeSmaLongDsl(),
      { feeBps: 0, slippageBps: 0 },
      { isBars: 50, oosBars: 10, step: 10, anchored: false },
    );

    expect(report.folds).toHaveLength(5);
    for (const f of report.folds) {
      // The reports always have these fields, even if no trades fire on a slice.
      expect(f.isReport).toHaveProperty("trades");
      expect(f.oosReport).toHaveProperty("trades");
      expect(f.isReport).toHaveProperty("totalPnlPct");
      expect(f.oosReport).toHaveProperty("totalPnlPct");
    }
  });

  it("does not mutate the input candles or dslJson", () => {
    const candles = makeFlatThenUp(80, 20, 100, 2);
    const dsl = makeSmaLongDsl();
    const candlesBefore = JSON.parse(JSON.stringify(candles));
    const dslBefore = JSON.parse(JSON.stringify(dsl));

    runWalkForward(
      candles,
      dsl,
      { feeBps: 0, slippageBps: 0 },
      { isBars: 30, oosBars: 10, step: 10, anchored: false },
    );

    expect(candles).toEqual(candlesBefore);
    expect(dsl).toEqual(dslBefore);
  });

  it("invokes onProgress once per fold with (done, total)", () => {
    const candles = makeFlatThenUp(100, 25, 100, 2);
    const onProgress = vi.fn();

    runWalkForward(
      candles,
      makeSmaLongDsl(),
      { feeBps: 0, slippageBps: 0 },
      { isBars: 50, oosBars: 10, step: 10, anchored: false },
      onProgress,
    );

    expect(onProgress).toHaveBeenCalledTimes(5);
    expect(onProgress.mock.calls).toEqual([
      [1, 5],
      [2, 5],
      [3, 5],
      [4, 5],
      [5, 5],
    ]);
  });

  it("each fold's reports equal direct runBacktest on the same slice", () => {
    const candles = makeFlatThenUp(100, 25, 100, 2);
    const opts = { feeBps: 0, slippageBps: 0 };
    const cfg = { isBars: 50, oosBars: 10, step: 10, anchored: false } as const;
    const dsl = makeSmaLongDsl();

    const wf = runWalkForward(candles, dsl, opts, cfg);

    // Direct slice — must match runWalkForward's per-fold output bit-for-bit.
    const isSlice0 = candles.slice(0, 50);
    const oosSlice0 = candles.slice(50, 60);
    const directIs = runBacktest(isSlice0, dsl, opts);
    const directOos = runBacktest(oosSlice0, dsl, opts);

    expect(wf.folds[0].isReport).toEqual(directIs);
    expect(wf.folds[0].oosReport).toEqual(directOos);
  });

  it("rejects MTF strategies with WalkForwardMtfNotSupportedError", () => {
    const candles = makeFlatThenUp(80, 20, 100, 2);
    const mtfDsl = {
      ...makeSmaLongDsl(),
      entry: {
        side: "Buy",
        signal: {
          type: "crossover",
          fast: { blockType: "SMA", length: 5, sourceTimeframe: "1h" },
          slow: { blockType: "SMA", length: 20 },
        },
        stopLoss: { type: "fixed_pct", value: 2 },
        takeProfit: { type: "fixed_pct", value: 4 },
      },
    };

    expect(() =>
      runWalkForward(
        candles,
        mtfDsl,
        { feeBps: 0, slippageBps: 0 },
        { isBars: 30, oosBars: 10, step: 10, anchored: false },
      ),
    ).toThrow(WalkForwardMtfNotSupportedError);

    try {
      runWalkForward(
        candles,
        mtfDsl,
        { feeBps: 0, slippageBps: 0 },
        { isBars: 30, oosBars: 10, step: 10, anchored: false },
      );
    } catch (err) {
      expect(err).toBeInstanceOf(WalkForwardMtfNotSupportedError);
      expect((err as Error).message).toContain("MTF-стратегий");
      expect((err as Error).message).toContain("sourceTimeframe='1h'");
    }
  });

  it("anchored layout produces growing IS reports", () => {
    const candles = makeFlatThenUp(100, 25, 100, 2);
    const wf = runWalkForward(
      candles,
      makeSmaLongDsl(),
      { feeBps: 0, slippageBps: 0 },
      { isBars: 50, oosBars: 10, step: 10, anchored: true },
    );

    expect(wf.folds).toHaveLength(5);
    // Anchored: isReport.candles should grow by step each fold.
    expect(wf.folds.map((f) => f.isReport.candles)).toEqual([50, 60, 70, 80, 90]);
    // OOS length stays constant.
    expect(wf.folds.map((f) => f.oosReport.candles)).toEqual([10, 10, 10, 10, 10]);
  });
});
