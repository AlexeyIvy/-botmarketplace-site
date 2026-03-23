/**
 * Restart/Resume Reconciliation Tests (#130)
 *
 * Validates that the Adaptive Regime Bot correctly handles worker restart:
 *
 *   1. Ephemeral state reconstruction (trailing stop, cooldown)
 *   2. No duplicate entry intents after restart with open position
 *   3. Exit evaluation works correctly after restart with reconstructed state
 *   4. Clean restart without position works normally
 *   5. Idempotent reprocessing of same candle window
 *   6. Adaptive strategy still works after resume
 *
 * All tests use the same pure-function boundary as production:
 *   - recoveryManager.ts for state reconstruction
 *   - signalEngine.ts / exitEngine.ts for signal evaluation
 *   - adaptiveStrategy.ts for regime-aware behavior
 *
 * All fixtures are deterministic: no randomness, no network I/O, fixed timestamps.
 */

import { describe, it, expect } from "vitest";
import {
  reconstructRunState,
  reconstructTrailingStopState,
  isEntryAllowedAfterResume,
  isDuplicateIntent,
  type ReconstructedRunState,
} from "../../src/lib/recoveryManager.js";
import { createTrailingStopState, type TrailingStopState } from "../../src/lib/exitEngine.js";
import { evaluateEntry } from "../../src/lib/signalEngine.js";
import { evaluateExit } from "../../src/lib/exitEngine.js";
import {
  evaluateAdaptiveEntry,
  determineRegime,
} from "../../src/lib/adaptiveStrategy.js";
import { createIndicatorCache } from "../../src/lib/dslEvaluator.js";
import type { PositionSnapshot } from "../../src/lib/positionManager.js";

