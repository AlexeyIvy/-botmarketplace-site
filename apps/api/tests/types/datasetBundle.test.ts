/**
 * 52-T1 — DatasetBundle type validation.
 *
 * Covers the positive cases the loader (52-T2) and route handlers (52-T4)
 * will rely on, plus the negative cases that catch malformed JSON before it
 * reaches Prisma.
 */

import { describe, it, expect } from "vitest";
import {
  parseDatasetBundle,
  parseDatasetBundleOrThrow,
  bundleIntervals,
  bundleHasInterval,
  bundleDatasetId,
  validateBundleAgainstPrimary,
  MAX_BUNDLE_INTERVALS,
} from "../../src/types/datasetBundle.js";

describe("parseDatasetBundle", () => {
  it("accepts a backtest-shape bundle (every value is a datasetId)", () => {
    const result = parseDatasetBundle({ M5: "ds_a", H1: "ds_b" });
    expect(result.errors).toEqual([]);
    expect(result.bundle).toEqual({ M5: "ds_a", H1: "ds_b" });
  });

  it("accepts a runtime-shape bundle (literal true)", () => {
    const result = parseDatasetBundle({ M5: true });
    expect(result.errors).toEqual([]);
    expect(result.bundle).toEqual({ M5: true });
  });

  it("accepts a mixed-shape bundle in default (runtime-permissive) mode", () => {
    const result = parseDatasetBundle({ M5: "ds_a", H1: true });
    expect(result.errors).toEqual([]);
    expect(result.bundle).toEqual({ M5: "ds_a", H1: true });
  });

  it("rejects empty bundle", () => {
    const result = parseDatasetBundle({});
    expect(result.bundle).toBeUndefined();
    expect(result.errors.some((e) => /at least 1 interval/.test(e.message))).toBe(true);
  });

  it(`rejects bundle with more than ${MAX_BUNDLE_INTERVALS} intervals`, () => {
    const result = parseDatasetBundle({
      M1: "a", M5: "b", M15: "c", M30: "d", H1: "e",
    });
    expect(result.bundle).toBeUndefined();
    expect(result.errors.some((e) => /at most/.test(e.message))).toBe(true);
  });

  it("rejects unknown interval keys", () => {
    const result = parseDatasetBundle({ X1: "ds" });
    expect(result.bundle).toBeUndefined();
    expect(result.errors.some((e) => /unknown interval/.test(e.message))).toBe(true);
  });

  it("rejects empty-string datasetId", () => {
    const result = parseDatasetBundle({ M5: "" });
    expect(result.bundle).toBeUndefined();
    expect(result.errors[0].field).toBe("datasetBundleJson.M5");
  });

  it("rejects non-string, non-true values", () => {
    const result = parseDatasetBundle({ M5: 42 });
    expect(result.bundle).toBeUndefined();
    expect(result.errors[0].field).toBe("datasetBundleJson.M5");
  });

  it("rejects null / arrays / scalars at the top level", () => {
    expect(parseDatasetBundle(null).errors[0].message).toMatch(/non-null object/);
    expect(parseDatasetBundle([]).errors[0].message).toMatch(/non-null object/);
    expect(parseDatasetBundle("ds_a").errors[0].message).toMatch(/non-null object/);
    expect(parseDatasetBundle(42).errors[0].message).toMatch(/non-null object/);
  });

  it("rejects literal true in backtest mode", () => {
    const result = parseDatasetBundle({ M5: true }, { mode: "backtest" });
    expect(result.bundle).toBeUndefined();
    expect(result.errors.some((e) => /backtest mode requires a concrete datasetId/.test(e.message))).toBe(true);
  });

  it("accepts all-string bundle in backtest mode", () => {
    const result = parseDatasetBundle({ M5: "ds_a", H1: "ds_b" }, { mode: "backtest" });
    expect(result.errors).toEqual([]);
    expect(result.bundle).toEqual({ M5: "ds_a", H1: "ds_b" });
  });

  it("collects multiple errors at once", () => {
    const result = parseDatasetBundle({ X1: "a", M5: 0 });
    expect(result.bundle).toBeUndefined();
    expect(result.errors.length).toBeGreaterThanOrEqual(2);
  });
});

describe("parseDatasetBundleOrThrow", () => {
  it("returns the bundle on success", () => {
    expect(parseDatasetBundleOrThrow({ M5: "ds_a" })).toEqual({ M5: "ds_a" });
  });

  it("throws on validation failure", () => {
    expect(() => parseDatasetBundleOrThrow({})).toThrow(/Invalid DatasetBundle/);
  });
});

describe("helpers", () => {
  const bundle = { M5: "ds_a", H1: true } as const;

  it("bundleIntervals returns insertion order", () => {
    expect(bundleIntervals(bundle)).toEqual(["M5", "H1"]);
  });

  it("bundleHasInterval distinguishes present vs absent keys", () => {
    expect(bundleHasInterval(bundle, "M5")).toBe(true);
    expect(bundleHasInterval(bundle, "M15")).toBe(false);
  });

  it("bundleDatasetId returns the string for concrete entries and null for true", () => {
    expect(bundleDatasetId(bundle, "M5")).toBe("ds_a");
    expect(bundleDatasetId(bundle, "H1")).toBeNull();
    expect(bundleDatasetId(bundle, "M15")).toBeNull();
  });
});

describe("validateBundleAgainstPrimary", () => {
  it("accepts when primary TF is present", () => {
    expect(validateBundleAgainstPrimary({ M5: "ds_a", H1: "ds_b" }, "M5")).toEqual([]);
  });

  it("rejects when primary TF is missing", () => {
    const errs = validateBundleAgainstPrimary({ M5: true }, "H1");
    expect(errs).toHaveLength(1);
    expect(errs[0].message).toMatch(/primary timeframe "H1" must be present/);
  });
});
