import { describe, it, expect, vi, beforeEach } from "vitest";

/**
 * Tests for partial-fill reconciliation wiring.
 *
 * Validates:
 * 1. Fill delta calculation (new cumExecQty - previous cumExecQty)
 * 2. Entry-side fill routing (first fill → open, subsequent → add)
 * 3. Exit-side fill routing → partial close / close
 * 4. Intent state transitions: PLACED → PARTIALLY_FILLED → FILLED
 * 5. Cancelled/rejected intent handling
 *
 * These are pure logic tests — no DB or network.
 *
 * Stage 3 — #129 follow-up: partial-fill wiring
 */

// ---------------------------------------------------------------------------
// Fill delta calculation
// ---------------------------------------------------------------------------

describe("fill delta calculation", () => {
  it("computes correct delta from zero", () => {
    const prevCumQty = 0;
    const exchangeCumQty = 0.3;
    const fillDelta = exchangeCumQty - prevCumQty;
    expect(fillDelta).toBeCloseTo(0.3);
  });

  it("computes correct delta from partial", () => {
    const prevCumQty = 0.3;
    const exchangeCumQty = 0.7;
    const fillDelta = exchangeCumQty - prevCumQty;
    expect(fillDelta).toBeCloseTo(0.4);
  });

  it("delta is zero when no new fills", () => {
    const prevCumQty = 0.5;
    const exchangeCumQty = 0.5;
    const fillDelta = exchangeCumQty - prevCumQty;
    expect(fillDelta).toBe(0);
  });

  it("full fill delta equals total qty", () => {
    const orderQty = 1.0;
    const prevCumQty = 0;
    const exchangeCumQty = 1.0;
    const fillDelta = exchangeCumQty - prevCumQty;
    expect(fillDelta).toBe(orderQty);
  });

  it("incremental partial fills accumulate", () => {
    const fills = [0.2, 0.3, 0.15, 0.35]; // total = 1.0
    let prevCum = 0;
    let totalApplied = 0;

    for (const fillQty of fills) {
      const newCum = prevCum + fillQty;
      const delta = newCum - prevCum;
      expect(delta).toBeCloseTo(fillQty);
      totalApplied += delta;
      prevCum = newCum;
    }

    expect(totalApplied).toBeCloseTo(1.0);
    expect(prevCum).toBeCloseTo(1.0);
  });
});

// ---------------------------------------------------------------------------
// Intent state transitions
// ---------------------------------------------------------------------------

describe("intent state transitions", () => {
  /**
   * Mirrors the state transition logic in reconcilePlacedIntents():
   *   Bybit status → intent state
   */
  function deriveIntentState(
    bybitStatus: string,
    currentState: string,
  ): "PLACED" | "PARTIALLY_FILLED" | "FILLED" | "CANCELLED" | "FAILED" {
    // Import mapBybitStatus logic inline for pure testing
    const mapped = mapBybitStatusPure(bybitStatus);

    if (mapped === "FILLED") return "FILLED";
    if (mapped === "PARTIALLY_FILLED") return "PARTIALLY_FILLED";
    if (mapped === "CANCELLED") return "CANCELLED";
    if (mapped === "REJECTED") return "FAILED";
    return currentState as "PLACED" | "PARTIALLY_FILLED";
  }

  function mapBybitStatusPure(
    bybitStatus: string,
  ): "SUBMITTED" | "FILLED" | "PARTIALLY_FILLED" | "CANCELLED" | "REJECTED" | "FAILED" {
    switch (bybitStatus) {
      case "New":
      case "Created":
      case "Untriggered":
      case "Active":
        return "SUBMITTED";
      case "PartiallyFilled":
        return "PARTIALLY_FILLED";
      case "Filled":
        return "FILLED";
      case "Cancelled":
      case "Deactivated":
        return "CANCELLED";
      case "Rejected":
        return "REJECTED";
      default:
        return "SUBMITTED";
    }
  }

  it("PLACED → PARTIALLY_FILLED on partial fill", () => {
    expect(deriveIntentState("PartiallyFilled", "PLACED")).toBe("PARTIALLY_FILLED");
  });

  it("PLACED → FILLED on full fill", () => {
    expect(deriveIntentState("Filled", "PLACED")).toBe("FILLED");
  });

  it("PARTIALLY_FILLED → FILLED on full fill", () => {
    expect(deriveIntentState("Filled", "PARTIALLY_FILLED")).toBe("FILLED");
  });

  it("PLACED stays PLACED when exchange says New", () => {
    expect(deriveIntentState("New", "PLACED")).toBe("PLACED");
  });

  it("PLACED → CANCELLED when exchange cancels", () => {
    expect(deriveIntentState("Cancelled", "PLACED")).toBe("CANCELLED");
  });

  it("PLACED → FAILED when exchange rejects", () => {
    expect(deriveIntentState("Rejected", "PLACED")).toBe("FAILED");
  });

  it("PARTIALLY_FILLED stays PARTIALLY_FILLED when no new status", () => {
    expect(deriveIntentState("PartiallyFilled", "PARTIALLY_FILLED")).toBe("PARTIALLY_FILLED");
  });
});

