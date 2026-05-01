/**
 * Multi-interval dataset bundle (docs/52-T1).
 *
 * A bundle is a `Partial<Record<CandleInterval, string | true>>`:
 *
 * - `string` — concrete `MarketDataset.id` for that interval. Required for
 *   backtest / walk-forward, where exactly-this-data is the whole point.
 * - `true`  — "any candles for this `(symbol, interval)`". Used by runtime,
 *   where the bot just wants live candles, not a frozen historical slice.
 *
 * The bundle lives on `Bot.datasetBundleJson`, `BacktestSweep.datasetBundleJson`
 * and `WalkForwardRun.datasetBundleJson` as a nullable JSON column. `null`
 * keeps the legacy single-TF behaviour driven by the model's primary
 * `timeframe` / `datasetId` fields.
 *
 * docs/50 §Решение 2 — bundle is intentionally NOT a Prisma model: keeps
 * migrations additive, avoids cascading FKs.
 *
 * Validation lives here as a hand-rolled function rather than zod because the
 * api package does not depend on zod (uses ajv elsewhere); the helper
 * returns `{ field, message }[]` to match the validation style of other
 * routes (`routes/presets.ts`, `routes/bots.ts`).
 */

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export const CANDLE_INTERVALS = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"] as const;
export type CandleInterval = typeof CANDLE_INTERVALS[number];

/** Practical ceiling — most flagship strategies need ≤3 TFs (5m/1H/4H, etc).
 *  Cap at 4 to bound loader work and keep query plans predictable. */
export const MAX_BUNDLE_INTERVALS = 4;

export type DatasetBundleValue = string | true;
export type DatasetBundle = Partial<Record<CandleInterval, DatasetBundleValue>>;

export type BundleMode = "runtime" | "backtest";

export interface BundleValidationError {
  field: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

const CANDLE_INTERVAL_SET: ReadonlySet<string> = new Set(CANDLE_INTERVALS);

/**
 * Validate a candidate JSON value as a DatasetBundle.
 *
 * Returns `{ bundle }` on success or `{ errors }` on failure. `mode="backtest"`
 * additionally requires every value to be a concrete `datasetId` (string).
 */
export function parseDatasetBundle(
  raw: unknown,
  opts: { mode?: BundleMode } = {},
): { bundle: DatasetBundle; errors: [] } | { bundle?: undefined; errors: BundleValidationError[] } {
  const errors: BundleValidationError[] = [];

  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    return { errors: [{ field: "datasetBundleJson", message: "must be a non-null object" }] };
  }

  const entries = Object.entries(raw as Record<string, unknown>);
  if (entries.length < 1) {
    errors.push({ field: "datasetBundleJson", message: "bundle must contain at least 1 interval" });
  }
  if (entries.length > MAX_BUNDLE_INTERVALS) {
    errors.push({
      field: "datasetBundleJson",
      message: `bundle must contain at most ${MAX_BUNDLE_INTERVALS} intervals (got ${entries.length})`,
    });
  }

  const out: DatasetBundle = {};
  for (const [key, value] of entries) {
    if (!CANDLE_INTERVAL_SET.has(key)) {
      errors.push({
        field: `datasetBundleJson.${key}`,
        message: `unknown interval "${key}" (allowed: ${CANDLE_INTERVALS.join(", ")})`,
      });
      continue;
    }
    const interval = key as CandleInterval;
    if (value === true) {
      if (opts.mode === "backtest") {
        errors.push({
          field: `datasetBundleJson.${interval}`,
          message: "backtest mode requires a concrete datasetId; received literal true",
        });
        continue;
      }
      out[interval] = true;
    } else if (typeof value === "string" && value.length > 0) {
      out[interval] = value;
    } else {
      errors.push({
        field: `datasetBundleJson.${interval}`,
        message: "value must be a non-empty string (datasetId) or literal true",
      });
    }
  }

  if (errors.length > 0) return { errors };
  return { bundle: out, errors: [] };
}

/**
 * Throwing variant — use only when the caller has already established the
 * value is supposed to be a valid bundle (e.g. data read back from a row that
 * passed validation on write).
 */
export function parseDatasetBundleOrThrow(
  raw: unknown,
  opts: { mode?: BundleMode } = {},
): DatasetBundle {
  const result = parseDatasetBundle(raw, opts);
  if (!result.bundle) {
    const summary = result.errors.map((e) => `${e.field}: ${e.message}`).join("; ");
    throw new Error(`Invalid DatasetBundle — ${summary}`);
  }
  return result.bundle;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function bundleIntervals(bundle: DatasetBundle): CandleInterval[] {
  // Preserve insertion order — callers that care about a primary-first
  // layout can rely on it; helpers below treat the set semantically.
  return Object.keys(bundle) as CandleInterval[];
}

export function bundleHasInterval(bundle: DatasetBundle, interval: CandleInterval): boolean {
  return Object.prototype.hasOwnProperty.call(bundle, interval);
}

/**
 * Returns the concrete datasetId for an interval, or `null` when:
 *  - the interval is missing,
 *  - the value is `true` (runtime placeholder, no dataset).
 */
export function bundleDatasetId(
  bundle: DatasetBundle,
  interval: CandleInterval,
): string | null {
  const v = bundle[interval];
  return typeof v === "string" ? v : null;
}

/**
 * The bundle is meaningful only if its primary TF is present — otherwise
 * the runtime / backtest cannot drive evaluation. Use this on every code
 * path that ingests a bundle alongside a primary timeframe.
 */
export function validateBundleAgainstPrimary(
  bundle: DatasetBundle,
  primaryInterval: CandleInterval,
): BundleValidationError[] {
  if (!bundleHasInterval(bundle, primaryInterval)) {
    return [{
      field: "datasetBundleJson",
      message: `primary timeframe "${primaryInterval}" must be present in the bundle`,
    }];
  }
  return [];
}
