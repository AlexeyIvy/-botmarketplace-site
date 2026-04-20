import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { validateBybitEnv } from "../../src/lib/bybitEnv.js";

describe("validateBybitEnv", () => {
  const saved = {
    NODE_ENV: process.env.NODE_ENV,
    BYBIT_ENV: process.env.BYBIT_ENV,
    BYBIT_BASE_URL: process.env.BYBIT_BASE_URL,
    BYBIT_ALLOW_LIVE: process.env.BYBIT_ALLOW_LIVE,
  };

  beforeEach(() => {
    delete process.env.NODE_ENV;
    delete process.env.BYBIT_ENV;
    delete process.env.BYBIT_BASE_URL;
    delete process.env.BYBIT_ALLOW_LIVE;
  });

  afterEach(() => {
    process.env.NODE_ENV = saved.NODE_ENV;
    process.env.BYBIT_ENV = saved.BYBIT_ENV;
    process.env.BYBIT_BASE_URL = saved.BYBIT_BASE_URL;
    process.env.BYBIT_ALLOW_LIVE = saved.BYBIT_ALLOW_LIVE;
  });

  it("does not throw in demo mode (default)", () => {
    expect(() => validateBybitEnv()).not.toThrow();
  });

  it("does not throw for live mode outside of production", () => {
    process.env.BYBIT_ENV = "live";
    process.env.NODE_ENV = "development";
    expect(() => validateBybitEnv()).not.toThrow();
  });

  it("throws in production + live without BYBIT_ALLOW_LIVE", () => {
    process.env.BYBIT_ENV = "live";
    process.env.NODE_ENV = "production";
    expect(() => validateBybitEnv()).toThrow(/BYBIT_ALLOW_LIVE=true/);
  });

  it("allows production + live with BYBIT_ALLOW_LIVE=true", () => {
    process.env.BYBIT_ENV = "live";
    process.env.NODE_ENV = "production";
    process.env.BYBIT_ALLOW_LIVE = "true";
    expect(() => validateBybitEnv()).not.toThrow();
  });

  it("does not throw for demo mode in production", () => {
    process.env.BYBIT_ENV = "demo";
    process.env.NODE_ENV = "production";
    expect(() => validateBybitEnv()).not.toThrow();
  });

  it("does not throw for unknown BYBIT_BASE_URL host (warn only)", () => {
    process.env.BYBIT_BASE_URL = "https://api.example.com";
    process.env.NODE_ENV = "production";
    expect(() => validateBybitEnv()).not.toThrow();
  });
});
