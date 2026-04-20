/**
 * Telegram Notification Service (Roadmap V3, Tier 4, #26)
 *
 * Sends notifications via Telegram Bot API for critical bot events:
 *   - RUN_FAILED, RUN_TIMED_OUT — run failures
 *   - RUN_STOPPING — circuit breaker triggered (pauseOnError / dailyLossLimit)
 *   - HEDGE_OPENED, HEDGE_CLOSED — hedge position lifecycle
 *
 * Configuration stored per-user in UserPreference.notifyJson:
 *   { telegram: { botToken: string, chatId: string, enabled: boolean } }
 *
 * Uses Node built-in fetch — no external dependencies.
 */

import { logger } from "./logger.js";
import { prisma } from "./prisma.js";
import { decryptWithFallback } from "./crypto.js";

const notifyLog = logger.child({ module: "notify" });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TelegramConfig {
  botToken: string;
  chatId: string;
  enabled: boolean;
}

export interface NotifyConfig {
  telegram?: TelegramConfig;
}

export type NotifyEventType =
  | "RUN_FAILED"
  | "RUN_TIMED_OUT"
  | "RUN_STOPPING"
  | "HEDGE_OPENED"
  | "HEDGE_CLOSED"
  | "INTENT_FAILED";

export interface NotifyPayload {
  eventType: NotifyEventType;
  symbol?: string;
  runId?: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Telegram sender
// ---------------------------------------------------------------------------

/**
 * Send a message via Telegram Bot API.
 * Non-blocking: errors are logged but never thrown (fire-and-forget).
 */
export async function sendTelegramMessage(
  config: TelegramConfig,
  text: string,
): Promise<boolean> {
  if (!config.enabled || !config.botToken || !config.chatId) {
    return false;
  }

  const url = `https://api.telegram.org/bot${config.botToken}/sendMessage`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: config.chatId,
        text,
        parse_mode: "HTML",
        disable_web_page_preview: true,
      }),
      signal: AbortSignal.timeout(10_000), // 10s timeout
    });

    if (!res.ok) {
      const body = await res.text().catch(() => "");
      notifyLog.warn({ status: res.status, body: body.slice(0, 200) }, "Telegram API error");
      return false;
    }

    return true;
  } catch (err) {
    notifyLog.warn({ err }, "Telegram send failed");
    return false;
  }
}

// ---------------------------------------------------------------------------
// Message formatting
// ---------------------------------------------------------------------------

function formatNotification(payload: NotifyPayload): string {
  const icon = EVENT_ICONS[payload.eventType] ?? "ℹ️";
  const parts: string[] = [];

  parts.push(`${icon} <b>${payload.eventType}</b>`);
  if (payload.symbol) parts.push(`Symbol: <code>${payload.symbol}</code>`);
  if (payload.runId) parts.push(`Run: <code>${payload.runId.slice(0, 8)}</code>`);
  parts.push("");
  parts.push(payload.message);
  parts.push("");
  parts.push(`<i>${new Date().toISOString()}</i>`);

  return parts.join("\n");
}

const EVENT_ICONS: Record<string, string> = {
  RUN_FAILED: "🔴",
  RUN_TIMED_OUT: "⏰",
  RUN_STOPPING: "⚠️",
  HEDGE_OPENED: "🟢",
  HEDGE_CLOSED: "🔵",
  INTENT_FAILED: "❌",
};

// ---------------------------------------------------------------------------
// Main notify function
// ---------------------------------------------------------------------------

/**
 * Send a notification if the user has Telegram configured.
 * Safe to call from anywhere — never throws.
 */
export async function notify(
  config: NotifyConfig | null | undefined,
  payload: NotifyPayload,
): Promise<void> {
  if (!config?.telegram?.enabled) return;

  const text = formatNotification(payload);
  await sendTelegramMessage(config.telegram, text);
}

// ---------------------------------------------------------------------------
// Config parsing
// ---------------------------------------------------------------------------

/**
 * Parse NotifyConfig from raw JSON (e.g., from UserPreference.notifyJson).
 * Returns null if invalid or not configured.
 */
export function parseNotifyConfig(raw: unknown): NotifyConfig | null {
  if (!raw || typeof raw !== "object") return null;

  const obj = raw as Record<string, unknown>;
  const tg = obj.telegram as Record<string, unknown> | undefined;

  if (!tg || typeof tg !== "object") return null;

  if (typeof tg.botToken !== "string" || typeof tg.chatId !== "string") {
    return null;
  }

  let botToken = tg.botToken;

  // Decrypt botToken if it was stored encrypted
  if (tg._tokenEncrypted) {
    try {
      botToken = decryptWithFallback(botToken);
    } catch (err) {
      notifyLog.warn({ err }, "failed to decrypt Telegram botToken");
      return null;
    }
  }

  return {
    telegram: {
      botToken,
      chatId: tg.chatId,
      enabled: tg.enabled !== false,
    },
  };
}

// ---------------------------------------------------------------------------
// Bot run event notification (used by botWorker)
// ---------------------------------------------------------------------------

/** In-memory cache of notification configs per workspace (TTL: 5 min) */
const configCache = new Map<string, { config: NotifyConfig | null; ts: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000;

/**
 * Invalidate cached notification config for a specific user.
 * Call after PUT /user/notifications to ensure changes take effect immediately.
 */
export function invalidateNotifyCache(userId: string): void {
  for (const [wsId, entry] of configCache) {
    // Force expiry so next read re-fetches from DB
    if (entry) entry.ts = 0;
  }
  notifyLog.debug({ userId }, "notify config cache invalidated");
}

/**
 * Load notification config for a workspace's owner.
 * Cached for 5 minutes to avoid DB queries on every poll cycle.
 */
async function getNotifyConfigForWorkspace(workspaceId: string): Promise<NotifyConfig | null> {
  const cached = configCache.get(workspaceId);
  if (cached && Date.now() - cached.ts < CACHE_TTL_MS) {
    return cached.config;
  }

  try {
    const ownerMember = await prisma.workspaceMember.findFirst({
      where: { workspaceId, role: "OWNER" },
      select: { userId: true },
    });

    if (!ownerMember) {
      configCache.set(workspaceId, { config: null, ts: Date.now() });
      return null;
    }

    const prefs = await prisma.userPreference.findUnique({
      where: { userId: ownerMember.userId },
      select: { notifyJson: true },
    });

    const config = parseNotifyConfig(prefs?.notifyJson);
    configCache.set(workspaceId, { config, ts: Date.now() });
    return config;
  } catch (err) {
    notifyLog.warn({ err, workspaceId }, "failed to load notify config");
    return null;
  }
}

/**
 * Send a notification for a bot run event.
 * Resolves the workspace owner's notification config and dispatches.
 * Fire-and-forget — never throws.
 */
export async function notifyRunEvent(
  workspaceId: string,
  payload: NotifyPayload,
): Promise<void> {
  try {
    const config = await getNotifyConfigForWorkspace(workspaceId);
    await notify(config, payload);
  } catch {
    // Never let notification failures affect the worker
  }
}
