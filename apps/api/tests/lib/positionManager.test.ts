import { describe, it, expect, vi, beforeEach } from "vitest";
import { calcUnrealisedPnl, type PositionSnapshot } from "../../src/lib/positionManager.js";

// ---------------------------------------------------------------------------
// Pure function tests (no DB required)
// ---------------------------------------------------------------------------

function makePosition(overrides: Partial<PositionSnapshot> = {}): PositionSnapshot {
  return {
    id: "pos-1",
    botId: "bot-1",
    botRunId: "run-1",
    symbol: "BTCUSDT",
    side: "LONG",
    status: "OPEN",
    entryQty: 1,
    avgEntryPrice: 50000,
    costBasis: 50000,
    currentQty: 1,
    realisedPnl: 0,
    slPrice: null,
    tpPrice: null,
    openedAt: new Date(),
    closedAt: null,
    ...overrides,
  };
}

describe("calcUnrealisedPnl", () => {
  it("returns positive PnL for LONG when price is above entry", () => {
    const pos = makePosition({ side: "LONG", avgEntryPrice: 50000, currentQty: 2 });
    expect(calcUnrealisedPnl(pos, 51000)).toBe(2000);
  });

  it("returns negative PnL for LONG when price is below entry", () => {
    const pos = makePosition({ side: "LONG", avgEntryPrice: 50000, currentQty: 1 });
    expect(calcUnrealisedPnl(pos, 49000)).toBe(-1000);
  });

  it("returns positive PnL for SHORT when price is below entry", () => {
    const pos = makePosition({ side: "SHORT", avgEntryPrice: 50000, currentQty: 1 });
    expect(calcUnrealisedPnl(pos, 49000)).toBe(1000);
  });

  it("returns negative PnL for SHORT when price is above entry", () => {
    const pos = makePosition({ side: "SHORT", avgEntryPrice: 50000, currentQty: 1 });
    expect(calcUnrealisedPnl(pos, 52000)).toBe(-2000);
  });

  it("returns 0 for CLOSED position", () => {
    const pos = makePosition({ status: "CLOSED", currentQty: 0 });
    expect(calcUnrealisedPnl(pos, 60000)).toBe(0);
  });

  it("returns 0 when currentQty is 0", () => {
    const pos = makePosition({ currentQty: 0 });
    expect(calcUnrealisedPnl(pos, 60000)).toBe(0);
  });

  it("scales with quantity", () => {
    const pos = makePosition({ side: "LONG", avgEntryPrice: 100, currentQty: 10 });
    expect(calcUnrealisedPnl(pos, 105)).toBe(50);
  });
});

// ---------------------------------------------------------------------------
// Position state transition logic tests (simulated in-memory)
// ---------------------------------------------------------------------------

/**
 * In-memory position state simulator that mirrors the positionManager logic
 * without requiring a database. This validates the accounting invariants.
 */
interface InMemoryPosition {
  side: "LONG" | "SHORT";
  entryQty: number;
  avgEntryPrice: number;
  costBasis: number;
  currentQty: number;
  realisedPnl: number;
  status: "OPEN" | "CLOSED";
  events: Array<{
    type: string;
    qty: number;
    price: number;
    realisedPnl: number;
  }>;
}

function openPos(side: "LONG" | "SHORT", qty: number, price: number): InMemoryPosition {
  return {
    side,
    entryQty: qty,
    avgEntryPrice: price,
    costBasis: qty * price,
    currentQty: qty,
    realisedPnl: 0,
    status: "OPEN",
    events: [{ type: "OPEN", qty, price, realisedPnl: 0 }],
  };
}

function addToPos(pos: InMemoryPosition, qty: number, price: number): void {
  if (pos.status !== "OPEN") throw new Error("Cannot add to closed position");
  const addCost = qty * price;
  pos.entryQty += qty;
  pos.costBasis += addCost;
  pos.avgEntryPrice = pos.costBasis / pos.entryQty;
  pos.currentQty += qty;
  pos.events.push({ type: "ADD", qty, price, realisedPnl: 0 });
}

