import { describe, it, expect } from "vitest";
import {
  evaluateExit,
  generateCloseIntent,
  createTrailingStopState,
  type TrailingStopState,
} from "../../src/lib/exitEngine.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";
import {
  makeUptrend,
  makeDowntrend,
  makeFlat,
  makeFlatThenUp,
  makeFlatThenDown,
} from "../fixtures/candles.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeLongPosition(
  entryPrice = 100,
  qty = 0.01,
  slPrice: number | null = 98,
  tpPrice: number | null = 104,
): PositionSnapshot {
  return {
    id: "pos-long",
    botId: "bot-1",
    botRunId: "run-1",
    symbol: "BTCUSDT",
    side: "LONG",
    status: "OPEN",
    entryQty: qty,
    avgEntryPrice: entryPrice,
    costBasis: qty * entryPrice,
    currentQty: qty,
    realisedPnl: 0,
    slPrice,
    tpPrice,
    openedAt: new Date(1_700_000_000_000),
    closedAt: null,
  };
}

function makeShortPosition(
  entryPrice = 200,
  qty = 0.01,
  slPrice: number | null = 204,
  tpPrice: number | null = 192,
): PositionSnapshot {
  return {
    id: "pos-short",
    botId: "bot-1",
    botRunId: "run-1",
    symbol: "BTCUSDT",
    side: "SHORT",
    status: "OPEN",
    entryQty: qty,
    avgEntryPrice: entryPrice,
    costBasis: qty * entryPrice,
    currentQty: qty,
    realisedPnl: 0,
    slPrice,
    tpPrice,
    openedAt: new Date(1_700_000_000_000),
    closedAt: null,
  };
}

