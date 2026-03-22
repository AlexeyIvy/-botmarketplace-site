/**
 * Replay-style integration test: runs a fixed candle stream through
 * signalEngine → entry → exitEngine → close, verifying the full
 * runtime intent sequence matches expected behavior.
 */
import { describe, it, expect } from "vitest";
import { evaluateEntry } from "../../src/lib/signalEngine.js";
import { evaluateExit, createTrailingStopState } from "../../src/lib/exitEngine.js";
import { computeSizing } from "../../src/lib/riskManager.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";
import { makeFlatThenUp } from "../fixtures/candles.js";

function makeLongDsl() {
  return {
    id: "replay-test",
    name: "Replay SMA Long",
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
    },
    risk: { maxPositionSizeUsd: 100, riskPerTradePct: 2, cooldownSeconds: 0 },
    execution: { orderType: "Market", clientOrderIdPrefix: "replay_" },
    guards: { maxOpenPositions: 1, maxOrdersPerMinute: 10, pauseOnError: true },
  };
}

describe("runtime replay – entry then exit over fixed candle stream", () => {
  it("produces ENTRY intent on crossover, then EXIT intent on TP hit", () => {
    const dsl = makeLongDsl();
    const allCandles = makeFlatThenUp(120, 25, 100, 2);

    // Phase 1: find entry signal by sliding window
    let entrySignal: ReturnType<typeof evaluateEntry> = null;
    let entryIdx = -1;
    for (let end = 22; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      entrySignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (entrySignal) {
        entryIdx = end - 1;
        break;
      }
    }

    expect(entrySignal).not.toBeNull();
    expect(entrySignal!.action).toBe("open");
    expect(entrySignal!.side).toBe("long");
    expect(entryIdx).toBeGreaterThan(20);

    // Phase 1b: risk manager confirms eligibility
    const sizing = computeSizing({
      dslJson: dsl,
      currentPrice: entrySignal!.price,
      hasOpenPosition: false,
      lastTradeCloseTime: 0,
      now: allCandles[entryIdx].openTime,
    });
    expect(sizing.eligible).toBe(true);
    expect(sizing.qty).toBeGreaterThan(0);

    // Phase 2: simulate position and run exit engine on subsequent candles
    const position: PositionSnapshot = {
      id: "pos-replay",
      botId: "bot-1",
      botRunId: "run-1",
      symbol: "BTCUSDT",
      side: "LONG",
      status: "OPEN",
      entryQty: sizing.qty,
      avgEntryPrice: entrySignal!.price,
      costBasis: sizing.qty * entrySignal!.price,
      currentQty: sizing.qty,
      realisedPnl: 0,
      slPrice: entrySignal!.slPrice,
      tpPrice: entrySignal!.tpPrice,
      openedAt: new Date(allCandles[entryIdx].openTime),
      closedAt: null,
    };

    const trailingState = createTrailingStopState(entrySignal!.price);
    let exitSignal: ReturnType<typeof evaluateExit> = null;
    let barsHeld = 0;

    for (let j = entryIdx + 1; j < allCandles.length; j++) {
      barsHeld++;
      const exitCandles = [allCandles[j]]; // single-candle tick
      exitSignal = evaluateExit({
        candles: exitCandles,
        dslJson: dsl,
        position,
        barsHeld,
        trailingState,
      });
      if (exitSignal) break;
    }

    // With a +2/bar uptrend and 4% TP, TP must eventually be hit
    expect(exitSignal).not.toBeNull();
    expect(exitSignal!.action).toBe("close");
    // Could be TP since price keeps rising; SL is below entry
    expect(exitSignal!.reason).toBe("tp");
    expect(exitSignal!.price).toBe(position.tpPrice);
    expect(barsHeld).toBeGreaterThan(0);
  });

  it("produces EXIT intent on SL hit when price reverses", () => {
    const dsl = makeLongDsl();
    // Flat → up → we'll manually create a reversal after entry
    const allCandles = makeFlatThenUp(60, 25, 100, 2);

    // Find entry
    let entrySignal: ReturnType<typeof evaluateEntry> = null;
    let entryIdx = -1;
    for (let end = 22; end <= allCandles.length; end++) {
      const window = allCandles.slice(0, end);
      entrySignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (entrySignal) {
        entryIdx = end - 1;
        break;
      }
    }
    expect(entrySignal).not.toBeNull();

    const entryPrice = entrySignal!.price;
    const slPrice = entrySignal!.slPrice;

    // Create crash candles that drop below SL
    const crashCandle = {
      openTime: allCandles[entryIdx].openTime + 60_000,
      open: entryPrice,
      high: entryPrice + 0.5,
      low: slPrice - 1, // goes below SL
      close: slPrice - 0.5,
      volume: 1000,
    };

    const position: PositionSnapshot = {
      id: "pos-replay-sl",
      botId: "bot-1",
      botRunId: "run-1",
      symbol: "BTCUSDT",
      side: "LONG",
      status: "OPEN",
      entryQty: 0.01,
      avgEntryPrice: entryPrice,
      costBasis: 0.01 * entryPrice,
      currentQty: 0.01,
      realisedPnl: 0,
      slPrice,
      tpPrice: entrySignal!.tpPrice,
      openedAt: new Date(allCandles[entryIdx].openTime),
      closedAt: null,
    };

    const result = evaluateExit({
      candles: [crashCandle],
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: createTrailingStopState(entryPrice),
    });

    expect(result).not.toBeNull();
    expect(result!.reason).toBe("sl");
    expect(result!.price).toBe(slPrice);
  });
});
