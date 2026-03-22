import { describe, it, expect } from "vitest";
import { evaluateEntry, generateOpenIntent } from "../../src/lib/signalEngine.js";
import { evaluateExit, createTrailingStopState } from "../../src/lib/exitEngine.js";
import { runDslBacktest } from "../../src/lib/dslEvaluator.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";
import {
  makeUptrend,
  makeDowntrend,
  makeFlat,
  makeFlatThenUp,
  makeFlatThenDown,
} from "../fixtures/candles.js";

// ---------------------------------------------------------------------------
// DSL fixtures — reusing patterns from dslEvaluator.test.ts
// ---------------------------------------------------------------------------

function makeSmaLongDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    id: "test-sma-long",
    name: "SMA Crossover Long",
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

function makeSmaShortDsl(fastLen = 5, slowLen = 20, slPct = 2, tpPct = 4) {
  return {
    ...makeSmaLongDsl(fastLen, slowLen, slPct, tpPct),
    id: "test-sma-short",
    entry: {
      side: "Sell",
      signal: {
        type: "crossunder",
        fast: { blockType: "SMA", length: fastLen },
        slow: { blockType: "SMA", length: slowLen },
      },
      stopLoss: { type: "fixed_pct", value: slPct },
      takeProfit: { type: "fixed_pct", value: tpPct },
    },
  };
}

