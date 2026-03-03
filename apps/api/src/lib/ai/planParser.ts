import { randomUUID } from "node:crypto";

// ---------------------------------------------------------------------------
// Types — ActionPlan contract shared between backend and frontend
// ---------------------------------------------------------------------------

export type ActionType =
  | "CREATE_STRATEGY"
  | "VALIDATE_DSL"
  | "CREATE_STRATEGY_VERSION"
  | "RUN_BACKTEST"
  | "CREATE_BOT"
  | "START_RUN"
  | "STOP_RUN";

export type DangerLevel = "LOW" | "MEDIUM" | "HIGH";

export interface ActionItem {
  actionId: string;
  type: ActionType;
  title: string;
  dangerLevel: DangerLevel;
  requiresConfirmation: boolean;
  dependsOn: string[];
  input: Record<string, unknown>;
  preconditions: string[];
  expectedOutcome: string;
}

export interface ActionPlan {
  planId: string;      // assigned by server after DB persist
  createdAt: string;
  expiresAt: string;
  actions: ActionItem[];
  note?: string;
}

// ---------------------------------------------------------------------------
// Allowlist
// ---------------------------------------------------------------------------

const ALLOWED_TYPES = new Set<string>([
  "CREATE_STRATEGY",
  "VALIDATE_DSL",
  "CREATE_STRATEGY_VERSION",
  "RUN_BACKTEST",
  "CREATE_BOT",
  "START_RUN",
  "STOP_RUN",
]);

const ALLOWED_DANGER_LEVELS = new Set<string>(["LOW", "MEDIUM", "HIGH"]);

// ---------------------------------------------------------------------------
// Secret scanner — reject inputs containing secret-like keys
// ---------------------------------------------------------------------------

const SECRET_KEY_RE = /api.?key|secret|password|token|encrypted/i;

