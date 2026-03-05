import type { FastifyInstance, FastifyReply } from "fastify";
import { prisma } from "../lib/prisma.js";

// ---------------------------------------------------------------------------
// Types & constants
// ---------------------------------------------------------------------------

const ALLOWED_INTERVALS = new Set(["1", "5", "15", "30", "60", "240", "D"]);
const MAX_WATCHLIST = 50;
const MAX_SYMBOL_LEN = 30;
const MAX_MARKETS = 20;

/** Default terminalJson returned when a user has no saved preferences. */
const DEFAULT_TERMINAL_JSON = {
  version: 1,
  terminal: {},
};

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function problem(reply: FastifyReply, status: number, detail: string) {
  const titles: Record<number, string> = {
    400: "Bad Request",
    401: "Unauthorized",
  };
  return reply.status(status).send({
    type: "about:blank",
    title: titles[status] ?? "Error",
    status,
    detail,
  });
}

/**
 * Validates terminalJson and returns an error string or null.
 * Schema (version 1):
 *   { version: 1, terminal: { "exchange:market": { watchlist, activeSymbol?, interval?, indicators?, layout? } } }
 */
function validateTerminalJson(val: unknown): string | null {
  if (typeof val !== "object" || val === null || Array.isArray(val)) {
    return "terminalJson must be an object";
  }
  const obj = val as Record<string, unknown>;

  if (obj.version !== 1) {
    return "terminalJson.version must equal 1";
  }

  if (typeof obj.terminal !== "object" || obj.terminal === null || Array.isArray(obj.terminal)) {
    return "terminalJson.terminal must be an object";
  }

  const terminal = obj.terminal as Record<string, unknown>;
  const keys = Object.keys(terminal);

  if (keys.length > MAX_MARKETS) {
    return `terminalJson.terminal must not exceed ${MAX_MARKETS} exchange+market keys`;
  }

  for (const key of keys) {
    // key must match "exchange:market" pattern
    if (!/^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$/.test(key)) {
      return `terminalJson.terminal key "${key}" must be in format "exchange:market"`;
    }

    const mkt = terminal[key];
    if (typeof mkt !== "object" || mkt === null || Array.isArray(mkt)) {
      return `terminalJson.terminal["${key}"] must be an object`;
    }
    const m = mkt as Record<string, unknown>;

    // watchlist — required, array of strings, max length
    if (!Array.isArray(m.watchlist)) {
      return `terminalJson.terminal["${key}"].watchlist must be an array`;
    }
    if (m.watchlist.length > MAX_WATCHLIST) {
      return `terminalJson.terminal["${key}"].watchlist must not exceed ${MAX_WATCHLIST} items`;
    }
    for (const sym of m.watchlist) {
      if (typeof sym !== "string" || sym.length === 0 || sym.length > MAX_SYMBOL_LEN) {
        return `terminalJson.terminal["${key}"].watchlist items must be non-empty strings up to ${MAX_SYMBOL_LEN} chars`;
      }
    }

    // activeSymbol — optional string
    if (m.activeSymbol !== undefined && m.activeSymbol !== null) {
      if (typeof m.activeSymbol !== "string" || m.activeSymbol.length > MAX_SYMBOL_LEN) {
        return `terminalJson.terminal["${key}"].activeSymbol must be a string up to ${MAX_SYMBOL_LEN} chars`;
      }
    }

    // interval — optional, must be in allowed set
    if (m.interval !== undefined && m.interval !== null) {
      if (!ALLOWED_INTERVALS.has(String(m.interval))) {
        return `terminalJson.terminal["${key}"].interval must be one of: ${[...ALLOWED_INTERVALS].join(", ")}`;
      }
    }

    // indicators — optional array
    if (m.indicators !== undefined && m.indicators !== null) {
      if (!Array.isArray(m.indicators)) {
        return `terminalJson.terminal["${key}"].indicators must be an array`;
      }
    }

    // layout — optional object
    if (m.layout !== undefined && m.layout !== null) {
      if (typeof m.layout !== "object" || Array.isArray(m.layout)) {
        return `terminalJson.terminal["${key}"].layout must be an object`;
      }
    }
  }

  return null;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function preferencesRoutes(app: FastifyInstance) {
  // ── GET /user/preferences ──────────────────────────────────────────────────
  app.get("/user/preferences", { onRequest: [app.authenticate] }, async (request, reply) => {
    const payload = request.user as { sub: string };

    const row = await prisma.userPreference.findUnique({
      where: { userId: payload.sub },
    });

    if (!row) {
      return reply.send({ terminalJson: DEFAULT_TERMINAL_JSON });
    }

    return reply.send({ terminalJson: row.terminalJson });
  });

  // ── PUT /user/preferences ──────────────────────────────────────────────────
  app.put<{ Body: { terminalJson: unknown } }>(
    "/user/preferences",
    { onRequest: [app.authenticate] },
    async (request, reply) => {
      const payload = request.user as { sub: string };
      const body = request.body as Record<string, unknown> | undefined;

      if (!body || typeof body !== "object" || !("terminalJson" in body)) {
        return problem(reply, 400, "Request body must contain terminalJson");
      }

      const err = validateTerminalJson(body.terminalJson);
      if (err) {
        return problem(reply, 400, err);
      }

      const row = await prisma.userPreference.upsert({
        where: { userId: payload.sub },
        create: {
          userId: payload.sub,
          terminalJson: body.terminalJson as object,
        },
        update: {
          terminalJson: body.terminalJson as object,
        },
      });

      return reply.send({ terminalJson: row.terminalJson });
    },
  );
}
