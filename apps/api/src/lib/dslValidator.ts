/**
 * Strategy DSL Validator (Ajv, JSON Schema 2020-12)
 *
 * Validates a strategy dslJson against the canonical schema.
 * Supports both v1 (MVP) and v2 (dynamic exits, conditional side) strategies.
 *
 * Returns null on success or an array of human-readable error messages.
 */

import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { calculateMaxExposure, calculateMaxDeviation } from "./dcaPlanning.js";
import type { DcaConfig } from "./dcaPlanning.js";

// ---------------------------------------------------------------------------
// Shared $defs
// ---------------------------------------------------------------------------

const EXIT_LEVEL_DEF = {
  type: "object",
  required: ["type", "value"],
  additionalProperties: false,
  properties: {
    type: { enum: ["fixed_pct", "fixed_price", "atr_multiple"] },
    value: { type: "number", exclusiveMinimum: 0 },
    atrPeriod: { type: "integer", minimum: 1 },
  },
} as const;

// ---------------------------------------------------------------------------
// DCA config $def (#131)
// ---------------------------------------------------------------------------

const DCA_CONFIG_DEF = {
  type: "object",
  additionalProperties: false,
  required: [
    "baseOrderSizeUsd",
    "maxSafetyOrders",
    "priceStepPct",
    "stepScale",
    "volumeScale",
    "takeProfitPct",
  ],
  properties: {
    baseOrderSizeUsd: { type: "number", exclusiveMinimum: 0 },
    maxSafetyOrders: { type: "integer", minimum: 1, maximum: 50 },
    priceStepPct: { type: "number", exclusiveMinimum: 0, maximum: 50 },
    stepScale: { type: "number", minimum: 1, maximum: 10 },
    volumeScale: { type: "number", minimum: 1, maximum: 10 },
    takeProfitPct: { type: "number", exclusiveMinimum: 0, maximum: 100 },
  },
} as const;

// ---------------------------------------------------------------------------
// Schema (v1 + v2 unified)
// ---------------------------------------------------------------------------