function makeBaseDsl(overrides: Record<string, unknown> = {}) {
  return {
    id: "test-exit",
    name: "Test Exit",
    dslVersion: 2,
    enabled: true,
    market: { exchange: "bybit", env: "demo", category: "linear", symbol: "BTCUSDT" },
    entry: {
      side: "Buy",
      signal: { type: "crossover", fast: { blockType: "SMA", length: 5 }, slow: { blockType: "SMA", length: 20 } },
    },
    exit: {
      stopLoss: { type: "fixed_pct", value: 2 },
      takeProfit: { type: "fixed_pct", value: 4 },
      ...overrides,
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "test_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

// ---------------------------------------------------------------------------
// Stop Loss tests
// ---------------------------------------------------------------------------

describe("exitEngine – stop loss", () => {
  it("triggers long SL when candle low goes below slPrice", () => {
    const position = makeLongPosition(100, 0.01, 98, 104);
    // Create a candle that dips below SL
    const candles = [
      { openTime: 1_700_000_060_000, open: 99, high: 99.5, low: 97.5, close: 98, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(result).not.toBeNull();
    expect(result!.action).toBe("close");
    expect(result!.reason).toBe("sl");
    expect(result!.price).toBe(98);
  });

  it("triggers short SL when candle high goes above slPrice", () => {
    const position = makeShortPosition(200, 0.01, 204, 192);
    const candles = [
      { openTime: 1_700_000_060_000, open: 201, high: 205, low: 200, close: 203, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(200),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("sl");
    expect(result!.price).toBe(204);
  });

  it("does not trigger SL when price stays within range", () => {
    const position = makeLongPosition(100, 0.01, 98, 104);
    const candles = [
      { openTime: 1_700_000_060_000, open: 100, high: 101, low: 99, close: 100.5, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(result).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Take Profit tests
// ---------------------------------------------------------------------------

describe("exitEngine – take profit", () => {
  it("triggers long TP when candle high reaches tpPrice", () => {
    const position = makeLongPosition(100, 0.01, 98, 104);
    const candles = [
      { openTime: 1_700_000_060_000, open: 103, high: 105, low: 102.5, close: 104.5, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("tp");
    expect(result!.price).toBe(104);
  });

  it("triggers short TP when candle low reaches tpPrice", () => {
    const position = makeShortPosition(200, 0.01, 204, 192);
    const candles = [
      { openTime: 1_700_000_060_000, open: 195, high: 196, low: 191, close: 193, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(200),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("tp");
    expect(result!.price).toBe(192);
  });
});

// ---------------------------------------------------------------------------
// Indicator Exit tests
// ---------------------------------------------------------------------------

describe("exitEngine – indicator exit", () => {
  it("triggers indicator exit when RSI > threshold on strong uptrend", () => {
    // 20 flat bars then 80 bars of aggressive +5 step → RSI will be overbought
    const candles = makeFlatThenUp(100, 20, 100, 5);
    // Position opened early in trend with very wide SL/TP so they don't fire first
    const entryPrice = candles[30].close;
    const position = makeLongPosition(
      entryPrice,
      0.01,
      entryPrice * 0.5, // extremely wide SL — will not trigger
      entryPrice * 3.0, // extremely wide TP — will not trigger
    );

    const dsl = makeBaseDsl({
      stopLoss: { type: "fixed_pct", value: 50 },
      takeProfit: { type: "fixed_pct", value: 200 },
      indicatorExit: {
        indicator: { type: "RSI", length: 14 },
        condition: { op: "gt", value: 70 },
        appliesTo: "both",
      },
    });

    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 70,
      trailingState: createTrailingStopState(entryPrice),
    });

    // With 80 consecutive +5 bars, RSI must be well above 70 — assert deterministically
    expect(result).not.toBeNull();
    expect(result!.action).toBe("close");
    expect(result!.reason).toBe("indicator_exit");
    expect(result!.description).toContain("RSI");
  });

  it("respects appliesTo=long filter — does not fire for short position", () => {
    const candles = makeFlatThenUp(100, 20, 100, 5);
    const entryPrice = candles[30].close;
    // Short position with extremely wide SL/TP
    const position = makeShortPosition(entryPrice, 0.01, entryPrice * 2.0, entryPrice * 0.1);

    const dsl = makeBaseDsl({
      stopLoss: { type: "fixed_pct", value: 100 },
      takeProfit: { type: "fixed_pct", value: 90 },
      indicatorExit: {
        indicator: { type: "RSI", length: 14 },
        condition: { op: "gt", value: 70 },
        appliesTo: "long", // only applies to long positions
      },
    });

    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 70,
      trailingState: createTrailingStopState(entryPrice),
    });

    // Indicator exit must NOT fire for a short position with appliesTo=long.
    // SL/TP are wide enough they shouldn't fire either, so result should be null.
    // But even if SL/TP fires, the important thing is it's NOT indicator_exit.
    if (result) {
      expect(result.reason).not.toBe("indicator_exit");
    } else {
      expect(result).toBeNull();
    }
  });

  it("fires indicator exit for short when appliesTo=both", () => {
    // Strong downtrend → RSI will be oversold (< 30)
    const candles = makeFlatThenDown(100, 20, 200, 3);
    const entryPrice = candles[30].close;
    const position = makeShortPosition(entryPrice, 0.01, entryPrice * 2.0, entryPrice * 0.1);

    const dsl = makeBaseDsl({
      stopLoss: { type: "fixed_pct", value: 100 },
      takeProfit: { type: "fixed_pct", value: 90 },
      indicatorExit: {
        indicator: { type: "RSI", length: 14 },
        condition: { op: "lt", value: 30 },
        appliesTo: "both",
      },
    });

    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 70,
      trailingState: createTrailingStopState(entryPrice),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("indicator_exit");
    expect(result!.description).toContain("RSI");
  });
});

// ---------------------------------------------------------------------------
// Time Exit tests
// ---------------------------------------------------------------------------

describe("exitEngine – time exit", () => {
  it("triggers time exit when barsHeld >= maxBarsInPosition", () => {
    const position = makeLongPosition(100, 0.01, 90, 120); // wide SL/TP
    const candles = [
      { openTime: 1_700_000_300_000, open: 101, high: 102, low: 100, close: 101, volume: 1000 },
    ];

    const dsl = makeBaseDsl({
      stopLoss: { type: "fixed_pct", value: 10 },
      takeProfit: { type: "fixed_pct", value: 20 },
      timeExit: { maxBarsInPosition: 5 },
    });

    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 5,
      trailingState: createTrailingStopState(100),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("time_exit");
    expect(result!.price).toBe(101); // close price
  });

  it("does not trigger time exit before maxBarsInPosition", () => {
    const position = makeLongPosition(100, 0.01, 90, 120);
    const candles = [
      { openTime: 1_700_000_300_000, open: 101, high: 102, low: 100, close: 101, volume: 1000 },
    ];

    const dsl = makeBaseDsl({
      stopLoss: { type: "fixed_pct", value: 10 },
      takeProfit: { type: "fixed_pct", value: 20 },
      timeExit: { maxBarsInPosition: 5 },
    });

    const result = evaluateExit({
      candles,
      dslJson: dsl,
      position,
      barsHeld: 3,
      trailingState: createTrailingStopState(100),
    });

    expect(result).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Trailing Stop tests
// ---------------------------------------------------------------------------

describe("exitEngine – trailing stop", () => {
  it("activates and triggers trailing stop on profitable move + pullback", () => {
    const position = makeLongPosition(100, 0.01, 90, 150); // wide SL/TP

    const dsl = makeBaseDsl({
      stopLoss: { type: "fixed_pct", value: 10 },
      takeProfit: { type: "fixed_pct", value: 50 },
      trailingStop: { type: "trailing_pct", activationPct: 2, callbackPct: 1 },
    });

    const trailingState = createTrailingStopState(100);

    // First tick: price rises above activation (100 * 1.02 = 102)
    const tick1 = [
      { openTime: 1_700_000_060_000, open: 101, high: 103, low: 100.5, close: 102.5, volume: 1000 },
    ];
    const r1 = evaluateExit({
      candles: tick1,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState,
    });
    // Should activate but not trigger yet
    expect(trailingState.activated).toBe(true);
    expect(trailingState.highWaterMark).toBe(103);

    // Second tick: price continues up
    const tick2 = [
      { openTime: 1_700_000_120_000, open: 102.5, high: 106, low: 102, close: 105, volume: 1000 },
    ];
    const r2 = evaluateExit({
      candles: tick2,
      dslJson: dsl,
      position,
      barsHeld: 2,
      trailingState,
    });
    expect(trailingState.highWaterMark).toBe(106);
    // Trailing stop at 106 * 0.99 = 104.94

    // Third tick: price drops below trailing stop
    const tick3 = [
      { openTime: 1_700_000_180_000, open: 105, high: 105.5, low: 104, close: 104.2, volume: 1000 },
    ];
    const r3 = evaluateExit({
      candles: tick3,
      dslJson: dsl,
      position,
      barsHeld: 3,
      trailingState,
    });

    expect(r3).not.toBeNull();
    expect(r3!.reason).toBe("trailing_stop");
    expect(r3!.price).toBeCloseTo(106 * 0.99, 2);
  });
});

// ---------------------------------------------------------------------------
// Exit priority tests
// ---------------------------------------------------------------------------

describe("exitEngine – exit priority", () => {
  it("SL has priority over TP (both hit same candle)", () => {
    const position = makeLongPosition(100, 0.01, 98, 104);
    // Candle that hits both SL and TP
    const candles = [
      { openTime: 1_700_000_060_000, open: 100, high: 105, low: 97, close: 101, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("sl"); // SL priority > TP
  });
});

// ---------------------------------------------------------------------------
// Position-aware tests
// ---------------------------------------------------------------------------

describe("exitEngine – position-aware", () => {
  it("returns null for CLOSED position", () => {
    const position = makeLongPosition(100);
    position.status = "CLOSED";

    const candles = [
      { openTime: 1_700_000_060_000, open: 99, high: 99.5, low: 97.5, close: 98, volume: 1000 },
    ];

    const result = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(result).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// generateCloseIntent tests
// ---------------------------------------------------------------------------

describe("exitEngine – generateCloseIntent", () => {
  it("returns close intent with opposite side", () => {
    const position = makeLongPosition(100, 0.01, 98, 104);
    const candles = [
      { openTime: 1_700_000_060_000, open: 99, high: 99.5, low: 97.5, close: 98, volume: 1000 },
    ];

    const result = generateCloseIntent({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(result).not.toBeNull();
    expect(result!.type).toBe("EXIT");
    expect(result!.side).toBe("SELL"); // opposite of LONG
    expect(result!.qty).toBe(0.01);
    expect(result!.intentId).toContain("exit_");
    expect(result!.reason).toBe("sl");
  });

  it("returns BUY side for short position close", () => {
    const position = makeShortPosition(200, 0.01, 204, 192);
    const candles = [
      { openTime: 1_700_000_060_000, open: 201, high: 205, low: 200, close: 203, volume: 1000 },
    ];

    const result = generateCloseIntent({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(200),
    });

    expect(result).not.toBeNull();
    expect(result!.side).toBe("BUY"); // opposite of SHORT
  });
});

// ---------------------------------------------------------------------------
// Determinism tests
// ---------------------------------------------------------------------------

describe("exitEngine – determinism", () => {
  it("same inputs produce same output", () => {
    const position = makeLongPosition(100, 0.01, 98, 104);
    const candles = [
      { openTime: 1_700_000_060_000, open: 99, high: 99.5, low: 97.5, close: 98, volume: 1000 },
    ];

    const a = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });
    const b = evaluateExit({
      candles,
      dslJson: makeBaseDsl(),
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(100),
    });

    expect(a).toEqual(b);
  });
});
