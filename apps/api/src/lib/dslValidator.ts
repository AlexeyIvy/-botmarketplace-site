/**
 * Strategy DSL Validator (Ajv, JSON Schema 2020-12)
 *
 * Validates a strategy dslJson against the canonical schema in
 * docs/schema/strategy.schema.json.
 *
 * Returns null on success or an array of human-readable error messages.
 */

import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

// Schema imported as a plain object (no dynamic FS reads in prod)
const STRATEGY_SCHEMA = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "https://example.local/schema/strategy.schema.json",
  title: "Strategy DSL (MVP)",
  type: "object",
  additionalProperties: false,
  required: ["id", "name", "dslVersion", "enabled", "market", "entry", "risk", "execution", "guards"],
  properties: {
    id: { type: "string", minLength: 1 },
    name: { type: "string", minLength: 1 },
    dslVersion: { type: "integer", minimum: 1 },
    enabled: { type: "boolean" },

    market: {
      type: "object",
      additionalProperties: false,
      required: ["exchange", "env", "category", "symbol"],
      properties: {
        exchange: { const: "bybit" },
        env: { const: "demo" },
        category: { const: "linear" },
        symbol: { type: "string", minLength: 1 },
      },
    },

    timeframes: {
      type: "array",
      items: { type: "string" },
      minItems: 0,
    },

    entry: {
      type: "object",
      additionalProperties: true,
    },

    risk: {
      type: "object",
      additionalProperties: false,
      required: ["maxPositionSizeUsd", "riskPerTradePct", "cooldownSeconds"],
      properties: {
        maxPositionSizeUsd: { type: "number", exclusiveMinimum: 0 },
        riskPerTradePct: { type: "number", exclusiveMinimum: 0, maximum: 100 },
        cooldownSeconds: { type: "integer", minimum: 0 },
        dailyLossLimitUsd: { type: "number", minimum: 0 },
      },
    },

    execution: {
      type: "object",
      additionalProperties: false,
      required: ["orderType", "clientOrderIdPrefix"],
      properties: {
        orderType: { enum: ["Market", "Limit"] },
        clientOrderIdPrefix: { type: "string", minLength: 1 },
        maxSlippageBps: { type: "integer", minimum: 0, maximum: 500 },
      },
    },

    guards: {
      type: "object",
      additionalProperties: false,
      required: ["maxOpenPositions", "maxOrdersPerMinute", "pauseOnError"],
      properties: {
        maxOpenPositions: { type: "integer", const: 1 },
        maxOrdersPerMinute: { type: "integer", minimum: 1, maximum: 120 },
        pauseOnError: { type: "boolean" },
      },
    },
  },
};

// Build Ajv instance once (module-level singleton)
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv as Parameters<typeof addFormats>[0]);
const validateSchema = ajv.compile(STRATEGY_SCHEMA);

export interface DslValidationError {
  field: string;
  message: string;
}

/**
 * Validate a strategy dslJson object against the Strategy DSL schema.
 *
 * @returns null if valid, or an array of errors if invalid.
 */
export function validateDsl(dslJson: unknown): DslValidationError[] | null {
  if (dslJson === null || dslJson === undefined) {
    return [{ field: "dslJson", message: "dslJson is required" }];
  }
  if (typeof dslJson !== "object" || Array.isArray(dslJson)) {
    return [{ field: "dslJson", message: "dslJson must be a JSON object" }];
  }

  const valid = validateSchema(dslJson);
  if (valid) return null;

  const errors: DslValidationError[] = (validateSchema.errors ?? []).map((e) => {
    const field = e.instancePath
      ? e.instancePath.replace(/^\//, "").replace(/\//g, ".")
      : (e.params as Record<string, unknown>)?.missingProperty
        ? String((e.params as Record<string, unknown>).missingProperty)
        : "dslJson";
    return { field, message: e.message ?? "invalid" };
  });

  return errors.length > 0 ? errors : [{ field: "dslJson", message: "Validation failed" }];
}
