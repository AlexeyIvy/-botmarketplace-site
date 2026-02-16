import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";

interface CreateWorkspaceBody {
  name?: string;
}

export async function workspacesRoutes(app: FastifyInstance) {
  // GET /workspaces — list all workspaces (MVP: no auth filter)
  app.get("/workspaces", async (_request, reply) => {
    const workspaces = await prisma.workspace.findMany({
      orderBy: { createdAt: "desc" },
      select: { id: true, name: true, createdAt: true, updatedAt: true },
    });
    return reply.send(workspaces);
  });

  // POST /workspaces — create a new workspace
  app.post<{ Body: CreateWorkspaceBody }>("/workspaces", async (request, reply) => {
    const { name } = request.body ?? {};

    if (name !== undefined && (typeof name !== "string" || name.trim().length === 0)) {
      return problem(reply, 400, "Validation Error", "name must be a non-empty string");
    }

    const shortId = crypto.randomUUID().slice(0, 8);
    const finalName = name?.trim() || `Workspace ${shortId}`;

    const workspace = await prisma.workspace.create({
      data: { name: finalName },
      select: { id: true, name: true, createdAt: true, updatedAt: true },
    });

    return reply.status(201).send(workspace);
  });
}
