/**
 * tradingKillSwitch — unit coverage (docs/54-T6 §5 / docs/15-operations §6.3).
 *
 * Pins:
 *
 *   1. Default (env unset) → enabled (fail-open).
 *   2. False-literal env values → disabled. Case-insensitive, whitespace
 *      tolerant. The accepted set is locked: false / 0 / no / off.
 *   3. Any other non-empty value (true / 1 / yes / arbitrary) → enabled.
 *   4. assertTradingEnabled throws TradingDisabledError when off and is a
 *      no-op when on.
 *   5. The thrown error's message matches the `errorClassifier` pattern
 *      `/trading disabled/i` so the worker retry loop classifies it as
 *      transient.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  isTradingEnabled,
  assertTradingEnabled,
  TradingDisabledError,
} from "../../src/lib/tradingKillSwitch.js";
import { classifyExecutionError } from "../../src/lib/errorClassifier.js";
import { bybitPlaceOrder } from "../../src/lib/bybitOrder.js";

let savedEnv: string | undefined;

beforeEach(() => {
  savedEnv = process.env.TRADING_ENABLED;
  delete process.env.TRADING_ENABLED;
});

afterEach(() => {
  if (savedEnv === undefined) delete process.env.TRADING_ENABLED;
  else process.env.TRADING_ENABLED = savedEnv;
});

// ---------------------------------------------------------------------------
// 1. Default
// ---------------------------------------------------------------------------

describe("isTradingEnabled — default fail-open", () => {
  it("returns true when TRADING_ENABLED is unset", () => {
    expect(isTradingEnabled()).toBe(true);
  });

  it("returns true when TRADING_ENABLED is empty string", () => {
    process.env.TRADING_ENABLED = "";
    expect(isTradingEnabled()).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 2. Disabled — accepted false-literal set
// ---------------------------------------------------------------------------

describe("isTradingEnabled — disabled values", () => {
  it.each(["false", "FALSE", "False", "0", "no", "NO", "off", "OFF", " false ", "  0  "])(
    "%s → disabled",
    (value) => {
      process.env.TRADING_ENABLED = value;
      expect(isTradingEnabled()).toBe(false);
    },
  );
});

// ---------------------------------------------------------------------------
// 3. Enabled — non-empty, non-false-literal values
// ---------------------------------------------------------------------------

describe("isTradingEnabled — enabled values", () => {
  it.each(["true", "1", "yes", "on", "TRUE", "anything-else", "live"])(
    "%s → enabled",
    (value) => {
      process.env.TRADING_ENABLED = value;
      expect(isTradingEnabled()).toBe(true);
    },
  );
});

// ---------------------------------------------------------------------------
// 4. assertTradingEnabled
// ---------------------------------------------------------------------------

describe("assertTradingEnabled", () => {
  it("no-op when enabled", () => {
    process.env.TRADING_ENABLED = "true";
    expect(() => assertTradingEnabled()).not.toThrow();
  });

  it("throws TradingDisabledError when disabled", () => {
    process.env.TRADING_ENABLED = "false";
    expect(() => assertTradingEnabled()).toThrow(TradingDisabledError);
  });

  it("the thrown error name + message are stable (errorClassifier-friendly)", () => {
    process.env.TRADING_ENABLED = "0";
    try {
      assertTradingEnabled();
      throw new Error("expected throw");
    } catch (err) {
      expect(err).toBeInstanceOf(TradingDisabledError);
      const e = err as TradingDisabledError;
      expect(e.name).toBe("TradingDisabledError");
      expect(e.message).toMatch(/trading disabled/i);
    }
  });
});

// ---------------------------------------------------------------------------
// 5. Classifier integration — TradingDisabledError → transient
// ---------------------------------------------------------------------------

describe("errorClassifier integration", () => {
  it("TradingDisabledError classifies as transient + retryable", () => {
    const err = new TradingDisabledError();
    const cls = classifyExecutionError(err);
    expect(cls.errorClass).toBe("transient");
    expect(cls.retryable).toBe(true);
  });

  it("a plain Error with the same message also classifies as transient (pattern match)", () => {
    const err = new Error("Trading disabled by global TRADING_ENABLED kill switch");
    expect(classifyExecutionError(err).errorClass).toBe("transient");
  });
});

// ---------------------------------------------------------------------------
// 6. bybitPlaceOrder integration — guard fires BEFORE fetch
// ---------------------------------------------------------------------------

describe("bybitPlaceOrder kill-switch guard", () => {
  const realFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = realFetch;
  });

  it("throws TradingDisabledError without making any HTTP call when disabled", async () => {
    process.env.TRADING_ENABLED = "false";

    const fetchSpy = vi.fn(async () =>
      new Response("{}", { status: 200, headers: { "content-type": "application/json" } }),
    );
    globalThis.fetch = fetchSpy as unknown as typeof fetch;

    await expect(
      bybitPlaceOrder("apiKey", "secret", {
        symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: "0.001",
      }),
    ).rejects.toBeInstanceOf(TradingDisabledError);

    // The guard runs before the fetch — no HTTP call must have been made.
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("when enabled, the guard is a no-op and the fetch is called", async () => {
    process.env.TRADING_ENABLED = "true";

    const fetchSpy = vi.fn(async () =>
      new Response(
        JSON.stringify({ retCode: 0, retMsg: "OK", result: { orderId: "x", orderLinkId: "y" } }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    globalThis.fetch = fetchSpy as unknown as typeof fetch;

    const out = await bybitPlaceOrder("apiKey", "secret", {
      symbol: "BTCUSDT", side: "Buy", orderType: "Market", qty: "0.001",
    });

    expect(out).toEqual({ orderId: "x", orderLinkId: "y" });
    expect(fetchSpy).toHaveBeenCalledOnce();
  });
});