const STRATEGY_SCHEMA = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "https://example.local/schema/strategy.schema.json",
  title: "Strategy DSL (v1 + v2)",
  type: "object",
  additionalProperties: false,
  required: [
    "id",
    "name",
    "dslVersion",
    "enabled",
    "market",
    "entry",
    "risk",
    "execution",
    "guards",
  ],
  properties: {
    id: { type: "string", minLength: 1 },
    name: { type: "string", minLength: 1 },
    dslVersion: { type: "integer", minimum: 1, maximum: 2 },
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
      properties: {
        side: { enum: ["Buy", "Sell"] },
        sideCondition: {
          type: "object",
          additionalProperties: false,
          required: ["indicator", "long", "short"],
          properties: {
            indicator: {
              type: "object",
              required: ["type"],
              properties: {
                type: { type: "string", minLength: 1 },
                length: { type: "integer", minimum: 1 },
              },
              additionalProperties: true,
            },
            source: {
              type: "string",
              enum: ["open", "high", "low", "close"],
              default: "close",
            },
            long: {
              type: "object",
              required: ["op"],
              properties: { op: { enum: ["gt", "gte", "lt", "lte"] } },
              additionalProperties: false,
            },
            short: {
              type: "object",
              required: ["op"],
              properties: { op: { enum: ["gt", "gte", "lt", "lte"] } },
              additionalProperties: false,
            },
          },
        },
      },
    },

    exit: {
      type: "object",
      additionalProperties: false,
      required: ["stopLoss", "takeProfit"],
      properties: {
        stopLoss: { $ref: "#/$defs/exitLevel" },
        takeProfit: { $ref: "#/$defs/exitLevel" },
        trailingStop: {
          type: "object",
          additionalProperties: false,
          required: ["type"],
          properties: {
            type: { enum: ["trailing_pct", "trailing_atr"] },
            activationPct: { type: "number", exclusiveMinimum: 0 },
            callbackPct: { type: "number", exclusiveMinimum: 0 },
            activationAtr: { type: "number", exclusiveMinimum: 0 },
            callbackAtr: { type: "number", exclusiveMinimum: 0 },
          },
        },
        indicatorExit: {
          type: "object",
          additionalProperties: false,
          required: ["indicator", "condition"],
          properties: {
            indicator: {
              type: "object",
              required: ["type"],
              properties: {
                type: { type: "string", minLength: 1 },
                length: { type: "integer", minimum: 1 },
              },
              additionalProperties: true,
            },
            condition: {
              type: "object",
              required: ["op", "value"],
              properties: {
                op: { enum: ["gt", "gte", "lt", "lte", "eq"] },
                value: { type: "number" },
              },
              additionalProperties: false,
            },
            appliesTo: { enum: ["long", "short", "both"], default: "both" },
          },
        },
        timeExit: {
          type: "object",
          additionalProperties: false,
          required: ["maxBarsInPosition"],
          properties: {
            maxBarsInPosition: { type: "integer", minimum: 1 },
          },
        },
      },
    },

    risk: {
      type: "object",
      additionalProperties: false,
      required: ["maxPositionSizeUsd", "riskPerTradePct", "cooldownSeconds"],
      properties: {
        maxPositionSizeUsd: { type: "number", exclusiveMinimum: 0 },
        riskPerTradePct: {
          type: "number",
          exclusiveMinimum: 0,
          maximum: 100,
        },
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

    dca: { $ref: "#/$defs/dcaConfig" },
  },

  $defs: {
    exitLevel: EXIT_LEVEL_DEF,
    dcaConfig: DCA_CONFIG_DEF,
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
 * Performs:
 * 1. Ajv JSON Schema validation (structural)
 * 2. Cross-field semantic checks (v1/v2 version consistency)
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

  // Collect Ajv schema errors
  const errors: DslValidationError[] = valid
    ? []
    : (validateSchema.errors ?? []).map((e) => {
        const field = e.instancePath
          ? e.instancePath.replace(/^\//, "").replace(/\//g, ".")
          : (e.params as Record<string, unknown>)?.missingProperty
            ? String((e.params as Record<string, unknown>).missingProperty)
            : "dslJson";
        return { field, message: e.message ?? "invalid" };
      });

  // Cross-field semantic validation
  const obj = dslJson as Record<string, unknown>;
  const dslVersion =
    typeof obj.dslVersion === "number" ? obj.dslVersion : undefined;
  const entry = obj.entry as Record<string, unknown> | undefined;
  const exit = obj.exit as Record<string, unknown> | undefined;

  // v2 fields present in v1 strategy
  if (dslVersion === 1) {
    if (exit) {
      errors.push({
        field: "exit",
        message:
          'top-level "exit" section requires dslVersion >= 2',
      });
    }
    if (entry?.sideCondition) {
      errors.push({
        field: "entry.sideCondition",
        message:
          '"entry.sideCondition" requires dslVersion >= 2',
      });
    }
  }

  // v2 requires exit section
  if (dslVersion === 2 && !exit) {
    errors.push({
      field: "exit",
      message:
        'dslVersion 2 requires a top-level "exit" section with stopLoss and takeProfit',
    });
  }

  // side and sideCondition are mutually exclusive
  if (entry?.side && entry?.sideCondition) {
    errors.push({
      field: "entry",
      message:
        '"entry.side" and "entry.sideCondition" are mutually exclusive; use one or the other',
    });
  }

  // sideCondition requires v2
  if (entry?.sideCondition && dslVersion !== undefined && dslVersion < 2) {
    // Already caught above for v1, but explicit for clarity
  }

  // At least one of side or sideCondition should be present in entry
  if (entry && !entry.side && !entry.sideCondition) {
    errors.push({
      field: "entry",
      message:
        'entry must have either "side" or "sideCondition"',
    });
  }

  // DCA semantic validation (#131)
  const dca = obj.dca as Record<string, unknown> | undefined;
  if (dca) {
    // DCA requires v2
    if (dslVersion === 1) {
      errors.push({
        field: "dca",
        message: '"dca" section requires dslVersion >= 2',
      });
    }

    // DCA requires risk.maxPositionSizeUsd as an exposure cap
    const risk = obj.risk as Record<string, unknown> | undefined;
    const maxPosUsd =
      typeof risk?.maxPositionSizeUsd === "number"
        ? risk.maxPositionSizeUsd
        : undefined;

    if (maxPosUsd === undefined) {
      errors.push({
        field: "risk.maxPositionSizeUsd",
        message:
          '"risk.maxPositionSizeUsd" is required when "dca" is configured, to cap total ladder exposure',
      });
    }

    // Build a DcaConfig for domain validation (only if all fields pass schema)
    const baseUsd =
      typeof dca.baseOrderSizeUsd === "number" ? dca.baseOrderSizeUsd : 0;
    const maxSO =
      typeof dca.maxSafetyOrders === "number" ? dca.maxSafetyOrders : 0;
    const stepPct =
      typeof dca.priceStepPct === "number" ? dca.priceStepPct : 0;
    const stepSc =
      typeof dca.stepScale === "number" ? dca.stepScale : 1;
    const volScale =
      typeof dca.volumeScale === "number" ? dca.volumeScale : 1;
    const tpPct =
      typeof dca.takeProfitPct === "number" ? dca.takeProfitPct : 0;

    if (baseUsd > 0 && maxSO > 0 && stepPct > 0) {
      const dcaCfg: DcaConfig = {
        baseOrderSizeUsd: baseUsd,
        maxSafetyOrders: maxSO,
        priceStepPct: stepPct,
        stepScale: stepSc,
        volumeScale: volScale,
        takeProfitPct: tpPct,
      };

      // Check cumulative deviation stays below 100%
      const maxDev = calculateMaxDeviation(dcaCfg);
      if (maxDev >= 100) {
        errors.push({
          field: "dca",
          message: `DCA cumulative price deviation reaches ${maxDev.toFixed(2)}%, which would produce non-positive trigger prices; reduce maxSafetyOrders, priceStepPct, or stepScale`,
        });
      }

      // Check total exposure against maxPositionSizeUsd
      if (maxPosUsd !== undefined) {
        const totalExposure = calculateMaxExposure(dcaCfg);
        if (totalExposure > maxPosUsd) {
          errors.push({
            field: "dca",
            message: `DCA total exposure (${totalExposure.toFixed(2)} USD) exceeds risk.maxPositionSizeUsd (${maxPosUsd} USD)`,
          });
        }
      }
    }
  }

  return errors.length > 0
    ? errors
    : null;
}
