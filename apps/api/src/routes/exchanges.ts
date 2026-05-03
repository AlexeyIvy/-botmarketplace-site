import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { getEncryptionKey, encrypt, decryptWithFallback } from "../lib/crypto.js";

// ---------------------------------------------------------------------------
// Safe projection — never return encryptedSecret or apiKey in responses
// ---------------------------------------------------------------------------

function safeView(conn: {
  id: string;
  workspaceId: string;
  exchange: string;
  name: string;
  status: string;
  createdAt: Date;
  updatedAt: Date;
  spotApiKey?: string | null;
  spotKeyLabel?: string | null;
}) {
  return {
    id: conn.id,
    workspaceId: conn.workspaceId,
    exchange: conn.exchange,
    name: conn.name,
    status: conn.status,
    createdAt: conn.createdAt,
    updatedAt: conn.updatedAt,
    // Boolean projection only — never expose the key string itself.
    // The label IS shown so operators can recognise "is this the spot
    // key I configured" without ever leaking the secret.
    hasSpotKey: Boolean(conn.spotApiKey),
    spotKeyLabel: conn.spotKeyLabel ?? null,
  };
}

// ---------------------------------------------------------------------------
// Validation constants
// ---------------------------------------------------------------------------

const API_KEY_MAX_LENGTH = 256;
const API_KEY_PATTERN = /^[a-zA-Z0-9\-_]+$/;

// ---------------------------------------------------------------------------
// Body shapes
// ---------------------------------------------------------------------------

interface CreateBody {
  exchange: string;
  name: string;
  apiKey: string;
  secret: string;
  /** Optional dedicated spot scope creds (docs/55-T5). When present, BOTH
   *  spotApiKey AND spotSecret must be supplied — submitting only one is a
   *  validation error so we never persist a half-configured spot key. */
  spotApiKey?: string;
  spotSecret?: string;
  /** Free-form label shown alongside the spot key in the UI. Optional. */
  spotKeyLabel?: string;
}

interface PatchBody {
  name?: string;
  apiKey?: string;
  secret?: string;
  /** Same dual-field rule on PATCH: supplying spotApiKey OR spotSecret
   *  alone is an error, except for the explicit clear path where BOTH
   *  are passed as `null`. */
  spotApiKey?: string | null;
  spotSecret?: string | null;
  spotKeyLabel?: string | null;
}

/** Validate an apiKey-shaped string. Returns an error message or null
 *  when the value passes. Centralised so the same rules apply to the
 *  linear `apiKey` and the optional `spotApiKey`. */