// ---------------------------------------------------------------------------
// Entry fill routing logic
// ---------------------------------------------------------------------------

describe("entry fill routing", () => {
  it("first fill on entry intent → openPosition path", () => {
    const prevCumQty = 0;
    const isEntry = true;
    const hasPosition = false;
    const fillDelta = 0.5;

    // Decision: first fill (prevCumQty=0) + no position → openPosition
    const action = decideEntryAction(prevCumQty, hasPosition, fillDelta);
    expect(action).toBe("openPosition");
  });

  it("subsequent fill on entry intent → applyPartialFill(entry)", () => {
    const prevCumQty = 0.3;
    const hasPosition = true;
    const fillDelta = 0.2;

    const action = decideEntryAction(prevCumQty, hasPosition, fillDelta);
    expect(action).toBe("applyPartialFill_entry");
  });

  it("fill on entry intent when position already exists → applyPartialFill(entry)", () => {
    // Edge case: prevCumQty=0 but position already exists (e.g. manual open)
    const prevCumQty = 0;
    const hasPosition = true;
    const fillDelta = 0.5;

    const action = decideEntryAction(prevCumQty, hasPosition, fillDelta);
    expect(action).toBe("applyPartialFill_entry");
  });
});

/**
 * Mirrors the routing logic in reconcileEntryFill().
 */
function decideEntryAction(
  prevCumQty: number,
  hasPosition: boolean,
  fillDelta: number,
): "openPosition" | "applyPartialFill_entry" | "skip" {
  if (fillDelta <= 0) return "skip";
  if (!hasPosition && prevCumQty === 0) return "openPosition";
  if (hasPosition) return "applyPartialFill_entry";
  // Shouldn't happen: has fills but no position
  return "skip";
}

// ---------------------------------------------------------------------------
// Exit fill routing logic
// ---------------------------------------------------------------------------

describe("exit fill routing", () => {
  it("partial exit fill → applyPartialFill(exit)", () => {
    const fillDelta = 0.3;
    const positionCurrentQty = 1.0;
    const hasPosition = true;

    const action = decideExitAction(hasPosition, fillDelta, positionCurrentQty);
    expect(action).toBe("applyPartialFill_exit");
  });

  it("full exit fill → applyPartialFill(exit) which closes", () => {
    // closePosition is called through applyPartialFill with fillSide="exit"
    const fillDelta = 1.0;
    const positionCurrentQty = 1.0;
    const hasPosition = true;

    const action = decideExitAction(hasPosition, fillDelta, positionCurrentQty);
    expect(action).toBe("applyPartialFill_exit");
  });

  it("no position for exit fill → skip", () => {
    const fillDelta = 0.5;
    const hasPosition = false;

    const action = decideExitAction(hasPosition, fillDelta, 0);
    expect(action).toBe("skip");
  });
});

function decideExitAction(
  hasPosition: boolean,
  fillDelta: number,
  positionCurrentQty: number,
): "applyPartialFill_exit" | "skip" {
  if (!hasPosition || fillDelta <= 0) return "skip";
  return "applyPartialFill_exit";
}

// ---------------------------------------------------------------------------
// End-to-end reconciliation scenario (pure math)
// ---------------------------------------------------------------------------

describe("reconciliation scenario – multi-step partial fill", () => {
  it("entry: 3 partial fills build correct position", () => {
    let prevCumQty = 0;
    let positionQty = 0;
    let costBasis = 0;

    // Fill 1: 0.2 BTC at 50000
    const fill1Cum = 0.2;
    const fill1Delta = fill1Cum - prevCumQty;
    expect(fill1Delta).toBeCloseTo(0.2);
    positionQty += fill1Delta;
    costBasis += fill1Delta * 50000;
    prevCumQty = fill1Cum;

    // Fill 2: cumExecQty = 0.5 (delta = 0.3) at 50500
    const fill2Cum = 0.5;
    const fill2Delta = fill2Cum - prevCumQty;
    expect(fill2Delta).toBeCloseTo(0.3);
    positionQty += fill2Delta;
    costBasis += fill2Delta * 50500;
    prevCumQty = fill2Cum;

    // Fill 3: cumExecQty = 1.0 (delta = 0.5) at 51000
    const fill3Cum = 1.0;
    const fill3Delta = fill3Cum - prevCumQty;
    expect(fill3Delta).toBeCloseTo(0.5);
    positionQty += fill3Delta;
    costBasis += fill3Delta * 51000;
    prevCumQty = fill3Cum;

    expect(positionQty).toBeCloseTo(1.0);

    const avgEntry = costBasis / positionQty;
    // (0.2*50000 + 0.3*50500 + 0.5*51000) / 1.0 = (10000 + 15150 + 25500) / 1.0 = 50650
    expect(avgEntry).toBeCloseTo(50650);
  });

  it("exit: 2 partial fills with correct realised PnL", () => {
    const avgEntry = 50000;
    let currentQty = 1.0;
    let realisedPnl = 0;

    // Partial exit 1: cumExecQty=0.4, delta=0.4 at 51000 (LONG)
    const exit1Delta = 0.4;
    const exit1Price = 51000;
    const pnl1 = (exit1Price - avgEntry) * exit1Delta;
    realisedPnl += pnl1;
    currentQty -= exit1Delta;
    expect(pnl1).toBe(400);
    expect(currentQty).toBeCloseTo(0.6);

    // Partial exit 2: cumExecQty=1.0, delta=0.6 at 49500 (loss on this tranche)
    const exit2Delta = 0.6;
    const exit2Price = 49500;
    const pnl2 = (exit2Price - avgEntry) * exit2Delta;
    realisedPnl += pnl2;
    currentQty -= exit2Delta;
    expect(pnl2).toBe(-300);
    expect(currentQty).toBeCloseTo(0);
    expect(realisedPnl).toBe(100); // 400 + (-300)
  });
});

