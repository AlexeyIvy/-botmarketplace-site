import { describe, it, expect } from "vitest";
import { sizeOrder, type SizeOrderInput } from "../../src/lib/runtime/positionSizer.js";
import type { InstrumentInfo } from "../../src/lib/exchange/instrumentCache.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeBtcInstrument(overrides: Partial<InstrumentInfo> = {}): InstrumentInfo {
  return {
    symbol: "BTCUSDT",
    baseCoin: "BTC",
    quoteCoin: "USDT",
    tickSize: 0.10,
    qtyStep: 0.001,
    minOrderQty: 0.001,
    maxOrderQty: 100,
    minNotional: 5,
    maxLeverage: 100,
    status: "Trading",
    fetchedAt: Date.now(),
    ...overrides,
  };
}

function makeDoge(): InstrumentInfo {
  return {
    symbol: "DOGEUSDT",
    baseCoin: "DOGE",
    quoteCoin: "USDT",
    tickSize: 0.00001,
    qtyStep: 1,
    minOrderQty: 10,
    maxOrderQty: 10_000_000,
    minNotional: 5,
    maxLeverage: 25,
    status: "Trading",
    fetchedAt: Date.now(),
  };
}

// ---------------------------------------------------------------------------
// Basic sizing
// ---------------------------------------------------------------------------

describe("positionSizer – basic sizing", () => {
  it("converts USD notional to exchange-valid BTC qty", () => {
    const result = sizeOrder(
      { notionalUsd: 100, currentPrice: 50_000, leverage: 1 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    expect(result.qty).toBe(0.002); // 100/50000 = 0.002 (rounds to step)
    expect(result.effectiveNotionalUsd).toBeCloseTo(100, 0);
  });

  it("applies leverage multiplier", () => {
    const result = sizeOrder(
      { notionalUsd: 100, currentPrice: 50_000, leverage: 10 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    // (100 * 10) / 50000 = 0.02
    expect(result.qty).toBe(0.02);
  });

  it("caps leverage to maxLeverage", () => {
    const result = sizeOrder(
      { notionalUsd: 100, currentPrice: 50_000, leverage: 200 },
      makeBtcInstrument({ maxLeverage: 100 }),
    );
    expect(result.valid).toBe(true);
    // (100 * 100) / 50000 = 0.2
    expect(result.qty).toBe(0.2);
  });

  it("handles DOGE with integer step", () => {
    const result = sizeOrder(
      { notionalUsd: 100, currentPrice: 0.1, leverage: 1 },
      makeDoge(),
    );
    expect(result.valid).toBe(true);
    expect(result.qty).toBe(1000); // 100/0.1 = 1000, step=1
  });
});

// ---------------------------------------------------------------------------
// Rejection cases
// ---------------------------------------------------------------------------

describe("positionSizer – rejections", () => {
  it("rejects when qty rounds below min", () => {
    const result = sizeOrder(
      { notionalUsd: 0.01, currentPrice: 50_000, leverage: 1 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(false);
    expect(result.reason).toBeDefined();
  });

  it("rejects zero notional", () => {
    const result = sizeOrder(
      { notionalUsd: 0, currentPrice: 50_000, leverage: 1 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(false);
    expect(result.reason).toContain("notionalUsd must be positive");
  });

  it("rejects zero price", () => {
    const result = sizeOrder(
      { notionalUsd: 100, currentPrice: 0, leverage: 1 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(false);
    expect(result.reason).toContain("currentPrice must be positive");
  });

  it("rejects when notional is below min notional", () => {
    const result = sizeOrder(
      { notionalUsd: 1, currentPrice: 50_000, leverage: 1 },
      makeBtcInstrument({ minNotional: 5, minOrderQty: 0.001 }),
    );
    // qty = 1/50000 = 0.00002, rounds to 0 by step=0.001
    expect(result.valid).toBe(false);
  });

  it("rejects qty exceeding max", () => {
    const result = sizeOrder(
      { notionalUsd: 10_000_000, currentPrice: 1, leverage: 100 },
      makeBtcInstrument({ maxOrderQty: 100 }),
    );
    expect(result.valid).toBe(false);
    expect(result.reason).toContain("exceeds maximum");
  });
});

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

describe("positionSizer – edge cases", () => {
  it("leverage defaults to 1 when below 1", () => {
    const result = sizeOrder(
      { notionalUsd: 100, currentPrice: 50_000, leverage: 0 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    expect(result.qty).toBe(0.002);
  });

  it("rounds down precisely for small amounts", () => {
    // 50 / 2000 = 0.025 → step 0.01 → 0.02
    const result = sizeOrder(
      { notionalUsd: 50, currentPrice: 2000, leverage: 1 },
      makeBtcInstrument({ qtyStep: 0.01, minOrderQty: 0.01 }),
    );
    expect(result.valid).toBe(true);
    expect(result.qty).toBe(0.02);
  });
});