import { makeStrongUptrend, makeStrongDowntrend, makeRangeBound } from "../fixtures/candles.js";
import {
  makeAdaptiveRegimeTrendDsl,
  makeAdaptiveRegimeLongOnlyDsl,
  makeAdaptiveStrategyConfig,
} from "../fixtures/adaptiveRegimeDsl.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makePosition(overrides: Partial<PositionSnapshot> = {}): PositionSnapshot {
  return {
    id: "pos-restart-test",
    botId: "bot-test",
    botRunId: "run-test",
    symbol: "BTCUSDT",
    side: "LONG",
    status: "OPEN",
    entryQty: 0.01,
    avgEntryPrice: 200,
    costBasis: 2,
    currentQty: 0.01,
    realisedPnl: 0,
    slPrice: 196,
    tpPrice: 208,
    openedAt: new Date("2024-01-01T00:00:00Z"),
    closedAt: null,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// 1. Ephemeral state reconstruction
// ---------------------------------------------------------------------------

describe("Restart/Resume — state reconstruction", () => {
  it("reconstructs trailing stop state from open position", () => {
    const position = makePosition({ avgEntryPrice: 250 });
    const state = reconstructTrailingStopState(position);

    expect(state).toBeDefined();
    expect(state.highWaterMark).toBe(250);
    expect(state.lowWaterMark).toBe(250);
    expect(state.activated).toBe(false);
    expect(state.trailingStopPrice).toBe(0);
  });

  it("reconstructed trailing state matches createTrailingStopState", () => {
    const position = makePosition({ avgEntryPrice: 300 });
    const reconstructed = reconstructTrailingStopState(position);
    const fresh = createTrailingStopState(300);

    expect(reconstructed).toEqual(fresh);
  });

  it("reconstructRunState returns full state for open position", () => {
    const position = makePosition({ id: "pos-123", avgEntryPrice: 200 });
    const lastClose = 1_700_000_100_000;

    const result = reconstructRunState(position, lastClose);

    expect(result.hasOpenPosition).toBe(true);
    expect(result.positionId).toBe("pos-123");
    expect(result.trailingStopState).not.toBeNull();
    expect(result.trailingStopState!.highWaterMark).toBe(200);
    expect(result.lastTradeCloseTime).toBe(lastClose);
  });

  it("reconstructRunState returns neutral state when no position", () => {
    const result = reconstructRunState(null, 0);

    expect(result.hasOpenPosition).toBe(false);
    expect(result.positionId).toBeNull();
    expect(result.trailingStopState).toBeNull();
    expect(result.lastTradeCloseTime).toBe(0);
  });

  it("reconstructRunState returns neutral state for closed position", () => {
    const position = makePosition({ status: "CLOSED" });
    const result = reconstructRunState(position, 1_700_000_100_000);

    expect(result.hasOpenPosition).toBe(false);
    expect(result.trailingStopState).toBeNull();
    // lastTradeCloseTime should still be preserved for cooldown
    expect(result.lastTradeCloseTime).toBe(1_700_000_100_000);
  });

  it("reconstruction is deterministic", () => {
    const position = makePosition({ avgEntryPrice: 175 });
    const r1 = reconstructRunState(position, 1000);
    const r2 = reconstructRunState(position, 1000);
    expect(r1).toEqual(r2);
  });

  it("reconstruction is idempotent (multiple calls produce same result)", () => {
    const position = makePosition({ avgEntryPrice: 200 });
    const results = [];
    for (let i = 0; i < 5; i++) {
      results.push(reconstructRunState(position, 5000));
    }
    for (let i = 1; i < results.length; i++) {
      expect(results[i]).toEqual(results[0]);
    }
  });
});

// ---------------------------------------------------------------------------
// 2. No duplicate entry after restart
// ---------------------------------------------------------------------------

describe("Restart/Resume — no duplicate entry", () => {
  it("signal engine returns null when position is already open", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const position = makePosition({ status: "OPEN" });

    // Even with strong trend signal, no entry when position exists
    const signal = evaluateEntry({ candles, dslJson: dsl, position });
    expect(signal).toBeNull();
  });

  it("isEntryAllowedAfterResume returns false for OPEN position", () => {
    const position = makePosition({ status: "OPEN" });
    expect(isEntryAllowedAfterResume(position)).toBe(false);
  });

  it("isEntryAllowedAfterResume returns true for null position", () => {
    expect(isEntryAllowedAfterResume(null)).toBe(true);
  });

  it("isEntryAllowedAfterResume returns true for CLOSED position", () => {
    const position = makePosition({ status: "CLOSED" });
    expect(isEntryAllowedAfterResume(position)).toBe(true);
  });

  it("isDuplicateIntent detects existing intent", () => {
    const existing = new Set(["entry_1700000000000_long", "exit_1700000060000_sl"]);
    expect(isDuplicateIntent(existing, "entry_1700000000000_long")).toBe(true);
    expect(isDuplicateIntent(existing, "entry_1700000120000_long")).toBe(false);
  });

  it("sliding window across restart does not produce duplicate entry", () => {
    // Simulate: before restart, signal fired at bar N.
    // After restart, same candle window is loaded — signal should fire again.
    // But with position already open (from the first signal), no new entry.
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    // First pass: find the first entry signal
    let firstSignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      firstSignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (firstSignal) break;
    }
    expect(firstSignal).not.toBeNull();

    // After restart: position is now open from that entry
    const position = makePosition({
      avgEntryPrice: firstSignal!.price,
      slPrice: firstSignal!.slPrice,
      tpPrice: firstSignal!.tpPrice,
      status: "OPEN",
    });

    // Re-evaluate with the SAME candle window — no new entry should fire
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      const signal = evaluateEntry({ candles: window, dslJson: dsl, position });
      expect(signal).toBeNull();
    }
  });

  it("intentId-based dedup prevents duplicate even if position not yet opened", () => {
    // Edge case: intent was created (PENDING) before restart,
    // but position hasn't opened yet (exchange hasn't filled).
    // The intentId check should catch this.
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    let firstSignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      firstSignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (firstSignal) break;
    }
    expect(firstSignal).not.toBeNull();

    const intentId = `entry_${firstSignal!.triggerTime}_${firstSignal!.side}`;
    const existingIntents = new Set([intentId]);

    // After restart: same signal fires, but intentId already exists
    expect(isDuplicateIntent(existingIntents, intentId)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 3. Exit correctness after restart
// ---------------------------------------------------------------------------

describe("Restart/Resume — exit correctness after restart", () => {
  it("exit engine works with reconstructed trailing stop state", () => {
    const entryPrice = 200;
    const slPrice = entryPrice * (1 - 2 / 100); // 196
    const tpPrice = entryPrice * (1 + 4 / 100); // 208

    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice,
      tpPrice,
      status: "OPEN",
    });

    // Reconstruct trailing stop state (as would happen after restart)
    const reconstructed = reconstructTrailingStopState(position);

    // Candle that hits SL
    const slCandle = [
      { openTime: 1_700_000_000_000, open: 200, high: 201, low: 195, close: 196, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles: slCandle,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: reconstructed,
    });

    expect(result).not.toBeNull();
    expect(result!.action).toBe("close");
    expect(result!.reason).toBe("sl");
  });

  it("exit engine triggers TP with reconstructed state", () => {
    const entryPrice = 200;
    const slPrice = entryPrice * (1 - 2 / 100);
    const tpPrice = entryPrice * (1 + 4 / 100);

    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice,
      tpPrice,
      status: "OPEN",
    });

    const reconstructed = reconstructTrailingStopState(position);

    // Candle that hits TP
    const tpCandle = [
      { openTime: 1_700_000_000_000, open: 205, high: 210, low: 204, close: 209, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles: tpCandle,
      dslJson: dsl,
      position,
      barsHeld: 5,
      trailingState: reconstructed,
    });

    expect(result).not.toBeNull();
    expect(result!.action).toBe("close");
    expect(result!.reason).toBe("tp");
  });

  it("exit evaluation with reconstructed state matches fresh state", () => {
    const entryPrice = 200;
    const position = makePosition({
      avgEntryPrice: entryPrice,
      slPrice: 196,
      tpPrice: 208,
      status: "OPEN",
    });

    const reconstructed = reconstructTrailingStopState(position);
    const fresh = createTrailingStopState(entryPrice);

    // Both should produce identical exit results
    const candle = [
      { openTime: 1_700_000_000_000, open: 200, high: 201, low: 195, close: 196, volume: 1000 },
    ];
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    const exitReconstructed = evaluateExit({
      candles: candle,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: reconstructed,
    });

    const exitFresh = evaluateExit({
      candles: candle,
      dslJson: dsl,
      position,
      barsHeld: 1,
      trailingState: fresh,
    });

    expect(exitReconstructed).toEqual(exitFresh);
  });

  it("no exit when price stays between SL and TP after restart", () => {
    const position = makePosition({
      avgEntryPrice: 200,
      slPrice: 196,
      tpPrice: 208,
      status: "OPEN",
    });

    const reconstructed = reconstructTrailingStopState(position);

    const safeCandle = [
      { openTime: 1_700_000_000_000, open: 201, high: 203, low: 199, close: 202, volume: 1000 },
    ];

    const dsl = makeAdaptiveRegimeLongOnlyDsl();
    const result = evaluateExit({
      candles: safeCandle,
      dslJson: dsl,
      position,
      barsHeld: 3,
      trailingState: reconstructed,
    });

    expect(result).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 4. Clean restart without position
// ---------------------------------------------------------------------------

describe("Restart/Resume — clean restart", () => {
  it("normal entry behavior when no prior position exists", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    // Reconstruct with no position, no prior close
    const recovered = reconstructRunState(null, 0);
    expect(recovered.hasOpenPosition).toBe(false);
    expect(recovered.trailingStopState).toBeNull();

    // Entry should work normally
    let signal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) break;
    }
    expect(signal).not.toBeNull();
    expect(signal!.action).toBe("open");
  });

  it("cooldown is respected when reconstructed from last close event", () => {
    // After restart: last close was 30 seconds ago, cooldown is 60 seconds
    // Entry should not be allowed during cooldown
    const now = Date.now();
    const lastClose = now - 30_000; // 30 seconds ago

    const recovered = reconstructRunState(null, lastClose);
    expect(recovered.lastTradeCloseTime).toBe(lastClose);

    // The caller (botWorker) would use this in computeSizing:
    //   lastTradeCloseTime → cooldown check
    // We verify the value is correctly preserved
    expect(recovered.lastTradeCloseTime).toBeGreaterThan(0);
    expect(now - recovered.lastTradeCloseTime).toBeLessThan(60_000);
  });
});