function makeDualSideDsl() {
  return {
    id: "test-dual-side",
    name: "EMA Dual Side",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      sideCondition: {
        indicator: { type: "EMA", length: 20 },
        long: { op: "gt" },
        short: { op: "lt" },
      },
      signal: {
        type: "crossover",
        fast: { blockType: "SMA", length: 5 },
        slow: { blockType: "SMA", length: 10 },
      },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 2 },
      takeProfit: { type: "fixed_pct", value: 4 },
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

function makeOpenPosition(): PositionSnapshot {
  return {
    id: "pos-1",
    botId: "bot-1",
    botRunId: "run-1",
    symbol: "BTCUSDT",
    side: "LONG",
    status: "OPEN",
    entryQty: 0.01,
    avgEntryPrice: 100,
    costBasis: 1,
    currentQty: 0.01,
    realisedPnl: 0,
    slPrice: 98,
    tpPrice: 104,
    openedAt: new Date(),
    closedAt: null,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("signalEngine – evaluateEntry", () => {
  it("returns null for insufficient candles", () => {
    const candles = makeUptrend(1);
    const result = evaluateEntry({ candles, dslJson: makeSmaLongDsl(), position: null });
    expect(result).toBeNull();
  });

  it("returns null when position is already open", () => {
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const result = evaluateEntry({
      candles,
      dslJson: makeSmaLongDsl(),
      position: makeOpenPosition(),
    });
    expect(result).toBeNull();
  });

  it("returns null on flat market (no crossover)", () => {
    const candles = makeFlat(80, 100);
    const result = evaluateEntry({ candles, dslJson: makeSmaLongDsl(), position: null });
    expect(result).toBeNull();
  });

  it("returns long signal on flat-then-up data when crossover fires", () => {
    // We need to find a candle window where crossover happens on the last bar.
    // Evaluate across sliding windows to find one that fires.
    const allCandles = makeFlatThenUp(80, 25, 100, 2);
    let foundSignal = false;

    for (let end = 22; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      const result = evaluateEntry({ candles: window, dslJson: makeSmaLongDsl(), position: null });
      if (result) {
        expect(result.action).toBe("open");
        expect(result.side).toBe("long");
        expect(result.price).toBeGreaterThan(0);
        expect(result.slPrice).toBeLessThan(result.price);
        expect(result.tpPrice).toBeGreaterThan(result.price);
        expect(result.signalType).toBe("crossover");
        expect(result.triggerTime).toBeGreaterThan(0);
        expect(result.reason).toContain("long");
        foundSignal = true;
        break;
      }
    }

    expect(foundSignal).toBe(true);
  });

  it("returns short signal on flat-then-down data when crossunder fires", () => {
    const allCandles = makeFlatThenDown(80, 25, 200, 2);
    let foundSignal = false;

    for (let end = 22; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      const result = evaluateEntry({
        candles: window,
        dslJson: makeSmaShortDsl(),
        position: null,
      });
      if (result) {
        expect(result.action).toBe("open");
        expect(result.side).toBe("short");
        expect(result.price).toBeGreaterThan(0);
        expect(result.slPrice).toBeGreaterThan(result.price);
        expect(result.tpPrice).toBeLessThan(result.price);
        expect(result.signalType).toBe("crossunder");
        foundSignal = true;
        break;
      }
    }

    expect(foundSignal).toBe(true);
  });

  it("does not throw on dual-side DSL with sideCondition", () => {
    const allCandles = makeFlatThenUp(80, 15, 100, 2);

    // Evaluate across all windows — must never throw
    for (let end = 15; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      const result = evaluateEntry({ candles: window, dslJson: makeDualSideDsl(), position: null });
      if (result) {
        expect(result.action).toBe("open");
        expect(["long", "short"]).toContain(result.side);
        expect(result.price).toBeGreaterThan(0);
        return; // signal found and validated — pass
      }
    }

    // If no signal fires across all windows, that's still a valid outcome
    // for this particular data shape. The test ensures no runtime errors.
  });

  it("is deterministic: same input produces same output", () => {
    const allCandles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl();

    // Find a window that produces a signal
    for (let end = 22; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      const a = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      const b = evaluateEntry({ candles: window, dslJson: dsl, position: null });

      if (a && b) {
        expect(a).toEqual(b);
        return;
      }
      expect(a).toEqual(b); // both null is also deterministic
    }
  });
});

describe("signalEngine – generateOpenIntent", () => {
  it("returns null when no signal fires", () => {
    const candles = makeFlat(80, 100);
    const result = generateOpenIntent(
      { candles, dslJson: makeSmaLongDsl(), position: null },
      { botRunId: "run-1", symbol: "BTCUSDT", sizingQty: 0.01 },
    );
    expect(result).toBeNull();
  });

  it("returns a BotIntent-compatible descriptor when signal fires", () => {
    const allCandles = makeFlatThenUp(80, 25, 100, 2);

    for (let end = 22; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      const result = generateOpenIntent(
        { candles: window, dslJson: makeSmaLongDsl(), position: null },
        { botRunId: "run-1", symbol: "BTCUSDT", sizingQty: 0.01 },
      );
      if (result) {
        expect(result.type).toBe("ENTRY");
        expect(result.side).toBe("BUY");
        expect(result.qty).toBe(0.01);
        expect(result.price).toBeGreaterThan(0);
        expect(result.slPrice).toBeLessThan(result.price);
        expect(result.tpPrice).toBeGreaterThan(result.price);
        expect(result.intentId).toContain("entry_");
        expect(result.reason).toBeTruthy();
        return;
      }
    }
  });
});

describe("signalEngine – parity with backtest evaluator", () => {
  it("signal fires at the same candle index as backtest entry", () => {
    // Both use the same evaluateSignal + determineSide primitives,
    // so signals should fire on the same candle given the same data.
    const candles = makeFlatThenUp(80, 25, 100, 2);
    const dsl = makeSmaLongDsl();

    const backtestReport = runDslBacktest(candles, dsl);
    if (backtestReport.trades === 0) return;

    const firstTradeEntry = backtestReport.tradeLog[0];

    // Find which candle window produces a signal from signalEngine
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) {
        // Signal should fire at the same time as backtest's first entry
        expect(signal.triggerTime).toBe(firstTradeEntry.entryTime);
        expect(signal.side).toBe(firstTradeEntry.side);
        break;
      }
    }
  });
});

// ---------------------------------------------------------------------------
// Replay sequence test: fixed candle stream → deterministic intent sequence
// ---------------------------------------------------------------------------

describe("signalEngine + exitEngine – replay sequence", () => {
  it("produces deterministic entry→exit sequence over a fixed candle stream", () => {
    const dsl = makeSmaLongDsl(5, 20, 2, 4);
    // 25 flat bars then strong uptrend — guarantees SMA crossover entry
    const candles = makeFlatThenUp(80, 25, 100, 2);

    type Intent = { type: "ENTRY" | "EXIT"; bar: number; side: string; price: number; reason?: string };
    const intents: Intent[] = [];

    let inPosition = false;
    let entryPrice = 0;
    let slPrice = 0;
    let tpPrice = 0;
    let entryBar = 0;

    // Simulate tick-by-tick evaluation
    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const currentCandle = candles[end - 1];

      if (!inPosition) {
        const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
        if (signal) {
          intents.push({
            type: "ENTRY",
            bar: end - 1,
            side: signal.side,
            price: signal.price,
            reason: signal.signalType,
          });
          inPosition = true;
          entryPrice = signal.price;
          slPrice = signal.slPrice;
          tpPrice = signal.tpPrice;
          entryBar = end - 1;
        }
      } else {
        const position = {
          id: "replay-pos",
          botId: "bot-1",
          botRunId: "run-1",
          symbol: "BTCUSDT",
          side: "LONG" as const,
          status: "OPEN" as const,
          entryQty: 0.01,
          avgEntryPrice: entryPrice,
          costBasis: 0.01 * entryPrice,
          currentQty: 0.01,
          realisedPnl: 0,
          slPrice,
          tpPrice,
          openedAt: new Date(candles[entryBar].openTime),
          closedAt: null,
        };
        const barsHeld = end - 1 - entryBar;
        const trailingState = createTrailingStopState(entryPrice);

        const exitSignal = evaluateExit({
          candles: window,
          dslJson: dsl,
          position,
          barsHeld,
          trailingState,
        });

        if (exitSignal) {
          intents.push({
            type: "EXIT",
            bar: end - 1,
            side: exitSignal.side,
            price: exitSignal.price,
            reason: exitSignal.reason,
          });
          inPosition = false;
        }
      }
    }

    // Must have at least one entry
    expect(intents.length).toBeGreaterThanOrEqual(1);
    expect(intents[0].type).toBe("ENTRY");

    // If we got an exit, it must come after entry
    if (intents.length >= 2) {
      expect(intents[1].type).toBe("EXIT");
      expect(intents[1].bar).toBeGreaterThan(intents[0].bar);
    }

    // Replay determinism: run the exact same loop again
    const intents2: Intent[] = [];
    let inPosition2 = false;
    let entryPrice2 = 0;
    let slPrice2 = 0;
    let tpPrice2 = 0;
    let entryBar2 = 0;

    for (let end = 2; end <= candles.length; end++) {
      const window = candles.slice(0, end);

      if (!inPosition2) {
        const signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
        if (signal) {
          intents2.push({
            type: "ENTRY",
            bar: end - 1,
            side: signal.side,
            price: signal.price,
            reason: signal.signalType,
          });
          inPosition2 = true;
          entryPrice2 = signal.price;
          slPrice2 = signal.slPrice;
          tpPrice2 = signal.tpPrice;
          entryBar2 = end - 1;
        }
      } else {
        const position = {
          id: "replay-pos",
          botId: "bot-1",
          botRunId: "run-1",
          symbol: "BTCUSDT",
          side: "LONG" as const,
          status: "OPEN" as const,
          entryQty: 0.01,
          avgEntryPrice: entryPrice2,
          costBasis: 0.01 * entryPrice2,
          currentQty: 0.01,
          realisedPnl: 0,
          slPrice: slPrice2,
          tpPrice: tpPrice2,
          openedAt: new Date(candles[entryBar2].openTime),
          closedAt: null,
        };
        const barsHeld = end - 1 - entryBar2;
        const trailingState = createTrailingStopState(entryPrice2);

        const exitSignal = evaluateExit({
          candles: window,
          dslJson: dsl,
          position,
          barsHeld,
          trailingState,
        });

        if (exitSignal) {
          intents2.push({
            type: "EXIT",
            bar: end - 1,
            side: exitSignal.side,
            price: exitSignal.price,
            reason: exitSignal.reason,
          });
          inPosition2 = false;
        }
      }
    }

    // Identical intent sequences
    expect(intents).toEqual(intents2);
  });
});
