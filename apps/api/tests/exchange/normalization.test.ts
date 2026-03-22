import { describe, it, expect } from "vitest";
import {
  normalizeOrder,
  roundToStep,
  countDecimals,
  type NormalizeOrderInput,
} from "../../src/lib/exchange/normalizer.js";
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

function makeEthInstrument(overrides: Partial<InstrumentInfo> = {}): InstrumentInfo {
  return {
    symbol: "ETHUSDT",
    baseCoin: "ETH",
    quoteCoin: "USDT",
    tickSize: 0.01,
    qtyStep: 0.01,
    minOrderQty: 0.01,
    maxOrderQty: 1000,
    minNotional: 5,
    maxLeverage: 100,
    status: "Trading",
    fetchedAt: Date.now(),
    ...overrides,
  };
}

function makeCheapInstrument(): InstrumentInfo {
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
// roundToStep
// ---------------------------------------------------------------------------

describe("roundToStep", () => {
  it("rounds down to step", () => {
    expect(roundToStep(0.0025, 0.001)).toBeCloseTo(0.002, 10);
  });

  it("keeps exact multiples unchanged", () => {
    expect(roundToStep(0.003, 0.001)).toBeCloseTo(0.003, 10);
  });

  it("rounds to integer step", () => {
    expect(roundToStep(15.7, 1)).toBe(15);
  });

  it("handles zero step (no-op)", () => {
    expect(roundToStep(1.234, 0)).toBe(1.234);
  });

  it("handles large qty step for cheap coins", () => {
    expect(roundToStep(155, 10)).toBe(150);
  });
});

// ---------------------------------------------------------------------------
// countDecimals
// ---------------------------------------------------------------------------

describe("countDecimals", () => {
  it("counts decimal places", () => {
    expect(countDecimals(0.001)).toBe(3);
    expect(countDecimals(0.10)).toBe(1);
    expect(countDecimals(1)).toBe(0);
    expect(countDecimals(0.01)).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// normalizeOrder — quantity normalization
// ---------------------------------------------------------------------------

describe("normalizeOrder – qty normalization", () => {
  it("rounds qty to qtyStep", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: 0.0025 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.order.qty).toBe("0.002");
      expect(result.order.diagnostics.appliedRules.length).toBeGreaterThan(0);
    }
  });

  it("keeps exact qty unchanged", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: 0.005 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.order.qty).toBe("0.005");
    }
  });

  it("rejects qty below minimum", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: 0.0001 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.reason).toContain("below minimum");
    }
  });

  it("rejects qty above maximum", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: 200 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.reason).toContain("exceeds maximum");
    }
  });
});

// ---------------------------------------------------------------------------
// normalizeOrder — price normalization
// ---------------------------------------------------------------------------

describe("normalizeOrder – price normalization", () => {
  it("rounds price to tickSize for Limit orders", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Limit", qty: 0.01, price: 50123.45 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.order.price).toBe("50123.4");
    }
  });

  it("rejects Limit order without price", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Limit", qty: 0.01 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.reason).toContain("Limit order requires a positive price");
    }
  });

  it("Market orders do not require price", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: 0.01 },
      makeBtcInstrument(),
    );
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.order.price).toBeUndefined();
    }
  });
});

// ---------------------------------------------------------------------------
// normalizeOrder — min notional
// ---------------------------------------------------------------------------

describe("normalizeOrder – min notional", () => {
  it("rejects order below min notional", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Limit", qty: 0.001, price: 1.0 },
      makeBtcInstrument({ minNotional: 5 }),
    );
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.reason).toContain("below minimum");
      expect(result.reason).toContain("notional");
    }
  });

  it("accepts order above min notional", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Limit", qty: 0.01, price: 50000 },
      makeBtcInstrument({ minNotional: 5 }),
    );
    expect(result.valid).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// normalizeOrder — instrument status
// ---------------------------------------------------------------------------

describe("normalizeOrder – instrument status", () => {
  it("rejects order on non-trading instrument", () => {
    const result = normalizeOrder(
      { symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: 0.01 },
      makeBtcInstrument({ status: "PreLaunch" }),
    );
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.reason).toContain("not trading");
    }
  });
});

// ---------------------------------------------------------------------------
// normalizeOrder — diagnostics
// ---------------------------------------------------------------------------

describe("normalizeOrder – diagnostics", () => {
  it("includes complete diagnostics", () => {
    const result = normalizeOrder(
      { symbol: "ETHUSDT", side: "Sell", orderType: "Limit", qty: 0.035, price: 3500.123 },
      makeEthInstrument(),
    );
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.order.diagnostics.rawQty).toBe(0.035);
      expect(result.order.diagnostics.normalizedQty).toBe(0.03);
      expect(result.order.diagnostics.rawPrice).toBe(3500.123);
      expect(result.order.diagnostics.normalizedPrice).toBe(3500.12);
      expect(result.order.diagnostics.notionalUsd).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// normalizeOrder — cheap coins with integer qty step
// ---------------------------------------------------------------------------

describe("normalizeOrder – cheap coins", () => {
  it("handles integer qty step (DOGE)", () => {
    const result = normalizeOrder(
      { symbol: "DOGEUSDT", side: "Buy", orderType: "Market", qty: 155 },
      makeCheapInstrument(),
    );
    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.order.qty).toBe("155");
    }
  });

  it("rejects DOGE order below min qty", () => {
    const result = normalizeOrder(
      { symbol: "DOGEUSDT", side: "Buy", orderType: "Market", qty: 5 },
      makeCheapInstrument(),
    );
    expect(result.valid).toBe(false);
  });
});