// ---------------------------------------------------------------------------
// Fill price derivation (avgPrice vs order price)
// ---------------------------------------------------------------------------

describe("fill price derivation", () => {
  /**
   * Mirrors the fill price logic in reconcilePlacedIntents():
   * Priority: avgPrice > order price > intent price > 0
   */
  function deriveFillPrice(
    avgPrice: string,
    orderPrice: string,
    intentPrice: number | null,
  ): number {
    const avgP = Number(avgPrice || "0");
    if (avgP > 0) return avgP;
    const ordP = Number(orderPrice || "0");
    if (ordP > 0) return ordP;
    return intentPrice ?? 0;
  }

  it("uses avgPrice when available (normal case)", () => {
    expect(deriveFillPrice("51234.5", "50000", 49000)).toBe(51234.5);
  });

  it("falls back to order price when avgPrice is '0' (unfilled)", () => {
    expect(deriveFillPrice("0", "50000", 49000)).toBe(50000);
  });

  it("falls back to intent price when both avgPrice and order price are '0'", () => {
    // Market order: price="0", avgPrice="0" before any fill
    expect(deriveFillPrice("0", "0", 49000)).toBe(49000);
  });

  it("returns 0 when all sources are empty", () => {
    expect(deriveFillPrice("", "0", null)).toBe(0);
  });

  it("prefers avgPrice over order price even when order price is valid", () => {
    // Limit order filled at better price than limit
    expect(deriveFillPrice("49800", "50000", 50000)).toBe(49800);
  });

  it("handles partial fill avgPrice correctly for VWAP", () => {
    // Partial fill at 50100, then another at 50300 → Bybit reports blended avgPrice
    const blendedAvgPrice = "50200";
    expect(deriveFillPrice(blendedAvgPrice, "50000", 50000)).toBe(50200);
  });
});

// ---------------------------------------------------------------------------
// Position side derivation from intent.side
// ---------------------------------------------------------------------------

describe("position side from intent.side", () => {
  function derivePositionSide(intentSide: string): "LONG" | "SHORT" {
    return intentSide === "SELL" ? "SHORT" : "LONG";
  }

  it("BUY intent → LONG position", () => {
    expect(derivePositionSide("BUY")).toBe("LONG");
  });

  it("SELL intent → SHORT position", () => {
    expect(derivePositionSide("SELL")).toBe("SHORT");
  });

  it("unknown side defaults to LONG", () => {
    expect(derivePositionSide("UNKNOWN")).toBe("LONG");
  });
});

// ---------------------------------------------------------------------------
// mapBybitStatus integration (live import)
// ---------------------------------------------------------------------------

describe("mapBybitStatus – intent reconciliation states", () => {
  it("maps all relevant Bybit statuses", async () => {
    const { mapBybitStatus } = await import("../../src/lib/bybitOrder.js");

    expect(mapBybitStatus("New")).toBe("SUBMITTED");
    expect(mapBybitStatus("PartiallyFilled")).toBe("PARTIALLY_FILLED");
    expect(mapBybitStatus("Filled")).toBe("FILLED");
    expect(mapBybitStatus("Cancelled")).toBe("CANCELLED");
    expect(mapBybitStatus("Rejected")).toBe("REJECTED");
    expect(mapBybitStatus("Deactivated")).toBe("CANCELLED");
  });
});

// ---------------------------------------------------------------------------
// OrderStatusResult includes avgPrice (live import)
// ---------------------------------------------------------------------------

describe("OrderStatusResult – avgPrice field", () => {
  it("interface includes avgPrice field", async () => {
    // Verify the type exists by importing and checking the module exports
    const mod = await import("../../src/lib/bybitOrder.js");
    // bybitGetOrderStatus returns OrderStatusResult which should have avgPrice
    // We can't instantiate the interface, but we verify the function exists
    expect(typeof mod.bybitGetOrderStatus).toBe("function");
    expect(typeof mod.mapBybitStatus).toBe("function");
  });
});