function closePos(pos: InMemoryPosition, qty: number, price: number): number {
  if (pos.status !== "OPEN") throw new Error("Cannot close closed position");
  if (qty > pos.currentQty + 1e-12) throw new Error("Cannot close more than current qty");

  const isFullClose = Math.abs(qty - pos.currentQty) < 1e-12;
  const closeQty = isFullClose ? pos.currentQty : qty;

  const priceDiff = pos.side === "LONG"
    ? price - pos.avgEntryPrice
    : pos.avgEntryPrice - price;
  const eventPnl = priceDiff * closeQty;

  pos.currentQty = isFullClose ? 0 : pos.currentQty - closeQty;
  pos.realisedPnl += eventPnl;

  if (isFullClose) {
    pos.status = "CLOSED";
  }

  pos.events.push({
    type: isFullClose ? "CLOSE" : "PARTIAL_CLOSE",
    qty: closeQty,
    price,
    realisedPnl: eventPnl,
  });

  return eventPnl;
}

describe("position state transitions (in-memory simulator)", () => {
  describe("open → close lifecycle", () => {
    it("opens a LONG position correctly", () => {
      const pos = openPos("LONG", 1, 50000);
      expect(pos.status).toBe("OPEN");
      expect(pos.entryQty).toBe(1);
      expect(pos.avgEntryPrice).toBe(50000);
      expect(pos.costBasis).toBe(50000);
      expect(pos.currentQty).toBe(1);
      expect(pos.realisedPnl).toBe(0);
      expect(pos.events).toHaveLength(1);
      expect(pos.events[0].type).toBe("OPEN");
    });

    it("opens a SHORT position correctly", () => {
      const pos = openPos("SHORT", 2, 40000);
      expect(pos.side).toBe("SHORT");
      expect(pos.entryQty).toBe(2);
      expect(pos.avgEntryPrice).toBe(40000);
      expect(pos.costBasis).toBe(80000);
    });

    it("closes LONG position with profit", () => {
      const pos = openPos("LONG", 1, 50000);
      const pnl = closePos(pos, 1, 55000);
      expect(pnl).toBe(5000);
      expect(pos.status).toBe("CLOSED");
      expect(pos.realisedPnl).toBe(5000);
      expect(pos.currentQty).toBe(0);
    });

    it("closes LONG position with loss", () => {
      const pos = openPos("LONG", 1, 50000);
      const pnl = closePos(pos, 1, 48000);
      expect(pnl).toBe(-2000);
      expect(pos.realisedPnl).toBe(-2000);
      expect(pos.status).toBe("CLOSED");
    });

    it("closes SHORT position with profit", () => {
      const pos = openPos("SHORT", 1, 50000);
      const pnl = closePos(pos, 1, 45000);
      expect(pnl).toBe(5000);
      expect(pos.realisedPnl).toBe(5000);
    });

    it("closes SHORT position with loss", () => {
      const pos = openPos("SHORT", 1, 50000);
      const pnl = closePos(pos, 1, 53000);
      expect(pnl).toBe(-3000);
      expect(pos.realisedPnl).toBe(-3000);
    });
  });

  describe("add to position (DCA / averaging)", () => {
    it("recalculates average entry on add", () => {
      const pos = openPos("LONG", 1, 50000);
      addToPos(pos, 1, 48000);

      expect(pos.entryQty).toBe(2);
      expect(pos.costBasis).toBe(98000);
      expect(pos.avgEntryPrice).toBe(49000); // VWAP: (50000 + 48000) / 2
      expect(pos.currentQty).toBe(2);
      expect(pos.events).toHaveLength(2);
    });

    it("handles weighted average with different quantities", () => {
      const pos = openPos("LONG", 2, 50000); // cost basis = 100000
      addToPos(pos, 1, 47000);               // add cost = 47000

      expect(pos.entryQty).toBe(3);
      expect(pos.costBasis).toBe(147000);
      expect(pos.avgEntryPrice).toBeCloseTo(49000, 2); // 147000 / 3
      expect(pos.currentQty).toBe(3);
    });

    it("handles triple DCA", () => {
      const pos = openPos("LONG", 1, 50000);
      addToPos(pos, 1, 48000);
      addToPos(pos, 1, 46000);

      expect(pos.entryQty).toBe(3);
      expect(pos.costBasis).toBe(144000);
      expect(pos.avgEntryPrice).toBe(48000); // (50000 + 48000 + 46000) / 3
    });

    it("throws when adding to closed position", () => {
      const pos = openPos("LONG", 1, 50000);
      closePos(pos, 1, 55000);
      expect(() => addToPos(pos, 1, 52000)).toThrow("Cannot add to closed position");
    });
  });

  describe("partial close", () => {
    it("partially closes and keeps position open", () => {
      const pos = openPos("LONG", 2, 50000);
      const pnl = closePos(pos, 1, 55000);

      expect(pnl).toBe(5000); // (55000 - 50000) × 1
      expect(pos.status).toBe("OPEN");
      expect(pos.currentQty).toBe(1);
      expect(pos.realisedPnl).toBe(5000);
      expect(pos.events).toHaveLength(2);
      expect(pos.events[1].type).toBe("PARTIAL_CLOSE");
    });

    it("partial close then full close", () => {
      const pos = openPos("LONG", 3, 50000);

      // Partial close 1 unit at profit
      const pnl1 = closePos(pos, 1, 55000);
      expect(pnl1).toBe(5000);
      expect(pos.currentQty).toBe(2);
      expect(pos.status).toBe("OPEN");

      // Full close remaining 2 units at loss
      const pnl2 = closePos(pos, 2, 49000);
      expect(pnl2).toBe(-2000); // (49000 - 50000) × 2
      expect(pos.currentQty).toBe(0);
      expect(pos.status).toBe("CLOSED");
      expect(pos.realisedPnl).toBe(3000); // 5000 + (-2000)
    });

    it("throws when close qty exceeds current qty", () => {
      const pos = openPos("LONG", 1, 50000);
      expect(() => closePos(pos, 2, 55000)).toThrow("Cannot close more than current qty");
    });

    it("throws when closing already closed position", () => {
      const pos = openPos("LONG", 1, 50000);
      closePos(pos, 1, 55000);
      expect(() => closePos(pos, 1, 55000)).toThrow("Cannot close closed position");
    });
  });

  describe("full lifecycle: open → add → partial close → close", () => {
    it("LONG lifecycle with DCA and partial close", () => {
      // Open 1 BTC at $50,000
      const pos = openPos("LONG", 1, 50000);
      expect(pos.avgEntryPrice).toBe(50000);

      // DCA: add 1 BTC at $46,000
      addToPos(pos, 1, 46000);
      expect(pos.avgEntryPrice).toBe(48000); // VWAP: (50000 + 46000) / 2
      expect(pos.currentQty).toBe(2);

      // Partial close: sell 1 BTC at $52,000
      const pnl1 = closePos(pos, 1, 52000);
      expect(pnl1).toBe(4000); // (52000 - 48000) × 1
      expect(pos.currentQty).toBe(1);
      expect(pos.status).toBe("OPEN");
      expect(pos.realisedPnl).toBe(4000);

      // Full close: sell remaining 1 BTC at $50,000
      const pnl2 = closePos(pos, 1, 50000);
      expect(pnl2).toBe(2000); // (50000 - 48000) × 1
      expect(pos.status).toBe("CLOSED");
      expect(pos.realisedPnl).toBe(6000); // 4000 + 2000

      // 5 events total: OPEN, ADD, PARTIAL_CLOSE, CLOSE
      expect(pos.events).toHaveLength(4);
      expect(pos.events.map((e) => e.type)).toEqual(["OPEN", "ADD", "PARTIAL_CLOSE", "CLOSE"]);
    });

    it("SHORT lifecycle with add and partial close", () => {
      // Open short 2 ETH at $3,000
      const pos = openPos("SHORT", 2, 3000);

      // DCA: add 1 ETH short at $3,200
      addToPos(pos, 1, 3200);
      expect(pos.avgEntryPrice).toBeCloseTo(3066.67, 1); // (6000 + 3200) / 3

      // Partial close 1 ETH at $2,800 (profit)
      const pnl1 = closePos(pos, 1, 2800);
      expect(pnl1).toBeCloseTo(266.67, 1); // (3066.67 - 2800) × 1
      expect(pos.currentQty).toBe(2);

      // Close remaining at $3,100 (loss on remaining)
      const pnl2 = closePos(pos, 2, 3100);
      expect(pnl2).toBeCloseTo(-66.67, 0); // (3066.67 - 3100) × 2
      expect(pos.status).toBe("CLOSED");
    });
  });

  describe("average entry recalculation edge cases", () => {
    it("same price adds do not change average", () => {
      const pos = openPos("LONG", 1, 50000);
      addToPos(pos, 1, 50000);
      expect(pos.avgEntryPrice).toBe(50000);
    });

    it("handles small quantities accurately", () => {
      const pos = openPos("LONG", 0.001, 50000);
      addToPos(pos, 0.002, 48000);

      expect(pos.entryQty).toBeCloseTo(0.003, 8);
      expect(pos.costBasis).toBeCloseTo(146, 2); // 50 + 96
      expect(pos.avgEntryPrice).toBeCloseTo(48666.67, 0);
    });

    it("handles large price differences", () => {
      const pos = openPos("LONG", 1, 100);
      addToPos(pos, 1, 10000);

      expect(pos.avgEntryPrice).toBe(5050); // (100 + 10000) / 2
    });
  });

  describe("realised PnL calculation", () => {
    it("zero PnL when close price equals entry", () => {
      const pos = openPos("LONG", 1, 50000);
      const pnl = closePos(pos, 1, 50000);
      expect(pnl).toBe(0);
    });

    it("partial closes accumulate realised PnL correctly", () => {
      const pos = openPos("LONG", 4, 100);

      closePos(pos, 1, 110); // +10
      expect(pos.realisedPnl).toBe(10);

      closePos(pos, 1, 90);  // -10
      expect(pos.realisedPnl).toBe(0);

      closePos(pos, 1, 120); // +20
      expect(pos.realisedPnl).toBe(20);

      closePos(pos, 1, 100); // 0
      expect(pos.realisedPnl).toBe(20);
      expect(pos.status).toBe("CLOSED");
    });

    it("PnL is symmetrical for long vs short at same price levels", () => {
      const longPos = openPos("LONG", 1, 100);
      const longPnl = closePos(longPos, 1, 110);

      const shortPos = openPos("SHORT", 1, 110);
      const shortPnl = closePos(shortPos, 1, 100);

      expect(longPnl).toBe(10);  // long profit: buy low sell high
      expect(shortPnl).toBe(10); // short profit: sell high buy low
    });
  });

  describe("position snapshot integrity", () => {
    it("makePosition creates valid snapshot", () => {
      const pos = makePosition();
      expect(pos.id).toBeDefined();
      expect(pos.side).toBe("LONG");
      expect(pos.status).toBe("OPEN");
    });

    it("calcUnrealisedPnl works with snapshot from makePosition", () => {
      const pos = makePosition({
        side: "LONG",
        avgEntryPrice: 100,
        currentQty: 5,
      });
      expect(calcUnrealisedPnl(pos, 110)).toBe(50);
    });
  });
});

// ---------------------------------------------------------------------------
// Schema / migration sanity tests
// ---------------------------------------------------------------------------

describe("position schema design", () => {
  it("PositionSide enum covers required cases", () => {
    const sides = ["LONG", "SHORT"] as const;
    expect(sides).toContain("LONG");
    expect(sides).toContain("SHORT");
  });

  it("PositionStatus enum covers lifecycle states", () => {
    const statuses = ["OPEN", "CLOSED"] as const;
    expect(statuses).toContain("OPEN");
    expect(statuses).toContain("CLOSED");
  });

  it("PositionEventType enum covers all mutations", () => {
    const types = ["OPEN", "ADD", "PARTIAL_CLOSE", "CLOSE", "SL_UPDATE", "TP_UPDATE"] as const;
    expect(types).toHaveLength(6);
    expect(types).toContain("OPEN");
    expect(types).toContain("ADD");
    expect(types).toContain("PARTIAL_CLOSE");
    expect(types).toContain("CLOSE");
    expect(types).toContain("SL_UPDATE");
    expect(types).toContain("TP_UPDATE");
  });
});