function validateApiKeyShape(value: unknown, fieldName: string): string | null {
  if (typeof value !== "string" || !value) {
    return `${fieldName} is required`;
  }
  if (value.length > API_KEY_MAX_LENGTH) {
    return `${fieldName} must not exceed ${API_KEY_MAX_LENGTH} characters`;
  }
  if (!API_KEY_PATTERN.test(value)) {
    return `${fieldName} contains invalid characters (only alphanumeric, dash, underscore allowed)`;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function exchangeRoutes(app: FastifyInstance) {
  // POST /exchanges — create a connection
  app.post<{ Body: CreateBody }>("/exchanges", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const key = getEncryptionKey(reply);
    if (!key) return;

    const { exchange, name, apiKey, secret, spotApiKey, spotSecret, spotKeyLabel } =
      request.body ?? {};

    const errors: Array<{ field: string; message: string }> = [];
    if (!exchange || typeof exchange !== "string") errors.push({ field: "exchange", message: "exchange is required" });
    if (!name || typeof name !== "string") errors.push({ field: "name", message: "name is required" });
    const apiKeyErr = validateApiKeyShape(apiKey, "apiKey");
    if (apiKeyErr) errors.push({ field: "apiKey", message: apiKeyErr });
    if (!secret || typeof secret !== "string") errors.push({ field: "secret", message: "secret is required" });

    // Spot creds: both-or-neither rule. spotKeyLabel is independent.
    const hasSpotKey = spotApiKey !== undefined && spotApiKey !== "";
    const hasSpotSecret = spotSecret !== undefined && spotSecret !== "";
    if (hasSpotKey !== hasSpotSecret) {
      errors.push({
        field: "spotApiKey",
        message: "spotApiKey and spotSecret must be supplied together (or neither)",
      });
    } else if (hasSpotKey && hasSpotSecret) {
      const spotKeyErr = validateApiKeyShape(spotApiKey, "spotApiKey");
      if (spotKeyErr) errors.push({ field: "spotApiKey", message: spotKeyErr });
      if (typeof spotSecret !== "string" || !spotSecret) {
        errors.push({ field: "spotSecret", message: "spotSecret must be a non-empty string" });
      }
    }
    if (spotKeyLabel !== undefined && typeof spotKeyLabel !== "string") {
      errors.push({ field: "spotKeyLabel", message: "spotKeyLabel must be a string when provided" });
    }
    if (errors.length > 0) {
      return problem(reply, 400, "Validation Error", "Invalid exchange connection payload", { errors });
    }

    // Unique check within workspace
    const existing = await prisma.exchangeConnection.findUnique({
      where: { workspaceId_name: { workspaceId: workspace.id, name } },
    });
    if (existing) {
      return problem(reply, 409, "Conflict", `Exchange connection "${name}" already exists in this workspace`);
    }

    const encryptedSecret = encrypt(secret, key);
    const spotEncryptedSecret =
      hasSpotKey && hasSpotSecret ? encrypt(spotSecret as string, key) : null;

    const conn = await prisma.exchangeConnection.create({
      data: {
        workspaceId: workspace.id,
        exchange: exchange.toUpperCase(),
        name,
        apiKey,
        encryptedSecret,
        spotApiKey: hasSpotKey ? (spotApiKey as string) : null,
        spotEncryptedSecret,
        spotKeyLabel: spotKeyLabel ?? null,
        status: "UNKNOWN",
      },
    });

    return reply.status(201).send(safeView(conn));
  });

  // GET /exchanges — list connections for workspace (no secrets)
  app.get("/exchanges", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const connections = await prisma.exchangeConnection.findMany({
      where: { workspaceId: workspace.id },
      orderBy: { createdAt: "desc" },
    });

    return reply.send(connections.map(safeView));
  });

  // GET /exchanges/:id — single connection (no secrets)
  app.get<{ Params: { id: string } }>("/exchanges/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const conn = await prisma.exchangeConnection.findUnique({
      where: { id: request.params.id },
    });
    if (!conn || conn.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Exchange connection not found");
    }

    return reply.send(safeView(conn));
  });

  // PATCH /exchanges/:id — update name / apiKey / secret
  app.patch<{ Params: { id: string }; Body: PatchBody }>("/exchanges/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const conn = await prisma.exchangeConnection.findUnique({
      where: { id: request.params.id },
    });
    if (!conn || conn.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Exchange connection not found");
    }

    const { name, apiKey, secret, spotApiKey, spotSecret, spotKeyLabel } =
      request.body ?? {};

    // Validate apiKey if provided
    if (apiKey !== undefined) {
      if (typeof apiKey !== "string" || !apiKey.trim()) {
        return problem(reply, 400, "Validation Error", "apiKey must be a non-empty string");
      }
      if (apiKey.length > API_KEY_MAX_LENGTH) {
        return problem(reply, 400, "Validation Error", `apiKey must not exceed ${API_KEY_MAX_LENGTH} characters`);
      }
      if (!API_KEY_PATTERN.test(apiKey)) {
        return problem(reply, 400, "Validation Error", "apiKey contains invalid characters (only alphanumeric, dash, underscore allowed)");
      }
    }

    // If secret is being updated we need the encryption key
    let encryptedSecret: string | undefined;
    if (secret !== undefined) {
      if (typeof secret !== "string" || !secret) {
        return problem(reply, 400, "Validation Error", "secret must be a non-empty string");
      }
      const key = getEncryptionKey(reply);
      if (!key) return;
      encryptedSecret = encrypt(secret, key);
    }

    // Spot creds — three valid shapes:
    //   1. Both omitted → no change.
    //   2. Both null    → clear the spot key.
    //   3. Both strings → rotate / set the spot key.
    // Anything else is rejected so we never persist a half-configured key.
    let spotEncryptedSecret: string | null | undefined; // undefined → no change
    let spotApiKeyValue: string | null | undefined;
    const spotKeyOmitted = spotApiKey === undefined && spotSecret === undefined;
    const spotKeyCleared = spotApiKey === null && spotSecret === null;
    const spotKeySet = typeof spotApiKey === "string" && typeof spotSecret === "string";
    if (!spotKeyOmitted) {
      if (spotKeyCleared) {
        spotApiKeyValue = null;
        spotEncryptedSecret = null;
      } else if (spotKeySet) {
        const spotKeyErr = validateApiKeyShape(spotApiKey, "spotApiKey");
        if (spotKeyErr) return problem(reply, 400, "Validation Error", spotKeyErr);
        if (!spotSecret) {
          return problem(reply, 400, "Validation Error", "spotSecret must be a non-empty string");
        }
        const key = getEncryptionKey(reply);
        if (!key) return;
        spotApiKeyValue = spotApiKey;
        spotEncryptedSecret = encrypt(spotSecret, key);
      } else {
        return problem(
          reply,
          400,
          "Validation Error",
          "spotApiKey and spotSecret must be supplied together (both string to set, both null to clear)",
        );
      }
    }

    if (spotKeyLabel !== undefined && spotKeyLabel !== null && typeof spotKeyLabel !== "string") {
      return problem(reply, 400, "Validation Error", "spotKeyLabel must be a string or null");
    }

    const updateData: Record<string, unknown> = {};
    if (name !== undefined) updateData.name = name;
    if (apiKey !== undefined) updateData.apiKey = apiKey;
    if (encryptedSecret !== undefined) updateData.encryptedSecret = encryptedSecret;
    if (spotApiKeyValue !== undefined) updateData.spotApiKey = spotApiKeyValue;
    if (spotEncryptedSecret !== undefined) updateData.spotEncryptedSecret = spotEncryptedSecret;
    if (spotKeyLabel !== undefined) updateData.spotKeyLabel = spotKeyLabel;
    // Reset status to UNKNOWN whenever ANY credential pair changes — the
    // operator should re-test the connection after rotation/clear.
    if (
      apiKey !== undefined ||
      secret !== undefined ||
      spotApiKeyValue !== undefined ||
      spotEncryptedSecret !== undefined
    ) {
      updateData.status = "UNKNOWN";
    }

    const updated = await prisma.exchangeConnection.update({
      where: { id: conn.id },
      data: updateData,
    });

    return reply.send(safeView(updated));
  });

  // DELETE /exchanges/:id
  app.delete<{ Params: { id: string } }>("/exchanges/:id", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const conn = await prisma.exchangeConnection.findUnique({
      where: { id: request.params.id },
    });
    if (!conn || conn.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Exchange connection not found");
    }

    await prisma.exchangeConnection.delete({ where: { id: conn.id } });
    return reply.status(204).send();
  });

  // POST /exchanges/:id/test — demo-first connectivity check
  app.post<{ Params: { id: string } }>("/exchanges/:id/test", { onRequest: [app.authenticate] }, async (request, reply) => {
    const workspace = await resolveWorkspace(request, reply);
    if (!workspace) return;

    const conn = await prisma.exchangeConnection.findUnique({
      where: { id: request.params.id },
    });
    if (!conn || conn.workspaceId !== workspace.id) {
      return problem(reply, 404, "Not Found", "Exchange connection not found");
    }

    let decryptedSecret: string;
    try {
      decryptedSecret = decryptWithFallback(conn.encryptedSecret);
    } catch (err) {
      request.log.error({ connectionId: conn.id, err }, "Failed to decrypt exchange secret");
      return problem(reply, 500, "Internal Server Error", "Failed to decrypt exchange credentials");
    }

    // Demo-first: validate that credentials are non-empty and perform a lightweight
    // reachability check. A real exchange call (e.g. GET /v5/account/info on Bybit)
    // would be wired in Stage 9b.
    let status: "CONNECTED" | "FAILED" = "FAILED";
    let detail = "Connection test failed";

    if (conn.apiKey && decryptedSecret) {
      // Demo placeholder: credentials present → optimistically mark CONNECTED.
      // Stage 9b will replace this with a real exchange API call.
      status = "CONNECTED";
      detail = "Credentials verified (demo-first — real exchange call deferred to Stage 9b)";
    }

    await prisma.exchangeConnection.update({
      where: { id: conn.id },
      data: { status },
    });

    return reply.send({
      id: conn.id,
      status,
      detail,
    });
  });
}
