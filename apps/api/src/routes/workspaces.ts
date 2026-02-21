import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { problem } from "../lib/problem.js";

interface CreateWorkspaceBody {
  name?: string;
}

export async function workspacesRoutes(app: FastifyInstance) {
  // GET /workspaces — list workspaces the authenticated user belongs to
  app.get("/workspaces", { onRequest: [app.authenticate] }, async (request, reply) => {
    const userId = (request.user as { sub: string }).sub;

    const memberships = await prisma.workspaceMember.findMany({
      where: { userId },
      include: {
        workspace: { select: { id: true, name: true, createdAt: true, updatedAt: true } },
      },
      orderBy: { createdAt: "desc" },
    });

    return reply.send(memberships.map((m: { workspace: unknown }) => m.workspace));
  });

  // POST /workspaces — create a new workspace (authenticated user becomes OWNER)
  app.post<{ Body: CreateWorkspaceBody }>("/workspaces", { onRequest: [app.authenticate] }, async (request, reply) => {
    const userId = (request.user as { sub: string }).sub;
    const { name } = request.body ?? {};

    if (name !== undefined && (typeof name !== "string" || name.trim().length === 0)) {
      return problem(reply, 400, "Validation Error", "name must be a non-empty string");
    }

    const shortId = crypto.randomUUID().slice(0, 8);
    const finalName = name?.trim() || `Workspace ${shortId}`;

    const workspace = await prisma.workspace.create({
      data: {
        name: finalName,
        members: {
          create: { userId, role: "OWNER" },
        },
      },
      select: { id: true, name: true, createdAt: true, updatedAt: true },
    });

    return reply.status(201).send(workspace);
  });
}