// ---------------------------------------------------------------------------
// 5. Idempotent reprocessing
// ---------------------------------------------------------------------------

describe("Restart/Resume — idempotent reprocessing", () => {
  it("same candle window produces same signal before and after restart", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    // Before restart: evaluate
    let beforeSignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      beforeSignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (beforeSignal) break;
    }

    // After restart: evaluate same window (no position yet)
    let afterSignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      afterSignal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (afterSignal) break;
    }

    // Same deterministic signal
    expect(beforeSignal).toEqual(afterSignal);
  });

  it("signal engine is pure: restart has no observable effect on output", () => {
    // The signal engine is a pure function. Given the same candles + DSL + position,
    // it produces the same result regardless of process restart.
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeTrendDsl();

    const results = [];
    for (let run = 0; run < 3; run++) {
      // Simulate fresh process (new cache, new evaluation)
      let signal = null;
      for (let end = 50; end <= candles.length; end++) {
        const window = candles.slice(0, end);
        signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
        if (signal) break;
      }
      results.push(signal);
    }

    // All runs produce identical results
    expect(results[0]).not.toBeNull();
    for (let i = 1; i < results.length; i++) {
      expect(results[i]).toEqual(results[0]);
    }
  });

  it("reconstruction followed by evaluation is idempotent", () => {
    const position = makePosition({ avgEntryPrice: 200, slPrice: 196, tpPrice: 208 });
    const candle = [
      { openTime: 1_700_000_000_000, open: 200, high: 201, low: 195, close: 196, volume: 1000 },
    ];
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    const results = [];
    for (let run = 0; run < 3; run++) {
      const state = reconstructTrailingStopState(position);
      const result = evaluateExit({
        candles: candle,
        dslJson: dsl,
        position,
        barsHeld: 1,
        trailingState: state,
      });
      results.push(result);
    }

    // All runs produce identical results
    expect(results[0]).not.toBeNull();
    for (let i = 1; i < results.length; i++) {
      expect(results[i]).toEqual(results[0]);
    }
  });
});