function containsSecretKeys(obj: unknown, depth = 0): boolean {
  if (depth > 5 || obj === null || typeof obj !== "object") return false;
  for (const key of Object.keys(obj as Record<string, unknown>)) {
    if (SECRET_KEY_RE.test(key)) return true;
    if (containsSecretKeys((obj as Record<string, unknown>)[key], depth + 1)) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Strip fence — some providers wrap JSON in markdown code blocks
// ---------------------------------------------------------------------------

function stripFence(raw: string): string {
  const stripped = raw.trim();
  // ```json ... ``` or ``` ... ```
  const fenceMatch = stripped.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/);
  if (fenceMatch) return fenceMatch[1];
  return stripped;
}

// ---------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------

export interface ParseResult {
  ok: true;
  actions: ActionItem[];
  note?: string;
}

export interface ParseError {
  ok: false;
  reason: string;
}

export function parsePlanResponse(raw: string): ParseResult | ParseError {
  let parsed: unknown;
  try {
    parsed = JSON.parse(stripFence(raw));
  } catch {
    return { ok: false, reason: "Provider returned non-JSON response" };
  }

  if (typeof parsed !== "object" || parsed === null) {
    return { ok: false, reason: "Provider returned non-object JSON" };
  }

  const obj = parsed as Record<string, unknown>;

  if (!Array.isArray(obj.actions)) {
    return { ok: false, reason: 'Missing "actions" array in plan response' };
  }

  // ---------------------------------------------------------------------------
  // Pass 1 — assign server UUIDs and build AI id → server UUID map
  // ---------------------------------------------------------------------------
  const aiToServer = new Map<string, string>();
  const serverToType = new Map<string, string>();
  const rawItems: Array<{ item: Record<string, unknown>; serverUuid: string }> = [];

  for (let i = 0; i < obj.actions.length; i++) {
    const raw = obj.actions[i];
    if (typeof raw !== "object" || raw === null) {
      return { ok: false, reason: `actions[${i}] is not an object` };
    }
    const item = raw as Record<string, unknown>;
    const serverUuid = randomUUID();
    const aiId = typeof item.actionId === "string" ? item.actionId : `__pos_${i}__`;
    aiToServer.set(aiId, serverUuid);
    if (typeof item.type === "string") serverToType.set(serverUuid, item.type);
    rawItems.push({ item, serverUuid });
  }

  // ---------------------------------------------------------------------------
  // Pass 2 — validate and build ActionItems
  // ---------------------------------------------------------------------------
  const validated: ActionItem[] = [];

  for (let i = 0; i < rawItems.length; i++) {
    const { item, serverUuid } = rawItems[i];

    // Validate type
    if (typeof item.type !== "string" || !ALLOWED_TYPES.has(item.type)) {
      return { ok: false, reason: `actions[${i}].type "${item.type}" is not allowed` };
    }

    // Validate dangerLevel
    const dangerLevel = typeof item.dangerLevel === "string" ? item.dangerLevel : "LOW";
    if (!ALLOWED_DANGER_LEVELS.has(dangerLevel)) {
      return { ok: false, reason: `actions[${i}].dangerLevel "${dangerLevel}" is invalid` };
    }

    // Resolve dependsOn: map AI-provided IDs to server UUIDs
    const rawDeps = Array.isArray(item.dependsOn) ? item.dependsOn : [];
    const dependsOn: string[] = rawDeps
      .filter((d): d is string => typeof d === "string")
      .map((d) => aiToServer.get(d) ?? d)
      .filter((d) => serverToType.has(d)); // only keep IDs that actually exist in this plan

    // Build input; inject dependency placeholder for CREATE_STRATEGY_VERSION → CREATE_STRATEGY
    let input: Record<string, unknown> =
      item.input && typeof item.input === "object" ? { ...(item.input as Record<string, unknown>) } : {};

    if (item.type === "CREATE_STRATEGY_VERSION" && dependsOn.length > 0) {
      // If strategyId is missing, empty, or looks like an AI-invented id (not a UUID from context),
      // and we depend on a CREATE_STRATEGY action — inject a FROM placeholder so the execute handler
      // can resolve it dynamically from the dependency's result.
      const createStrategyDepId = dependsOn.find(
        (d) => serverToType.get(d) === "CREATE_STRATEGY",
      );
      if (createStrategyDepId) {
        const strategyId = input.strategyId;
        const looksLikeContextUuid =
          typeof strategyId === "string" &&
          /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(strategyId);
        if (!looksLikeContextUuid) {
          input = { ...input, strategyId: `__FROM:${createStrategyDepId}:strategyId__` };
        }
      }
    }

    if (containsSecretKeys(input)) {
      return { ok: false, reason: `actions[${i}] input contains secret-like keys — rejected` };
    }

    validated.push({
      actionId: serverUuid,
      type: item.type as ActionType,
      title: typeof item.title === "string" ? item.title.slice(0, 80) : item.type,
      dangerLevel: dangerLevel as DangerLevel,
      requiresConfirmation: true,
      dependsOn,
      input,
      preconditions: Array.isArray(item.preconditions)
        ? (item.preconditions as unknown[]).filter((p): p is string => typeof p === "string")
        : [],
      expectedOutcome: typeof item.expectedOutcome === "string"
        ? item.expectedOutcome.slice(0, 200)
        : "",
    });
  }

  return {
    ok: true,
    actions: validated,
    note: typeof obj.note === "string" ? obj.note.slice(0, 500) : undefined,
  };
}

// ---------------------------------------------------------------------------
// Build final ActionPlan (called after DB persist so planId is known)
// ---------------------------------------------------------------------------

const PLAN_TTL_MINUTES = 30;

export function buildActionPlan(
  planId: string,
  actions: ActionItem[],
  note?: string,
): ActionPlan {
  const now = new Date();
  const expiresAt = new Date(now.getTime() + PLAN_TTL_MINUTES * 60 * 1000);
  return {
    planId,
    createdAt: now.toISOString(),
    expiresAt: expiresAt.toISOString(),
    actions,
    note,
  };
}
