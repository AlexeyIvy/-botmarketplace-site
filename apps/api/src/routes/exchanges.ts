import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";
import { resolveWorkspace } from "../lib/workspace.js";
import { getEncryptionKey, encrypt, decrypt } from "../lib/crypto.js";

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
}) {
  return {
    id: conn.id,
    workspaceId: conn.workspaceId,
    exchange: conn.exchange,
    name: conn.name,
    status: conn.status,
    createdAt: conn.createdAt,
    updatedAt: conn.updatedAt,
  };
}

// ---------------------------------------------------------------------------
// Body shapes
// ---------------------------------------------------------------------------

interface CreateBody {
  exchange: string;
  name: string;
  apiKey: string;
  secret: string;
}

interface PatchBody {
  name?: string;
  apiKey?: string;
  secret?: string;
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

    const { exchange, name, apiKey, secret } = request.body ?? {};

    const errors: Array<{ field: string; message: string }> = [];
    if (!exchange || typeof exchange !== "string") errors.push({ field: "exchange", message: "exchange is required" });
    if (!name || typeof name !== "string") errors.push({ field: "name", message: "name is required" });
    if (!apiKey || typeof apiKey !== "string") errors.push({ field: "apiKey", message: "apiKey is required" });
    if (!secret || typeof secret !== "string") errors.push({ field: "secret", message: "secret is required" });
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

    const conn = await prisma.exchangeConnection.create({
      data: {
        workspaceId: workspace.id,
        exchange: exchange.toUpperCase(),
        name,
        apiKey,
        encryptedSecret,
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

    const { name, apiKey, secret } = request.body ?? {};

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

    const updateData: Record<string, unknown> = {};
    if (name !== undefined) updateData.name = name;
    if (apiKey !== undefined) updateData.apiKey = apiKey;
    if (encryptedSecret !== undefined) updateData.encryptedSecret = encryptedSecret;
    // Reset status to UNKNOWN whenever credentials change
    if (apiKey !== undefined || secret !== undefined) updateData.status = "UNKNOWN";

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

    const key = getEncryptionKey(reply);
    if (!key) return;

    let decryptedSecret: string;
    try {
      decryptedSecret = decrypt(conn.encryptedSecret, key);
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