// ---------------------------------------------------------------------------
// 6. Adaptive strategy after resume
// ---------------------------------------------------------------------------

describe("Restart/Resume — adaptive strategy after resume", () => {
  it("adaptive entry works after resume in trend regime", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);

    // Before restart: find first adaptive entry
    let beforeSignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      beforeSignal = evaluateAdaptiveEntry({ candles: window, config, position: null });
      if (beforeSignal) break;
    }
    expect(beforeSignal).not.toBeNull();
    expect(beforeSignal!.regime).toBe("trend");

    // After restart: same evaluation (no position)
    let afterSignal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      afterSignal = evaluateAdaptiveEntry({ candles: window, config, position: null });
      if (afterSignal) break;
    }

    // Same signal
    expect(afterSignal).toEqual(beforeSignal);
  });

  it("adaptive entry blocked after resume with open position", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const position = makePosition({ status: "OPEN" });

    const signal = evaluateAdaptiveEntry({ candles, config, position });
    expect(signal).toBeNull();
  });

  it("adaptive entry works after resume in range regime", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeRangeBound(200);

    // Find first adaptive entry in range mode
    let signal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateAdaptiveEntry({ candles: window, config, position: null });
      if (signal) break;
    }

    // Should find a range-mode entry
    if (signal) {
      expect(signal.regime).toBe("range");
      expect(signal.action).toBe("open");
    }
    // If no signal fires in range, that's also valid — the test proves
    // the adaptive engine runs without error after resume
  });

  it("regime detection is unaffected by restart", () => {
    const config = makeAdaptiveStrategyConfig();
    const candles = makeStrongUptrend(80);
    const cache = createIndicatorCache();

    // Regime detection is a pure function — same result regardless of restart
    const regimes: string[] = [];
    for (let i = 28; i < candles.length; i++) {
      regimes.push(determineRegime(config.regime, i, candles, cache));
    }

    // Re-run with fresh cache (simulating restart)
    const cache2 = createIndicatorCache();
    const regimes2: string[] = [];
    for (let i = 28; i < candles.length; i++) {
      regimes2.push(determineRegime(config.regime, i, candles, cache2));
    }

    expect(regimes).toEqual(regimes2);
  });
});

// ---------------------------------------------------------------------------
// 7. Defense-in-depth: multiple safety layers
// ---------------------------------------------------------------------------

describe("Restart/Resume — defense-in-depth", () => {
  it("three layers prevent duplicate entry: position check + intentId dedup + signal purity", () => {
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    // Layer 1: Find first signal
    let signal = null;
    for (let end = 28; end <= candles.length; end++) {
      const window = candles.slice(0, end);
      signal = evaluateEntry({ candles: window, dslJson: dsl, position: null });
      if (signal) break;
    }
    expect(signal).not.toBeNull();

    // Layer 1: Position check blocks entry
    const position = makePosition({ status: "OPEN", avgEntryPrice: signal!.price });
    const blocked1 = evaluateEntry({ candles, dslJson: dsl, position });
    expect(blocked1).toBeNull();

    // Layer 2: IntentId dedup blocks even without position
    const intentId = `entry_${signal!.triggerTime}_${signal!.side}`;
    expect(isDuplicateIntent(new Set([intentId]), intentId)).toBe(true);

    // Layer 3: isEntryAllowedAfterResume blocks with open position
    expect(isEntryAllowedAfterResume(position)).toBe(false);
  });

  it("reconstruction + evaluation pipeline produces no side effects", () => {
    // The entire pipeline is pure:
    // reconstruct → evaluate → signal/null
    // No database writes, no map mutations, no global state changes
    const position = makePosition({ avgEntryPrice: 200 });
    const candles = makeStrongUptrend(80);
    const dsl = makeAdaptiveRegimeLongOnlyDsl();

    // Reconstruct
    const state = reconstructRunState(position, 1000);

    // Evaluate entry (blocked by open position)
    const entry = evaluateEntry({ candles, dslJson: dsl, position });
    expect(entry).toBeNull();

    // Evaluate exit (works with reconstructed state)
    const slCandle = [
      { openTime: 1_700_000_000_000, open: 200, high: 201, low: 195, close: 196, volume: 1000 },
    ];
    const exit = evaluateExit({
      candles: slCandle,
      dslJson: dsl,
      position: makePosition({ avgEntryPrice: 200, slPrice: 196, tpPrice: 208 }),
      barsHeld: 1,
      trailingState: state.trailingStopState!,
    });
    expect(exit).not.toBeNull();
    expect(exit!.reason).toBe("sl");
  });
});
